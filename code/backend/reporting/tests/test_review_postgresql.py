"""Run with config.test_settings and PostgreSQL 16; never a SQLite lock claim."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import SkipTest, skipUnless
import uuid

from django.db import connection, connections, IntegrityError, transaction
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from accounts.models import User
from common.testing import user
from core.models import AuditEvent, HumanVerification, IncidentCardVersion, Notification
from core.test_fixtures import source_chain


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL 16 and real migrations.')
class ReporterLockTests(TransactionTestCase):
    def setUp(self):
        if connection.pg_version // 10000 != 16:
            raise SkipTest('SLR12 transaction acceptance requires PostgreSQL major 16.')
        self.owner = user()
        self.report, _, _, self.card, _ = source_chain(self.owner)

    def api_client(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(pk=self.owner.id))
        return client

    def parallel(self, endpoint, body, same_key=False):
        gate = Barrier(2)
        common = uuid.uuid4()
        def execute(index):
            try:
                client = self.api_client()
                gate.wait(timeout=10)
                response = client.post(f'/api/v1/reports/{self.report.id}/{endpoint}/', body, format='json',
                    HTTP_IDEMPOTENCY_KEY=str(common if same_key else uuid.uuid4()))
                return response.status_code, response.get('Idempotency-Replayed')
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as executor:
            jobs = [executor.submit(execute, index) for index in range(2)]
            return [job.result(timeout=20) for job in jobs]

    def confirm(self):
        response = self.api_client().post(f'/api/v1/reports/{self.report.id}/human-verifications/',
            {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision},
            format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 201, response.data)
        self.report.refresh_from_db()

    def test_parallel_card_revisions_have_one_winner(self):
        results = self.parallel('cards/revisions', {'parent_id': str(self.card.id),
            'patch': {'location_text': 'Lokasi revisi'}, 'expected_revision': self.report.revision})
        self.assertEqual(sorted(status for status, _ in results), [201, 409])
        self.assertEqual(IncidentCardVersion.objects.count(), 2)

    def test_parallel_confirmations_do_not_duplicate(self):
        results = self.parallel('human-verifications', {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision})
        self.assertEqual(sorted(status for status, _ in results), [201, 409])
        self.assertEqual(HumanVerification.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='HUMAN_VERIFIED').count(), 1)

    def test_parallel_submit_different_keys_have_one_winner(self):
        self.confirm()
        results = self.parallel('submit', {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision})
        self.assertEqual(sorted(status for status, _ in results), [200, 409])
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='REPORT_SUBMITTED').count(), 1)

    def test_parallel_submit_same_key_replays_after_commit(self):
        self.confirm()
        results = self.parallel('submit', {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision}, same_key=True)
        self.assertEqual([status for status, _ in results], [200, 200])
        self.assertEqual(sum(replayed == 'true' for _, replayed in results), 1)
        self.assertEqual(Notification.objects.count(), 1)

    def test_official_source_is_locked_by_database(self):
        self.confirm()
        response = self.api_client().post(f'/api/v1/reports/{self.report.id}/submit/',
            {'card_version_id': str(self.card.id), 'expected_revision': self.report.revision},
            format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 200, response.data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('UPDATE core_report SET official_card_version_id=NULL, submitted_at=NULL WHERE id=%s', [self.report.id])
