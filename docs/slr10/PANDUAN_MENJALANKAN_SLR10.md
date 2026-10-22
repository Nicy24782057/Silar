# Panduan Menjalankan SILAR — SLR_10 di Windows

Panduan ini menyatukan perintah dari file `.bat` pendukung SLR_10. Salin perintah ke **CMD** dan jalankan satu per satu. File `.bat` menjalankan perintah secara otomatis; Markdown menjadi panduan untuk menjalankannya secara manual.

Lokasi yang disarankan dalam repository: `docs/slr10/PANDUAN_MENJALANKAN.md`.

## 1. Persiapan

- Python 3.13 dan fondasi backend SLR_08 sudah tersedia.
- PostgreSQL aktif dan `code/backend/.env` sesuai database laptop masing-masing. Pada laptop Maulana, PostgreSQL 16 memakai port **5433**.
- Node.js/npm diperlukan untuk membangun atau mengubah frontend serta menjalankan tes frontend. Sesuai `package.json`, Node yang didukung adalah `^20.19.0 || >=22.12.0`.
- Hasil clone/pull GitHub memerlukan build frontend karena `code/frontend/dist/` diabaikan Git. ZIP SLR_10 versi 1.1.0 menyertakan `dist`, sehingga frontend bawaannya dapat dijalankan tanpa Node.js.
- Decoder FFmpeg/FFprobe diperlukan untuk validasi format audio seperti MP3, WebM/Opus dan M4A/MP4-AAC. Setup mencoba menyiapkannya melalui WinGet bila tersedia.

Semua contoh memakai lokasi berikut. Sesuaikan path jika repository berada di tempat lain:

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar"
```

Jika `.env` backend belum tersedia, selesaikan penyiapan SLR_08 terlebih dahulu mengikuti `docs/backend/README.md`.

## 2. Menyiapkan SLR_10

Dari folder utama repository, jalankan:

```cmd
py -3.13 tools\setup_slr10.py
```

Perintah ini setara dengan `SIAPKAN_SLR10.bat`: menyiapkan virtual environment bila belum ada, memasang dependensi tambahan, menyelaraskan origin frontend lokal, menjalankan pemeriksaan/migration/bootstrap backend, serta membangun frontend jika npm tersedia. Jika `requirements-ai.txt` tersedia, dependensi SLR_10 dan AI dipasang dalam satu resolver.

Tunggu sampai muncul **Persiapan selesai**. Jika gagal, perbaiki pesan kegagalan sebelum melanjutkan. Setup dijalankan saat pemasangan awal atau setelah perubahan dependensi/konfigurasi yang memerlukannya.

## 3. Menjalankan backend — CMD pertama

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar\code\backend"
.venv\Scripts\python.exe manage.py runserver localhost:8001
```

Setara dengan `JALANKAN_BACKEND.bat`. Biarkan CMD ini terbuka. Backend menggunakan `http://localhost:8001`.

## 4. Menjalankan frontend — CMD kedua

### Pilihan A: menjalankan hasil build

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar"
py -3.13 tools\serve_frontend.py
```

Setara dengan `JALANKAN_FRONTEND_BAWAAN.bat`. Skrip menyajikan `code/frontend/dist/` dan meneruskan permintaan `/api/` ke backend lokal. Biarkan CMD ini terbuka.

### Pilihan B: mengembangkan frontend

Gunakan pilihan ini saat mengedit kode Vue, sebagai pengganti pilihan A:

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar\code\frontend"
npm run dev
```

Setara dengan `JALANKAN_FRONTEND_DEV.bat`. Dependensi npm harus sudah terpasang melalui setup atau `npm ci --ignore-scripts`.

Kedua pilihan memakai port **5173**; jalankan satu pilihan frontend pada satu waktu.

### Membuka aplikasi

Buka **http://localhost:5173** di browser. Gunakan hostname `localhost` secara konsisten. Setelah memperbarui build, tekan **Ctrl+F5**.

Untuk mencoba PWA, gunakan hasil build melalui pilihan A.

## 5. Membuka email OTP/reset lokal

Jika backend memakai `EMAIL_MODE=file`, buka CMD tambahan lalu jalankan:

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar\code\backend"
powershell -NoProfile -Command "Get-ChildItem '.\private_outbox\*.eml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { notepad.exe $_.FullName }"
```

Setara dengan `BUKA_EMAIL_LOKAL.bat`. Perintah membuka email terbaru di Notepad. Jika belum ada email, lakukan registrasi/resend/reset melalui antarmuka terlebih dahulu. Jika memakai SMTP, periksa kotak masuk email penerima.

## 6. Pengujian otomatis

Jalankan tahap berikut satu per satu dari CMD tambahan. Lanjutkan ke tahap berikutnya setelah tahap sebelumnya berhasil.

### Tes alat pemasangan

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar"
py -3.13 -m unittest discover -s tools\tests -v
```

### Tes backend pada database PostgreSQL yang dikonfigurasi

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar\code\backend"
.venv\Scripts\python.exe manage.py test --settings=config.test_settings --verbosity=1
```

Django menggunakan database pengujian; akun database memerlukan izin yang sesuai untuk membuatnya.

### Tes dan build frontend

```cmd
cd /d "C:\Users\A C E R\Documents\KULIAH\PEMROGRAMAN INTERNET II\Silar\code\frontend"
npm test
npm run build
```

Rangkaian ini setara dengan `UJI_SLR10.bat`. Tes/build frontend memerlukan Node.js/npm. Catat hasil yang benar-benar dijalankan di `docs/slr10/`; hasil pengujian lingkungan lain tersedia pada `HASIL_VERIFIKASI.md`.

## 7. Uji alur Reporter

1. Login sebagai Reporter terverifikasi.
2. Buat draft dan simpan teks; coba unggah gambar PNG/JPEG serta audio yang didukung.
3. Tutup tab setelah bukti tersimpan, sebelum membuat bundle.
4. Buka kembali aplikasi dan draft. Pastikan bukti dapat dibaca tanpa upload ulang.
5. Pilih bukti dan buat Evidence Bundle melalui tindakan eksplisit.
6. Periksa keadaan offline dan tampilan responsif. Draft, evidence dan API tetap memerlukan koneksi.

Analisis nyata memerlukan modul serta aset SLR_11. Ikuti `docs/slr10/INTEGRASI_SLR11.md` untuk penggabungan dan pengujiannya.

## 8. Memasang isi ZIP ke repository — opsional

Tahap ini khusus pemasangan dari paket ZIP ke repository tujuan. Jika kode sudah diperoleh melalui clone/pull GitHub atau sudah terpasang, lanjutkan dari bagian persiapan dan setup.

Buka CMD pada folder hasil ekstraksi yang berisi `tools/install_slr10.py`, kemudian jalankan:

```cmd
py -3.13 tools\install_slr10.py
```

Setara dengan `PASANG_KE_REPO.bat`. Saat diminta, masukkan path folder utama repository tujuan. Setelah pemasangan selesai, jalankan setup dari repository tujuan.

## 9. Menghentikan aplikasi dan mengelola panduan

Tekan **Ctrl+C** pada masing-masing CMD backend/frontend sampai server berhenti.

Panduan Markdown ini menyediakan perintah pengganti launcher `.bat` SLR_10. Pertahankan kode `tools/`, `code/frontend/` dan `code/backend/` karena perintah di atas menggunakannya. Jika tim merapikan launcher di repository, sesuaikan juga tautan/petunjuk pada dokumentasi dan paket rilis. `README.md` utama tetap menjadi pengantar proyek.
