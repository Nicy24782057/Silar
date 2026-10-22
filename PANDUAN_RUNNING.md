# Panduan menjalankan SILAR — SLR10 dan SLR11

Windows/PowerShell, 22 Oktober 2026. Gunakan Python **3.12** dan PostgreSQL **16** sesuai lingkungan SLR11 yang sudah berhasil. Backend: `http://localhost:8001`. Frontend: `http://localhost:5173`.

Untuk pemakaian sehari-hari setelah konfigurasi selesai, langsung ke **bagian C**. Folder repository adalah folder utama yang berisi `code/` dan `tools/`.

## A. Memasang integrasi SLR10 dan SLR11

1. Hentikan kedua server dengan `Ctrl+C` pada masing-masing terminal.
2. Ekstrak paket integrasi 0.2.0 ke folder sementara di luar repository tujuan. Buka PowerShell pada folder yang berisi `terapkan_integrasi.py` dan `integrasi-manifest.json`.
3. Periksa rencana pemasangan:

```powershell
$SilarTujuan = Read-Host "Tempel path folder utama repository Silar yang sudah digunakan"
py -3.12 .\terapkan_integrasi.py --target "$SilarTujuan" --dry-run
```

Jika muncul konflik, baca nama berkas yang disebut dan selesaikan perbedaannya dahulu. Jika pemeriksaan berhasil dan rencananya sesuai, pasang:

```powershell
py -3.12 .\terapkan_integrasi.py --target "$SilarTujuan"
Set-Location "$SilarTujuan"
```

Pemasang memeriksa seluruh berkas sebelum menulis. Sumber dari commit dasar yang dikenal serta paket awal SLR11 dikenali dalam LF/CRLF; berkas yang sudah sama tidak disalin ulang. Perubahan lokal yang belum dikenal menghentikan seluruh preflight. Berkas yang diganti/dihapus dicadangkan dalam `.slr11-backups/`. `.env`, venv, database, model, media privat dan berkas di luar daftar perubahan tidak disentuh.

Jika perubahan integrasi sudah didapat melalui Git, mulai dari bagian B. Jangan menjalankan installer ZIP SLR10 lama pada source gabungan; `tools/release-manifest.json` tetap merekam distribusi SLR10 1.1.1, sedangkan paket integrasi memakai `integrasi-manifest.json` sendiri.

## B. Menyiapkan dependensi setelah pembaruan

Jalankan dari folder utama repository tujuan:

```powershell
py -3.12 tools/setup_slr10.py
```

Script menggunakan venv backend yang sudah ada dan menyelesaikan dependensi SLR10 bersama `requirements-ai.txt` bila tersedia. Script memeriksa Django, menerapkan migration yang belum terpasang, menjalankan bootstrap idempoten, serta menyiapkan frontend. Koneksi database dan secret lokal dipertahankan.

Instalasi lokal tim yang sudah berhasil menggunakan PostgreSQL 16 pada **port 5433**. Pertahankan `.env`, venv, database dan aset SLR11 yang sudah berhasil. `.env.example` hanya menjadi daftar konfigurasi; jangan menyalinnya menimpa `.env` yang sudah digunakan.

### Konfigurasi AI yang sudah ada

`reporting` dan `ai_pipeline` sudah didaftarkan bersama pada settings dan URL. Lokasi default aset lokal adalah `code/backend/model_assets/sena`, `nara`, dan `whisper-small`; kode adapter SLR09 dibaca dari `models/slr09/`. Override `MODEL_ASSET_ROOT`, `SILAR_SLR09_ROOT`, `SENA_MODEL_DIR`, `NARA_MODEL_DIR`, dan `WHISPER_MODEL_DIR` yang sudah benar tetap dipakai.

