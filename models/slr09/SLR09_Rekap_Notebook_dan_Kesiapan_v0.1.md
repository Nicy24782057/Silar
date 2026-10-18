# SLR09 - Rekap notebook dan kesiapan aset v0.1

**Revisi setelah hasil fine-tuning SENA dan keputusan threshold - 18 Oktober 2026.**

**Pembaruan rekap NARA:** tabel sebelum/sesudah fine-tuning dilengkapi untuk acuan revisi, validation pilot, dan test historis.

**Letak dokumen di repository:** `docs/ai/slr09/SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md`. Path relatif seperti `config/`, `results/`, `code/`, `data/` dan `evidence/` pada bagian lama laporan dihitung dari `models/slr09/`; tabel lokasi NARA di bawah memakai path lengkap dari root repository.

**Workflow:** gunakan hasil training yang sudah selesai -> catat pilihan cutoff pengguna -> periksa kontrak konfigurasi Fusion -> gunakan paket untuk SLR11.

## Status saat ini

Pelatihan/fine-tuning NARA dan SENA telah selesai menurut dua laporan Colab yang diterima. Analisis saat ini memakai prediksi tersimpan; tidak menjalankan training atau inferensi baru. Hasil NARA sebelumnya dipertahankan. Paket berisi seluruh notebook sumber, notebook fine-tuning, metrik, confusion matrix, kurva, data review dan kode lengkap.

Model baru disajikan sebagai **kandidat integrasi**, belum dipromosikan menjadi model produksi. Pengguna telah memilih **A (cutoff 0,95)** untuk konfigurasi kandidat integrasi. Parameter tersimpan dan terikat pada identitas SENA hasil evaluasi; konfigurasi belum diterapkan pada aplikasi. Acuan Teknis, PRD, anotasi, status TUNDA/DEFERRED dan model aktif proyek lama tidak diubah.

## SENA: hasil run yang sudah selesai

Run 20261018T044447_926664Z; PREPARE/FINE_TUNE/EVALUATE/EXPORT berstatus SUCCEEDED. Menggunakan 110 train dan 620 validation hasil review, GPU Tesla T4, Transformers 4.57.1. Training berlangsung 6 epoch/42 optimizer steps; checkpoint terbaik adalah step 28 pada **epoch 4**, bukan checkpoint epoch terakhir. Early stopping berhenti setelah dua epoch tanpa peningkatan macro F1. Waktu training tercatat 68,427 detik, bukan benchmark backend atau VM tujuan.

| Metrik pada 620 validation yang sama | SENA v1 | Fine-tune |
| --- | --- | --- |
| Accuracy | 64,03% | 88,06% |
| Macro F1 lima kelas | 65,75% | 88,07% |
| Weighted F1 | 65,67% | 87,77% |
| Prediksi sesuai acuan | 397/620 | 546/620 |
| Kejadian diprediksi NON_EVENT | 213/489 | 28/489 |
| NON_EVENT diprediksi kejadian | 10/131 | 45/131 |
| Salah kategori antarjenis kejadian | 0 | 1 |

Accuracy meningkat 24,03 poin persentase dan macro F1 meningkat 22,32 poin persentase. Pada pasangan narasi yang sama: **184 membaik, 35 memburuk, 362 tetap benar, 39 tetap salah**. Jumlah kesalahan total turun 223 menjadi 74. Kenaikan false event tetap merupakan regresi penting, bukan hasil yang dihapus demi skor total.

| Kategori | Jumlah acuan | F1 SENA v1 | F1 fine-tune |
| --- | --- | --- | --- |
| FLOOD | 131 | 53,55% | 86,47% |
| EARTHQUAKE | 108 | 53,69% | 92,98% |
| FIRE | 141 | 81,48% | 95,77% |
| ACCIDENT | 109 | 88,00% | 94,93% |
| NON_EVENT | 131 | 52,04% | 70,20% |

