# Keputusan akhir model SENA–NARA FINAL084

Tahap training dan pengujian model ditutup sesuai permintaan pengguna pada 20 Oktober 2026 pukul 22:51:37 WIB. Batas isi berlebih pada field kosong direvisi dari ≤5% menjadi ≤6%. Aset MVP diterima berdasarkan kriteria revisi ini: seluruh 9 pemeriksaan terpenuhi. Tidak ada training, perubahan bobot, perubahan label manusia, atau inferensi baru setelah keputusan pengguna.

## Dampak perubahan batas

| Komponen | Batas awal | Batas revisi |
| --- | ---: | ---: |
| Maksimum isi berlebih | 5% | 6% |
| Hasil model yang sama | 10/174 = 5,75% | 10/174 = 5,75% |
| Field berlebih yang diizinkan pada 174 acuan kosong | 8 | 10 |
| Pemeriksaan terpenuhi | 8/9 | 9/9 |
| Keputusan metrik | Belum memenuhi seluruh target | Memenuhi seluruh target revisi |

Kenaikan batas sebesar satu poin persentase hanya mengubah toleransi dan keputusan penerimaan. Tidak ada peningkatan kinerja yang dapat diklaim dari revisi ini: semua prediksi dan nilai metrik identik. Tidak ada uji signifikansi atau hasil baru yang digunakan untuk mengklaim perbaikan statistik. Keputusan dibuat setelah hasil diketahui dan dicatat sebagai penerimaan pilot dengan kriteria pengguna yang direvisi, bukan uji independen baru.

## Nilai hasil tetap

- SENA: 49/50 narasi benar (98%); macro F1 97.99%; recall NON_EVENT 90%; recall keempat kelas kejadian masing-masing 100%.
- NARA: macro F1 seluruh 14 label non-O 85.31%; exact span F1 81.86%.
- Field nonkosong tepat: 154/176 = 87,50%; isi berlebih pada acuan kosong: 10/174 = 5,75%.
- Kontrak adapter/Fusion serta kontras simulasi/latihan yang ditetapkan protokol tetap terpenuhi. Cutoff confidence tetap 0,95, kategori hanya dari SENA, dan verifikasi manusia selalu wajib.

Hasil penerimaan pertama dengan batas 5% tetap utuh dalam `original_run/evaluation.json`, termasuk status 8/9. Perhitungan keputusan dengan batas 6% memakai prediksi tersimpan yang sama dan disimpan terpisah di `evidence/acceptance_FINAL084_target006_20261020/`. Notebook 32 merekam perhitungan tersebut tanpa memuat model.

## Model yang diserahkan

| Aset | Berkas persis yang digunakan | SHA256 arsip |
| --- | --- | --- |
| SENA v0.8.4 | SILAR_SENA_context_v0.8.4_20261020.zip | `6d9ed7b2705301602aa72b67c911843dd8451b115efce8739ae4f07bde3cd3e5` |
| NARA reviewed pilot | SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip | `bce9feba0dd2ae4518880708085f44286ae8d1dd7e50f4eb452e36824f967798` |

NARA yang digunakan adalah bobot reviewed pilot 18 Oktober 2026, bersama adapter 0.5.3, postprocessing 0.3.1, composition 0.3.1 dan victim guard 0.5.0. Seluruh kode tersebut disertakan dalam paket evaluasi. Tanggal model NARA dipertahankan sesuai identitas aslinya. Bobot tidak diganti atau diberi nomor versi baru akibat perubahan batas penerimaan.

## Notebook dan data review

Paket `SLR09_Notebook_dan_Data_Evaluasi_FINAL084_v0.8.4.zip` berisi:

- Notebook 31 sumber dan salinan `_executed`: eksekusi inferensi aktual pada 50 acuan FINAL084, dengan hasil awal 8/9 pada batas 5%.
- Notebook 32 sumber dan salinan `_executed`: keputusan akhir pada batas 6% dari prediksi tersimpan, tanpa training atau inferensi baru.
- Excel review asli `Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx`, 50 APPROVED dan 692 token, SHA256 `046e468d3b9cb137d39ce5886dbc0eee0325cc5d406902de745b980f02253ad4`.
- JSON acuan manusia yang dibekukan, seluruh prediksi JSONL, hasil metrik awal, keputusan revisi, audit review, lock, lingkungan inferensi dan snapshot sumber sebelum model dimuat.
- Evaluator, importer, runtime SENA/NARA, adapter/postprocessing, tokenizer role contract, konfigurasi terkunci dan requirements yang dipakai. Semua 21 file yang terikat pada pengujian disertakan dengan hash identik.

Excel dan acuan pertama tetap mencatat target 5% yang berlaku ketika review dan pengujian pertama dilakukan. Persetujuan batas baru 6% berada pada berkas keputusan terpisah; label acuan dan target lama tidak ditulis ulang.

## Cakupan penyelesaian

Training dan pengujian aset model selesai. Penerimaan mutu berlaku untuk pilot aset MVP dengan kriteria revisi pengguna. Pilot terdiri dari 50 narasi sintetis yang direview manusia; perubahan batas tidak membuktikan peningkatan generalisasi atau kalibrasi confidence. Deployment, target VM/backend submission, dan status Done untuk keseluruhan proyek tidak diklaim oleh serah terima model ini. Konfigurasi yang dibekukan sebelum pengujian mempertahankan metadata historisnya; keputusan penerimaan terkini berada pada berkas revisi dan recovery terkini.
