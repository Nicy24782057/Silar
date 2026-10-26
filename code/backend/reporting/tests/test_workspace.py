"""PostgreSQL integration checks for the SLR13 workspace and existing aggregate."""
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from django.core.management import call_command
from django.db import close_old_connections, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from common.testing import user
from core.models import AuditEvent, OperatorAssignment, OperatorReview, FollowUpRecord, PublicationVersion, Notification
from core.permissions import OPERATOR_PERMISSIONS, ADMIN_PERMISSIONS, permission_queryset
from core.test_fixtures import source_chain


class WorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_silar', verbosity=0)
        cls.owner = user('private-reporter@example.test')
        cls.owner.full_name = 'Nama Reporter Rahasia'; cls.owner.save()
        cls.andi = user('andi@example.test', role='OPERATOR', perms=OPERATOR_PERMISSIONS)
        cls.andi.full_name = 'Andi Pratama'; cls.andi.save()
        cls.rina = user('rina@example.test', role='OPERATOR', perms=OPERATOR_PERMISSIONS)
        cls.rina.full_name = 'Rina Lestari'; cls.rina.save()
        cls.admin = user('admin@example.test', role='ADMIN', perms=ADMIN_PERMISSIONS)
        cls.report, cls.bundle, cls.analysis_run, cls.card, cls.evidence = source_chain(cls.owner, official=True)
        cls.draft, *_ = source_chain(cls.owner, official=False)

    def setUp(self): self.client = APIClient()

    def as_user(self, person): self.client.force_authenticate(user=person)

    def read(self, path): return self.client.get('/api/v1/workspace/' + path)

    def write(self, action, body=None, person=None, key=None, report=None):
        if person: self.as_user(person)
        report = report or self.report; report.refresh_from_db()
        payload = {'expected_revision': report.revision, **(body or {})}
        return self.client.post(f'/api/v1/workspace/reports/{report.id}/{action}/', payload,
                                format='json', HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def claimed(self):
        response = self.write('claim', person=self.andi)
        self.assertEqual(response.status_code, 200, response.content)
        return response

    def reviewed(self, outcome='VALID'):
        self.claimed()
        response = self.write('reviews', {'outcome': outcome, 'reason': 'Hasil pemeriksaan sumber resmi.'})
        self.assertEqual(response.status_code, 201, response.content)
        return response

    def test_queue_contains_only_official_summary_without_reporter_pii(self):
        self.as_user(self.andi); response = self.read('reports/?scope=queue')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)
        row = response.json()['results'][0]
        self.assertEqual(row['id'], str(self.report.id))
        self.assertNotIn('Nama Reporter Rahasia', response.content.decode())
        for key in ['email', 'owner_id', 'text_content', 'location_text', 'official_bundle']:
            self.assertNotIn(key, row)

    def test_reporter_cannot_open_staff_lists_or_claim(self):
        self.as_user(self.owner)
        self.assertEqual(self.read('reports/?scope=queue').status_code, 403)
        self.assertEqual(self.write('claim').status_code, 403)

    def test_claim_assigns_exact_account_name_and_replay_has_no_extra_events(self):
        key = uuid.uuid4(); result = self.write('claim', person=self.andi, key=key)
        self.assertEqual(result.status_code, 200)
        self.as_user(self.andi)
        row = self.read('reports/?scope=assigned').json()['results'][0]
        self.assertEqual(row['operator_name'], 'Andi Pratama')
        self.assertEqual(row['operator_id'], str(self.andi.id))
        repeat = self.client.post(f'/api/v1/workspace/reports/{self.report.id}/claim/',
            {'expected_revision': 1}, format='json', HTTP_IDEMPOTENCY_KEY=str(key))
        self.assertEqual(repeat.status_code, 200, repeat.content)
        self.assertEqual(repeat['Idempotency-Replayed'], 'true')
        self.assertEqual(OperatorAssignment.objects.filter(report=self.report).count(), 1)
        self.assertEqual(AuditEvent.objects.filter(report=self.report, action='REPORT_CLAIMED').count(), 1)

    def test_claim_requires_both_claim_and_assigned_read_permissions(self):
        person = user('queue-only@example.test', role='OPERATOR', perms=['view_queue', 'claim_report'])
        self.assertEqual(self.write('claim', person=person).status_code, 403)

    def test_admin_role_does_not_allow_operator_decisions_or_private_source(self):
        self.claimed(); self.as_user(self.admin)
        response = self.read(f'reports/{self.report.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertFalse(data['private_access']); self.assertIsNone(data['official_bundle'])
        self.assertEqual(data['assignment']['operator_name'], 'Andi Pratama')
        self.assertEqual(self.write('reviews', {'outcome': 'VALID', 'reason': 'Tidak berhak.'}).status_code, 403)

    def test_explicit_admin_operator_grants_still_require_assignment(self):
        self.admin.user_permissions.add(*permission_queryset().filter(codename__in=OPERATOR_PERMISSIONS))
        self.claimed()
        self.assertEqual(self.write('reviews', {'outcome': 'VALID', 'reason': 'Belum ditugaskan.'}, person=self.admin).status_code, 404)

    def test_reassignment_preserves_history_and_revokes_old_handler_and_replay(self):
        key=uuid.uuid4(); self.write('claim', person=self.andi, key=key)
        result=self.write('assignment', {'operator_id': str(self.rina.id), 'reason': 'Pengalihan wilayah.'}, person=self.admin)
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(OperatorAssignment.objects.filter(report=self.report).count(), 2)
        self.assertEqual(OperatorAssignment.objects.filter(report=self.report, ended_at__isnull=True).get().operator_id, self.rina.id)
        self.as_user(self.andi)
        self.assertEqual(self.read(f'reports/{self.report.id}/').status_code, 404)
        replay=self.client.post(f'/api/v1/workspace/reports/{self.report.id}/claim/', {'expected_revision':1},
            format='json', HTTP_IDEMPOTENCY_KEY=str(key))
        self.assertEqual(replay.status_code, 409)
        self.as_user(self.rina)
        self.assertTrue(self.read(f'reports/{self.report.id}/').json()['data']['private_access'])

    def test_assignment_targets_use_names_and_exclude_unverified_inactive_and_plain_admin(self):
        user('pending@example.test', role='OPERATOR', verified=False, perms=OPERATOR_PERMISSIONS)
        user('disabled@example.test', role='OPERATOR', active=False, perms=OPERATOR_PERMISSIONS)
        self.as_user(self.admin); response=self.read('assignment-targets/')
        self.assertEqual({x['full_name']for x in response.json()['results']},{'Andi Pratama','Rina Lestari'})
        self.assertNotIn('email',response.json()['results'][0])

    def test_reassignment_rejects_missing_reason_and_noneligible_target(self):
        self.as_user(self.admin)
        self.assertEqual(self.write('assignment',{'operator_id':str(self.andi.id),'reason':' '}).status_code,400)
        self.assertEqual(self.write('assignment',{'operator_id':str(self.owner.id),'reason':'Uji.'}).status_code,422)

    def test_stale_revision_does_not_record_review(self):
        self.claimed()
        result=self.write('reviews',{'outcome':'VALID','reason':'Sumber sesuai.','expected_revision':1})
        self.assertEqual(result.status_code,409)
        self.assertEqual(result.json()['error']['code'],'REVISION_CONFLICT')
        self.assertEqual(OperatorReview.objects.count(),0)

    def test_each_review_outcome_retains_actor_time_and_official_version(self):
        self.claimed()
        for outcome in ['VALID','INVALID','INCONCLUSIVE']:
            result=self.write('reviews',{'outcome':outcome,'reason':'Pemeriksaan '+outcome})
            self.assertEqual(result.status_code,201,result.content)
            row=OperatorReview.objects.filter(report=self.report).latest('reviewed_at')
            self.assertEqual(row.operator_id,self.andi.id);self.assertEqual(row.card_version_id,self.card.id)
            self.assertIsNotNone(row.reviewed_at);self.assertEqual(row.outcome,outcome)
        self.card.refresh_from_db();self.assertEqual(self.card.version_number,1)

    def test_followups_require_review_and_terminal_reason_and_reject_repeat(self):
        self.claimed()
        self.assertEqual(self.write('followups',{'description':'Periksa lokasi.'}).status_code,422)
        self.write('reviews',{'outcome':'VALID','reason':'Sesuai sumber.'})
        self.assertEqual(self.write('followups',{'description':'Periksa lokasi.'}).status_code,201)
        item=FollowUpRecord.objects.get(report=self.report)
        self.assertEqual(self.write(f'followups/{item.id}',{'status':'CANCELLED','completion_reason':' '}).status_code,400)
        self.assertEqual(self.write(f'followups/{item.id}',{'status':'CANCELLED','completion_reason':'Tugas tidak lagi diperlukan.'}).status_code,200)
        item.refresh_from_db();self.assertEqual(item.status,'CANCELLED');self.assertIsNotNone(item.finished_at)
        self.assertEqual(self.write(f'followups/{item.id}',{'status':'DONE','completion_reason':'Ulang.'}).status_code,422)

    def test_prepare_is_only_direction_without_creating_or_publishing_candidate(self):
        self.reviewed()
        result=self.write('decision',{'decision':'PREPARE','reason':'Layak disiapkan.'})
        self.assertEqual(result.status_code,200,result.content)
        self.report.refresh_from_db();self.assertEqual(self.report.publication_status,'PENDING_APPROVAL')
        self.assertEqual(PublicationVersion.objects.count(),0)
        self.assertEqual(self.write('close',{'closure_note':'Belum boleh.'}).status_code,422)

    def test_invalid_and_inconclusive_cannot_prepare_but_can_close_internal(self):
        self.claimed()
        for outcome in ['INVALID','INCONCLUSIVE']:
            with self.subTest(outcome=outcome):
                self.write('reviews',{'outcome':outcome,'reason':'Bukti tidak cukup.'})
                self.assertEqual(self.write('decision',{'decision':'PREPARE','reason':'Tidak boleh.'}).status_code,422)
        self.assertEqual(self.write('close',{'closure_note':'Ditutup dengan hasil inconclusive.'}).status_code,200)

    def test_close_guards_pending_followup_and_closed_blocks_writes_but_retains_reads(self):
        self.reviewed();self.write('followups',{'description':'Tindak lanjuti.'})
        self.write('decision',{'decision':'INTERNAL','reason':'Untuk penanganan internal.'})
        self.assertEqual(self.write('close',{'closure_note':'Belum selesai.'}).status_code,422)
        item=FollowUpRecord.objects.get(report=self.report)
        self.write(f'followups/{item.id}',{'status':'DONE','completion_reason':'Sudah ditangani.'})
        key=uuid.uuid4();result=self.write('close',{'closure_note':'Penanganan selesai.'},key=key)
        self.assertEqual(result.status_code,200,result.content)
        self.assertEqual(self.read(f'reports/{self.report.id}/').status_code,200)
        self.assertEqual(self.write('reviews',{'outcome':'VALID','reason':'Ulang.'}).status_code,422)
        self.assertEqual(self.write('assignment',{'operator_id':str(self.rina.id),'reason':'Tidak boleh.'},person=self.admin).status_code,422)
        self.assertEqual(AuditEvent.objects.filter(report=self.report,action='REPORT_CLOSED').count(),1)

    def test_active_candidate_blocks_close_and_review(self):
        self.reviewed()
        candidate=PublicationVersion.objects.create(report=self.report,card_version=self.card,version_number=1,
            data={'event_type':'FLOOD','summary':'Kejadian banjir.','general_location':None,'time_text':None,'occurred_at':None,'general_impact':None,'handling_update':None},sanitized_by=self.andi)
        self.report.refresh_from_db();self.report.active_publication_candidate=candidate;self.report.publication_status='INTERNAL';self.report.save()
        self.assertEqual(self.write('reviews',{'outcome':'INVALID','reason':'Diblokir.'}).status_code,422)
        self.assertEqual(self.write('close',{'closure_note':'Diblokir.'}).status_code,422)

    def test_audit_is_read_only_named_and_monitoring_has_no_private_content(self):
        self.claimed();self.as_user(self.admin)
        data=self.read('audit/').json()['results']
        self.assertEqual(data[0]['actor_name'],'Andi Pratama')
        response=self.read('services/');self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['data']['database'],'READY')
        for hidden in ['raw_output','text_content','SECRET_KEY','GEMINI_API_KEY','execution_context','private-reporter']:
            self.assertNotIn(hidden,response.content.decode())
        self.assertEqual(self.client.post('/api/v1/workspace/services/',{},format='json').status_code,405)

    def test_account_changes_retain_reason_and_full_name_in_targets(self):
        self.as_user(self.admin)
        old_ids=set(permission_queryset().filter(codename__in=OPERATOR_PERMISSIONS).values_list('id',flat=True))
        read_id=permission_queryset().get(codename='view_assigned_report').id
        response=self.client.patch(f'/api/v1/admin/operators/{self.andi.id}/',{'full_name':'Andi Nama Baru','permission_ids':[read_id],'reason':'Pembaruan nama petugas.'},format='json')
        self.assertEqual(response.status_code,200,response.content)
        data=self.read('assignment-targets/').json()['results']
        self.assertIn('Andi Nama Baru',[x['full_name']for x in data])
        event=AuditEvent.objects.filter(object_id=self.andi.id).latest('created_at')
        self.assertEqual(event.after['reason'],'Pembaruan nama petugas.')
        self.assertEqual(set(event.before['permission_ids']),old_ids)
        self.assertEqual(event.after['permission_ids'],[read_id])


class ClaimConcurrencyTests(TransactionTestCase):
    def test_two_simultaneous_claims_produce_one_current_handler(self):
        call_command('bootstrap_silar',verbosity=0)
        owner=user('concurrent-owner@example.test')
        one=user('one@example.test',role='OPERATOR',perms=OPERATOR_PERMISSIONS)
        two=user('two@example.test',role='OPERATOR',perms=OPERATOR_PERMISSIONS)
        with transaction.atomic(): report,*_=source_chain(owner,official=True)
        barrier=threading.Barrier(2)
        def attempt(person):
            close_old_connections();client=APIClient();client.force_authenticate(user=person);barrier.wait(timeout=10)
            try:return client.post(f'/api/v1/workspace/reports/{report.id}/claim/',{'expected_revision':1},format='json',HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())).status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2)as executor:results=list(executor.map(attempt,[one,two]))
        self.assertEqual(sorted(results),[200,409])
        self.assertEqual(OperatorAssignment.objects.filter(report=report,ended_at__isnull=True).count(),1)
        self.assertEqual(AuditEvent.objects.filter(report=report,action='REPORT_CLAIMED').count(),1)
