import hashlib
from pathlib import Path
import tempfile
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from common.testing import user
from core.models import EvidenceItem, Report
from reporting.tests.audio_fixtures import audio_fixtures


class AudioContractAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fixtures_folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixtures_folder.cleanup)
        cls.fixtures = audio_fixtures(cls.fixtures_folder.name)

    def setUp(self):
        if self.fixtures is None:
            self.skipTest('FFmpeg dan ffprobe diperlukan untuk tes API codec.')
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media.name))
        override.enable(); self.addCleanup(override.disable)
        self.client = APIClient()
        self.client.force_authenticate(user=user())
        response = self.client.post('/api/v1/reports/', {}, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 201, response.data)
        self.report = response.data['data']['report']

    def upload(self, name, raw, mime):
        return self.client.post('/api/v1/reports/' + self.report['id'] + '/evidence/',
            {'type': 'AUDIO', 'file': SimpleUploadedFile(name, raw, mime),
             'expected_revision': self.report['revision']}, format='multipart',
             HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))

    def test_five_audio_formats_preserve_original_and_restore_before_bundle(self):
        for path, mime, valid in self.fixtures:
            if not valid:
                continue
            with self.subTest(name=path.name):
                raw = path.read_bytes()
                response = self.upload(path.name, raw, mime)
                self.assertEqual(response.status_code, 201, response.data)
                self.report = response.data['data']['report']
                item = response.data['data']['object']
                self.assertEqual(item['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(item['mime_type'], mime)
                media = self.client.get('/api/v1/evidence/' + item['id'] + '/media/')
                self.assertEqual(b''.join(media.streaming_content), raw)
                self.assertEqual(media['Cache-Control'], 'no-store')
        revision = self.report['revision']
        response = self.client.get('/api/v1/reports/' + self.report['id'] + '/evidence/?page_size=2')
        self.assertEqual(response.data['count'], 5)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(response['Cache-Control'], 'no-store')
        report = Report.objects.get(pk=self.report['id'])
        self.assertEqual(report.revision, revision)
        self.assertIsNone(report.active_bundle_id)

    def test_unsupported_codecs_video_and_cover_cannot_become_evidence(self):
        for path, mime, valid in self.fixtures:
            if valid:
                continue
            with self.subTest(name=path.name):
                response = self.upload(path.name, path.read_bytes(), mime)
                self.assertEqual(response.status_code, 415, response.data)
                self.assertEqual(response.data['error']['code'], 'MEDIA_UNSUPPORTED')
        self.assertFalse(EvidenceItem.objects.exists())
        self.assertEqual(Report.objects.get().revision, 1)
        self.assertFalse(any(Path(self.media.name).rglob('*')))

    def test_spoofed_extension_mime_and_corruption_fail_before_revision_changes(self):
        wav = (Path(self.fixtures_folder.name) / 'pcm.wav').read_bytes()
        for name, raw, mime in [('renamed.mp3', wav, 'audio/mpeg'),
                                ('wrong.wav', wav, 'audio/mp4'),
                                ('corrupt.mp4', b'not MP4', 'audio/mp4')]:
            with self.subTest(name=name):
                self.assertEqual(self.upload(name, raw, mime).status_code, 415)
        self.assertFalse(EvidenceItem.objects.exists())
        self.assertEqual(Report.objects.get().revision, 1)

    def test_browser_mp4_container_mime_still_requires_aac_without_video(self):
        folder = Path(self.fixtures_folder.name)
        response = self.upload('browser.mp4', (folder / 'aac.mp4').read_bytes(), 'video/mp4')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['object']['mime_type'], 'audio/mp4')
        self.report = response.data['data']['report']
        response = self.upload('video.mp4', (folder / 'video.mp4').read_bytes(), 'video/mp4')
        self.assertEqual(response.status_code, 415, response.data)