Model lebih banyak mengenali kejadian yang dirujuk dalam berita, bantuan atau komentar. NON_EVENT masih menjadi batas lemah, dengan F1 70,20%. Contoh false event yang tetap dipertahankan sesuai review: KEC-01395 (statistik kecelakaan mudik), KEB-00598 (edukasi penyebab/penanggulangan kebakaran), BAN-01074 (pencegahan), dan GEM-01398 (lelucon umum). KEC-00351 masih salah NON_EVENT pada komentar yang merujuk kecelakaan tertentu. GEM-01229 salah memilih EARTHQUAKE saat acuan menetapkan ACCIDENT sebagai kejadian utama.

Keterangan contoh merupakan penelaahan terhadap label final yang sudah ada; tidak membuat anotasi baru atau mengubah kategori agar sesuai prediksi. Seluruh 74 kesalahan beserta confidence tersimpan pada results/sena_finetune_20261018T044447_926664Z/classification_errors.json; perubahan seluruh 620 prediksi ada pada prediction_transitions.csv.

**Batas metrik:** 620 narasi merupakan validation yang digunakan memilih checkpoint. Ini bukan test independen. Kandidat split historis SENA belum terbukti bebas dari training checkpoint awal. Tiga validation TUNDA tetap dikeluarkan. Test resmi tidak digunakan dalam fine-tune ini, dan tidak ada klaim skor test baru. Baseline memakai prediksi yang sudah selesai; inferensi baseline tidak diulang.

## Cutoff confidence kandidat integrasi

Pengguna telah memilih **A (cutoff 0,95)** untuk konfigurasi kandidat integrasi. Parameter tersimpan dan terikat pada identitas SENA hasil evaluasi; konfigurasi belum diterapkan pada aplikasi.

| Cutoff | Ditandai confidence rendah | Kesalahan yang ditandai | Kesalahan masih di kelompok atas | Accuracy teramati pada kelompok atas |
| --- | --- | --- | --- | --- |
| 0,90 | 102 (16,45%) | 38/74 | 36 | 93,05% |
| 0,95 | 153 (24,68%) | 51/74 | 23 | 95,07% |
| 0,99 | 437 (70,48%) | 72/74 | 2 | 98,91% |

Angka kelompok atas bersifat kondisional pada validation yang sama. Memilih cutoff tidak mengubah accuracy keseluruhan 88,06% atau memperbaiki 74 label yang salah. Kebenaran suatu prediksi tidak dijamin oleh confidence, dan 0,95 tidak berarti model pasti benar 95%.

**A. Cutoff 0,95 - dipilih pengguna untuk kandidat integrasi.** Menandai 153/620 narasi, mencakup 51/74 kesalahan dan menyisakan 23 kesalahan pada kelompok atas. Sebanyak 102 prediksi yang sebenarnya sesuai acuan ikut mendapat tanda. Kelebihannya lebih banyak kesalahan mendapat perhatian; konsekuensinya tanda uncertain lebih sering muncul. Tambahan 51 tanda dibanding 0,90 mencakup 13 kesalahan tambahan; ini pilihan pertukaran pada hasil yang terlihat, bukan optimasi atau jaminan pada data baru.

**B. Cutoff 0,90.** Menandai 102/620 narasi, mencakup 38/74 kesalahan, dan menyisakan 36 kesalahan pada kelompok atas. Sebanyak 64 prediksi yang benar ikut ditandai. Tanda lebih sedikit, dengan lebih banyak kesalahan ber-confidence tinggi tersisa.

Cutoff 0,99 disertakan sebagai pembanding: 437/620 ditandai (70,48%), mencakup 72/74 kesalahan tetapi juga 365 prediksi benar. Proporsi tanda yang besar menjadi alasan tidak menempatkannya sebagai rekomendasi awal.

