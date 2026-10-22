from dataclasses import dataclass
import hashlib
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from .audio import DecodedAudio, MAX_AUDIO_BYTES, decode_audio
from .errors import PipelineFailure, not_ready


@dataclass(frozen=True)
class EvidenceSource:
    evidence_id: object
    type: str
    text: str = ""
    data: bytes = b""
    mime_type: str = ""
    audio: DecodedAudio | None = None


def route_for(items):
    types = [item.type for item in items]
    if (
        not types or set(types) - {"TEXT", "AUDIO", "IMAGE"}
        or types.count("TEXT") > 1 or types.count("AUDIO") > 1
        or types.count("IMAGE") > 3
    ):
        raise PipelineFailure("INVALID_PAYLOAD", "Kombinasi bukti tidak sesuai batas kanal.", 400)
    return "".join(letter for kind, letter in (("TEXT", "T"), ("AUDIO", "A"), ("IMAGE", "I")) if kind in types)


def validate_image(data, name, mime):
    if len(data) > 5 * 1024 * 1024:
        raise PipelineFailure("INPUT_TOO_LARGE", "Ukuran gambar melebihi batas.", 413)
    try:
        from PIL import Image
    except ImportError as error:
        raise not_ready() from error
    try:
        with Image.open(BytesIO(data)) as image:
            if image.width * image.height > 12_000_000:
                raise PipelineFailure("INPUT_TOO_LARGE", "Dimensi gambar melebihi batas.", 413)
            actual = {"PNG": "image/png", "JPEG": "image/jpeg"}.get(image.format)
            suffixes = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}}
            if not actual or Path(name or "").suffix.lower() not in suffixes[actual] or mime != actual:
                raise ValueError("Image metadata does not match its content.")
            image.verify()
        # Verify complete decoding as well as the container signature.
        with Image.open(BytesIO(data)) as image:
            image.load()
        return actual
    except PipelineFailure:
        raise
    except Exception as error:
        raise PipelineFailure("MEDIA_UNSUPPORTED", "Isi gambar tidak dapat diproses.", 415) from error


def load_sources(bundle):
    """Read only immutable, private evidence; never use an upload name as a path."""
    from core.storage import PrivateMediaStorage

    members = list(bundle.items.select_related("evidence").order_by("position"))
    route_for([member.evidence for member in members])
    sources, total = [], 0
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    storage = PrivateMediaStorage()
    for member in members:
        item = member.evidence
        if item.report_id != bundle.report_id:
            raise PipelineFailure("INVALID_PAYLOAD", "Sumber bukti tidak sesuai laporan.", 400)
        if item.type == "TEXT":
            text = item.text_content or ""
            if not text.strip() or len(text) > 5000:
                raise PipelineFailure("INVALID_PAYLOAD", "Teks bukti tidak sesuai batas.", 400)
            data = text.encode("utf-8")
            source = EvidenceSource(item.id, "TEXT", text=text)
        else:
            limit = MAX_AUDIO_BYTES if item.type == "AUDIO" else 5 * 1024 * 1024
            try:
                path = Path(storage.path(item.file_key)).resolve(strict=True)
                path.relative_to(root)
                with path.open("rb") as stream:
                    data = stream.read(limit + 1)
            except (OSError, ValueError, TypeError, SuspiciousFileOperation) as error:
                raise PipelineFailure("MEDIA_UNSUPPORTED", "Bukti media belum dapat dibaca.", 415) from error
            if len(data) > limit:
                raise PipelineFailure("INPUT_TOO_LARGE", "Ukuran bukti melebihi batas.", 413)
            if item.type == "AUDIO":
                audio = decode_audio(data, item.original_name, item.mime_type)
                source = EvidenceSource(item.id, "AUDIO", audio=audio, mime_type=audio.mime_type)
            else:
                mime = validate_image(data, item.original_name, item.mime_type)
                source = EvidenceSource(item.id, "IMAGE", data=data, mime_type=mime)
        if len(data) != item.byte_size or hashlib.sha256(data).hexdigest() != item.sha256:
            raise PipelineFailure("MEDIA_UNSUPPORTED", "Integritas bukti tidak sesuai rekaman.", 415)
        total += len(data)
        if total > 25 * 1024 * 1024:
            raise PipelineFailure("INPUT_TOO_LARGE", "Total bukti melebihi batas bundle.", 413)
        sources.append(source)
    return sources
