# SLR09 - Paket notebook dan rekap v0.1

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
