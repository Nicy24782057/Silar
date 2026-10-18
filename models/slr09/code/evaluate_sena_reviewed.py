"""Evaluate saved SENA predictions against the completed B1 review.

No model, training, new neural inference, probability fitting, or production
threshold selection is performed. This analysis adds the 620 final human
references; the previous analysis used 71 reviewed and 552 original references.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


LABELS = ["FLOOD", "EARTHQUAKE", "FIRE", "ACCIDENT", "NON_EVENT"]
THRESHOLDS = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
SENA_WEIGHTS_SHA256 = "ae7ceb9959b7f0f3c55a6babd2cf73759a1d9458daadb654ca2fb68ca25cc4dc"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def jsonl(raw: bytes) -> list[dict]:
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def unique_index(rows: list[dict], label: str) -> dict[str, dict]:
    result = {row["id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate IDs: {label}")
    return result


def score(gold: list[str], pred: list[str]) -> dict:
    if len(gold) != len(pred) or not gold:
        raise ValueError("Gold/prediction coverage differs or is empty")
    index = {label: i for i, label in enumerate(LABELS)}
    matrix = [[0 for _ in LABELS] for _ in LABELS]
    for g, p in zip(gold, pred):
        if g not in index or p not in index:
            raise ValueError("Unknown SENA category")
        matrix[index[g]][index[p]] += 1
    report = {}
    for i, label in enumerate(LABELS):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * tp / (support + predicted) if support + predicted else 0.0
        report[label] = dict(support=support, predicted=predicted, precision=precision, recall=recall, f1=f1)
    correct = sum(matrix[i][i] for i in range(len(LABELS)))
    event_count = sum(g != "NON_EVENT" for g in gold)
    false_non_event = sum(g != "NON_EVENT" and p == "NON_EVENT" for g, p in zip(gold, pred))
    false_event = sum(g == "NON_EVENT" and p != "NON_EVENT" for g, p in zip(gold, pred))
    wrong_event_type = sum(g != p and g != "NON_EVENT" and p != "NON_EVENT" for g, p in zip(gold, pred))
    return {
        "records": len(gold), "correct": correct, "incorrect": len(gold) - correct,
        "accuracy": correct / len(gold),
        "macro_f1_all_five_classes": sum(v["f1"] for v in report.values()) / len(LABELS),
        "weighted_f1": sum(v["f1"] * v["support"] for v in report.values()) / len(gold),
        "per_class": report,
        "labels": LABELS, "confusion_matrix_rows_gold_columns_prediction": matrix,
        "gold_event_count": event_count, "false_non_event_count": false_non_event,
        "false_non_event_rate_among_gold_events": false_non_event / event_count if event_count else None,
        "false_event_count": false_event, "wrong_event_type_count": wrong_event_type,
    }


def cutoff_analysis(rows: list[dict]) -> list[dict]:
    results = []
    for threshold in THRESHOLDS:
        high = [r for r in rows if r["confidence"] >= threshold]
        low = [r for r in rows if r["confidence"] < threshold]
        correct_high = sum(r["gold"] == r["prediction"] for r in high)
        errors_high = len(high) - correct_high
        errors_low = sum(r["gold"] != r["prediction"] for r in low)
        all_errors = errors_high + errors_low
        results.append({
            "threshold": threshold,
            "below_threshold_uncertain": len(low), "at_or_above_threshold": len(high),
            "coverage_at_or_above": len(high) / len(rows),
            "correct_at_or_above": correct_high,
            "accuracy_at_or_above": correct_high / len(high) if high else None,
            "errors_at_or_above": errors_high,
            "errors_below_threshold": errors_low,
            "fraction_of_errors_flagged": errors_low / all_errors if all_errors else None,
            "false_non_event_at_or_above": sum(r["gold"] != "NON_EVENT" and r["prediction"] == "NON_EVENT" for r in high),
            "non_event_predictions_blocked_total": sum(r["prediction"] == "NON_EVENT" for r in rows),
        })
    return results


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    columns = columns or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(runtime_zip: Path, review_jsonl: Path, review_checkpoint: Path,
             review_manifest: Path, reviewed_workbook: Path, output: Path) -> dict:
    raw_review = review_jsonl.read_bytes()
    review = jsonl(raw_review)
    cp = json.loads(review_checkpoint.read_bytes())
    manifest_bytes = review_manifest.read_bytes()
    workbook_bytes = reviewed_workbook.read_bytes()
    checks = []

    def require(condition: bool, name: str) -> None:
        checks.append({"check": name, "passed": bool(condition)})
        if not condition:
            raise ValueError(name)

    require(digest(manifest_bytes) == cp["manifest_sha256"], "frozen review manifest SHA-256")
    require(digest(workbook_bytes) == cp["workbook_sha256"], "human-reviewed workbook SHA-256")
    require(not cp["validation_errors"], "review checkpoint contains no validation errors")
    approved = [r for r in cp["approved"] if r.get("cohort") == "sena_validation"]
    require(unique_index(review, "review JSONL") == unique_index(approved, "checkpoint approved"),
            "620 exported references exactly match approved checkpoint")
    require(len(review) == 620, "620 final SENA references")
    require(all(r["status"] in {"REVIEW_TERCATAT", "FINAL_TERWARIS"} for r in review),
            "only final human review statuses scored")
    require(all(r["final"] in LABELS for r in review), "all reviewed categories recognized")
    pending = [r for r in cp["pending"] if r["sheet"] == "SENA_Validation"]
    require({r["id"] for r in pending} == {"BAN-01028", "KEB-01113", "BAN-01529"},
            "three deferred SENA cases unchanged and excluded")

    with ZipFile(runtime_zip) as archive:
        require(archive.testzip() is None, "runtime archive CRC")
        candidate_bytes = archive.read("results/candidate_split/candidate_validation.jsonl")
        prediction_bytes = archive.read("results/sena_validation/predictions.jsonl")
        split = json.loads(archive.read("results/candidate_split/split_manifest.json"))
        run = json.loads(archive.read("results/sena_validation/run_summary.json"))
        require(digest(candidate_bytes) == split["files_sha256"]["candidate_validation.jsonl"],
                "candidate narrative snapshot SHA-256")
        require(digest(prediction_bytes) == run["predictions_sha256"], "saved predictions SHA-256")
        require(run["status"] == "SUCCEEDED" and run["records_completed"] == 623,
                "successful 623-record original SENA inference")
        require(run["models"]["sena"]["files"]["model.safetensors"] == SENA_WEIGHTS_SHA256,
                "fixed SENA v1 weight identity in original run")
    candidate = unique_index(jsonl(candidate_bytes), "candidate narratives")
    predictions = unique_index(jsonl(prediction_bytes), "saved predictions")
    require(set(candidate) == set(predictions) and len(candidate) == 623, "all original candidate IDs covered")
    require(set(candidate) == {r["id"] for r in review} | {r["id"] for r in pending},
            "620 scored plus three omitted cover exactly the original 623")
    rows = []
    for ref in review:
        rid = ref["id"]
        case = candidate[rid]
        prediction = predictions[rid]
        require(ref["text"] == case["text"] and digest(ref["text"].encode("utf-8")) == prediction["input_sha256"],
                f"{rid}: exact narrative and inference input identity")
        classifier = prediction["event_classifier"]
        probs = classifier["probabilities"]
        require(set(probs) == set(LABELS) and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) and 0 <= v <= 1 for v in probs.values()), f"{rid}: five finite probabilities")
        require(abs(sum(probs.values()) - 1) < 2e-5 and classifier["label"] == max(probs, key=probs.get)
                and abs(classifier["confidence"] - probs[classifier["label"]]) < 1e-6,
                f"{rid}: confidence and argmax consistent")
        require(not prediction["sena_token_coverage"]["truncated"], f"{rid}: input not truncated")
        rows.append({"id": rid, "text": ref["text"], "gold": ref["final"],
                     "original_gold": case["gold_label"], "prediction": classifier["label"],
                     "confidence": classifier["confidence"], "review_status": ref["status"],
                     "review_note": ref["note"], "input_sha256": prediction["input_sha256"]})
    gold = [r["gold"] for r in rows]
    pred = [r["prediction"] for r in rows]
    reviewed_metrics = score(gold, pred)
    original_metrics = score([r["original_gold"] for r in rows], pred)
    cutoffs = cutoff_analysis(rows)
    errors = []
    for r in rows:
        if r["gold"] == r["prediction"]:
            continue
        kind = "FALSE_NON_EVENT" if r["prediction"] == "NON_EVENT" else (
            "FALSE_EVENT" if r["gold"] == "NON_EVENT" else "WRONG_EVENT_TYPE")
        errors.append({**r, "error_kind": kind})
    result = {
        "schema": "slr09-sena-reviewed-evaluation-0.1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "REVIEWED_620_OF_CANDIDATE_623_NOT_INDEPENDENT_TEST",
        "records_original": 623, "records_scored": len(rows), "records_omitted": len(pending),
        "omitted_cases": pending, "metrics_reviewed": reviewed_metrics,
        "metrics_original_gold_same_620": original_metrics,
        "reference_labels_changed": sum(r["gold"] != r["original_gold"] for r in rows),
        "cutoff_analysis": cutoffs,
        "new_training_executed": False, "new_neural_inference_executed": False,
        "probability_calibration_fitted": False, "production_threshold_selected": False,
        "production_confidence_threshold": None,
        "historical_training_split_identity_verified": False,
        "reviewed_reference_is_new_blind_test": False,
        "non_event_always_blocks_submission": True,
        "human_verification_required_at_all_confidences": True,
        "source_sha256": {"runtime_zip": digest(runtime_zip.read_bytes()),
            "predictions": digest(prediction_bytes), "review_jsonl": digest(raw_review),
            "review_checkpoint": digest(review_checkpoint.read_bytes()),
            "review_manifest": digest(manifest_bytes), "workbook": digest(workbook_bytes)},
        "original_run_summary": run, "original_split_manifest": split,
        "checks": checks,
        "limitations": [
            "Kandidat validation direkonstruksi; identitas terhadap training historis SENA belum terbukti.",
            "Review dilakukan setelah analisis prediksi; angka ini merupakan analisis retrospektif.",
            "Tiga kasus ambigu tetap ditunda; 620 bukan seluruh 623 kasus.",
            "Cutoff hanya menandai confidence rendah; tidak memperbaiki label atau membatalkan NON_EVENT.",
            "Tidak memilih target mutu, model produksi, threshold produksi, atau melatih temperature scaling.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "evaluation.json", result)
    write_json(output / "omitted_cases.json", pending)
    write_json(output / "scored_rows.json", rows)
    write_csv(output / "classification_errors.csv", errors, ["id", "text", "gold", "original_gold",
              "prediction", "confidence", "review_status", "review_note", "input_sha256", "error_kind"])
    write_csv(output / "threshold_candidates.csv", cutoffs)
    write_csv(output / "per_class.csv", [{"label": k, **v} for k, v in reviewed_metrics["per_class"].items()])
    with (output / "confusion_matrix.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["gold/prediction", *LABELS])
        for label, row in zip(LABELS, reviewed_metrics["confusion_matrix_rows_gold_columns_prediction"]):
            writer.writerow([label, *row])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-zip", type=Path, required=True)
    parser.add_argument("--review-jsonl", type=Path, required=True)
    parser.add_argument("--review-checkpoint", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path, required=True)
    parser.add_argument("--reviewed-workbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.runtime_zip, args.review_jsonl, args.review_checkpoint,
                      args.review_manifest, args.reviewed_workbook, args.output_dir)
    print(json.dumps({"scope": result["scope"], "scored": result["records_scored"],
        "accuracy": result["metrics_reviewed"]["accuracy"],
        "macro_f1": result["metrics_reviewed"]["macro_f1_all_five_classes"],
        "false_non_event": result["metrics_reviewed"]["false_non_event_count"],
        "checks_passed": len(result["checks"]), "new_neural_inference": False}, indent=2))


if __name__ == "__main__":
    main()
