"""Assemble the ordered SLR09 notebook snapshot without rerunning old models."""
from __future__ import annotations

import ast
import base64
import contextlib
import csv
import hashlib
import io
import json
import os
import shutil
import sys
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

WORKSPACE = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1]
FINE_SOURCE = WORKSPACE / "tmp/slr09_final_package_20261018/fine_tune_snapshot"
NARA_EVAL = WORKSPACE / "outputs/SLR09_NARA_Evaluasi_Acuan_Revisi_v0.1"
FINE_AUDIT = WORKSPACE / "inputs/slr09_review80_evaluation_v01/restored/SLR09_NARA_Audit_FineTune_20261018_v0.1"
B1 = WORKSPACE / "outputs/SLR09_B1_Hasil_Review_v0.1"
NEW_SENA = ROOT / "results/sena_reviewed_620"
RUNTIME_ZIP = WORKSPACE / "inputs/slr09_runtime/SLR09_Hasil_Runtime_20261016T121116_789228Z.zip"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def copy(source, relative):
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def code_hash(nb):
    return sha("\n\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code").encode())


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source, tags=None):
    return {"cell_type": "code", "metadata": {"tags": tags or []}, "source": source.splitlines(keepends=True),
            "execution_count": None, "outputs": []}


def make_notebook(cells, name):
    for i, cell in enumerate(cells):
        cell.setdefault("id", sha((name + str(i)).encode())[:12])
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"}, "colab": {"name": name}}, "nbformat": 4, "nbformat_minor": 5}


def payload_cell(files, default_root, variable="WORK_ROOT"):
    payload = {name: base64.b64encode(raw).decode() for name, raw in files.items()}
    encoded = base64.b64encode(zlib.compress(json.dumps(payload).encode(), 9)).decode()
    hashes = {name: sha(raw) for name, raw in files.items()}
    return code(f'''# Restore frozen code/data only; this cell does not run a model.
from pathlib import Path
import base64, hashlib, json, os, sys, zlib
{variable} = Path(os.environ.get("SLR09_NOTEBOOK_ROOT", {default_root!r}))
SNAPSHOT = json.loads(zlib.decompress(base64.b64decode({encoded!r})))
EXPECTED = {hashes!r}
for relative, value in SNAPSHOT.items():
    raw = base64.b64decode(value)
    if hashlib.sha256(raw).hexdigest() != EXPECTED[relative]:
        raise ValueError("Frozen snapshot differs: " + relative)
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Invalid snapshot path")
    target = {variable} / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
sys.path.insert(0, str({variable} / "code"))
print("Snapshot restored:", len(SNAPSHOT), "files.")
''')


def wrap_notebook(source, name, title, description, provenance):
    original_raw = source.read_bytes()
    original = json.loads(original_raw)
    result = json.loads(original_raw)
    note = md(f"# {title}\n\n**Workflow:** baca fungsi dan sumber → tinjau kode/hasil tersimpan → jalankan hanya jika memang memerlukan eksperimen baru.\n\n{description}\n\nKode sumber seluruh sel dipertahankan. Nama TanggapMakna pada path atau metadata historis tetap menunjukkan asal aset. File ini disusun sebagai lampiran kode; tidak wajib dijalankan ulang.\n")
    result["cells"].insert(0, note)
    for i, cell in enumerate(result["cells"]):
        cell.setdefault("id", sha((name + str(i)).encode())[:12])
    result.setdefault("metadata", {})["silar_packaging"] = {
        "source_filename": source.name, "source_sha256": sha(original_raw),
        "original_code_cells_sha256": code_hash(original), "code_changed": False,
        "source_contains_saved_outputs": any(c.get("outputs") for c in original["cells"]),
    }
    assert code_hash(result) == code_hash(original)
    target = ROOT / "notebooks" / name
    dump(target, result)
    original_target = copy(source, "sources/notebooks_original/" + source.name)
    provenance.append({"notebook": target.relative_to(ROOT).as_posix(),
        "source": original_target.relative_to(ROOT).as_posix(),
        "source_sha256": sha(original_raw), "code_cells_sha256": code_hash(original),
        "all_code_cells_unchanged": True,
        "original_saved_output_cells": sum(bool(c.get("outputs")) for c in original["cells"])})


