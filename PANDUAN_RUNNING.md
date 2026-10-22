# Panduan menjalankan SILAR — SLR10 1.1.1

Windows/PowerShell, 22 Oktober 2026. Gunakan Python **3.12** dan PostgreSQL **16** sesuai lingkungan SLR11 yang sudah berhasil. Backend: `http://localhost:8001`. Frontend: `http://localhost:5173`.

Untuk pemakaian sehari-hari setelah konfigurasi selesai, langsung ke **bagian C**. Folder repository adalah folder utama yang berisi `code/` dan `tools/`.

## A. Memasang pembaruan ke repository yang sudah berjalan

1. Hentikan kedua server dengan `Ctrl+C` pada masing-masing terminal.
2. Ekstrak ZIP 1.1.1 ke folder sementara yang terpisah dari repository tujuan. Buka PowerShell pada folder `SLR_10_SILAR` hasil ekstraksi.
3. Periksa rencana pemasangan:

```powershell
$SilarTujuan = Read-Host "Tempel path folder utama repository Silar yang sudah digunakan"
py -3.12 tools/install_slr10.py --target "$SilarTujuan" --dry-run
```

Jika muncul konflik, baca nama berkas yang disebut dan selesaikan perbedaannya dahulu. Jika pemeriksaan berhasil dan rencananya sesuai, pasang:

```powershell
py -3.12 tools/install_slr10.py --target "$SilarTujuan"
Set-Location "$SilarTujuan"
```

Installer mengenali paket 1.0.0 dan 1.1.0, termasuk LF/CRLF yang diketahui. Launcher root, aset build lama, dan berkas distribusi yang sudah tidak dipakai hanya dihapus jika hash-nya dikenal; salinannya dicadangkan dalam `.slr10-backups/`. Perubahan lokal yang tidak dikenal menghentikan preflight sebelum penyalinan. `.env`, venv, database, model, media privat, serta kode dan requirements SLR11 dipertahankan.

## B. Menyiapkan dependensi setelah pembaruan

Jalankan dari folder utama repository tujuan:

```powershell
py -3.12 tools/setup_slr10.py
```

Script menggunakan venv backend yang sudah ada dan menyelesaikan dependensi SLR10 bersama `requirements-ai.txt` bila tersedia. Script memeriksa Django, menerapkan migration yang belum terpasang, menjalankan bootstrap idempoten, serta menyiapkan frontend. Koneksi database dan secret lokal dipertahankan.

Instalasi lokal tim yang sudah berhasil menggunakan PostgreSQL 16 pada **port 5433**. Jangan mengganti `.env` yang sudah benar dengan `.env.example`, menghapus venv/database, atau mengunduh ulang model untuk pembaruan SLR10 ini.

FFmpeg/FFprobe diperlukan untuk MP3, WebM/Opus, dan M4A/MP4-AAC. Jika decoder belum terbaca:

```powershell
ffmpeg -version
ffprobe -version
```

Script setup dapat mencoba pemasangan `Gyan.FFmpeg` melalui WinGet pada Windows. Jika gagal, sediakan FFmpeg/FFprobe lalu jalankan setup kembali. WAV PCM tertentu tetap dapat dibaca modul `wave` Python tanpa FFmpeg.

Jika Node/npm tersedia, setup membangun frontend. Build bawaan dapat digunakan bila Node/npm belum tersedia; Node/npm diperlukan untuk perubahan dan pembangunan ulang frontend.

### Hanya untuk instalasi baru tanpa `.env`

Lewati bagian ini pada laptop yang konfigurasi database/SLR11-nya sudah berhasil. Untuk repository baru, sediakan PostgreSQL 16, lalu dari root:

```powershell
py -3.12 code/backend/scripts/setup_local.py
```

Masukkan host/port server yang benar; instalasi lokal tim memakai `127.0.0.1:5433`. Ikuti prompt database baru hanya untuk instalasi baru. Lanjutkan setup pada awal bagian B. Jika memerlukan akun Admin baru:

```powershell
code/backend/.venv/Scripts/python.exe code/backend/manage.py create_silar_admin
```

Tidak ada username/password bawaan yang dibagikan dalam paket.

## C. Menjalankan aplikasi setiap hari

### Terminal 1 — backend

Buka PowerShell dari root repository:

```powershell
Set-Location code/backend
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py runserver localhost:8001 --noreload
```

Biarkan terminal terbuka. Hanya jika PowerShell menolak aktivasi script, gunakan kebijakan untuk sesi terminal ini:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Alternatif tanpa aktivasi, dari direktori backend:

```powershell
.\.venv\Scripts\python.exe manage.py runserver localhost:8001 --noreload
```

### Terminal 2 — frontend build bawaan

Buka terminal kedua dari root repository:

```powershell
py -3.12 tools/serve_frontend.py
```

Buka **http://localhost:5173**. Server menyajikan build Vue dan meneruskan `/api/` ke backend port 8001. Gunakan hostname `localhost` secara konsisten untuk cookie/CSRF. Server bawaan ditujukan untuk pengembangan/demo lokal.

