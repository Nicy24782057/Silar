# SLR11 — Bukti pekerjaan dan catatan waktu proses

Pembaruan dokumentasi: **23 Oktober 2026**. Cakupan implementasi: implementasi awal 0.1.0 dan paket integrasi SLR10–SLR11 0.2.0. Identitas pipeline pada run TAI yang dibaca kembali adalah `silar-pipeline-0.1.0`.

## Ringkasan bukti terbaru

**Ketujuh kombinasi kanal telah memiliki run berstatus `SUCCEEDED` pada database aplikasi pelaksana: T, A, I, TA, TI, AI dan TAI.** Rekap berisi 10 run berhasil. Pemeriksaan hubungan data pada seluruh 10 run menghasilkan **10 `OK`, 0 perlu diperiksa**, dengan ketujuh rute terbaca.

Pada lingkungan Windows pelaksana, **24 tes transaksi dan integrasi backend lulus dalam 19,483 detik**. Tes mencakup penyimpanan hasil, replay/idempotency, pembacaan hasil ketika respons awal tidak digunakan, konflik perubahan sumber, kegagalan finalisasi, keadaan `UNKNOWN`, serta pemulihan teknis dengan fencing token. Suite ini menggunakan transaksi PostgreSQL dan model/provider pengganti untuk mengendalikan kondisi pengujian.

Pengujian aplikasi dengan runtime asli tetap dicatat melalui run tersimpan dan bukti pelaksana. Metadata run TAI memuat referensi transkrip/narasi, versi Whisper, Gemini, SENA/NARA dan Fusion, serta waktu per tahap. Frontend juga telah mencapai draft awal Incident Card tersimpan berdasarkan konfirmasi pelaksana dan screenshot.

**Keterangan “tanpa database dan tanpa panggilan Gemini” hanya berlaku pada lampiran waktu uji komponen versi awal tanggal 21 Oktober 2026.** Angka dan batas lingkungan arsip tersebut tetap digunakan sesuai asal pengukurannya.

## 1. Sumber bukti dan urutan pengujian

| Waktu / urutan | Bukti | Lingkup |
| --- | --- | --- |
| 21 Oktober 2026 | `docs/ai/slr11/evidence/model_runtime_smoke.json` pada arsip versi awal | Eksekusi komponen lokal SENA/NARA serta jalur Whisper pada sampel sintetis; angka historis disertakan pada bagian 6. |
| 22 Oktober 2026, 00.30 WIB | Run TAI `fb4eadcc-291e-4e5a-ba38-42b15bcbdf14` | Pengujian TAI melalui backend. Waktu run berasal dari timestamp tersimpan yang diberikan pelaksana. |
| Sesi integrasi sampai 22 Oktober 2026 | Konfirmasi dan screenshot frontend | Alur mencapai hasil analisis dan draft awal Incident Card tersimpan. |
| 23 Oktober 2026 | Rekap run, pemeriksaan relasi, dan keluaran dua modul tes | Ketujuh rute terbaca; 10 run dengan relasi `OK`; 24 tes transaksi/integrasi lulus. |

Sumber terbaru disertakan dalam direktori `evidence/windows-pg16-20261023/`:

- `verifikasi-relasi-dan-pemulihan.txt`: salinan utuh keluaran terminal yang dikirim pelaksana sebagai `Teks yang ditempel (1)(1).txt`; memuat skrip pemeriksaan, hasil per run, ringkasan, nama seluruh tes dan hasil akhir.
- `rekap-run-dan-relasi.json`: rekap terstruktur yang diturunkan dari hasil pemeriksaan pada log tersebut, dilengkapi jumlah run per rute.
- `metadata-run-tai.json`: transkripsi metadata run TAI dari keluaran terminal yang diberikan pelaksana dalam sesi integrasi; bukan hasil kueri atau inferensi baru oleh penyusun dokumen.