def prepare_sources():
    for relative in ["data/sena_train_reviewed.jsonl", "data/sena_validation_reviewed.jsonl"]:
        copy(B1 / "checkpoint" / Path(relative).name, relative)
    copy(NEW_SENA / "evaluation.json", "data/baseline_reviewed_evaluation.json")
    manifest = {"schema": "sena-reviewed-pilot-input-0.1", "training_executed": False,
        "train_narratives": 110, "validation_narratives": 620,
        "historical_base_training_membership_verified": False,
        "deferred_ids": ["BAN-01028", "KEB-01113", "BAN-01529"],
        "sha256": {name: sha((ROOT / name).read_bytes()) for name in [
            "data/sena_train_reviewed.jsonl", "data/sena_validation_reviewed.jsonl", "data/baseline_reviewed_evaluation.json"]}}
    dump(ROOT / "data/input_manifest.json", manifest)
    for relative in ["checkpoint/review_checkpoint.json", "review_manifest.json", "source/SLR09_B1_Review_Anotasi_MVP_20261017.xlsx"]:
        copy(B1 / relative, "sources/sena_review/" + Path(relative).name)
    copy(RUNTIME_ZIP, "sources/SLR09_Hasil_Runtime_20261016T121116_789228Z.zip")
    copy(FINE_AUDIT / "sources/SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip", "sources/SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip")
    copy(WORKSPACE / "upload/SLR09_NARA_Hasil_Evaluasi_Acuan_Revisi_20261018T040239Z.zip", "sources/SLR09_NARA_Hasil_Evaluasi_Acuan_Revisi_20261018T040239Z.zip")
    for folder, prefix in [(NARA_EVAL / "results", "results/nara_reviewed_79"), (NARA_EVAL / "evidence", "evidence/nara_reviewed_79")]:
        for source in folder.iterdir():
            if source.is_file(): copy(source, prefix + "/" + source.name)
    for source in (NARA_EVAL / "code").glob("*.py"):
        copy(source, "code/nara_reviewed_evaluation/" + source.name)
    for source in FINE_SOURCE.rglob("*"):
        if source.is_file(): copy(source, "nara_finetune_frozen/" + source.relative_to(FINE_SOURCE).as_posix())
    for source in (FINE_SOURCE / "code").iterdir():
        if source.is_file(): copy(source, "code/active_nara_adapter/" + source.name)
    for source in [FINE_AUDIT / "audit/perubahan_84_field.csv", FINE_AUDIT / "audit/riwayat_epoch.csv"]:
        copy(source, "results/nara_adapter_12/" + source.name)
    for source in (FINE_AUDIT / "audit/grafik_dari_colab").iterdir():
        if source.is_file(): copy(source, "results/nara_training_figures/" + source.name)
    copy(FINE_AUDIT / "SLR09_NARA_Laporan_Pemeriksaan_FineTune_20261018_v0.1.md", "docs/SLR09_NARA_Laporan_Pemeriksaan_FineTune_20261018_v0.1.md")
    copy(NARA_EVAL / "SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md", "docs/SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md")
    governance = WORKSPACE / "inputs/slr09_final_sources_20261018/governance/CT"
    copy(governance / "SILAR_Card_SLR07-16_Final.md", "sources/governance/SILAR_Card_SLR07-16_Final.md")
    copy(governance / "SILAR_Technical_Reference(1).docx", "sources/governance/SILAR_Technical_Reference_v0.3.docx")
    context = WORKSPACE / "inputs/slr09_final_sources_20261018/notebook_and_context/CT"
    copy(context / "MEET.md", "sources/governance/MEET.md")
    copy(context / "Internet Programming II (1).pdf", "sources/governance/Internet_Programming_II.pdf")
    with ZipFile(RUNTIME_ZIP) as archive:
        for member in ["results/smoke/run_summary.json", "results/sena_validation/run_summary.json", "results/candidate_split/split_manifest.json"]:
            destination = ROOT / "evidence/baseline_runtime" / Path(member).parent.name / Path(member).name
            destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(archive.read(member))
    with ZipFile(ROOT / "sources/SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip") as archive:
        for member in ["run_state.json", "model_export_manifest.json", "comparison.json", "baseline_nara_v1_field_diagnostics.json", "finetuned_nara_field_diagnostics.json"]:
            destination = ROOT / "evidence/nara_finetune" / member
            destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(archive.read(member))


def plot_sena():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    evaluation = json.loads((NEW_SENA / "evaluation.json").read_text())
    labels = evaluation["metrics_reviewed"]["labels"]
    matrix = evaluation["metrics_reviewed"]["confusion_matrix_rows_gold_columns_prediction"]
    fig, ax = plt.subplots(figsize=(8, 6.4), constrained_layout=True)
    im = ax.imshow(matrix, cmap="Blues"); fig.colorbar(im, ax=ax, shrink=.78)
    ax.set(xticks=range(5), yticks=range(5), xticklabels=labels, yticklabels=labels,
        xlabel="Prediksi SENA v1 tersimpan", ylabel="Label review final",
        title="SENA: 620 label review final\nPrediksi lama; tidak ada inferensi baru")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    for i, row in enumerate(matrix):
        for j, number in enumerate(row):
            ax.text(j, i, str(number), ha="center", va="center", color="white" if number > 65 else "#17243b", fontsize=11)
    fig.savefig(NEW_SENA / "confusion_matrix.png", dpi=165); plt.close(fig)


