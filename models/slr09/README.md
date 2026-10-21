# SLR09 — model SENA dan NARA v0.8.4

Hasil terbaru berada di [reports/README.md](reports/README.md) atau [BUKA_HASIL.html](BUKA_HASIL.html). Pada FINAL084: SENA accuracy **98,00%**, macro F1 **97,99%**; NARA macro F1 14 non-O **85,31%**, exact span F1 **81,86%**.

## Isi folder

| Folder | Fungsi |
| --- | --- |
| [notebooks/](notebooks/README.md) | Notebook final 29–32 beserta keluaran eksekusinya: training, verifikasi ekspor, uji FINAL084 dan keputusan batas 6%. |
| [historical/](historical/README.md) | Notebook lama, dikelompokkan menurut tahap/versi. Satu README menjelaskan seluruh kelompoknya. |
| [reports/](reports/README.md) | Hasil terbaru SENA, NARA, field dan keputusan FINAL084; metrics_summary.json memuat angka beserta sumbernya. |
| [code/](code/README.md) | Implementasi runtime, adapter, training, importer/evaluator dan pengujian. |
| [config/](config/README.md) | Konfigurasi, lock model, requirements dan keputusan cutoff. Versi config final adalah v0.9; pipeline v0.8.4. |
| [data/](data/README.md) | Data training/development, proposal acuan, identitas split dan catatan retirement putaran lama. |
| [acceptance/](acceptance/README.md) | Workbook review manusia dan protokol penerimaan. Workbook FINAL084 yang diuji memakai nama v0_8_4. |
| [evidence/](evidence/README.md) | Bukti mentah training/pengujian: log, prediksi, acuan beku, snapshot sumber, metrik asli dan revisi keputusan. |
| [results/](results/README.md) | Laporan, Excel, grafik dan hasil olahan eksperimen sebelum FINAL084. |
| [sources/](sources/README.md) | ZIP laporan asal, dokumen acuan proyek dan sumber review. Notebook asalnya dikelompokkan di historical. |
| [nara_finetune_frozen/](nara_finetune_frozen/README.md) | Kode, data dan split fine-tune NARA reviewed pilot yang dibekukan. |
| [examples/](examples/README.md) | Tiga narasi sintetis untuk smoke test pemuatan; bukan data uji penerimaan terbaru. |
| [docs/](docs/README.md) | Tiga laporan teknis awal tentang evaluasi NARA dan kondisi sebelum fine-tune SENA. |

## Identitas dan cakupan

[release_manifest.json](release_manifest.json) mencatat pasangan model, versi kode dan status penerimaan. [FILE_MANIFEST.json](FILE_MANIFEST.json) mencatat hash berkas dan pemetaan lokasi notebook/snapshot yang dirapikan. asset_manifest.json serta sumber yang terikat pada pengujian mempertahankan isi pra-uji aslinya.

SENA memakai SILAR_SENA_context_v0.8.4_20261020.zip; NARA memakai SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip. Folder arsip model tersedia kosong di luar folder ini. Bobot NARA tetap, sedangkan kode pendamping field diperbarui.

Training dan pengujian model selesai dalam cakupan pilot aset MVP. Keputusan 9/9 memakai batas isi berlebih ≤6%; hasil awal 8/9 pada batas 5% dan prediksinya tetap tersedia. Revisi batas tidak mengubah metrik. Cutoff 0,95 dan verifikasi manusia tetap berlaku; pemuatan VM tujuan serta status formal card belum terverifikasi.
