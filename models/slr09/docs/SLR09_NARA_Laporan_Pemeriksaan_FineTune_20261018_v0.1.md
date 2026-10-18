# SLR09 — Pemeriksaan hasil fine-tune NARA v0.1

**Run:** `20261018T001122_607337Z` · **Tanggal pemeriksaan:** 18 Oktober 2026.

**Workflow:** cocokkan sumber dan pemisahan data → hitung ulang prediksi → telusuri perubahan ekstraksi → tentukan status kandidat.

## Kesimpulan

Fine-tune tercatat berhasil dan metrik yang dikirim konsisten dengan prediksi mentah. Kinerja pada validasi hasil review meningkat, tetapi test historis menurun. Model baru sebaiknya dipertahankan sebagai **kandidat eksperimen**; hasil ini belum menjadi dasar mengganti model aktif atau menetapkan model produksi.

Hasil review yang dipilih pengguna tetap berlaku: 15 label flat dengan adapter; WOUND mencakup kondisi fisik eksplisit sesuai pedoman 0.2. Tidak ada anotasi, aturan adapter, konfigurasi pelatihan, atau kode notebook pelatihan yang diubah dalam pemeriksaan ini.

## Bukti yang diperiksa dan batas pemeriksaan

ZIP laporan `SLR09_NARA_Hasil_FineTune_20261018T001122_607337Z.zip` tersedia dan dibaca lengkap: 30 file. SHA-256: `879b3205419a9897075145a64c94e29c1f3b81b558af170a8181f55fdfa63bfb`.

**140 pemeriksaan konsistensi lulus.** Audit memakai hitungan mandiri berbasis jumlah token dan span, tanpa mengimpor fungsi metrik dari pipeline pelatihan. Nilai metrik token, precision/recall/F1 tiap label, metrik span, serta confusion matrix JSON/CSV cocok dengan laporan. Gold validasi cocok dengan file review terkunci; gold test historis cocok dengan CSV sumber yang hash-nya diverifikasi. Kelulusan pemeriksaan ini berarti data dan perhitungannya konsisten, bukan persetujuan kelayakan produksi.

ZIP model `SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip` tidak tersedia dalam pemeriksaan ini. Status ekspor berhasil, perubahan hash bobot, dan pemeriksaan reload berasal dari laporan Colab. Bobot baru belum diperiksa langsung dan inferensi tidak dijalankan ulang di lingkungan pemeriksaan.

## Urutan artefak dalam tahap ini

| Urutan | Artefak/kejadian | Makna |
| --- | --- | --- |
| 1 | NARA v1 dari artefak sebelumnya | Checkpoint sumber fine-tune; tidak dilatih ulang dari bobot acak. |
| 2 | Review B1 dan suplemen korban | Keputusan manusia menjadi label acuan; satu narasi berstatus TUNDA dikeluarkan. |
| 3 | Pilihan A: pertahankan hasil review | Pedoman efektif 0.2 dan guard 0.4 mempertahankan cakupan kondisi fisik eksplisit. |
| 4 | Paket fine-tune v0.1 dibekukan | 157 train dan 41 validasi; 15 label tetap; tidak memasukkan diagnostik/test ke fine-tune. |
| 5 | Run Colab 18 Oktober 2026, 07:11–07:18 WIB | 10 epoch, 100 optimizer steps; checkpoint terbaik pada epoch 10. |
| 6 | Audit hasil run ini | Prediksi dihitung ulang; perbaikan dan kemunduran dicatat; belum ada pemilihan model final. |

Urutan ini hanya mencakup tahap review dan fine-tune NARA yang buktinya tersedia; tidak mengubah urutan PRD, dokumen acuan, atau pekerjaan SLR07–08.

## Pelaksanaan dan pemisahan data

| Bagian | Narasi | Token sumber | Fungsi |
| --- | --- | --- | --- |
| Train hasil review | 157 | 3647 | Memperbarui bobot model. |
| Validasi hasil review | 41 | 994 | Memilih checkpoint berdasarkan macro F1 non-O. |
| Test historis | 1000 | 21924 | Evaluasi sesudah checkpoint dipilih; memakai label lama. |
| Diagnostik dikenal | 12 | 84 field / 31 acuan berisi | Menelusuri keluaran NARA dan adapter; bukan blind test. |

