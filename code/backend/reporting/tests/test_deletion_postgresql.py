"""Native trigger and delete-versus-submit acceptance; PostgreSQL 16 only."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4
from django.db import connection, connections, IntegrityError, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from common.testing import user
from core.models import Report, HumanVerification, AuditEvent
from core.test_fixtures import source_chain


@skipUnless(connection.vendor=='postgresql','Requires PostgreSQL 16 with real migrations.')
class DraftDeletionLockTests(TransactionTestCase):
    def setUp(self):
        self.owner=user();self.report,_,_,self.card,_=source_chain(self.owner)
        HumanVerification.objects.create(report=self.report,card_version=self.card,reporter=self.owner,confirmed_at=timezone.now())
        self.report.preparation_status='READY';self.report.save()

    def race(self,submit=False):
        gate=Barrier(2);key=str(uuid4());revision=self.report.revision
        def action(index):
            try:
                client=APIClient();client.force_authenticate(User.objects.get(pk=self.owner.id));gate.wait(timeout=10)
                if submit and index:
                    response=client.post(f'/api/v1/reports/{self.report.id}/submit/',{'card_version_id':str(self.card.id),'expected_revision':revision},format='json',HTTP_IDEMPOTENCY_KEY=str(uuid4()))
                else:
                    response=client.delete(f'/api/v1/reports/{self.report.id}/',{'expected_revision':revision},format='json',HTTP_IDEMPOTENCY_KEY=key)
                return response.status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(action,[0,1]))

    def test_same_key_concurrent_delete_has_one_audit(self):
        self.assertEqual(self.race(),[200,200])
        self.assertEqual(AuditEvent.objects.filter(report=self.report,action='REPORT_DELETED').count(),1)

    def test_delete_and_submit_cannot_both_commit(self):
        result=self.race(submit=True);self.assertEqual(result.count(200),1,result)
        self.report.refresh_from_db()
        self.assertNotEqual(bool(self.report.deleted_at),bool(self.report.submitted_at))

    def test_raw_sql_cannot_restore_or_change_a_deleted_report(self):
        client=APIClient();client.force_authenticate(self.owner)
        response=client.delete(f'/api/v1/reports/{self.report.id}/',{'expected_revision':self.report.revision},format='json',HTTP_IDEMPOTENCY_KEY=str(uuid4()))
        self.assertEqual(response.status_code,200,response.data)
        for values in [{'deleted_at':None,'deleted_by':None},{'revision':self.report.revision+2}]:
            with self.assertRaises(IntegrityError),transaction.atomic():Report.objects.filter(pk=self.report.pk).update(**values)