Perhitungan tanda di tabel hanya LOW_CLASSIFICATION_CONFIDENCE. Kemampuan mendeteksi konflik ekstraksi umum tidak diklaim. Aturan tetap: confidence **di bawah** cutoff diberi tanda; nilai sama dengan cutoff berada pada kelompok atas. **Semua** prediksi NON_EVENT tetap memblokir pengiriman, termasuk yang ber-confidence rendah. Semua laporan tetap membutuhkan Human Verification. Tanda uncertain tidak mengubah kategori atau mempublikasikan laporan otomatis.

File config/threshold_decision.json menyimpan instruksi pengguna, dan config/threshold_options.json mencatat selected_option=A serta perbandingan opsi. activated=false berarti belum diterapkan pada aplikasi, bukan berarti pilihan belum dicatat. File **config/SLR09_Konfigurasi_Integrasi_v0.1.json** menyediakan confidence_threshold=0.95 dan calibration_reference yang terikat pada run, hash bobot serta laporan SENA. Builder membaca keputusan ini sehingga pembaruan paket tidak mengembalikan pilihan menjadi null.

calibration_reference adalah rujukan pengukuran, bukan bukti kalibrasi probabilitas. Pemilihan cutoff tidak melakukan temperature scaling atau metode kalibrasi baru. Tidak ada target mutu numerik baru yang dibuat seolah-olah disepakati sebelum melihat skor. Penerimaan kandidat beserta batas metrik masih memerlukan review kelompok.

## Pemeriksaan kontrak konfigurasi Fusion

code/verify_selected_fusion_config.py memakai fixture buatan untuk memeriksa batas 0,949, 0,950 dan 0,951, blokir NON_EVENT, kategori dari SENA, serta guard konfigurasi tanpa threshold/referensi. Field kosong saja tidak membuat uncertain. Kewajiban Human Verification dipertahankan dalam konfigurasi; penerapannya oleh backend belum dibuktikan oleh pemeriksaan fungsi ini.

Hasil pemeriksaan terdapat pada evidence/selected_threshold_contract_checks.json. Ini pemeriksaan aturan dan konsistensi konfigurasi, bukan inferensi model atau tambahan skor evaluasi neural. Tidak ada training, pengujian ulang NARA, atau inferensi SENA yang diulang.

## NARA dan adapter: hasil yang dipakai kembali

| Bagian | Hasil | Cakupan |
| --- | --- | --- |
| Fine-tune NARA | 157 train/41 validation; validation macro F1 78,65% | Validation memilih checkpoint; bukan test independen. |
| Evaluasi acuan revisi | Macro F1 non-O 53,43% -> 79,32%; exact span F1 43,69% -> 63,84% | 79 narasi/1.701 token; UJI-019 DEFERRED. |
| Test historis | Macro F1 67,77% -> 58,56% | 1.000 narasi dengan label historis; hasil tetap dicatat. |
| Tujuh field A4.22 | 66/84 -> 73/84 cocok; 13 membaik, 6 memburuk | 12 diagnostik dikenal, nilai kosong ikut dihitung. |

### Perbandingan lengkap NARA sebelum dan sesudah fine-tuning

Metrik berikut dibaca dari hasil evaluasi yang telah selesai. Tidak ada pelatihan, inferensi, atau perubahan anotasi baru untuk melengkapi rekap ini. Setiap tabel memakai cakupan data dan acuan labelnya sendiri; angka antartabel tidak digabung menjadi satu skor.

#### Evaluasi terhadap acuan revisi: 79 narasi / 1.701 token

NARA v1 dan hasil fine-tuning dibandingkan terhadap acuan review final yang sama, mengikuti pedoman nara-role-guideline-0.2. Dari 80 narasi yang direview, satu narasi UJI-019 / GEM-00141 tetap DEFERRED dan tidak dihitung. Ini merupakan hasil pada subset beracuan revisi, bukan evaluasi penuh 80 narasi atau revisi seluruh test historis 1.000 narasi.

