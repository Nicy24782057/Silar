"""SLR12 -> SLR11 integration with explicit neural/provider doubles."""
import os
from unittest.mock import MagicMock, patch
import uuid

from django.db import connection
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ai_pipeline.tests.test_database import ControlledRuntime
from ai_pipeline.tests.test_reporting_integration import component_capacity
from common.testing import user
from core.test_fixtures import source_chain


class NarrativeReviewIntegrationTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor == 'sqlite':
            if os.getenv('SILAR_ALLOW_COMPONENT_DB') != '1':
                raise RuntimeError('Use PostgreSQL 16 or explicit component settings.')
            capacity = patch('ai_pipeline.services.analysis_slot', component_capacity)
            capacity.start();self.addCleanup(capacity.stop)
        self.owner = user()
        self.client = APIClient();self.client.force_authenticate(user=self.owner)
        self.report, _, _, self.card, _ = source_chain(self.owner, channels='TAI')
        self.runtime = ControlledRuntime()
        self.whisper = MagicMock();self.gemini = MagicMock()
        self.factories = {}
        for name, value in [('reviewed_runtime', self.runtime), ('whisper_client', self.whisper), ('GeminiClient', self.gemini)]:
            replacement = patch('ai_pipeline.pipeline.'+name, return_value=value)
            self.factories[name] = replacement.start();self.addCleanup(replacement.stop)

    def post(self, endpoint, payload):
        return self.client.post(f'/api/v1/reports/{self.report.id}/{endpoint}/', payload,
            format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))

    def analyze_revision(self):
        response = self.post('narratives/revisions', {'parent_id': str(self.card.narrative_id),
            'text': 'Air meluap di Jalan Melati.', 'expected_revision': self.report.revision})
        self.assertEqual(response.status_code, 201, response.data)
        report = response.data['data']['report']
        result = self.post('analyses', {'mode': 'NARRATIVE_REVISION', 'bundle_id': report['active_bundle_id'],
            'narrative_id': report['active_narrative_id'], 'input_revision': report['input_revision'], 'expected_revision': report['revision']})
        self.assertEqual(result.status_code, 201, result.data)
        self.factories['whisper_client'].assert_not_called();self.factories['GeminiClient'].assert_not_called()
        self.whisper.transcribe.assert_not_called();self.gemini.narrative.assert_not_called()
        self.assertEqual([name for name, _ in self.runtime.calls], ['SENA', 'NARA', 'FUSION'])
        self.assertEqual(self.runtime.calls[0], ('SENA', 'Air meluap di Jalan Melati.'))
        self.report.refresh_from_db()
        self.assertEqual(self.report.analysis_runs.order_by('-created_at','-id').first().route, 'TAI')
        return result

    def test_revised_narrative_runs_only_sena_nara_fusion_then_can_confirm_and_submit(self):
        self.analyze_revision()
        newer = self.report.current_card_version
        self.assertNotEqual(newer.id, self.card.id)
        self.assertEqual(newer.narrative.origin, 'REPORTER_REVISION')
        self.assertNotEqual(newer.sena_result_id, self.card.sena_result_id)
        self.assertEqual(newer.narrative_id, self.report.active_narrative_id)
        response = self.post('human-verifications', {'card_version_id': str(newer.id), 'expected_revision': self.report.revision})
        self.assertEqual(response.status_code, 201, response.data)
        response = self.post('submit', {'card_version_id': str(newer.id), 'expected_revision': response.data['data']['report']['revision']})
        self.assertEqual(response.status_code, 200, response.data)

    def test_non_event_after_reanalysis_still_blocks_confirmation(self):
        self.runtime.label = 'NON_EVENT'
        self.analyze_revision()
        self.assertEqual(self.report.preparation_status, 'BLOCKED')
        result = self.post('human-verifications', {'card_version_id': str(self.report.current_card_version_id),
            'expected_revision': self.report.revision})
        self.assertEqual(result.status_code, 422, result.data)
        self.assertEqual(result.data['error']['code'], 'NON_EVENT')
