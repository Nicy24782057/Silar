"""Pemuatan kandidat SENA/NARA terpilih; inferensi lokal tanpa training/backend.

Identitas berasal dari manifest ekspor kandidat, bukan asset_lock baseline.
Model hanya dimuat dari berkas lokal yang cocok hash; training_args.bin diabaikan.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import statistics
import sys
import time
import zipfile

from silar_ai_adapter import (
    ADAPTER_VERSION, EVENT_CATEGORIES, FUSION_VERSION, NARA_LABELS,
    adapt_legacy_ai_output, fuse_for_silar,
)
from slr09_runtime import (
    SilarModelRunner, build_adapter_input, environment_snapshot, read_records,
    sha256_file, text_digest, write_json,
)

CANDIDATE_RUNNER_VERSION = "silar-candidate-runtime-0.5.0"
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_CONFIG = "SLR09_Konfigurasi_Integrasi_v0.4.json"
CANDIDATE_LOCK = "quality_candidate_asset_lock_v0.7.json"
RUNTIME_FILES = frozenset({
    "config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
    "special_tokens_map.json", "vocab.txt",
})


def selected_assets(root=PACKAGE_ROOT):
    root = Path(root)
    config = json.loads((root / "config" / INTEGRATION_CONFIG).read_text())
    lock = json.loads((root / "config" / CANDIDATE_LOCK).read_text())
    profile = json.loads((root / "config/inference_environment.json").read_text())
    if config.get("adapter_version") != ADAPTER_VERSION or config.get("fusion_version") != FUSION_VERSION:
        raise ValueError("Versi adapter/Fusion tidak cocok dengan konfigurasi kandidat")
    threshold = config.get("confidence_threshold")
    if type(threshold) not in (float, int) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold kandidat tidak valid")
    if not isinstance(config.get("calibration_reference"), str) or not config["calibration_reference"].strip():
        raise ValueError("Rujukan pengukuran cutoff kandidat wajib tersedia")
    for name, expected_labels in (("sena", EVENT_CATEGORIES), ("nara", NARA_LABELS)):
        spec, candidate = lock["models"][name], config[name]
        for key in ("archive_sha256", "archive_name", "run_id", "labels"):
            if spec.get(key) != candidate.get(key):
                raise ValueError(f"{name}: lock kandidat dan konfigurasi berbeda pada {key}")
        if tuple(spec["labels"]) != tuple(expected_labels):
            raise ValueError(f"{name}: urutan label kandidat tidak sesuai adapter")
        if spec["files"].get("model.safetensors") != candidate["weights_sha256"]:
            raise ValueError(f"{name}: hash bobot kandidat tidak konsisten")
        if set(spec["files"]) != RUNTIME_FILES:
            raise ValueError(f"{name}: daftar berkas runtime kandidat tidak dikenal")
        for value in (spec["archive_sha256"], *spec["files"].values()):
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError(f"{name}: hash SHA-256 tidak valid")
    return config, lock, profile


def verify_candidate_directory(directory, name, spec):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"{name}: direktori kandidat lokal tidak tersedia")
    observed = {}
    for filename, expected in spec["files"].items():
        if filename not in RUNTIME_FILES:
            raise ValueError(f"{name}: berkas di luar whitelist runtime")
        path = directory / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{name}: berkas tidak tersedia: {filename}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"{name}: hash kandidat berbeda: {filename}")
        observed[filename] = actual
    model_config = json.loads((directory / "config.json").read_text())
    expected = {str(i): label for i, label in enumerate(spec["labels"])}
    if model_config.get("id2label") != expected:
        raise ValueError(f"{name}: label konfigurasi bobot tidak sesuai kandidat")
    return {"model_id": spec["model_id"], "run_id": spec["run_id"],
            "archive_sha256_expected": spec["archive_sha256"], "files": observed,
            "labels": spec["labels"], "candidate_directory_verified": True}


def extract_candidate_archive(archive, destination, name, spec):
    archive, destination = Path(archive), Path(destination)
    if not archive.is_file() or sha256_file(archive) != spec["archive_sha256"]:
        raise ValueError(f"{name}: arsip berbeda dari kandidat terpilih")
    if destination.is_symlink():
        raise ValueError("Direktori ekstraksi tidak boleh symlink")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for filename, expected in spec["files"].items():
            if filename not in RUNTIME_FILES or source.namelist().count(filename) != 1:
                raise ValueError(f"{name}: anggota runtime tidak tersedia/unik: {filename}")
            target = destination / filename
            if target.is_symlink():
                raise ValueError("Target ekstraksi tidak boleh symlink")
            if target.exists():
                if not target.is_file() or sha256_file(target) != expected:
                    raise ValueError(f"{name}: target sudah ada dan berbeda: {filename}")
                continue
            with source.open(filename) as stream, target.open("xb") as output:
                while chunk := stream.read(1024 * 1024):
                    output.write(chunk)
    evidence = verify_candidate_directory(destination, name, spec)
    evidence["archive_sha256_observed"] = sha256_file(archive)
    return evidence


def check_dependencies(profile, version_lookup=importlib.metadata.version):
    observed, problems = {}, []
    for name in profile["guard_packages"]:
        try:
            observed[name] = version_lookup(name)
        except importlib.metadata.PackageNotFoundError:
            observed[name] = None
        expected = profile["pinned_packages"][name]
        # Build CPU/CUDA PyTorch boleh berbeda suffix; versi pokok tetap sama.
        actual = observed[name]
        normalized = actual.split("+", 1)[0] if actual else None
        if normalized != expected:
            problems.append(f"{name}: perlu {expected}, tersedia {actual or 'belum terpasang'}")
    if problems:
        raise RuntimeError("Profil inference belum sesuai: " + "; ".join(problems))
    return observed


class CandidateModelRunner(SilarModelRunner):
    """Memakai algoritma inferensi historis dengan identitas kandidat eksplisit."""
    def __init__(self, sena_dir, nara_dir, *, root=PACKAGE_ROOT, device="cpu", cpu_threads=None):
        self.config, lock, profile = selected_assets(root)
        self.model_evidence = {name: verify_candidate_directory(directory, name, lock["models"][name])
                               for name, directory in (("sena", sena_dir), ("nara", nara_dir))}
        self.inference_versions = check_dependencies(profile)
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
        self.torch, self.device = torch, torch.device(device)
        if self.device.type not in {"cpu", "cuda"}:
            raise ValueError("Device harus cpu atau cuda")
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA diminta tetapi tidak tersedia")
        if cpu_threads is not None:
            if type(cpu_threads) is not int or cpu_threads < 1:
                raise ValueError("cpu_threads harus integer positif")
            torch.set_num_threads(cpu_threads)
        started = time.perf_counter()
        self.sena_tokenizer, self.sena_model = self._load(sena_dir, AutoTokenizer, AutoModelForSequenceClassification)
        self.nara_tokenizer, self.nara_model = self._load(nara_dir, AutoTokenizer, AutoModelForTokenClassification)
        self.sync()
        self.load_seconds = time.perf_counter() - started


def candidate_record(record, event_prediction, nara_tokens, config, lock):
    raw, trace = build_adapter_input(record["text"], event_prediction, nara_tokens)
    adapted = adapt_legacy_ai_output(raw, narrative_id=record["id"],
        sena_model_version=lock["models"]["sena"]["model_id"],
        nara_model_version=lock["models"]["nara"]["model_id"])
    fused = fuse_for_silar(adapted, confidence_threshold=config["confidence_threshold"],
        calibration_reference=config["calibration_reference"])
    return {"id": record["id"], "input_sha256": text_digest(record["text"]),
            "event_classifier": event_prediction, "adapted_result": adapted,
            "fusion_result": fused, "postprocessing_trace": trace}


def run_smoke(args):
    records = read_records(args.input)
    output = args.output_dir
    if output.exists() and any(output.iterdir()):
        raise ValueError("Gunakan direktori hasil kosong untuk menjaga bukti sebelumnya")
    output.mkdir(parents=True, exist_ok=True)
    summary_path, predictions_path = output / "run_summary.json", output / "predictions.jsonl"
    summary = {"schema": "slr09-candidate-smoke-0.2", "runner_version": CANDIDATE_RUNNER_VERSION,
        "status": "RUNNING", "input_sha256": sha256_file(args.input),
        "environment_label": args.environment_label, "environment_scope": args.environment_scope,
        "environment": environment_snapshot(), "training_executed": False,
        "model_inference_executed": False, "sena_inference_executed": False,
        "nara_inference_executed": False, "fusion_executed": False,
        "records_expected": len(records), "records_completed": 0,
        "production_deployed": False, "quality_acceptance_approved_by_this_run": False,
        "scope": "ASSET_LOADING_AND_SINGLE_PASS_INFERENCE_NOT_BACKEND_OR_QUALITY_ACCEPTANCE"}
    write_json(summary_path, summary)
    started, latencies, runner = time.perf_counter(), [], None
    try:
        config, lock, _ = selected_assets(args.root)
        summary["confidence_threshold"] = config["confidence_threshold"]
        summary["calibration_reference"] = config["calibration_reference"]
        summary["configuration_sha256"] = sha256_file(args.root / "config" / INTEGRATION_CONFIG)
        summary["candidate_lock_sha256"] = sha256_file(args.root / "config" / CANDIDATE_LOCK)
        runner = CandidateModelRunner(args.sena_dir, args.nara_dir, root=args.root,
                                      device=args.device, cpu_threads=args.cpu_threads)
        summary["models"], summary["model_load_seconds"] = runner.model_evidence, runner.load_seconds
        with predictions_path.open("x", encoding="utf-8") as stream:
            for record in records:
                runner.sync()
                before = time.perf_counter()
                event, sena_coverage = runner.predict_sena(record["text"])
                summary["model_inference_executed"] = summary["sena_inference_executed"] = True
                tokens, nara_coverage = runner.predict_nara(record["text"])
                summary["nara_inference_executed"] = True
                result = candidate_record(record, event, tokens, config, lock)
                summary["fusion_executed"] = True
                runner.sync()
                elapsed = time.perf_counter() - before
                result.update(sena_token_coverage=sena_coverage, nara_token_coverage=nara_coverage,
                              elapsed_seconds=elapsed)
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                latencies.append(elapsed)
                summary["records_completed"] += 1
        summary["status"] = "SUCCEEDED"
    except Exception as error:
        summary["status"] = "FAILED"
        summary["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        summary["wall_seconds_including_loading"] = time.perf_counter() - started
        if runner is not None:
            summary["environment"] = environment_snapshot(runner.torch, runner.device)
        if latencies:
            summary["per_record_seconds"] = {"min": min(latencies), "median": statistics.median(latencies),
                "max": max(latencies), "scope": "SINGLE_PASS_INCLUDING_FIRST_RECORD_NOT_CAPACITY_BENCHMARK"}
        if predictions_path.exists():
            summary["predictions_sha256"] = sha256_file(predictions_path)
        write_json(summary_path, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Verifikasi dan ekstrak kedua arsip kandidat")
    extract.add_argument("--root", type=Path, default=PACKAGE_ROOT)
    extract.add_argument("--sena-zip", type=Path, required=True)
    extract.add_argument("--nara-zip", type=Path, required=True)
    extract.add_argument("--output-dir", type=Path, required=True)
    run = commands.add_parser("smoke", help="Inferensi kedua kandidat dan adapter/Fusion terpilih")
    run.add_argument("--root", type=Path, default=PACKAGE_ROOT)
    run.add_argument("--sena-dir", type=Path, required=True)
    run.add_argument("--nara-dir", type=Path, required=True)
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    run.add_argument("--cpu-threads", type=int)
    run.add_argument("--environment-label", required=True)
    run.add_argument("--environment-scope", choices=("TARGET", "REPRESENTATIVE"), required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            _, lock, _ = selected_assets(args.root)
            if (args.output_dir / "extraction_evidence.json").exists():
                raise ValueError("Bukti ekstraksi sudah ada; gunakan direktori hasil baru")
            evidence = {name: extract_candidate_archive(path, args.output_dir / name, name, lock["models"][name])
                        for name, path in (("sena", args.sena_zip), ("nara", args.nara_zip))}
            write_json(args.output_dir / "extraction_evidence.json", evidence)
        else:
            result = run_smoke(args)
            print(json.dumps({"status": result["status"], "records_completed": result["records_completed"]}, indent=2))
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print(f"Kandidat belum siap: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
