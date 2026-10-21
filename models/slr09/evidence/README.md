# Bukti mentah training dan pengujian

Setiap subfolder merekam putaran yang tercantum pada namanya. File evaluasi, prediksi, label manusia dan snapshot asli tidak ditulis ulang saat folder dirapikan.

| Subfolder | Isi dan konteks |
| --- | --- |
| [acceptance_v084_confirmed_20261020/](acceptance_v084_confirmed_20261020/) | Uji FINAL084 asli: acuan manusia, snapshot 21 sumber, prediksi 50 narasi dan evaluasi awal 8/9 pada batas 5%. original_run/ menyimpan keluaran asli; pre_inference_snapshot/ menyimpan sumber sebelum model dimuat. |
| [acceptance_FINAL084_target006_20261020/](acceptance_FINAL084_target006_20261020/) | Keputusan revisi batas 6%: 9/9 dari prediksi FINAL084 yang sama; tanpa inferensi atau training baru. |
| [quality_fix_v084/](quality_fix_v084/) | Training SENA terakhir di training29/ dan verifikasi ekspor di export_verification30/; memuat data beku, konfigurasi, log dan hasil. |
| [acceptance_v081/](acceptance_v081/) | Uji FINAL081: inferensi 50/50 selesai, pelaporan awal gagal saat SCORING. scoring_completed/ menilai prediksi beku yang sama tanpa mengganti gold atau mengulang inferensi. |
| [acceptance_v082/](acceptance_v082/) | Uji FINAL082 asli: seluruh target angka lulus, satu kontras gagal; total 8/9. |
| [acceptance_v083_confirmed_20261020/](acceptance_v083_confirmed_20261020/) | Uji FINAL083 asli, hasil 6/9; kemudian menjadi data pengembangan/regresi. |
| [final083_review_audit_20261020/](final083_review_audit_20261020/) | Audit review dan snapshot sumber FINAL083. |
| [protocol_snapshots/](protocol_snapshots/) | Snapshot input dan protokol sebelum pergantian versi; pre_v* menyimpan known_inputs serta review_bundle saat itu. |
| [source_snapshots/](source_snapshots/) | Salinan unik kode/config sebelum pergantian versi. Salinan identik yang sudah ada pada snapshot uji tidak digandakan. |
| [baseline_runtime/](baseline_runtime/) | Pemuatan, prediksi dan evaluasi baseline awal. |
| [candidate_smoke_20261018T224651Z_672df897/](candidate_smoke_20261018T224651Z_672df897/) | Bukti pemuatan kandidat pada CPU representatif; bukan bukti VM tujuan. |
| [field_fix_v082/](field_fix_v082/) | Replay pengembangan dan pemeriksaan perubahan komposisi field sesudah FINAL081. |
| [nara_finetune/](nara_finetune/) | Bukti training serta ekspor NARA reviewed pilot. |
| [nara_reviewed_79/](nara_reviewed_79/) | Bukti evaluasi acuan revisi NARA pada 79 narasi. |
| [context_fix_v083/](context_fix_v083/) | Bukti pengembangan perbaikan konteks v0.8.3. |
| [revision_v0.4.1/](revision_v0.4.1/) | Bukti revisi sumber/kontrak v0.4.1. |
| [quality_fix_v05/](quality_fix_v05/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v05. |
| [quality_fix_v083/](quality_fix_v083/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v083. |
| [revision_v0.2/](revision_v0.2/) | Bukti revisi sumber/kontrak v0.2. |
| [quality_fix_v06/](quality_fix_v06/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v06. |
| [quality_fix_v08_recovered/](quality_fix_v08_recovered/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v08_recovered. |
| [revision_v0.4/](revision_v0.4/) | Bukti revisi sumber/kontrak v0.4. |
| [quality_fix_v07/](quality_fix_v07/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v07. |
| [quality_fix_v081/](quality_fix_v081/) | Data, konfigurasi, log, prediksi dan pemeriksaan pengembangan v081. |

JSON provenance/checkpoint_preservation merekam path pada saat eksekusi asli. Lokasi notebook/snapshot yang dirapikan tercatat pada FILE_MANIFEST.json di folder induk. JSON root lainnya memuat provenance notebook, pemeriksaan konfigurasi dan pemeriksaan artefak pada tahap saat itu; keputusan aktif berada di release_manifest.json. Ringkasan angka terbaru berada di [reports/](../reports/README.md).