| Metrik | Sebelum fine-tuning (NARA v1) | Sesudah fine-tuning |
| --- | --- | --- |
| Akurasi token | 65,73% | 81,42% |
| Precision macro non-O | 71,66% | 82,05% |
| Recall macro non-O | 48,47% | 77,53% |
| Macro F1 non-O | 53,43% | 79,32% |
| Micro F1 non-O | 53,82% | 78,96% |
| Weighted F1 non-O | 50,97% | 79,10% |
| F1 span tepat | 43,69% | 63,84% |

Metrik non-O menghitung 14 label role selain O. Akurasi token menghitung seluruh token, termasuk label O. F1 span tepat menghitung kecocokan label dan batas span secara utuh. Macro F1 non-O meningkat 25,89 poin persentase, sedangkan F1 span tepat meningkat 20,15 poin persentase pada subset ini.

#### Validation pilot saat fine-tuning: 41 narasi

Validation ini digunakan memilih checkpoint dalam run pelatihan NARA. Cakupannya berbeda dari evaluasi 79 narasi di atas dan bukan test independen.

| Metrik | Sebelum fine-tuning (NARA v1) | Sesudah fine-tuning |
| --- | --- | --- |
| Akurasi token | 57,14% | 77,57% |
| Macro F1 non-O | 49,28% | 78,65% |

#### Test historis: 1.000 narasi dengan label asli

Hasil pada label historis tetap disajikan agar regresi dapat ditelusuri. Acuan label 1.000 narasi ini belum diselaraskan seluruhnya dengan pedoman revisi; hasilnya tidak menggantikan evaluasi acuan revisi 79 narasi dan tidak boleh disajikan sebagai skor test beracuan revisi.

| Metrik | Sebelum fine-tuning (NARA v1) | Sesudah fine-tuning |
| --- | --- | --- |
| Akurasi token | 86,25% | 68,15% |
| Macro F1 non-O | 67,77% | 58,56% |

Perbandingan menunjukkan peningkatan pada acuan revisi yang telah direview dan penurunan pada acuan historis. Keduanya tetap dicatat; hasil ini tidak menyatakan bahwa semua metrik atau seluruh jenis narasi membaik.

#### Lokasi laporan, confusion matrix dan rincian metrik NARA

Path berikut dihitung dari root repository sesuai penempatan paket di models/slr09/.

| Bukti | Path repository |
| --- | --- |
| Laporan evaluasi acuan revisi lengkap | `models/slr09/docs/SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md` |
| Angka lengkap sebelum/sesudah pada acuan revisi | `models/slr09/results/nara_reviewed_79/evaluation.json` |
| Metrik per label | `models/slr09/results/nara_reviewed_79/per_label.csv` |
| Confusion matrix sebelum fine-tuning | `models/slr09/results/nara_reviewed_79/baseline_confusion_matrix.png` |
| Confusion matrix sesudah fine-tuning | `models/slr09/results/nara_reviewed_79/finetuned_confusion_matrix.png` |
| Grafik F1 per label sebelum/sesudah | `models/slr09/results/nara_reviewed_79/f1_per_label.png` |
| Perbandingan validation pilot, test historis dan diagnostik adapter | `models/slr09/evidence/nara_finetune/comparison.json` |

Buka [laporan NARA lengkap](../../../models/slr09/docs/SLR09_NARA_Laporan_Evaluasi_Acuan_Revisi_v0.1.md), [confusion matrix sebelum](../../../models/slr09/results/nara_reviewed_79/baseline_confusion_matrix.png), [confusion matrix sesudah](../../../models/slr09/results/nara_reviewed_79/finetuned_confusion_matrix.png), dan [grafik F1 per label](../../../models/slr09/results/nara_reviewed_79/f1_per_label.png). Hasil tersebut sudah tersedia di paket; notebook tidak perlu dijalankan ulang untuk membacanya.

Regresi NARA tetap dicatat: time_text 12/12 -> 10/12 dan impacts 6/12 -> 5/12. INFORMATION, batas frasa waktu, lokasi/objek dan kasus sesak nafas masih mempunyai keterbatasan. WOUND F1 100% pada subset 79 hanya didukung lima token pada dua narasi. Seluruh occurred_at diagnostik null; kecocokannya tidak membuktikan parser tanggal berisi.

