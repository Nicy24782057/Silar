"""Update the existing SLR09 notebook package after the completed SENA run.

No training or neural inference. Existing notebook code and review data remain
unchanged; the update adds run evidence, analysis, and explicit user selection.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
from pathlib import Path

from analyze_sena_completed_run import RUN_ID, EXPECTED_ZIP_SHA256
from build_package import md, code, payload_cell, make_notebook


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def code_hash(nb):
    value = "\n\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    return hashlib.sha256(value.encode()).hexdigest()


def pct(value):
    return f"{value * 100:.2f}%".replace(".", ",")


def model_proposals(root, result):
    nara = json.loads((root / "evidence/nara_finetune/model_export_manifest.json").read_text())
    nara_run = json.loads((root / "evidence/nara_finetune/run_state.json").read_text())
    sena = result["model_export_manifest"]
    models = {
        "schema": "slr09-model-candidates-0.1", "status": "PROPOSED_FOR_SLR11_NOT_ACTIVATED",
        "production_model_selected": False, "threshold_selected": None,
        "quality_acceptance_approved": False,
        "sena": {"archive_name": sena["archive_name"], "archive_sha256": sena["archive_sha256"],
            "weights_sha256": sena["files_sha256"]["model.safetensors"],
            "run_id": RUN_ID, "labels": result["finetuned_metrics"]["labels"],
            "weight_identity_source": "COLAB_EXPORT_MANIFEST_NOT_DIRECT_WEIGHT_INSPECTION"},
        "nara": {"archive_name": Path(nara_run["model_archive_path"]).name,
            "archive_sha256": nara_run["model_archive_sha256"], "weights_sha256": nara["new_weights_sha256"],
            "run_id": nara["run_id"], "labels": nara["labels"],
            "weight_identity_source": "COLAB_EXPORT_MANIFEST_NOT_DIRECT_WEIGHT_INSPECTION"},
        "adapter_version": "silar-adapter-0.4.0", "victim_guard_version": "silar-victim-guard-0.4.0",
        "role_guideline_version": "nara-role-guideline-0.2", "fusion_version": "silar-fusion-a4.22-0.1.0",
        "target_vm_loading_and_joint_new_model_inference_verified": False,
        "general_extraction_conflict_detection_verified": False,
        "unchanged_rules": {"category_from_sena_only": True, "non_event_blocks_submission": True,
            "human_verification_always_required": True, "empty_fields_do_not_automatically_make_uncertain": True,
            "unknown_extracted_values_remain_null_or_empty_array": True},
    }
    options = {"schema": "slr09-confidence-cutoff-proposals-0.1", "selected_option": None,
        "activated": False, "purpose": "PROPOSED_INTEGRATION_PILOT_NOT_PRODUCTION_ACCEPTANCE",
        "recommended_option": "A", "reference_run_id": RUN_ID,
        "sena_weights_sha256": models["sena"]["weights_sha256"],
        "reference_report_sha256": EXPECTED_ZIP_SHA256,
        "reference_scope": "620_REVIEWED_VALIDATION_CHECKPOINT_SELECTION_NOT_INDEPENDENT_TEST",
        "options": [], "overall_model_accuracy_is_unchanged_by_cutoff": True,
        "note": "Flag when confidence < cutoff; equality is above. NON_EVENT still blocks; all reports need Human Verification."}
    for option, threshold in [("A", .95), ("B", .90)]:
        row = next(r for r in result["cutoff_comparison"] if r["threshold"] == threshold)
        options["options"].append({"option": option, "confidence_threshold": threshold,
            "low_confidence_flag_count": row["below_threshold_uncertain"],
            "low_confidence_flag_rate": row["flagged_rate"], "errors_flagged": row["errors_below_threshold"],
            "correct_predictions_also_flagged": row["correct_predictions_also_flagged"],
            "errors_remaining_at_or_above": row["errors_at_or_above"],
            "observed_accuracy_at_or_above": row["accuracy_at_or_above"],
            "calibration_reference": f"SLR09_SENA_{RUN_ID}:reviewed_validation620:cutoff_{threshold:.2f}",
            "activated": False})
    decision_path = root / "config/threshold_decision.json"
    if decision_path.exists():
        decision = json.loads(decision_path.read_text())
        if (decision.get("decision_source") != "EXPLICIT_USER_INSTRUCTION"
                or decision.get("scope") != "CANDIDATE_INTEGRATION_CONFIGURATION"
                or decision.get("reference_run_id") != RUN_ID
                or decision.get("sena_weights_sha256") != models["sena"]["weights_sha256"]
                or decision.get("reference_report_sha256") != EXPECTED_ZIP_SHA256
                or decision.get("production_deployment_authorized") is not False
                or decision.get("quality_acceptance_approved") is not False):
            raise ValueError("Threshold decision has an incompatible identity or scope")
        selected = next((row for row in options["options"]
                         if row["option"] == decision.get("selected_option")
                         and row["confidence_threshold"] == decision.get("confidence_threshold")), None)
        if selected is None:
            raise ValueError("Threshold decision does not match an evaluated option")
        options.update({"selected_option": selected["option"],
            "confidence_threshold": selected["confidence_threshold"],
            "calibration_reference": selected["calibration_reference"],
            "selection_status": "USER_SELECTED_FOR_INTEGRATION",
            "decision_file": "config/threshold_decision.json",
            "purpose": "SELECTED_CANDIDATE_INTEGRATION_NOT_PRODUCTION_ACCEPTANCE",
            "activated_means": "DEPLOYED_TO_APPLICATION; FALSE_DOES_NOT_MEAN_UNSELECTED"})
        for row in options["options"]:
            row["selected"] = row["option"] == selected["option"]
        models.update({"status": "CONFIGURED_FOR_SLR11_NOT_DEPLOYED",
            "threshold_selected": selected["confidence_threshold"],
            "threshold_option": selected["option"],
            "threshold_configuration": "config/SLR09_Konfigurasi_Integrasi_v0.1.json"})
        integration = {"schema": "slr09-integration-configuration-0.1",
            "status": "USER_SELECTED_FOR_INTEGRATION", "selected_option": selected["option"],
            "confidence_threshold": selected["confidence_threshold"],
            "calibration_reference": selected["calibration_reference"],
            "decision_file": "config/threshold_decision.json",
            "low_confidence_rule": "confidence < confidence_threshold",
            "equal_to_threshold_is_low_confidence": False,
            "reference_run_id": RUN_ID, "reference_report_sha256": EXPECTED_ZIP_SHA256,
            "reference_scope": options["reference_scope"],
            "probability_calibration_fitted": False,
            "selection_basis": "OBSERVED_VALIDATION_TRADEOFF_AND_EXPLICIT_USER_DECISION",
            "sena": models["sena"], "nara": models["nara"],
            "adapter_version": models["adapter_version"], "fusion_version": models["fusion_version"],
            "victim_guard_version": models["victim_guard_version"],
            "role_guideline_version": models["role_guideline_version"],
            "rules": models["unchanged_rules"],
            "production_deployed": False, "production_model_selected": False,
            "quality_acceptance_approved": False,
            "target_vm_loading_and_joint_new_model_inference_verified": False,
            "general_extraction_conflict_detection_verified": False}
        dump(root / "config/SLR09_Konfigurasi_Integrasi_v0.1.json", integration)
    dump(root / "config/model_candidates.json", models)
    dump(root / "config/threshold_options.json", options)
    return models, options


def update_report(root, result, models, options):
    baseline = result["baseline_metrics"]; fine = result["finetuned_metrics"]
    selected = options["selected_option"] is not None
    selection_status = (f"Pengguna telah memilih **{options['selected_option']} (cutoff {str(options['confidence_threshold']).replace('.', ',')})** untuk konfigurasi kandidat integrasi. Parameter tersimpan dan terikat pada identitas SENA hasil evaluasi; konfigurasi belum diterapkan pada aplikasi."
        if selected else "Threshold belum dipilih atau diaktifkan.")
    rows = "\n".join(f"| {label} | {v['support']} | {pct(baseline['per_class'][label]['f1'])} | {pct(v['f1'])} |" for label, v in fine["per_class"].items())
    cuts = "\n".join(f"| {r['threshold']:.2f} | {r['below_threshold_uncertain']} ({pct(r['flagged_rate'])}) | {r['errors_below_threshold']}/74 | {r['errors_at_or_above']} | {pct(r['accuracy_at_or_above'])} |" for r in result["cutoff_comparison"] if r["threshold"] in [.90, .95, .99])
    cuts = re.sub(r"\| 0\.(\d+) \|", r"| 0,\1 |", cuts)
    report = f'''# SLR09 - Rekap notebook dan kesiapan aset v0.1

**Revisi setelah hasil fine-tuning SENA dan keputusan threshold - 18 Oktober 2026.**

**Workflow:** gunakan hasil training yang sudah selesai -> catat pilihan cutoff pengguna -> periksa kontrak konfigurasi Fusion -> gunakan paket untuk SLR11.

## Status saat ini

Pelatihan/fine-tuning NARA dan SENA telah selesai menurut dua laporan Colab yang diterima. Analisis saat ini memakai prediksi tersimpan; tidak menjalankan training atau inferensi baru. Hasil NARA sebelumnya dipertahankan. Paket berisi seluruh notebook sumber, notebook fine-tuning, metrik, confusion matrix, kurva, data review dan kode lengkap.

Model baru disajikan sebagai **kandidat integrasi**, belum dipromosikan menjadi model produksi. {selection_status} Acuan Teknis, PRD, anotasi, status TUNDA/DEFERRED dan model aktif proyek lama tidak diubah.

## SENA: hasil run yang sudah selesai

Run {RUN_ID}; PREPARE/FINE_TUNE/EVALUATE/EXPORT berstatus SUCCEEDED. Menggunakan 110 train dan 620 validation hasil review, GPU Tesla T4, Transformers 4.57.1. Training berlangsung 6 epoch/42 optimizer steps; checkpoint terbaik adalah step 28 pada **epoch 4**, bukan checkpoint epoch terakhir. Early stopping berhenti setelah dua epoch tanpa peningkatan macro F1. Waktu training tercatat 68,427 detik, bukan benchmark backend atau VM tujuan.

| Metrik pada 620 validation yang sama | SENA v1 | Fine-tune |
| --- | --- | --- |
| Accuracy | {pct(baseline['accuracy'])} | {pct(fine['accuracy'])} |
| Macro F1 lima kelas | {pct(baseline['macro_f1_all_five_classes'])} | {pct(fine['macro_f1_all_five_classes'])} |
| Weighted F1 | {pct(baseline['weighted_f1'])} | {pct(fine['weighted_f1'])} |
| Prediksi sesuai acuan | 397/620 | 546/620 |
| Kejadian diprediksi NON_EVENT | 213/489 | 28/489 |
| NON_EVENT diprediksi kejadian | 10/131 | 45/131 |
| Salah kategori antarjenis kejadian | 0 | 1 |

Accuracy meningkat 24,03 poin persentase dan macro F1 meningkat 22,32 poin persentase. Pada pasangan narasi yang sama: **184 membaik, 35 memburuk, 362 tetap benar, 39 tetap salah**. Jumlah kesalahan total turun 223 menjadi 74. Kenaikan false event tetap merupakan regresi penting, bukan hasil yang dihapus demi skor total.

| Kategori | Jumlah acuan | F1 SENA v1 | F1 fine-tune |
| --- | --- | --- | --- |
{rows}

Model lebih banyak mengenali kejadian yang dirujuk dalam berita, bantuan atau komentar. NON_EVENT masih menjadi batas lemah, dengan F1 {pct(fine['per_class']['NON_EVENT']['f1'])}. Contoh false event yang tetap dipertahankan sesuai review: KEC-01395 (statistik kecelakaan mudik), KEB-00598 (edukasi penyebab/penanggulangan kebakaran), BAN-01074 (pencegahan), dan GEM-01398 (lelucon umum). KEC-00351 masih salah NON_EVENT pada komentar yang merujuk kecelakaan tertentu. GEM-01229 salah memilih EARTHQUAKE saat acuan menetapkan ACCIDENT sebagai kejadian utama.

Keterangan contoh merupakan penelaahan terhadap label final yang sudah ada; tidak membuat anotasi baru atau mengubah kategori agar sesuai prediksi. Seluruh 74 kesalahan beserta confidence tersimpan pada results/sena_finetune_{RUN_ID}/classification_errors.json; perubahan seluruh 620 prediksi ada pada prediction_transitions.csv.

**Batas metrik:** 620 narasi merupakan validation yang digunakan memilih checkpoint. Ini bukan test independen. Kandidat split historis SENA belum terbukti bebas dari training checkpoint awal. Tiga validation TUNDA tetap dikeluarkan. Test resmi tidak digunakan dalam fine-tune ini, dan tidak ada klaim skor test baru. Baseline memakai prediksi yang sudah selesai; inferensi baseline tidak diulang.

## Cutoff confidence kandidat integrasi

{selection_status}

| Cutoff | Ditandai confidence rendah | Kesalahan yang ditandai | Kesalahan masih di kelompok atas | Accuracy teramati pada kelompok atas |
| --- | --- | --- | --- | --- |
{cuts}

Angka kelompok atas bersifat kondisional pada validation yang sama. Memilih cutoff tidak mengubah accuracy keseluruhan 88,06% atau memperbaiki 74 label yang salah. Kebenaran suatu prediksi tidak dijamin oleh confidence, dan 0,95 tidak berarti model pasti benar 95%.

**A. Cutoff 0,95 - dipilih pengguna untuk kandidat integrasi.** Menandai 153/620 narasi, mencakup 51/74 kesalahan dan menyisakan 23 kesalahan pada kelompok atas. Sebanyak 102 prediksi yang sebenarnya sesuai acuan ikut mendapat tanda. Kelebihannya lebih banyak kesalahan mendapat perhatian; konsekuensinya tanda uncertain lebih sering muncul. Tambahan 51 tanda dibanding 0,90 mencakup 13 kesalahan tambahan; ini pilihan pertukaran pada hasil yang terlihat, bukan optimasi atau jaminan pada data baru.

**B. Cutoff 0,90.** Menandai 102/620 narasi, mencakup 38/74 kesalahan, dan menyisakan 36 kesalahan pada kelompok atas. Sebanyak 64 prediksi yang benar ikut ditandai. Tanda lebih sedikit, dengan lebih banyak kesalahan ber-confidence tinggi tersisa.

Cutoff 0,99 disertakan sebagai pembanding: 437/620 ditandai (70,48%), mencakup 72/74 kesalahan tetapi juga 365 prediksi benar. Proporsi tanda yang besar menjadi alasan tidak menempatkannya sebagai rekomendasi awal.

Perhitungan tanda di tabel hanya LOW_CLASSIFICATION_CONFIDENCE. Kemampuan mendeteksi konflik ekstraksi umum tidak diklaim. Aturan tetap: confidence **di bawah** cutoff diberi tanda; nilai sama dengan cutoff berada pada kelompok atas. **Semua** prediksi NON_EVENT tetap memblokir pengiriman, termasuk yang ber-confidence rendah. Semua laporan tetap membutuhkan Human Verification. Tanda uncertain tidak mengubah kategori atau mempublikasikan laporan otomatis.

File config/threshold_decision.json menyimpan instruksi pengguna, dan config/threshold_options.json mencatat selected_option={options['selected_option']} serta perbandingan opsi. activated=false berarti belum diterapkan pada aplikasi, bukan berarti pilihan belum dicatat. File **config/SLR09_Konfigurasi_Integrasi_v0.1.json** menyediakan confidence_threshold={options.get('confidence_threshold')} dan calibration_reference yang terikat pada run, hash bobot serta laporan SENA. Builder membaca keputusan ini sehingga pembaruan paket tidak mengembalikan pilihan menjadi null.

calibration_reference adalah rujukan pengukuran, bukan bukti kalibrasi probabilitas. Pemilihan cutoff tidak melakukan temperature scaling atau metode kalibrasi baru. Tidak ada target mutu numerik baru yang dibuat seolah-olah disepakati sebelum melihat skor. Penerimaan kandidat beserta batas metrik masih memerlukan review kelompok.

## Pemeriksaan kontrak konfigurasi Fusion

code/verify_selected_fusion_config.py memakai fixture buatan untuk memeriksa batas 0,949, 0,950 dan 0,951, blokir NON_EVENT, kategori dari SENA, serta guard konfigurasi tanpa threshold/referensi. Field kosong saja tidak membuat uncertain. Kewajiban Human Verification dipertahankan dalam konfigurasi; penerapannya oleh backend belum dibuktikan oleh pemeriksaan fungsi ini.

Hasil pemeriksaan terdapat pada evidence/selected_threshold_contract_checks.json. Ini pemeriksaan aturan dan konsistensi konfigurasi, bukan inferensi model atau tambahan skor evaluasi neural. Tidak ada training, pengujian ulang NARA, atau inferensi SENA yang diulang.

## NARA dan adapter: hasil yang dipakai kembali

| Bagian | Hasil | Cakupan |
| --- | --- | --- |
| Fine-tune NARA | 157 train/41 validation; validation macro F1 78,65% | Validation memilih checkpoint; bukan test independen. |
| Evaluasi acuan revisi | Macro F1 non-O 53,43% -> 79,32%; exact span F1 43,69% -> 63,84% | 79 narasi/1.701 token; UJI-019 DEFERRED. |
| Test historis | Macro F1 67,77% -> 58,56% | 1.000 narasi dengan label historis; hasil tetap dicatat. |
| Tujuh field A4.22 | 66/84 -> 73/84 cocok; 13 membaik, 6 memburuk | 12 diagnostik dikenal, nilai kosong ikut dihitung. |

Regresi NARA tetap dicatat: time_text 12/12 -> 10/12 dan impacts 6/12 -> 5/12. INFORMATION, batas frasa waktu, lokasi/objek dan kasus sesak nafas masih mempunyai keterbatasan. WOUND F1 100% pada subset 79 hanya didukung lima token pada dua narasi. Seluruh occurred_at diagnostik null; kecocokannya tidak membuktikan parser tanggal berisi.

Tidak ada replay adapter, evaluasi NARA, training NARA atau perubahan aturan baru pada pembaruan ini. Hasil berasal dari artefak yang telah diperiksa. Raw NARA tetap 15 label flat; kategori final dari SENA. Skema ekstraksi tetap location_text, time_text, occurred_at, involved_parties, impacts, victims, affected_objects. REASON tidak dijadikan field produk baru. Informasi tak ditemukan tetap null atau array kosong.

## Identitas kandidat dan batas pemeriksaan bobot

| Komponen | Kandidat/versi |
| --- | --- |
| SENA | {models['sena']['archive_name']} |
| NARA | {models['nara']['archive_name']} |
| Adapter | silar-adapter-0.4.0 |
| Guard korban | silar-victim-guard-0.4.0 |
| Pedoman NARA | nara-role-guideline-0.2 |
| Aturan Fusion | silar-fusion-a4.22-0.1.0 |

SHA bobot SENA: {models['sena']['weights_sha256']}. SHA bobot NARA: {models['nara']['weights_sha256']}. Identitas mengikuti manifest ekspor Colab; bobot besar tidak dibuka langsung pada pemeriksaan ini. Reload SENA pada tiga contoh dilaporkan cocok oleh run Colab. Perbandingan kinerja tujuh field untuk gabungan kedua model baru belum dijalankan; angka 73/84 sebelumnya memakai SENA lama yang tetap sebagai komponen diagnostik.

config/model_candidates.json menyimpan label, versi, hash dan status {models['status']}. Parameter pilihan tersedia untuk pemanggilan Fusion pada tahap integrasi. Pemilihan threshold tidak mengubah status model produksi, persetujuan mutu, atau bukti pemuatan pada VM tujuan.

## Kesiapan terhadap card SLR09

| Bagian | Status dan bukti |
| --- | --- |
| Aset/provenance/label | Sumber, label dan hash tersedia; bukti bobot baru mengikuti manifest Colab. |
| Data/anotasi/preprocessing/split | Data review dan kode tersedia; NARA memiliki ID split; keterbatasan split historis SENA dicatat. |
| Pelatihan dan evaluasi | Kedua fine-tune selesai. Metrik, kurva, matriks dan contoh kesalahan tersedia, dengan pemisahan validation/test. |
| Pemetaan NARA/adapter A4.22 | Kode dan hasil diagnostik tersedia; seluruh regresi dan batas cakupan tetap dilaporkan. |
| Target mutu dan penerimaan | Belum ada angka penerimaan final yang disepakati; kandidat dan tradeoff siap ditinjau kelompok. |
| Threshold/ambiguity | A (0,95) dikunci untuk kandidat integrasi; kontrak batas dan guard diperiksa. Belum diterapkan pada aplikasi. Deteksi konflik umum tidak diklaim. |
| Kesiapan pemuatan | Baseline telah berjalan di CPU notebook; reload kandidat dilaporkan di T4. Belum bukti pemuatan/joint inference kedua kandidat pada VM tujuan. |
| Versioning/commit | Paket, versi dan hash siap. Commit/LFS serta review penerimaan kelompok belum dilakukan di sini. |

**Usulan status: In Review untuk meninjau hasil dan konfigurasi kandidat; belum menandai Done.** Ini usulan dokumentasi, bukan perubahan card GitHub. Kriteria yang masih terbuka berasal dari card asli, bukan penambahan fitur atau kewajiban baru. Integrasi backend dan benchmark sistem penuh tetap berada pada SLR11/SLR15; kesiapan aset pada lingkungan tujuan tetap perlu dibuktikan sesuai ruang lingkupnya.

## Urutan artefak dan notebook

Urutan dokumen proyek tetap laporan perancangan -> hasil revisi -> penyempurnaan Acuan Teknis SLR04/desain 0.3 -> pemetaan MEET05. PRD tidak direvisi oleh pekerjaan ini. Notebook bernomor menyatakan alur ketergantungan, bukan tanggal pasti seluruh eksperimen historis.

| Notebook | Fungsi dan keadaan |
| --- | --- |
| 00_SLR09_Hasil_Terverifikasi.ipynb | Ringkasan terkini kedua model, adapter dan cutoff terpilih; membaca hasil tersimpan. |
| 01_SENA_Pelatihan_Awal.ipynb | Kode V3A utuh; sumber asli tidak menyimpan output training. |
| 02_NARA_Pelatihan_Awal.ipynb | Kode V2 utuh beserta output historis sumber. |
| 03_NARA_FineTune_dan_Evaluasi.ipynb | Kode eksperimen NARA yang telah selesai. |
| 04_NARA_Evaluasi_Acuan_Revisi.ipynb | Kode evaluasi 79 narasi yang telah selesai. |
| 05_SILAR_Inferensi_Baseline_dan_Kalibrasi.ipynb | Dokumentasi runner baseline lama, bukan runner gabungan kandidat baru. |
| 06_SENA_Evaluasi_620_Review.ipynb | Analisis SENA v1 pada seluruh review final. |
| 07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb | Kode fine-tune yang run-nya sudah diterima; hasil run dicantumkan terpisah dari sel training sumber. |
| 08_SENA_Analisis_Hasil_dan_Threshold.ipynb | Analisis hasil SENA baru, transisi kesalahan dan cutoff; tanpa model. |

**Seluruh hasil pada tahap ini sudah tersedia. Notebook 01-07 tidak perlu dijalankan ulang.** Kode sel sumber dipertahankan; nama historis TanggapMakna menunjukkan asal, sedangkan notebook utama memakai SENA/NARA. historical/ menyimpan feasibility, local evaluation dan Fusion/blind lama. Completeness Engine atau aturan status historis tidak diaktifkan menjadi fitur SILAR.

## Sumber/lisensi dan reproduksi

Dataset Semantic Role Labeling Datasets for Crisis Event, Ariyanto dkk., halaman Mendeley V2 DOI 10.17632/r76v5sjyv2.2 menyatakan CC BY 4.0. Model card indolem/indobert-base-uncased menyatakan MIT. Pemeriksaan sumber resmi tercatat 18 Oktober 2026. Identitas byte dataset mengikuti asset_lock, bukan asumsi kesamaan arsip terhadap versi halaman publik. Tidak menetapkan lisensi baru untuk proyek.

- https://data.mendeley.com/datasets/r76v5sjyv2/2
- https://huggingface.co/indolem/indobert-base-uncased

ZIP laporan SENA yang diterima tersimpan byte-identik di sources/. SHA-256: {EXPECTED_ZIP_SHA256}. code/analyze_sena_completed_run.py mereproduksi analisis dari prediksi tersebut; field confidence_threshold_selected=null di snapshot analisis mencerminkan keadaan sebelum keputusan pengguna. Konfigurasi terkini dibaca dari config/, tanpa menimpa catatan hasil run lama. code/update_package_after_sena.py memperbarui ringkasan tanpa model. code/verify_selected_fusion_config.py memeriksa konfigurasi terpilih. code/qa_package.py memeriksa notebook/snapshot; code/finalize_package.py membuat ZIP dan memverifikasi isi/hash. Kode builder tahap persiapan tetap ada sebagai riwayat dan meneruskan pembaruan jika sumber run selesai tersedia. Bobot besar tetap mengikuti arsip Drive yang sudah ada; tidak diperlukan unggah ulang untuk analisis ini.
'''
    report_path = root / "SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md"
    historical = root / "docs/SLR09_Rekap_Sebelum_Hasil_SENA_v0.1.md"
    if not historical.exists(): shutil.copyfile(report_path, historical)
    report_path.write_text(report, encoding="utf-8")
    (root / "README.md").write_text('''# SLR09 - Paket notebook dan rekap v0.1

**Pembaruan sesudah pilihan pengguna A (0,95), 18 Oktober 2026.**

**Workflow:** baca rekap -> buka notebook 00/08 -> gunakan konfigurasi A (0,95) -> lanjutkan tahap integrasi dengan hasil yang sudah tersedia.

Pelatihan NARA dan SENA sudah selesai menurut laporan Colab. Seluruh notebook 01-07 menjadi lampiran kode; tidak perlu Run all kembali. Notebook 00/08 membaca hasil tersimpan tanpa model. Tidak ada training atau inferensi baru pada pembaruan ini.

| Lokasi | Isi |
| --- | --- |
| SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md | Hasil terkini, batas metrik, status card dan pilihan threshold. |
| notebooks/ | Sembilan notebook 00-08: dari pelatihan awal hingga analisis hasil. |
| config/model_candidates.json | Identitas kandidat SENA/NARA dan adapter; belum aktif. |
| config/SLR09_Konfigurasi_Integrasi_v0.1.json | Parameter Fusion pilihan A (0,95), identitas kandidat, dan aturan wajib. |
| config/threshold_decision.json dan config/threshold_options.json | Keputusan eksplisit pengguna dan perbandingan cutoff. |
| evidence/selected_threshold_contract_checks.json | Pemeriksaan batas/guard Fusion tanpa model; bukan skor neural. |
| code/ | Kode utuh pelatihan, analisis, adapter, pembaruan dan pemeriksaan. |
| results/sena_finetune_20261018T044447_926664Z/ | Hasil run asli serta transisi kesalahan/cutoff tambahan. |
| results/nara_reviewed_79/ dan results/nara_adapter_12/ | Hasil NARA yang dipakai kembali. |
| sources/ | Sumber notebook, review, acuan dan ZIP laporan. |
| historical/ dan docs/ | Riwayat eksperimen dan laporan terdahulu. |

Model besar tetap di Drive. Threshold A (0,95) telah dipilih untuk kandidat integrasi, belum diterapkan pada aplikasi. NON_EVENT tetap memblokir pengiriman dan Human Verification tetap wajib. Instruksi pemilihan threshold tidak menetapkan penerimaan mutu akhir atau promosi produksi.

Reproduksi analisis (opsional, tanpa model): python code/analyze_sena_completed_run.py
Pembaruan artefak: python code/update_package_after_sena.py
Pemeriksaan konfigurasi terpilih: python code/verify_selected_fusion_config.py
Pemeriksaan sumber/snapshot notebook: python code/qa_package.py
Pembuatan ZIP sesudah QA: python code/finalize_package.py

Nama sumber TanggapMakna dipertahankan untuk provenance. Notebook 05 khusus baseline historis; kode adapter aktif 0.4 ada pada code/active_nara_adapter. Kode training 07 tidak diubah oleh pembaruan hasil.
''', encoding="utf-8")


def attach_image(cells, path, title):
    raw = path.read_bytes(); name = path.name
    cell = md(f"## {title}\n\n![{title}](attachment:{name})\n")
    cell["attachments"] = {name: {"image/png": base64.b64encode(raw).decode()}}
    cells.append(cell)


def update_notebooks(root, result):
    saved = root / "results" / ("sena_finetune_" + RUN_ID)
    cached = {"cached/sena_completed.json": (saved / "completed_run_analysis.json").read_bytes(),
        "cached/nara_evaluation.json": (root / "results/nara_reviewed_79/evaluation.json").read_bytes(),
        "cached/adapter_fields.csv": (root / "results/nara_adapter_12/perubahan_84_field.csv").read_bytes(),
        "cached/integration_config.json": (root / "config/SLR09_Konfigurasi_Integrasi_v0.1.json").read_bytes(),
        "cached/threshold_contract_checks.json": (root / "evidence/selected_threshold_contract_checks.json").read_bytes()}
    cells = [md("# SLR09 - Hasil terverifikasi\n\n**Workflow:** baca hasil tersimpan -> tinjau konfigurasi A (0,95) -> lanjutkan ke integrasi.\n\nFine-tuning kedua model selesai menurut laporan Colab. Sel ini tidak memuat model atau mengulang training/inferensi. Semua metrik SENA adalah validation, sedangkan NARA memakai cakupan evaluasi yang dijelaskan. Threshold dipilih pengguna setelah analisis selesai; konfigurasi terkini dibaca terpisah dari snapshot analisis historis.\n"),
        payload_cell(cached, "/content/slr09_hasil_terverifikasi"),
        code('''sena = json.loads((WORK_ROOT / "cached/sena_completed.json").read_text())
nara = json.loads((WORK_ROOT / "cached/nara_evaluation.json").read_text())
for label, metric in [("SENA v1", sena["baseline_metrics"]), ("SENA fine-tune", sena["finetuned_metrics"])]:
    print(label, "accuracy:", f"{100*metric['accuracy']:.2f}%", "macro F1:", f"{100*metric['macro_f1_all_five_classes']:.2f}%")
print("Perubahan prediksi:", sena["prediction_changes"])
print("Best checkpoint: epoch", sena["best_epoch"], "step", sena["best_step"])
for model in ["baseline", "finetuned"]:
    print("NARA", model, "macro F1 non-O:", nara["metrics"][model]["reviewed_gold"]["token_metrics"]["macro_f1_no_o"])
print("Cakupan NARA:", nara["coverage"]["scored_narratives"], "narasi")
'''),
        md("## Cutoff terpilih: A (0,95)\n\nPilihan pengguna berlaku untuk kandidat integrasi. Di bawah cutoff berarti confidence rendah; sama dengan cutoff tidak mendapat tanda tersebut. NON_EVENT tetap memblokir; Human Verification tetap wajib. Accuracy kelompok atas bukan accuracy keseluruhan. Konfigurasi belum diterapkan pada aplikasi.\n"),
        code('''for row in sena["cutoff_comparison"]:
    if row["threshold"] in [0.9, 0.95, 0.99]:
        print("Cutoff", row["threshold"], "ditandai:", row["below_threshold_uncertain"], "kesalahan ditandai:", row["errors_below_threshold"], "kesalahan kelompok atas:", row["errors_at_or_above"])
print("Rekomendasi usulan:", sena["proposed_recommended_cutoff"])
integration = json.loads((WORK_ROOT / "cached/integration_config.json").read_text())
contract_checks = json.loads((WORK_ROOT / "cached/threshold_contract_checks.json").read_text())
print("Pilihan pengguna:", integration["selected_option"], "threshold:", integration["confidence_threshold"])
print("Aturan:", integration["low_confidence_rule"])
print("Referensi:", integration["calibration_reference"])
print("Kontrak konfigurasi:", len(contract_checks["checks"]), "pemeriksaan lulus:", contract_checks["all_passed"])
print("Fixture buatan; bukan evaluasi neural.")
print("Diterapkan pada aplikasi:", integration["production_deployed"])
'''),
        md("## Adapter yang sudah diperiksa\n\nCSV di bawah berasal dari audit run NARA terdahulu, tanpa menjalankan adapter lagi.\n"),
        code('''import csv
with (WORK_ROOT / "cached/adapter_fields.csv").open(encoding="utf-8-sig") as stream:
    fields = list(csv.DictReader(stream))
print("Baseline:", sum(r["baseline_correct"] == "True" for r in fields), "/", len(fields))
print("Fine-tune:", sum(r["finetuned_correct"] == "True" for r in fields), "/", len(fields))
print("Nilai kosong ikut dihitung; 12 diagnostik dikenal.")
print("Tidak ada training atau inferensi baru pada pembaruan ini.")
''')]
    attach_image(cells, saved / "confusion_matrix.png", "Confusion matrix SENA dari run Colab")
    attach_image(cells, saved / "training_curves.png", "Kurva training SENA dari run Colab")
    dump(root / "notebooks/00_SLR09_Hasil_Terverifikasi.ipynb", make_notebook(cells, "00_SLR09_Hasil_Terverifikasi.ipynb"))

    # Training code is preserved, with actual external results documented in Markdown.
    training_path = root / "notebooks/07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb"
    original_path = root / "sources/notebooks_original/07_SENA_FineTune_dan_Evaluasi_v0.1_pre_run.ipynb"
    if not original_path.exists(): shutil.copyfile(training_path, original_path)
    notebook = json.loads(training_path.read_text())
    original = json.loads(original_path.read_text())
    metric = result["finetuned_metrics"]
    notebook["cells"][0]["source"] = md(f'''# SLR09 - Fine-tune SENA dan evaluasi v0.1

**Workflow:** baca hasil run yang sudah selesai -> telusuri kode/data pelatihan -> jalankan hanya bila membutuhkan eksperimen baru.

**Run {RUN_ID} sudah diterima dan berstatus SUCCEEDED. Tidak perlu Run all kembali.**
110 train/620 validation; training berhenti pada epoch 6; checkpoint terbaik epoch 4/step 28.
Accuracy validation {pct(metric['accuracy'])}; macro F1 {pct(metric['macro_f1_all_five_classes'])}; salah NON_EVENT 28 dan false event 45.

Hasil berasal dari ZIP laporan Colab yang disimpan pada sources/. Sel training sumber di bawah dipertahankan utuh dan tidak diberi output eksekusi buatan. Laporan ini bukan klaim bahwa training dijalankan di lingkungan penyusunan paket. Validation dipakai memilih checkpoint dan bukan test independen. Sel berikut masih merupakan kode reproduksi yang akan melatih lagi jika dijalankan.
''')["source"]
    assert code_hash(notebook) == code_hash(original)
    notebook.setdefault("metadata", {})["completed_external_run"] = {"run_id": RUN_ID, "status": "SUCCEEDED",
        "source_report_sha256": EXPECTED_ZIP_SHA256, "training_code_changed": False,
        "local_training_cell_execution_claimed": False}
    dump(training_path, notebook)
    dump(root / "evidence/sena_training_source_unchanged.json", {"source": original_path.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        "code_cells_sha256": code_hash(original), "updated_code_cells_sha256": code_hash(notebook),
        "all_training_code_cells_unchanged": True, "external_run_id": RUN_ID})

    # The additional analysis notebook reads the finished result, not a model.
    cells = [md("# SENA - Analisis hasil fine-tuning dan threshold terpilih\n\n**Workflow:** baca snapshot hasil -> bandingkan kesalahan -> baca keputusan A (0,95) -> tinjau pemeriksaan konfigurasi.\n\nPengguna memilih A (0,95). Hasil metrik berasal dari prediksi tersimpan; pemeriksaan Fusion memakai fixture buatan tanpa model. Tidak ada training, inferensi atau perubahan gold. Snapshot analisis lama tetap menyimpan keadaan sebelum pemilihan; konfigurasi terkini tersedia terpisah.\n"),
        payload_cell({name: cached[name] for name in ["cached/sena_completed.json", "cached/integration_config.json",
            "cached/threshold_contract_checks.json"]}, "/content/slr09_sena_completed_analysis"),
        code('''analysis = json.loads((WORK_ROOT / "cached/sena_completed.json").read_text())
print("Run:", analysis["run_id"])
print("Baseline:", analysis["baseline_metrics"]["macro_f1_all_five_classes"])
print("Fine-tune:", analysis["finetuned_metrics"]["macro_f1_all_five_classes"])
print("Perubahan:", analysis["prediction_changes"])
for row in analysis["cutoff_comparison"]:
    if row["threshold"] in [.9, .95, .99]:
        print("Cutoff", row["threshold"], "flag", row["below_threshold_uncertain"], "error flagged", row["errors_below_threshold"], "error above", row["errors_at_or_above"])
integration = json.loads((WORK_ROOT / "cached/integration_config.json").read_text())
contract_checks = json.loads((WORK_ROOT / "cached/threshold_contract_checks.json").read_text())
print("Dipilih pengguna:", integration["selected_option"], integration["confidence_threshold"])
print("Referensi:", integration["calibration_reference"])
print("Pemeriksaan kontrak tanpa model:", len(contract_checks["checks"]), "lulus:", contract_checks["all_passed"])
print("Human Verification wajib:", integration["rules"]["human_verification_always_required"])
print("Diterapkan pada aplikasi:", integration["production_deployed"])
'''), md("## Contoh kesalahan yang tetap dilaporkan\n\nAcuan di bawah mengikuti review final, tidak disunting agar cocok dengan prediksi.\n"),
        code('''for row in analysis["examples"]:
    print(row["id"], "gold:", row["gold"], "prediksi:", row["new_prediction"], "confidence:", row["new_confidence"])
    print(row["text"])
    print()
''')]
    attach_image(cells, saved / "confusion_matrix.png", "Confusion matrix dari run Colab")
    attach_image(cells, saved / "training_curves.png", "Kurva dari run Colab")
    cells.append(md("## Kode analisis lengkap\n\nFile yang sama tersedia pada code/analyze_sena_completed_run.py. Reproduksi dari paket diekstrak bersifat opsional dan tidak memerlukan bobot.\n\n```python\n" + (root / "code/analyze_sena_completed_run.py").read_text() + "\n```\n"))
    cells.append(md("## Kode pemeriksaan konfigurasi lengkap\n\nFile yang sama tersedia pada code/verify_selected_fusion_config.py. Pemeriksaan ini telah selesai; menjalankannya kembali bersifat opsional.\n\n```python\n" + (root / "code/verify_selected_fusion_config.py").read_text() + "\n```\n"))
    dump(root / "notebooks/08_SENA_Analisis_Hasil_dan_Threshold.ipynb", make_notebook(cells, "08_SENA_Analisis_Hasil_dan_Threshold.ipynb"))


def update(root, run_zip=None):
    root = Path(root)
    target = root / "sources" / f"SLR09_SENA_Hasil_FineTune_{RUN_ID}.zip"
    if run_zip is not None and Path(run_zip).resolve() != target.resolve():
        shutil.copyfile(run_zip, target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != EXPECTED_ZIP_SHA256:
        raise ValueError("Completed report snapshot differs")
    analysis_path = root / "results" / ("sena_finetune_" + RUN_ID) / "completed_run_analysis.json"
    if not analysis_path.exists():
        from analyze_sena_completed_run import analyze
        analyze(root, target)
    result = json.loads(analysis_path.read_text())
    models, options = model_proposals(root, result)
    if options["selected_option"] is not None:
        from verify_selected_fusion_config import verify
        verify(root)
    update_report(root, result, models, options)
    update_notebooks(root, result)
    dump(root / "evidence/current_operation.json", {"revision": "AFTER_USER_THRESHOLD_SELECTION",
        "accepted_external_sena_run": RUN_ID, "external_sena_training_completed": True,
        "new_training_executed_in_this_update": False, "new_neural_inference_executed_in_this_update": False,
        "nara_evaluation_or_adapter_replay_repeated": False,
        "training_notebook_code_changed": False, "production_model_selected": False,
        "confidence_threshold_selected": options.get("confidence_threshold"),
        "selected_option": options["selected_option"], "production_deployed": False,
        "synthetic_fusion_contract_checks_executed": options["selected_option"] is not None,
        "repository_or_github_card_mutated": False})
    print("Package updated; user selection preserved for integration, not deployed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-zip", type=Path)
    arguments = parser.parse_args()
    update(arguments.root, arguments.run_zip)
