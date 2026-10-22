"""Validate actual bytes. Originals are retained; derived audio belongs to SLR_11."""
import hashlib
import io
import json
import os
from pathlib import PureWindowsPath
import shutil
import subprocess
import tempfile
import warnings
import wave
from PIL import Image, UnidentifiedImageError
from common.api import ApiProblem

MIB = 1024 * 1024
TEXT_LIMIT = 5000
IMAGE_LIMIT = 5 * MIB
AUDIO_LIMIT = 10 * MIB
BUNDLE_LIMIT = 25 * MIB
MAX_PIXELS = 12_000_000
MAX_AUDIO_SECONDS = 120
AUDIO_SAMPLE_RATE = 16000
MAX_DECODED_AUDIO_BYTES = MAX_AUDIO_SECONDS * AUDIO_SAMPLE_RATE * 2
AUDIO_PROFILES = {
    '.wav': ('audio/wav', {'wav'}, {'pcm_s16le', 'pcm_s24le', 'pcm_s32le', 'pcm_u8', 'pcm_f32le'}),
    '.mp3': ('audio/mpeg', {'mp3'}, {'mp3'}),
    '.m4a': ('audio/mp4', {'mov', 'mp4', 'm4a'}, {'aac'}),
    '.mp4': ('audio/mp4', {'mov', 'mp4', 'm4a'}, {'aac'}),
    '.webm': ('audio/webm', {'matroska', 'webm'}, {'opus'}),
}


def problem(code='MEDIA_UNSUPPORTED', message='Berkas tidak dapat didekode sebagai media yang didukung.', status=415):
    raise ApiProblem(code, message, status)


def clean_name(name):
    name = PureWindowsPath(str(name).replace('/', '\\')).name
    return ''.join(c for c in name if c.isprintable() and c not in '<>:"/\\|?*')[-200:] or 'bukti'


def validate_image(raw, name):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                kind = image.format
                if kind not in ('PNG', 'JPEG') or image.width * image.height > MAX_PIXELS:
                    problem(message='Gambar harus PNG/JPEG dan maksimal 12 megapiksel.')
                if getattr(image, 'n_frames', 1) != 1:
                    problem(message='Gunakan PNG/JPEG statis, bukan gambar animasi.')
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
        suffix = PureWindowsPath(name).suffix.lower()
        if suffix not in ({'.png'} if kind == 'PNG' else {'.jpg', '.jpeg'}):
            problem(message='Ekstensi gambar harus sesuai isi PNG/JPEG.')
        return 'image/png' if kind == 'PNG' else 'image/jpeg'
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        problem()


