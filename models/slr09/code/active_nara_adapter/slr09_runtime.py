"""Runner baseline historis SLR09 dan helper inferensi.

Untuk kandidat fine-tune baru gunakan slr09_candidate_runtime.py; identitas
asset_lock pada modul ini sengaja tetap milik baseline historis.

Inferensi saja; tidak melakukan training, menyimpan database, atau menjalankan
Fusion/Completeness lama. Impor PyTorch/Transformers ditunda hingga model dimuat.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import sys
import time
import zipfile

from silar_ai_adapter import (
    ADAPTER_VERSION, EVENT_CATEGORIES, NARA_LABELS, TOKEN_PATTERN,
    adapt_legacy_ai_output,
)

RUNNER_VERSION = "silar-runtime-0.5.0"
MAX_LENGTH = 256
HERE = Path(__file__).resolve().parent


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_records(path):
    records, ids = [], set()
    with Path(path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"Baris {number}: object diperlukan")
            key, text = record.get("id"), record.get("text")
            if not isinstance(key, str) or not key.strip() or key in ids:
                raise ValueError(f"Baris {number}: ID kosong/duplikat/tidak valid")
            if not isinstance(text, str) or not TOKEN_PATTERN.search(text):
                raise ValueError(f"Baris {number}: narasi tanpa token")
            if "gold_label" in record and record["gold_label"] not in EVENT_CATEGORIES:
                raise ValueError(f"Baris {number}: gold_label tidak dikenal")
            ids.add(key)
            records.append(record)
    if not records:
        raise ValueError("File input kosong")
    return records


def validate_prediction(prediction):
    if not isinstance(prediction, dict) or prediction.get("label") not in EVENT_CATEGORIES:
        raise ValueError("Prediksi SENA tidak valid")
    probabilities = prediction.get("probabilities")
    if not isinstance(probabilities, dict) or set(probabilities) != set(EVENT_CATEGORIES):
        raise ValueError("Probabilitas harus mencakup tepat lima kelas")
    numbers = [prediction.get("confidence"), *probabilities.values()]
    if any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1 for x in numbers):
        raise ValueError("Confidence/probabilitas harus angka finite 0..1")
    confidence = prediction["confidence"]
    if not math.isclose(sum(probabilities.values()), 1.0, abs_tol=1e-6):
        raise ValueError("Jumlah probabilitas tidak mendekati satu")
    if not math.isclose(confidence, probabilities[prediction["label"]], abs_tol=1e-6):
        raise ValueError("Confidence berbeda dari probabilitas label")
    if confidence + 1e-6 < max(probabilities.values()):
        raise ValueError("Label bukan argmax probabilitas")


def asset_lock():
    return json.loads((HERE / "asset_lock.json").read_text(encoding="utf-8"))


def verify_model_directory(directory, name):
    directory = Path(directory).resolve(strict=True)
    spec = asset_lock()["models"][name]
    observed = {}
    for filename, expected_hash in spec["files"].items():
        path = directory / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"{name}: berkas lokal tidak tersedia: {filename}")
        actual = sha256_file(path)
        if actual != expected_hash:
            raise ValueError(f"{name}: hash {filename} berbeda dari aset yang diaudit")
        observed[filename] = actual
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    labels = tuple(config["id2label"][str(i)] for i in range(len(spec["labels"])))
    if labels != tuple(spec["labels"]):
        raise ValueError(f"{name}: urutan label berbeda")
    return {"files": observed, "labels": list(labels), "model_id": spec["model_id"]}


def extract_model_archive(archive_path, destination, name):
    """Ekstrak hanya berkas runtime flat yang hash-nya telah dikunci."""
    archive_path, destination = Path(archive_path), Path(destination)
    spec = asset_lock()["models"][name]
    if sha256_file(archive_path) != spec["archive_sha256"]:
        raise ValueError(f"{name}: ZIP berbeda dari paket model yang diaudit")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for filename in spec["files"]:
            if names.count(filename) != 1:
                raise ValueError(f"{name}: anggota ZIP tidak unik: {filename}")
            target = destination / filename
            if target.is_symlink():
                raise ValueError("Target ekstraksi tidak boleh symlink")
            if target.exists():
                if sha256_file(target) != spec["files"][filename]:
                    raise ValueError(f"Target sudah ada dan berbeda: {target}")
                continue
            with archive.open(filename) as source, target.open("xb") as stream:
                shutil.copyfileobj(source, stream)
    # training_args.bin tidak dibaca atau dideserialisasi.
    return verify_model_directory(destination, name)


def encode_nara_words(tokens, tokenizer, max_length=MAX_LENGTH):
    """Algoritma srl_encode_words notebook lama, dengan dependency eksplisit."""
    input_ids = [tokenizer.cls_token_id]
    positions = []
    partial_last_word = False
    for word in tokens:
        pieces = tokenizer.tokenize(str(word))
        if not pieces:
            pieces = [tokenizer.unk_token]
        piece_ids = tokenizer.convert_tokens_to_ids(pieces)
        remaining = max_length - 1 - len(input_ids)
        if remaining <= 0:
            break
        partial_last_word = len(piece_ids) > remaining
        piece_ids = piece_ids[:remaining]
        positions.append(len(input_ids))
        input_ids.extend(piece_ids)
    input_ids.append(tokenizer.sep_token_id)
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "positions": positions,
        "partial_last_word": partial_last_word,
    }


def build_adapter_input(text, event_prediction, nara_tokens):
    """Bangun input dari span mentah, guard lokal dan fallback waktu literal."""
    import legacy_postprocessing as legacy
    from silar_victim_guard import apply_reviewed_victim_safety, VICTIM_GUARD_VERSION
    spans_before_guard = legacy.all_srl_spans(nara_tokens)
    spans, safety_flags = apply_reviewed_victim_safety(text, deepcopy(spans_before_guard))
    time_values = legacy.span_texts(spans, "TIME-ARG")
    time_source = "SRL"
    if not time_values:
        time_values = [legacy.normalize_display_text(item["text"]) for item in legacy.time_fallback(text)]
        from silar_postprocessing import supplemental_time_fallback
        extra = supplemental_time_fallback(text[:nara_tokens[-1]['end']] if nara_tokens else '')
        time_values = [value for value in time_values if not any(value.casefold() in longer.casefold() for longer in extra if value.casefold()!=longer.casefold())]
        time_values += [value for value in extra if value not in time_values]
        time_source = "DETERMINISTIC_FALLBACK" if time_values else "MISSING"
    return {
        "report_text": text,
        "event_classifier": event_prediction,
        "srl_token_predictions": nara_tokens,
        "srl_spans": spans,
        "incident_card": {"time": time_values, "time_source": time_source},
    }, {"spans_before_guard": spans_before_guard, "victim_safety_flags": safety_flags,
        "victim_guard_version": VICTIM_GUARD_VERSION}


def environment_snapshot(torch=None, device=None):
    versions = {}
    for name in ("torch", "transformers", "tokenizers", "safetensors", "numpy", "pandas", "scikit-learn", "iterative-stratification"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    snapshot = {
        "python": platform.python_version(), "platform": platform.platform(),
        "machine": platform.machine(), "cpu_count": os.cpu_count(),
        "packages": versions, "device": str(device) if device is not None else None,
        "peak_process_rss_bytes": None,
        "measurement_scope": "PROCESS_ON_OBSERVED_ENVIRONMENT_NOT_AUTOMATIC_TARGET_VM_PROOF",
    }
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmHWM:"):
                snapshot["peak_process_rss_bytes"] = int(line.split()[1]) * 1024
    if torch is not None:
        snapshot["torch_num_threads"] = torch.get_num_threads()
        snapshot["cuda_available"] = torch.cuda.is_available()
        snapshot["cuda_runtime"] = torch.version.cuda
        if device is not None and device.type == "cuda":
            snapshot["gpu_name"] = torch.cuda.get_device_name(device)
            snapshot["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(device)
    return snapshot


class SilarModelRunner:
    def __init__(self, sena_dir, nara_dir=None, *, device="cpu", cpu_threads=None):
        self.model_evidence = {"sena": verify_model_directory(sena_dir, "sena")}
        if nara_dir is not None:
            self.model_evidence["nara"] = verify_model_directory(nara_dir, "nara")
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
        except ImportError as error:
            raise RuntimeError("PyTorch/Transformers belum siap; gunakan environment runtime pada petunjuk") from error
        if importlib.metadata.version("transformers") != "5.13.1":
            raise RuntimeError("Runner ini disiapkan untuk transformers==5.13.1 sesuai metadata aset")
        self.torch = torch
        self.device = torch.device(device)
        if self.device.type not in {"cpu", "cuda"}:
            raise ValueError("Pilih cpu atau cuda secara eksplisit")
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA diminta tetapi tidak tersedia; tidak berpindah device diam-diam")
        if cpu_threads is not None:
            if type(cpu_threads) is not int or cpu_threads < 1:
                raise ValueError("cpu_threads harus integer positif")
            torch.set_num_threads(cpu_threads)
        started = time.perf_counter()
        self.sena_tokenizer, self.sena_model = self._load(sena_dir, AutoTokenizer, AutoModelForSequenceClassification)
        self.nara_tokenizer = self.nara_model = None
        if nara_dir is not None:
            self.nara_tokenizer, self.nara_model = self._load(nara_dir, AutoTokenizer, AutoModelForTokenClassification)
        self.sync()
        self.load_seconds = time.perf_counter() - started

    def _load(self, directory, tokenizer_class, model_class):
        path = str(Path(directory).resolve(strict=True))
        tokenizer = tokenizer_class.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        model, loading = model_class.from_pretrained(
            path, local_files_only=True, trust_remote_code=False,
            use_safetensors=True, dtype=self.torch.float32, output_loading_info=True,
        )
        for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"):
            if loading.get(key):
                raise RuntimeError(f"Pemuatan {model_class.__name__} tidak lengkap: {key}: {loading[key]}")
        model.to(self.device)
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        return tokenizer, model

    def sync(self):
        if self.device.type == "cuda":
            self.torch.cuda.synchronize(self.device)

    def predict_sena(self, text):
        torch = self.torch
        full_ids = self.sena_tokenizer(text, truncation=False, add_special_tokens=True)["input_ids"]
        encoded = self.sena_tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)
        inputs = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.inference_mode():
            logits = self.sena_model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1)
        pred_id = int(probabilities.argmax().item())
        labels = self.model_evidence["sena"]["labels"]
        result = {
            "label": labels[pred_id], "confidence": float(probabilities[pred_id].item()),
            "probabilities": {labels[index]: float(probabilities[index].item()) for index in range(len(labels))},
        }
        validate_prediction(result)
        return result, {
            "source_wordpieces_with_special_tokens": len(full_ids),
            "processed_wordpieces_with_special_tokens": int(inputs["input_ids"].shape[1]),
            "truncated": len(full_ids) > MAX_LENGTH,
        }

    def predict_nara(self, text):
        if self.nara_model is None:
            raise RuntimeError("NARA belum dimuat")
        torch = self.torch
        token_items = [{"token": match.group().lower(), "original": match.group(),
                        "start": match.start(), "end": match.end()} for match in TOKEN_PATTERN.finditer(text)]
        encoded = encode_nara_words([item["token"] for item in token_items], self.nara_tokenizer)
        inputs = {
            key: torch.tensor([encoded[key]], dtype=torch.long, device=self.device)
            for key in ("input_ids", "attention_mask")
        }
        with torch.inference_mode():
            logits = self.nara_model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1)
        labels, output = self.model_evidence["nara"]["labels"], []
        for index, position in enumerate(encoded["positions"]):
            pred_id = int(probabilities[position].argmax().item())
            output.append({**token_items[index], "label": labels[pred_id],
                           "confidence": float(probabilities[position, pred_id].item())})
        return output, {
            "source_regex_tokens": len(token_items), "processed_regex_tokens": len(output),
            "all_regex_tokens_processed": len(token_items) == len(output),
            "last_wordpiece_sequence_partial": encoded["partial_last_word"],
            "processed_wordpieces_with_special_tokens": len(encoded["input_ids"]),
            "alignment": "FIRST_WORDPIECE_LEGACY_INFERENCE_NOT_PROOF_OF_TRAINING_ALIGNMENT",
        }


def run_inference(args):
    records = read_records(args.input)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    prediction_path, summary_path = out / "predictions.jsonl", out / "run_summary.json"
    if prediction_path.exists() or summary_path.exists():
        raise ValueError("Folder hasil sudah berisi run; gunakan folder baru agar bukti sebelumnya terjaga")
    started = time.perf_counter()
    runner = None
    latencies = []
    count = 0
    summary = {
        "runner_version": RUNNER_VERSION, "adapter_version": ADAPTER_VERSION,
        "mode": args.command, "status": "RUNNING", "input_sha256": sha256_file(args.input),
        "model_inference_executed": False, "training_executed": False,
        "production_threshold_selected": False, "fusion_executed": False,
        "environment_label": args.environment_label,
        "environment": environment_snapshot(), "records_expected": len(records),
    }
    write_json(summary_path, summary)
    try:
        runner = SilarModelRunner(args.sena_dir, args.nara_dir if args.command == "smoke" else None,
                                  device=args.device, cpu_threads=args.cpu_threads)
        summary["models"] = runner.model_evidence
        summary["model_load_seconds"] = runner.load_seconds
        with prediction_path.open("x", encoding="utf-8") as stream:
            for record in records:
                runner.sync()
                before = time.perf_counter()
                event_prediction, sena_tokens = runner.predict_sena(record["text"])
                # Prediksi neural pertama benar-benar sudah terjadi.
                summary["model_inference_executed"] = True
                result = {"id": record["id"], "input_sha256": text_digest(record["text"]),
                          "event_classifier": event_prediction, "sena_token_coverage": sena_tokens}
                if args.command == "smoke":
                    nara_tokens, coverage = runner.predict_nara(record["text"])
                    legacy_input, trace = build_adapter_input(record["text"], event_prediction, nara_tokens)
                    result["adapted_result"] = adapt_legacy_ai_output(
                        legacy_input, narrative_id=record["id"],
                        sena_model_version="SILAR_SENA_v1", nara_model_version="SILAR_NARA_v1",
                    )
                    result["nara_token_coverage"] = coverage
                    result["postprocessing_trace"] = trace
                    result["fusion_not_executed_reason"] = "PRODUCTION_THRESHOLD_NOT_CALIBRATED"
                runner.sync()
                result["elapsed_seconds"] = time.perf_counter() - before
                latencies.append(result["elapsed_seconds"])
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                count += 1
                if count == 1 or count % 25 == 0 or count == len(records):
                    print(f"{args.command}: {count}/{len(records)}", flush=True)
        summary["status"] = "SUCCEEDED"
    except Exception as error:
        summary["status"] = "FAILED"
        summary["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        summary["records_completed"] = count
        summary["wall_seconds_including_loading"] = time.perf_counter() - started
        if runner is not None:
            summary["environment"] = environment_snapshot(runner.torch, runner.device)
        if latencies:
            summary["per_record_seconds_including_first_record"] = {
                "min": min(latencies), "median": statistics.median(latencies),
                "mean": statistics.mean(latencies), "max": max(latencies),
                "scope": "SINGLE_PASS_NOT_STEADY_STATE_OR_CONCURRENT_BACKEND_BENCHMARK",
            }
        if prediction_path.exists():
            summary["predictions_sha256"] = sha256_file(prediction_path)
        write_json(summary_path, summary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Verifikasi ZIP dan ekstrak berkas runtime yang dikunci")
    extract.add_argument("--sena-zip", type=Path, required=True)
    extract.add_argument("--nara-zip", type=Path, required=True)
    extract.add_argument("--output-dir", type=Path, required=True)
    for command in ("smoke", "sena"):
        run = commands.add_parser(command)
        run.add_argument("--sena-dir", type=Path, required=True)
        if command == "smoke":
            run.add_argument("--nara-dir", type=Path, required=True)
        run.add_argument("--input", type=Path, required=True)
        run.add_argument("--output-dir", type=Path, required=True)
        run.add_argument("--device", choices=("cpu", "cuda"), required=True)
        run.add_argument("--cpu-threads", type=int)
        run.add_argument("--environment-label", required=True)
    args = parser.parse_args(argv)
    if args.command == "extract":
        evidence = {name: extract_model_archive(path, args.output_dir / name, name)
                    for name, path in (("sena", args.sena_zip), ("nara", args.nara_zip))}
        write_json(args.output_dir / "extraction_evidence.json", evidence)
    else:
        run_inference(args)


if __name__ == "__main__":
    main()
