# SLR09 - Rekap notebook, evaluasi SENA, dan kesiapan aset v0.1

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
| SENA terhadap 620 label final | Accuracy 64.03%; macro F1 65.75% | Analisis retrospektif dari prediksi tersimpan. |

Laporan evaluasi NARA yang dikirim pengguna identik dengan laporan sebelumnya; metrik dan tabel kesalahan sama. Perbedaan evaluation.json hanya waktu pembuatan. Tidak ada alasan menjalankan ulang evaluasi tersebut.

## Temuan baru: SENA belum sesuai dengan keseluruhan review final

Analisis lama memakai 623 kandidat: 71 referensi hasil review dan 552 label sumber. Angka 94,70% accuracy dan 94,39% macro F1 dari referensi campuran tersebut tetap berlaku dalam cakupannya, tetapi tidak menggambarkan seluruh hasil review B1 yang kemudian diselesaikan.

Paket sekarang mencocokkan 620 referensi final dengan ID, teks persis, hash input, kategori, confidence, dan probabilitas dari run SENA yang sama. Tiga kasus TUNDA tetap dikeluarkan: BAN-01028, KEB-01113, BAN-01529. Tidak ada bobot berubah atau inferensi baru. Label final mengikuti keputusan reviewer, bukan koreksi otomatis oleh kode.

| Acuan pada 620 narasi yang sama | Accuracy | Macro F1 lima kelas |
| --- | --- | --- |
| Label sumber historis | 88.55% | 86.61% |
| Seluruh review final | 64.03% | 65.75% |

Review mengubah 228 dari 620 label. SENA memprediksi 334 NON_EVENT, sedangkan acuan final memiliki 131 NON_EVENT. Dari 489 narasi berlabel kejadian dalam review, **213 diprediksi NON_EVENT (43,56%)**. Ada 10 arah sebaliknya (acuan NON_EVENT, prediksi kejadian), tanpa pertukaran antarempat kategori kejadian pada subset ini. Total 397 benar dan 223 berbeda dari acuan.

| Kategori | Acuan | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| FLOOD | 131 | 94.23% | 37.40% | 53.55% |
| EARTHQUAKE | 108 | 97.56% | 37.04% | 53.69% |
| FIRE | 141 | 97.06% | 70.21% | 81.48% |
| ACCIDENT | 109 | 96.70% | 80.73% | 88.00% |
| NON_EVENT | 131 | 36.23% | 92.37% | 52.04% |

Ini menunjukkan ketidakselarasan SENA terhadap kebijakan anotasi final pada subset ini. Hasil tersebut tidak menunjukkan bahwa bobot SENA tiba-tiba berubah setelah evaluasi lama. Identitas kandidat validation terhadap train/validation checkpoint SENA historis tetap belum terbukti; karena itu skor bukan test independen.

## Threshold belum dapat menyelesaikan kesalahan kategori

| Cutoff confidence | Di bawah cutoff | Pada/di atas cutoff | Accuracy kelompok atas | Salah NON_EVENT pada kelompok atas |
| --- | --- | --- | --- | --- |
| 0.80 | 43 | 577 | 65.51% | 193 |
| 0.90 | 79 | 541 | 67.28% | 174 |
| 0.95 | 128 | 492 | 68.70% | 152 |
| 0.99 | 470 | 150 | 83.33% | 25 |

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

## Validasi hasil analisis

Metrik baru SENA telah dicocokkan dengan scikit-learn (accuracy, macro/weighted F1, precision/recall/F1/support setiap kelas dan confusion matrix) pada kedua acuan 620 narasi yang sama. Sumber review cocok dengan checkpoint, manifest dan workbook terkunci. Hash input dan probabilitas dicocokkan pada setiap narasi. Tidak ada training atau inferensi neural baru pada penyusunan paket. Evidence berisi hasil pemeriksaan, hash notebook sumber, status notebook baru dan manifest berkas.