ID train, validasi, dan test tidak beririsan. `KEB-00486` tetap dikeluarkan karena TUNDA. File sumber dan dua checkpoint review cocok dengan hash pada paket terkunci. Semua 15 label terdapat pada train dan validasi.

Konfigurasi run: seed 42; maksimum 256 wordpiece; learning rate 0,00002; batch train 16; batch evaluasi 32; weight decay 0,01; maksimum 10 epoch; early-stopping patience 2. Runtime melaporkan Tesla T4, Transformers 4.57.1, dan waktu pelatihan 322,9832 detik. Checkpoint terpilih `checkpoint-100`.

Run mencapai batas 10 epoch. Nilai macro F1 validasi terus meningkat pada setiap epoch, sehingga early stopping tidak menghentikan run lebih awal. Pemilihan checkpoint mengikuti macro F1 validasi, bukan test historis.

| Epoch | Step | Train loss tercatat | Validation loss | Macro F1 validasi non-O |
| --- | --- | --- | --- | --- |
| 1 | 10 | 1.3647 | 1.0992 | 63,25% |
| 2 | 20 | 0.7514 | 0.8694 | 67,40% |
| 3 | 30 | 0.5605 | 0.7856 | 72,07% |
| 4 | 40 | 0.4236 | 0.7073 | 74,51% |
| 5 | 50 | 0.3459 | 0.6903 | 75,66% |
| 6 | 60 | 0.2861 | 0.6537 | 76,38% |
| 7 | 70 | 0.2421 | 0.6394 | 78,37% |
| 8 | 80 | 0.2076 | 0.6524 | 78,41% |
| 9 | 90 | 0.2068 | 0.6417 | 78,59% |
| 10 | 100 | 0.1935 | 0.6365 | 78,65% |

Kurva loss dan F1 serta empat confusion matrix asli Colab disertakan di `audit/grafik_dari_colab/`. Kurva menunjukkan pembelajaran pada validasi ini; kurva tersebut sendiri tidak membuktikan kemampuan generalisasi pada data baru.

## Perbandingan metrik

Macro F1 non-O adalah rata-rata F1 **14 label selain O**, dengan bobot sama per label. Kesalahan dari/ke O tetap memengaruhi false positive dan false negative. Akurasi token menggunakan seluruh 15 label. Metrik span menuntut label dan batas token yang tepat pada label flat, tanpa mengasumsikan format BIO. Selisih dilaporkan dalam **poin persentase**, bukan persentase kenaikan relatif.

### Validasi hasil review — 41 narasi

| Metrik | NARA v1 | Fine-tune | Selisih (poin) |
| --- | --- | --- | --- |
| Akurasi token | 57,14% | 77,57% | +20,42 |
| Precision macro non-O | 63,02% | 82,05% | +19,03 |
| Recall macro non-O | 51,56% | 79,26% | +27,70 |
| Macro F1 non-O | 49,28% | 78,65% | +29,37 |
| Micro F1 non-O | 49,29% | 76,51% | +27,22 |
| F1 span tepat | 37,77% | 64,21% | +26,44 |

### Test historis — 1.000 narasi

| Metrik | NARA v1 | Fine-tune | Selisih (poin) |
| --- | --- | --- | --- |
| Akurasi token | 86,25% | 68,15% | -18,09 |
| Precision macro non-O | 74,76% | 53,62% | -21,14 |
| Recall macro non-O | 65,75% | 75,87% | +10,12 |
| Macro F1 non-O | 67,77% | 58,56% | -9,21 |
| Micro F1 non-O | 74,13% | 56,20% | -17,93 |
| F1 span tepat | 67,75% | 44,14% | -23,61 |

Validasi hasil review digunakan untuk memilih checkpoint. Karena itu **78,65% bukan skor test independen dan bukan akurasi keseluruhan aplikasi**. Dua label validasi, EARTHQUAKE dan FALSE, masing-masing hanya memiliki tiga token acuan; nilai per label ini memiliki dukungan yang sangat kecil.

Test historis masih memakai label lama. Penurunan macro F1 9,21 poin tetap merupakan temuan penting. Perubahan pedoman dapat berkontribusi pada ketidakcocokan label, tetapi run ini belum dapat memisahkannya dari penurunan generalisasi atau penyesuaian berlebihan pada sampel kecil. Penyebab tunggal seperti 'hanya beda anotasi' atau 'pasti overfitting' belum terbukti.

### Pola kesalahan test historis

