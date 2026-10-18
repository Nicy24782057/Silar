"""Metrik token dan span flat; diturunkan dari audit terdahulu tanpa mengubah definisi.

Sumber SHA-256: c101387293b8f1ab60331880adb1badfcd001a0701e05a619f0c33dc00062ba2
"""

from collections import Counter

LABELS = (
    "O", "ACCIDENT-EVENT", "AFFECTEDOBJECTS-ARG", "DEATHVICTIM-ARG",
    "EARTHQUAKE-EVENT", "FALSE-EVENT", "FIRE-EVENT", "FLOOD-EVENT",
    "INFORMATION-ARG", "OFFICER-ARG", "PLACE-ARG", "REASON-ARG",
    "STREET-ARG", "TIME-ARG", "WOUNDVICTIM-ARG",
)



def divide(a, b):
    return a / b if b else 0.0



def flat_spans(labels):
    """Span kontigu label identik; O diabaikan. Tidak menafsirkan BIO."""
    spans = set()
    start = 0
    while start < len(labels):
        end = start + 1
        while end < len(labels) and labels[end] == labels[start]:
            end += 1
        if labels[start] != "O":
            spans.add((labels[start], start, end))
        start = end
    return spans



def recompute(rows):
    index = {label: i for i, label in enumerate(LABELS)}
    matrix = [[0] * len(LABELS) for _ in LABELS]
    span_counts = Counter()
    used = 0
    for row in rows:
        for gold, pred in zip(row["gold_labels"], row["predicted_labels"]):
            matrix[index[gold]][index[pred]] += 1
        if not row["coverage"]["truncated"]:
            used += 1
            gold, pred = flat_spans(row["gold_labels"]), flat_spans(row["predicted_labels"])
            span_counts["tp"] += len(gold & pred)
            span_counts["fp"] += len(pred - gold)
            span_counts["fn"] += len(gold - pred)
    total = sum(map(sum, matrix))
    by_label = {}
    for i, label in enumerate(LABELS):
        tp = matrix[i][i]
        gold_total = sum(matrix[i])
        pred_total = sum(row[i] for row in matrix)
        precision, recall = divide(tp, pred_total), divide(tp, gold_total)
        by_label[label] = {
            "precision": precision, "recall": recall,
            "f1-score": divide(2 * precision * recall, precision + recall),
            "support": gold_total, "predicted_tokens": pred_total,
        }
    roles = [by_label[label] for label in LABELS[1:]]
    role_tp = sum(matrix[i][i] for i in range(1, len(LABELS)))
    pred_roles = sum(row["predicted_tokens"] for row in roles)
    gold_roles = sum(row["support"] for row in roles)
    micro_precision, micro_recall = divide(role_tp, pred_roles), divide(role_tp, gold_roles)
    token_metrics = {
        "accuracy": divide(sum(matrix[i][i] for i in range(len(LABELS))), total),
        "precision_macro_no_o": sum(x["precision"] for x in roles) / 14,
        "recall_macro_no_o": sum(x["recall"] for x in roles) / 14,
        "macro_f1_no_o": sum(x["f1-score"] for x in roles) / 14,
        "micro_f1_no_o": divide(2 * micro_precision * micro_recall, micro_precision + micro_recall),
        "weighted_f1_no_o": divide(sum(x["f1-score"] * x["support"] for x in roles), gold_roles),
        "predicted_non_o_rate": divide(pred_roles, total),
        "gold_non_o_rate": divide(gold_roles, total),
    }
    sp, sr = divide(span_counts["tp"], span_counts["tp"] + span_counts["fp"]), divide(span_counts["tp"], span_counts["tp"] + span_counts["fn"])
    span_metrics = {
        "precision": sp, "recall": sr, "f1": divide(2 * sp * sr, sp + sr),
        "true_positive_spans": span_counts["tp"],
        "false_positive_spans": span_counts["fp"],
        "false_negative_spans": span_counts["fn"],
        "records_used": used, "records_excluded_due_to_truncation": len(rows) - used,
    }
    pairs = sorted(
        ({"gold": a, "prediction": b, "count": matrix[i][j]}
         for i, a in enumerate(LABELS) for j, b in enumerate(LABELS)
         if i != j and matrix[i][j]),
        key=lambda x: (-x["count"], x["gold"], x["prediction"]),
    )
    return {
        "narratives": len(rows), "token_count": total,
        "token_metrics": token_metrics, "span_metrics": span_metrics,
        "by_label": by_label, "confusion_matrix": matrix,
        "gold_o_predicted_non_o": sum(matrix[0][1:]),
        "gold_non_o_predicted_o": sum(row[0] for row in matrix[1:]),
        "top_confusions": pairs[:15],
    }


