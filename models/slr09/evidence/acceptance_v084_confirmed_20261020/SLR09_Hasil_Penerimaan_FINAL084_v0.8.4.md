# Hasil penerimaan FINAL084 SLR_09 v0.8.4

**Status mutu: belum lulus. Status pekerjaan: In Review.** Uji penerimaan pertama pada FINAL084 selesai pada 20 Oktober 2026, pukul 22:38 WIB. Delapan dari sembilan pemeriksaan terpenuhi. Satu yang belum terpenuhi adalah isi berlebih pada field acuan kosong: 10/174 atau 5,75%, melebihi batas 5%.

## Hasil review manusia

Workbook yang diserahkan adalah `Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx`, reviewer Bintang. Seluruh 50 narasi berstatus APPROVED, masing-masing 10 per kelas. Semua 692 token terisi dan seluruh 14 role non-O tercakup. Teks narasi, ID, urutan/teks token, target dan cutoff lolos validasi.

Dua perubahan substantif dari usulan awal dipertahankan:

- FINAL084-EARTHQUAKE-01: Dampak menjadi `mengguncang` dari `mengguncang Kecamatan Puspareja`.
- FINAL084-EARTHQUAKE-10: token `susulan` menjadi O dari EARTHQUAKE-EVENT; token `Gempa` tetap pemicu kejadian.

Kedua perubahan adalah pilihan acuan reviewer yang valid dan bersumber dari teks. Catatan bahwa lokasi sudah berada di field Lokasi tidak menjadi larangan umum atas frasa yang boleh muncul pada dua field berbeda: peran token dan cakupan field tidak selalu satu banding satu. Misalnya, frasa korban dapat juga memberikan identitas pihak. Pada pengujian ini acuan tetap persis sesuai review, tanpa mengubah kode agar mengikuti dua koreksi tersebut.

SHA256 workbook masukan: `046e468d3b9cb137d39ce5886dbc0eee0325cc5d406902de745b980f02253ad4`. Masukan asli tidak diedit; salinan identik, audit per sel dan dua perubahan acuan tersedia pada direktori submission.

## Hasil pengujian aktual

| Pemeriksaan | Hasil | Target tetap | Status |
| --- | ---: | ---: | --- |
| SENA macro F1 | 97.99% | ≥85% | Lulus |
| Recall NON_EVENT | 90.00% | ≥90% | Lulus |
| Recall minimum empat kelas kejadian | 100.00% | ≥80% | Lulus |
| NARA macro F1 seluruh 14 non-O | 85.31% | ≥75% | Lulus |
| NARA exact span F1 | 81.86% | ≥60% | Lulus |
| Field nonkosong tepat | 87.50% | ≥80% | Lulus |
| Isi berlebih pada field kosong | 5.75% | ≤5% | Belum lulus |
| Kontrak adapter/Fusion | 0 kesalahan | 0 kesalahan | Lulus |
| Kontras simulasi/latihan dan kejadian nyata sesuai protokol | Semua benar | Semua benar | Lulus |

SENA benar pada 49/50 narasi (98%). Recall empat kelas kejadian masing-masing 100%; NON_EVENT benar 9/10, tepat memenuhi target 90%. Target memang mengizinkan satu kesalahan NON_EVENT pada sepuluh contoh; tidak ada tuntutan akurasi kategori 100% pada seluruh pilot.

Field nonkosong tepat berjumlah 154/176 (87,50%). Kecocokan pada field kosong tidak dimasukkan untuk menaikkan skor tersebut. Ada 32 perbedaan field secara keseluruhan: 22 pada acuan nonkosong dan 10 pada acuan kosong. Metrik isi berlebih menghitung sel field, bukan jumlah item di dalam sel.

## Satu kesalahan kategori

`FINAL084-NON_EVENT-08`: “Gempa dan banjir hanya muncul dalam cerita yang dibaca guru di Sekolah Puspanirmala siang ini.”

Acuan manusia NON_EVENT, prediksi SENA FLOOD, confidence 81.80%. Ini cerita yang tidak menyatakan kejadian nyata. Kesalahan ditandai LOW_CLASSIFICATION_CONFIDENCE karena berada di bawah cutoff 0,95. Total empat narasi ditandai; tidak ada kesalahan kategori pada confidence ≥0,95 dalam 50 contoh ini. Hasil kecil ini tidak membuktikan kalibrasi atau jaminan 95% benar. Kategori tetap berasal dari SENA; FALSE-EVENT NARA tidak menggantinya.

