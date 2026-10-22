import io
from pathlib import Path
import tempfile
import uuid
from unittest.mock import patch
from PIL import Image
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from common.testing import user
from core.models import Report, EvidenceItem, EvidenceBundle, EvidenceBundleItem, AuditEvent, IdempotencyRecord
from core.test_fixtures import source_chain
from core.storage import PrivateMediaStorage
from django.core.files.uploadedfile import SimpleUploadedFile


class InputAPITests(TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.override = override_settings(PRIVATE_MEDIA_ROOT=Path(self.folder.name))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.folder.cleanup)
        self.owner = user()
        self.other = user(email='other@silar.test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def create(self, key=None):
        return self.client.post('/api/v1/reports/', {}, format='json', HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def report(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['data']['report']

    def text(self, report, text='Banjir menggenangi jalan umum.', key=None):
        return self.client.post('/api/v1/reports/' + report['id'] + '/evidence/',
            {'type': 'TEXT', 'text_content': text, 'expected_revision': report['revision']},
            format='multipart', HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def bundle(self, report, ids, key=None):
        return self.client.post('/api/v1/reports/' + report['id'] + '/bundles/',
            {'evidence_ids': ids, 'expected_revision': report['revision']}, format='json',
            HTTP_IDEMPOTENCY_KEY=str(key or uuid.uuid4()))

    def image(self, report):
        buffer = io.BytesIO()
        Image.new('RGB', (8, 8), '#1f625c').save(buffer, format='PNG')
        return self.client.post('/api/v1/reports/' + report['id'] + '/evidence/',
            {'type': 'IMAGE', 'file': SimpleUploadedFile('bukti.png', buffer.getvalue(), 'image/png'),
             'expected_revision': report['revision']}, format='multipart', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))

    def test_create_draft_and_exact_snapshot(self):
        report = self.report()
        self.assertEqual(report['workflow_status'], 'NOT_SUBMITTED')
        self.assertIsNone(report['active_bundle_id'])
        self.assertEqual(report['revision'], 1)
        self.assertEqual(IdempotencyRecord.objects.get().report_id, uuid.UUID(report['id']))
        self.assertEqual(AuditEvent.objects.get().action, 'REPORT_CREATED')

    def test_create_idempotent_replay_no_duplicate(self):
        key = uuid.uuid4()
        first = self.create(key)
        second = self.create(key)
        self.assertEqual(first.data, second.data)
        self.assertEqual(second['Idempotency-Replayed'], 'true')
        self.assertEqual(Report.objects.count(), 1)

    def test_create_rejects_payload_and_missing_key(self):
        self.assertEqual(self.client.post('/api/v1/reports/', {}, format='json').status_code, 400)
        response = self.client.post('/api/v1/reports/', {'owner_id': str(self.other.id)}, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Report.objects.exists())

    def test_private_api_requires_login(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/reports/').status_code, 401)

    def test_operator_cannot_create_report(self):
        self.owner.role = 'OPERATOR'
        self.owner.save(update_fields=['role'])
        self.assertEqual(self.create().status_code, 403)

    def test_unverified_account_rejected(self):
        self.owner.email_verified_at = None
        self.owner.save(update_fields=['email_verified_at'])
        self.assertEqual(self.create().status_code, 403)

    def test_text_upload_preserves_original_and_does_not_activate_bundle(self):
        report = self.report()
        original = '  Banjir di jalan umum.  '
        response = self.text(report, original)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['object']['text_content'], original)
        self.assertNotIn('file_key', response.data['data']['object'])
        state = response.data['data']['report']
        self.assertIsNone(state['active_bundle_id'])
        self.assertEqual(state['input_revision'], 1)
        self.assertEqual(state['revision'], 2)

    def test_restore_before_bundle_uses_read_only_paginated_evidence(self):
        report = self.report()
        for i in range(3):
            report = self.text(report, 'Keterangan sumber ' + str(i)).data['data']['report']
        new_session = APIClient()
        new_session.force_authenticate(user=self.owner)
        url = '/api/v1/reports/' + report['id'] + '/evidence/?page_size=2'
        first = new_session.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data['count'], 3)
        self.assertEqual(len(first.data['results']), 2)
        self.assertIsNotNone(first.data['next'])
        second = new_session.get('/api/v1/reports/' + report['id'] + '/evidence/?page_size=2&page=2')
        self.assertEqual(len(second.data['results']), 1)
        current = Report.objects.get(pk=report['id'])
        self.assertEqual(current.revision, 4)
        self.assertEqual(current.input_revision, 1)
        self.assertIsNone(current.active_bundle_id)
        self.assertEqual(EvidenceBundle.objects.count(), 0)
        self.assertEqual(first['Cache-Control'], 'no-store')

    def test_other_owner_cannot_read_or_mutate_sources(self):
        report = self.report()
        self.client.force_authenticate(user=self.other)
        for path in ['', 'evidence/']:
            self.assertEqual(self.client.get('/api/v1/reports/' + report['id'] + '/' + path).status_code, 404)
        self.assertEqual(self.text(report).status_code, 404)

    def test_missing_report_is_404_not_internal_error(self):
        self.assertEqual(self.text({'id': str(uuid.uuid4()), 'revision': 1}).status_code, 404)

    def test_upload_idempotency_does_not_duplicate_evidence(self):
        report = self.report()
        key = uuid.uuid4()
        first = self.text(report, key=key)
        replay = self.text(report, key=key)
        self.assertEqual(first.data, replay.data)
        self.assertEqual(replay['Idempotency-Replayed'], 'true')
        self.assertEqual(EvidenceItem.objects.count(), 1)
        self.assertEqual(Report.objects.get().revision, 2)

    def test_idempotency_payload_mismatch_is_409(self):
        report = self.report()
        key = uuid.uuid4()
        self.text(report, key=key)
        response = self.text(report, 'Sumber berbeda.', key=key)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 'IDEMPOTENCY_MISMATCH')

    def test_revision_conflict_leaves_no_new_item(self):
        report = self.report()
        self.text(report)
        response = self.text(report, 'Bukti lain.')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(EvidenceItem.objects.count(), 1)

    def test_bundle_activates_sources_and_versions_remain(self):
        report = self.report()
        one = self.text(report)
        report = one.data['data']['report']
        id1 = one.data['data']['object']['id']
        first = self.bundle(report, [id1])
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(first.data['data']['report']['input_revision'], 2)
        two = self.text(first.data['data']['report'], 'Narasi bukti kedua.')
        second = self.bundle(two.data['data']['report'], [two.data['data']['object']['id']])
        self.assertEqual(second.data['data']['object']['version_number'], 2)
        self.assertEqual(EvidenceBundle.objects.count(), 2)
        self.assertEqual(EvidenceItem.objects.count(), 2)
        self.assertEqual(EvidenceBundleItem.objects.filter(bundle_id=first.data['data']['object']['id']).get().evidence_id, uuid.UUID(id1))

    def test_bundle_rejects_empty_duplicate_or_cross_report_ids(self):
        report = self.report()
        upload = self.text(report)
        report = upload.data['data']['report']
        evidence = upload.data['data']['object']['id']
        for ids in ([], [evidence, evidence], [str(uuid.uuid4())]):
            self.assertEqual(self.bundle(report, ids).status_code, 400)
        self.assertEqual(EvidenceBundle.objects.count(), 0)

    def test_bundle_cannot_contain_two_text_channels(self):
        report = self.report()
        first = self.text(report)
        second = self.text(first.data['data']['report'], 'Sumber teks lainnya.')
        ids = [x.data['data']['object']['id'] for x in (first, second)]
        self.assertEqual(self.bundle(second.data['data']['report'], ids).status_code, 400)

    def test_bundle_replay_returns_original_even_after_later_upload(self):
        first = self.text(self.report())
        report = first.data['data']['report']
        ids = [first.data['data']['object']['id']]
        key = uuid.uuid4()
        bundle = self.bundle(report, ids, key)
        self.text(bundle.data['data']['report'], 'Bukti sesudah bundle.')
        replay = self.bundle(report, ids, key)
        self.assertEqual(replay.data, bundle.data)
        self.assertEqual(Report.objects.get().revision, 4)

    def test_image_bytes_private_and_access_checked_each_time(self):
        upload = self.image(self.report())
        self.assertEqual(upload.status_code, 201, upload.data)
        item = upload.data['data']['object']
        path = '/api/v1/evidence/' + item['id'] + '/media/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'\x89PNG'))
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_fake_image_is_rejected_without_saving_file(self):
        report = self.report()
        response = self.client.post('/api/v1/reports/' + report['id'] + '/evidence/',
            {'type': 'IMAGE', 'file': SimpleUploadedFile('bad.png', b'not an image', 'image/png'), 'expected_revision': 1},
            format='multipart', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 415)
        self.assertEqual(list(Path(self.folder.name).rglob('*')), [])

    def test_transaction_failure_removes_new_media_file(self):
        report = self.report()
        with patch('reporting.services.record_event', side_effect=RuntimeError('test rollback')):
            response = self.image(report)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(EvidenceItem.objects.count(), 0)
        self.assertEqual(Report.objects.get().revision, 1)
        self.assertEqual([x for x in Path(self.folder.name).rglob('*') if x.is_file()], [])

    def test_list_is_summary_only_and_pagination_is_validated(self):
        self.report()
        response = self.client.get('/api/v1/reports/?scope=owned&page_size=1')
        self.assertEqual(response.data['count'], 1)
        for name in ('owner_id', 'text_content', 'active_bundle', 'narrative', 'email'):
            self.assertNotIn(name, response.data['results'][0])
        for query in ('page_size=101', 'page=0', 'unexpected=1', 'workflow_status=INVALID_STATUS'):
            self.assertEqual(self.client.get('/api/v1/reports/?' + query).status_code, 400)

    def test_draft_cannot_be_read_by_admin_monitor(self):
        report = self.report()
        self.owner.role = 'ADMIN'
        self.owner.save(update_fields=['role'])
        self.assertEqual(self.client.get('/api/v1/reports/' + report['id'] + '/').status_code, 404)

    def test_detail_empty_keys_and_ai_result_read_adapter(self):
        report, bundle, run, card, evidence = source_chain(self.owner)
        response = self.client.get('/api/v1/reports/' + str(report.id) + '/')
        self.assertEqual(response.status_code, 200, response.data)
        detail = response.data['data']
        self.assertEqual(detail['current_card']['id'], str(card.id))
        self.assertIsInstance(detail['latest_run']['sena']['confidence'], float)
        self.assertNotIn('execution_token', detail['latest_run'])
        self.assertNotIn('file_key', detail['active_bundle']['items'][0]['evidence'])

    def test_evidence_get_rejects_extra_query(self):
        report = self.report()
        self.assertEqual(self.client.get('/api/v1/reports/' + report['id'] + '/evidence/?type=TEXT').status_code, 400)
