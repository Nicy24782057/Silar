import json,tempfile,uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connection,transaction,IntegrityError,DatabaseError
from django.http import Http404
from django.test import TestCase,TransactionTestCase,override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from common.api import ApiProblem
from common.testing import user
from accounts.models import Role,User
from accounts.services import issue_tokens
from .models import *
from .permissions import *
from .audit import record_event
from .mutations import atomic_mutation,MutationResult
from .capacity import analysis_slot,create_reserved_run,fail_known_run
from .storage import PrivateMediaStorage,store_validated_media,private_media_response
from .test_fixtures import source_chain,extraction
from .validators import nara_data,card_data,public_data,normalization_warnings

class FoundationTests(TestCase):
    @classmethod
    def setUpTestData(cls):call_command('bootstrap_silar',verbosity=0)
    def setUp(self):self.owner=user()

    def test_postgresql_16_is_actual_test_engine(self):
        self.assertEqual(connection.vendor,'postgresql')
        with connection.cursor() as cursor:
            cursor.execute('SHOW server_version_num');self.assertEqual(int(cursor.fetchone()[0])//10000,16)

    def test_version_number_uniqueness_is_database_enforced(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():
            NarrativeVersion.objects.create(report=report,bundle=bundle,version_number=1,text='Berbeda',origin='REPORTER_REVISION',created_by=self.owner)

    def test_sena_nara_are_one_per_run(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():
            SENAResult.objects.create(analysis_run=run,narrative=card.narrative,category='FLOOD',confidence='.7',model_version='duplicate')

    def test_json_shape_and_category_separation(self):
        nara_data(extraction());card_data(dict(event_type='FLOOD',**extraction()))
        with self.assertRaises(ValidationError):nara_data(dict(event_type='FLOOD',**extraction()))
        with self.assertRaises(ValidationError):card_data(dict(event_type='OTHER',**extraction()))
        self.assertEqual(extraction()['victims'],[])

    def test_nara_warnings_preserve_adapter_metadata_without_category(self):
        normalization_warnings([{'code':'EXTRACTION_AMBIGUITY','field':'time_text'}])
        for value in ([{'code':'EXTRACTION_AMBIGUITY','field':['bad']}],[{'code':'X','field':'event_type'}],{}):
            with self.subTest(value=value),self.assertRaises(ValidationError):normalization_warnings(value)
        report,bundle,run,card,evidence=source_chain(self.owner)
        self.assertEqual(card.nara_result.normalization_warnings,[])

    def test_unknown_fields_and_naive_event_time_are_rejected(self):
        data=extraction();data['occurred_at']='2026-10-17T10:00:00'
        with self.assertRaises(ValidationError):nara_data(data)

    def test_impossible_calendar_date_is_a_validation_error(self):
        data=extraction();data['occurred_at']='2026-02-31T10:00:00Z'
        with self.assertRaises(ValidationError):nara_data(data)
        data['occurred_at']='2026-10-17T10:00:00Z';nara_data(data)
        data['extra']='hidden'
        with self.assertRaises(ValidationError):nara_data(data)

    def test_public_allowlist_does_not_allow_private_fields(self):
        data={'event_type':'FLOOD','summary':'Banjir dilaporkan.','general_location':None,'time_text':None,
              'occurred_at':None,'general_impact':None,'handling_update':None}
        public_data(data)
        data['reporter_email']='private@example.test'
        with self.assertRaises(ValidationError):public_data(data)

    def test_cross_report_reference_is_rejected(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        with self.assertRaises(ValidationError):Report.objects.create(owner=self.owner,active_bundle=bundle)

    def test_history_cannot_be_updated_by_orm_or_raw_sql(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        with self.assertRaises(ValidationError):EvidenceItem.objects.filter(pk=evidence.pk).update(text_content='Ganti')
        with self.assertRaises(ValidationError):evidence.delete()
        with self.assertRaises(IntegrityError),transaction.atomic():
            with connection.cursor() as cursor:cursor.execute('UPDATE core_evidenceitem SET text_content=%s WHERE id=%s',['Ganti',evidence.id])

    def test_json_type_constraint_blocks_raw_sql_bypass(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():
            with connection.cursor() as cursor:cursor.execute("UPDATE core_analysisrun SET execution_context='[]'::jsonb WHERE id=%s",[run.id])

    def test_submitted_source_is_locked_in_database(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        with self.assertRaises(IntegrityError),transaction.atomic():Report.objects.filter(pk=report.id).update(input_revision=2)

    def test_closed_report_is_terminal(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        report.workflow_status='CLOSED';report.closed_at=timezone.now();report.closed_by=self.owner;report.closure_note='Selesai';report.save()
        with self.assertRaises(IntegrityError),transaction.atomic():Report.objects.filter(pk=report.id).update(workflow_status='IN_REVIEW')

    def test_unknown_holds_global_slot_and_report_reservation(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        run.status='UNKNOWN';run.finished_at=None;run.save()
        other=Report.objects.create(owner=self.owner)
        ledger=IdempotencyRecord.objects.create(actor=self.owner,report=other,key=uuid.uuid4(),scope='other',request_hash='c'*64)
        with self.assertRaises(IntegrityError),transaction.atomic():
            # bulk_create deliberately bypasses model clean to exercise the DB partial unique index.
            AnalysisRun.objects.bulk_create([AnalysisRun(report=other,bundle=bundle,input_revision=1,request_record=ledger,
                mode='EVIDENCE',route='T',started_at=timezone.now(),capacity_slot=1)])
        with override_settings(ANALYSIS_CAPACITY=2):
            ledger2=IdempotencyRecord.objects.create(actor=self.owner,report=report,key=uuid.uuid4(),scope='same',request_hash='d'*64)
            with self.assertRaises(IntegrityError),transaction.atomic():
                AnalysisRun.objects.create(report=report,bundle=bundle,input_revision=1,request_record=ledger2,
                    mode='EVIDENCE',route='T',started_at=timezone.now(),capacity_slot=2)

    def test_one_active_assignment_preserves_ended_history(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        op=user('op@example.test',role=Role.OPERATOR)
        first=OperatorAssignment.objects.create(report=report,operator=op,assigned_by=op,source='SELF_CLAIM',started_at=timezone.now())
        with self.assertRaises(IntegrityError),transaction.atomic():
            OperatorAssignment.objects.create(report=report,operator=op,assigned_by=op,source='SELF_CLAIM',started_at=timezone.now())
        first.ended_at=timezone.now();first.save()
        OperatorAssignment.objects.create(report=report,operator=op,assigned_by=op,source='SELF_CLAIM',started_at=timezone.now())
        self.assertEqual(report.assignments.count(),2)

    def test_assignment_identity_and_ledger_history_cannot_be_rewritten(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        op=user('op@example.test',role=Role.OPERATOR)
        assignment=OperatorAssignment.objects.create(report=report,operator=op,assigned_by=op,source='SELF_CLAIM',started_at=timezone.now())
        with self.assertRaises(IntegrityError),transaction.atomic():OperatorAssignment.objects.filter(pk=assignment.id).update(reason='Ganti riwayat')
        with self.assertRaises(IntegrityError),transaction.atomic():IdempotencyRecord.objects.filter(pk=run.request_record_id).delete()

    def test_analysis_enums_are_database_constraints(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        for field in ('route','stage'):
            with self.subTest(field=field),self.assertRaises(IntegrityError),transaction.atomic():
                AnalysisRun.objects.filter(pk=run.id).update(**{field:'INVALID'})

    def test_publication_content_requires_new_version_and_closed_rejects_candidates(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        data={'event_type':'FLOOD','summary':'Banjir dilaporkan.','general_location':None,'time_text':None,
              'occurred_at':None,'general_impact':None,'handling_update':None}
        candidate=PublicationVersion.objects.create(report=report,card_version=card,version_number=1,data=data,sanitized_by=self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():PublicationVersion.objects.filter(pk=candidate.id).update(data=dict(data,summary='Diubah'))
        with self.assertRaises(IntegrityError),transaction.atomic():PublicationVersion.objects.filter(pk=candidate.id).update(state='PUBLISHED',approved_by=self.owner,approved_at=timezone.now(),published_by=self.owner,published_at=timezone.now())
        report.workflow_status='CLOSED';report.closed_at=timezone.now();report.closed_by=self.owner;report.closure_note='Selesai';report.save()
        with self.assertRaises(IntegrityError),transaction.atomic():
            PublicationVersion.objects.create(report=report,card_version=card,version_number=2,data=data,sanitized_by=self.owner)

    def test_admin_and_superuser_do_not_inherit_operator_actions(self):
        admin=user('admin@example.test',role=Role.ADMIN,perms=ADMIN_PERMISSIONS)
        admin.is_superuser=True;admin.save()
        self.assertFalse(set(OPERATOR_PERMISSIONS)&effective_permissions(admin))
        with self.assertRaises(ApiProblem):require_operator(admin,'review_report')

    def test_owner_assignment_monitoring_and_private_access_scopes(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        stranger=user('other@example.test')
        admin=user('admin@example.test',role=Role.ADMIN,perms=['monitor_report'])
        operator=user('op@example.test',role=Role.OPERATOR,perms=['view_assigned_report','review_report'])
        self.assertTrue(can_read_report(self.owner,report,True));self.assertFalse(can_read_report(stranger,report,True))
        self.assertTrue(can_read_report(admin,report));self.assertFalse(can_read_report(admin,report,True))
        self.assertFalse(can_read_report(operator,report,True))
        OperatorAssignment.objects.create(report=report,operator=operator,assigned_by=operator,source='SELF_CLAIM',started_at=timezone.now())
        self.assertTrue(can_read_report(operator,report,True))
        require_handler(operator,report,'review_report')
        admin.user_permissions.add(permission_queryset().get(codename='view_private_evidence'))
        self.assertTrue(can_read_report(admin,report,True))
        draft=Report.objects.create(owner=self.owner);self.assertFalse(can_read_report(admin,draft,True))

    def test_audit_is_in_same_transaction_and_whitelisted(self):
        with self.assertRaises(ValueError):record_event(actor=self.owner,action='BAD',object_type='User',after={'password':'never'})
        count=AuditEvent.objects.count()
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                record_event(actor=self.owner,action='ROLLBACK',object_type='User')
                raise RuntimeError('rollback')
        self.assertEqual(AuditEvent.objects.count(),count)
        audit=record_event(actor=self.owner,action='TEST',object_type='User',after={'is_active':True})
        with self.assertRaises(IntegrityError),transaction.atomic():
            with connection.cursor() as cursor:cursor.execute('DELETE FROM core_auditevent WHERE id=%s',[audit.id])

    def test_audit_read_requires_explicit_admin_permission(self):
        admin=user('admin@example.test',role=Role.ADMIN,perms=['view_audit'])
        audit=record_event(actor=self.owner,action='TEST',object_type='User',object_id=self.owner.id)
        client=APIClient();client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_tokens(admin)[0])
        response=client.get('/api/v1/admin/audit/?action=TEST')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['count'],1)
        self.assertEqual(set(response.json()['results'][0]),{'id','created_at','actor_id','actor_role','report_id','action','object_type','object_id','before','after','request_id'})
        admin.user_permissions.clear()
        self.assertEqual(client.get('/api/v1/admin/audit/').status_code,403)

    def test_admin_handling_uses_operator_role_snapshot(self):
        report,bundle,run,card,evidence=source_chain(self.owner,official=True)
        admin=user('admin@example.test',role=Role.ADMIN,perms=['view_assigned_report','review_report'])
        with self.assertRaises(ValueError):record_event(actor=admin,action='REVIEWED',object_type='Report',report=report,acting_role='OPERATOR')
        OperatorAssignment.objects.create(report=report,operator=admin,assigned_by=admin,source='SELF_CLAIM',started_at=timezone.now())
        event=record_event(actor=admin,action='REVIEWED',object_type='Report',report=report,acting_role='OPERATOR')
        self.assertEqual(event.actor_role,'OPERATOR')

    def mutation(self,report,key,authorize=require_owner_draft,payload=None,revision=None,apply=None):
        def commit(actor,current):
            current.revision+=1;current.save()
            record_event(actor=actor,action='TEST_MUTATION',object_type='Report',object_id=current.id,report=current,after={'revision':current.revision})
            return MutationResult({'data':{'revision':current.revision}},200,'Report',current.id)
        return atomic_mutation(actor=self.owner,key=key,scope='test.mutation',payload=payload or {'expected_revision':1},
            authorize=authorize,apply=apply or commit,report_id=report.id,expected_revision=revision if revision is not None else 1)

    def test_idempotent_replay_returns_frozen_result_before_revision_check(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4()
        first=self.mutation(report,key)
        Report.objects.filter(pk=report.id).update(revision=9)
        second=self.mutation(report,key)
        self.assertTrue(second.replayed);self.assertEqual(first.payload,second.payload)
        self.assertEqual(AuditEvent.objects.filter(action='TEST_MUTATION').count(),1)

    def test_idempotency_mismatch_and_revision_conflict(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4();self.mutation(report,key)
        with self.assertRaises(ApiProblem) as error:self.mutation(report,key,payload={'changed':True})
        self.assertEqual(error.exception.error_code,'IDEMPOTENCY_MISMATCH')
        other=Report.objects.create(owner=self.owner)
        with self.assertRaises(ApiProblem) as error:self.mutation(other,key)
        self.assertEqual(error.exception.error_code,'IDEMPOTENCY_MISMATCH')
        with self.assertRaises(ApiProblem) as error:self.mutation(report,uuid.uuid4())
        self.assertEqual(error.exception.error_code,'REVISION_CONFLICT')

    def test_authorization_precedes_idempotency_replay(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4();self.mutation(report,key)
        def denied(actor,current):raise ApiProblem('PERMISSION_DENIED','Dicabut',403)
        with self.assertRaises(ApiProblem) as error:self.mutation(report,key,authorize=denied)
        self.assertEqual(error.exception.error_code,'PERMISSION_DENIED')

    def test_expired_key_is_retained_and_cannot_be_reused(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4();self.mutation(report,key)
        IdempotencyRecord.objects.filter(key=key).update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(ApiProblem) as error:self.mutation(report,key)
        self.assertEqual(error.exception.error_code,'IDEMPOTENCY_EXPIRED')
        self.assertTrue(IdempotencyRecord.objects.filter(key=key).exists())

    def test_unknown_request_cannot_auto_retry(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4();self.mutation(report,key)
        IdempotencyRecord.objects.filter(key=key).update(state='UNKNOWN',expires_at=None)
        with self.assertRaises(ApiProblem) as error:self.mutation(report,key)
        self.assertEqual(error.exception.error_code,'REQUEST_UNKNOWN')

    def test_mutation_failure_rolls_back_resource_and_ledger(self):
        report=Report.objects.create(owner=self.owner);key=uuid.uuid4()
        def crash(actor,current):
            current.revision=8;current.save();raise RuntimeError('simulated')
        with self.assertRaises(RuntimeError):self.mutation(report,key,apply=crash)
        report.refresh_from_db();self.assertEqual(report.revision,1)
        self.assertFalse(IdempotencyRecord.objects.filter(key=key).exists())

    def test_ledger_never_stores_credentials(self):
        report=Report.objects.create(owner=self.owner)
        with self.assertRaises(ValueError):self.mutation(report,uuid.uuid4(),payload={'nested':{'password':'never'}})

    def test_reservation_and_failure_are_token_fenced(self):
        report,bundle,old,card,evidence=source_chain(self.owner)
        run=create_reserved_run(actor=self.owner,report_id=report.id,bundle_id=bundle.id,input_revision=1,
            expected_revision=report.revision,key=uuid.uuid4(),mode='EVIDENCE',route='T',slot=1)
        report.refresh_from_db();self.assertEqual(report.preparation_status,'PROCESSING');self.assertIsNone(report.current_card_version_id)
        with self.assertRaises(ApiProblem):fail_known_run(run.id,uuid.uuid4())
        run=fail_known_run(run.id,run.execution_token)
        self.assertEqual(run.status,'FAILED')
        ledger=IdempotencyRecord.objects.get(pk=run.request_record_id)
        self.assertEqual(ledger.state,'FAILED');self.assertIsNotNone(ledger.response_payload)

    def test_private_media_has_no_public_url_and_requires_report_access(self):
        report,bundle,run,card,text=source_chain(self.owner)
        with tempfile.TemporaryDirectory() as directory,override_settings(PRIVATE_MEDIA_ROOT=Path(directory)):
            key=store_validated_media(ContentFile(b'fixture-only'))
            evidence=EvidenceItem.objects.create(report=report,type='IMAGE',file_key=key,original_name='bukti.png',mime_type='image/png',
                byte_size=12,sha256='e'*64,uploaded_by=self.owner)
            with self.assertRaises(NotImplementedError):PrivateMediaStorage().url(key)
            response=private_media_response(self.owner,evidence)
            self.assertEqual(response['Cache-Control'],'no-store')
            # Direct helper unit test: response.close normally emits end-of-HTTP
            # signals that would close TestCase's outer database transaction.
            with patch('django.http.response.signals.request_finished.send'):response.close()
            with self.assertRaises(Http404):private_media_response(user('stranger@example.test'),evidence)

    def test_health_checks_database_without_claiming_ai_ready(self):
        response=APIClient().get('/health/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['data']['postgresql_major'],16)
        self.assertNotIn('ai',response.json()['data'])

class DatabaseTransactionTests(TransactionTestCase):
    def setUp(self):self.owner=user()

    def test_empty_bundle_cannot_commit(self):
        report=Report.objects.create(owner=self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():
            EvidenceBundle.objects.create(report=report,version_number=1,source_digest='a'*64,created_by=self.owner)
        self.assertEqual(EvidenceBundle.objects.count(),0)

    def test_committed_bundle_cannot_gain_members(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        extra=EvidenceItem.objects.create(report=report,type='TEXT',text_content='Tambahan',byte_size=8,sha256='e'*64,uploaded_by=self.owner)
        with self.assertRaises(IntegrityError),transaction.atomic():
            EvidenceBundleItem.objects.create(bundle=bundle,evidence=extra,position=2)

    def test_audit_requires_atomic_block(self):
        with self.assertRaises(RuntimeError):record_event(actor=self.owner,action='NO_TRANSACTION',object_type='User')

    def test_dedicated_session_lock_rejects_parallel_slot_and_releases(self):
        with analysis_slot() as slot:
            self.assertEqual(slot,1)
            with self.assertRaises(ApiProblem) as error:
                with analysis_slot():self.fail('Parallel lock accepted')
            self.assertEqual(error.exception.error_code,'CAPACITY_BUSY')
        with analysis_slot() as slot:self.assertEqual(slot,1)

    def test_unknown_reservation_still_blocks_slot_after_session_lost(self):
        report,bundle,run,card,evidence=source_chain(self.owner)
        run.status='UNKNOWN';run.finished_at=None;run.save()
        with self.assertRaises(ApiProblem) as error:
            with analysis_slot():self.fail('UNKNOWN reservation ignored')
        self.assertEqual(error.exception.error_code,'CAPACITY_BUSY')
