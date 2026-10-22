"""Shared decoder boundary; also callable by SLR10 before accepting an upload."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from .errors import PipelineFailure, not_ready

MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_AUDIO_SECONDS = 120
SAMPLE_RATE = 16000


@dataclass(frozen=True)
class DecodedAudio:
    samples: object
    duration_ms: int
    mime_type: str
    codec: str


def decode_audio(data, original_name, declared_mime=None):
    if not data:
        raise PipelineFailure("MEDIA_UNSUPPORTED", "Audio kosong tidak dapat diproses.", 415)
    if len(data) > MAX_AUDIO_BYTES:
        raise PipelineFailure("INPUT_TOO_LARGE", "Audio melebihi batas ukuran.", 413)
    try:
        import av
        import numpy as np
    except ImportError as error:
        raise not_ready() from error
    suffix = Path(original_name or "").suffix.lower()
    try:
        with av.open(BytesIO(data)) as container:
            streams = list(container.streams.audio)
            if len(streams) != 1 or list(container.streams.video):
                raise ValueError("Exactly one audio stream is required.")
            stream = streams[0]
            codec = stream.codec_context.name
            format_name = container.format.name
            if suffix == ".mp3" and "mp3" in format_name and codec in {"mp3", "mp3float"}:
                mime, accepted = "audio/mpeg", {"audio/mpeg", "audio/mp3"}
            elif suffix == ".wav" and format_name == "wav" and codec.startswith("pcm_"):
                mime, accepted = "audio/wav", {"audio/wav", "audio/x-wav", "audio/wave"}
            elif suffix == ".webm" and "webm" in format_name and codec == "opus":
                mime, accepted = "audio/webm", {"audio/webm"}
            elif suffix in {".m4a", ".mp4"} and "mp4" in format_name and codec == "aac":
                mime, accepted = "audio/mp4", {"audio/mp4", "audio/x-m4a", "video/mp4"}
            else:
                raise ValueError("Unsupported container or codec.")
            if declared_mime and declared_mime.split(";", 1)[0].strip().lower() not in accepted:
                raise ValueError("Media type does not match decoded audio.")
            resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
            parts, sample_count = [], 0

            def collect(frames):
                nonlocal sample_count
                for frame in frames:
                    samples = frame.to_ndarray().reshape(-1)
                    sample_count += samples.size
                    if sample_count > MAX_AUDIO_SECONDS * SAMPLE_RATE:
                        raise PipelineFailure(
                            "INPUT_TOO_LARGE", "Durasi audio melebihi dua menit.", 413
                        )
                    parts.append(samples)

            for frame in container.decode(stream):
                collect(resampler.resample(frame))
            collect(resampler.resample(None))
            if not sample_count:
                raise ValueError("Empty decoded audio.")
            samples = np.concatenate(parts).astype(np.float32) / 32768.0
            return DecodedAudio(samples, round(sample_count * 1000 / SAMPLE_RATE), mime, codec)
    except PipelineFailure:
        raise
    except Exception as error:
        raise PipelineFailure(
            "MEDIA_UNSUPPORTED", "Format atau isi audio belum dapat diproses.", 415
        ) from error