Prediksi label non-O naik dari 33,52% menjadi 55,96% token, sedangkan acuan historis berisi 33,63% non-O. Pada validasi revisi, acuan non-O berisi 67,61% dan prediksi fine-tune 63,88%. Perbedaan kepadatan anotasi ini nyata, tetapi belum menjelaskan seluruh penurunan.

Token dengan acuan historis O yang diprediksi sebagai suatu peran meningkat dari **1.098 menjadi 5.128**. Rinciannya antara lain:

| Acuan → prediksi | NARA v1 (token) | Fine-tune (token) |
| --- | --- | --- |
| O → INFORMATION-ARG | 206 | 1517 |
| O → OFFICER-ARG | 152 | 1295 |
| O → PLACE-ARG | 252 | 798 |
| O → TIME-ARG | 29 | 664 |

Ini menunjukkan model lebih sering mengeluarkan peran pada teks yang berlabel O dalam acuan lama. Dampaknya pada keluaran aplikasi harus diperiksa terhadap acuan revisi, bukan diasumsikan benar atau salah seluruhnya.

### F1 per label

| Label | Support validasi | F1 v1 → fine (validasi) | Support test historis | F1 v1 → fine (historis) |
| --- | --- | --- | --- | --- |
| O | 322 | 65,96% → 79,59% | 14550 | 92,37% → 77,85% |
| ACCIDENT-EVENT | 14 | 83,33% → 90,32% | 225 | 82,05% → 79,11% |
| AFFECTEDOBJECTS-ARG | 49 | 68,75% → 76,92% | 794 | 79,19% → 74,38% |
| DEATHVICTIM-ARG | 14 | 66,67% → 87,50% | 183 | 71,14% → 65,50% |
| EARTHQUAKE-EVENT | 3 | 0,00% → 100,00% | 227 | 56,32% → 56,90% |
| FALSE-EVENT | 3 | 26,09% → 50,00% | 801 | 76,53% → 45,71% |
| FIRE-EVENT | 26 | 57,89% → 86,27% | 193 | 85,64% → 74,53% |
| FLOOD-EVENT | 11 | 62,50% → 100,00% | 141 | 56,73% → 71,31% |
| INFORMATION-ARG | 122 | 1,50% → 60,94% | 574 | 48,40% → 25,02% |
| OFFICER-ARG | 155 | 34,74% → 78,87% | 410 | 71,06% → 34,42% |
| PLACE-ARG | 145 | 68,48% → 85,29% | 2315 | 84,40% → 70,88% |
| REASON-ARG | 39 | 45,61% → 57,58% | 256 | 39,53% → 45,06% |
| STREET-ARG | 22 | 75,56% → 85,71% | 511 | 58,70% → 50,39% |
| TIME-ARG | 47 | 43,75% → 83,67% | 647 | 86,50% → 65,31% |
| WOUNDVICTIM-ARG | 22 | 55,07% → 58,06% | 97 | 52,63% → 61,31% |

SENA tetap menjadi penentu kategori kejadian. Label kejadian milik NARA pada tabel ini tidak boleh diperlakukan sebagai hasil klasifikasi SENA.

## Pemeriksaan 12 diagnostik dan 84 field

Kecocokan exact seluruh field meningkat dari **66/84 menjadi 73/84**. Rinciannya: 60 tetap cocok, **13 membaik, 6 memburuk**, dan 5 tetap tidak cocok. Pada 31 acuan yang berisi, kecocokan naik dari **14/31 menjadi 25/31**. Pada 53 acuan kosong, kecocokan turun dari **52/53 menjadi 48/53**.

Penilaian ini membandingkan nilai lengkap, termasuk urutan daftar dan batas teks. Satu nilai tambahan pada daftar menjadikan field tersebut tidak exact, meskipun isi yang benar juga ada.

| Field | Exact v1 (termasuk kosong) | Exact fine (termasuk kosong) | Acuan berisi | Exact pada acuan berisi: v1 → fine |
| --- | --- | --- | --- | --- |
| location_text | 9/12 | 11/12 | 8 | 5 → 7 |
| time_text | 12/12 | 10/12 | 5 | 5 → 4 |
| occurred_at | 12/12 | 12/12 | 0 | Tidak ada acuan berisi |
| involved_parties | 7/12 | 12/12 | 6 | 1 → 6 |
| impacts | 6/12 | 5/12 | 6 | 0 → 3 |
| victims | 12/12 | 12/12 | 1 | 1 → 1 |
| affected_objects | 8/12 | 11/12 | 5 | 2 → 4 |