def write_reports():
    e = json.loads((NEW_SENA / "evaluation.json").read_text())
    m = e["metrics_reviewed"]
    per = "\n".join(f"| {label} | {v['support']} | {v['precision']*100:.2f}% | {v['recall']*100:.2f}% | {v['f1']*100:.2f}% |" for label, v in m["per_class"].items())
    cuts = "\n".join(f"| {r['threshold']:.2f} | {r['below_threshold_uncertain']} | {r['at_or_above_threshold']} | {(r['accuracy_at_or_above']*100 if r['accuracy_at_or_above'] is not None else 0):.2f}% | {r['false_non_event_at_or_above']} |" for r in e["cutoff_analysis"] if r["threshold"] in [.8,.9,.95,.99])
    report = f'''# SLR09 - Rekap notebook, evaluasi SENA, dan kesiapan aset v0.1

**Workflow:** gunakan bukti yang sudah ada -> lengkapi evaluasi pada acuan final -> catat bagian yang selesai -> jalankan hanya eksperimen baru yang diperlukan -> finalisasi penyerahan.

Tanggal: 18 Oktober 2026. Paket ini merupakan snapshot pekerjaan sampai tahap ini. Notebook pelatihan awal dan fine-tune NARA dihimpun lengkap; training SENA baru belum dijalankan. Tidak ada model, anotasi, PRD, threshold produksi, atau repository aplikasi yang diubah oleh penyusunan paket ini.

## Hasil yang sudah selesai dan tidak perlu diulang

| Bagian | Hasil | Batas pembacaan |
| --- | --- | --- |
| NARA fine-tune | 157 train, 41 validation; 10 epoch; validation macro F1 78,65% | Validation dipakai memilih checkpoint. |
| NARA pada acuan revisi | 79 narasi/1.701 token; macro F1 53,43% -> 79,32% | UJI-019 tetap DEFERRED; bukan penuh 80. |
| NARA pada test historis | Macro F1 67,77% -> 58,56% | Acuan label lama; hasil tetap dipertahankan. |
| Adapter tujuh field | 66/84 -> 73/84 nilai cocok; 13 membaik, 6 memburuk, 5 tetap salah, 60 tetap cocok | 12 diagnostik dikenal; nilai kosong ikut dihitung. |
| Pemeriksaan bobot NARA baru | Ekspor/reload dilaporkan berhasil oleh run Colab | Bobot tidak dibuka langsung dalam penyusunan paket ini. |
| SENA terhadap 620 label final | Accuracy {m['accuracy']*100:.2f}%; macro F1 {m['macro_f1_all_five_classes']*100:.2f}% | Analisis retrospektif dari prediksi tersimpan. |

Laporan evaluasi NARA yang dikirim pengguna identik dengan laporan sebelumnya; metrik dan tabel kesalahan sama. Perbedaan evaluation.json hanya waktu pembuatan. Tidak ada alasan menjalankan ulang evaluasi tersebut.

## Temuan baru: SENA belum sesuai dengan keseluruhan review final

Analisis lama memakai 623 kandidat: 71 referensi hasil review dan 552 label sumber. Angka 94,70% accuracy dan 94,39% macro F1 dari referensi campuran tersebut tetap berlaku dalam cakupannya, tetapi tidak menggambarkan seluruh hasil review B1 yang kemudian diselesaikan.

Paket sekarang mencocokkan 620 referensi final dengan ID, teks persis, hash input, kategori, confidence, dan probabilitas dari run SENA yang sama. Tiga kasus TUNDA tetap dikeluarkan: BAN-01028, KEB-01113, BAN-01529. Tidak ada bobot berubah atau inferensi baru. Label final mengikuti keputusan reviewer, bukan koreksi otomatis oleh kode.

| Acuan pada 620 narasi yang sama | Accuracy | Macro F1 lima kelas |
| --- | --- | --- |
| Label sumber historis | {e['metrics_original_gold_same_620']['accuracy']*100:.2f}% | {e['metrics_original_gold_same_620']['macro_f1_all_five_classes']*100:.2f}% |
| Seluruh review final | {m['accuracy']*100:.2f}% | {m['macro_f1_all_five_classes']*100:.2f}% |

Review mengubah 228 dari 620 label. SENA memprediksi 334 NON_EVENT, sedangkan acuan final memiliki 131 NON_EVENT. Dari 489 narasi berlabel kejadian dalam review, **213 diprediksi NON_EVENT (43,56%)**. Ada 10 arah sebaliknya (acuan NON_EVENT, prediksi kejadian), tanpa pertukaran antarempat kategori kejadian pada subset ini. Total 397 benar dan 223 berbeda dari acuan.

{per_header()}
{per}

Ini menunjukkan ketidakselarasan SENA terhadap kebijakan anotasi final pada subset ini. Hasil tersebut tidak menunjukkan bahwa bobot SENA tiba-tiba berubah setelah evaluasi lama. Identitas kandidat validation terhadap train/validation checkpoint SENA historis tetap belum terbukti; karena itu skor bukan test independen.

## Threshold belum dapat menyelesaikan kesalahan kategori

| Cutoff confidence | Di bawah cutoff | Pada/di atas cutoff | Accuracy kelompok atas | Salah NON_EVENT pada kelompok atas |
| --- | --- | --- | --- | --- |
{cuts}

Pada cutoff 0,95, masih ada 152 salah NON_EVENT dengan confidence tinggi. Mengubah cutoff hanya menambah penanda LOW_CLASSIFICATION_CONFIDENCE; tidak mengubah kategori dan tidak membuka blokir NON_EVENT. Human Verification tetap wajib pada confidence berapa pun. Tabel ini merupakan analisis cutoff, tanpa temperature scaling dan tanpa memilih threshold produksi.

## Adapter A4.22: pemeriksaan yang sudah tersedia

Adapter aktif dalam eksperimen NARA adalah silar-adapter-0.4.0, guard silar-victim-guard-0.4.0, pedoman nara-role-guideline-0.2. Kode utuh berada pada code/active_nara_adapter/ dan nara_finetune_frozen/code/.

| Field | Baseline cocok | Fine-tune cocok | Catatan |
| --- | --- | --- | --- |
| location_text | 9/12 | 11/12 | D04 masih mencampur kios dengan dekat pasar. |
| time_text | 12/12 | 10/12 | D07 tahun muncul; D08 pagi ini menjadi pagi. |
| occurred_at | 12/12 | 12/12 | Seluruh acuan null; belum menguji tanggal/jam berisi. |
| involved_parties | 7/12 | 12/12 | Perbaikan pada pihak yang disebut. |
| impacts | 6/12 | 5/12 | Tambahan frasa yang tidak sesuai acuan masih muncul. |
| victims | 12/12 | 12/12 | Hanya satu acuan berisi pada diagnostik ini. |
| affected_objects | 8/12 | 11/12 | D04 kios masih hilang. |

Enam regresi adalah D07 time_text/impacts, D08 time_text/impacts, D10 impacts, dan D11 impacts. Label/gold tidak diubah agar cocok dengan prediksi. Tidak menambah filter heuristik, membuang ekstraksi hanya karena NON_EVENT, memperluas field, atau menjalankan adapter yang sama lagi pada paket ini. Pada validasi kondisi fisik sebelumnya, kasus sesak nafas masih gagal dan tetap dicatat. Skor WOUND 100% pada 79 narasi hanya memiliki lima token dalam dua narasi.

## Eksperimen berikutnya yang benar-benar baru

Notebook 07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb disiapkan untuk fine-tune **SENA**, memakai **110 train dan 620 validation hasil review yang sudah ada**. Tiga TUNDA tetap dikecualikan; label dan peran split dipertahankan. NARA tidak dilatih atau diuji ulang. Baseline 620 dipakai dari hasil tersimpan sehingga inferensi baseline tidak diulang.

Konfigurasi mengikuti sumber historis: seed 42, max_length 256, LR 2e-5, batch 16/32, weight decay 0,01, maksimal 10 epoch, patience 2, best checkpoint berdasarkan macro F1 lima kelas. Dataset train/validation serta SHA-nya tertanam. Source model memakai SILAR_SENA_v1.zip yang sudah ada di MyDrive/SILAR_SLR09, dengan verifikasi hash. Tidak membutuhkan unggah ulang model atau review tambahan.

Run all pada notebook 07 menjalankan training baru di GPU Colab. Paket ini hanya memverifikasi sintaks, bootstrap, dan data notebook tersebut. **Training, kualitas model baru, reload model baru, dan hasil GPU notebook 07 belum diuji di sini.** Tidak ada angka hasil SENA fine-tune yang dibuat sebelum eksekusi.

Hasil yang perlu diperiksa setelah run adalah SLR09_SENA_Hasil_FineTune_<run_id>.zip. Model baru disimpan terpisah di Drive. Pemilihan model dan threshold produksi tidak otomatis dilakukan. Validation dipakai memilih checkpoint; skor validation bukan test baru yang buta. SENA historis tidak mengekspor identitas train/validation lengkap, sehingga keterbatasan paparan checkpoint awal tetap dicatat.

## Status terhadap card SLR09

| Task card | Bukti/status saat ini |
| --- | --- |
| Audit dua aset dan asalnya | Tersedia: lock/hash, label, notebook sumber, bukti run. Bobot NARA baru mengikuti manifest Colab. |
| Sumber/lisensi, preprocessing, anotasi, split | Terdokumentasi. NARA memiliki ID split; SENA historis memiliki keterbatasan identitas split. |
| Input/kategori/confidence SENA | Terverifikasi dari 623 prediksi aktual; 620 dinilai terhadap review final. |
| Label/span/pemetaan NARA | Tersedia 15 label, adapter 0.4, evaluasi token/span dan 84 field diagnostik. |
| Kode/proses pelatihan | Kode awal SENA/NARA lengkap; fine-tune NARA selesai. Fine-tune SENA baru disiapkan. |
| Evaluasi sesuai MVP/kasus NON_EVENT | NARA dan SENA dilaporkan terpisah; temuan salah NON_EVENT SENA belum diperbaiki. |
| Target mutu penerimaan akhir | Angka penerimaan final belum disepakati; tidak dibuat otomatis dari skor yang sudah terlihat. |
| Adapter/contoh/versi untuk SLR11 | Kode lengkap dan contoh nyata tersedia; regresi tetap dicatat. |
| Kalibrasi/ambiguity/threshold | Analisis cutoff tersedia; threshold produksi null. Kemampuan deteksi konflik umum tidak diklaim. |
| Pemuatan/dependensi/sumber daya | Baseline sudah berjalan pada CPU notebook; NARA fine-tune/reload pada T4 menurut laporan. Belum bukti VM tujuan. |
| Versioning/aset besar | Hash, versi, sumber dan pedoman penempatan tersedia. Commit/LFS repository tidak dilakukan dalam percakapan ini. |
| Review kelompok/commit | Keputusan reviewer dipertahankan. Penutupan card dan commit kelompok belum diklaim. |

Status yang sesuai saat ini adalah **SLR09 masih In Progress**, dengan eksperimen perbaikan SENA yang konkret. UJI-019 dan tiga TUNDA bukan alasan mengulang narasi yang sudah disetujui. Integrasi backend, Whisper/Gemini, media, deployment dan benchmark sistem penuh mengikuti SLR11/SLR15/SLR16, bukan eksperimen tambahan tersembunyi pada paket ini.

## Urutan notebook

1. 00_SLR09_Hasil_Terverifikasi.ipynb: ringkasan aktual yang bisa dibaca tanpa menjalankan model.
2. 01_SENA_Pelatihan_Awal.ipynb: seluruh kode V3A; sumber asli tidak menyimpan output training.
3. 02_NARA_Pelatihan_Awal.ipynb: seluruh kode V2 dan output historis yang tersimpan.
4. 03_NARA_FineTune_dan_Evaluasi.ipynb: eksperimen NARA yang sudah selesai; lampiran, tidak perlu Run all.
5. 04_NARA_Evaluasi_Acuan_Revisi.ipynb: evaluasi 79 narasi yang sudah selesai; reproduksi opsional.
6. 05_SILAR_Inferensi_Baseline_dan_Kalibrasi.ipynb: runtime baseline 0.2; bukan runner kandidat NARA 0.4 baru.
7. 06_SENA_Evaluasi_620_Review.ipynb: kode analisis baru yang hasilnya sudah dihitung di paket ini.
8. 07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb: satu eksperimen baru yang belum dijalankan.

Notebook feasibility, evaluasi lokal, Fusion GEMASTIK, blind lama, dan salinan V2 disertakan pada historical/. Completeness Engine, status lama, pertanyaan adaptif dan aturan historis tidak diaktifkan menjadi fitur SILAR. Penomoran notebook menyatakan alur ketergantungan, bukan klaim tanggal pasti semua eksperimen lama. Urutan dokumen tetap: laporan perancangan -> hasil revisi -> penyempurnaan Acuan Teknis SLR04 (versi desain 0.3), lalu pemetaan MEET05; PRD tidak diubah.

## Provenance dan lisensi

Dataset: Semantic Role Labeling Datasets for Crisis Event, Ariyanto dkk.; halaman Mendeley versi 2, DOI 10.17632/r76v5sjyv2.2, menyatakan CC BY 4.0. Backbone indolem/indobert-base-uncased menyatakan MIT pada model card. Rujukan diperiksa 18 Oktober 2026. Ini identitas lisensi sumber yang dinyatakan penerbit, bukan pemberian lisensi baru untuk proyek atau bukti commit backbone yang dipakai training historis.

- https://data.mendeley.com/datasets/r76v5sjyv2/2
- https://huggingface.co/indolem/indobert-base-uncased
- https://huggingface.co/indolem/indobert-base-uncased/blob/7ccb3cd0f5b08ffbaa465aade22328e8600e23eb/README.md

Identitas byte dataset run mengikuti asset_lock: arsip 3e22f54044e7b44f49a243aeb3e6fdad3dc2ce0d000ce8a0fd5a33f7d9c56cbf dan CSV 14ff9121e37cdaed2a0b8f35e2131da4c710daebf2cad0781fdbbdfdad00c211. Versi halaman publik tidak dipakai untuk mengklaim kesamaan byte arsip. Dataset besar dan bobot tetap mengikuti sumber Drive; paket tidak menyertakan bobot.

## Pemeriksaan paket

Metrik baru SENA telah dicocokkan dengan scikit-learn (accuracy, macro/weighted F1, precision/recall/F1/support setiap kelas dan confusion matrix) pada kedua acuan 620 narasi yang sama. Sumber review cocok dengan checkpoint, manifest dan workbook terkunci. Hash input dan probabilitas dicocokkan pada setiap narasi. Tidak ada training atau inferensi neural baru pada penyusunan paket. Evidence berisi hasil pemeriksaan, hash notebook sumber, status notebook baru dan manifest berkas.
'''
    (ROOT / "SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md").write_text(report, encoding="utf-8")
    readme = '''# SLR09 - Paket notebook dan rekap v0.1

**Workflow:** baca rekap -> buka notebook 00 -> gunakan hasil yang sudah selesai -> jalankan hanya notebook 07 jika meneruskan perbaikan SENA.

Tidak perlu menjalankan ulang notebook 01-06. Seluruh kode lengkap tersedia. Notebook 07 adalah eksperimen baru SENA, belum hasil training.

| Folder/berkas | Isi |
| --- | --- |
| SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md | Status, hasil SENA/NARA, adapter, threshold dan urutan. |
| notebooks/ | Delapan notebook bernomor 00-07. |
| historical/ | Feasibility dan pipeline lama sebagai riwayat. |
| code/ | Analisis SENA baru, training SENA yang disiapkan, builder dan kode adapter NARA lengkap. |
| nara_finetune_frozen/ | Kode/data/split yang tertanam pada notebook fine-tune NARA yang telah dipakai. |
| data/ | 110 train, 620 validation SENA yang sudah direview dan baseline beku. |
| results/ | Metrik, per kelas, matriks, kesalahan dan cutoff, termasuk hasil NARA yang dipakai ulang. |
| evidence/ | Pemeriksaan serta asal eksekusi; tidak berisi klaim training baru. |
| sources/ | Notebook asli, review, hasil run dan acuan; byte sumber dipertahankan. |

Untuk training baru: notebook 07 memakai GPU Colab dan ZIP SILAR_SENA_v1.zip yang sudah ada di MyDrive/SILAR_SLR09. Data review dan kode tertanam. Hasil disimpan ke Drive dalam ZIP model dan ZIP hasil kecil terpisah. NARA tidak dilatih ulang. Tidak ada threshold produksi otomatis.

Nama file notebook utama memakai SENA/NARA. Kode sel notebook sumber tidak diubah; path historis TanggapMakna tetap dipertahankan agar asal dan eksperimennya dapat ditelusuri. Metadata provenance mencatat hash file asal dan hash semua code cell. Output yang tersimpan pada sumber tidak disebut output run baru.

Notebook 05 khusus baseline lama; adapter aktif 0.4 berada pada code/active_nara_adapter dan notebook 03. Jangan mengganti adapter baru dengan runner baseline lama.
'''
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def per_header():
    return "| Kategori | Acuan | Precision | Recall | F1 |\n| --- | --- | --- | --- | --- |"


