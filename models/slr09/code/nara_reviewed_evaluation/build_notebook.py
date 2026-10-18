#!/usr/bin/env python3
"""Buat notebook lengkap dengan snapshot input review, tanpa menyisipkan bobot."""
import base64
import hashlib
import io
import json
from pathlib import Path
import textwrap
import zipfile


def main():
    root = Path(__file__).resolve().parent.parent
    payload = io.BytesIO()
    files = [p for p in (root/"data").iterdir() if p.is_file()]
    files += [root/"code"/name for name in ("validate_review.py", "nara_token_metrics.py", "evaluate_reviewed_nara.py", "write_report.py")]
    files += [root/"sources"/name for name in ("SLR09_NARA_Review_Uji_80_Reviewed.xlsx", "historical_test_original_labels.jsonl", "corpus_provenance.json", "input_provenance.json")]
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, p.relative_to(root).as_posix())
    raw = payload.getvalue()
    payload64 = base64.b64encode(raw).decode("ascii")
    cells = []
    def md(text):
        cells.append({"cell_type":"markdown", "id":f"md-{len(cells):04d}", "metadata":{}, "source":textwrap.dedent(text).strip()+"\n"})
    def code(text):
        source = textwrap.dedent(text).strip()+"\n"
        compile(source, "notebook-cell", "exec")
        cells.append({"cell_type":"code", "id":f"code-{len(cells):04d}", "metadata":{}, "source":source, "execution_count":None, "outputs":[]})
    md("""
    # SLR09 — Evaluasi NARA dengan acuan revisi

    Workflow: validasi snapshot Excel → gunakan hanya APPROVED lengkap → cocokkan prediksi run tetap → hitung metrik dan confusion matrix → ekspor hasil.

    Snapshot ini berisi **79 APPROVED / 1.701 token** dan **UJI-019 DEFERRED / 17 token**. Hasil adalah evaluasi parsial dari sampel 80, dengan status review tetap. Notebook tidak mengubah label, menjalankan training, memuat bobot, atau menjalankan inferensi neural baru. SENA dan tujuh field adapter tidak dievaluasi di notebook ini.

    Hasil yang telah dihitung dalam pemeriksaan: macro F1 non-O **53,43% → 79,32%**, F1 span tepat **43,69% → 63,84%**. Gunakan CPU; GPU tidak diperlukan. Run all dipakai untuk mereproduksi hasil.
    """)
    code('''
    import base64, hashlib, io, json, os, sys, zipfile
    from pathlib import Path, PurePosixPath

    EVAL_ROOT = Path(os.environ.get("SLR09_EVAL_ROOT", "/content/slr09_nara_eval_revised_v01" if Path("/content").is_dir() else "slr09_nara_eval_runtime")).resolve()
    PAYLOAD_B64 = "''' + payload64 + '''"
    PAYLOAD_SHA256 = "''' + hashlib.sha256(raw).hexdigest() + '''"
    raw = base64.b64decode(PAYLOAD_B64)
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Payload notebook berubah")
    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            relative = PurePosixPath(item.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Path snapshot tidak sah")
            destination = EVAL_ROOT.joinpath(*relative.parts)
            content = archive.read(item)
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError("Snapshot lokal berbeda; gunakan direktori SLR09_EVAL_ROOT yang baru: " + str(destination))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
    sys.path.insert(0, str(EVAL_ROOT / "code"))
    print("Snapshot input dan kode siap. Tidak ada bobot model dalam payload.")
    ''')
    md("""
    ## Sumber prediksi

    ZIP hasil run `20261018T001122_607337Z` sudah ada di folder Drive `SILAR_SLR09`. Hash arsip diperiksa sebelum evaluasi. Bila menjalankan dari paket kode lengkap di komputer lokal, file pada folder sources dipakai. Untuk lokasi lain, set environment `SLR09_RESULTS_ZIP` ke path ZIP tersebut.
    """)
    code('''
    REPORT_NAME = "SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip"
    configured = os.environ.get("SLR09_RESULTS_ZIP")
    local_source = Path.cwd() / "sources" / REPORT_NAME
    if configured:
        RESULTS_ZIP = Path(configured)
    elif local_source.is_file():
        RESULTS_ZIP = local_source
    else:
        try:
            from google.colab import drive
        except ImportError:
            raise FileNotFoundError("ZIP hasil diperlukan. Set SLR09_RESULTS_ZIP atau jalankan dari folder paket kode lengkap.")
        drive.mount("/content/drive")
        RESULTS_ZIP = Path("/content/drive/MyDrive/SILAR_SLR09") / REPORT_NAME
    if not RESULTS_ZIP.is_file():
        raise FileNotFoundError("ZIP hasil run belum ditemukan: " + str(RESULTS_ZIP))
    REVIEW_XLSX = EVAL_ROOT / "sources/SLR09_NARA_Review_Uji_80_Reviewed.xlsx"
    RESULT_DIR = EVAL_ROOT / "results"
    EVALUATION_SCOPE = "approved-subset"
    print("Scope:", EVALUATION_SCOPE, "— kasus DEFERRED tetap tidak diberi skor.")
    ''')
    md("""
    ## Validasi dan evaluasi

    Validator asli tetap menolak evaluasi penuh 80 selama ada DEFERRED. Analisis berikut secara eksplisit memakai subset APPROVED, bukan mengubah gate tersebut. Label sementara UJI-019 tidak dimasukkan.
    """)
    code('''
    from validate_review import validate_file
    from evaluate_reviewed_nara import evaluate, plot
    validation, _, _, _ = validate_file(REVIEW_XLSX, EVAL_ROOT / "data")
    print(json.dumps({k:validation[k] for k in ["ready_narratives", "deferred_narratives", "missing_labels", "invalid_labels", "ready_to_evaluate"]}, indent=2))
    result = evaluate(REVIEW_XLSX, EVAL_ROOT / "data", RESULTS_ZIP,
                      EVAL_ROOT / "sources/historical_test_original_labels.jsonl",
                      RESULT_DIR, scope=EVALUATION_SCOPE)
    plot(result, RESULT_DIR)
    print(json.dumps({"evaluation_scope":result["evaluation_scope"], "coverage":result["coverage"]}, indent=2))
    for model in ["baseline", "finetuned"]:
        print(model, json.dumps(result["metrics"][model]["reviewed_gold"]["token_metrics"], indent=2))
    ''')
    md("""
    ## Laporan, matriks, dan batas interpretasi

    Macro F1 menggunakan 14 label non-O yang tetap; O ikut memengaruhi false positive/negative. F1 span memerlukan batas dan label yang sama persis, bukan evaluasi BIO. Hasil WOUND memiliki dukungan sangat kecil. Test historis 1.000 narasi tetap dilaporkan dengan penurunannya; evaluasi parsial ini tidak menggantikan hasil tersebut.
    """)
    code('''
    from write_report import write_report
    REPORT_PATH = EVAL_ROOT / "SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md"
    write_report(result, REPORT_PATH, RESULT_DIR)
    try:
        from IPython.display import display, Markdown, Image
    except ImportError:
        print(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        display(Markdown(REPORT_PATH.read_text(encoding="utf-8")))
        for filename in ["baseline_confusion_matrix.png", "finetuned_confusion_matrix.png", "f1_per_label.png"]:
            display(Image(filename=str(RESULT_DIR / filename)))
    ''')
    md("""
    ## Ekspor hasil kecil

    Ekspor berisi metrik, cakupan 79/80, status satu kasus tertunda, acuan subset yang disetujui, rincian kesalahan, grafik, dan laporan. Tidak membuat gold penuh 80 atau mengubah workbook input.
    """)
    code('''
    import shutil
    from datetime import datetime, timezone
    name = "SLR09_NARA_Hasil_Evaluasi_Acuan_Revisi_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".zip"
    export_zip = EVAL_ROOT / name
    with zipfile.ZipFile(export_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(RESULT_DIR.rglob("*")):
            if file.is_file():
                archive.write(file, "results/" + file.relative_to(RESULT_DIR).as_posix())
        archive.write(REPORT_PATH, REPORT_PATH.name)
    try:
        from google.colab import files
    except ImportError:
        print("Hasil:", export_zip)
    else:
        drive_folder = Path("/content/drive/MyDrive/SILAR_SLR09")
        if drive_folder.is_dir():
            shutil.copyfile(export_zip, drive_folder / name)
        files.download(str(export_zip))
    ''')
    md("""
    ## Kode sumber lengkap

    Empat modul berikut juga ditampilkan sebagai teks yang dapat dibaca. Isinya sama dengan modul yang disimpan bootstrap di folder code. Paket ZIP menyediakan file Python terpisah beserta pembuat notebook dan pemeriksaan independen.
    """)
    for filename in ("validate_review.py", "nara_token_metrics.py", "evaluate_reviewed_nara.py", "write_report.py"):
        md("### " + filename + "\n\n```python\n" + (root/"code"/filename).read_text(encoding="utf-8") + "\n```")
    notebook = {"nbformat":4, "nbformat_minor":5, "metadata":{"kernelspec":{"display_name":"Python 3", "language":"python", "name":"python3"}, "language_info":{"name":"python"}}, "cells":cells}
    output = root / "SLR09_NARA_Evaluasi_Acuan_Revisi_v0.1.ipynb"
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    print(json.dumps({"notebook":output.name, "code_cells":sum(c["cell_type"]=="code" for c in cells), "payload_bytes":len(raw), "source_weights_embedded":False, "new_training_or_inference":False}, indent=2))


if __name__ == "__main__":
    main()
