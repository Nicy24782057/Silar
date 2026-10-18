#!/usr/bin/env python3
"""Laporan evaluasi dari angka aktual; tidak mengubah anotasi/prediksi."""
import csv
import json
from pathlib import Path


def pct(x):
    return f"{100*x:.2f}%".replace(".", ",")


def pp(x):
    return f"{100*x:+.2f}".replace(".", ",")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *["| " + " | ".join(str(v).replace("|", "\\|") for v in row) + " |" for row in rows]])


def write_report(result, output, results_dir):
    d, c = result, result["coverage"]
    b, f = (d["metrics"][m]["reviewed_gold"] for m in ("baseline", "finetuned"))
    old_b, old_f = (d["metrics"][m]["historical_gold_same_subset"] for m in ("baseline", "finetuned"))
    with (Path(results_dir) / "narrative_errors.csv").open(encoding="utf-8-sig") as stream:
        record_errors = list(csv.DictReader(stream))
    improved = sum(int(r["fewer_errors_after_finetune"]) > 0 for r in record_errors)
    regressed = sum(int(r["fewer_errors_after_finetune"]) < 0 for r in record_errors)
    same = len(record_errors) - improved - regressed
    lines = [
        "# SLR09 — Evaluasi NARA terhadap acuan revisi v0.1", "",
        "**Workflow:** validasi Excel → tentukan cakupan sesuai status review → cocokkan prediksi run tetap → hitung token/span dan matriks → analisis hasil.", "",
        f"**Status: {d['evaluation_scope']}.** Sampel awal {c['sample_narratives']} narasi/{c['sample_tokens']} token. "
        f"Yang dinilai: **{c['scored_narratives']} narasi/{c['scored_tokens']} token**, dengan {c['omitted_narratives']} narasi/{c['omitted_tokens']} token belum disetujui. "
        "Hasil ini tidak disebut sebagai evaluasi penuh 80 narasi.", "",
        "## Hasil utama", "",
        "Prediksi kandidat fine-tune lebih sesuai dengan acuan revisi pada subset yang disetujui. "
        f"Macro F1 non-O meningkat dari **{pct(b['token_metrics']['macro_f1_no_o'])} menjadi {pct(f['token_metrics']['macro_f1_no_o'])}**, "
        f"atau **{pp(f['token_metrics']['macro_f1_no_o']-b['token_metrics']['macro_f1_no_o'])} poin persentase**. "
        "Ini merupakan evaluasi ulang prediksi yang telah tersimpan, tanpa melatih model atau menjalankan inferensi neural baru.", "",
        table(["Metrik terhadap acuan revisi", "NARA v1", "Fine-tune", "Selisih (poin persentase)"], [
            *[[label, pct(b["token_metrics"][key]), pct(f["token_metrics"][key]), pp(f["token_metrics"][key]-b["token_metrics"][key])] for label, key in [("Akurasi token", "accuracy"), ("Precision macro non-O", "precision_macro_no_o"), ("Recall macro non-O", "recall_macro_no_o"), ("Macro F1 non-O", "macro_f1_no_o"), ("Micro F1 non-O", "micro_f1_no_o"), ("Weighted F1 non-O", "weighted_f1_no_o")]],
            ["F1 span tepat", pct(b["span_metrics"]["f1"]), pct(f["span_metrics"]["f1"]), pp(f["span_metrics"]["f1"]-b["span_metrics"]["f1"])],
        ]), "",
        "Macro F1 memakai seluruh 14 label non-O dengan bobot sama per label. Akurasi token memasukkan O. "
        "Kesalahan dari/ke O tetap memengaruhi precision dan recall role. F1 span menuntut label dan batas token tepat untuk span flat yang kontigu; format ini tidak dianggap BIO. "
        f"Semua {c['scored_tokens']} token sumber tercakup dan tidak ada narasi dinyatakan terpotong dalam metadata inferensi. "
        "Teks sumber yang memang berhenti di tengah kalimat tetap dinilai sebagaimana tertulis, terpisah dari truncation oleh batas input model.", "",
        "## Validasi review", "",
        f"Reviewer: **{d['reviewer']}**. Pada {c['sample_tokens']} token dalam Excel: "
        f"label kosong {d['validation_summary']['missing_labels']}, label tidak dikenal {d['validation_summary']['invalid_labels']}, "
        f"dan normalisasi huruf {d['validation_summary']['case_canonicalizations']}. "
        "ID, teks, token sumber, posisi token, dan daftar label cocok dengan paket uji terkunci. "
        "Workbook pengguna tidak diubah.", "",
        f"Dari {c['sample_narratives']} narasi, {c['scored_narratives']} berstatus APPROVED dan {c['omitted_narratives']} masih DEFERRED. "
        "Validator evaluasi penuh tetap menyatakan belum siap. Analisis ini membaca hanya acuan yang telah disetujui dan mencatat kasus yang tidak dinilai; "
        "tidak membuat gold penuh 80, tidak mengganti kasus dengan sampel lain, dan tidak mengubah DEFERRED menjadi APPROVED.", "",
        table(["ID review", "ID sumber", "Status", "Token", "Catatan reviewer"], [[r["review_id"], r["source_id"], r["status"], r["tokens"], r["review_note"]] for r in d["omitted_cases"]] or [["—", "—", "Semua selesai", 0, "—"]]), "",
    ]
    for r in d["omitted_cases"]:
        lines += ["> " + r["text"], "", "Label sementara kasus ini tidak dipakai untuk skor. Status DEFERRED dipertahankan sesuai file yang dikirim; belum ada keputusan pengguna yang mengubahnya.", ""]
    lines += [
        "Proporsi kelompok sumber pada subset yang dinilai: " + ", ".join(f"{k} {v}" for k, v in sorted(c["scored_source_groups"].items())) + ". "
        "Kelompok sumber adalah asal pengumpulan narasi, bukan kategori kejadian final SENA. "
        "Keputusan menunda kasus ambigu dapat memengaruhi karakter subset; cakupan dan pengecualiannya harus tetap dilaporkan.", "",
        "## Dampak perubahan anotasi pada narasi yang sama", "",
        "Untuk memeriksa pengaruh acuan, kedua prediksi tetap juga dinilai terhadap label historis pada **subset narasi yang sama**:", "",
        table(["Acuan pada subset yang sama", "Macro F1 NARA v1", "Macro F1 fine-tune"], [
            ["Historis", pct(old_b["token_metrics"]["macro_f1_no_o"]), pct(old_f["token_metrics"]["macro_f1_no_o"])],
            ["Review pedoman 0.2", pct(b["token_metrics"]["macro_f1_no_o"]), pct(f["token_metrics"]["macro_f1_no_o"])],
        ]), "",
        f"Review mengubah label **{d['historical_to_reviewed_tokens_changed']} dari {c['scored_tokens']} token** "
        f"({pct(d['historical_to_reviewed_tokens_changed']/c['scored_tokens'])}). "
        f"Proporsi non-O pada acuan naik dari {pct(old_b['token_metrics']['gold_non_o_rate'])} menjadi {pct(b['token_metrics']['gold_non_o_rate'])}. "
        "Perubahan ini membalik urutan performa dua model pada subset yang sama. Ini merupakan bukti langsung bahwa ketidakcocokan anotasi memengaruhi penilaian pada subset ini. "
        "Bukti tersebut tidak menetapkan bahwa seluruh penurunan pada test historis disebabkan oleh perubahan anotasi, dan tidak menghasilkan estimasi untuk 1.000 acuan revisi.", "",
        table(["Perubahan label historis → revisi", "Token"], [[r["old"] + " → " + r["new"], r["tokens"]] for r in d["historical_to_reviewed_change_pairs"][:8]]), "",
        "Test historis 1.000 narasi tetap memiliki macro F1 **" + pct(d["historical_test_1000_unchanged"]["baseline"]["macro_f1_no_o"]) + " → " + pct(d["historical_test_1000_unchanged"]["finetuned"]["macro_f1_no_o"]) + "**. "
        "Hasil historis tersebut tetap dipertahankan dalam pelaporan bersama hasil revisi; keduanya mengukur kesesuaian terhadap acuan yang berbeda.", "",
        "## Rincian per label", "",
        table(["Label", "Token acuan", "Narasi dengan label", "F1 NARA v1", "F1 fine-tune"], [[label, f["by_label"][label]["support"], d["gold_narrative_support"][label], pct(b["by_label"][label]["f1-score"]), pct(f["by_label"][label]["f1-score"])] for label in f["by_label"]]), "",
        "Dukungan setiap label dilaporkan pada tabel; denominator macro F1 tetap seluruh 14 non-O. "
        f"WOUND memiliki F1 {pct(f['by_label']['WOUNDVICTIM-ARG']['f1-score'])}, dengan dukungan "
        f"**{f['by_label']['WOUNDVICTIM-ARG']['support']} token pada {d['gold_narrative_support']['WOUNDVICTIM-ARG']} narasi**. "
        "Ini belum membuktikan penguasaan seluruh variasi luka/kondisi fisik dan tidak membatalkan kegagalan kasus sesak nafas pada validasi terdahulu. "
        "Label REASON masih lemah: F1 **" + pct(f["by_label"]["REASON-ARG"]["f1-score"]) + "**, dengan " + str(f["by_label"]["REASON-ARG"]["support"]) + " token acuan. "
        "INFORMATION memiliki F1 **" + pct(f["by_label"]["INFORMATION-ARG"]["f1-score"]) + "** dan FALSE-EVENT **" + pct(f["by_label"]["FALSE-EVENT"]["f1-score"]) + "**.", "",
        "## Kesalahan yang masih terlihat", "",
        f"Berdasarkan jumlah token salah per narasi: **{improved} membaik, {regressed} memburuk, dan {same} tetap**. "
        "Ukuran ini adalah perbandingan jumlah kesalahan token, bukan skor exact seluruh narasi.", "",
        table(["Acuan → prediksi fine-tune", "Token salah"], [[r["gold"] + " → " + r["prediction"], r["count"]] for r in f["top_confusions"][:8]]), "",
        "Pada INFORMATION, sebagian informasi masih hilang menjadi O dan sebagian token O justru diberi INFORMATION. "
        "Ini mendukung pemeriksaan batas frasa dan arti hasil ekstraksi pada integrasi berikutnya. "
        "Token berlabel INFORMATION tidak otomatis membuktikan nilai field impacts sudah benar.", "",
        f"{regressed} narasi dengan jumlah kesalahan token bertambah:", "",
        table(["ID review", "Token salah NARA v1", "Token salah fine-tune", "Catatan reviewer"], [[r["review_id"], r["baseline_wrong_tokens"], r["finetuned_wrong_tokens"], r["review_note"]] for r in record_errors if int(r["fewer_errors_after_finetune"]) < 0]), "",
        "## Batas kesimpulan dan langkah berikutnya", "",
        "1. Ini evaluasi parsial pada 79 narasi yang disetujui dari sampel test historis yang pernah dievaluasi. Tidak disebut test baru yang sepenuhnya belum pernah digunakan.",
        "2. Sampling ditetapkan tanpa prediksi, skor kesalahan, atau label role historis. Review disusun tanpa menampilkan label lama dan prediksi pada workbook.",
        "3. Data test NARA terpisah dari seluruh train/validation NARA asli dan tidak dipakai fine-tune/pemilihan epoch. Keterpisahan gabungan terhadap pelatihan SENA tidak dibuktikan oleh paket ini.",
        "4. Hasil adalah token dan span NARA. Tujuh field A4.22, SENA, fusion, foto, threshold, dan deployment tidak dievaluasi ulang di sini.",
        "5. Prediksi dibaca dari run Colab tetap. Pemeriksaan langsung bobot ekspor baru belum dilakukan; identitas bobot mengikuti manifest run yang hash arsip laporannya diverifikasi.",
        "6. Sampel kecil dan satu reviewer membatasi kesimpulan luas. Dukungan role langka harus dibaca bersama F1, terutama WOUND.", "",
        "Hasil ini mendukung kandidat fine-tune sebagai model yang lebih selaras dengan pedoman revisi pada subset tersebut. "
        "Status model produksi belum ditetapkan. Tahap selanjutnya yang disarankan adalah pemeriksaan integrasi kandidat NARA dengan adapter tujuh field, "
        "terutama batas impacts, pihak, waktu, dan penyebab, menggunakan artefak diagnostik yang telah tersedia. "
        "UJI-019 tetap terbuka sampai ada keputusan reviewer; hasil 80 narasi penuh baru dapat dihitung setelahnya.", "",
        "## Artefak dan reproduksi", "",
        "Notebook `SLR09_NARA_Evaluasi_Acuan_Revisi_v0.1.ipynb` berisi kode evaluasi lengkap. "
        "Notebook memakai snapshot Excel review dan data terkunci, lalu membaca ZIP hasil prediksi yang sudah ada di Drive. "
        "Tidak memerlukan bobot model atau GPU. Hasil pada folder results sudah dihitung dalam pemeriksaan ini; menjalankan notebook bersifat reproduksi.", "",
        "Paket kode lengkap menyertakan validator asli tanpa perubahan, metrik token/span, kode evaluasi dan laporan, snapshot input, "
        "provenance, tabel kesalahan, dua confusion matrix, grafik F1 per label, serta pemeriksaan independen metrik. "
        "Label review dan status dalam workbook unggahan dipertahankan byte-identik.", "",
        "SHA-256 Excel review: `" + d["review_source_sha256"] + "`.",
        "SHA-256 ZIP hasil run: `" + d["predictions_source"]["report_zip_sha256"] + "`.", "",
    ]
    Path(output).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    result = json.loads((base / "results/evaluation.json").read_text())
    output = base / "SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md"
    write_report(result, output, base / "results")
    print(output.name)