Tidak ada replay adapter, evaluasi NARA, training NARA atau perubahan aturan baru pada pembaruan ini. Hasil berasal dari artefak yang telah diperiksa. Raw NARA tetap 15 label flat; kategori final dari SENA. Skema ekstraksi tetap location_text, time_text, occurred_at, involved_parties, impacts, victims, affected_objects. REASON tidak dijadikan field produk baru. Informasi tak ditemukan tetap null atau array kosong.

## Identitas kandidat dan batas pemeriksaan bobot

| Komponen | Kandidat/versi |
| --- | --- |
| SENA | SILAR_SENA_reviewed_pilot_20261018T044447_926664Z.zip |
| NARA | SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip |
| Adapter | silar-adapter-0.4.0 |
| Guard korban | silar-victim-guard-0.4.0 |
| Pedoman NARA | nara-role-guideline-0.2 |
| Aturan Fusion | silar-fusion-a4.22-0.1.0 |

SHA bobot SENA: 9512a4895de281f3696e6c53a86d1271ad45180339995af01cf2b886ddc0afad. SHA bobot NARA: ef84ccfeca2d116942c5d7f8882e064192279eabf92127e8adc1741933b60c29. Identitas mengikuti manifest ekspor Colab; bobot besar tidak dibuka langsung pada pemeriksaan ini. Reload SENA pada tiga contoh dilaporkan cocok oleh run Colab. Perbandingan kinerja tujuh field untuk gabungan kedua model baru belum dijalankan; angka 73/84 sebelumnya memakai SENA lama yang tetap sebagai komponen diagnostik.

config/model_candidates.json menyimpan label, versi, hash dan status CONFIGURED_FOR_SLR11_NOT_DEPLOYED. Parameter pilihan tersedia untuk pemanggilan Fusion pada tahap integrasi. Pemilihan threshold tidak mengubah status model produksi, persetujuan mutu, atau bukti pemuatan pada VM tujuan.

## Kesiapan terhadap card SLR09

| Bagian | Status dan bukti |
| --- | --- |
| Aset/provenance/label | Sumber, label dan hash tersedia; bukti bobot baru mengikuti manifest Colab. |
| Data/anotasi/preprocessing/split | Data review dan kode tersedia; NARA memiliki ID split; keterbatasan split historis SENA dicatat. |
| Pelatihan dan evaluasi | Kedua fine-tune selesai. Metrik, kurva, matriks dan contoh kesalahan tersedia, dengan pemisahan validation/test. |
| Pemetaan NARA/adapter A4.22 | Kode dan hasil diagnostik tersedia; seluruh regresi dan batas cakupan tetap dilaporkan. |
| Target mutu dan penerimaan | Belum ada angka penerimaan final yang disepakati; kandidat dan tradeoff siap ditinjau kelompok. |
| Threshold/ambiguity | A (0,95) dikunci untuk kandidat integrasi; kontrak batas dan guard diperiksa. Belum diterapkan pada aplikasi. Deteksi konflik umum tidak diklaim. |
| Kesiapan pemuatan | Baseline telah berjalan di CPU notebook; reload kandidat dilaporkan di T4. Belum bukti pemuatan/joint inference kedua kandidat pada VM tujuan. |
| Versioning/commit | Paket, versi dan hash siap. Commit/LFS serta review penerimaan kelompok belum dilakukan di sini. |

**Usulan status: In Review untuk meninjau hasil dan konfigurasi kandidat; belum menandai Done.** Ini usulan dokumentasi, bukan perubahan card GitHub. Kriteria yang masih terbuka berasal dari card asli, bukan penambahan fitur atau kewajiban baru. Integrasi backend dan benchmark sistem penuh tetap berada pada SLR11/SLR15; kesiapan aset pada lingkungan tujuan tetap perlu dibuktikan sesuai ruang lingkupnya.

