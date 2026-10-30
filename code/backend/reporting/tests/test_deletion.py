"""Owner-only logical deletion; no evidence or history is physically removed."""
from uuid import uuid4
from datetime import timedelta
from unittest.mock import patch
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from common.testing import user
from core.models import Report, AuditEvent, IdempotencyRecord, EvidenceItem
from core.test_fixtures import source_chain


class DraftDeletionTests(TestCase):
    def setUp(self):
        self.owner=user();self.other=user('other-delete@example.test')
        self.client=APIClient();self.client.force_authenticate(self.owner)
        self.report,self.bundle,self.run,self.card,self.evidence=source_chain(self.owner)

    def remove(self,report=None,key=None,body=None):
        report=report or self.report
        return self.client.delete(f'/api/v1/reports/{report.id}/',
            body if body is not None else {'expected_revision':report.revision},format='json',HTTP_IDEMPOTENCY_KEY=str(key or uuid4()))

    def test_owner_deletes_only_draft_and_retains_all_evidence_and_history(self):
        before=EvidenceItem.objects.count()
        result=self.remove();self.assertEqual(result.status_code,200,result.data)
        self.report.refresh_from_db();self.assertIsNotNone(self.report.deleted_at)
        self.assertEqual(self.report.deleted_by_id,self.owner.id)
        self.assertEqual(EvidenceItem.objects.count(),before)
        self.assertTrue(self.report.card_versions.exists())
        self.assertEqual(AuditEvent.objects.filter(report=self.report,action='REPORT_DELETED').count(),1)
        self.assertNotIn(str(self.report.id),[x['id'] for x in self.client.get('/api/v1/reports/?scope=owned').data['results']])

    def test_foreign_owner_cannot_delete_even_with_forged_id_and_revision(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.remove().status_code,404)
        self.report.refresh_from_db();self.assertIsNone(self.report.deleted_at)
        self.assertFalse(AuditEvent.objects.filter(action='REPORT_DELETED').exists())

    def test_anonymous_operator_and_admin_cannot_delete(self):
        for actor in [None,user('delete-op@example.test',role='OPERATOR'),user('delete-admin@example.test',role='ADMIN')]:
            self.client.force_authenticate(actor)
            self.assertIn(self.remove().status_code,[401,403])
        self.report.refresh_from_db();self.assertIsNone(self.report.deleted_at)

    def test_submitted_report_is_rejected(self):
        report,*_=source_chain(self.owner,official=True)
        self.assertEqual(self.remove(report).status_code,422)
        report.refresh_from_db();self.assertIsNone(report.deleted_at)

    def test_stale_revision_does_not_delete_or_write_a_ledger(self):
        self.assertEqual(self.remove(body={'expected_revision':self.report.revision+1}).status_code,409)
        self.report.refresh_from_db();self.assertIsNone(self.report.deleted_at)
        self.assertFalse(IdempotencyRecord.objects.filter(scope__startswith='DELETE').exists())

    def test_exact_replay_returns_original_result_and_one_audit(self):
        key=uuid4();body={'expected_revision':self.report.revision}
        first=self.remove(key=key,body=body);second=self.remove(key=key,body=body)
        self.assertEqual(first.status_code,200,first.data)
        self.assertEqual(first.data,second.data);self.assertEqual(second['Idempotency-Replayed'],'true')
        self.assertEqual(AuditEvent.objects.filter(action='REPORT_DELETED').count(),1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.remove(key=key,body=body).status_code,404)
        self.client.force_authenticate(self.owner)
        ledger=IdempotencyRecord.objects.get(actor=self.owner,key=key)
        ledger.expires_at=timezone.now()-timedelta(seconds=1);ledger.save()
        expired=self.remove(key=key,body=body)
        self.assertEqual(expired.status_code,409)
        self.assertEqual(expired.data['error']['code'],'IDEMPOTENCY_EXPIRED')
        self.assertEqual(AuditEvent.objects.filter(action='REPORT_DELETED').count(),1)

    def test_deleted_report_and_its_versions_media_runs_and_requests_are_unreadable(self):
        self.assertEqual(self.remove().status_code,200)
        base=f'/api/v1/reports/{self.report.id}'
        for path in [base+'/',base+'/evidence/',base+'/versions/',base+'/history/',
                     base+f'/versions/IncidentCardVersion/{self.card.id}/',
                     base+f'/analysis-runs/{self.run.id}/',
                     f'/api/v1/requests/{self.run.request_record.key}/',
                     f'/api/v1/evidence/{self.evidence.id}/media/']:
            self.assertEqual(self.client.get(path).status_code,404,path)
        self.assertFalse(any(row['report_id']==str(self.report.id) for row in self.client.get('/api/v1/requests/?include_expired=true').data['results']))
        response=self.client.post(base+'/human-verifications/',{'card_version_id':str(self.card.id),'expected_revision':self.report.revision},format='json',HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        self.assertEqual(response.status_code,404)

    def test_running_or_unknown_analysis_blocks_deletion(self):
        for state in ['RUNNING','UNKNOWN']:
            self.run.status=state;self.run.finished_at=None;self.run.save()
            self.assertEqual(self.remove().status_code,409)
        self.report.refresh_from_db();self.assertIsNone(self.report.deleted_at)

    def test_audit_failure_rolls_back_deletion_revision_and_ledger(self):
        self.client.raise_request_exception=False;revision=self.report.revision
        with patch('reporting.services.record_event',side_effect=RuntimeError('audit unavailable')):
            self.assertEqual(self.remove().status_code,500)
        self.report.refresh_from_db();self.assertIsNone(self.report.deleted_at)
        self.assertEqual(self.report.revision,revision)
        self.assertFalse(IdempotencyRecord.objects.filter(scope__startswith='DELETE').exists())

    def test_raw_update_cannot_mark_a_submitted_report_or_wrong_owner_deleted(self):
        submitted,*_=source_chain(self.owner,official=True)
        for obj,who in [(self.report,self.other),(submitted,self.owner),(self.report,None)]:
            with self.assertRaises(IntegrityError),transaction.atomic():
                Report.objects.filter(pk=obj.pk).update(deleted_at=timezone.now(),deleted_by=who)

    def test_invalid_body_unknown_fields_and_missing_key_are_rejected(self):
        for body in [{},{'expected_revision':0},{'expected_revision':1,'owner':str(self.other.id)}]:
            self.assertEqual(self.remove(body=body).status_code,400)
        self.assertEqual(self.client.delete(f'/api/v1/reports/{self.report.id}/',{'expected_revision':1},format='json').status_code,400)