Arsip `hasil-verifikasi-slr10-slr11.txt` sebelumnya hanya mencatat perintah. Kesimpulan hasil pemeriksaan menggunakan keluaran terminal lengkap yang tercantum di atas.

## 2. Bukti Pekerjaan — teks untuk card SLR11

Pipeline SLR11 telah diintegrasikan dengan frontend dan pengelolaan bukti SLR10. Database aplikasi pelaksana mencatat 10 run `SUCCEEDED` yang mencakup T, A, I, TA, TI, AI dan TAI. Pemeriksaan hubungan narasi, SENA/NARA, Incident Card, laporan/bundle, transkrip dan ledger menghasilkan 10 run `OK`, tanpa temuan pada aturan yang diperiksa. Sebanyak 24 tes transaksi dan integrasi backend pada Windows/PostgreSQL lulus dalam 19,483 detik. Frontend telah mencapai draft awal Incident Card tersimpan.

| Bagian pekerjaan | Bukti implementasi/verifikasi |
| --- | --- |
| Routing, narasi, transkripsi, SENA, NARA dan Fusion | Kode pada `code/backend/ai_pipeline/`, menggunakan aset/adapter SLR09. Konfigurasi, dependensi dan alur pipeline dijelaskan dalam `docs/ai/slr11/SLR11_Integrasi_dan_Verifikasi_v0.1.md`. |
| Integrasi backend/frontend | Kode pada `code/backend/reporting/`, konfigurasi backend gabungan dan `code/frontend/`. Laporan integrasi awal tersedia dalam `docs/ai/slr11/HASIL_INTEGRASI_v0.2.0.md`; hasil lanjutan pada lingkungan pelaksana dicatat dalam dokumen ini. |
| Tujuh rute pada database aplikasi | T = 3, A = 1, I = 1, TA = 1, TI = 1, AI = 2 dan TAI = 1 run `SUCCEEDED`; seluruhnya lolos pemeriksaan hubungan data. Bukti: `evidence/windows-pg16-20261023/rekap-run-dan-relasi.json` dan log lengkap. |
| Konsistensi hasil tersimpan | 10 run `OK`, 0 perlu diperiksa. Narasi, SENA/NARA, kartu, laporan/bundle, transkrip dan ledger memenuhi aturan pemeriksaan pada bagian 3. |
| Transaksi, idempotency dan pemulihan | 15 tes `ai_pipeline.tests.test_database` dan 9 tes `ai_pipeline.tests.test_reporting_integration`, total 24 tes lulus. Mencakup commit sebelum respons berhasil, replay tanpa inferensi/mutasi ganda, akses pemilik, respons hilang, konflik sumber berubah, kegagalan finalisasi, `UNKNOWN` dan fencing token. |
| Uji langsung backend TAI dan waktu proses | Run `fb4eadcc-291e-4e5a-ba38-42b15bcbdf14`, status `SUCCEEDED`, dengan transkrip dan narasi tersimpan. `timings_ms.TOTAL = 6926.025` ms, sekitar 6,93 detik, sesuai batas pengukuran internal pipeline. Rincian pada bagian 5–6. |
| Uji langsung frontend | Konfirmasi pelaksana dan screenshot menunjukkan draft awal Incident Card tersimpan, kategori Kebakaran, versi 1, keyakinan model 99,97%, ekstraksi, narasi sumber dan peringatan pemeriksaan dampak. Keberhasilan penyimpanan setelah pemuatan ulang juga telah dikonfirmasi pelaksana. |
| Arsip otomatis paket integrasi | Arsip 0.2.0 mencatat 74 tes regresi backend dan 9 tes sambungan input–analisis, serta 35 tes frontend dan build Vue/PWA dengan 45 modul. Bukti historis: `docs/ai/slr11/evidence/integrasi-v0.2.0/`. Lingkup dan lingkungan arsip tetap mengikuti laporan aslinya. |
| Prosedur operasional dan pemulihan | Prosedur `recover_ai_run`, pemeriksaan proses lama, fencing token dan retry eksplisit tersedia dalam laporan versi awal. Panduan menjalankan aplikasi dan membaca hasil tersimpan tersedia dalam `PANDUAN_RUNNING.md`. |
| Masukan pengukuran SLR15 | Metadata run menyediakan `timings_ms`, rute, versi model dan timestamp. Dokumen ini menyertakan satu pengukuran TAI tersimpan beserta angka historis komponen dan batas pengukurannya. |