Perbaikan paling terlihat pada pihak terlibat, lokasi, dan objek terdampak. Namun `impacts` secara total turun dari **6/12 menjadi 5/12**, dan `time_text` turun dari **12/12 menjadi 10/12**. Kecocokan `victims` 12/12 hanya memiliki **satu** acuan berisi; ini tidak membuktikan seluruh variasi kondisi korban sudah dikuasai. Seluruh acuan `occurred_at` kosong, sehingga hasil 12/12 tidak menguji normalisasi timestamp.

### Enam field yang memburuk

| ID | Field | Acuan | NARA v1 | Fine-tune |
| --- | --- | --- | --- | --- |
| D07 | time_text | null | null | "tahun" |
| D07 | impacts | [] | [] | ["Pemerintah sedang membahas"] |
| D08 | time_text | "pagi ini" | "pagi ini" | "pagi" |
| D08 | impacts | [] | [] | ["simulasi evakuasi"] |
| D10 | impacts | [] | [] | ["belum diketahui"] |
| D11 | impacts | [] | [] | ["dua orang dibawa ambulans", "penyebabnya belum diketahui"] |

Contoh D07: pembahasan solusi banjir untuk tahun depan menghasilkan waktu `tahun` dan tambahan impact `Pemerintah sedang membahas`. Contoh D08: simulasi menghasilkan tambahan impact `simulasi evakuasi` serta waktu `pagi` yang tidak sama dengan acuan `pagi ini`. Pada D10–D11, frasa ketidaktahuan penyebab ikut masuk ke impacts. Semua dibandingkan dengan hasil review yang tetap dipertahankan.

### Lima field yang masih tidak cocok sebelum dan sesudah fine-tune

| ID | Field | Acuan | Fine-tune |
| --- | --- | --- | --- |
| D02 | impacts | ["dua rumah sudah terendam"] | ["Air naik cepat", "dua rumah sudah terendam"] |
| D03 | impacts | ["Bangunan bergoyang"] | ["Bangunan bergoyang", "warga langsung keluar rumah"] |
| D04 | location_text | "dekat pasar" | "kios dekat pasar" |
| D04 | affected_objects | ["kios"] | [] |
| D12 | impacts | ["warga keluar rumah"] | ["terasa", "warga keluar rumah"] |

D02, D03, dan D12 sudah memuat sebagian isi yang diharapkan, tetapi masih menambahkan impact lain. D04 masih mencampur batas lokasi/objek: `kios dekat pasar` menjadi lokasi, sedangkan objek `kios` hilang.

Prediksi NARA untuk diagnostik ini baru dijalankan di Colab. SENA memakai prediksi aktual tersimpan dari run sebelumnya; fusion produksi tidak dijalankan. Status NON_EVENT tidak digunakan untuk menyembunyikan seluruh ekstraksi NARA: acuan yang telah direview tetap dipakai sesuai keputusan pengguna untuk menilai klaim teks. Angka 73/84 tidak boleh disebut akurasi produksi atau skor blind test.

## Empat contoh kondisi fisik korban

| ID | Partisi | Acuan WOUND | Hasil setelah guard | Temuan |
| --- | --- | --- | --- | --- |
| KEC-01099 | train | tiga kritis | ["tiga kritis"] | Target ada |
| KEC-01462 | train | angkotpengendara motor tak sadarkan diri | ["angkotpengendara motor tak sadarkan diri"] | Target ada |
| KEB-00290 | validation | 1 korban mengalami sesak nafas | [] | Target belum terekstrak |
| KEC-01399 | validation | korban r2 dua orang dalam keadaan kritis | ["korban r2 dua orang dalam keadaan kritis"] | Target ada |

Dua contoh train berhasil, tetapi merupakan data yang sudah dipakai memperbarui bobot. Dari dua contoh validasi, `kritis` berhasil dan `sesak nafas` gagal. Keduanya juga bagian dari validasi pemilihan checkpoint; jangan menyebutnya blind test 4/4 atau menggeneralisasikan rasio 1/2 ke populasi.

