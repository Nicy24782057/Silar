# Menjalankan SILAR dari awal

Panduan Windows/PowerShell, 13 November 2026. Folder utama adalah folder `Silar` yang berisi `code/`, `tools/`, dan `SETUP_SILAR.bat`.

## 1. Siapkan perangkat lunak

| Kebutuhan | Persiapan |
| --- | --- |
| Git | Untuk mengambil dan memperbarui repository. |
| Python | Gunakan **Python 3.12** beserta Python Launcher. Periksa dengan `py -3.12 --version`. |
| PostgreSQL | Pasang **PostgreSQL 16**, jalankan servicenya, dan siapkan kredensial administrator untuk instalasi database baru. |
| Node.js/npm | Gunakan versi yang sesuai `code/frontend/package.json`: `^20.19.0` atau `>=22.12.0`. Pengujian revisi ini memakai Node 24. |
| FFmpeg/FFprobe | Setup mencoba memasangnya melalui WinGet di Windows jika belum tersedia. Pemeriksaan akhir harus berhasil menjalankan keduanya. |
| Internet dan ruang disk | Paket AI CPU berukuran besar. Siapkan waktu unduh dan ruang untuk paket serta aset model. |

Jika PostgreSQL berbeda versi terpasang bersamaan, masukkan **port instance PostgreSQL 16**. Port tidak menentukan versinya. Pada instalasi tim sebelumnya, PostgreSQL 16 memakai `5433` sedangkan `5432` dipakai versi lain.

```powershell
git clone https://github.com/Nicy24782057/Silar.git
cd Silar
```

## 2. Jalankan satu setup lengkap

Dari folder utama:

```powershell
py -3.12 tools/setup_silar.py
```

Alternatif: klik dua kali **`SETUP_SILAR.bat`**. Tombol lama `code/backend/SETUP_LOKAL.bat` dan perintah lama `tools/setup_slr10.py` juga mengarah ke setup lengkap ini.

Setup mengerjakan tiga tahap:

1. Jika `.env` belum tersedia, meminta koneksi PostgreSQL 16, membuat database/role baru dan rahasia acak. Konfigurasi yang sudah ada dipakai kembali. Database lama tidak direset.
2. Memasang dependensi backend **dan AI** dalam `.venv` backend, menyiapkan FFmpeg/FFprobe, menerapkan migration, menyiapkan katalog izin, memasang paket frontend dan membangun frontend.
3. Memeriksa versi paket, impor `av`, `numpy`, `psutil`, decoder, PostgreSQL 16 dan migration yang belum diterapkan. Kegagalan langkah ini menghasilkan status setup gagal.

Tetap baca hasil pada terminal sampai selesai. Pesan fondasi backend selesai belum berarti semua paket AI/frontend tersedia. `code/backend/scripts/setup_local.py` adalah pembantu fondasi yang dipanggil setup lengkap, bukan pintu instalasi lengkap.

Untuk memeriksa ulang tanpa pemasangan atau perubahan database:

```powershell
py -3.12 tools/setup_silar.py --check
```

Pemeriksaan ini tidak mengunduh model, menjalankan inferensi, atau mengirim email. Keberhasilan pemasangan paket tidak membuktikan inferensi AI maupun pengiriman SMTP sudah berhasil.

## 3. Siapkan aset dan konfigurasi AI

Pemasangan paket berbeda dari pemasangan bobot model. Aset bawaan disimpan pada:

- `code/backend/model_assets/sena/`
- `code/backend/model_assets/nara/`
- `code/backend/model_assets/whisper-small/`

Ikuti prosedur aset pada [panduan integrasi AI SLR11](docs/ai/slr11/SLR11_Integrasi_dan_Verifikasi_v0.1.md). Gunakan adapter, manifest dan versi yang sudah ditetapkan proyek. Path khusus dapat diisi melalui `SENA_MODEL_DIR`, `NARA_MODEL_DIR`, `WHISPER_MODEL_DIR`, dan `SILAR_SLR09_ROOT`.

Folder `models/` menyimpan arsip sumber SENA/NARA, sedangkan backend membaca hasil ekstraksinya pada folder `model_assets/` di atas. Keberadaan arsip belum berarti model sudah siap dimuat. Dari `code/backend`, verifikasi dan ekstrak arsip menggunakan command proyek:

```powershell
.\.venv\Scripts\python.exe manage.py prepare_ai_models
```

