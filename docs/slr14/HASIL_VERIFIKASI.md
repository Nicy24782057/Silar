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

## Batas yang belum lolos

1. PostgreSQL 16 tidak tersedia di lingkungan ini. Migration 0005, trigger
   keadaan terhapus, lock lintas transaksi dan race DELETE melawan submit
   belum dibuktikan pada engine asli. Jalankan `verify_slr14.py` pada konfigurasi
   PostgreSQL 16 tim; status harus `PASSED`, tanpa skip. Paket tidak dinyatakan
   selesai penerimaan native hanya berdasarkan SQLite atau build.
2. Percobaan tambahan sembilan tes `ai_pipeline.tests.test_reporting_integration`
   belum lulus di lingkungan ini. Setelah dependensi psutil yang sudah tercantum
   pada requirements AI tersedia, setup berhenti pada pembacaan identitas proses
   (`psutil.NoSuchProcess`, sebelum run terbentuk) akibat lingkungan proses QA.
   Tes tersebut tidak dilewati/dipalsukan agar dianggap lulus. Catatan ada pada
   `bukti/integrasi-ai-tambahan.txt`. Jalankan kembali pada lingkungan aplikasi
   lokal dengan stack AI SLR11 yang lengkap. Regresi Reporter di browser tidak
   menjalankan inferensi AI baru; pengujian ini tidak membuktikan model/layanan
   AI eksternal atau pengiriman email nyata.

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

Perintah ini hanya pemeriksaan komponen eksplisit. Penerimaan penuh harus memakai
[UJI_POSTGRESQL16.md](UJI_POSTGRESQL16.md). Tambahan tes integrasi pada lingkungan
aplikasi yang lengkap:

```powershell
.\.venv\Scripts\python.exe manage.py test ai_pipeline.tests.test_reporting_integration --settings=config.test_settings --noinput
```

Keputusan desain, daftar sumber dan pratinjau terkini tersedia pada
[AUDIT_MENYELURUH_20261030.md](AUDIT_MENYELURUH_20261030.md).
