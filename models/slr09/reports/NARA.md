# NARA — model dan evaluasi FINAL084

**Pembaruan README: 21 Oktober 2026.** Hasil yang dilaporkan berasal dari pengujian FINAL084 pada 20 Oktober 2026; pembaruan ini menyajikan keluaran yang sudah tersimpan.

NARA memberi label pada token narasi untuk mengenali lokasi, waktu, pihak, dampak, korban dan objek terdampak. Pada FINAL084, NARA mencapai **macro F1 14 label non-O 85,31%** dan **exact span F1 81,86%**. Confusion matrix lengkap dan penjelasannya tersedia langsung di dokumen ini.

## 1. Peran dan identitas model

NARA menggunakan klasifikasi token berbasis BERT dengan **15 label flat**, satu label untuk setiap token acuan. Label flat tidak memakai penanda BIO; pembentukan rentang dan field ditangani kode pendamping. Kategori akhir laporan—FLOOD, EARTHQUAKE, FIRE, ACCIDENT atau NON_EVENT—ditentukan oleh SENA.

| Komponen | Identitas yang digunakan |
| --- | --- |
| Bobot NARA | `SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip` |
| Tanggal bobot | 18 Oktober 2026; bobot yang sama digunakan pada FINAL084. |
| Pipeline evaluasi | SLR09 v0.8.4. |
| Adapter | 0.5.3 |
| Postprocessing | 0.3.1 |
| Composition | 0.3.1 |
| Victim guard | 0.5.0 |
| Runtime kandidat | 0.6.5, `slr09_candidate_runtime.py`. |
| SHA-256 arsip NARA | `bce9feba0dd2ae4518880708085f44286ae8d1dd7e50f4eb452e36824f967798` |

Bobot reviewed pilot berasal dari fine-tune dengan 157 narasi train dan 41 validation. Validation tersebut dipakai memilih checkpoint. Nomor v0.8.4 di atas merujuk pada pipeline akhir; bobot NARA tidak dilatih ulang atau diberi identitas baru saat aturan penerimaan direvisi.

## 2. Keluaran yang dibentuk bersama adapter

| Field | Informasi yang disimpan |
| --- | --- |
| `location_text` | Frasa lokasi/jalan yang dinyatakan dalam narasi. |
| `time_text` | Frasa waktu yang dinyatakan dalam narasi. |
| `occurred_at` | Field waktu terstruktur dalam kontrak. Pada FINAL084 seluruh acuan dan keluarannya bernilai null; kemampuan normalisasi timestamp belum dibuktikan oleh pengujian ini. |
| `involved_parties` | Pihak yang dinyatakan terlibat. |
| `impacts` | Dampak yang dibentuk dari span informasi dan komposisi literal yang didukung aturan. |
| `victims` | Korban meninggal atau luka/kondisi fisik eksplisit yang lolos guard. |
| `affected_objects` | Benda/objek yang dinyatakan terdampak. |

Label `REASON-ARG` tetap menjadi bagian anotasi token dan tidak menambah field produk baru. `FALSE-EVENT` menunjukkan konteks penyebutan kejadian, bukan vonis hoaks. Informasi yang tidak didukung teks tetap null atau array kosong. Verifikasi manusia tetap wajib; cutoff confidence 0,95 pada pipeline berkaitan dengan klasifikasi SENA, bukan nilai macro F1 NARA.

## 3. Data evaluasi dan ringkasan metrik

FINAL084 memuat **50 narasi sintetis yang direview manusia, 692 token, dan 15 label**, termasuk O. Semua 50 narasi berstatus APPROVED. Acuan manusia serta sumber pengujian dibekukan sebelum inferensi. Satuan penilaian token berbeda dari jumlah narasi maupun jumlah span.

| Metrik | Hasil | Makna |
| --- | --- | --- |
| Macro F1 seluruh 14 label non-O | **85,31%** | Rerata F1 14 role dengan bobot sama; O dikecualikan. |
| Akurasi token, termasuk O | **86,71% — 600/692** | Diturunkan dari diagonal confusion matrix pada bagian 5. |
| Exact span precision | **77,29%** | 194/251 span prediksi tepat. |
| Exact span recall | **87,00%** | 194/223 span acuan ditemukan tepat. |
| Exact span F1 | **81,86%** | Menggabungkan precision dan recall span persis. |
| Span TP / FP / FN | **194 / 57 / 29** | Span benar / prediksi berlebih atau salah / span acuan yang terlewat. |

Akurasi token dihitung dari jumlah token yang labelnya benar. Macro F1 memberi bobot sama pada setiap role, sehingga role jarang tidak tertutup oleh dominasi O. Exact span menuntut label dan batas rentang token cocok dengan acuan. Ketiganya mengukur hal yang berbeda.

## 4. Label dan hasil per label

Kode 00–14 di kolom pertama adalah legenda baris/kolom confusion matrix. **Support adalah jumlah token acuan**, bukan jumlah narasi. O ditampilkan untuk diagnosis, tetapi tidak masuk macro F1 14 non-O.