Command memeriksa hash arsip serta berkas runtime terhadap manifest SLR09. Jika berkas tujuan yang sudah ada berbeda, command berhenti untuk diperiksa; tidak menimpanya otomatis. Arsip SENA/NARA memakai Git LFS. Jika ukuran arsip hanya sekitar 134 byte, unduh isi LFS terlebih dahulu. Ukuran arsip yang dipilih proyek adalah SENA 412.184.854 byte dan NARA 408.238.634 byte; ukuran cocok belum menggantikan pemeriksaan hash.

Untuk audio, siapkan Whisper secara terpisah. Command berikut dapat mengunduh model dari Hugging Face dan mencatat manifest lokal; memerlukan internet serta ruang disk tambahan:

```powershell
.\.venv\Scripts\python.exe manage.py prepare_ai_models --whisper-only --whisper-revision 536b0662742c02347bc0e980a01041f333bce120
```

Runtime aplikasi ini menggunakan CPU untuk SENA/NARA dan CPU `int8` untuk Whisper. NVIDIA/CUDA bukan syarat untuk konfigurasi tersebut. Model dimuat oleh backend ketika diperlukan; tidak ada server model terpisah yang harus dijalankan. Mulai ulang backend sesudah menyiapkan model atau mengganti konfigurasi, lalu coba analisis teks dahulu sebelum audio/foto/kombinasi.

Isi `GEMINI_API_KEY` dan model yang sesuai pada `.env` untuk pemrosesan foto/kombinasi kanal. Teks dan audio tunggal tidak memakai Gemini. Analisis tidak mengunduh aset otomatis.

## 4. Pilih pengiriman email

Reporter dan Operator menggunakan backend pengiriman yang sama.

| Pengaturan | Tempat menerima pesan |
| --- | --- |
| `EMAIL_MODE=file` | Berkas `.eml` pada `code/backend/private_outbox/`; pesan belum dikirim ke Gmail. Hanya untuk pengujian lokal. |
| `EMAIL_MODE=smtp` | Email dikirim melalui layanan pengirim yang dikonfigurasi, menuju alamat penerima, termasuk Gmail. |

Untuk pengiriman sungguhan, atur konfigurasi SMTP sesuai penyedia akun pengirim. Contoh nama pengaturan:

```dotenv
EMAIL_MODE=smtp
EMAIL_HOST=smtp.penyedia-pengirim.example
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=akun-pengirim@example.com
EMAIL_HOST_PASSWORD=ISI_KREDENSIAL_SMTP_LOKAL
DEFAULT_FROM_EMAIL=SILAR <akun-pengirim@example.com>
```

