# SLR09 — Pedoman NARA 15 label v0.2

Workflow: gunakan review final → pertahankan partisi NARA asli → fine-tune dari checkpoint NARA v1 → evaluasi token/span dan diagnostik field → ekspor → evaluasi integrasi berikutnya.

Versi ini menegaskan keputusan pengguna **A — Pertahankan hasil review** pada 18 Oktober 2026. Tidak ada label token hasil review yang diubah. Perluasan makna WOUND berlaku pada eksperimen pilot ini; tag kebijakan v0.1 dalam checkpoint lama tetap dipertahankan sebagai provenance waktu review. Manifest eksperimen memakai kebijakan efektif v0.2.

## 1. Representasi dan kontrak

NARA tetap mempunyai 15 label flat, satu label per token. Tidak menambah BIO, label ke-16, atau field A4.22. Adapter mengisi tujuh field: `location_text`, `time_text`, `occurred_at`, `involved_parties`, `impacts`, `victims`, dan `affected_objects`. Kategori kejadian tetap kewenangan SENA. `occurred_at` tidak dibuat dari waktu relatif tanpa konteks tanggal yang sah.

| ID | Label | Definisi operasional |
|---:|---|---|
| 0 | O | Di luar role khusus atau penghubung di luar batas frasa |
| 1 | ACCIDENT-EVENT | Pemicu kecelakaan yang dinyatakan terjadi |
| 2 | AFFECTEDOBJECTS-ARG | Frasa benda terdampak, termasuk kuantitas |
| 3 | DEATHVICTIM-ARG | Korban meninggal yang dinyatakan eksplisit, beserta subjek/kuantitas dan statusnya |
| 4 | EARTHQUAKE-EVENT | Pemicu gempa yang dinyatakan terjadi |
| 5 | FALSE-EVENT | Penyebutan kejadian dalam simulasi, hipotesis, negasi, atau pembahasan umum yang tidak menyatakan kejadian tersebut |
| 6 | FIRE-EVENT | Pemicu kebakaran yang dinyatakan terjadi |
| 7 | FLOOD-EVENT | Pemicu banjir yang dinyatakan terjadi |
| 8 | INFORMATION-ARG | Predikat/keterangan dampak atau reaksi setelah role yang lebih khusus dialokasikan |
| 9 | OFFICER-ARG | Pihak terlibat: orang, kelompok, atau organisasi; bukan hanya petugas |
| 10 | PLACE-ARG | Frasa lokasi selain jalan, termasuk keterangan yang diperlukan seperti dekat pasar |
| 11 | REASON-ARG | Penyebab yang dinyatakan eksplisit |
| 12 | STREET-ARG | Frasa lokasi jalan |
| 13 | TIME-ARG | Frasa waktu utuh, termasuk sejak/sekitar bila dinyatakan |
| 14 | WOUNDVICTIM-ARG | Korban dengan luka/cedera atau kondisi fisik yang dinyatakan eksplisit dalam konteks kejadian, termasuk kritis, sesak napas/nafas, dan tak/tidak sadarkan diri; sertakan subjek/kuantitas dan kondisi yang relevan |

Nama WOUNDVICTIM dipertahankan untuk kompatibilitas head model. Dengan keputusan A, label ini lebih luas daripada luka fisik. Ekstraksi menyimpan klaim literal, bukan menyimpulkan diagnosis atau penyebab kondisi tersebut.

## 2. Batas makna korban

Contoh yang disetujui dan tetap dipertahankan:

| ID | Frasa WOUND | Partisi |
|---|---|---|
| KEC-01099 | tiga kritis | Train |
| KEC-01462 | angkotpengendara motor tak sadarkan diri | Train |
| KEB-00290 | 1 korban mengalami sesak nafas | Validation |
| KEC-01399 | korban r2 dua orang dalam keadaan kritis | Validation |

Token sumber `angkotpengendara` tetap satu token; tidak dipecah atau diperbaiki sebagai label baru. Dua contoh train di atas tidak boleh dilaporkan sebagai pengujian heldout.

- Hilang, mengungsi, dievakuasi, hadirnya ambulans, kendaraan rusak, dan besarnya kejadian tidak otomatis berarti korban luka/kondisi fisik tertentu.
- Kondisi yang dinegasikan tidak menjadi korban positif. “Korban tidak kritis” berbeda dari kondisi “korban tidak sadarkan diri”; kata tidak pada contoh kedua adalah bagian kondisi fisik yang dinyatakan.
- “Pasokan air kritis” atau “sistem kritis” bukan kondisi fisik korban manusia.
- Label FALSE-EVENT bukan penilaian benar/hoaks dunia nyata. Keputusan NON_EVENT di integrasi tetap mengikuti SENA. NARA mengekstrak klaim literal sesuai tugas, tanpa menebak dari foto.

## 3. Frasa tumpang tindih dan komposisi