def validate_audio(raw, name):
    suffix = PureWindowsPath(name).suffix.lower()
    if suffix not in AUDIO_PROFILES:
        problem(message='Gunakan WAV PCM, MP3, WebM/Opus, atau M4A/MP4 dengan AAC tanpa video.')
    mime, formats, codecs = AUDIO_PROFILES[suffix]
    probe = shutil.which(os.getenv('FFPROBE_BINARY', 'ffprobe'))
    decoder = shutil.which(os.getenv('FFMPEG_BINARY', 'ffmpeg'))
    if not probe or not decoder:
        if suffix != '.wav':
            problem('MEDIA_DECODER_NOT_READY', 'Decoder audio belum tersedia. Pasang FFmpeg atau gunakan WAV PCM.', 503)
        try:
            with wave.open(io.BytesIO(raw), 'rb') as audio:
                duration = audio.getnframes() / audio.getframerate()
                frames = audio.readframes(audio.getnframes())
                if len(frames) != audio.getnframes() * audio.getnchannels() * audio.getsampwidth():
                    problem()
                if duration <= 0 or duration > MAX_AUDIO_SECONDS:
                    problem('INPUT_TOO_LARGE', 'Durasi audio harus lebih dari 0 dan maksimal 2 menit.', 413)
            return mime
        except (wave.Error, EOFError, ZeroDivisionError):
            problem()
    with tempfile.TemporaryDirectory(prefix='silar-audio-') as folder:
        from pathlib import Path
        path = Path(folder) / ('input' + suffix)
        path.write_bytes(raw)
        try:
            info = subprocess.run([probe, '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_format',
                                   '-show_streams', '-of', 'json', str(path)], capture_output=True, timeout=12)
            if info.returncode:
                problem()
            data = json.loads(info.stdout)
            streams = data.get('streams', [])
            audios = [s for s in streams if s.get('codec_type') == 'audio']
            # Cover art is a video stream too. Reject it instead of storing an
            # audio item that the strict SLR_11 decoder may subsequently reject.
            videos = [s for s in streams if s.get('codec_type') == 'video']
            detected = set(data.get('format', {}).get('format_name', '').split(','))
            if len(audios) != 1 or videos or not formats.intersection(detected) or audios[0].get('codec_name') not in codecs:
                problem()
            # Container duration includes codec padding and is not the decoded
            # signal length. Count mono 16 kHz s16 samples, as SLR_11 does.
            # The output byte limit bounds long inputs just beyond the
            # boundary; the upload itself is never rewritten.
            decoded = subprocess.run([decoder, '-nostdin', '-v', 'error', '-xerror', '-threads', '1',
                '-protocol_whitelist', 'file,pipe', '-i', str(path), '-map', '0:a:0', '-vn',
                '-ac', '1', '-ar', str(AUDIO_SAMPLE_RATE), '-c:a', 'pcm_s16le',
                '-fs', str(MAX_DECODED_AUDIO_BYTES + 2), '-f', 's16le', 'pipe:1'],
                capture_output=True, timeout=30)
            if decoded.returncode:
                problem()
            if not decoded.stdout or len(decoded.stdout) % 2:
                problem()
            if len(decoded.stdout) > MAX_DECODED_AUDIO_BYTES:
                problem('INPUT_TOO_LARGE', 'Durasi audio maksimal 2 menit.', 413)
            return mime
        except FileNotFoundError:
            problem('MEDIA_DECODER_NOT_READY', 'Decoder audio belum tersedia. Pasang FFmpeg atau gunakan WAV PCM.', 503)
        except (subprocess.TimeoutExpired, ValueError, TypeError, KeyError, OSError):
            problem()


def validate_upload(data):
    kind = data['type']
    if kind == 'TEXT':
        text = data['text_content']
        if len(text) > TEXT_LIMIT or not text.strip():
            problem('INVALID_PAYLOAD', 'Teks harus nonkosong dan maksimal 5.000 karakter.', 400)
        raw = text.encode('utf-8')
        return dict(type=kind, text_content=text, file_key=None, original_name=None, mime_type=None,
                    byte_size=len(raw), sha256=hashlib.sha256(raw).hexdigest()), raw
    upload = data['file']
    limit = IMAGE_LIMIT if kind == 'IMAGE' else AUDIO_LIMIT
    if upload.size > limit:
        problem('INPUT_TOO_LARGE', 'Gambar maksimal 5 MiB; audio maksimal 10 MiB.', 413)
    raw = upload.read(limit + 1)
    if not raw or len(raw) > limit:
        problem('INPUT_TOO_LARGE', 'Ukuran berkas tidak dapat diterima.', 413)
    name = clean_name(upload.name)
    mime = validate_image(raw, name) if kind == 'IMAGE' else validate_audio(raw, name)
    client_mime = (upload.content_type or '').lower().split(';', 1)[0]
    aliases = {'audio/x-wav': 'audio/wav', 'audio/wave': 'audio/wav', 'audio/x-m4a': 'audio/mp4',
               'audio/mp3': 'audio/mpeg', 'video/mp4': 'audio/mp4', 'image/jpg': 'image/jpeg'}
    if client_mime and client_mime != 'application/octet-stream' and aliases.get(client_mime, client_mime) != mime:
        problem(message='Jenis MIME berkas tidak cocok dengan isi yang didekode.')
    return dict(type=kind, text_content=None, original_name=name, mime_type=mime,
                byte_size=len(raw), sha256=hashlib.sha256(raw).hexdigest()), raw