### Pilihan frontend development

Gunakan sebagai pengganti server build bawaan; pilih satu server pada port 5173. Dari root repository:

```powershell
Set-Location code/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run dev
```

`npm ci` diperlukan saat menyiapkan dependensi atau lockfile berubah. Sesi berikutnya cukup `npm run dev`. Engine mengikuti `package.json`: Node 20 mulai 20.19.0, atau Node mulai 22.12.0. Setelah mengubah source frontend, bangun ulang dari `code/frontend`:

```powershell
npm run build
```

Untuk menghentikan aplikasi tekan `Ctrl+C` di kedua terminal. Keluar dari venv backend dengan `deactivate`.

## D. Akun dan email lokal

Daftar Reporter melalui frontend dan gunakan OTP email terbaru. Pada `EMAIL_MODE=file`, email disimpan lokal di `code/backend/private_outbox/`. Dari root repository:

```powershell
Invoke-Item code/backend/private_outbox
```

Urutkan berdasarkan waktu dan buka berkas terbaru dengan editor teks. Gunakan OTP/tautan yang sesuai tindakan: verifikasi email, aktivasi Operator, atau reset password. Jangan memasukkan email lokal dan kredensial ke commit.

## E. Alur SLR10 dan penghubung SLR11

1. Login, buat atau lanjutkan draft.
2. Simpan teks, unggah/rekam audio, atau unggah PNG/JPEG.
3. Periksa bukti tersimpan, termasuk pemulihan sebelum bundle setelah draft ditutup/dibuka kembali.
4. Pilih bukti lalu bentuk bundle melalui tindakan eksplisit.
5. Jika SLR11 dan asetnya siap, jalankan analisis dan baca draft Incident Card tersimpan.

Audio: WAV PCM, MP3, WebM/Opus, M4A/MP4-AAC tanpa video/cover; maksimal 10 MiB dan isi hasil decode sampai 120 detik. Bundle maksimal satu teks, satu audio, tiga gambar; total 25 MiB termasuk byte teks. Bukti asli dipertahankan.

`reporting` dan `ai_pipeline` harus sama-sama terdaftar pada konfigurasi gabungan. Lihat `docs/slr10/INTEGRASI_SLR11.md`. Pertahankan konfigurasi model/Whisper/Gemini yang sudah berhasil; revisi SLR10 ini tidak memerlukan penyiapan ulang bobot model.

Jika respons analisis terputus, baca status/hasil tersimpan. RUNNING/UNKNOWN tidak diulang otomatis. Koreksi, Human Verification, konfirmasi, dan submit resmi mengikuti SLR12.

## F. Pengujian sesuai perubahan

Hasil aktual revisi ada di `docs/slr10/HASIL_VERIFIKASI.md`. Pengujian frontend/PWA 1.1.0 tetap menjadi bukti untuk source logika yang sama. Tidak perlu mengulang seluruh tes hanya untuk menjalankan aplikasi.

Jika mengubah validator audio, jalankan dari terminal backend dengan venv aktif:

```powershell
python manage.py test reporting.tests.test_media reporting.tests.test_audio_api --settings=config.test_settings --verbosity=2
```

Perintah ini memakai PostgreSQL dari `.env` dan migration asli. Pastikan role database pengujian tim memiliki izin yang sesuai. SQLite terisolasi pada penyusunan paket hanya membuktikan komponen.

Jika mengubah installer/manifest, jalankan dari root:

```powershell
py -3.12 -m unittest discover -s tools/tests -v
```

Jika mengubah logika frontend/PWA, jalankan dari `code/frontend`:

```powershell
npm test
npm run build
```

Untuk penerimaan gabungan terbaru, lakukan regresi PostgreSQL dan alur AI bersama SLR11 sesuai perubahan yang digabung. Catat hasil aktual sebelum menutup card.

## G. Pemecahan masalah

| Gejala | Tindakan |
| --- | --- |
| Port 5173 dipakai | Hentikan frontend lama; pilih satu server frontend. |
| Backend tidak terhubung | Pastikan Django berjalan di localhost:8001. |
| NOT_FOUND pada root backend | Buka frontend localhost:5173; root backend bukan halaman aplikasi. |
| Konflik installer | Tinjau berkas yang disebut; pertahankan pekerjaan lokal/rekan. |
| PostgreSQL mayor salah atau koneksi ditolak | Periksa server PostgreSQL 16, host, dan port 5433 pada `.env` instalasi tim. |
| Decoder belum tersedia | Periksa FFmpeg/FFprobe atau gunakan WAV PCM yang didukung. |
| Analisis belum tersedia | Periksa app/URL SLR11 dan konfigurasi aset; bukti/bundle tetap tersimpan. |
| Aset lama masih terlihat | Tutup tab lama, buka kembali, dan Ctrl+F5; periksa pembaruan PWA bila terpasang. |

`.env`, `.venv`, private outbox/media, aset model, node_modules, dan backup lokal tidak termasuk ZIP rilis. Dokumentasi hasil pengujian menjelaskan batas penerimaan revisi.
