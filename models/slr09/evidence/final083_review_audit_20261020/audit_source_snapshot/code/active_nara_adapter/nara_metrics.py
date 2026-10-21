"""Metrik token dan span label flat; tidak menganggap label sebagai BIO."""
from collections import Counter
import csv
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

from nara_data import LABELS, dump, dump_jsonl


def flatten_eval(logits, labels):
    if isinstance(logits, tuple):
        logits = logits[0]
    if not np.isfinite(logits).all():
        raise ValueError("Logit NaN/Inf tidak boleh dijadikan skor evaluasi")
    predicted = np.argmax(logits, axis=-1)
    labels = np.asarray(labels)
    if predicted.shape != labels.shape:
        raise ValueError("Dimensi prediksi/gold tidak sama")
    mask = labels != -100
    if not np.any(mask):
        raise ValueError("Evaluasi tidak mempunyai token gold")
    return labels[mask].astype(int), predicted[mask].astype(int)


def compute_metrics(eval_prediction):
    logits, labels = eval_prediction
    truth, prediction = flatten_eval(logits, labels)
    pm, rm, fm, _ = precision_recall_fscore_support(truth, prediction, labels=list(range(1, 15)), average="macro", zero_division=0)
    _, _, fi, _ = precision_recall_fscore_support(truth, prediction, labels=list(range(1, 15)), average="micro", zero_division=0)
    _, _, fw, _ = precision_recall_fscore_support(truth, prediction, labels=list(range(1, 15)), average="weighted", zero_division=0)
    return {"accuracy": float(accuracy_score(truth, prediction)),
            "precision_macro_no_o": float(pm), "recall_macro_no_o": float(rm),
            "macro_f1_no_o": float(fm), "micro_f1_no_o": float(fi), "weighted_f1_no_o": float(fw),
            "predicted_non_o_rate": float(np.mean(prediction != 0)), "gold_non_o_rate": float(np.mean(truth != 0))}


def flat_spans(labels):
    result = set()
    start = 0
    while start < len(labels):
        end = start + 1
        while end < len(labels) and labels[end] == labels[start]:
            end += 1
        if labels[start] != 0:
            result.add((int(labels[start]), start, end))
        start = end
    return result


def span_report(predicted_rows, gold_rows, metadata):
    counts = Counter()
    used = 0
    for pred, gold, meta in zip(predicted_rows, gold_rows, metadata):
        if meta["truncated"]:
            continue  # Tidak memberi kredit untuk batas span yang terpotong.
        used += 1
        predicted, expected = flat_spans(pred), flat_spans(gold)
        counts["tp"] += len(predicted & expected)
        counts["fp"] += len(predicted - expected)
        counts["fn"] += len(expected - predicted)
    precision = counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else 0.0
    recall = counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "true_positive_spans": counts["tp"], "false_positive_spans": counts["fp"],
            "false_negative_spans": counts["fn"], "records_used": used,
            "records_excluded_due_to_truncation": len(metadata) - used,
            "definition": "Label dan batas token sumber harus sama persis; span flat kontigu non-O, bukan BIO."}


def save_evaluation(result, records, metadata, output_directory, title):
    out = Path(output_directory)
    out.mkdir(parents=True, exist_ok=True)
    logits = result.predictions[0] if isinstance(result.predictions, tuple) else result.predictions
    predicted = np.argmax(logits, axis=-1)
    labels = np.asarray(result.label_ids)
    truth, guess = flatten_eval(logits, labels)
    details, pred_rows, gold_rows = [], [], []
    for row, pred, gold, meta in zip(records, predicted, labels, metadata):
        mask = gold != -100
        pred = [int(x) for x in pred[mask]]
        gold = [int(x) for x in gold[mask]]
        if len(pred) != meta["processed_words"]:
            raise ValueError("Prediksi tidak selaras dengan sumber")
        pred_rows.append(pred)
        gold_rows.append(gold)
        details.append({"id": row["id"], "text": row["text"],
                        "processed_tokens": row["tokens"][:len(pred)],
                        "gold_labels": [LABELS[i] for i in gold], "predicted_labels": [LABELS[i] for i in pred],
                        "coverage": meta})
    matrix = confusion_matrix(truth, guess, labels=list(range(15)))
    report = {"token_metrics": compute_metrics((logits, labels)),
              "trainer_metrics": {k: float(v) for k, v in result.metrics.items()},
              "token_count": int(len(truth)), "narratives": len(records),
              "span_metrics": span_report(pred_rows, gold_rows, metadata),
              "classification_report": classification_report(truth, guess, labels=list(range(15)), target_names=list(LABELS), output_dict=True, zero_division=0),
              "confusion_matrix": matrix.tolist(), "label_order": list(LABELS),
              "metric_denominator": "Hanya wordpiece pertama token sumber yang diproses; -100 diabaikan. Label O tetap pada akurasi dan confusion matrix.",
              "all_14_non_o_labels_in_macro_denominator": True}
    dump(out / "metrics.json", report)
    dump_jsonl(out / "predictions.jsonl", details)
    with (out / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["gold / prediction", *LABELS])
        writer.writerows([[label, *row] for label, row in zip(LABELS, matrix.tolist())])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 12))
    img = ax.imshow(matrix, cmap="Blues")
    for i in range(15):
        for j in range(15):
            if matrix[i, j]:
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=8,
                        color="white" if matrix[i, j] > matrix.max() / 2 else "black")
    ax.set_xticks(range(15), LABELS, rotation=65, ha="right", fontsize=8)
    ax.set_yticks(range(15), LABELS, fontsize=8)
    ax.set(xlabel="Predicted label", ylabel="Gold label", title=title)
    fig.colorbar(img, ax=ax, shrink=.75)
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=220)
    plt.close(fig)
    return report
