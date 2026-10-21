"""Data terkunci, alignment first-wordpiece, dan aset lokal NARA.

Alignment mempertahankan satu label per token sumber. Special token dan
wordpiece lanjutan memakai -100. Satu fungsi encoder dipakai training, evaluasi,
dan inferensi; unit corpus dan regex serving tetap dibedakan pada audit.
"""
from __future__ import annotations
from collections import Counter, OrderedDict
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

from silar_ai_adapter import NARA_LABELS, TOKEN_PATTERN
from slr09_runtime import encode_nara_words

LABELS = tuple(NARA_LABELS)
LABEL2ID = {label: i for i, label in enumerate(LABELS)}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def dump_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in rows), encoding="utf-8")


def load_locked_data(root):
    root = Path(root)
    manifest = json.loads((root / "data/dataset_manifest.json").read_text(encoding="utf-8"))
    if manifest["effective_annotation_policy"] != "nara-role-guideline-0.2" or manifest["user_decision"] != "A_PERTAHANKAN_HASIL_REVIEW":
        raise ValueError("Keputusan/pedoman dataset tidak cocok")
    for relative, expected in manifest["files_sha256"].items():
        if sha256(root / relative) != expected:
            raise ValueError("Hash sumber dataset berubah: " + relative)
    rows = {part: read_jsonl(root / f"data/{part}_reviewed.jsonl") for part in ("train", "validation")}
    seen = set()
    for part, items in rows.items():
        historical = set(json.loads((root / f"splits/{part}_ids.json").read_text()))
        if [r["id"] for r in items] != manifest["selected_ids"][part]:
            raise ValueError("ID/urutan data berubah")
        for row in items:
            if row["id"] in seen or row["id"] not in historical:
                raise ValueError("ID duplikat atau partisi salah")
            seen.add(row["id"])
            if len(row["tokens"]) != len(row["labels"]) or any(label not in LABELS for label in row["labels"]):
                raise ValueError("Target label tidak valid")
            if " ".join(row["tokens"]) != row["text"]:
                raise ValueError("Token sumber berubah")
            if not row.get("reviewer"):
                raise ValueError("Target tidak memiliki provenance reviewer")
        support = Counter(label for row in items for label in row["labels"])
        if set(support) != set(LABELS):
            raise ValueError("Cakupan label berbeda dari data yang disetujui")
    test = set(json.loads((root / "splits/test_ids.json").read_text()))
    deferred = {r["id"] for r in read_jsonl(root / "data/excluded_supplement_review.jsonl")}
    if seen & (test | deferred):
        raise ValueError("Test/TUNDA masuk data eksperimen")
    return rows, manifest


def extract_baseline_model(root, model_zip, destination):
    root, destination = Path(root), Path(destination)
    lock = json.loads((root / "data/asset_lock.json").read_text())["models"]["nara"]
    if sha256(model_zip) != lock["archive_sha256"]:
        raise ValueError("ZIP NARA bukan aset sumber yang diaudit")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(model_zip) as archive:
        names = archive.namelist()
        for filename, expected in lock["files"].items():
            if names.count(filename) != 1:
                raise ValueError("Anggota ZIP model tidak unik")
            target = destination / filename
            if target.is_symlink():
                raise ValueError("Target model tidak boleh berupa symlink")
            if not target.exists():
                with archive.open(filename) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
            if sha256(target) != expected:
                raise ValueError("File model berbeda: " + filename)
    config = json.loads((destination / "config.json").read_text())
    if tuple(config["id2label"][str(i)] for i in range(15)) != LABELS:
        raise ValueError("Mapping label checkpoint berubah")
    # training_args.bin tidak diekstrak atau dibaca.
    return destination


def load_historical_test(root, dataset_zip):
    root = Path(root)
    lock = json.loads((root / "data/asset_lock.json").read_text())["dataset"]
    if sha256(dataset_zip) != lock["archive_sha256"]:
        raise ValueError("ZIP dataset berbeda")
    ids = json.loads((root / "splits/test_ids.json").read_text())
    selected = set(ids)
    with zipfile.ZipFile(dataset_zip) as archive:
        names = [name for name in archive.namelist() if name.endswith("3-Labeled Data/all-labeled-data.csv") and "Version 2.0" not in name]
        if len(names) != 1:
            raise ValueError("CSV sumber tidak unik")
        raw = archive.read(names[0])
    if hashlib.sha256(raw).hexdigest() != lock["csv_sha256"]:
        raise ValueError("CSV sumber berbeda")
    grouped = OrderedDict()
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        if row["text_id"] not in selected or row["token"] == "":
            continue
        item = grouped.setdefault(row["text_id"], {"id": row["text_id"], "tokens": [], "labels": []})
        item["tokens"].append(row["token"])
        item["labels"].append(row["argument"])
    if set(grouped) != selected:
        raise ValueError("ID test sumber tidak lengkap")
    return [{**grouped[key], "text": " ".join(grouped[key]["tokens"]),
             "annotation_policy": "HISTORICAL_ORIGINAL_LABELS_NOT_REVIEWED_V02"} for key in ids]


def make_features(records, tokenizer, max_length=256):
    features, metadata = [], []
    for record in records:
        encoded = encode_nara_words(record["tokens"], tokenizer, max_length=max_length)
        positions = encoded["positions"]
        aligned = [-100] * len(encoded["input_ids"])
        for index, position in enumerate(positions):
            aligned[position] = LABEL2ID[record["labels"][index]]
        if not positions:
            raise ValueError("Narasi tanpa target yang dapat diproses")
        features.append({"input_ids": encoded["input_ids"], "attention_mask": encoded["attention_mask"], "labels": aligned})
        regex_units = [match.group(0) for match in TOKEN_PATTERN.finditer(record["text"])]
        metadata.append({"id": record["id"], "source_words": len(record["tokens"]),
                         "processed_words": len(positions), "positions": positions,
                         "input_wordpieces_with_special_tokens": len(encoded["input_ids"]),
                         "partial_last_word": encoded["partial_last_word"],
                         "truncated": len(positions) < len(record["tokens"]) or encoded["partial_last_word"],
                         "runtime_regex_words": len(regex_units),
                         "source_units_equal_runtime_regex_units": record["tokens"] == regex_units})
    return features, metadata


class FeatureDataset:
    def __init__(self, features):
        self.features = features

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index]
