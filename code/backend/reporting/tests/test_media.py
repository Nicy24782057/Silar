import io
import wave
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from common.api import ApiProblem
from reporting.media import validate_upload
from reporting.tests.audio_fixtures import audio_fixtures, duration_audio_fixtures


class MediaDecoderTests(SimpleTestCase):
    def image(self, fmt='PNG', size=(10, 10)):
        stream = io.BytesIO()
        Image.new('RGB', size).save(stream, format=fmt)
        return stream.getvalue()

    def test_valid_png_and_jpeg_use_decoder_mime(self):
        for kind, name, mime in [('PNG', 'a.png', 'image/png'), ('JPEG', 'a.jpg', 'image/jpeg')]:
            raw = self.image(kind)
            metadata, result = validate_upload({'type': 'IMAGE', 'file': SimpleUploadedFile(name, raw, mime)})
            self.assertEqual(result, raw)
            self.assertEqual(metadata['mime_type'], mime)

    def test_extension_mismatch_or_wrong_mime_rejected(self):
        for name, mime in [('x.jpg', 'image/jpeg'), ('x.png', 'image/jpeg')]:
            with self.assertRaises(ApiProblem):
                validate_upload({'type': 'IMAGE', 'file': SimpleUploadedFile(name, self.image(), mime)})

    def test_large_dimensions_rejected(self):
        with self.assertRaises(ApiProblem):
            validate_upload({'type': 'IMAGE', 'file': SimpleUploadedFile('x.png', self.image(size=(4001, 3000)), 'image/png')})

    def test_audio_pcm_actual_frames_and_duration(self):
        stream = io.BytesIO()
        with wave.open(stream, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b'\0\0' * 800)
        with patch('reporting.media.shutil.which', return_value=None):
            metadata, raw = validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile('voice.wav', stream.getvalue(), 'audio/wav')})
        self.assertEqual(metadata['mime_type'], 'audio/wav')

    def test_missing_decoder_cannot_accept_fake_mp3(self):
        with patch('reporting.media.shutil.which', return_value=None), self.assertRaises(ApiProblem) as error:
            validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile('voice.mp3', b'fake', 'audio/mpeg')})
        self.assertEqual(error.exception.error_code, 'MEDIA_DECODER_NOT_READY')

    def test_text_unicode_byte_size_preserves_original(self):
        metadata, raw = validate_upload({'type': 'TEXT', 'text_content': '  Banjir 🌧  '})
        self.assertEqual(metadata['byte_size'], len('  Banjir 🌧  '.encode()))
        self.assertEqual(raw.decode(), '  Banjir 🌧  ')

    def test_ffmpeg_audio_profiles_are_actually_decoded(self):
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('Tes profil audio membutuhkan FFmpeg dan ffprobe.')
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.wav'
            with wave.open(str(source), 'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
                audio.writeframes(b'\0\0' * 1600)
            for ext, codec, mime in [('mp3', 'libmp3lame', 'audio/mpeg'), ('m4a', 'aac', 'audio/mp4'),
                                     ('webm', 'libopus', 'audio/webm'), ('mp4', 'aac', 'audio/mp4')]:
                dest = Path(folder) / ('sample.' + ext)
                converted = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source), '-c:a', codec,
                                            str(dest)], capture_output=True)
                self.assertEqual(converted.returncode, 0, 'Encoder fixture FFmpeg tidak tersedia: ' + codec)
                metadata, raw = validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile(dest.name, dest.read_bytes(), mime)})
                self.assertEqual(metadata['mime_type'], mime)

    def test_audio_contract_rejects_actual_unsupported_codecs_video_and_cover(self):
        with tempfile.TemporaryDirectory() as folder:
            fixtures = audio_fixtures(folder)
            if fixtures is None:
                self.skipTest('FFmpeg dan ffprobe diperlukan untuk matriks codec.')
            for path, mime, accepted in fixtures:
                with self.subTest(name=path.name):
                    upload = {'type': 'AUDIO', 'file': SimpleUploadedFile(path.name, path.read_bytes(), mime)}
                    if accepted:
                        metadata, original = validate_upload(upload)
                        self.assertEqual(original, path.read_bytes())
                        self.assertEqual(metadata['mime_type'], mime)
                    else:
                        with self.assertRaises(ApiProblem) as error:
                            validate_upload(upload)
                        self.assertEqual(error.exception.error_code, 'MEDIA_UNSUPPORTED')

    def test_renamed_container_mime_corruption_and_size_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            fixtures = audio_fixtures(folder)
            if fixtures is None:
                self.skipTest('FFmpeg dan ffprobe diperlukan.')
            source = Path(folder) / 'pcm.wav'
            for name, raw, mime in [('renamed.mp3', source.read_bytes(), 'audio/mpeg'),
                                    ('wrong.wav', source.read_bytes(), 'audio/mp4'),
                                    ('broken.mp3', b'not audio', 'audio/mpeg'),
                                    ('empty.wav', b'', 'audio/wav'),
                                    ('large.wav', b'0' * (10 * 1024 ** 2 + 1), 'audio/wav')]:
                with self.subTest(name=name), self.assertRaises(ApiProblem):
                    validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile(name, raw, mime)})

    def test_duration_above_120_seconds_is_rejected(self):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as audio:
            audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
            audio.writeframes(b'\0\0' * (121 * 16000))
        with self.assertRaises(ApiProblem) as error:
            validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile('long.wav', buffer.getvalue(), 'audio/wav')})
        self.assertEqual(error.exception.error_code, 'INPUT_TOO_LARGE')

    def test_exact_120_seconds_accepts_all_target_codecs_with_padding(self):
        with tempfile.TemporaryDirectory() as folder:
            fixtures = duration_audio_fixtures(folder, 120 * 16000)
            if fixtures is None:
                self.skipTest('FFmpeg dan ffprobe diperlukan untuk batas codec.')
            for path, mime in fixtures:
                with self.subTest(name=path.name):
                    original = path.read_bytes()
                    metadata, raw = validate_upload({'type': 'AUDIO',
                        'file': SimpleUploadedFile(path.name, original, mime)})
                    self.assertEqual(metadata['mime_type'], mime)
                    self.assertEqual(raw, original)

    def test_119_9_seconds_remains_valid_for_all_target_codecs(self):
        with tempfile.TemporaryDirectory() as folder:
            fixtures = duration_audio_fixtures(folder, 1199 * 1600)
            if fixtures is None:
                self.skipTest('FFmpeg dan ffprobe diperlukan untuk batas codec.')
            for path, mime in fixtures:
                with self.subTest(name=path.name):
                    metadata, _ = validate_upload({'type': 'AUDIO',
                        'file': SimpleUploadedFile(path.name, path.read_bytes(), mime)})
                    self.assertEqual(metadata['mime_type'], mime)

    def test_decoded_audio_over_120_seconds_is_rejected_for_all_target_codecs(self):
        with tempfile.TemporaryDirectory() as folder:
            fixtures = duration_audio_fixtures(folder, 120 * 16000 + 160)
            if fixtures is None:
                self.skipTest('FFmpeg dan ffprobe diperlukan untuk batas codec.')
            for path, mime in fixtures:
                with self.subTest(name=path.name), self.assertRaises(ApiProblem) as error:
                    validate_upload({'type': 'AUDIO',
                        'file': SimpleUploadedFile(path.name, path.read_bytes(), mime)})
                self.assertEqual(error.exception.error_code, 'INPUT_TOO_LARGE')

    def test_decoder_disappearing_is_a_service_failure(self):
        with patch('reporting.media.shutil.which', return_value='/missing/decoder'), \
             patch('reporting.media.subprocess.run', side_effect=FileNotFoundError), self.assertRaises(ApiProblem) as error:
            validate_upload({'type': 'AUDIO', 'file': SimpleUploadedFile('voice.mp3', b'fixture', 'audio/mpeg')})
        self.assertEqual(error.exception.error_code, 'MEDIA_DECODER_NOT_READY')
