"""Read-only list filters; also runnable against the PostgreSQL acceptance database."""
from django.test import TestCase
from rest_framework.test import APIClient

from common.testing import user
from core.models import AnalysisRun, AuditEvent, IdempotencyRecord, Report
from core.test_fixtures import source_chain


class ReporterListFilterTests(TestCase):
    def setUp(self):
        self.owner = user()
        self.other = user(email='other-list@example.test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.examples = {}
        for category in ('FLOOD', 'EARTHQUAKE', 'FIRE', 'ACCIDENT'):
            self.examples[category] = source_chain(self.owner, category=category)[0]
        self.draft = Report.objects.create(owner=self.owner)
        self.non_event = source_chain(self.owner, category='NON_EVENT')[0]
        self.official = source_chain(self.owner, category='EARTHQUAKE', official=True)[0]
        self.foreign = source_chain(self.other, category='EARTHQUAKE')[0]

    def get(self, **params):
        return self.client.get('/api/v1/reports/', {'scope': 'owned', **params})

    def test_all_four_categories_include_earthquake_and_keep_ownership(self):
        for category in self.examples:
            with self.subTest(category=category):
                response = self.get(event_type=category)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(response.data['results'])
                self.assertTrue(all(item['event_type'] == category for item in response.data['results']))
                ids = {item['id'] for item in response.data['results']}
                self.assertIn(str(self.examples[category].id), ids)
                self.assertNotIn(str(self.foreign.id), ids)

    def test_category_filters_before_count_and_pagination(self):
        for _ in range(4):
            source_chain(self.owner, category='FIRE')
        response = self.get(event_type='FIRE', page_size=2, ordering='created_at')
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('event_type=FIRE', response.data['next'])
        second = self.get(event_type='FIRE', page_size=2, ordering='created_at', page=2)
        self.assertEqual(second.data['count'], 5)
        self.assertTrue(all(item['event_type'] == 'FIRE' for item in second.data['results']))
        self.assertFalse({item['id'] for item in response.data['results']} & {item['id'] for item in second.data['results']})

    def test_category_preparation_and_workflow_combine(self):
        response = self.get(event_type='EARTHQUAKE', preparation_status='AWAITING_CONFIRMATION', workflow_status='NOT_SUBMITTED')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.examples['EARTHQUAKE'].id))
        submitted = self.get(event_type='EARTHQUAKE', preparation_status='READY', workflow_status='SUBMITTED')
        self.assertEqual(submitted.data['count'], 1)
        self.assertEqual(submitted.data['results'][0]['id'], str(self.official.id))

    def test_unclassified_covers_missing_card_and_json_null(self):
        response = self.get(event_type='UNCLASSIFIED')
        self.assertEqual({item['id'] for item in response.data['results']}, {str(self.draft.id), str(self.non_event.id)})
        self.assertTrue(all(item['event_type'] is None for item in response.data['results']))
        self.assertEqual(self.get(event_type='UNCLASSIFIED', preparation_status='BLOCKED').data['count'], 1)

    def test_bad_filter_is_rejected_without_treating_non_event_as_category(self):
        for params in ({'event_type': 'NON_EVENT'}, {'event_type': 'INVALID'}, {'event_type': ''}, {'preparation_status': 'DONE'}):
            with self.subTest(params=params):
                response = self.get(**params)
                self.assertEqual(response.status_code, 400, response.data)
                self.assertEqual(response.data['error']['code'], 'INVALID_PAYLOAD')

    def test_official_projection_is_returned_and_detail_is_read_only(self):
        response = self.get(workflow_status='SUBMITTED', event_type='EARTHQUAKE')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['event_type'], self.official.official_card_version.data['event_type'])
        before = (AnalysisRun.objects.count(), AuditEvent.objects.count(), IdempotencyRecord.objects.count())
        revision = self.official.revision
        for _ in range(2):
            self.assertEqual(self.get(event_type='EARTHQUAKE').status_code, 200)
            detail = self.client.get(f'/api/v1/reports/{self.official.id}/')
            self.assertEqual(detail.status_code, 200, detail.data)
            self.assertEqual(detail.data['data']['official_card']['id'], str(self.official.official_card_version_id))
            self.assertIn('no-store', detail.headers.get('Cache-Control', ''))
        self.official.refresh_from_db()
        self.assertEqual(self.official.revision, revision)
        self.assertEqual(before, (AnalysisRun.objects.count(), AuditEvent.objects.count(), IdempotencyRecord.objects.count()))
