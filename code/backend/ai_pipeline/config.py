from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings

from .errors import not_ready


@dataclass(frozen=True)
class Options:
    slr09_root: Path
    sena_dir: Path
    nara_dir: Path
    whisper_dir: Path
    whisper_variant: str
    cpu_threads: int
    gemini_key: str = field(repr=False)
    gemini_model: str
    gemini_timeout_ms: int
    gemini_output_tokens: int
    deadline_seconds: int


def options():
    """AI misconfiguration does not prevent login or other non-AI endpoints."""
    try:
        result = Options(
            slr09_root=Path(settings.SILAR_SLR09_ROOT).expanduser().resolve(),
            sena_dir=Path(settings.SENA_MODEL_DIR).expanduser().resolve(),
            nara_dir=Path(settings.NARA_MODEL_DIR).expanduser().resolve(),
            whisper_dir=Path(settings.WHISPER_MODEL_DIR).expanduser().resolve(),
            whisper_variant=str(settings.WHISPER_VARIANT),
            cpu_threads=int(settings.AI_CPU_THREADS),
            gemini_key=str(settings.GEMINI_API_KEY),
            gemini_model=str(settings.GEMINI_MODEL),
            gemini_timeout_ms=int(settings.GEMINI_TIMEOUT_MS),
            gemini_output_tokens=int(settings.GEMINI_MAX_OUTPUT_TOKENS),
            deadline_seconds=int(settings.ANALYSIS_DEADLINE_SECONDS),
        )
        if (
            result.cpu_threads < 1
            or result.gemini_timeout_ms < 1
            or result.gemini_output_tokens < 1
            or result.deadline_seconds < 1
            or result.whisper_variant != "small"
            or not result.gemini_model.strip()
        ):
            raise ValueError
        return result
    except (ValueError, TypeError, AttributeError, OSError) as error:
        raise not_ready() from error