| Kode | Label | Precision | Recall | F1 | Support |
| --- | --- | ---: | ---: | ---: | ---: |
| 00 | `O` | 97,60% | 79,48% | 87,61% | 307 |
| 01 | `ACCIDENT-EVENT` | 76,92% | 100,00% | 86,96% | 10 |
| 02 | `AFFECTEDOBJECTS-ARG` | 90,91% | 85,11% | 87,91% | 47 |
| 03 | `DEATHVICTIM-ARG` | 100,00% | 100,00% | 100,00% | 12 |
| 04 | `EARTHQUAKE-EVENT` | 90,91% | 100,00% | 95,24% | 10 |
| 05 | `FALSE-EVENT` | 100,00% | 36,36% | 53,33% | 11 |
| 06 | `FIRE-EVENT` | 71,43% | 100,00% | 83,33% | 10 |
| 07 | `FLOOD-EVENT` | 76,92% | 100,00% | 86,96% | 10 |
| 08 | `INFORMATION-ARG` | 32,88% | 72,73% | 45,28% | 33 |
| 09 | `OFFICER-ARG` | 87,50% | 100,00% | 93,33% | 28 |
| 10 | `PLACE-ARG` | 89,61% | 97,18% | 93,24% | 71 |
| 11 | `REASON-ARG` | 81,82% | 100,00% | 90,00% | 9 |
| 12 | `STREET-ARG` | 92,59% | 100,00% | 96,15% | 25 |
| 13 | `TIME-ARG` | 97,89% | 95,88% | 96,88% | 97 |
| 14 | `WOUNDVICTIM-ARG` | 75,00% | 100,00% | 85,71% | 12 |

### Arti label

| Kode | Makna operasional ringkas |
| --- | --- |
| 00 · `O` | Token di luar role khusus. |
| 01 · `ACCIDENT-EVENT` | Pemicu kecelakaan yang dinyatakan terjadi. |
| 02 · `AFFECTEDOBJECTS-ARG` | Benda/objek terdampak, termasuk kuantitasnya. |
| 03 · `DEATHVICTIM-ARG` | Korban meninggal yang disebutkan secara eksplisit. |
| 04 · `EARTHQUAKE-EVENT` | Pemicu gempa yang dinyatakan terjadi. |
| 05 · `FALSE-EVENT` | Penyebutan kejadian dalam simulasi, hipotesis, negasi atau pembahasan yang tidak menyatakan kejadian itu terjadi. |
| 06 · `FIRE-EVENT` | Pemicu kebakaran yang dinyatakan terjadi. |
| 07 · `FLOOD-EVENT` | Pemicu banjir yang dinyatakan terjadi. |
| 08 · `INFORMATION-ARG` | Predikat/keterangan dampak atau reaksi setelah role yang lebih khusus dialokasikan. |
| 09 · `OFFICER-ARG` | Pihak terlibat: orang, kelompok atau organisasi; cakupannya lebih luas daripada petugas. |
| 10 · `PLACE-ARG` | Frasa lokasi selain jalan. |
| 11 · `REASON-ARG` | Penyebab yang dinyatakan secara eksplisit. |
| 12 · `STREET-ARG` | Frasa lokasi jalan. |
| 13 · `TIME-ARG` | Frasa waktu, termasuk sejak/sekitar bila dinyatakan. |
| 14 · `WOUNDVICTIM-ARG` | Korban dengan luka/cedera atau kondisi fisik eksplisit sesuai pedoman pilot, termasuk kritis, sesak napas dan tidak sadarkan diri. |

WOUNDVICTIM mengikuti cakupan kondisi fisik yang disetujui pada pedoman pilot. Ekstraksi menyimpan klaim literal dalam narasi dan tidak menyimpulkan diagnosis atau penyebab kondisi korban.

## 5. Confusion matrix lengkap

**Baris = label acuan manusia. Kolom = label prediksi NARA.** Setiap sel berisi jumlah token, bukan persentase. Kode label mengikuti tabel pada bagian 4. Nilai diagonal menunjukkan prediksi benar; sel di luar diagonal menunjukkan pertukaran label.

Tabel berukuran 15 × 15 ini memuat seluruh **692 token**, termasuk O. Pada tampilan sempit, tabel dapat digeser mendatar.

| Acuan / Prediksi | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **00** | 244 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 49 | 3 | 2 | 2 | 0 | 2 | 4 |
| **01** | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **02** | 0 | 0 | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 2 | 0 | 0 |
| **03** | 0 | 0 | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **04** | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **05** | 0 | 2 | 0 | 0 | 0 | 4 | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **06** | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **07** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **08** | 3 | 1 | 2 | 0 | 0 | 0 | 2 | 0 | 24 | 1 | 0 | 0 | 0 | 0 | 0 |
| **09** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 0 | 0 | 0 | 0 | 0 |
| **10** | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 69 | 0 | 0 | 0 | 0 |
| **11** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 0 |
| **12** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 0 | 0 |
| **13** | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 93 | 0 |
| **14** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |

Jumlah seluruh sel: **692**. Jumlah diagonal: **600**. Token dengan label berbeda dari acuan: **92**. Akurasi token yang diturunkan dari matriks ini adalah **86,71%**; perhitungan tersebut mencakup O.

### Pola kesalahan yang paling terlihat

- **O → INFORMATION-ARG: 49 token.** Ini seluruh false positive INFORMATION-ARG pada matriks. Hanya 24 dari 73 prediksi INFORMATION-ARG yang sesuai acuan, sehingga precision label ini 32,88% dan F1 45,28%.
- **FALSE-EVENT: 4 dari 11 token tepat.** Tujuh sisanya diprediksi ACCIDENT-EVENT (2), FIRE-EVENT (2), dan FLOOD-EVENT (3). Precision 100% pada empat prediksi FALSE-EVENT tidak menutupi recall yang masih 36,36%.
- **AFFECTEDOBJECTS-ARG tertukar dengan lokasi.** Dari 47 token acuan, 40 tepat, 5 menjadi PLACE-ARG dan 2 menjadi STREET-ARG. Model masih kesulitan membedakan objek terdampak dari frasa lokasi pada sebagian konteks.
- **TIME-ARG relatif kuat pada pilot ini:** 93 dari 97 token tepat. Empat sisanya menjadi O (3) dan PLACE-ARG (1).

Kekuatan pada beberapa role tidak menghapus kelemahan INFORMATION-ARG dan FALSE-EVENT. Kategori akhir tetap berasal dari SENA; label event NARA dibaca sebagai hasil tugas token.

## 6. Hasil field setelah pemrosesan

Hasil berikut menilai **pipeline field NARA bersama adapter/postprocessing/composition/guard**. Nilainya terpisah dari metrik token dan span di atas.

| Metrik field | Hasil |
| --- | --- |
| Field nonkosong yang cocok persis | **154/176 = 87,50%** |
| Field acuan kosong yang terisi berlebih | **10/174 = 5,75%** |

| Field | Tepat / acuan nonkosong | Ketepatan | Terisi berlebih / acuan kosong |
| --- | ---: | ---: | ---: |
| `location_text` | 42/47 | 89,36% | 1/3 |
| `time_text` | 46/47 | 97,87% | 0/3 |
| `occurred_at` | Tidak ada acuan nonkosong | — | 0/50 |
| `involved_parties` | 23/24 | 95,83% | 1/26 |
| `impacts` | 16/28 | 57,14% | 5/22 |
| `victims` | 8/8 | 100,00% | 0/42 |
| `affected_objects` | 19/22 | 86,36% | 3/28 |

Pada `impacts`, hanya 16/28 acuan nonkosong cocok persis dan 5/22 acuan kosong terisi berlebih. Angka agregat 87,50% tetap harus dibaca bersama kelemahan field tersebut. Kesesuaian 50 nilai null pada `occurred_at` tidak membuktikan normalisasi waktu.

## 7. Keputusan penerimaan dan cakupan hasil

Pada batas isi berlebih awal ≤5%, pasangan model memenuhi 8/9 pemeriksaan. Setelah pengguna menyetujui batas ≤6%, hasil yang sama memenuhi **9/9 pemeriksaan** untuk pilot aset MVP. Perubahan aturan tersebut tidak mengubah bobot, label manusia, prediksi, confusion matrix, atau nilai metrik. Ini perubahan toleransi penerimaan setelah hasil diketahui.

FINAL084 merupakan pilot kecil berbasis narasi sintetis yang direview manusia. Hasilnya tidak membuktikan performa pada populasi laporan lapangan atau kalibrasi probabilitas. Hasil lama pada 79 narasi memakai dataset berbeda. FINAL081–083 yang kemudian digunakan untuk perbaikan merupakan data development/regresi; hasilnya tidak diperlakukan sebagai skor akhir model ini.

Training dan pengujian aset telah ditutup. Bukti yang tersedia belum membuktikan pemuatan di VM tujuan atau kesiapan deployment produksi.

## 8. Rujukan bukti

Seluruh metrik dan confusion matrix sudah disajikan di README ini. Tautan berikut menyediakan jejak sumber apabila diperlukan; path relatif berlaku ketika file berada di `models/slr09/reports/NARA.md`.

- [Evaluasi asli FINAL084 pada batas awal 5%](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/evaluation.json).
- [Keputusan pada batas revisi 6% dari prediksi yang sama](../evidence/acceptance_FINAL084_target006_20261020/evaluation_under_limit006.json).
- [Prediksi asli setiap narasi dan token](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/predictions.jsonl).
- [Workbook review manusia yang digunakan](../acceptance/Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx).
- [Notebook 31: inferensi/evaluasi asli yang telah dieksekusi](../notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb).
- [Pedoman 15 label NARA](../nara_finetune_frozen/SLR09_Pedoman_NARA_15Label_v0.2.md).
- [Identitas model dan versi kode](../release_manifest.json).
- [Laporan rinci field dan keputusan penerimaan](FIELD_DAN_KEPUTUSAN.md).
