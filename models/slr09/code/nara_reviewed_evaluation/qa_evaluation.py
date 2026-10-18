#!/usr/bin/env python3
"""Verifikasi metrik dengan scikit-learn dan span dengan groupby terpisah."""
from collections import Counter
import csv
from itertools import groupby
import json
import math
from pathlib import Path
import tempfile
import zipfile

from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from evaluate_reviewed_nara import evaluate, REPORT_NAME
from validate_review import validate_file, read_json, digest, dump
from nara_token_metrics import LABELS


def independent_spans(labels):
    spans, start = set(), 0
    for label, group in groupby(labels):
        length = len(list(group))
        if label != "O":
            spans.add((label, start, start + length))
        start += length
    return spans


def main():
    root = Path(__file__).resolve().parent.parent
    result = read_json(root / "results/evaluation.json")
    workbook = root / "sources/SLR09_NARA_Review_Uji_80_Reviewed.xlsx"
    validation, reviewed, records, narratives = validate_file(workbook, root / "data")
    mapping = {r["review_id"]: r for r in read_json(root / "data/selection_manifest.json")["selected_records"]}
    ready = {r["review_id"] for r in validation["details"] if r["ready"]}
    checks = []
    def require(name, ok):
        if not ok:
            raise ValueError("QA gagal: " + name)
        checks.append({"check": name, "passed": True})
    def close(a, b):
        return math.isclose(float(a), float(b), abs_tol=1e-12, rel_tol=1e-12)
    require("review unchanged", digest(workbook) == result["review_source_sha256"])
    require("79 approved and one deferred", len(ready) == 79 and validation["deferred_narratives"] == 1 and not validation["ready_to_evaluate"])
    require("partial scope disclosed", result["evaluation_scope"] == "PARTIAL_APPROVED_SUBSET_NOT_FULL_80" and result["coverage"]["scored_tokens"] == 1701)
    require("UJI-019 omitted rather than relabelled", result["omitted_cases"][0]["review_id"] == "UJI-019" and result["omitted_cases"][0]["status"] == "DEFERRED")
    with zipfile.ZipFile(root / "sources" / REPORT_NAME) as archive:
        for model in ("baseline", "finetuned"):
            rows = {r["id"]: r for r in map(json.loads, archive.read(model + "_historical_test/predictions.jsonl").decode().splitlines())}
            for policy in ("reviewed_gold", "historical_gold_same_subset"):
                truth, predicted, span_counts = [], [], Counter()
                for record in records:
                    key = record["review_id"]
                    if key not in ready:
                        continue
                    row = rows[mapping[key]["source_id"]]
                    gold = reviewed[key] if policy == "reviewed_gold" else row["gold_labels"]
                    pred = row["predicted_labels"]
                    truth.extend(gold)
                    predicted.extend(pred)
                    gsp, psp = independent_spans(gold), independent_spans(pred)
                    span_counts["tp"] += len(gsp & psp)
                    span_counts["fp"] += len(psp - gsp)
                    span_counts["fn"] += len(gsp - psp)
                expected = result["metrics"][model][policy]
                actual = expected["token_metrics"]
                pm, rm, fm, _ = precision_recall_fscore_support(truth, predicted, labels=list(LABELS[1:]), average="macro", zero_division=0)
                _, _, micro, _ = precision_recall_fscore_support(truth, predicted, labels=list(LABELS[1:]), average="micro", zero_division=0)
                _, _, weighted, _ = precision_recall_fscore_support(truth, predicted, labels=list(LABELS[1:]), average="weighted", zero_division=0)
                require(model + "/" + policy + ": all token metrics verified independently", all(close(actual[k], v) for k, v in {"accuracy": accuracy_score(truth, predicted), "precision_macro_no_o": pm, "recall_macro_no_o": rm, "macro_f1_no_o": fm, "micro_f1_no_o": micro, "weighted_f1_no_o": weighted, "gold_non_o_rate": sum(x != "O" for x in truth)/len(truth), "predicted_non_o_rate": sum(x != "O" for x in predicted)/len(predicted)}.items()))
                require(model + "/" + policy + ": full confusion matrix", confusion_matrix(truth, predicted, labels=list(LABELS)).tolist() == expected["confusion_matrix"])
                precision = span_counts["tp"] / (span_counts["tp"] + span_counts["fp"])
                recall = span_counts["tp"] / (span_counts["tp"] + span_counts["fn"])
                span_f1 = 2*precision*recall/(precision+recall)
                require(model + "/" + policy + ": independent exact spans", expected["span_metrics"]["true_positive_spans"] == span_counts["tp"] and expected["span_metrics"]["false_positive_spans"] == span_counts["fp"] and expected["span_metrics"]["false_negative_spans"] == span_counts["fn"] and close(expected["span_metrics"]["f1"], span_f1))
    with tempfile.TemporaryDirectory(prefix="slr09-full80-gate-") as temp:
        try:
            evaluate(workbook, root/"data", root/"sources"/REPORT_NAME, root/"sources/historical_test_original_labels.jsonl", temp, scope="full80")
        except ValueError as error:
            require("full80 gate still rejects unresolved reference", "Evaluasi penuh 80 ditolak" in str(error))
        else:
            raise ValueError("Full80 seharusnya ditolak")
    with (root / "results/narrative_errors.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    require("omitted case not scored in per-record results", len(rows) == 79 and all(r["review_id"] != "UJI-019" for r in rows))
    require("no automatic production promotion or fresh neural inference", not result["production_model_selected"] and not result["predictions_source"]["fresh_neural_inference_executed"] and not result["predictions_source"]["training_executed"])
    for path in (root/"code").glob("*.py"):
        compile(path.read_text(), str(path), "exec")
    dump(root / "evidence/independent_qa.json", {"checks": checks, "checks_passed": len(checks), "reference_workbook_byte_identical": True, "new_training_or_neural_inference": False})
    print(json.dumps({"checks_passed": len(checks), "independent_sklearn_metrics": True, "full80_gate_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
