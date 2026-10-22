"""SLR10 input -> SLR11 service -> stored A6 readers.

Provider/model clients are explicit doubles. On PostgreSQL this uses the real
capacity locks and migrations. Explicit SQLite component mode replaces only the
PostgreSQL capacity context and does not prove triggers or cross-process locks.
"""
from contextlib import contextmanager
from datetime import timedelta
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import uuid

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import PASSWORD, user
from core.models import AnalysisRun, AuditEvent, HumanVerification, IdempotencyRecord, IncidentCardVersion, Report
from ai_pipeline.errors import PipelineFailure, not_ready
from ai_pipeline.output import card_data, narrative_data
from ai_pipeline.tests.test_database import ControlledRuntime


@contextmanager
def component_capacity():
    yield 1


class ReportingAnalysisIntegrationTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor == 'sqlite':
            if os.getenv('SILAR_ALLOW_COMPONENT_DB') != '1':
                raise RuntimeError('SQLite integration requires explicit component mode.')
            guard = patch('ai_pipeline.services.analysis_slot', component_capacity)
            guard.start()
            self.addCleanup(guard.stop)
        self.owner = user()
        self.other = user('other-integration@example.test')
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        config = override_settings(PRIVATE_MEDIA_ROOT=Path(folder.name))
        config.enable()
        self.addCleanup(config.disable)
        self.runtime = ControlledRuntime()
        self.whisper = MagicMock(version='fixture-whisper')
        self.whisper.transcribe.return_value = 'Air meluap di Jalan Melati.'
        self.gemini = MagicMock()
        self.gemini.narrative.return_value = ('Air meluap di Jalan Melati.', {'resolved_model': 'fixture-gemini'})
        for name, value in [('reviewed_runtime', self.runtime), ('whisper_client', self.whisper), ('GeminiClient', self.gemini)]:
            mock = patch('ai_pipeline.pipeline.' + name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def post(self, path, body, *, multipart=False, key=None):
        response = self.client.post(path, body, format='multipart' if multipart else 'json',
                                    HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))
        return response

    def source(self, channels='T'):
        created = self.post('/api/v1/reports/', {})
        self.assertEqual(created.status_code, 201, created.data)
        report = created.data['data']['report']
        evidence = []
        for channel in channels:
            payload = {'expected_revision': report['revision']}
            if channel == 'T':
                payload.update(type='TEXT', text_content='  Air meluap di Jalan Melati.  ')
            elif channel == 'A':
                raw = (Path(__file__).parent / 'fixtures/tone.wav').read_bytes()
                payload.update(type='AUDIO', file=SimpleUploadedFile('tone.wav', raw, 'audio/wav'))
            else:
                stream = BytesIO()
                Image.new('RGB', (8, 8), 'blue').save(stream, format='PNG')
                payload.update(type='IMAGE', file=SimpleUploadedFile('bukti.png', stream.getvalue(), 'image/png'))
            uploaded = self.post(f"/api/v1/reports/{report['id']}/evidence/", payload, multipart=True)
            self.assertEqual(uploaded.status_code, 201, uploaded.data)
            report = uploaded.data['data']['report']
            evidence.append(uploaded.data['data']['object'])
        listed = self.client.get(f"/api/v1/reports/{report['id']}/evidence/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data['count'], len(channels))
        self.assertIsNone(report['active_bundle_id'])
        bundled = self.post(f"/api/v1/reports/{report['id']}/bundles/", {
            'evidence_ids': [item['id'] for item in evidence], 'expected_revision': report['revision'],
        })
        self.assertEqual(bundled.status_code, 201, bundled.data)
        return bundled.data['data']['report'], evidence

    def analyze(self, report, key=None):
        body = {'mode': 'EVIDENCE', 'bundle_id': report['active_bundle_id'],
                'input_revision': report['input_revision'], 'expected_revision': report['revision']}
        key = key or uuid.uuid4()
        return self.post(f"/api/v1/reports/{report['id']}/analyses/", body, key=key), key

    def detail(self, report):
        response = self.client.get(f"/api/v1/reports/{report['id']}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        return response.data['data']

    def test_seven_routes_from_actual_upload_bundle_to_matching_stored_card(self):
        for route in ('T', 'A', 'I', 'TA', 'TI', 'AI', 'TAI'):
            with self.subTest(route=route):
                self.whisper.transcribe.reset_mock()
                self.gemini.narrative.reset_mock()
                report, evidence = self.source(route)
                response, _ = self.analyze(report)
                self.assertEqual(response.status_code, 201, response.data)
                detail = self.detail(report)
                run = detail['latest_run']
                stored = Report.objects.get(pk=report['id'])
                self.assertEqual(run['route'], route)
                self.assertEqual(run['status'], 'SUCCEEDED')
                self.assertEqual(detail['current_card'], card_data(stored.current_card_version))
                self.assertEqual(detail['active_narrative'], narrative_data(stored.active_narrative))
                self.assertEqual(run['nara']['narrative_id'], detail['current_card']['narrative_id'])
                self.assertEqual(run['sena']['id'], detail['current_card']['sena_result_id'])
                self.assertEqual(run['nara']['id'], detail['current_card']['nara_result_id'])
                read = self.client.get(f"/api/v1/reports/{report['id']}/analysis-runs/{run['id']}/")
                self.assertEqual(read.status_code, 200)
                self.assertEqual(read.data['data'], run)
                self.assertEqual(self.whisper.transcribe.call_count, int('A' in route))
                self.assertEqual(self.gemini.narrative.call_count, int('I' in route or len(route) > 1))
                self.assertEqual(stored.workflow_status, 'NOT_SUBMITTED')
                self.assertIsNone(stored.official_card_version_id)
                self.assertFalse(HumanVerification.objects.filter(report=stored).exists())
                self.assertEqual([member['evidence']['id'] for member in detail['active_bundle']['items']],
                                 [item['id'] for item in evidence])

    def test_lost_response_is_recovered_by_reading_request_run_and_report_without_mutation(self):
        report, _ = self.source('TAI')
        completed, key = self.analyze(report)
        self.assertEqual(completed.status_code, 201)
        stored = Report.objects.get(pk=report['id'])
        before = (stored.revision, AnalysisRun.objects.count(), AuditEvent.objects.count(), len(self.runtime.calls))
        listed = self.client.get(f"/api/v1/requests/?report_id={report['id']}&page_size=2")
        rows = list(listed.data['results'])
        if listed.data['next']:
            rows += self.client.get(listed.data['next']).data['results']
        record = next(row for row in rows if row['key'] == str(key))
        self.assertTrue(record['replay_available'])
        selected = self.client.get(f'/api/v1/requests/{key}/')
        self.assertEqual(selected.data['data'], record)
        self.assertNotIn('response_payload', record)
        run = self.client.get(f"/api/v1/reports/{report['id']}/analysis-runs/{record['result_id']}/")
        self.assertEqual(run.data['data']['id'], self.detail(report)['latest_run']['id'])
        stored.refresh_from_db()
        self.assertEqual(before, (stored.revision, AnalysisRun.objects.count(), AuditEvent.objects.count(), len(self.runtime.calls)))
        replay, _ = self.analyze(report, key)
        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay['Idempotency-Replayed'], 'true')
        self.assertEqual(replay.data, completed.data)
        self.assertEqual(len(self.runtime.calls), before[-1])

    def test_other_owner_cannot_read_request_run_report_or_media(self):
        report, evidence = self.source('TAI')
        completed, key = self.analyze(report)
        run_id = completed.data['data']['result']['id']
        self.client.force_authenticate(self.other)
        paths = [f"/api/v1/reports/{report['id']}/", f'/api/v1/requests/{key}/',
                 f"/api/v1/reports/{report['id']}/analysis-runs/{run_id}/"]
        paths += [f"/api/v1/evidence/{item['id']}/media/" for item in evidence if item['type'] != 'TEXT']
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 404, path)
        listed = self.client.get(f"/api/v1/requests/?report_id={report['id']}")
        self.assertEqual(listed.data['count'], 0)

    def test_source_changed_through_input_api_preserves_new_bundle_and_rejects_old_card(self):
        report, _ = self.source()
        changed = []

        def change_source():
            latest = self.detail(report)['report']
            upload = self.post(f"/api/v1/reports/{report['id']}/evidence/", {
                'type': 'TEXT', 'text_content': 'Sumber baru setelah analisis dimulai.',
                'expected_revision': latest['revision'],
            }, multipart=True)
            self.assertEqual(upload.status_code, 201, upload.data)
            data = upload.data['data']
            bundle = self.post(f"/api/v1/reports/{report['id']}/bundles/", {
                'evidence_ids': [data['object']['id']], 'expected_revision': data['report']['revision'],
            })
            self.assertEqual(bundle.status_code, 201, bundle.data)
            changed.append(bundle.data['data']['report']['active_bundle_id'])

        self.runtime.before_fusion = change_source
        response, key = self.analyze(report)
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['error']['code'], 'INPUT_CHANGED')
        detail = self.detail(report)
        self.assertEqual(detail['report']['active_bundle_id'], changed[0])
        self.assertEqual(detail['report']['preparation_status'], 'DRAFT')
        self.assertIsNone(detail['current_card'])
        self.assertEqual(detail['latest_run']['status'], 'FAILED')
        self.assertIsNotNone(detail['latest_run']['nara'])
        self.assertEqual(IdempotencyRecord.objects.get(key=key).error_code, 'INPUT_CHANGED')

    def test_known_failure_can_be_read_replayed_and_explicitly_retried_from_fresh_revision(self):
        report, _ = self.source()
        with patch.object(self.runtime, 'sena', side_effect=PipelineFailure('AI_UPSTREAM_FAILED', 'Layanan gagal.', 502)):
            response, key = self.analyze(report)
        self.assertEqual(response.status_code, 502, response.data)
        detail = self.detail(report)
        self.assertEqual(detail['latest_run']['status'], 'FAILED')
        self.assertIsNotNone(detail['latest_run']['output_narrative'])
        self.assertIsNone(detail['current_card'])
        replay, _ = self.analyze(report, key)
        self.assertEqual(replay.status_code, 502)
        self.assertEqual(replay['Idempotency-Replayed'], 'true')
        retried, _ = self.analyze(detail['report'])
        self.assertEqual(retried.status_code, 201, retried.data)
        self.assertEqual(AnalysisRun.objects.count(), 2)
        self.assertEqual(IncidentCardVersion.objects.count(), 1)

    def test_unknown_finalization_remains_read_only_and_holds_another_analysis(self):
        report, _ = self.source()
        with patch('ai_pipeline.services.finalize', side_effect=DatabaseError('test uncertain commit')):
            response, key = self.analyze(report)
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['error']['code'], 'REQUEST_UNKNOWN')
        state = self.detail(report)
        self.assertEqual(state['latest_run']['status'], 'UNKNOWN')
        before = (state['report']['revision'], AnalysisRun.objects.count(), AuditEvent.objects.count(), len(self.runtime.calls))
        read = self.client.get(f'/api/v1/requests/{key}/')
        self.assertEqual(read.data['data']['state'], 'UNKNOWN')
        self.assertFalse(read.data['data']['replay_available'])
        refused, _ = self.analyze(state['report'])
        self.assertEqual(refused.status_code, 409, refused.data)
        self.assertEqual(refused.data['error']['code'], 'REQUEST_UNKNOWN')
        fresh = self.detail(report)
        self.assertEqual(before, (fresh['report']['revision'], AnalysisRun.objects.count(), AuditEvent.objects.count(), len(self.runtime.calls)))

    def test_non_event_and_uncertain_are_stored_without_verification_or_submission(self):
        for category, confidence, status, uncertain in [('NON_EVENT', 0.99, 'BLOCKED', False),
                                                        ('FLOOD', 0.94, 'AWAITING_CONFIRMATION', True)]:
            self.runtime.label, self.runtime.confidence = category, confidence
            report, _ = self.source()
            response, _ = self.analyze(report)
            self.assertEqual(response.status_code, 201, response.data)
            detail = self.detail(report)
            self.assertEqual(detail['report']['preparation_status'], status)
            self.assertEqual(detail['current_card']['uncertain'], uncertain)
            self.assertIsNone(detail['report']['submitted_at'])
        self.assertFalse(HumanVerification.objects.exists())

    def test_missing_ai_configuration_preserves_login_draft_and_uploaded_evidence(self):
        report, _ = self.source()
        with patch('ai_pipeline.services.options', side_effect=not_ready()):
            rejected, _ = self.analyze(report)
        self.assertEqual(rejected.status_code, 503)
        self.assertEqual(rejected.data['error']['code'], 'AI_CONFIGURATION_NOT_READY')
        self.assertFalse(AnalysisRun.objects.exists())
        guest = APIClient(enforce_csrf_checks=True)
        csrf = guest.get('/api/v1/auth/csrf/').data['data']['csrf_token']
        with override_settings(AI_CPU_THREADS='invalid'):
            login = guest.post('/api/v1/auth/login/', {'email': self.owner.email, 'password': PASSWORD},
                               format='json', HTTP_ORIGIN='http://localhost:5173', HTTP_X_CSRFTOKEN=csrf)
            self.assertEqual(login.status_code, 200, login.data)
            guest.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['data']['access'])
            read = guest.get(f"/api/v1/reports/{report['id']}/evidence/")
            self.assertEqual(read.status_code, 200)
            self.assertEqual(read.data['count'], 1)

    def test_expired_request_remains_readable_without_available_replay(self):
        report, _ = self.source()
        response, key = self.analyze(report)
        self.assertEqual(response.status_code, 201)
        with patch('ai_pipeline.views.timezone.now', return_value=timezone.now() + timedelta(days=2)):
            normal = self.client.get(f"/api/v1/requests/?report_id={report['id']}")
            self.assertEqual(normal.data['count'], 0)
            historical = self.client.get(f"/api/v1/requests/?report_id={report['id']}&include_expired=true")
            self.assertTrue(any(row['key'] == str(key) for row in historical.data['results']))
            selected = self.client.get(f'/api/v1/requests/{key}/')
            self.assertFalse(selected.data['data']['replay_available'])
