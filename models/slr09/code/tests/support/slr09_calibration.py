"""Rekonstruksi kandidat validation SENA dan tabel threshold untuk ditinjau.

Tidak melatih model, memakai held-out test untuk tuning, memilih threshold
otomatis, atau mengubah konfigurasi produksi.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import zipfile

from silar_ai_adapter import EVENT_CATEGORIES
from slr09_runtime import (
    asset_lock, read_records, sha256_file, text_digest,
    validate_prediction, write_json,
)

CALIBRATION_VERSION = "silar-threshold-analysis-0.1.0"
SPLIT_STATUS = "CANDIDATE_VALIDATION_RECONSTRUCTED_HISTORICAL_IDENTITY_UNVERIFIED"
EVENT_ROLE_TO_CLASS = {
    "FLOOD-EVENT": "FLOOD", "EARTHQUAKE-EVENT": "EARTHQUAKE",
    "FIRE-EVENT": "FIRE", "ACCIDENT-EVENT": "ACCIDENT",
}


def derive_records(dataset_zip):
    """Urutan grouping/cleaning/label mengikuti notebook V3A yang diberikan."""
    import pandas as pd
    lock = asset_lock()["dataset"]
    if sha256_file(dataset_zip) != lock["archive_sha256"]:
        raise ValueError("ZIP dataset berbeda dari versi yang telah diaudit")
    with zipfile.ZipFile(dataset_zip) as archive:
        candidates = [name for name in archive.namelist()
                      if name.endswith("3-Labeled Data/all-labeled-data.csv") and "Version 2.0" not in name]
        if len(candidates) != 1:
            raise ValueError("CSV berlabel Indonesia tidak unik")
        member = candidates[0]
        content = archive.read(member)
    if hashlib.sha256(content).hexdigest() != lock["csv_sha256"]:
        raise ValueError("Hash CSV sumber tidak cocok")
    frame = pd.read_csv(io.BytesIO(content))
    if len(frame) != 99206 or frame["text_id"].nunique() != 4150:
        raise ValueError("Ukuran dataset berbeda dari audit")
    clean = frame[frame["token"].notna()].copy().reset_index(drop=True)
    records = []
    for text_id, group in clean.groupby("text_id", sort=False):
        roles = set(group["argument"].astype(str).tolist())
        true_roles = sorted(roles & set(EVENT_ROLE_TO_CLASS))
        false_event = "FALSE-EVENT" in roles
        label, reason = None, ""
        if len(true_roles) == 1 and not false_event:
            label = EVENT_ROLE_TO_CLASS[true_roles[0]]
        elif not true_roles and false_event:
            label = "NON_EVENT"
        elif len(true_roles) > 1:
            reason = "MULTIPLE_TRUE_EVENTS"
        elif true_roles and false_event:
            reason = "TRUE_PLUS_FALSE"
        else:
            reason = "NO_EVENT_SIGNAL"
        records.append({
            "id": str(text_id), "text": " ".join(group["token"].astype(str).tolist()),
            "gold_label": label, "exclusion_reason": reason,
            "official_split": "test" if int(str(text_id).split("-")[1]) <= 250 else "train_pool",
        })
    if len(clean) != 99202 or len(records) != 4150:
        raise ValueError("Cleaning sumber berbeda dari audit")
    return records, {"csv_member": member, "raw_rows": len(frame), "clean_rows": len(clean),
                     "texts": len(records), "blank_token_rows_removed": len(frame) - len(clean)}


def prepare_candidate_split(dataset_zip, output_dir):
    import numpy as np
    from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
    if importlib.metadata.version("iterative-stratification") != "0.1.9":
        raise ValueError("Rekonstruksi ini disiapkan dengan iterative-stratification==0.1.9")
    records, source = derive_records(dataset_zip)
    usable = [record for record in records if record["gold_label"] is not None]
    pool = [record for record in usable if record["official_split"] == "train_pool"]
    test = [record for record in usable if record["official_split"] == "test"]
    if (len(usable), len(pool), len(test)) != (4096, 3110, 986):
        raise ValueError("Jumlah pool SENA tidak cocok dengan audit")
    labels = np.array([EVENT_CATEGORIES.index(record["gold_label"]) for record in pool])
    y = np.eye(len(EVENT_CATEGORIES))[labels]
    x = np.arange(len(pool)).reshape(-1, 1)
    splitter = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, validation_idx = next(splitter.split(x, y))
    train = [pool[int(index)] for index in train_idx]
    validation = [pool[int(index)] for index in validation_idx]
    split_ids = {name: [record["id"] for record in rows]
                 for name, rows in (("train", train), ("validation", validation), ("test", test))}
    a, b, c = (set(split_ids[name]) for name in ("train", "validation", "test"))
    if a & b or a & c or b & c or (a | b) != {record["id"] for record in pool}:
        raise ValueError("Kebocoran/kekurangan ID pada rekonstruksi split")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filenames = ("candidate_validation.jsonl", "train_ids.json", "validation_ids.json", "test_ids.json", "split_manifest.json")
    if any((output_dir / name).exists() for name in filenames):
        raise ValueError("Bukti split sudah tersedia; gunakan folder baru")
    validation_path = output_dir / "candidate_validation.jsonl"
    with validation_path.open("x", encoding="utf-8") as stream:
        for record in validation:
            stream.write(json.dumps({key: record[key] for key in ("id", "text", "gold_label")}, ensure_ascii=False) + "\n")
    for name, values in split_ids.items():
        write_json(output_dir / f"{name}_ids.json", values)
    manifest = {
        "analysis_version": CALIBRATION_VERSION, "split_status": SPLIT_STATUS,
        "historical_split_identity_verified": False,
        "production_threshold_can_be_finalized_from_this_artifact_alone": False,
        "reason": "SENA tidak mengekspor ID train/validation; versi dependency saat training tidak terkunci dalam notebook lama.",
        "method": "V3A minimal cleaning, derived single label, official prefix split, iterative stratifier",
        "seed": 42, "validation_fraction": 0.20,
        "nara_validation_ids_used_for_sena": False,
        "held_out_test_used_for_tuning": False, "blind_test_used": False,
        "source": {**source, "dataset_archive_sha256": sha256_file(dataset_zip),
                   "csv_sha256": asset_lock()["dataset"]["csv_sha256"],
                   "training_notebook_sha256": asset_lock()["source_notebooks"]["sena_training_sha256"]},
        "counts": {"all": len(records), "usable": len(usable), "excluded": len(records) - len(usable),
                   "train": len(train), "validation": len(validation), "test_excluded_from_tuning": len(test)},
        "class_counts": {name: dict(Counter(record["gold_label"] for record in rows))
                         for name, rows in (("train", train), ("validation", validation), ("test_not_used", test))},
        "versions": {name: importlib.metadata.version(name)
                     for name in ("numpy", "pandas", "scikit-learn", "iterative-stratification")},
        "files_sha256": {name: sha256_file(output_dir / name) for name in filenames if name != "split_manifest.json"},
        "production_confidence_threshold": None,
    }
    write_json(output_dir / "split_manifest.json", manifest)
    return manifest


def threshold_table(pairs):
    """Semantik A4.22.1: uncertain bila confidence < threshold; tidak unblock NON_EVENT."""
    thresholds = sorted({0.0, 1.0, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99,
                         *(prediction["confidence"] for _, prediction in pairs)})
    rows = []
    for threshold in thresholds:
        above = [(gold, pred) for gold, pred in pairs if pred["confidence"] >= threshold]
        below = [(gold, pred) for gold, pred in pairs if pred["confidence"] < threshold]
        above_correct = sum(gold == pred["label"] for gold, pred in above)
        row = {
            "threshold": threshold, "n_total": len(pairs),
            "n_above_or_equal": len(above), "n_below": len(below),
            "fraction_above_or_equal": len(above) / len(pairs),
            "correct_above_or_equal": above_correct,
            "accuracy_above_or_equal": above_correct / len(above) if above else None,
            "errors_above_or_equal": len(above) - above_correct,
            "errors_below": sum(gold != pred["label"] for gold, pred in below),
            "false_non_event_above_or_equal": sum(gold != "NON_EVENT" and pred["label"] == "NON_EVENT" for gold, pred in above),
            "false_non_event_below": sum(gold != "NON_EVENT" and pred["label"] == "NON_EVENT" for gold, pred in below),
        }
        rows.append(row)
    return rows


def summarize_predictions(input_path, predictions_path, run_summary_path, split_manifest_path, output_dir):
    inputs = read_records(input_path)
    source = json.loads(Path(split_manifest_path).read_text(encoding="utf-8"))
    run = json.loads(Path(run_summary_path).read_text(encoding="utf-8"))
    if source.get("split_status") != SPLIT_STATUS or source.get("historical_split_identity_verified") is not False:
        raise ValueError("Gunakan manifest kandidat validation yang dihasilkan skrip ini")
    if source["files_sha256"]["candidate_validation.jsonl"] != sha256_file(input_path):
        raise ValueError("Input validation berbeda dari manifest")
    if run.get("status") != "SUCCEEDED" or run.get("mode") != "sena" or run.get("model_inference_executed") is not True:
        raise ValueError("Diperlukan run inferensi SENA aktual yang selesai")
    if run.get("input_sha256") != sha256_file(input_path) or run.get("predictions_sha256") != sha256_file(predictions_path):
        raise ValueError("Hash input/prediksi berbeda dari bukti run")
    if run["models"]["sena"]["files"] != asset_lock()["models"]["sena"]["files"]:
        raise ValueError("Model runtime bukan aset SENA yang dikunci")
    input_ids = [record["id"] for record in inputs]
    validation_ids_path = Path(split_manifest_path).parent / "validation_ids.json"
    if sha256_file(validation_ids_path) != source["files_sha256"]["validation_ids.json"]:
        raise ValueError("Daftar ID validation berubah")
    if json.loads(validation_ids_path.read_text(encoding="utf-8")) != input_ids:
        raise ValueError("ID input berbeda dari kandidat validation")
    for name in ("train", "test"):
        path = Path(split_manifest_path).parent / f"{name}_ids.json"
        if sha256_file(path) != source["files_sha256"][f"{name}_ids.json"]:
            raise ValueError(f"Daftar ID {name} berubah")
        if set(input_ids) & set(json.loads(path.read_text(encoding="utf-8"))):
            raise ValueError(f"ID kandidat validation tumpang tindih dengan {name}")
    expected = {record["id"]: record for record in inputs}
    seen, pairs, errors = set(), [], []
    confusion = {gold: {pred: 0 for pred in EVENT_CATEGORIES} for gold in EVENT_CATEGORIES}
    with Path(predictions_path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("id")
            if key not in expected or key in seen:
                raise ValueError("ID prediksi asing atau duplikat")
            seen.add(key)
            record = expected[key]
            if row.get("input_sha256") != text_digest(record["text"]):
                raise ValueError("Prediksi berasal dari narasi yang berbeda")
            prediction = row["event_classifier"]
            validate_prediction(prediction)
            gold = record.get("gold_label")
            if gold not in EVENT_CATEGORIES:
                raise ValueError("Gold label validation belum tersedia")
            pairs.append((gold, prediction))
            confusion[gold][prediction["label"]] += 1
            if gold != prediction["label"]:
                errors.append({"id": key, "text": record["text"], "gold_label": gold,
                               "predicted_label": prediction["label"], "confidence": prediction["confidence"]})
    if seen != set(expected) or run.get("records_completed") != len(inputs):
        raise ValueError("Prediksi validation tidak lengkap")
    per_class = {}
    for label in EVENT_CATEGORIES:
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        predicted = sum(confusion[gold][label] for gold in EVENT_CATEGORIES)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        per_class[label] = {"support": support, "precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}
    curve = threshold_table(pairs)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if any((output_dir / name).exists() for name in ("threshold_candidates.csv", "threshold_analysis.json", "classification_errors.json")):
        raise ValueError("Analisis sudah ada; gunakan folder hasil baru")
    with (output_dir / "threshold_candidates.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(curve[0]))
        writer.writeheader()
        writer.writerows(curve)
    write_json(output_dir / "classification_errors.json", errors)
    gold_events = sum(gold != "NON_EVENT" for gold, _ in pairs)
    false_non_events = sum(gold != "NON_EVENT" and pred["label"] == "NON_EVENT" for gold, pred in pairs)
    result = {
        "analysis_version": CALIBRATION_VERSION, "status": "EXPLORATORY_THRESHOLD_ANALYSIS_REQUIRES_REVIEW",
        "split_status": SPLIT_STATUS, "historical_split_identity_verified": False,
        "production_confidence_threshold": None, "production_threshold_selected": False,
        "records": len(pairs), "accuracy": sum(gold == pred["label"] for gold, pred in pairs) / len(pairs),
        "macro_f1_all_five_classes": sum(value["f1"] for value in per_class.values()) / len(EVENT_CATEGORIES),
        "per_class": per_class, "confusion_matrix_rows_gold_columns_prediction": confusion,
        "gold_event_count": gold_events, "false_non_event_count": false_non_events,
        "false_non_event_rate_among_gold_events": false_non_events / gold_events if gold_events else None,
        "threshold_candidate_count": len(curve),
        "interpretation": [
            "Confidence di bawah threshold hanya menandai LOW_CLASSIFICATION_CONFIDENCE.",
            "Keluaran NON_EVENT tetap diblokir pada semua threshold, termasuk bila confidence rendah.",
            "Above-threshold tidak berarti auto-confirmed atau boleh melewati Human Verification.",
            "Tidak ada target mutu atau threshold produksi yang ditetapkan otomatis.",
            "Ini analisis cutoff; tidak melakukan temperature scaling atau kalibrasi probabilitas terlatih.",
            "Identitas split historis belum terbukti; hasil ini sendiri belum cukup untuk penguncian threshold produksi.",
        ],
        "evidence_sha256": {"validation_input": sha256_file(input_path), "predictions": sha256_file(predictions_path),
                            "run_summary": sha256_file(run_summary_path), "split_manifest": sha256_file(split_manifest_path)},
    }
    write_json(output_dir / "threshold_analysis.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--dataset-zip", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--input", type=Path, required=True)
    summarize.add_argument("--predictions", type=Path, required=True)
    summarize.add_argument("--run-summary", type=Path, required=True)
    summarize.add_argument("--split-manifest", type=Path, required=True)
    summarize.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare_candidate_split(args.dataset_zip, args.output_dir)
        print(json.dumps({"status": result["split_status"], "counts": result["counts"]}, ensure_ascii=False, indent=2))
    else:
        result = summarize_predictions(args.input, args.predictions, args.run_summary, args.split_manifest, args.output_dir)
        print(json.dumps({key: result[key] for key in ("status", "records", "accuracy", "macro_f1_all_five_classes", "production_confidence_threshold")}, indent=2))


if __name__ == "__main__":
    main()
