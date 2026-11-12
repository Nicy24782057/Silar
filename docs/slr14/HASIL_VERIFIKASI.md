# Hasil verifikasi SLR14 — audit lanjutan 30 Oktober 2026

Base: `1af8ac6f098b1a50fc83b4c74f8b0b4bbaaf73cd` (SLR13).
Kode, build dan antarmuka diperiksa setelah revisi alur lanjutan. Backend tidak
berubah pada revisi alur, notifikasi, dan Operator; hasil backend di bawah berasal dari audit menyeluruh. Hasil lulus
berikut tidak menggantikan penerimaan native PostgreSQL 16.

| Pemeriksaan | Hasil | Bukti/lingkup |
| --- | --- | --- |
| Unit frontend | 109 lulus | `bukti/frontend-unit.txt`; kontrak publik, filter, izin, recovery dan PWA |
| Build produksi | Lulus | `bukti/frontend-build.txt` |
| Backend komponen | 94 lulus, 5 dilewati | `bukti/backend-komponen-audit.txt`; 99 kasus, termasuk 11 penghapusan. Lima yang dilewati memerlukan PostgreSQL asli. |
| Status model/migration | Tidak ada perubahan model yang belum dibuat migration | `makemigrations core --check --dry-run`; konsistensi history DB tidak dapat diperiksa karena PostgreSQL tidak tersambung. |
| Penerimaan PostgreSQL 16 | BLOCKED; 143 tes ditemukan, 0 dijalankan | `bukti/postgresql16-preflight.json`; bukan hasil lulus |
| Sumber desain | 30 SVG × dua tema; tujuh tab dan dialog dibuka | `bukti/sumber-desain-audit.txt` |
| Regresi antarmuka luas (paket alur sebelumnya) | 174 kombinasi lulus | `bukti/browser-matriks-alur.txt`; akun/publik/semua role, dua tema × desktop/tablet/ponsel |
| Reporter/portal (paket sebelumnya) | 60 kombinasi lulus | `bukti/browser-reporter-notifikasi.txt`; enam lebar 1440/1100/820/640/390/320, empat tahap pelaporan, API nyata lokal, input teks/WAV/PNG, revisi v2, konfirmasi dan submit terpisah |
| Admin/Operator mendalam | Lulus | `bukti/browser-admin-operator-audit.txt`; semua tujuh tab, review awal, halaman bersama, delapan halaman Admin dan lima dialog, dua tema × desktop/ponsel |
| Notifikasi, tahap draft dan hasil otomatis (paket sebelumnya) | Lulus | `bukti/notifikasi-dan-hasil.txt`; 24 kombinasi notifikasi + 12 penanda, transisi login tiga role, progres, hasil terbuka otomatis, analisis gagal tetap di bukti, konfirmasi/submit riil lokal, refresh/URL belum dikirim |
| Alur Operator terbaru | Lulus | `bukti/operator-alur-publikasi.txt`; 60 kombinasi proses, review otomatis, pratinjau langsung, konfirmasi merangkai keputusan/create/approve, publish eksplisit, kontrak sembilan field dan versi pengganti |
| Pemulihan Operator terbaru | Lulus | `bukti/operator-pemulihan.txt`; review/keputusan terputus dipulihkan dengan GET, formulir ditahan pada penolakan, approval gagal tidak publish, 28 kombinasi tujuh tab, reduced motion, metadata Admin |
| Keadaan API/tindakan | Lulus | `bukti/browser-tindakan-audit.txt`; hapus, foreign ID, respons hilang, media gagal/retry, JSON AI, penugasan gagal/kosong, ringkasan administratif, readback akun dengan satu POST |
| Login pendek/transisi | 24 kombinasi login lulus; navigasi/transisi lulus | `bukti/browser-login-transisi-audit.txt`; ukuran contoh 1535 × 727, layar pendek, 641/640, ponsel 320; ruang teks/art/privasi terpisah; normal motion dan anchor |
| Login vs sumber | 0 piksel statis berbeda | Dua tema, panel 680 × 900; area ilustrasi bergerak dikecualikan |
| Publikasi browser | Lulus | `bukti/publikasi-audit.txt`; kandidat privat, sanitasi, persetujuan, publish terpisah, sembilan field publik dan review terkunci |
| PWA produksi | Lulus | `bukti/pwa-operator.txt`; 60 aset UI, tanpa API/media/laporan/kredensial di cache; shell offline, login terkunci, data publik tidak dibaca dari cache |