Pada KEB-00290, token `1 korban mengalami` diprediksi WOUND, tetapi `sesak` dan `nafas` diprediksi INFORMATION. Akibatnya span WOUND yang masuk ke guard kehilangan bukti kondisi fisik dan dihapus dengan flag `WOUND_VICTIM_SUPPRESSED_NO_WOUND_EVIDENCE`. Temuan ini menunjukkan pemisahan label neural yang keliru pada contoh tersebut. Aturan guard yang sudah mendukung sesak napas tidak otomatis dapat memulihkan frasa yang tidak diprediksi dalam span WOUND. Review tetap dipertahankan; audit ini tidak melonggarkan guard atau menyisipkan label koreksi.

## Cakupan token dan perbedaan unit inferensi

Tidak ada narasi terpotong atau wordpiece terakhir parsial pada train, validasi, maupun test historis. Evaluasi token menggunakan wordpiece pertama setiap token sumber; special token dan subword lanjutan tidak dihitung sebagai target tambahan. Unit token corpus berbeda dari regex serving pada 34/157 narasi train, 5/41 validasi, dan 210/1.000 test. Perbedaan ini tercatat dan tidak dipakai untuk mengubah gold secara diam-diam. Skor token corpus dan pemeriksaan field saat serving mengukur keluaran pada unit yang berbeda.

## Status dan langkah berikutnya

| Bagian | Status |
| --- | --- |
| Run fine-tune | Selesai menurut laporan; hasil perhitungan konsisten. |
| Validasi sesuai review | Membaik; digunakan memilih checkpoint. |
| Test historis | Menurun; tetap dicatat sebagai keterbatasan dan bahan analisis. |
| Ekstraksi adapter | Ada perbaikan dan regresi; terutama perlu menangani tambahan impacts yang tidak sesuai acuan. |
| Bobot ekspor baru | Ekspor/reload dilaporkan berhasil; belum diperiksa langsung di sini. |
| Pemilihan model final/threshold produksi | Belum dilakukan. |

Rekomendasi berikutnya adalah **evaluasi terpisah dengan acuan pedoman 0.2 sebelum memilih model final atau melatih ulang lagi**. Kandidat ini dan konfigurasi evaluasinya perlu dibekukan terlebih dahulu. Anotasi evaluasi dilakukan tanpa melihat prediksi model; data tersebut tidak digunakan untuk training atau memilih checkpoint. Sampel diagnostik yang sudah sering dilihat tidak dapat menggantikan evaluasi terpisah tersebut.

| Pilihan langkah | Kelebihan | Kekurangan/konsekuensi |
| --- | --- | --- |
| A. Evaluasi terpisah sesuai pedoman revisi — rekomendasi | Memberi pembanding yang sesuai target baru dan dasar memilih model. | Membutuhkan review label tambahan; sumber dan jumlah sampelnya perlu disepakati sebelum disiapkan. |
| B. Langsung fine-tune ulang pada data yang sama | Dapat menjalankan eksperimen lanjutan lebih cepat. | Belum menjawab perbedaan kebijakan label, berisiko terus menyesuaikan model pada validasi kecil; tidak direkomendasikan sebagai langkah sekarang. |

Audit ini belum menambahkan dataset review baru atau memulai fine-tune lanjutan. ZIP laporan sudah cukup untuk analisis di atas. Pengiriman ulang ZIP model diperlukan bila pemeriksaan langsung isi/bobot ekspor menjadi langkah berikutnya.

## Berkas pendukung

- `audit/hasil_audit.json`: hasil hitung mandiri dan 140 pemeriksaan, termasuk batas verifikasi bobot.
- `audit/perbandingan_label.csv`: precision/recall/F1 dan support tiap label.
- `audit/perubahan_84_field.csv`: semua acuan, prediksi sebelum/sesudah, dan status perubahan.
- `audit/perubahan_prediksi_token.csv`: posisi token yang prediksinya berubah, beserta gold terkunci.
- `audit/riwayat_epoch.csv`: loss dan macro F1 setiap epoch.
- `audit/grafik_dari_colab/`: kurva dan confusion matrix asli, tanpa mengganti angka.
- `code/audit_hasil_nara.py` dan `code/buat_laporan.py`: kode lengkap pemeriksaan dan penyusunan laporan.
- `sources/`: ZIP hasil asli, sumber terkunci yang diperlukan untuk audit, serta salinan 1.000 record test historis dan provenance CSV.

Paket ini melengkapi notebook fine-tune v0.1 yang telah dikirim. Kode dan notebook pelatihan sebelumnya tidak diubah oleh pemeriksaan hasil ini.
