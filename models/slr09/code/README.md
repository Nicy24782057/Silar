# Kode model dan evaluasi

| Bagian | Fungsi |
| --- | --- |
| active_nara_adapter/ | Runtime pasangan model dan pembentuk field. Jalur final: slr09_candidate_runtime.py; adapter 0.5.3, composition 0.3.1, postprocessing 0.3.1 dan victim guard 0.5.0. |
| acceptance/ | Import review Excel, validasi acuan, evaluasi penerimaan dan keputusan batas 6% dari prediksi tersimpan. |
| quality_fix/ | Skrip eksperimen per versi, termasuk cache/training SENA v0.8.4, ekspor dan verifikasi. |
| nara_reviewed_evaluation/ | Evaluasi NARA terhadap acuan hasil review terdahulu. |
| tests/ | Pemeriksaan kontrak, runtime dan aturan pemrosesan. |
| Skrip pada root code/ | Pelatihan/analisis awal SENA, pemeriksaan kandidat dan pembentuk artefak versi lama. |

slr09_runtime.py menyimpan jalur baseline/helper historis. Skrip pembentuk notebook/paket lama merekam susunan workspace saat eksperimen. Sumber final yang terikat pada uji FINAL084 tetap identik dengan snapshot pengujian.
