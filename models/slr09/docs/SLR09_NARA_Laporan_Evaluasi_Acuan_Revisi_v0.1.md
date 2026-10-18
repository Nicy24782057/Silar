# SLR09 — Evaluasi NARA terhadap acuan revisi v0.1

**Workflow:** validasi Excel → tentukan cakupan sesuai status review → cocokkan prediksi run tetap → hitung token/span dan matriks → analisis hasil.

**Status: PARTIAL_APPROVED_SUBSET_NOT_FULL_80.** Sampel awal 80 narasi/1718 token. Yang dinilai: **79 narasi/1701 token**, dengan 1 narasi/17 token belum disetujui. Hasil ini tidak disebut sebagai evaluasi penuh 80 narasi.

## Hasil utama

Prediksi kandidat fine-tune lebih sesuai dengan acuan revisi pada subset yang disetujui. Macro F1 non-O meningkat dari **53,43% menjadi 79,32%**, atau **+25,89 poin persentase**. Ini merupakan evaluasi ulang prediksi yang telah tersimpan, tanpa melatih model atau menjalankan inferensi neural baru.

| Metrik terhadap acuan revisi | NARA v1 | Fine-tune | Selisih (poin persentase) |
| --- | --- | --- | --- |
| Akurasi token | 65,73% | 81,42% | +15,70 |
| Precision macro non-O | 71,66% | 82,05% | +10,39 |
| Recall macro non-O | 48,47% | 77,53% | +29,07 |
| Macro F1 non-O | 53,43% | 79,32% | +25,89 |
| Micro F1 non-O | 53,82% | 78,96% | +25,13 |
| Weighted F1 non-O | 50,97% | 79,10% | +28,14 |
| F1 span tepat | 43,69% | 63,84% | +20,15 |

Macro F1 memakai seluruh 14 label non-O dengan bobot sama per label. Akurasi token memasukkan O. Kesalahan dari/ke O tetap memengaruhi precision dan recall role. F1 span menuntut label dan batas token tepat untuk span flat yang kontigu; format ini tidak dianggap BIO. Semua 1701 token sumber tercakup dan tidak ada narasi dinyatakan terpotong dalam metadata inferensi. Teks sumber yang memang berhenti di tengah kalimat tetap dinilai sebagaimana tertulis, terpisah dari truncation oleh batas input model.

## Validasi review

Reviewer: **bintang**. Pada 1718 token dalam Excel: label kosong 0, label tidak dikenal 0, dan normalisasi huruf 0. ID, teks, token sumber, posisi token, dan daftar label cocok dengan paket uji terkunci. Workbook pengguna tidak diubah.

Dari 80 narasi, 79 berstatus APPROVED dan 1 masih DEFERRED. Validator evaluasi penuh tetap menyatakan belum siap. Analisis ini membaca hanya acuan yang telah disetujui dan mencatat kasus yang tidak dinilai; tidak membuat gold penuh 80, tidak mengganti kasus dengan sampel lain, dan tidak mengubah DEFERRED menjadi APPROVED.

| ID review | ID sumber | Status | Token | Catatan reviewer |
| --- | --- | --- | --- | --- |
| UJI-019 | GEM-00141 | DEFERRED | 17 | Belum jelas apakah klausa gempa menyatakan kejadian atau andaian. Akhir terpotong; label FALSE sementara. |

> begitu gempa bumi melanda lelaki macho dengan tato kapak di sekujur tubuhnya bisa lekas sembunyi di balik

Label sementara kasus ini tidak dipakai untuk skor. Status DEFERRED dipertahankan sesuai file yang dikirim; belum ada keputusan pengguna yang mengubahnya.

Proporsi kelompok sumber pada subset yang dinilai: BAN 20, GEM 19, KEB 20, KEC 20. Kelompok sumber adalah asal pengumpulan narasi, bukan kategori kejadian final SENA. Keputusan menunda kasus ambigu dapat memengaruhi karakter subset; cakupan dan pengecualiannya harus tetap dilaporkan.

## Dampak perubahan anotasi pada narasi yang sama

Untuk memeriksa pengaruh acuan, kedua prediksi tetap juga dinilai terhadap label historis pada **subset narasi yang sama**:

| Acuan pada subset yang sama | Macro F1 NARA v1 | Macro F1 fine-tune |
| --- | --- | --- |
| Historis | 71,55% | 56,23% |
| Review pedoman 0.2 | 53,43% | 79,32% |

Review mengubah label **625 dari 1701 token** (36,74%). Proporsi non-O pada acuan naik dari 34,45% menjadi 56,91%. Perubahan ini membalik urutan performa dua model pada subset yang sama. Ini merupakan bukti langsung bahwa ketidakcocokan anotasi memengaruhi penilaian pada subset ini. Bukti tersebut tidak menetapkan bahwa seluruh penurunan pada test historis disebabkan oleh perubahan anotasi, dan tidak menghasilkan estimasi untuk 1.000 acuan revisi.

| Perubahan label historis → revisi | Token |
| --- | --- |
| O → INFORMATION-ARG | 140 |
| O → OFFICER-ARG | 96 |
| O → PLACE-ARG | 69 |
| O → TIME-ARG | 57 |
| INFORMATION-ARG → O | 32 |
| STREET-ARG → PLACE-ARG | 26 |
| O → STREET-ARG | 24 |
| FALSE-EVENT → EARTHQUAKE-EVENT | 22 |

Test historis 1.000 narasi tetap memiliki macro F1 **67,77% → 58,56%**. Hasil historis tersebut tetap dipertahankan dalam pelaporan bersama hasil revisi; keduanya mengukur kesesuaian terhadap acuan yang berbeda.

## Rincian per label

| Label | Token acuan | Narasi dengan label | F1 NARA v1 | F1 fine-tune |
| --- | --- | --- | --- | --- |
| O | 733 | 79 | 75,77% | 84,46% |
| ACCIDENT-EVENT | 22 | 17 | 77,78% | 80,95% |
| AFFECTEDOBJECTS-ARG | 60 | 23 | 63,16% | 79,25% |
| DEATHVICTIM-ARG | 12 | 4 | 86,96% | 90,91% |
| EARTHQUAKE-EVENT | 37 | 15 | 60,38% | 98,63% |
| FALSE-EVENT | 29 | 15 | 41,67% | 64,29% |
| FIRE-EVENT | 23 | 18 | 80,00% | 85,11% |
| FLOOD-EVENT | 24 | 18 | 40,00% | 86,36% |
| INFORMATION-ARG | 170 | 47 | 16,22% | 57,76% |
| OFFICER-ARG | 140 | 40 | 28,74% | 82,84% |
| PLACE-ARG | 269 | 64 | 73,20% | 88,17% |
| REASON-ARG | 13 | 3 | 28,57% | 33,33% |
| STREET-ARG | 70 | 14 | 74,17% | 82,19% |
| TIME-ARG | 94 | 30 | 46,40% | 80,66% |
| WOUNDVICTIM-ARG | 5 | 2 | 30,77% | 100,00% |

Dukungan setiap label dilaporkan pada tabel; denominator macro F1 tetap seluruh 14 non-O. WOUND memiliki F1 100,00%, dengan dukungan **5 token pada 2 narasi**. Ini belum membuktikan penguasaan seluruh variasi luka/kondisi fisik dan tidak membatalkan kegagalan kasus sesak nafas pada validasi terdahulu. Label REASON masih lemah: F1 **33,33%**, dengan 13 token acuan. INFORMATION memiliki F1 **57,76%** dan FALSE-EVENT **64,29%**.

## Kesalahan yang masih terlihat

Berdasarkan jumlah token salah per narasi: **61 membaik, 7 memburuk, dan 11 tetap**. Ukuran ini adalah perbandingan jumlah kesalahan token, bukan skor exact seluruh narasi.

| Acuan → prediksi fine-tune | Token salah |
| --- | --- |
| INFORMATION-ARG → O | 64 |
| O → INFORMATION-ARG | 43 |
| OFFICER-ARG → O | 26 |
| TIME-ARG → O | 18 |
| PLACE-ARG → O | 17 |
| O → PLACE-ARG | 13 |
| PLACE-ARG → STREET-ARG | 13 |
| O → TIME-ARG | 12 |

