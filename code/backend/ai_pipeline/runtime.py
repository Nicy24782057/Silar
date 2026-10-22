"""Use the reviewed SLR09 implementation unchanged, with local verified weights."""
from functools import lru_cache
import importlib
import json
from pathlib import Path
import sys
from threading import RLock
from types import SimpleNamespace

from .errors import invalid_output, not_ready

_IMPORT_LOCK = RLock()


def active_modules(root):
    directory = (Path(root) / "code" / "active_nara_adapter").resolve()
    if not (directory / "slr09_candidate_runtime.py").is_file():
        raise not_ready()
    with _IMPORT_LOCK:
        # SLR09 modules use absolute sibling imports. Reject an existing import
        # from another location instead of silently mixing adapter versions.
        names = (
            "slr09_candidate_runtime", "slr09_runtime", "silar_ai_adapter",
            "legacy_postprocessing", "silar_nara_composition",
            "silar_postprocessing", "silar_victim_guard",
        )
        for name in names:
            module = sys.modules.get(name)
            if module and Path(module.__file__).resolve().parent != directory:
                raise not_ready()
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
        try:
            candidate = importlib.import_module("slr09_candidate_runtime")
            adapter = importlib.import_module("silar_ai_adapter")
            historical = importlib.import_module("slr09_runtime")
        except (ImportError, ValueError, OSError) as error:
            raise not_ready() from error
        return candidate, adapter, historical


class ReviewedRuntime:
    def __init__(self, options):
        self.options = options
        self.candidate, self.adapter, self.historical = active_modules(options.slr09_root)
        self._runner = None
        self._lock = RLock()
        try:
            self.config, self.asset_lock, self.profile = self.candidate.selected_assets(options.slr09_root)
            self.candidate.check_dependencies(self.profile)
            for name, directory in (("sena", options.sena_dir), ("nara", options.nara_dir)):
                self.candidate.verify_candidate_directory(
                    directory, name, self.asset_lock["models"][name]
                )
            self.identity = configuration_identity(options.slr09_root)
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
            raise not_ready() from error

    @property
    def versions(self):
        return {
            "sena": self.asset_lock["models"]["sena"]["model_id"] + "|" + self.adapter.ADAPTER_VERSION,
            "nara": self.asset_lock["models"]["nara"]["model_id"] + "|" + self.adapter.ADAPTER_VERSION,
            "adapter": self.adapter.ADAPTER_VERSION,
            "fusion": self.adapter.FUSION_VERSION,
            "runtime": self.candidate.CANDIDATE_RUNNER_VERSION,
            "confidence_threshold": self.config["confidence_threshold"],
            "calibration_reference": self.config["calibration_reference"],
            "configuration_sha256": self.identity[0],
            "asset_lock_sha256": self.identity[1],
            "inference_profile_sha256": self.identity[2],
        }

    def runner(self):
        with self._lock:
            if self._runner is None:
                try:
                    self._runner = self.candidate.CandidateModelRunner(
                        self.options.sena_dir, self.options.nara_dir,
                        root=self.options.slr09_root, device="cpu",
                        cpu_threads=self.options.cpu_threads,
                    )
                except Exception as error:
                    raise not_ready() from error
            return self._runner

    def sena(self, narrative):
        with self._lock:
            result, coverage = self.runner().predict_sena(narrative)
            self.runner().sync()
        # Check JSON finiteness at the boundary before persisting any raw output.
        try:
            json.dumps(result, allow_nan=False)
            self.historical.validate_prediction(result)
        except (ValueError, TypeError, KeyError) as error:
            raise invalid_output() from error
        return result, coverage

    def nara(self, narrative, narrative_id, sena):
        with self._lock:
            tokens, coverage = self.runner().predict_nara(narrative)
            self.runner().sync()
        try:
            raw, trace = self.historical.build_adapter_input(narrative, sena, tokens)
            adapted = self.adapter.adapt_legacy_ai_output(
                raw, narrative_id=str(narrative_id),
                sena_model_version=self.asset_lock["models"]["sena"]["model_id"],
                nara_model_version=self.asset_lock["models"]["nara"]["model_id"],
            )
            json.dumps(adapted, allow_nan=False)
        except (ValueError, TypeError, KeyError) as error:
            raise invalid_output() from error
        return adapted, coverage, trace

    def fuse(self, adapted):
        try:
            return self.adapter.fuse_for_silar(
                adapted,
                confidence_threshold=self.config["confidence_threshold"],
                calibration_reference=self.config["calibration_reference"],
            )
        except (ValueError, TypeError, KeyError) as error:
            raise invalid_output() from error


def configuration_identity(root):
    import hashlib
    try:
        return tuple(hashlib.sha256((Path(root) / "config" / name).read_bytes()).hexdigest() for name in (
            "SLR09_Konfigurasi_Integrasi_v0.9.json",
            "quality_candidate_asset_lock_v0.8.4.json",
            "inference_environment.json",
        ))
    except OSError as error:
        raise not_ready() from error


@lru_cache(maxsize=1)
def _reviewed_runtime(root, sena_dir, nara_dir, cpu_threads, identity):
    runtime = ReviewedRuntime(SimpleNamespace(
        slr09_root=root, sena_dir=sena_dir, nara_dir=nara_dir, cpu_threads=cpu_threads
    ))
    if runtime.identity != identity:
        raise not_ready()
    return runtime


def reviewed_runtime(options):
    # API-key rotation and HTTP settings must not load another pair of models.
    return _reviewed_runtime(
        options.slr09_root, options.sena_dir, options.nara_dir, options.cpu_threads,
        configuration_identity(options.slr09_root),
    )


def safe_service_metadata():
    """Internal SLR13 input: configuration evidence, not an upstream health claim.

    The SLR13 endpoint must apply monitor_services authorization and derive
    ServiceStatus states from its actual checks. This helper runs no inference
    and exposes no credentials, process identity, host paths or private input.
    """
    from django.conf import settings
    from .clients import verified_whisper_manifest
    from .config import options
    from .errors import PipelineFailure

    versions = {"SENA": None, "NARA": None, "Whisper": None, "Gemini": None}
    configured = {"sena_nara": False, "whisper": False, "gemini": False}
    try:
        config = options()
    except PipelineFailure:
        return {
            "models": [{"name": name, "version": value} for name, value in versions.items()],
            "configuration_present": configured, "capacity_limit": settings.ANALYSIS_CAPACITY,
        }
    try:
        runtime = reviewed_runtime(config)
        versions.update(SENA=runtime.versions["sena"], NARA=runtime.versions["nara"])
        configured["sena_nara"] = True
    except PipelineFailure:
        pass
    try:
        manifest = verified_whisper_manifest(config)
        versions["Whisper"] = "whisper-small|" + manifest["revision"]
        configured["whisper"] = True
    except PipelineFailure:
        pass
    if config.gemini_key.strip():
        versions["Gemini"] = config.gemini_model
        configured["gemini"] = True
    return {
        "models": [{"name": name, "version": value} for name, value in versions.items()],
        "configuration_present": configured, "capacity_limit": settings.ANALYSIS_CAPACITY,
    }