Prioritas satu label per token tetap: korban eksplisit → lokasi/waktu → objek terdampak → pihak → informasi dampak yang tersisa. Pemicu kejadian dan penyebab berada pada frasanya sendiri.

- `dua orang terluka` menjadi satu frasa WOUND, bukan label ganda OFFICER sekaligus. Adapter dapat mengambil prefix pihak literal yang didukung aturan.
- `merendam` adalah INFORMATION dan `beberapa rumah` AFFECTEDOBJECTS; komposisi dapat membentuk dampak “merendam beberapa rumah”.
- Komposisi harus mempunyai anchor INFORMATION dan hanya menggabungkan komponen yang langsung bersebelahan. Tidak melintasi O, batas klausa, atau kemunculan yang ambigu.
- Frasa waktu mempertahankan sejak/sekitar. Waktu yang sudah ditolak guard tidak dipulihkan.
- Label flat tidak membedakan dua entitas sejenis yang langsung berdampingan; batasan ini dinilai pada evaluasi span/field.

## 4. Implementasi guard v0.4

`legacy_postprocessing.py` tetap byte-identik sebagai bukti helper historis. Runtime v0.4 memakai wrapper `silar_victim_guard.py` untuk memperluas dukungan empat kondisi sesuai keputusan A.

Wrapper memeriksa span WOUND yang sudah diprediksi, cue kondisi, konteks pihak/kuantitas, grounding pada teks, dan negasi sebelum cue. Kata tak/tidak dalam frasa tidak sadarkan diri tidak diperlakukan sebagai penyangkalan kondisi itu. Kemunculan berulang dengan konteks positif dan negatif ditahan sebagai ambigu. Aturan ini tidak membuat span dari token O dan tidak menambah kode uncertainty aplikasi.

Death dan WOUND dengan cue luka lama tetap melalui guard historis. Batas normalisasi/helper lama masih berlaku; wrapper ini bukan parser semantik umum atau perombakan seluruh ekstraksi korban. Contoh nama/kondisi di luar pola yang didukung tetap perlu dievaluasi. Trace mencatat versi guard; raw token dan span sebelum guard dipertahankan.

## 5. Data pilot dan evaluasi

| Sumber | Train | Validation |
|---|---:|---:|
| B1 disetujui | 86 | 24 |
| Pelengkap disetujui | 71 | 17 |
| Pilot | 157 | 41 |

Total 198 narasi/4.641 token; seluruh 15 label terwakili pada train dan validation. `KEB-00486` tetap TUNDA dan dikeluarkan. Tidak ada versi label lama yang ditambahkan pada ID yang sudah direvisi.

1.000 test memakai anotasi historis dan tetap terpisah. Nilainya tidak otomatis mewakili pedoman v0.2. D01–D12 tetap diagnostik yang sudah dikenal; bukan data train atau blind test. Evaluasi field menggunakan prediksi SENA aktual tersimpan sebagai komponen tetap, dan inferensi NARA baru dari run Colab. Tidak menyebutnya inferensi SENA baru atau hasil end-to-end produksi.

Alignment: satu label sumber ditempatkan pada WordPiece pertama; piece lanjutan dan special token -100. Encoder sama dipakai pada training dan inferensi. Serving memakai segmentasi regex, sedangkan gold token mengikuti korpus; perbedaan unit tersebut dilaporkan pada audit. Metrik token hanya memakai token sumber yang terproses. Metrik span persis mengecualikan narasi terpotong dan tidak memakai asumsi BIO.

Validation 41 narasi dipakai memilih checkpoint; performanya adalah hasil development pilot. Macro F1 non-O selalu memakai seluruh 14 label non-O, termasuk label yang tidak diprediksi. Akurasi dan confusion matrix tetap memasukkan O. Nilai baru hanya tersedia setelah notebook benar-benar dijalankan.

Split SENA dan NARA berbeda. Validation SENA sendiri tidak otomatis menjadi holdout gabungan, karena sebagian teks pernah melatih NARA. Evaluasi integrasi berikutnya harus memperhatikan data training kedua komponen.

## 6. Urutan artefak tahap NARA

1. Notebook sumber TanggapMakna SRL V2: bukti training NARA lama.
2. Adapter v0.3 dan pedoman v0.1: pemetaan/komposisi 15 label serta awal penyelarasan.
3. B1 final: 110 keputusan token.
4. Audit split dan pelengkap: 88 APPROVED, satu TUNDA; gabungan 157/41.
5. Keputusan A → pedoman v0.2 dan guard/runtime v0.4, dengan label manusia tetap.
6. Notebook fine-tune pilot: baseline → training → evaluasi → ekspor. Bobot baru dan metrik baru dihasilkan saat eksekusi Colab.

Dokumen ini memperbarui pedoman AI NARA, bukan PRD atau dokumen acuan proyek SILAR secara keseluruhan.