**Commit pekerjaan:** pengisian dan pencocokan SHA/URL commit dilakukan oleh pelaksana.

Jumlah tes dari arsip berbeda tidak dijumlahkan menjadi total kasus unik karena beberapa suite saling tumpang tindih. Hasil terbaru yang dapat dibuktikan dari log Windows adalah 24 tes lulus.

## 3. Tujuh rute dan pemeriksaan hasil persisten

### Rekap per rute

| Rute | Kanal asli | Run `SUCCEEDED` | Relasi `OK` |
| --- | --- | ---: | ---: |
| T | Teks | 3 | 3 |
| A | Audio | 1 | 1 |
| I | Gambar | 1 | 1 |
| TA | Teks + audio | 1 | 1 |
| TI | Teks + gambar | 1 | 1 |
| AI | Audio + gambar | 2 | 2 |
| TAI | Teks + audio + gambar | 1 | 1 |
| **Total** | **7 kombinasi** | **10** | **10** |

Pemeriksaan dilakukan terhadap run `mode=EVIDENCE` dan `status=SUCCEEDED` yang sudah tersimpan. Pembacaan tersebut tidak menjalankan inferensi baru.

### Aturan hubungan data yang diperiksa

1. Narasi tersimpan dan berisi teks.
2. `producer_run_id` narasi menunjuk run yang diperiksa.
3. Hasil SENA dan NARA tersedia dan memakai narasi keluaran run yang sama.
4. Terdapat tepat satu kartu `AI_FUSION` berdasarkan hasil SENA dari run tersebut.
5. Kartu merujuk narasi serta hasil SENA dan NARA yang sesuai.
6. Run, bundle, narasi dan kartu berasal dari laporan yang sama; narasi dan kartu memakai bundle run tersebut.
7. Data kartu sama dengan kategori SENA dan `normalized_output` NARA; kategori kartu untuk `NON_EVENT` bernilai `null`.
8. Rute yang memuat audio memiliki transkrip dengan run dan laporan yang sesuai; rute tanpa audio tidak memakai transkrip.
9. Ledger berstatus `SUCCEEDED`, bertipe hasil `Run`, menunjuk run/laporan yang sesuai dan mencatat status respons 201.

Pemeriksaan menggunakan kartu milik masing-masing run. Kartu historis tidak diwajibkan menjadi kartu aktif laporan saat ini.

**Hasil: 10 run `OK`, 0 perlu diperiksa.** Pemeriksaan ini membuktikan konsistensi data pada aturan tersebut. Ketepatan makna informasi tetap dinilai terhadap bukti sumber; hubungan data yang konsisten tidak otomatis membuktikan seluruh ekstraksi benar.

## 4. Verifikasi transaksi, replay dan pemulihan pada Windows/PostgreSQL

### Lingkungan dan perintah

- Sistem operasi: Windows, sesuai keluaran terminal pelaksana.
- Python: 3.12.10, 64 bit, menggunakan interpreter `.venv` proyek.
- Database uji: PostgreSQL, alias `default`, nama `test_silar_local`.
- Suite `AnalysisDatabaseTests` pada paket integrasi memeriksa vendor PostgreSQL dan versi mayor 16 sebelum menjalankan setiap tes; seluruh 15 tesnya tercatat lulus.
- Setting: `config.test_settings`; pelaksanaan memakai `--keepdb`.
- Model/provider: pengganti yang dikendalikan oleh suite. Media tes memakai direktori sementara.

