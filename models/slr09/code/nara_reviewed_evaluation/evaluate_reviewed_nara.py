#!/usr/bin/env python3
"""Nilai prediksi run tetap terhadap review manusia; tanpa training/inferensi.

--scope approved-subset menghasilkan analisis parsial bila ada DEFERRED.
--scope full80 tetap menolak evaluasi bila belum semua 80 disetujui.
Validator dan workbook sumber tidak diubah. Kasus DEFERRED tetap tercatat.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import zipfile

from validate_review import validate_file, read_json, dump, digest
from nara_token_metrics import LABELS, recompute

RUN_ID = "20261018T001122_607337Z"
REPORT_NAME = f"SLR09_NARA_Hasil_FineTune_{RUN_ID}.zip"
REPORT_SHA = "879b3205419a9897075145a64c94e29c1f3b81b558af170a8181f55fdfa63bfb"


def jsonl(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in rows), encoding="utf-8")


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evaluate(workbook, data_dir, results_zip, historical_gold, output, *, scope="approved-subset"):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    validation, reviewed_labels, records, narratives = validate_file(workbook, data_dir)
    dump(output / "review_validation.json", validation)
    if scope not in ("approved-subset", "full80"):
        raise ValueError("Scope tidak dikenal")
    if scope == "full80" and not validation["ready_to_evaluate"]:
        raise ValueError("Evaluasi penuh 80 ditolak: review masih memiliki kasus belum disetujui")
    ready = {r["review_id"] for r in validation["details"] if r["ready"]}
    if not ready:
        raise ValueError("Tidak ada narasi APPROVED lengkap untuk dianalisis")
    if any(d["status"] == "APPROVED" and not d["ready"] for d in validation["details"]):
        raise ValueError("Ada APPROVED yang belum memenuhi label/reviewer; selesaikan input terlebih dahulu")
    if digest(results_zip) != REPORT_SHA:
        raise ValueError("ZIP prediksi berbeda dari run tetap yang ditetapkan")
    selection = read_json(Path(data_dir) / "selection_manifest.json")
    locked = read_json(Path(data_dir) / "candidate_lock.json")
    mapping = {r["review_id"]: r for r in selection["selected_records"]}
    old_corpus = {r["id"]: r for r in jsonl(Path(historical_gold).read_bytes())}
    public = {r["review_id"]: r for r in records}
    approved_records = [r for r in records if r["review_id"] in ready]
    omitted = [{"review_id": r["review_id"], "source_id": mapping[r["review_id"]]["source_id"], "status": narratives[r["review_id"]]["status"], "tokens": len(r["tokens"]), "text": r["text"], "review_note": narratives[r["review_id"]]["note"], "temporary_labels_not_used_for_scoring": True} for r in records if r["review_id"] not in ready]
    checks = []
    def check(name, ok):
        if not ok:
            raise ValueError("Pemeriksaan gagal: " + name)
        checks.append({"check": name, "passed": True})
    check("fixed report SHA-256", digest(results_zip) == REPORT_SHA)
    provenance = read_json(Path(historical_gold).parent / "corpus_provenance.json")
    check("historical reference copy SHA-256", digest(historical_gold) == provenance["selected_jsonl_sha256"])
    check("historical source CSV matches frozen selection", provenance["csv_sha256"] == selection["source_csv_sha256"])
    check("stable source IDs unique and all test", len(mapping) == 80 and len({r["source_id"] for r in mapping.values()}) == 80 and all(r["original_nara_split"] == "test" for r in mapping.values()))
    predicted, metrics, source_metrics, changes = {}, {}, {}, Counter()
    gold_by_review = {}
    with zipfile.ZipFile(results_zip) as archive:
        check("report ZIP CRC", archive.testzip() is None)
        state = json.loads(archive.read("run_state.json"))
        exported = json.loads(archive.read("model_export_manifest.json"))
        check("candidate run fixed before reannotation", state["run_id"] == exported["run_id"] == locked["candidate_run_id"] == RUN_ID)
        check("reported baseline/candidate hash consistency", state["baseline_weights_sha256"] == locked["source_weights_sha256_reported"] == exported["source_weights_sha256"] and exported["new_weights_sha256"] == locked["candidate_weights_sha256_reported"])
        for model in ("baseline", "finetuned"):
            raw = jsonl(archive.read(model + "_historical_test/predictions.jsonl"))
            index = {r["id"]: r for r in raw}
            check(model + ": 1000 unique saved test predictions", len(raw) == len(index) == 1000)
            revised_rows, original_rows = [], []
            for record in approved_records:
                key = record["review_id"]
                source_id = mapping[key]["source_id"]
                row, original = index[source_id], old_corpus[source_id]
                if row["processed_tokens"] != record["tokens"] or original["tokens"] != record["tokens"] or row["text"] != record["text"]:
                    raise ValueError("Teks/token tidak sama: " + key)
                if row["gold_labels"] != original["labels"]:
                    raise ValueError("Gold historis berbeda dari salinan sumber: " + key)
                if row["coverage"]["truncated"] or row["coverage"]["partial_last_word"]:
                    raise ValueError("Subset mengandung narasi terpotong: " + key)
                if not (len(row["predicted_labels"]) == len(reviewed_labels[key]) == len(record["tokens"])) or not set(row["predicted_labels"]) <= set(LABELS):
                    raise ValueError("Bentuk label tidak sama: " + key)
                original_rows.append(row)
                revised_rows.append({**row, "gold_labels": reviewed_labels[key]})
                gold_by_review[key] = row["gold_labels"]
                if model == "baseline":
                    changes.update((a, b) for a, b in zip(row["gold_labels"], reviewed_labels[key]) if a != b)
            check(model + ": input and historical gold match source; complete token coverage", len(revised_rows) == len(ready))
            metrics[model] = {"reviewed_gold": recompute(revised_rows), "historical_gold_same_subset": recompute(original_rows)}
            predicted[model] = {r["id"]: r for r in revised_rows}
            source_metrics[model] = json.loads(archive.read(model + "_historical_test/metrics.json"))["token_metrics"]
    scored = len(approved_records)
    token_count = sum(len(r["tokens"]) for r in approved_records)
    partial = scored != len(records)
    support = dict(Counter(label for r in approved_records for label in reviewed_labels[r["review_id"]]))
    role_narratives = {label: sum(label in reviewed_labels[r["review_id"]] for r in approved_records) for label in LABELS}
    reference_rows, token_errors, record_errors = [], [], []
    for r in approved_records:
        key, source_id = r["review_id"], mapping[r["review_id"]]["source_id"]
        gold = reviewed_labels[key]
        base = predicted["baseline"][source_id]["predicted_labels"]
        fine = predicted["finetuned"][source_id]["predicted_labels"]
        reference_rows.append({"review_id": key, "source_id": source_id, "text": r["text"], "tokens": r["tokens"], "labels": gold, "reviewer": validation["reviewer"], "status": "APPROVED", "policy": "nara-role-guideline-0.2", "scope": "APPROVED_SUBSET_REFERENCE" if partial else "FULL_80_APPROVED_REFERENCE", "note": narratives[key]["note"]})
        base_wrong, fine_wrong = sum(a != b for a, b in zip(gold, base)), sum(a != b for a, b in zip(gold, fine))
        record_errors.append({"review_id": key, "source_id": source_id, "tokens": len(gold), "baseline_wrong_tokens": base_wrong, "finetuned_wrong_tokens": fine_wrong, "fewer_errors_after_finetune": base_wrong - fine_wrong, "text": r["text"], "review_note": narratives[key]["note"]})
        for i, (token, g, b, f) in enumerate(zip(r["tokens"], gold, base, fine), 1):
            if f != g or b != g:
                token_errors.append({"review_id": key, "source_id": source_id, "position": i, "token": token, "reviewed_gold": g, "historical_gold": gold_by_review[key][i-1], "baseline_prediction": b, "finetuned_prediction": f, "baseline_correct": g == b, "finetuned_correct": g == f})
    write_jsonl(output / "approved_reference_for_analysis.jsonl", reference_rows)
    write_csv(output / "narrative_errors.csv", record_errors)
    if token_errors:
        write_csv(output / "token_errors.csv", token_errors)
    label_table = []
    for label in LABELS:
        b, f = (metrics[m]["reviewed_gold"]["by_label"][label] for m in ("baseline", "finetuned"))
        label_table.append({"label": label, "gold_tokens": f["support"], "gold_narratives": role_narratives[label], "baseline_precision": b["precision"], "baseline_recall": b["recall"], "baseline_f1": b["f1-score"], "finetuned_precision": f["precision"], "finetuned_recall": f["recall"], "finetuned_f1": f["f1-score"], "f1_delta_percentage_points": 100 * (f["f1-score"] - b["f1-score"])})
    write_csv(output / "per_label.csv", label_table)
    write_csv(output / "historical_to_reviewed_changes.csv", [{"historical_label": a, "reviewed_label": b, "tokens_changed": count} for (a, b), count in changes.most_common()])
    write_csv(output / "omitted_cases.csv", [{"review_id": r["review_id"], "source_id": r["source_id"], "status": r["status"], "tokens": r["tokens"], "text": r["text"], "review_note": r["review_note"]} for r in omitted] or [{"review_id": "", "source_id": "", "status": "NONE_OMITTED", "tokens": 0, "text": "", "review_note": ""}])
    for model in ("baseline", "finetuned"):
        with (output / (model + "_confusion_matrix.csv")).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["gold / prediction", *LABELS])
            writer.writerows([[label, *row] for label, row in zip(LABELS, metrics[model]["reviewed_gold"]["confusion_matrix"])])
    result = {
        "schema": "silar-nara-revised-reference-evaluation-0.1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": "PARTIAL_APPROVED_SUBSET_NOT_FULL_80" if partial else "FULL_80_APPROVED",
        "requested_scope": scope,
        "review_validation_full_80_ready": validation["ready_to_evaluate"],
        "validation_summary": {"missing_labels": validation["missing_labels"], "invalid_labels": validation["invalid_labels"], "case_canonicalizations": len(validation["case_canonicalizations"])},
        "coverage": {"sample_narratives": len(records), "sample_tokens": sum(len(r["tokens"]) for r in records), "scored_narratives": scored, "scored_tokens": token_count, "omitted_narratives": len(omitted), "omitted_tokens": sum(r["tokens"] for r in omitted), "scored_source_groups": dict(Counter(mapping[r["review_id"]]["source_group"] for r in approved_records))},
        "reviewer": validation["reviewer"], "omitted_cases": omitted,
        "gold_label_support": support, "gold_narrative_support": role_narratives,
        "historical_to_reviewed_tokens_changed": sum(changes.values()),
        "historical_to_reviewed_change_pairs": [{"old": a, "new": b, "tokens": count} for (a, b), count in changes.most_common()],
        "metrics": metrics, "historical_test_1000_unchanged": source_metrics,
        "predictions_source": {"run_id": RUN_ID, "report_zip_sha256": REPORT_SHA, "reused_saved_predictions": True, "fresh_neural_inference_executed": False, "training_executed": False, "weights_independently_verified_here": False, "reported_baseline_weights_sha256": locked["source_weights_sha256_reported"], "reported_finetuned_weights_sha256": locked["candidate_weights_sha256_reported"]},
        "review_source_sha256": digest(workbook),
        "data_lock_sha256": digest(Path(data_dir) / "data_lock.json"),
        "metric_definition": "Accuracy over all 15 labels; macro/micro/weighted F1 over fixed 14 non-O labels; O-related errors still counted; exact contiguous flat spans, not BIO; source-token first-wordpiece projection.",
        "checks": checks,
        "full_80_frozen_gold_created": False,
        "uploaded_review_workbook_modified": False,
        "deferred_status_automatically_changed": False,
        "new_adapter_field_references_created": False,
        "sena_or_production_fusion_evaluated": False,
        "production_model_selected": False,
    }
    check("all scored counts agree", all(metrics[m][p]["narratives"] == scored and metrics[m][p]["token_count"] == token_count for m in metrics for p in metrics[m]))
    dump(output / "evaluation.json", result)
    return result


def plot(result, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    output = Path(output)
    coverage = result["coverage"]
    for model, title in (("baseline", "NARA v1"), ("finetuned", "NARA fine-tuned")):
        matrix = np.array(result["metrics"][model]["reviewed_gold"]["confusion_matrix"])
        fig, ax = plt.subplots(figsize=(13, 10))
        im = ax.imshow(matrix, cmap="Blues")
        for i in range(15):
            for j in range(15):
                if matrix[i, j]:
                    ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=8, color="white" if matrix[i, j] > matrix.max() / 2 else "black")
        ax.set_xticks(range(15), LABELS, rotation=60, ha="right", fontsize=8)
        ax.set_yticks(range(15), LABELS, fontsize=8)
        ax.set(xlabel="Predicted label", ylabel="Reviewed gold label", title=f"{title}: revised-policy gold, {coverage['scored_narratives']}/{coverage['sample_narratives']} approved narratives")
        fig.colorbar(im, ax=ax, shrink=.7)
        fig.tight_layout()
        fig.savefig(output / (model + "_confusion_matrix.png"), dpi=180)
        plt.close(fig)
    rows = result["metrics"]
    fig, ax = plt.subplots(figsize=(11, 8))
    y = np.arange(14)
    b = [rows["baseline"]["reviewed_gold"]["by_label"][label]["f1-score"] * 100 for label in LABELS[1:]]
    f = [rows["finetuned"]["reviewed_gold"]["by_label"][label]["f1-score"] * 100 for label in LABELS[1:]]
    ax.barh(y - .18, b, .36, label="NARA v1", color="#8C9EAF")
    ax.barh(y + .18, f, .36, label="Fine-tuned", color="#315E8C")
    ax.set_yticks(y, [f"{label} (n={result['gold_label_support'][label]} tokens)" for label in LABELS[1:]], fontsize=8)
    ax.invert_yaxis()
    ax.set(xlim=(0, 105), xlabel="Token F1 (%)", title=f"Reviewed gold: {coverage['scored_narratives']} approved narratives; support shown per role")
    handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", bbox_to_anchor=(.67, .005), ncol=2, frameon=False)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, .06, 1, 1))
    fig.savefig(output / "f1_per_label.png", dpi=180)
    plt.close(fig)


def main():
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=base / "sources/SLR09_NARA_Review_Uji_80_Reviewed.xlsx")
    parser.add_argument("--data-dir", type=Path, default=base / "data")
    parser.add_argument("--results-zip", type=Path, default=base / "sources" / REPORT_NAME)
    parser.add_argument("--historical-gold", type=Path, default=base / "sources/historical_test_original_labels.jsonl")
    parser.add_argument("--output", type=Path, default=base / "results")
    parser.add_argument("--scope", choices=["approved-subset", "full80"], required=True)
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.workbook, args.data_dir, args.results_zip, args.historical_gold, args.output, scope=args.scope)
    if args.plots:
        plot(result, args.output)
    print(json.dumps({"scope": result["evaluation_scope"], "coverage": result["coverage"], "baseline_macro_f1": result["metrics"]["baseline"]["reviewed_gold"]["token_metrics"]["macro_f1_no_o"], "finetuned_macro_f1": result["metrics"]["finetuned"]["reviewed_gold"]["token_metrics"]["macro_f1_no_o"], "fresh_neural_inference": False}, indent=2))


if __name__ == "__main__":
    main()