Pertahankan `GEMINI_API_KEY`, `GEMINI_MODEL` dan pengaturan Whisper yang sudah berhasil pada `.env` atau environment backend. Teks/audio tunggal tidak memakai Gemini; gambar dan kombinasi kanal memakai Gemini. Request analisis tidak mengunduh model otomatis. Jika aset belum disiapkan, ikuti prosedur penyiapan awal dalam `docs/ai/slr11/SLR11_Integrasi_dan_Verifikasi_v0.1.md`; langkah tersebut hanya untuk mesin yang belum memiliki aset, bukan langkah rutin setiap pembaruan.

Konfigurasi AI yang belum siap menghasilkan pesan aman pada analisis. Akun, draft, unggahan dan pembacaan bukti tetap tersedia.

FFmpeg/FFprobe diperlukan untuk MP3, WebM/Opus, dan M4A/MP4-AAC. Jika decoder belum terbaca:

```powershell
ffmpeg -version
ffprobe -version
```

Script setup dapat mencoba pemasangan `Gyan.FFmpeg` melalui WinGet pada Windows. Jika gagal, sediakan FFmpeg/FFprobe lalu jalankan setup kembali. WAV PCM tertentu tetap dapat dibaca modul `wave` Python tanpa FFmpeg.

Setup membangun frontend bila Node/npm tersedia. Repository Git dan paket perubahan integrasi tidak menyertakan `dist/`; jalankan build setelah memasang pembaruan. Node 20 mulai 20.19.0 atau Node mulai 22.12.0 mengikuti `package.json`.

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

### Terminal 2 — frontend hasil build

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

Jika respons analisis terputus, pilih **Periksa status dan hasil tersimpan**, lalu **Baca request ini** pada request yang relevan. Riwayat dipaginasi; gunakan **Muat riwayat berikutnya** bila diperlukan. Pilihan **Sertakan riwayat permintaan yang lebih lama** membuka metadata terminal yang masa replay-nya sudah habis.

Pembacaan ini hanya memakai GET request, run bila sudah memiliki referensi hasil, dan detail Report terbaru. Tidak ada replay atau analisis otomatis. RUNNING/UNKNOWN menahan analisis baru. Hasil Incident Card mengikuti sumber/versi draft terbaru; status request lama ditampilkan terpisah. Koreksi, Human Verification, konfirmasi dan submit resmi mengikuti SLR12.

## F. Pengujian sesuai perubahan

Hasil integrasi terbaru ada di `docs/ai/slr11/HASIL_INTEGRASI_v0.2.0.md`; hasil rilis SLR10 tetap berada di `docs/slr10/HASIL_VERIFIKASI.md`. Tidak perlu mengulang seluruh tes hanya untuk menjalankan aplikasi.

Untuk memverifikasi sambungan baru pada PostgreSQL 16 tim, gunakan terminal backend dengan venv aktif:

```powershell
python manage.py check
python manage.py test reporting.tests ai_pipeline.tests --settings=config.test_settings --verbosity=2
```

Perintah tersebut mencakup 15 tes transaksi/API SLR11 yang disediakan sebelumnya dan sembilan tes sambungan input-analisis baru. Pastikan izin database pengujian tersedia. Model/provider diganti secara eksplisit oleh suite ini; jalankan alur frontend dengan aset/kunci nyata untuk penerimaan inferensi. Pengujian komponen SQLite pada penyusunan paket tidak menggantikan hasil PostgreSQL.

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

Untuk penerimaan model nyata, gunakan tujuh kombinasi T, A, I, TA, TI, AI dan TAI melalui frontend. Catat versi model, sumber contoh, narasi, kategori/confidence, ekstraksi, status kartu serta waktu proses. Uji respons terputus, sumber berubah dan status tersimpan. Bukti fixture tidak dihitung sebagai penerimaan mutu AI; catat hasil aktual sebelum menutup card.

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

`.env`, `.venv`, private outbox/media, aset model, node_modules, dist dan backup lokal tidak termasuk paket perubahan integrasi. Dokumentasi hasil pengujian menjelaskan batas penerimaannya.