Perintah yang tercatat:

```powershell
.\.venv\Scripts\python.exe manage.py test `
  ai_pipeline.tests.test_database `
  ai_pipeline.tests.test_reporting_integration `
  --settings=config.test_settings `
  --verbosity=2 `
  --keepdb
```

Hasil akhir:

```text
Found 24 test(s).
System check identified no issues (0 silenced).
Ran 24 tests in 19.483s
OK
Preserving test database for alias 'default' ('test_silar_local')...
```

Seluruh 24 tes ditampilkan dengan hasil `ok`; tidak ada kegagalan atau tes dilewati yang tercatat pada keluaran tersebut.

### Cakupan yang telah lulus

| Kelompok | Perilaku yang diperiksa |
| --- | --- |
| Penyimpanan dan finalisasi | Kartu, ledger dan audit tersimpan sebelum respons berhasil; sumber tujuh rute dan referensi audio persisten; alur upload/bundle sampai kartu dapat dibaca kembali. |
| Replay/idempotency | Replay mengembalikan snapshot tanpa inferensi, perubahan revision atau audit ganda; akun diperiksa kembali; key dengan revision/payload berbeda ditolak; replay hasil lama tetap mengikuti kontraknya. |
| Pembacaan setelah respons hilang | Hasil request, run dan laporan dapat dibaca tanpa mutasi; replay mengembalikan hasil yang sama. Tes memodelkan respons hilang dengan membaca hasil setelah respons awal tidak dipakai, tanpa memutus jaringan browser secara fisik. |
| Sumber berubah | Perubahan sumber langsung maupun melalui API input mempertahankan sumber baru dan hasil parsial yang sah; kartu dari sumber lama tidak diaktifkan. |
| Kegagalan dan rollback | Kegagalan upstream mempertahankan jejak parsial yang sesuai; kegagalan finalisasi membatalkan kartu dan tidak mengembalikan sukses; retry eksplisit setelah kegagalan mengikuti revision terbaru. |
| `UNKNOWN` dan pemulihan | GET tetap membaca keadaan tersimpan tanpa mutasi; analisis baru ditahan; pembatalan proses aktif ditolak; setelah bukti berhenti yang disimulasikan pada batas observasi proses, token diganti, audit/keadaan difinalisasi dan token lama ditolak. |
| Akses dan kapasitas | Pemilik lain tidak dapat membaca/menganalisis sumber privat; kapasitas penuh tidak memutasi laporan. |
| Kontrak pendukung | NON_EVENT/uncertain, revisi narasi tanpa Whisper/Gemini, konfigurasi AI belum siap dan request kedaluwarsa mengikuti kontrak masing-masing. |

Transaksi, migration dan konteks kapasitas pada eksekusi ini menggunakan PostgreSQL. Pengganti model/provider serta observasi proses pada tes pemulihan memungkinkan skenario kegagalan dikendalikan. Hasil tes tersebut digunakan untuk penerimaan perilaku layanan; mutu inferensi model nyata tetap memakai bukti eksekusi aplikasi dan evaluasi model SLR09.

## 5. Keterlacakan run TAI yang dibaca kembali

| Metadata | Nilai tersimpan |
| --- | --- |
| Run | `fb4eadcc-291e-4e5a-ba38-42b15bcbdf14` |
| Report | `8d439838-12c3-44e2-919a-c9502bd23403` |
| Rute / status | `TAI` / `SUCCEEDED` |
| Mulai, UTC | `2026-10-21 17:30:38.354684+00:00` |
| Selesai, UTC | `2026-10-21 17:30:45.271146+00:00` |
| Mulai, WIB | 22 Oktober 2026, 00.30.38 WIB |
| Referensi transkrip | `165e00c7-a8e6-4ed4-b3f6-bfef011fbc50` |
| Referensi narasi | `59b002a0-a52e-4baf-92c2-cf0d0dd0045b` |
| Pipeline | `silar-pipeline-0.1.0` |
| SENA | `SILAR_SENA_context_v084_20261020T144453Z\|silar-adapter-0.5.3` |
| NARA | `SILAR_NARA_reviewed_pilot_20261018T001122_607337Z\|silar-adapter-0.5.3` |
| Whisper | `whisper-small\|536b0662742c0234\|cpu-int8` |
| Gemini, diminta dan teresolusi | `gemini-3.5-flash-lite` |
| SDK Gemini | `2.32.0` |
| Prompt | `silar-unified-narrative-0.1.0` |
| Fusion | `silar-fusion-a4.22-0.1.0` |

Versi serta hash konfigurasi/aset yang diberikan pelaksana dipertahankan dalam `evidence/windows-pg16-20261023/metadata-run-tai.json`. Nilai confidence threshold 0,95 pada metadata adalah cutoff operasional; referensi kalibrasinya secara eksplisit menyatakan `NOT_PROBABILITY_CALIBRATED`.

## 6. Catatan waktu proses untuk SLR15

### Waktu TAI pada database aplikasi pelaksana

Sumber: `timings_ms` run TAI pada bagian 5. Data ini dibaca dari hasil tersimpan, tanpa menjalankan TAI ulang untuk penulisan dokumen.

| Field | Waktu (ms) |
| --- | ---: |
| `WHISPER` | 1.749,836 |
| `NARRATIVE` | 4.873,112 |
| `SENA` | 67,991 |
| `NARA` | 71,394 |
| `FUSION` | 0,199 |
| **`TOTAL`** | **6.926,025** |

`TOTAL` setara sekitar **6,93 detik** menurut batas penghitung internal pipeline. Angka berasal dari satu run; pengukuran berulang dan statistik latensi lingkungan sasaran dilanjutkan pada SLR15. Durasi sampai hasil diterima/ditampilkan browser tidak dicatat dalam bukti ini.

### Makna field waktu pada implementasi

| Field | Batas pengukuran |
| --- | --- |
| `WHISPER` | Eksekusi transkripsi saat tahap ini dijalankan. |
| `NARRATIVE` | Pembentukan narasi melalui Normalizer/Gemini sesuai rute. |
| `SENA`, `NARA`, `FUSION` | Eksekusi masing-masing tahap; penulisan hasil tahap ke database terjadi sesudah penghitung tahap dihentikan. |
| `TOTAL` | Dimulai setelah pemuatan pipeline/preflight, sebelum reservasi kapasitas. Nilai diambil sebelum pemanggilan finalisasi; tidak mencakup transaksi finalisasi/commit sesudahnya, jaringan atau render browser. |
| `finished_at - started_at` | Selang timestamp run. Timestamp selesai ditetapkan di dalam transaksi finalisasi sebelum commit; berbeda dari durasi sampai respons diterima browser. |
| Durasi suite tes 19,483 detik | Waktu menjalankan 24 tes transaksi/integrasi dengan model/provider pengganti; tidak digunakan sebagai waktu satu analisis AI. |

Tahap yang tidak dijalankan tidak diperlakukan sebagai 0 ms. Jumlah waktu tahap, durasi suite tes dan build tidak dinyatakan sebagai latensi total pengguna.

### Lampiran waktu uji komponen versi awal — 21 Oktober 2026

Sumber: `docs/ai/slr11/evidence/model_runtime_smoke.json`. Lingkungan Python 3.12.14/Linux. Pengukuran komponen ini menggunakan model lokal SENA/NARA, tanpa database dan tanpa panggilan Gemini.

| Sampel sintetis | Narasi (ms) | SENA (ms) | NARA (ms) | Fusion (ms) |
| --- | ---: | ---: | ---: | ---: |
| Teks banjir Jalan Melati/Desa Sukamaju | 0,157 | 4.636,362 | 83,653 | 0,253 |
| Teks kecelakaan mobil di Jalan Mawar | 0,021 | 66,097 | 85,760 | 0,184 |
| Teks simulasi kebakaran/NON_EVENT | 0,024 | 75,207 | 86,320 | 0,124 |

Jalur ujaran sintetis dengan audio sumber 3.685 ms mencatat `elapsed_seconds=8.393`, yaitu 8,393 detik pada blok pengujian tersebut. Transkripsi menyimpang dan menghasilkan NON_EVENT. Bukti ini menunjukkan eksekusi jalur teknis pada sampelnya; mutu audio Indonesia alami dinilai melalui bukti yang sesuai.

Angka historis tersebut tetap dikaitkan dengan lingkungan dan sampel asalnya. Pengukuran TAI tersimpan pada Windows dicatat tersendiri pada tabel sebelumnya.

### Teks ringkas untuk penyerahan SLR15

SLR11 menyediakan pencatatan waktu per tahap pada run analisis. Database aplikasi pelaksana memuat 10 run berhasil yang mencakup tujuh kombinasi kanal dan lolos pemeriksaan hubungan data. Run TAI `fb4eadcc-291e-4e5a-ba38-42b15bcbdf14` mencatat `TOTAL` internal 6.926,025 ms, dengan versi model dan referensi sumber tersimpan. Sebanyak 24 tes transaksi/integrasi pada Windows/PostgreSQL juga lulus dalam 19,483 detik; durasi suite tersebut dicatat sesuai lingkup pengujiannya. Pengukuran berulang, latensi API/browser, statistik, kapasitas dan sumber daya lingkungan sasaran dilanjutkan pada SLR15 sesuai acuan proyek.

## 7. Pemakaian bukti untuk SLR10 dan SLR11

| Lingkup penerimaan | Bukti yang dapat dipakai |
| --- | --- |
| SLR11: tujuh rute dan hasil persisten | Rekap 10 run berhasil, 10 relasi `OK`, metadata TAI, serta tes tujuh rute pada dua suite. |
| SLR11: idempotency, finalisasi dan pemulihan | Log 24 tes transaksi/integrasi lulus, dengan cakupan dan pengganti yang dijelaskan pada bagian 4. |
| SLR10: sambungan pengelolaan bukti ke SLR11 | Tes alur upload/bundle sampai hasil tersimpan serta konfirmasi/screenshot frontend sampai draft awal Incident Card. |
| SLR10: UI, akun, responsif, perangkat/browser dan PWA | Mengikuti bukti pada `docs/slr10/HASIL_VERIFIKASI.md` dan arsip pengujian SLR10 sesuai versi/lingkungannya. Log backend terbaru tidak menetapkan hasil baru untuk seluruh pengujian UI/perangkat/PWA. |

Pemeriksaan/koreksi/konfirmasi manusia pada SLR12 dan pengukuran lengkap SLR15 tetap mengikuti cakupan card masing-masing. Dokumen ini mencatat penyimpanan draft awal Incident Card serta penerimaan teknis integrasi yang telah dibuktikan.

## 8. Penempatan dan penggunaan

Tempatkan dokumen ini pada:

```text
docs/ai/slr11/BUKTI_PEKERJAAN_DAN_WAKTU_PROSES_SLR11.md
```

Tempatkan tiga file bukti pendamping pada:

```text
docs/ai/slr11/evidence/windows-pg16-20261023/
```

Paket ZIP pendamping sudah memakai struktur folder tersebut dan dapat diekstrak dari folder utama repository. Tautkan dokumen serta direktori bukti pada card SLR11; gunakan bagian 7 sebagai rujukan penerimaan integrasi pada card SLR10.

Bagian 2 dapat disalin ke “Bukti Pekerjaan” card SLR11. Pengisian dan pencocokan SHA/URL commit dikerjakan oleh pelaksana. Penetapan selesai mengikuti keterpenuhan checklist masing-masing card dan keterlacakan bukti tersebut.
