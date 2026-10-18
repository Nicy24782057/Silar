"""Analyze the completed SENA run from saved predictions only.

The module does not load model weights, train, or run neural inference.
It preserves the reviewed labels and proposes, rather than selects, cutoffs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

RUN_ID = "20261018T044447_926664Z"
EXPECTED_ZIP_SHA256 = "0077365fac8b70d4c624958bbcef60978aab41cf50978bd78f8154c9bdbf691f"


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def analyze(root: Path, run_zip: Path | None = None) -> dict:
    root = Path(root)
    run_zip = Path(run_zip) if run_zip else root / "sources" / f"SLR09_SENA_Hasil_FineTune_{RUN_ID}.zip"
    if hashlib.sha256(run_zip.read_bytes()).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("Completed SENA report archive differs")
    baseline_path = root / "results/sena_reviewed_620/scored_rows.json"
    baseline = {r["id"]: r for r in json.loads(baseline_path.read_text())}
    refs_path = root / "data/sena_validation_reviewed.jsonl"
    refs = {r["id"]: r for r in [json.loads(line) for line in refs_path.read_text().splitlines() if line.strip()]}
    destination = root / "results" / ("sena_finetune_" + RUN_ID)
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(run_zip) as archive:
        if archive.testzip() is not None: raise ValueError("Report ZIP CRC error")
        for entry in archive.infolist():
            relative = Path(entry.filename)
            if relative.is_absolute() or ".." in relative.parts: raise ValueError("Invalid report path")
            if not entry.is_dir():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(entry.filename))
        read_json = lambda name: json.loads(archive.read(name))
        state = read_json("run_state.json")
        comparison = read_json("comparison.json")
        metrics = read_json("finetuned_validation_metrics.json")
        cutoffs = read_json("cutoff_analysis.json")["rows"]
        history = read_json("training_log_history.json")
        export = read_json("model_export_manifest.json")
        inputs = read_json("input_manifest.json")
        rows = [json.loads(line) for line in archive.read("finetuned_validation_predictions.jsonl").decode().splitlines() if line.strip()]
    assert state["run_id"] == RUN_ID and state["status"] == "SUCCEEDED"
    assert state["training_completed"] and state["model_exported"]
    assert not state["baseline_neural_inference_repeated"]
    assert not state["production_model_selected"] and not state["production_threshold_selected"]
    assert len(rows) == len(baseline) == len(refs) == 620
    assert len({r["id"] for r in rows}) == 620 and {r["id"] for r in rows} == set(baseline) == set(refs)
    checks = []
    for relative, expected in inputs["sha256"].items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected
        checks.append({"check": relative + ": frozen input SHA-256", "passed": True})
    transitions = []
    for row in rows:
        rid = row["id"]; old = baseline[rid]; ref = refs[rid]
        assert row["text"] == old["text"] == ref["text"] and row["gold"] == old["gold"] == ref["final"]
        probabilities = row["probabilities"]
        assert set(probabilities) == set(metrics["labels"])
        assert all(math.isfinite(v) and 0 <= v <= 1 for v in probabilities.values())
        assert abs(sum(probabilities.values()) - 1) < 2e-5
        assert row["prediction"] == max(probabilities, key=probabilities.get)
        assert math.isclose(row["confidence"], probabilities[row["prediction"]], abs_tol=1e-6)
        old_correct = old["prediction"] == row["gold"]
        new_correct = row["prediction"] == row["gold"]
        change = ("STILL_CORRECT" if old_correct else "IMPROVED") if new_correct else ("REGRESSED" if old_correct else "STILL_WRONG")
        kind = "CORRECT" if new_correct else ("FALSE_NON_EVENT" if row["prediction"] == "NON_EVENT" else
            ("FALSE_EVENT" if row["gold"] == "NON_EVENT" else "WRONG_EVENT_TYPE"))
        transitions.append({"id": rid, "text": row["text"], "gold": row["gold"],
            "baseline_prediction": old["prediction"], "new_prediction": row["prediction"],
            "baseline_confidence": old["confidence"], "new_confidence": row["confidence"],
            "change": change, "new_error_kind": kind, "review_note": ref["note"]})
    checks.append({"check": "all 620 IDs/texts/gold/argmax/confidence/probabilities", "passed": True})
    counts = dict(Counter(row["change"] for row in transitions))
    assert counts["STILL_CORRECT"] + counts["IMPROVED"] == metrics["correct"]
    assert counts["REGRESSED"] + counts["STILL_WRONG"] == metrics["incorrect"]
    extended = []
    for cutoff in cutoffs:
        threshold = cutoff["threshold"]
        low = [r for r in rows if r["confidence"] < threshold]
        high = [r for r in rows if r["confidence"] >= threshold]
        wrong_high = [r for r in high if r["gold"] != r["prediction"]]
        wrong_low = [r for r in low if r["gold"] != r["prediction"]]
        assert len(low) == cutoff["below_threshold_uncertain"]
        assert len(high) == cutoff["at_or_above_threshold"]
        assert len(wrong_low) == cutoff["errors_below_threshold"]
        assert len(wrong_high) == cutoff["errors_at_or_above"]
        assert len(wrong_low) + len(wrong_high) == 74
        extended.append({**cutoff, "flagged_rate": len(low) / len(rows),
            "correct_predictions_also_flagged": len(low) - len(wrong_low),
            "false_event_at_or_above": sum(r["gold"] == "NON_EVENT" for r in wrong_high),
            "wrong_event_type_at_or_above": sum(r["gold"] != "NON_EVENT" and r["prediction"] != "NON_EVENT" for r in wrong_high)})
    checks.append({"check": "all nine cutoff partitions match the original report", "passed": True})
    evaluation_epochs = [r for r in history if "eval_macro_f1" in r]
    best_epoch = max(evaluation_epochs, key=lambda r: r["eval_macro_f1"])
    assert math.isclose(best_epoch["eval_macro_f1"], state["best_validation_macro_f1"], abs_tol=1e-12)
    assert math.isclose(metrics["macro_f1_all_five_classes"], best_epoch["eval_macro_f1"], abs_tol=1e-12)
    checks.append({"check": "selected checkpoint metric equals saved prediction metric", "passed": True})
    example_ids = ["KEC-01395", "KEB-00598", "BAN-01074", "GEM-01398", "KEC-00351", "GEM-01229"]
    examples = [next(r for r in transitions if r["id"] == rid) for rid in example_ids]
    result = {"schema": "slr09-completed-sena-analysis-0.1", "run_id": RUN_ID,
        "run_report_sha256": EXPECTED_ZIP_SHA256, "source_report_files": 17,
        "state": state, "baseline_metrics": comparison["baseline_reused_without_neural_rerun"],
        "finetuned_metrics": metrics, "prediction_changes": counts,
        "best_epoch": best_epoch["epoch"], "best_step": best_epoch["step"],
        "epochs_completed": state["epochs_completed"], "optimizer_steps": state["optimizer_steps"],
        "cutoff_comparison": extended, "examples": examples, "model_export_manifest": export,
        "proposed_recommended_cutoff": 0.95, "alternative_cutoff": 0.90,
        "confidence_threshold_selected": None, "threshold_activated": False,
        "validation_used_for_checkpoint_selection": True, "independent_test": False,
        "historical_sena_training_split_identity_verified": False,
        "model_weights_directly_read_in_this_analysis": False,
        "new_training_executed_in_this_analysis": False,
        "new_neural_inference_executed_in_this_analysis": False,
        "previous_attachment_check": "Accuracy/F1/per-class/confusion matrix were independently checked with scikit-learn on receipt.",
        "checks": checks}
    dump(destination / "completed_run_analysis.json", result)
    write_csv(destination / "prediction_transitions.csv", transitions)
    write_csv(destination / "threshold_comparison.csv", extended)
    write_csv(destination / "error_examples.csv", examples)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-zip", type=Path)
    arguments = parser.parse_args()
    result = analyze(arguments.root, arguments.run_zip)
    print(json.dumps({"run_id": result["run_id"], "changes": result["prediction_changes"],
        "best_epoch": result["best_epoch"], "checks_passed": len(result["checks"]),
        "threshold_selected": None, "training_or_neural_inference_executed_here": False}, indent=2))
