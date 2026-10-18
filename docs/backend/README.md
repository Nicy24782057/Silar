# SLR_08 — Fondasi backend dan database SILAR

Paket ini menyediakan backend Django/DRF untuk akun, keamanan dan audit, beserta fondasi skema yang digunakan SLR_10–SLR_14. Acuan aktif adalah PRD 0.5, Acuan Teknis 0.3 termasuk Lampiran A, pemetaan fitur final dan rancangan UI/UX SLR_07. Snapshot sumber serta hash ada pada [baseline.json](baseline.json).

Status: **siap untuk uji lokal dan integrasi fondasi**. Sebanyak **73 pengujian otomatis** dan **9 pemeriksaan instalasi/HTTP** lulus pada lingkungan pengujian. Bukti dan batas pemeriksaan ada di [hasil-verifikasi.md](hasil-verifikasi.md). Penerimaan kelompok, pemeriksaan Windows/browser dan commit repository masih harus dicatat oleh tim.

## Mulai di Windows

Prasyarat: Python 3.12 atau 3.13, PostgreSQL **mayor 16** yang berjalan, dan internet saat pemasangan dependency. Python 3.12 dipakai dalam pengujian paket. Unduh installer dari [Python](https://www.python.org/downloads/windows/) dan [PostgreSQL](https://www.postgresql.org/download/windows/).

1. Ekstrak ZIP ke folder kerja sementara. Masuk ke `code/backend`.
2. Jalankan `SETUP_LOKAL.bat`. Masukkan koneksi administrator PostgreSQL, lalu nama database dan role **baru**. Script membuat virtual environment, memasang versi paket yang dikunci, membuat tiga rahasia acak berbeda, menulis `.env`, menjalankan migration serta `bootstrap_silar`.
3. Jalankan `BUAT_ADMIN.bat`. Masukkan email, nama dan password sendiri. Akun Admin dibuat melalui prosedur lokal tepercaya; registrasi publik selalu membuat Reporter.
4. Jalankan `JALANKAN_BACKEND.bat`. Backend tersedia di `http://localhost:8001`. `GET /health/` harus menampilkan `READY` dan `postgresql_major: 16`.
5. Jalankan frontend tim secara terpisah, umumnya `http://localhost:5173`. Prototype SLR_07 dapat tetap dijalankan di port 8000. Panduan penyambungan ada di [frontend-handoff.md](frontend-handoff.md).

Untuk CMD manual, jalankan dari `code/backend`:

```bat
py -3.12 scripts\setup_local.py
.venv\Scripts\python.exe manage.py create_silar_admin
.venv\Scripts\python.exe manage.py runserver localhost:8001
```

Pada Linux/macOS, jalankan `python3.12 scripts/setup_local.py`, kemudian gunakan `.venv/bin/python` untuk perintah `manage.py`. Virtual environment, Python dan PostgreSQL tidak dibundel di ZIP.

Setup otomatis khusus localhost. Role database lokal diberi `CREATEDB` agar Django dapat membuat database pengujian terpisah. Ini pilihan pengembangan lokal; deployment SLR_16 perlu role runtime dengan hak lebih terbatas dan prosedur migration tersendiri. Jika nama database/role sudah ada, setup meminta nama baru. Jika `.env` sudah ada, konfigurasi dipakai kembali, tanpa mengganti rahasia atau menghapus data.

## Email, challenge dan akun

Konfigurasi awal `EMAIL_MODE=file` menyimpan email privat di `private_outbox/*.eml`. Buka email itu dengan editor teks atau pembaca email untuk memperoleh kode dan tautan challenge. Mode ini membuktikan alur akun lokal; pengiriman ke alamat internet memerlukan SMTP yang dikonfigurasi tim. File email tidak disajikan oleh backend dan tidak masuk Git/ZIP.

Registrasi/request OTP mengembalikan pesan generik yang sama, termasuk ketika email tidak dikenal, tidak memenuhi syarat atau pengiriman gagal. `challenge_id` dan kode publik diperoleh **dari email**, bukan respons registrasi. `auth/otp/verify/` hanya untuk verifikasi Reporter. Aktivasi Operator dan reset password mengonsumsi challenge secara atomik bersama perubahan akun. Verifikasi tidak otomatis melakukan login dan bukan 2FA saat login.

Nilai awal: OTP 10 menit; resend 60 detik; 5 percobaan salah dan 5 permintaan kirim per akun/purpose selama 15 menit; pembatasan IP tambahan. Counter verifikasi tetap berlaku setelah resend. Kode lama dicabut ketika kode baru dibuat. Angka dapat dikonfigurasi melalui `.env` sesuai hasil uji tim.

Admin awal memperoleh lima izin administrasi, tanpa `view_private_evidence` dan tanpa izin Operator. Opsi CLI `create_silar_admin --grant-private` atau `--grant-operator` merupakan pemberian hak terpisah melalui prosedur tepercaya. Admin berizin Operator tetap memerlukan assignment untuk tindakan laporan. Tidak ada endpoint untuk mengubah Reporter menjadi Admin.

## Kesiapan integrasi

| Komponen | Isi paket | Lanjutan |
| --- | --- | --- |
| FR01 / AK01–AK07 | Registrasi, OTP, aktivasi, reset, login/refresh/logout, profil; API nyata | Tim frontend menghubungkan layar akun |
| FR23 / AD03 | Layanan audit atomik dan API baca Admin berizin | Setiap layanan bisnis menambahkan event audit |
| FR02 / AD01 | Layanan/API akun Operator, katalog tujuh izin, aktivasi/nonaktif; dukungan SLR_08 | Antarmuka dan penerimaan FR02 tetap SLR_13 |
| Skema A4/A8 | Seluruh model bisnis, ledger, FK/pointer siklik, constraint, indeks, migration | Digunakan pemilik card berikutnya |
| NFR01 | Pemeriksaan akun aktif/verified, peran, izin eksplisit, ownership/assignment dan proyeksi | Wajib dipanggil pada endpoint bisnis berikutnya |
| Revision/idempotency/kapasitas | Helper dan pengujian integritas | Orkestrasi request/finalisasi pipeline SLR_11 |
| FR03/04 | Helper storage privat dan model sumber | API draft/upload/bundle/media SLR_10 |
| FR05–FR13 | Model versi/run/hasil/konfirmasi tersedia | Inferensi SLR_11, koreksi/submit SLR_12 |
| FR14/15 | Model riwayat/notifikasi tersedia | API riwayat dan notifikasi SLR_12 |
| Penanganan dan publikasi | Model, constraint dan helper akses | Endpoint bisnis SLR_13–SLR_14 |
| Portal, PWA, monitoring AI | Belum diimplementasikan | Card fitur dan deployment terkait |

Endpoint yang belum dibangun tidak mengembalikan hasil contoh seolah layanan nyata. Kontrak OpenAPI hanya berisi endpoint yang tersedia. `/health/` memeriksa database; endpoint tersebut tidak menyatakan Whisper/Gemini/SENA/NARA sudah siap.

## Struktur dan konfigurasi

Kode berada di `code/backend`; dokumentasi berada di `docs/backend`. Entry point `manage.py`, konfigurasi `config/settings.py`, akun `accounts`, model/layanan bersama `core`, serta envelope/middleware `common`. File [openapi.json](openapi.json) dapat diimpor ke alat pengujian API. Contoh request ada di [examples/akun.http](examples/akun.http).

Dependency utama dikunci: Django 5.2.18, DRF 3.16.1, Simple JWT 5.5.1, psycopg 3.3.6, django-cors-headers 4.9.0 dan python-dotenv 1.2.4. Dependency transitif juga dikunci di `requirements.txt`; `pip check` lulus pada lingkungan uji. Perubahan versi perlu diuji kembali.

`.env` memuat `SECRET_KEY`, `JWT_SIGNING_KEY` dan `OTP_HMAC_KEY` berbeda, kredensial database serta konfigurasi SMTP. Jangan membagikan file itu. Contoh hanya berisi placeholder; setup membuat nilai acak. `private_media`, `private_outbox` dan `model_assets` terpisah dari file web dan diabaikan Git. Hak file POSIX diperketat; pada Windows pertahankan ACL folder hanya untuk akun pengembang/proses yang memerlukan.

Mode lokal mengizinkan HTTP localhost dan cookie tanpa `Secure`. Mode nonlokal mewajibkan HTTPS untuk URL frontend, cookie Secure dan pengalihan HTTPS; file email dinonaktifkan. Pengaturan reverse proxy, SMTP nyata, backup, retensi, kapasitas dan proses server produksi mengikuti SLR_15/16, belum diuji sebagai deployment dalam paket ini.

## Pengujian dan pemulihan lokal

```bat
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test --settings=config.test_settings
.venv\Scripts\python.exe -m pip check
```

Runner membuat database `test_<DB_NAME>` tersendiri. Jangan gunakan nama itu untuk data pekerjaan tim. Jika database pengujian sudah ada, Django meminta keputusan pengguna; jangan menyetujui penghapusan jika database tersebut ternyata berisi data penting. `config.test_settings` menggunakan hasher cepat hanya untuk pengujian; menjalankan layanan selalu memakai `config.settings`.

Untuk mencabut seluruh sesi akun: `.venv\Scripts\python.exe manage.py revoke_silar_sessions alamat@example.com`. Logout biasa mencabut refresh sesi tersebut; access token dapat tetap berlaku sampai TTL. Reset password atau perintah pencabutan seluruh sesi menaikkan `auth_version`, sehingga access dan refresh lama ditolak pada request berikutnya.

Jika koneksi ditolak, periksa service PostgreSQL 16 dan port `.env`. Jika `CSRF_FAILED`, ambil ulang CSRF dan pastikan cookie, header, origin serta hostname konsisten. Jika respons OTP tetap generik, periksa email lokal terbaru dan cooldown; jangan mengubah respons API untuk membuka identitas akun.

Penjelasan skema dan helper ada di [database-dan-layanan.md](database-dan-layanan.md). Checklist pengumpulan dan penempatan repository ada di [penyerahan.md](penyerahan.md).
