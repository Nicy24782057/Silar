# Konfigurasi dan identitas model

| Berkas/kelompok | Fungsi |
| --- | --- |
| SLR09_Konfigurasi_Integrasi_v0.9.json | Konfigurasi yang digunakan dalam pengujian akhir. v0.9 adalah versi konfigurasi; pipeline tetap v0.8.4. |
| quality_candidate_asset_lock_v0.8.4.json | Identitas model dan kontrak label yang dibekukan sebelum uji FINAL084. |
| model_candidates.json | Pasangan model kandidat terkini beserta lokasi arsipnya. |
| inference_environment.json dan requirements-inference.txt | Catatan lingkungan serta dependensi inferensi. |
| threshold_decision.json dan threshold_options.json | Keputusan cutoff 0,95 dan perbandingan awalnya. |
| Konfigurasi/lock versi sebelumnya | Jejak parameter putaran lama; tidak menjadi pilihan runtime final. |
| requirements-quality-cpu.txt dan requirements-tests.txt | Dependensi eksperimen CPU dan pengujian. |

Flag pra-uji pada konfigurasi/lock tetap asli. Keputusan penerimaan aktif berada pada [release_manifest.json](../release_manifest.json).