def build_notebooks():
    provenance = []
    definitions = [
        (WORKSPACE / "inputs/slr09_legacy/CT/TanggapMakna_V3A_EventClassifier.ipynb", "01_SENA_Pelatihan_Awal.ipynb", "SENA - Pelatihan awal", "Sumber V3A membentuk lima kategori dari dataset, melatih IndoBERT, mengevaluasi test, menghitung confusion matrix, dan mengekspor aset. Sumber yang diterima tidak menyimpan output training. Angka SENA saat ini terdapat pada notebook 00/06; tidak dibuat sebagai output training V3A."),
        (WORKSPACE / "upload/TanggapMakna_SRL_Feasibility_V2.ipynb", "02_NARA_Pelatihan_Awal.ipynb", "NARA - Pelatihan awal 15 label", "Sumber V2 melatih 15 label flat, melakukan alignment subword, evaluasi, dan ekspor. Output di bawah adalah output historis sumber. Prototype Completeness Engine pada bagian akhir adalah riwayat eksperimen; tidak menjadi fitur aktif SILAR."),
        (WORKSPACE / "inputs/slr09_final_sources_20261018/notebook_and_context/SLR09_NARA_FineTune_dan_Evaluasi_v0.1.ipynb", "03_NARA_FineTune_dan_Evaluasi.ipynb", "NARA - Fine-tune dan evaluasi", "Eksperimen 157 train/41 validation sudah dijalankan pada run 20261018T001122_607337Z. Run all di bawah benar-benar akan melatih lagi; tidak diperlukan untuk pekerjaan saat ini. Hasil aktual berada pada sources/SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip dan notebook 00."),
        (NARA_EVAL / "SLR09_NARA_Evaluasi_Acuan_Revisi_v0.1.ipynb", "04_NARA_Evaluasi_Acuan_Revisi.ipynb", "NARA - Evaluasi acuan revisi", "Evaluasi 79 narasi sudah dihitung dan diperiksa. Menjalankan notebook ini hanya reproduksi opsional; UJI-019 tetap DEFERRED. Tidak ada training atau inferensi baru."),
        (WORKSPACE / "outputs/SLR09_Runtime_v0.2.0/notebooks/SLR09_Uji_Inferensi_dan_Kandidat_Threshold_v0.3.ipynb", "05_SILAR_Inferensi_Baseline_dan_Kalibrasi.ipynb", "SILAR - Inferensi baseline dan analisis cutoff", "Ini dokumentasi runtime baseline 0.2.0 dengan bobot awal. Replay/inferensi baseline telah berjalan sebelumnya. Bukan runner kandidat NARA 0.4 baru. Hasil cutoff lama tidak dikunci sebagai threshold produksi."),
    ]
    for args in definitions: wrap_notebook(*args, provenance)
    historical = [
        WORKSPACE / "upload/TanggapMakna_AI_Feasibility_Colab.ipynb",
        WORKSPACE / "upload/TanggapMakna_Local_Evaluation_FINAL.ipynb",
        WORKSPACE / "upload/Salinan_dari_TanggapMakna_SRL_Feasibility_V2.ipynb",
        WORKSPACE / "inputs/slr09_legacy/CT/TanggapMakna_V3_Fusion_Engine_v1_1_FIXED.ipynb",
        WORKSPACE / "inputs/slr09_legacy/CT/TanggapMakna_FINAL_One_Time_Blind_Evaluation.ipynb",
    ]
    for source in historical: copy(source, "historical/" + source.name)
    dump(ROOT / "evidence/notebook_source_provenance.json", provenance)

    # New SENA evaluation notebook: identical analysis function already executed.
    files = {"code/evaluate_sena_reviewed.py": (ROOT / "code/evaluate_sena_reviewed.py").read_bytes(),
        "source/runtime.zip": RUNTIME_ZIP.read_bytes(),
        "source/review.jsonl": (ROOT / "data/sena_validation_reviewed.jsonl").read_bytes(),
        "source/checkpoint.json": (B1 / "checkpoint/review_checkpoint.json").read_bytes(),
        "source/manifest.json": (B1 / "review_manifest.json").read_bytes(),
        "source/reviewed.xlsx": (B1 / "source/SLR09_B1_Review_Anotasi_MVP_20261017.xlsx").read_bytes()}
    cells = [md("# SENA - Evaluasi 620 label review final\n\n**Workflow:** pulihkan snapshot -> cocokkan sumber -> hitung metrik -> baca kesalahan/cutoff.\n\nHasil sudah dihitung pada paket ini. Tidak wajib dijalankan ulang. Notebook memakai prediksi lama; tidak memuat model, training, inferensi neural atau threshold produksi. Tiga TUNDA tetap tidak dinilai.\n"),
        payload_cell(files, "/content/slr09_sena_reviewed_620"),
        code('''from evaluate_sena_reviewed import evaluate
evaluation = evaluate(WORK_ROOT / "source/runtime.zip", WORK_ROOT / "source/review.jsonl",
    WORK_ROOT / "source/checkpoint.json", WORK_ROOT / "source/manifest.json",
    WORK_ROOT / "source/reviewed.xlsx", WORK_ROOT / "results")
print(json.dumps(evaluation["metrics_reviewed"], indent=2))
print("Cakupan:", evaluation["scope"])
'''), md("## Kode lengkap\n\nFile yang sama juga tersedia pada code/evaluate_sena_reviewed.py.\n\n```python\n" + (ROOT / "code/evaluate_sena_reviewed.py").read_text() + "\n```\n")]
    dump(ROOT / "notebooks/06_SENA_Evaluasi_620_Review.ipynb", make_notebook(cells, "06_SENA_Evaluasi_620_Review.ipynb"))

    # New SENA experiment, not executed here. Full code and frozen review embedded.
    train_files = {name: (ROOT / name).read_bytes() for name in ["code/sena_experiment.py", "code/evaluate_sena_reviewed.py",
        "data/input_manifest.json", "data/sena_train_reviewed.jsonl", "data/sena_validation_reviewed.jsonl", "data/baseline_reviewed_evaluation.json"]}
    cells = [md("# SLR09 - Fine-tune SENA dan evaluasi v0.1\n\n**Workflow:** pulihkan data review -> gunakan baseline tersimpan -> muat SENA v1 dari Drive -> fine-tune 110 train -> pilih checkpoint pada 620 validation -> evaluasi -> ekspor.\n\n**Ini eksperimen baru yang belum dijalankan. Run all akan melatih SENA.** Pilih GPU Colab. NARA tidak dilatih atau diuji ulang. Tidak perlu mengunggah ulang model atau mengisi review lagi. Tiga TUNDA tetap dikecualikan. Validation dipakai memilih checkpoint dan bukan test independen. Tidak mengganti model aktif atau menetapkan threshold produksi.\n"),
        md("## 1. Dependensi\n\nGunakan sesi GPU baru; PyTorch bawaan Colab dipakai. Transformers mengikuti versi yang telah dipakai pada run NARA sebelumnya.\n"),
        code('''import os, subprocess, sys
os.environ["USE_TF"] = "0"
os.environ["USE_FLAX"] = "0"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "transformers==4.57.1", "accelerate>=1.2,<2", "safetensors>=0.4,<1", "matplotlib", "scikit-learn"])
''', ["requires-colab-gpu"]),
        md("## 2. Snapshot dan validasi data\n\nSel ini hanya memulihkan kode/data dan memeriksa input; belum memuat atau melatih model.\n"),
        payload_cell(train_files, "/content/slr09_sena_finetune_v01"),
        code('''from sena_experiment import SenaExperiment, validate_reviewed_data
checked = validate_reviewed_data(WORK_ROOT)
print({k: checked[k] for k in ["train_narratives", "validation_narratives", "train_class_counts", "validation_class_counts"]})
print("Baseline tersimpan:", checked["baseline"]["metrics_reviewed"]["accuracy"], checked["baseline"]["metrics_reviewed"]["macro_f1_all_five_classes"])
print("Tidak ada inferensi baseline ulang.")
'''),
        md("## 3. Drive dan sumber model\n\nZIP SILAR_SENA_v1.zip sudah berada di folder yang sama seperti pekerjaan sebelumnya. Hash sumber diperiksa sebelum training.\n"),
        code('''from google.colab import drive
drive.mount("/content/drive")
DRIVE_FOLDER = Path("/content/drive/MyDrive/SILAR_SLR09")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
experiment = SenaExperiment(WORK_ROOT, DRIVE_FOLDER)
print("Run baru:", experiment.run_id)
''', ["requires-colab-gpu"]),
        md("## 4. Pemuatan dan pemeriksaan alignment input\n\nMemastikan GPU, hash bobot, urutan lima label, input tidak terpotong dan pembagian data.\n"),
        code('''prepared = experiment.prepare()
print(json.dumps(prepared, ensure_ascii=False, indent=2))
''', ["requires-colab-gpu"]),
        md("## 5. Fine-tune baru\n\nMaksimal 10 epoch dan patience 2. Checkpoint dipilih dari macro F1 lima kelas validation. Test tidak dipakai.\n"),
        code('''training = experiment.fit()
print(json.dumps(training, ensure_ascii=False, indent=2))
''', ["requires-colab-gpu"]),
        md("## 6. Evaluasi kandidat baru\n\nMenghasilkan precision/recall/F1 per kelas, confusion matrix, kesalahan NON_EVENT, kurva dan analisis cutoff. Hasil baseline dipakai dari perhitungan yang sudah selesai.\n"),
        code('''evaluation = experiment.evaluate()
print(json.dumps(evaluation, ensure_ascii=False, indent=2))
''', ["requires-colab-gpu"]),
        md("## 7. Ekspor dan pemeriksaan reload\n\nModel diuji reload pada tiga contoh dan disimpan ke Drive. Hasil kecil tersimpan terpisah dari bobot.\n"),
        code('''saved = experiment.export()
print(json.dumps(saved, ensure_ascii=False, indent=2))
''', ["requires-colab-gpu"]),
        md("## Hasil yang dikirim kembali\n\nKirim **SLR09_SENA_Hasil_FineTune_<run_id>.zip**. Model besar tetap di Drive. Jika gagal, ZIP hasil sementara menyimpan stage/status; periksa sebelum memulai training baru. Tidak perlu menjalankan notebook NARA kembali.\n")]
    for name in ["sena_experiment.py", "evaluate_sena_reviewed.py"]:
        cells.append(md("## Lampiran kode lengkap: " + name + "\n\n```python\n" + (ROOT / "code" / name).read_text() + "\n```\n"))
    dump(ROOT / "notebooks/07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb", make_notebook(cells, "07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb"))

    # Reader notebook executes only reads/prints of already computed results.
    summary_files = {
        "cached/nara_evaluation.json": (NARA_EVAL / "results/evaluation.json").read_bytes(),
        "cached/sena_evaluation.json": (NEW_SENA / "evaluation.json").read_bytes(),
        "cached/adapter_fields.csv": (ROOT / "results/nara_adapter_12/perubahan_84_field.csv").read_bytes(),
    }
    cells = [md("# SLR09 - Hasil terverifikasi dan urutan notebook\n\n**Workflow:** baca hasil yang sudah ada -> pahami cakupan -> lanjutkan hanya eksperimen baru SENA.\n\nSel notebook ini membaca snapshot hasil, tanpa training atau inferensi. Tidak wajib dijalankan ulang. Notebook 01-06 menjadi lampiran kode untuk pekerjaan yang sudah tersedia; notebook 07 adalah eksperimen baru SENA yang belum dijalankan.\n"), payload_cell(summary_files, "/content/slr09_hasil_terverifikasi"),
        code('''nara = json.loads((WORK_ROOT / "cached/nara_evaluation.json").read_text())
sena = json.loads((WORK_ROOT / "cached/sena_evaluation.json").read_text())
print("NARA:", nara["coverage"]["scored_narratives"], "narasi;", nara["coverage"]["scored_tokens"], "token")
for model in ["baseline", "finetuned"]:
    metric = nara["metrics"][model]["reviewed_gold"]["token_metrics"]
    print(model, "macro F1 non-O:", format(metric["macro_f1_no_o"], ".6f"))
print("SENA:", sena["records_scored"], "review final dari", sena["records_original"])
print("Accuracy:", format(sena["metrics_reviewed"]["accuracy"], ".6f"))
print("Macro F1:", format(sena["metrics_reviewed"]["macro_f1_all_five_classes"], ".6f"))
print("Salah NON_EVENT:", sena["metrics_reviewed"]["false_non_event_count"])
'''),
        md("## Adapter tujuh field\n\nHasil berikut berasal dari CSV audit run NARA yang sudah selesai. Ini 12 diagnostik dikenal dan nilai kosong ikut dihitung.\n"),
        code('''import csv
with (WORK_ROOT / "cached/adapter_fields.csv").open(encoding="utf-8-sig") as stream:
    fields = list(csv.DictReader(stream))
print("Field diperiksa:", len(fields))
print("Baseline cocok:", sum(r["baseline_correct"] == "True" for r in fields))
print("Fine-tune cocok:", sum(r["finetuned_correct"] == "True" for r in fields))
print("Perubahan:")
for row in fields:
    if row["baseline_correct"] == "True" and row["finetuned_correct"] == "False":
        print(row["id"], row["field"], "reference:", row["reference"], "hasil:", row["finetuned"])
'''),
        md("## Confidence tidak memperbaiki kategori\n\nNON_EVENT tetap memblokir pengiriman di setiap cutoff; Human Verification tetap diperlukan.\n"),
        code('''for row in sena["cutoff_analysis"]:
    if row["threshold"] in [0.8, 0.9, 0.95, 0.99]:
        print("Cutoff", row["threshold"], "di bawah:", row["below_threshold_uncertain"], "salah NON_EVENT pada/di atas:", row["false_non_event_at_or_above"])
print("Training baru pada penyusunan paket: tidak.")
print("Threshold produksi dipilih: tidak.")
print("Berikutnya: notebook 07, fine-tune SENA dengan review yang sudah ada.")
''')]
    for relative, title in [("results/sena_reviewed_620/confusion_matrix.png", "SENA terhadap 620 review final"),
                            ("results/nara_reviewed_79/f1_per_label.png", "NARA terhadap 79 review final")]:
        image = (ROOT / relative).read_bytes(); name = Path(relative).name
        cell = md(f"## {title}\n\n![{title}](attachment:{name})\n")
        cell["attachments"] = {name: {"image/png": base64.b64encode(image).decode()}}
        cells.append(cell)
    dump(ROOT / "notebooks/00_SLR09_Hasil_Terverifikasi.ipynb", make_notebook(cells, "00_SLR09_Hasil_Terverifikasi.ipynb"))


def main():
    completed_report = ROOT / "sources/SLR09_SENA_Hasil_FineTune_20261018T044447_926664Z.zip"
    if completed_report.exists():
        # After the external run, the completed-results updater owns the snapshot.
        from update_package_after_sena import update
        update(ROOT)
        return
    prepare_sources()
    plot_sena()
    write_reports()
    build_notebooks()
    dump(ROOT / "evidence/current_operation.json", {"created_utc": datetime.now(timezone.utc).isoformat(),
        "new_sena_evaluation_uses_existing_predictions_and_new_final_references": True,
        "nara_evaluation_repeated": False, "adapter_replay_repeated": False,
        "new_training_executed": False, "new_neural_inference_executed": False,
        "new_sena_training_notebook_prepared": True, "production_threshold_selected": False,
        "repository_or_github_card_mutated": False})
    print("Prepared ordered notebook snapshot:", ROOT)


if __name__ == "__main__":
    main()
