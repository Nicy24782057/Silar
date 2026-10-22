import time

from . import PIPELINE_VERSION
from .clients import GeminiClient, whisper_client
from .errors import PipelineFailure, invalid_output
from .narrative import NORMALIZER_VERSION, normalize
from .runtime import reviewed_runtime
from .sources import route_for


class Pipeline:
    """Inference outside DB transactions; callbacks perform short guarded writes."""
    def __init__(self, options):
        self.options = options
        self.runtime = reviewed_runtime(options)

    def preflight(self, route, mode):
        if mode != "NARRATIVE_REVISION":
            if "A" in route:
                whisper_client(self.options)
            if "I" in route or len(route) > 1:
                GeminiClient(self.options)

    def execute(self, sources, *, existing_narrative, before, persist):
        route = route_for(sources)
        deadline = time.monotonic() + self.options.deadline_seconds
        versions = {"pipeline": PIPELINE_VERSION, **self.runtime.versions}

        def remaining():
            ms = int((deadline - time.monotonic()) * 1000)
            if ms <= 0:
                raise PipelineFailure("ANALYSIS_TIMEOUT", "Batas waktu analisis terlampaui.", 504)
            return ms

        def stage(name, work):
            remaining()
            before(name)
            started = time.perf_counter()
            result = work()
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            identifier = persist(name, result, elapsed, versions)
            remaining()
            return result, identifier

        transcript = None
        if existing_narrative is None and "A" in route:
            source = next(item for item in sources if item.type == "AUDIO")
            client = whisper_client(self.options)
            versions["whisper"] = client.version
            (transcript, _), _ = stage(
                "WHISPER",
                lambda: (client.transcribe(source.audio), {
                    "evidence_id": source.evidence_id, "model_version": client.version,
                    "duration_ms": source.audio.duration_ms,
                }),
            )

        def form_narrative():
            if existing_narrative is not None:
                return {"id": existing_narrative.id, "text": existing_narrative.text, "origin": "REPORTER_REVISION"}
            if route in {"T", "A"}:
                versions["normalizer"] = NORMALIZER_VERSION
                raw = next(item.text for item in sources if item.type == "TEXT") if route == "T" else transcript
                return {"text": normalize(raw), "origin": "NORMALIZER"}
            narrative, metadata = GeminiClient(self.options).narrative(sources, transcript, remaining())
            versions["gemini"] = metadata
            return {"text": narrative, "origin": "GEMINI"}

        narrative, narrative_id = stage("NARRATIVE", form_narrative)
        text = narrative["text"]
        (sena, sena_coverage), _ = stage("SENA", lambda: self.runtime.sena(text))
        (adapted, nara_coverage, trace), _ = stage(
            "NARA", lambda: self.runtime.nara(text, narrative_id, sena)
        )
        fused, _ = stage("FUSION", lambda: self.runtime.fuse(adapted))
        if "incident_card_version_fields" not in fused:
            raise invalid_output()
        before("PERSIST")
        return fused


def get_pipeline(options):
    return Pipeline(options)