Pada INFORMATION, sebagian informasi masih hilang menjadi O dan sebagian token O justru diberi INFORMATION. Ini mendukung pemeriksaan batas frasa dan arti hasil ekstraksi pada integrasi berikutnya. Token berlabel INFORMATION tidak otomatis membuktikan nilai field impacts sudah benar.

7 narasi dengan jumlah kesalahan token bertambah:

| ID review | Token salah NARA v1 | Token salah fine-tune | Catatan reviewer |
| --- | --- | --- | --- |
| UJI-002 | 3 | 6 | Pembahasan antisipasi tanpa kecelakaan tertentu. Jalan dan musim disebut secara umum. |
| UJI-010 | 4 | 5 | Magnitudo 51 mengikuti teks sumber dan tidak dianggap dampak. Mengguncang menjadi informasi. |
| UJI-012 | 3 | 5 | Lahan tidak produktif adalah frasa objek; kata tidak tidak menyangkal kebakaran. |
| UJI-018 | 0 | 1 | Tragis tidak menyatakan kondisi atau jumlah korban tertentu. |
| UJI-028 | 0 | 8 | Pembahasan penyebab retakan secara umum. Tidak ada gempa atau tembok tertentu yang dilaporkan terdampak. |
| UJI-047 | 4 | 7 | Harapan/andaian berbahasa Jawa. Tidak ada kebakaran atau kondisi korban yang ditegaskan terjadi. |
| UJI-051 | 1 | 6 | Nasihat keselamatan umum. Risiko 60% bukan jumlah korban atau dampak kecelakaan tertentu. |

## Batas kesimpulan dan langkah berikutnya

1. Ini evaluasi parsial pada 79 narasi yang disetujui dari sampel test historis yang pernah dievaluasi. Tidak disebut test baru yang sepenuhnya belum pernah digunakan.
2. Sampling ditetapkan tanpa prediksi, skor kesalahan, atau label role historis. Review disusun tanpa menampilkan label lama dan prediksi pada workbook.
3. Data test NARA terpisah dari seluruh train/validation NARA asli dan tidak dipakai fine-tune/pemilihan epoch. Keterpisahan gabungan terhadap pelatihan SENA tidak dibuktikan oleh paket ini.
4. Hasil adalah token dan span NARA. Tujuh field A4.22, SENA, fusion, foto, threshold, dan deployment tidak dievaluasi ulang di sini.
5. Prediksi dibaca dari run Colab tetap. Pemeriksaan langsung bobot ekspor baru belum dilakukan; identitas bobot mengikuti manifest run yang hash arsip laporannya diverifikasi.
6. Sampel kecil dan satu reviewer membatasi kesimpulan luas. Dukungan role langka harus dibaca bersama F1, terutama WOUND.

Hasil ini mendukung kandidat fine-tune sebagai model yang lebih selaras dengan pedoman revisi pada subset tersebut. Status model produksi belum ditetapkan. Tahap selanjutnya yang disarankan adalah pemeriksaan integrasi kandidat NARA dengan adapter tujuh field, terutama batas impacts, pihak, waktu, dan penyebab, menggunakan artefak diagnostik yang telah tersedia. UJI-019 tetap terbuka sampai ada keputusan reviewer; hasil 80 narasi penuh baru dapat dihitung setelahnya.

## Artefak dan reproduksi

Notebook `SLR09_NARA_Evaluasi_Acuan_Revisi_v0.1.ipynb` berisi kode evaluasi lengkap. Notebook memakai snapshot Excel review dan data terkunci, lalu membaca ZIP hasil prediksi yang sudah ada di Drive. Tidak memerlukan bobot model atau GPU. Hasil pada folder results sudah dihitung dalam pemeriksaan ini; menjalankan notebook bersifat reproduksi.

Paket kode lengkap menyertakan validator asli tanpa perubahan, metrik token/span, kode evaluasi dan laporan, snapshot input, provenance, tabel kesalahan, dua confusion matrix, grafik F1 per label, serta pemeriksaan independen metrik. Label review dan status dalam workbook unggahan dipertahankan byte-identik.

SHA-256 Excel review: `2fedd29e14663f9cc129ca9f0b43b2244e480e51d134c1dea77a1b913910e3e9`.
SHA-256 ZIP hasil run: `879b3205419a9897075145a64c94e29c1f3b81b558af170a8181f55fdfa63bfb`.
