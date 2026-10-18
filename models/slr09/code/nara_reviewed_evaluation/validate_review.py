#!/usr/bin/env python3
"""Validasi Excel review tanpa mengubah label kosong menjadi O.

Hanya pustaka standar Python. Tidak menjalankan model atau menghitung metrik
sebelum semua 80 narasi disetujui. --freeze menulis gold hanya bila lengkap.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_xlsx(path):
    """Read cell values/formula flags; never evaluate formulas or external links."""
    sheets = {}
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Nama anggota ZIP Excel duplikat")
        if archive.testzip() is not None:
            raise ValueError("ZIP Excel rusak")
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//m:t", NS)) for si in root.findall("m:si", NS)]
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            target = targets[sheet.attrib[RID]]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            root = ET.fromstring(archive.read(member))
            values = {}
            for cell in root.findall(".//m:sheetData/m:row/m:c", NS):
                kind, ref = cell.attrib.get("t"), cell.attrib["r"]
                node = cell.find("m:v", NS)
                text = node.text if node is not None and node.text is not None else ""
                if kind == "s":
                    text = shared[int(text)]
                elif kind == "inlineStr":
                    text = "".join(t.text or "" for t in cell.findall(".//m:t", NS))
                values[ref] = {"value": text, "formula": cell.find("m:f", NS) is not None, "type": kind}
            sheets[sheet.attrib["name"]] = values
    return sheets


def cell_value(sheet, ref, *, allow_formula=False):
    cell = sheet.get(ref, {"value": "", "formula": False})
    if cell["formula"] and not allow_formula:
        raise ValueError("Rumus tidak diizinkan pada input/sumber: " + ref)
    return cell["value"]


def load_locked_data(data_dir):
    data_dir = Path(data_dir)
    lock = read_json(data_dir / "data_lock.json")
    for name, expected in lock.items():
        if digest(data_dir / name) != expected:
            raise ValueError("Sumber paket berubah: " + name)
    records = read_json(data_dir / "review_records.json")["records"]
    schema = read_json(data_dir / "label_schema.json")
    if len(records) != 80 or sum(len(r["tokens"]) for r in records) != 1718:
        raise ValueError("Jumlah narasi/token berubah")
    if schema["blank_label_is_o"] or len(schema["labels"]) != 15:
        raise ValueError("Skema label tidak sesuai")
    return records, schema


def read_annotations(sheets, records, schema):
    for name in ("Narasi", "Token", "Pedoman"):
        if name not in sheets:
            raise ValueError("Tab wajib tidak ditemukan: " + name)
    guide = sheets["Pedoman"]
    if [cell_value(guide, f"C{r}") for r in range(8, 23)] != [r["label"] for r in schema["labels"]]:
        raise ValueError("Daftar 15 label di Pedoman berubah")
    narrative_sheet, token_sheet = sheets["Narasi"], sheets["Token"]
    reviewer = str(cell_value(narrative_sheet, "C4")).strip()
    narratives, tokens = {}, {}
    # Read populated record rows independent of row order, so whole-table
    # sorting does not move notes or labels away from their stable keys.
    narrative_rows = sorted({int(m.group(2)) for ref in narrative_sheet if (m := re.fullmatch(r"([B-DGH])(\d+)", ref)) and int(m.group(2)) >= 8})
    for n in narrative_rows:
        key = cell_value(narrative_sheet, f"B{n}")
        if not key:
            if any(cell_value(narrative_sheet, f"{c}{n}") for c in ("C", "G", "H")):
                raise ValueError(f"ID narasi kosong pada baris {n}")
            continue
        if key in narratives:
            raise ValueError("ID narasi duplikat: " + key)
        narratives[key] = {"review_id": key, "text": cell_value(narrative_sheet, f"C{n}"), "token_count": cell_value(narrative_sheet, f"D{n}"), "status": cell_value(narrative_sheet, f"G{n}"), "note": cell_value(narrative_sheet, f"H{n}")}
    token_rows = sorted({int(m.group(2)) for ref in token_sheet if (m := re.fullmatch(r"([B-F])(\d+)", ref)) and int(m.group(2)) >= 8})
    for n in token_rows:
        key = cell_value(token_sheet, f"B{n}")
        if not key:
            if any(cell_value(token_sheet, f"{c}{n}") for c in ("C", "D", "E", "F")):
                raise ValueError(f"ID token kosong pada baris {n}")
            continue
        position = cell_value(token_sheet, f"C{n}")
        try:
            position_number = int(position)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Posisi token tidak valid pada baris {n}") from exc
        stable_key = (key, position_number)
        if stable_key in tokens:
            raise ValueError("Kunci token duplikat: " + str(stable_key))
        tokens[stable_key] = {"token": cell_value(token_sheet, f"D{n}"), "label": cell_value(token_sheet, f"E{n}"), "note": cell_value(token_sheet, f"F{n}"), "excel_row": n}
    expected_ids = {r["review_id"] for r in records}
    expected_keys = {(r["review_id"], i + 1) for r in records for i in range(len(r["tokens"]))}
    if set(narratives) != expected_ids or set(tokens) != expected_keys:
        raise ValueError("ID/jumlah/posisi narasi atau token berubah")
    for row in records:
        if narratives[row["review_id"]]["text"] != row["text"]:
            raise ValueError("Teks narasi berubah: " + row["review_id"])
        if str(narratives[row["review_id"]]["token_count"]) != str(len(row["tokens"])):
            raise ValueError("Jumlah token sumber berubah: " + row["review_id"])
        for i, token in enumerate(row["tokens"], 1):
            if tokens[(row["review_id"], i)]["token"] != token:
                raise ValueError(f"Token sumber berubah: {row['review_id']} posisi {i}")
    return reviewer, narratives, tokens


def validate_annotations(records, schema, reviewer, narratives, tokens):
    allowed = {r["label"] for r in schema["labels"]}
    counts, details, canonicalizations, invalid = Counter(), [], [], []
    labels_by_id = {}
    for row in records:
        key = row["review_id"]
        status_raw = narratives[key]["status"]
        status = str(status_raw).upper()
        note = str(narratives[key]["note"]).strip()
        missing, bad, labels = 0, 0, []
        for position in range(1, len(row["tokens"]) + 1):
            raw = tokens[(key, position)]["label"]
            if raw is None or raw == "":
                missing += 1
                labels.append(None)
                continue
            label = str(raw).upper()  # Case only; no guessed aliases/whitespace/O fill.
            if label not in allowed:
                bad += 1
                invalid.append({"review_id": key, "position": position, "label": raw})
            elif raw != label:
                canonicalizations.append({"review_id": key, "position": position, "input": raw, "canonical_label": label})
            labels.append(label)
        counts[status] += 1
        counts["missing_labels"] += missing
        counts["invalid_labels"] += bad
        issues = []
        if status not in schema["statuses"]:
            issues.append("STATUS_TIDAK_VALID")
        elif status == "PENDING":
            issues.append("BELUM_DISETUJUI")
        elif status == "DEFERRED":
            issues.append("KASUS_DITUNDA")
            if not note:
                issues.append("CATATAN_TUNDA_WAJIB")
        if missing:
            issues.append("LABEL_KOSONG")
        if bad:
            issues.append("LABEL_TIDAK_VALID")
        if not reviewer:
            issues.append("REVIEWER_BELUM_DIISI")
        ready = status == "APPROVED" and not missing and not bad and bool(reviewer)
        counts["ready_narratives"] += int(ready)
        details.append({"review_id": key, "status": status, "missing_labels": missing, "invalid_labels": bad, "ready": ready, "issues": issues})
        labels_by_id[key] = labels
    complete = counts["ready_narratives"] == len(records)
    report = {
        "review_status": "COMPLETE_ALL_APPROVED" if complete else "AWAITING_REVIEW_OR_RESOLUTION",
        "ready_to_evaluate": complete,
        "reviewer": reviewer, "narratives_expected": len(records),
        "tokens_expected": sum(len(r["tokens"]) for r in records),
        "ready_narratives": counts["ready_narratives"],
        "pending_narratives": counts["PENDING"], "deferred_narratives": counts["DEFERRED"],
        "missing_labels": counts["missing_labels"], "invalid_labels": counts["invalid_labels"],
        "case_canonicalizations": canonicalizations, "invalid_label_details": invalid,
        "details": details, "blank_labels_converted_to_o": 0,
        "deferred_records_automatically_replaced_or_dropped": False,
        "neural_inference_executed": False, "metrics_computed": False,
    }
    return report, labels_by_id


def validate_file(workbook, data_dir):
    records, schema = load_locked_data(data_dir)
    reviewer, narratives, tokens = read_annotations(read_xlsx(workbook), records, schema)
    report, labels = validate_annotations(records, schema, reviewer, narratives, tokens)
    report["workbook_sha256"] = digest(workbook)
    return report, labels, records, narratives


def main():
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--data-dir", type=Path, default=base / "data")
    parser.add_argument("--output-dir", type=Path, default=base / "review_validation")
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    report, labels, records, narratives = validate_file(args.workbook, args.data_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dump(args.output_dir / "review_validation.json", report)
    print(json.dumps({k: report[k] for k in ("review_status", "ready_to_evaluate", "ready_narratives", "pending_narratives", "deferred_narratives", "missing_labels", "invalid_labels")}, indent=2))
    if args.freeze:
        if not report["ready_to_evaluate"]:
            raise SystemExit("Review belum lengkap; gold evaluasi tidak ditulis.")
        mapping = {r["review_id"]: r for r in read_json(args.data_dir / "selection_manifest.json")["selected_records"]}
        reviewed_at = datetime.now(timezone.utc).isoformat()
        rows = [{"id": mapping[r["review_id"]]["source_id"], "review_id": r["review_id"], "text": r["text"], "tokens": r["tokens"], "labels": labels[r["review_id"]], "reviewer": report["reviewer"], "review_note": narratives[r["review_id"]]["note"], "annotation_policy": "nara-role-guideline-0.2", "reviewed_at_utc": reviewed_at, "split": "test", "source": "REANNOTATED_HISTORICAL_TEST"} for r in records]
        target = args.output_dir / "test_reviewed_policy02.jsonl"
        with target.open("x", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        dump(args.output_dir / "frozen_test_manifest.json", {"narratives": len(rows), "tokens": sum(len(r["tokens"]) for r in rows), "gold_sha256": digest(target), "workbook_sha256": report["workbook_sha256"], "reviewer": report["reviewer"], "reviewed_at_utc": reviewed_at, "candidate_lock_sha256": digest(args.data_dir / "candidate_lock.json"), "not_for_training_or_checkpoint_selection": True})


if __name__ == "__main__":
    main()