Alamat host di atas adalah placeholder. Penyedia SMTP pengirim tidak harus Gmail agar penerima Gmail dapat menerima pesan. Jika memakai Gmail sebagai pengirim dan metode App Password tersedia untuk akun tersebut, ikuti [petunjuk resmi Google](https://support.google.com/mail/answer/185833). Metode tersebut memerlukan Verifikasi 2 Langkah dan dapat dibatasi oleh kebijakan akun. Isi kredensial secara lokal pada `.env`, lalu mulai ulang backend.

Pada frontend development, bantuan folder lokal dapat disembunyikan dengan `VITE_AUTH_LOCAL_HELP=false` di `code/frontend/.env.local`. Pengaturan itu hanya mengatur petunjuk, bukan cara pengiriman.

## 5. Buat Admin pertama

Dari folder utama setelah setup lengkap:

```powershell
code/backend/.venv/Scripts/python.exe code/backend/manage.py create_silar_admin
```

Pilih email dan kata sandi sendiri. Tidak ada sandi bawaan. Sandi baru minimal **15 karakter**, serta diperiksa terhadap sandi umum dan pola mudah ditebak. Gunakan beberapa kata yang tidak berkaitan. Menambahkan angka/simbol pada nama tidak otomatis membuatnya layak.

Admin membuat Operator melalui **Manajemen Operator**. Email aktivasi dikirim melalui mode yang dipilih pada langkah 4. Operator memasukkan email dan kode pada halaman Verifikasi akun, kemudian membuat kata sandinya sendiri. Akun belum aktif sebelum kata sandi berhasil disimpan.

## 6. Jalankan aplikasi setiap hari

Terminal backend, dari `code/backend`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver localhost:8001 --noreload
```

Terminal frontend terpisah, dari `code/frontend`:

```powershell
npm.cmd run dev
```

Buka **http://localhost:5173**. Pertahankan nama host `localhost` saat memakai konfigurasi origin tersebut.

Reporter mendaftar lalu langsung menuju formulir kode dengan email terisi. Ambil kode dari email terbaru dan masukkan di aplikasi. Tautan email hanya jalan pintas. **Login → Verifikasi akun** digunakan untuk melanjutkan proses yang belum selesai. Halaman yang sama menangani Reporter dan Operator tanpa pilihan peran.

Kode berlaku 10 menit secara bawaan, dengan 5 pemeriksaan per akun/keperluan dalam 15 menit. Kirim ulang memiliki jeda 60 detik dan batas 5 permintaan per 15 menit. Meminta kode baru tidak menghapus hitungan pemeriksaan; kode sebelumnya menjadi tidak berlaku. Nilai aktual mengikuti konfigurasi backend dan ditampilkan pada halaman kode.

Ruang kerja Operator terdiri atas **Pemeriksaan → Tindak lanjut → Keputusan**. Ringkasan, narasi, bukti dan formulir review berada di Pemeriksaan. Setelah review tersimpan dan dibaca kembali, aplikasi otomatis membuka Tindak lanjut. Tindak lanjut tidak wajib ditambahkan. Publikasi tetap memerlukan pemeriksaan pratinjau, konfirmasi, dan tindakan menerbitkan. Riwayat dibuka melalui tombol tersendiri.

## 7. Memasang pembaruan kode

Hentikan kedua server, gabungkan pembaruan sesuai path, lalu jalankan setup lengkap pada langkah 2. Pertahankan `.env`, media privat, database, dan model yang sudah tersedia.

Revisi akun ini menambah migration `accounts.0002_emailotp_activation_auth_version_and_more`. Jika paket/dependensi sudah lengkap, penerapan migration dapat dijalankan dari terminal backend:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
```

Frontend perlu dibangun kembali setelah perubahan source:

```powershell
npm.cmd run build
```

Pada PWA yang sudah terpasang, gunakan pembaruan pada menu Aplikasi & Koneksi, lalu buka kembali aplikasi.

## 8. Menjalankan pengujian

Dari `code/backend`, PostgreSQL 16 dengan role yang memiliki hak membuat database uji:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --include-pipeline-integration
.\.venv\Scripts\python.exe manage.py test accounts.tests accounts.test_account_flow --settings=config.test_settings --verbosity=2
```

Perintah pertama menjalankan 152 tes pada database terpisah, termasuk 9 tes integrasi dengan klien model/provider simulasi. Hasil JSON berada di `docs/slr14/hasil-postgresql/`. Ini tidak membuktikan model asli atau Gmail sudah berjalan. Pengujian akun mencakup OTP, aktivasi, sandi, pembatasan dan permintaan bersamaan.

Dari `code/frontend`:

```powershell
npm.cmd test
npm.cmd run build
```

## 9. Jika ada masalah

| Gejala | Pemeriksaan |
| --- | --- |
| Setup dasar selesai tetapi paket audio belum tersedia | Gunakan setup lengkap pada langkah 2. `requirements.txt` saja tidak memuat seluruh paket AI. |
| `AI_CONFIGURATION_NOT_READY` hanya pada rute audio dalam tes integrasi | Periksa impor `.\.venv\Scripts\python.exe -c "import av,numpy; print(av.__version__,numpy.__version__)"`. Versi acuan ada di `requirements-ai.txt`. |
| Verifikasi terhenti pada identitas proses | Periksa `psutil` pada venv yang dipakai. Pertahankan pemeriksaan identitas proses; jangan menggantinya dengan identitas palsu. |
| Server PostgreSQL salah versi | Cocokkan port `.env` dengan instance mayor 16. |
| Python venv menunjuk instalasi lama yang sudah hilang | Siapkan ulang venv dengan Python 3.12 sambil mempertahankan `.env`, database dan model. |
| Kode tidak masuk Gmail | Periksa `EMAIL_MODE`. Mode berkas hanya membuat `.eml`. Untuk SMTP, periksa layanan/kredensial pengirim, spam, dan batas layanan. |
| Kode salah atau sudah dipakai | Gunakan email yang benar dan kode pesan terbaru; minta kode baru setelah jeda bila perlu. |
| Login masih menampilkan antarmuka lama | Perbarui source, bangun ulang frontend, lalu perbarui PWA. |

[Catatan perubahan dan bukti revisi SLR15](docs/slr15/revisi-20261113/README.md). [Arsip panduan sebelum revisi](docs/archive/PANDUAN_RUNNING_20261024.md).
