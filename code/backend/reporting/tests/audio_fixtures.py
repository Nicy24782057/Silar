"""Small synthetic files with actual codecs; no model weights or user media."""
from pathlib import Path
import shutil
import subprocess
import wave
from PIL import Image


def duration_audio_fixtures(folder, sample_count):
    """Encode a known number of 16 kHz samples, including codec padding."""
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return None
    folder = Path(folder)
    source = folder / 'duration.wav'
    with wave.open(str(source), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b'\0\0' * sample_count)
    rows = [(source, 'audio/wav')]
    for suffix, codec, mime in [('mp3', 'libmp3lame', 'audio/mpeg'),
                                ('m4a', 'aac', 'audio/mp4'), ('mp4', 'aac', 'audio/mp4'),
                                ('webm', 'libopus', 'audio/webm')]:
        path = folder / ('duration.' + suffix)
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source),
                        '-c:a', codec, str(path)], capture_output=True, check=True, timeout=30)
        rows.append((path, mime))
    return rows


def audio_fixtures(folder):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        return None
    folder = Path(folder)
    source = folder / 'pcm.wav'
    with wave.open(str(source), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b'\0\0' * 4000)
    rows = [('pcm.wav', 'audio/wav', True)]
    for name, codec, mime, valid in [
        ('mp3.mp3', 'libmp3lame', 'audio/mpeg', True),
        ('aac.m4a', 'aac', 'audio/mp4', True),
        ('aac.mp4', 'aac', 'audio/mp4', True),
        ('opus.webm', 'libopus', 'audio/webm', True),
        ('opus.ogg', 'libopus', 'audio/ogg', False),
        ('alac.m4a', 'alac', 'audio/mp4', False),
        ('vorbis.webm', 'libvorbis', 'audio/webm', False),
        ('adpcm.wav', 'adpcm_ima_wav', 'audio/wav', False),
    ]:
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source), '-c:a', codec,
                        str(folder / name)], capture_output=True, check=True, timeout=15)
        rows.append((name, mime, valid))
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
        'color=c=blue:size=32x32:duration=0.25', '-i', str(source), '-shortest', '-c:v', 'mpeg4',
        '-c:a', 'aac', str(folder / 'video.mp4')], capture_output=True, check=True, timeout=15)
    rows.append(('video.mp4', 'audio/mp4', False))
    cover = folder / 'cover.jpg'
    Image.new('RGB', (32, 32), '#1f625c').save(cover, 'JPEG')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source), '-i', str(cover),
        '-map', '0:a', '-map', '1:v', '-c:a', 'libmp3lame', '-c:v', 'copy', '-disposition:v',
        'attached_pic', str(folder / 'cover.mp3')], capture_output=True, check=True, timeout=15)
    rows.append(('cover.mp3', 'audio/mpeg', False))
    return [(folder / name, mime, valid) for name, mime, valid in rows]