## Urutan artefak dan notebook

Urutan dokumen proyek tetap laporan perancangan -> hasil revisi -> penyempurnaan Acuan Teknis SLR04/desain 0.3 -> pemetaan MEET05. PRD tidak direvisi oleh pekerjaan ini. Notebook bernomor menyatakan alur ketergantungan, bukan tanggal pasti seluruh eksperimen historis.

| Notebook | Fungsi dan keadaan |
| --- | --- |
| 00_SLR09_Hasil_Terverifikasi.ipynb | Ringkasan terkini kedua model, adapter dan cutoff terpilih; membaca hasil tersimpan. |
| 01_SENA_Pelatihan_Awal.ipynb | Kode V3A utuh; sumber asli tidak menyimpan output training. |
| 02_NARA_Pelatihan_Awal.ipynb | Kode V2 utuh beserta output historis sumber. |
| 03_NARA_FineTune_dan_Evaluasi.ipynb | Kode eksperimen NARA yang telah selesai. |
| 04_NARA_Evaluasi_Acuan_Revisi.ipynb | Kode evaluasi 79 narasi yang telah selesai. |
| 05_SILAR_Inferensi_Baseline_dan_Kalibrasi.ipynb | Dokumentasi runner baseline lama, bukan runner gabungan kandidat baru. |
| 06_SENA_Evaluasi_620_Review.ipynb | Analisis SENA v1 pada seluruh review final. |
| 07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb | Kode fine-tune yang run-nya sudah diterima; hasil run dicantumkan terpisah dari sel training sumber. |
| 08_SENA_Analisis_Hasil_dan_Threshold.ipynb | Analisis hasil SENA baru, transisi kesalahan dan cutoff; tanpa model. |

**Seluruh hasil pada tahap ini sudah tersedia. Notebook 01-07 tidak perlu dijalankan ulang.** Kode sel sumber dipertahankan; nama historis TanggapMakna menunjukkan asal, sedangkan notebook utama memakai SENA/NARA. historical/ menyimpan feasibility, local evaluation dan Fusion/blind lama. Completeness Engine atau aturan status historis tidak diaktifkan menjadi fitur SILAR.

## Sumber/lisensi dan reproduksi

Dataset Semantic Role Labeling Datasets for Crisis Event, Ariyanto dkk., halaman Mendeley V2 DOI 10.17632/r76v5sjyv2.2 menyatakan CC BY 4.0. Model card indolem/indobert-base-uncased menyatakan MIT. Pemeriksaan sumber resmi tercatat 18 Oktober 2026. Identitas byte dataset mengikuti asset_lock, bukan asumsi kesamaan arsip terhadap versi halaman publik. Tidak menetapkan lisensi baru untuk proyek.

- https://data.mendeley.com/datasets/r76v5sjyv2/2
- https://huggingface.co/indolem/indobert-base-uncased

ZIP laporan SENA yang diterima tersimpan byte-identik di sources/. SHA-256: 0077365fac8b70d4c624958bbcef60978aab41cf50978bd78f8154c9bdbf691f. code/analyze_sena_completed_run.py mereproduksi analisis dari prediksi tersebut; field confidence_threshold_selected=null di snapshot analisis mencerminkan keadaan sebelum keputusan pengguna. Konfigurasi terkini dibaca dari config/, tanpa menimpa catatan hasil run lama. code/update_package_after_sena.py memperbarui ringkasan tanpa model. code/verify_selected_fusion_config.py memeriksa konfigurasi terpilih. code/qa_package.py memeriksa notebook/snapshot; code/finalize_package.py membuat ZIP dan memverifikasi isi/hash. Kode builder tahap persiapan tetap ada sebagai riwayat dan meneruskan pembaruan jika sumber run selesai tersedia. Bobot besar tetap mengikuti arsip Drive yang sudah ada; tidak diperlukan unggah ulang untuk analisis ini.