Kasus fiksi tersebut dilaporkan pada metrik NON_EVENT. Pemeriksaan kontras khusus pada protokol mencakup keluarga simulasi, latihan murni, dan kejadian nyata saat latihan; semua contoh pada kelompok khusus itu benar. Kelulusan pemeriksaan kontras tersebut tidak menyembunyikan satu kesalahan fiksi di atas.

## Sepuluh field kosong yang terisi berlebih

| ID | Field | Prediksi |
| --- | --- | --- |
| FINAL084-FLOOD-08 | impacts | ["menyebabkan dua warga meninggal"] |
| FINAL084-FLOOD-10 | location_text | "halaman rumah" |
| FINAL084-EARTHQUAKE-03 | affected_objects | ["bangunan"] |
| FINAL084-FIRE-07 | impacts | ["membuat dua penghuni terluka"] |
| FINAL084-FIRE-09 | involved_parties | ["seluruh penghuni selamat"] |
| FINAL084-ACCIDENT-03 | affected_objects | ["kendaraan"] |
| FINAL084-NON_EVENT-01 | impacts | ["memimpin"] |
| FINAL084-NON_EVENT-05 | impacts | ["membatalkan"] |
| FINAL084-NON_EVENT-05 | affected_objects | ["Gudang Weningjati"] |
| FINAL084-NON_EVENT-09 | impacts | ["membuka loket"] |

Pola yang tersisa mencakup pengulangan frasa luka/meninggal ke dampak, objek yang sekadar diperiksa atau dipakai dalam pengaturan lalu lintas, frasa umum yang terbaca sebagai lokasi, serta aktivitas nonkejadian yang terbaca sebagai dampak. Ini diagnosis dari keluaran tersimpan, bukan perubahan gold atau implementasi.

Pada denominator tetap 174, batas 5% mengizinkan paling banyak delapan field kosong terisi. Sembilan masih 5,17%; delapan menjadi 4,60%. Perhitungan ini menjelaskan kegagalan metrik dan tidak mengizinkan penghapusan kesalahan atau perubahan acuan setelah hasil diketahui.

## Bukti dan batas kesimpulan

Notebook 31 benar-benar dieksekusi melalui CPython cell executor dan salinan `_executed` menyimpan stream serta metadata. Acuan manusia divalidasi dan dibekukan; 21 file terikat disalin sebelum pemuatan kedua model. Identitas arsip dan runtime diverifikasi. Inferensi SENA serta NARA berjalan pada seluruh 50 narasi tanpa pemotongan; 692 token diproses. Penghitungan ulang memakai prediksi tersimpan mereproduksi hasil secara identik.

Tidak ada pelatihan, perubahan bobot, penyesuaian adapter, penurunan target, atau perubahan cutoff pada tahap penerimaan ini. SENA tetap v0.8.4 dan NARA tetap reviewed pilot 20261018. Hasil lama pada 200 narasi merupakan regresi development; hasil FINAL084 ini adalah pengujian pertama pada 50 narasi baru yang sudah direview. Dua putaran tersebut tidak disamakan.

Pilot sintetis buatan asisten dengan review manusia ini bukan sampel lapangan acak yang representatif. Exact overlap terhadap sumber tersedia sudah diperiksa sebelum pengujian; independensi semantik dan keanggotaan seluruh training awal belum terbukti. Eksekusi memakai CPU representatif dan bukan verifikasi target VM/backend submission. Bukti 91 uji kontrak aktif sebelumnya tetap tersedia; kode terikat tidak berubah dan suite tidak dijalankan ulang tanpa kebutuhan.

## Kelanjutan

Prioritas perbaikan berikutnya adalah presisi field NARA, terutama sepuluh sel di atas, sambil menjaga dampak, korban dan objek yang benar. Satu false event pada cerita juga tetap menjadi catatan pengembangan. Pada checkpoint ini FINAL084 belum dipakai melatih atau memilih ulang kandidat dan belum dipensiunkan menjadi development. Jika hasilnya dipakai mengubah kandidat, pensiunkan set terlebih dahulu, pertahankan hasil pertama ini, dan gunakan acuan manusia baru untuk penerimaan berikutnya.

Persetujuan mutu, Done dan deployment tetap false. Kategori hanya dari SENA; NON_EVENT memblokir submission dan verifikasi manusia tetap wajib. Acuan PENDING dalam template merupakan usulan historis; sumber APPROVED yang benar-benar diuji berada pada `evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/reviewed_bundle_frozen.json`.