Browser memakai Chromium headless dengan API lokal dan database SQLite khusus
QA, terpisah per suite. Pemeriksaan integritas database dilakukan setelah suite.
Konfigurasi QA, fixture, database, email uji, kredensial dan `dist` tidak dikirim.
Ini bukan konfigurasi menjalankan aplikasi. Mesin aplikasi tetap PostgreSQL 16.
Tampilan dinilai dengan data uji, sehingga isi/angka berbeda dari contoh SVG.

## Tambahan penuntasan verifikasi

Baseline implementasi sudah berada di main pada e0dc889. Tambahan alat verifikasi
memisahkan scope native dasar dari integrasi API/pipeline. Frontend dan pipeline
runtime tidak diubah. Hasil berikut berasal dari pemeriksaan tambahan ini:

| Pemeriksaan tambahan | Hasil | Bukti |
| --- | --- | --- |
| Guard verifier | 17 lulus, tanpa membuat database | bukti/penuntasan-guard-verifikasi.txt |
| Native dasar | BLOCKED; 143 ditemukan, 0 dijalankan | bukti/penuntasan-native-dasar.json |
| Native + integrasi API/pipeline | BLOCKED; 152 ditemukan, termasuk sembilan integrasi; 0 dijalankan | bukti/penuntasan-native-dan-integrasi-api.json |
| Lingkungan proses/model | Identitas OS tidak terverifikasi; aset model default tidak tersedia; inferensi asli tidak dijalankan | bukti/penuntasan-lingkungan.json |

Perintah gabungan: `verify_slr14.py --include-pipeline-integration`. Sembilan tes
menggunakan model/provider uji; `live_ai_inference_exercised=false` tetap tercatat
meskipun nanti perintah ini PASSED. Penjelasan dan urutan lokal ada di
[PENUNTASAN_VERIFIKASI_20261030.md](PENUNTASAN_VERIFIKASI_20261030.md).

## Batas yang belum lolos

1. PostgreSQL 16 tidak tersedia di lingkungan ini. Migration 0005, trigger
   keadaan terhapus, lock lintas transaksi dan race DELETE melawan submit
   belum dibuktikan pada engine asli. Jalankan `verify_slr14.py` pada konfigurasi
   PostgreSQL 16 tim; status harus `PASSED`, tanpa skip. Paket tidak dinyatakan
   selesai penerimaan native hanya berdasarkan SQLite atau build.
2. Sembilan tes `ai_pipeline.tests.test_reporting_integration` adalah integrasi
   API/pipeline/penyimpanan dengan **model/provider uji**, bukan inferensi AI asli.
   Percobaan sebelumnya tertahan saat membaca identitas proses psutil sebelum
   run terbentuk. Guard tambahan kini menghentikan lingkungan proses yang tidak
   dapat dibuktikan, bukan mengganti identitas atau melewati pemeriksaan. Gunakan
   `verify_slr14.py --include-pipeline-integration` pada PostgreSQL 16 lokal tim.
3. Inferensi nyata Whisper/SENA/NARA/Fusion/Gemini serta uji end-to-end pada kode
   terintegrasi tetap memerlukan aset/kunci dan lingkungan aplikasi sebenarnya.
   Hasil komponen, browser dan test doubles tidak membuktikan mutu model atau
   panggilan provider asli. Pengujian lintas fitur/performa mengikuti SLR15.

## Mengulang pemeriksaan komponen

```text
SILAR_ALLOW_COMPONENT_DB=1 python manage.py test \
  reporting.tests.test_publication \
  reporting.tests.test_slr14_verification \
  reporting.tests.test_workspace.WorkspaceTests \
  reporting.tests.test_workspace_update03 \
  reporting.tests.test_review \
  reporting.tests.test_report_list_filters \
  reporting.tests.test_deletion \
  reporting.tests.test_deletion_postgresql \
  --settings=reporting.component_test_settings --noinput
```

Perintah ini hanya pemeriksaan komponen eksplisit. Penerimaan native memakai
[UJI_POSTGRESQL16.md](UJI_POSTGRESQL16.md). Untuk scope native beserta sembilan tes
integrasi API dengan model/provider uji:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --include-pipeline-integration
```

Keputusan desain dan pratinjau dijelaskan pada
[AUDIT_MENYELURUH_20261030.md](AUDIT_MENYELURUH_20261030.md) serta
[ALUR_OPERATOR_20261030.md](ALUR_OPERATOR_20261030.md).
