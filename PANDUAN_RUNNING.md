# Panduan menjalankan SILAR — SLR10, SLR11 dan SLR12

Windows/PowerShell, diperbarui 24 Oktober 2026. Gunakan Python **3.12** dan PostgreSQL **16** sesuai lingkungan SLR11 yang sudah berhasil. Backend: `http://localhost:8001`. Frontend: `http://localhost:5173`.

Untuk pemakaian sehari-hari setelah konfigurasi selesai, langsung ke **bagian C**. Folder repository adalah folder utama yang berisi `code/` dan `tools/`.

## A. Memasang pembaruan pada clone

### Pembaruan tampilan SLR12 0.4.3

Paket `SLR12_SILAR_UI_v0.4.3.zip` menyesuaikan Login, Registrasi, Periksa Email sesudah registrasi dan Verifikasi OTP mengikuti empat SVG pengguna. Desktop memakai panel identitas SILAR di kiri dan formulir di kanan; HP memakai formulir satu kolom dengan logo ringkas. Revisi sebelumnya mengenai sidebar kiri, notifikasi ringkas, penguncian tahap dan Bukti aktif tetap disertakan. Paket kumulatif dapat diterapkan pada clone dengan SLR12 0.2.0 + UI 0.3.x atau UI 0.4.0–0.4.2.

1. Ekstrak ZIP ke folder sementara.
2. Gabungkan isi `code/frontend/` ke `Silar/code/frontend/`, isi `docs/slr12/` ke `Silar/docs/slr12/`, dan panduan ini ke root `Silar/`. Timpa file dengan path yang sama. ZIP adalah paket perubahan: jangan menghapus folder frontend atau menggantinya hanya dengan isi ZIP.
3. Dari terminal `Silar/code/frontend`, jalankan:

```powershell
npm.cmd run build
```

4. Jalankan frontend seperti bagian C. Pada server pengembangan, gunakan `npm.cmd run dev` dari folder frontend. Muat ulang halaman. Untuk PWA yang sudah terpasang, gunakan pembaruan di Aplikasi & Koneksi jika tersedia, kemudian buka kembali aplikasi.

Logo navigasi dan header HP tetap dibaca dari `code/frontend/public/brand/silar-logo.png`, dengan proporsi utuh tanpa pemotongan. Panel identitas akun memakai `code/frontend/src/assets/auth-identity.svg`, diturunkan dari ilustrasi/logo/wordmark SVG pengguna dengan latar gradien SVG yang lebih ringan. Tulisan navigasi SILAR memakai Manrope dan teks antarmuka memakai Poppins lokal.

**Paket tidak menimpa `public/brand/`, `public/icons/` atau `public/manifest.webmanifest`.** Logo dan ikon/manifest yang telah Anda sesuaikan tetap digunakan. Konfigurasi build mempertahankan perbaikan PWA 0.3.1 yang membaca aset yang benar-benar tersedia. Tidak ada dependensi npm baru, migrasi atau perubahan kode backend.

Alur akun yang diperbarui:

1. Buka `/login` untuk masuk, atau **Buat akun** untuk registrasi Reporter.
2. Isi nama, email, kata sandi baru dan pengulangannya. Setelah layanan merespons, halaman berubah menjadi **Periksa Email**. Respons tetap umum: tampilan tidak menjamin akun baru dibuat atau email berhasil terkirim.
3. Buka pesan SILAR terbaru untuk email yang didaftarkan. Buka tautan **Buka halaman aplikasi**, kemudian isi kode enam digit dari pesan yang sama. ID verifikasi diambil dari parameter `challenge_id` pada tautan; pengguna tidak perlu menyalin atau mengetik ID.
4. Tanpa tautan atau bila format ID tidak sesuai, input/tombol verifikasi dikunci. Keberadaan ID yang berformat benar belum membuktikan tautan sah; backend memeriksa kode, tujuan, masa berlaku dan pemakaian sebelumnya.
5. Jika memerlukan petunjuk baru, gunakan **Kirim ulang petunjuk verifikasi**. Pada halaman OTP, isi email dalam formulir kirim ulang yang terpisah. Gunakan pasangan tautan dan kode terbaru dari email. Masa berlaku dan pembatasan permintaan mengikuti konfigurasi/respons backend.
6. Sesudah verifikasi berhasil, klik **Lanjut ke Login** dan masuk dengan email serta kata sandi. Verifikasi tidak membuat sesi login secara otomatis. Jika halaman sesudah registrasi tertutup atau dimuat ulang, cukup buka tautan terbaru dari email untuk melanjutkan.

Bantuan email uji lokal:

- Pada `npm.cmd run dev` melalui `localhost`/`127.0.0.1`, bantuan berkas email tampil otomatis. Jika backend memakai `EMAIL_MODE=file`, buka berkas `.eml` terbaru untuk email Anda di `code/backend/private_outbox/`, lalu buka tautan di dalam pesan.
- Pada build produksi, bantuan folder lokal disembunyikan secara bawaan. Untuk preview lokal yang sengaja memakai email berkas, set `VITE_AUTH_LOCAL_HELP=true` pada `.env.local` frontend sebelum menjalankan atau membangun ulang. Set `VITE_AUTH_LOCAL_HELP=false` untuk menyembunyikannya juga di development. Flag ini hanya mengatur petunjuk; tidak mengubah pengiriman email backend atau membuka folder sebagai endpoint publik.
- Untuk backend SMTP, periksa kotak masuk email dan folder spam. Jangan gunakan kode dari pesan lain dengan tautan yang sedang dibuka.

Alur pelaporan dan notifikasi dari revisi sebelumnya:

- Halaman Notifikasi memakai baris sekitar 76 px untuk pesan satu baris di desktop. Pesan berada di atas tanggal dan status baca; **Buka laporan** serta **Tandai dibaca** berada di kanan. Pesan panjang menambah tinggi baris agar informasi tetap utuh.
- Notifikasi belum dibaca memiliki latar biru lembut, pesan lebih tegas dan teks **Belum dibaca**. Notifikasi yang sudah dibaca tampil lebih tenang. Pada HP, tindakan berpindah ke bawah pesan dengan tinggi target sentuh minimal 44 px.
- Filter **Hanya belum dibaca**, **Muat ulang**, pembacaan halaman berikutnya dan pembaruan status tetap melalui API. Membuka halaman atau **Buka laporan** tidak otomatis menandai pesan dibaca. Tombol **Tandai dibaca** adalah tindakan tersendiri.
- Draft baru mulai di tahap 1. Menyimpan bukti belum membuka tahap 2 atau 3; jalankan analisis terlebih dahulu.
- Tahap 2 terbuka setelah hasil yang sesuai dengan sumber aktif tersimpan. Periksa kartu/narasi/bukti dan lakukan koreksi bila diperlukan.
- Untuk masuk tahap 3, tekan **Lanjut ke konfirmasi** pada tahap 2. Setelah itu, konfirmasi versi aktif lalu kirim melalui tindakan terpisah.
- Versi yang sudah dikonfirmasi atau laporan resmi mengikuti keadaan tersimpan. Perubahan sumber, input yang belum disimpan dan versi kartu baru membatasi kembali kemajuan yang belum sah. Koreksi narasi tetap menyediakan analisis ulang di tahap 2, dengan tahap 3 terkunci sampai hasil baru tersedia.
- Setelah server mengonfirmasi penyimpanan teks/audio/gambar, halaman mengarah ke **Bukti aktif**. Konfirmasi penyimpanan muncul di panel tersebut dan item terbaru ditandai **Baru disimpan**. Gunakan **Tambah bukti lain** untuk kembali ke formulir, atau baca sumber dan tekan **Analisis laporan**.
- Pengunggahan yang gagal atau hanya berhasil sebagian dijelaskan sesuai hasilnya. Tindakan analisis/konfirmasi/pengiriman tidak dijalankan otomatis oleh perpindahan tahap, fokus atau pemuatan ulang.

Filter kategori termasuk Gempa Bumi, popup Detail melalui Fetch API, riwayat versi, notifikasi serta batas PWA tetap tersedia. Hasil verifikasi ada pada `docs/slr12/HASIL_VERIFIKASI_UI_v0.4.3.md`; daftar file/hash ada pada `docs/slr12/ui-v0.4.3/DAFTAR_PERUBAHAN.json`. Bagian 0.3.x berikut merupakan catatan asal perbaikan sebelumnya.

### Perbaikan build PWA 0.3.1

Jika UI 0.3.0 sudah diterapkan dan build berhenti dengan `ENOENT public/icons/icon-192.png`, ambil **`code/frontend/vite.config.js`** dari paket 0.3.1 dan timpa file dengan path yang sama pada clone. Dari terminal `code/frontend`, jalankan kembali `npm.cmd run build`. Perbaikan ini tidak memerlukan perubahan database, backend, model atau dependensi.

Konfigurasi sebelumnya masih memakai daftar nama ikon tetap. Konfigurasi baru membaca aset yang tersedia pada `public/brand/`, `public/icons/`, `public/fonts/` serta ikon lokal yang dirujuk manifest. Nama ikon lama yang sudah dihapus tidak dipaksakan masuk cache. Perubahan isi aset atau HTML tetap mengubah versi cache.

Apabila manifest masih menunjuk ikon yang telah dihapus, build menampilkan peringatan yang menyebut `src` tersebut. Cocokkan `icons[].src` dalam `public/manifest.webmanifest` dengan nama/path ikon PWA yang benar-benar digunakan pada clone; pertahankan ukuran/jenis/purpose sesuai asetnya. File yang tidak tersedia tidak dimasukkan ke precache. Perbaikan ini tidak membuat ikon pengganti atau mengganti manifest pengguna secara otomatis.

Hasil pemeriksaan khusus tersedia pada `docs/slr12/HASIL_VERIFIKASI_PWA_v0.3.1.md`. Pengujian backend/inferensi SLR11 tidak perlu diulang untuk perbaikan konfigurasi ini.

### Tambahan UI Laporan Saya 0.3.1, sesudah SLR12 0.2.0

Paket `SLR12_SILAR_UI_Laporan_Saya_v0.3.1.zip` adalah **tambahan** untuk clone yang sudah memakai SLR12 0.2.0. Paket ini memuat perubahan UI 0.3.0 beserta perbaikan PWA 0.3.1. Hentikan server backend/frontend, ekstrak ZIP ke folder sementara, lalu salin `code/`, `docs/` serta panduan ini mengikuti path yang sama pada clone. Aset build `dist`, database, model, konfigurasi lokal dan dependensi tidak disertakan. Daftar berkas/hash paket tersedia pada `docs/slr12/ui-v0.3.1/DAFTAR_PERUBAHAN.json`.

Pembaruan ini memakai logo final yang sudah diberikan: `code/frontend/public/brand/silar-logo.png`. Sidebar membaca PNG tersebut; penyesuaian bingkai gambar ada pada `code/frontend/src/reports-ui.css`. Tulisan SILAR memakai Manrope, sedangkan isi aplikasi memakai Poppins. Font dan lisensinya disertakan pada `public/fonts/`, sehingga tidak memerlukan pemuatan font eksternal.

**Berkas `public/icons/icon-192.png`, `icon-512.png` dan `public/manifest.webmanifest` tidak disertakan atau ditimpa oleh tambahan ini.** Tetap gunakan ikon PWA yang sudah Anda ganti pada clone. Favicon memakai PNG logo final `/brand/silar-logo.png`. Konfigurasi build membaca HTML, ikon/manifest lokal serta logo/font baru untuk membentuk versi cache aset yang baru. Paket ini tidak memerlukan pemasangan dependensi baru atau migration baru.

Di terminal `code/backend`:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Kemudian di terminal `code/frontend`:

```powershell
npm.cmd run build
```

Jalankan kedua server melalui bagian C. Buka **Laporan Saya** dan periksa:

1. Logo, tulisan SILAR dan warna teks tampil benar; judul serta kontrol daftar sejajar pada layar lebar.
2. Filter **Gempa Bumi**, kategori lain dan status menampilkan data yang sesuai. Filter berlaku di backend sebelum pagination.
3. **Muat ulang** mempertahankan filter, urutan dan halaman.
4. **Detail** membaca Incident Card tersimpan dalam dialog. **Edit** membuka halaman rincian SLR12 yang sudah digunakan; draft memakai **Lanjutkan laporan**, laporan terkirim memakai **Lihat rincian**.
5. Pergantian tema mempertahankan isian pada halaman rincian. Koreksi, konfirmasi dan pengiriman tetap menggunakan tindakan SLR12.
6. Periksa pembaruan aplikasi pada **Aplikasi & Koneksi**, aktifkan pembaruan yang tersedia dan muat ulang. Pastikan ikon PWA yang sudah Anda sesuaikan tetap digunakan.

Tes filter baru dapat dijalankan pada database uji PostgreSQL clone:

```powershell
.\.venv\Scripts\python.exe manage.py test reporting.tests.test_report_list_filters --settings=config.test_settings
```

Hasil pemeriksaan paket serta kontrak filter tambahan dicatat dalam `docs/slr12/UI_LAPORAN_SAYA_v0.3.0.md`. Bukti 0.2.0 tetap merupakan riwayat versinya sendiri.

### Paket dasar SLR12 0.2.0 — hanya bila belum dipasang

Jika SLR12 0.2.0 sudah berjalan pada clone Anda, gunakan bagian tambahan UI 0.3.1 di atas. Bagian ini menjelaskan pemasangan paket dasar 0.2.0.

Paket lengkap revisi SLR12 **0.2.0** ditujukan untuk source gabungan `4e0dccad76ccf2fe36e25e3b5fb329863b88cd3e`. Hentikan kedua server, ekstrak ZIP ke folder sementara, lalu gabungkan berkas dalam `code/`, `docs/` dan `PANDUAN_RUNNING.md` mengikuti path yang sama pada clone. Daftar serta hash berkas tersedia di `docs/slr12/DAFTAR_PERUBAHAN.json`. Salin juga stylesheet baru, `public/brand/` dan `public/icons/` dari paket yang sama.

Gunakan konfigurasi `.env`, database, venv dan model SLR11 yang sudah berhasil. Pembaruan ini memakai tabel/migration yang sudah ada dan tidak menambah dependensi. Pada terminal `code/backend`, jalankan `.\.venv\Scripts\python.exe manage.py check`. Perintah Python dan npm di panduan memakai executable langsung agar dapat dipakai pada PowerShell yang memblokir skrip aktivasi. Bangun frontend dari `code/frontend`:

```powershell
npm.cmd run build
```

Jika dependensi frontend belum tersedia pada clone, jalankan `npm.cmd ci --ignore-scripts --no-audit --no-fund` dahulu. Setelah itu jalankan aplikasi mengikuti bagian C dan gunakan alur baru pada bagian E. Aset build tidak disertakan dalam paket perubahan.

Pastikan source frontend disalin ke clone yang sama dengan terminal build/server. Dari root clone:

```powershell
Test-Path .\code\frontend\src\components\ReportReview.vue
Select-String -Path .\code\frontend\src\views\DraftView.vue -SimpleMatch "ReportReview"
```

Hasil pertama harus `True`; hasil kedua harus memuat import/pemakaian komponen pemeriksaan. Setelah build dan server dimulai, footer menampilkan **SLR12 · UI 0.2.0**. Detail laporan memiliki tab **Input & bukti**, **Periksa hasil** dan **Versi & riwayat**; sidebar memuat **Notifikasi**. Jika hanya kartu hasil lama yang terlihat, periksa source/build, bukan menjalankan analisis kembali.

Untuk cache PWA lama, buka **Aplikasi & Koneksi** lalu **Gunakan pembaruan aplikasi** bila tersedia. Tutup seluruh tab/jendela SILAR termasuk PWA yang terpasang, kemudian buka lagi `http://localhost:5173`. Jendela penyamaran dapat dipakai untuk memeriksa build terbaru dari server; login kembali sesuai kebutuhan. `Ctrl+F5` membantu memuat ulang aset ketika source/build/server sudah benar.


### Fondasi SLR10/SLR11 untuk instalasi yang belum terintegrasi

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
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver localhost:8001 --noreload
```

Biarkan terminal terbuka. Perintah tersebut memakai Python milik venv secara langsung sehingga aktivasi `Activate.ps1` tidak diperlukan.

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
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run dev
```

`npm.cmd ci` diperlukan saat menyiapkan dependensi atau lockfile berubah. Sesi berikutnya cukup `npm.cmd run dev`. Engine mengikuti `package.json`: Node 20 mulai 20.19.0, atau Node mulai 22.12.0. Setelah mengubah source frontend, bangun ulang dari `code/frontend`:

```powershell
npm.cmd run build
```

Untuk menghentikan aplikasi tekan `Ctrl+C` di kedua terminal.

## D. Akun dan email lokal

Daftar Reporter melalui frontend dan gunakan OTP email terbaru. Pada `EMAIL_MODE=file`, email disimpan lokal di `code/backend/private_outbox/`. Dari root repository:

```powershell
Invoke-Item code/backend/private_outbox
```

Urutkan berdasarkan waktu dan buka berkas terbaru dengan editor teks. Gunakan OTP/tautan yang sesuai tindakan: verifikasi email, aktivasi Operator, atau reset password. Jangan memasukkan email lokal dan kredensial ke commit.

## E. Alur laporan SLR10, SLR11 dan SLR12

### Membaca daftar laporan

**Laporan Saya** menyediakan filter status dan urutan terbaru/terlama. Filter serta pagination membaca ringkasan melalui API; jumlah mengikuti hasil filter yang sedang dimuat. Gunakan **Lanjutkan** pada laporan yang belum dikirim, atau **Lihat laporan** pada laporan resmi.

### Menyimpan sumber dan menjalankan analisis

1. Login sebagai Reporter, lalu buat atau lanjutkan draft.
2. Isi keterangan dan tekan **Simpan bukti teks**. Teks menjadi keterangan aktif yang dapat dibaca; form baru tidak ditampilkan lagi. Gunakan **Ubah keterangan** untuk mengisi ulang teks tersimpan dan **Simpan perubahan keterangan** untuk menggantinya. Teks sebelumnya tetap tersimpan privat dalam **Arsip bukti sebelumnya**.
3. Tambahkan audio/gambar sesuai kebutuhan. Satu audio aktif diperbolehkan; **Simpan pengganti audio** mengganti kanal aktif dan mempertahankan rekaman sebelumnya. Gambar yang disimpan otomatis ikut sebagai sumber; maksimal tiga gambar aktif. Kelompok unggahan yang melampaui batas jumlah/total ditolak sebelum upload. **Keluarkan gambar dari analisis** hanya mengeluarkannya dari sumber berikutnya; bukti asli tetap ada di arsip dan versi terdahulu.
4. Periksa panel **Bukti laporan**. Seluruh bukti aktif di panel ini dipakai bersama. Pada laporan lama tanpa bundle, keterangan/audio terbaru menjadi default aktif; versi sebelumnya dapat dipilih melalui arsip. Bundle yang sudah ada mempertahankan pilihannya; bukti yang diunggah setelah pembentukan bundle ikut sebagai perubahan sumber. Jika ada lebih dari tiga gambar pada data lama, aplikasi meminta pengurangan sumber aktif dan tidak memangkasnya diam-diam.
5. Jika daftar bukti lama memiliki halaman berikutnya, tekan **Baca semua bukti sebelum analisis**. Langkah ini hanya membaca halaman API dan memperbarui ringkasan sumber; belum membuat bundle atau menjalankan inferensi. Baca informasi pemrosesan Gemini dan centang pernyataannya bila rute memerlukannya.
6. Tekan **Analisis laporan**. Tindakan eksplisit ini menyiapkan bundle/snapshot baru bila sumber berubah, kemudian menjalankan satu request analisis sesuai kontrak SLR11. Bundle yang sumbernya sama dipakai kembali. Kegagalan atau respons persiapan yang belum pasti menghentikan alur; tidak ada POST ulang otomatis. Hasil analisis yang berhasil membuka tab **Periksa hasil**. Analisis belum merupakan pengiriman laporan resmi.

Bundle tetap menjadi snapshot sumber berversi di backend. Formulir utama tidak memerlukan centang bukti atau tombol pembentukan bundle tersendiri. Arsip dipakai bila ingin mengembalikan sumber lama; pilihan sumber baru disimpan ketika Analisis laporan ditekan. GET draft, bukti, versi dan hasil tidak membentuk bundle atau menjalankan inferensi.

### Memeriksa, mengonfirmasi dan mengirim

7. Pada **Periksa hasil**, bandingkan bukti, narasi dan draft Incident Card. Panel **Konfirmasi & kirim laporan** berada di samping kartu pada desktop dan tampil lebih awal pada layar kecil. **Perbaiki informasi kartu** tersedia pada header Incident Card. Status pemeriksaan/publikasi dapat dibuka melalui **Pemeriksaan & publikasi** pada metadata laporan. **Perbaiki informasi kartu** membuka tujuh field yang boleh dikoreksi. **Simpan versi kartu baru** mempertahankan sumber, hasil mentah AI dan versi lama; kategori tidak dapat diubah langsung. Penggantian tema selama pengisian mempertahankan isian.
8. Jika narasi perlu diperbaiki, gunakan **Perbaiki narasi**, **Simpan versi narasi baru**, lalu **Analisis ulang narasi ini**. Penyimpanan menonaktifkan kartu lama. Mode revisi narasi memanggil SENA/NARA/Fusion pada narasi revisi; Whisper/Gemini tidak diulang.
9. Centang **Saya telah membandingkan versi … dengan bukti dan narasi**, lalu **Konfirmasi versi ini**. Versi yang sudah dikonfirmasi menampilkan checkbox tercentang dan terkunci. Tombol **Kirim laporan** baru dapat digunakan setelah versi aktif yang sah dikonfirmasi. Pilih **Kirim laporan**, tinjau konfirmasi pengiriman, lalu **Kirim sekarang**. Versi resmi dan sumbernya terkunci setelah submit sah.
10. Buka **Versi & riwayat** untuk membaca versi lama, sumbernya dan perbandingan induk. Menu **Notifikasi** menampilkan pembaruan untuk penerima yang sedang masuk, termasuk pemberitahuan sesudah pengiriman.

NON_EVENT menahan konfirmasi/pengiriman; perbaiki sumber lalu analisis ulang. Penanda uncertain tetap tersedia sesudah koreksi/konfirmasi. Informasi yang belum tersedia tetap null atau daftar kosong, bukan pernyataan bahwa korban pasti nol. Konfirmasi Reporter, pemeriksaan Operator dan publikasi adalah tahap berbeda.

### Tema, batas input dan pemulihan

Pengalih **Mode terang/Mode gelap** tersedia pada header. Pilihan valid pada browser dipakai saat dibuka kembali; bila belum ada pilihan, mode mengikuti perangkat. Bila penyimpanan browser tidak tersedia, pengubah tetap bekerja selama sesi. Tema tidak menghapus isian atau mengirim mutasi laporan. Mark SVG dan ikon PWA yang disertakan merupakan usulan identitas berbasis huruf S; penetapan sebagai logo final mengikuti penerimaan pengguna. Rincian desain tersedia pada `docs/slr12/PENYEMPURNAAN_UI.md`.

Audio: WAV PCM, MP3, WebM/Opus, M4A/MP4-AAC tanpa video/cover; maksimal 10 MiB dan isi hasil decode sampai 120 detik. Bundle maksimal satu teks, satu audio, tiga gambar; total 25 MiB termasuk byte teks. Bukti asli dipertahankan.

`reporting` dan `ai_pipeline` harus sama-sama terdaftar pada konfigurasi gabungan. Lihat `docs/slr10/INTEGRASI_SLR11.md`. Pertahankan konfigurasi model/Whisper/Gemini yang sudah berhasil.

Jika respons persiapan sumber, analisis, koreksi, konfirmasi atau pengiriman terputus, pilih **Periksa permintaan dan hasil tersimpan**, lalu **Baca permintaan ini** pada tindakan yang relevan. **Baca draft tersimpan** pada peringatan membaca ulang sumber saat persiapan belum pasti. Pembacaan tersebut tidak mengirim analisis baru; setelah keadaan sah diketahui, percobaan berikutnya merupakan tindakan eksplisit pengguna. Pada form pemeriksaan, **Periksa request dan laporan tersimpan** membaca tindakan yang key-nya masih diketahui.

Riwayat dipaginasi; gunakan **Muat riwayat berikutnya** bila diperlukan. **Sertakan riwayat permintaan yang lebih lama** membuka metadata terminal yang masa replay-nya sudah habis. Pembacaan memakai GET request, run bila memiliki referensi hasil, dan detail Report terbaru. RUNNING/UNKNOWN menahan analisis baru. Hasil kartu mengikuti sumber/versi terbaru; status request lama ditampilkan terpisah. Konflik revision mempertahankan isian lokal untuk dibandingkan; form lama tidak dikirim ulang atau dipindahkan ke parent baru secara otomatis.

## F. Pengujian sesuai perubahan

Hasil perubahan SLR12 berada di `docs/slr12/HASIL_VERIFIKASI.md`. Riwayat integrasi SLR11 berada di `docs/ai/slr11/HASIL_INTEGRASI_v0.2.0.md`; hasil rilis SLR10 berada di `docs/slr10/HASIL_VERIFIKASI.md`. Menjalankan aplikasi sehari-hari cukup mengikuti bagian C.

Untuk memverifikasi tindakan baru SLR12 pada PostgreSQL 16 tim, gunakan terminal backend:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test reporting.tests.test_review reporting.tests.test_review_pipeline reporting.tests.test_review_postgresql --settings=config.test_settings --verbosity=2
```

Perintah tersebut berisi 27 tes API SLR12, dua tes sambungan revisi narasi-pipeline serta lima tes PostgreSQL untuk request bersamaan dan penguncian versi resmi. Gunakan role dengan izin membuat database pengujian. Model/provider diganti secara eksplisit; pengujian ini tidak mengukur mutu inferensi. Dua tes sambungan memastikan revisi narasi menggunakan SENA/NARA/Fusion tanpa Whisper/Gemini. Hasil komponen SQLite dalam paket tidak membuktikan lock/trigger PostgreSQL; lima tes PostgreSQL tersebut belum dijalankan pada lingkungan penyusunan paket.

Jika mengubah validator audio, jalankan dari terminal backend dengan venv aktif:

```powershell
.\.venv\Scripts\python.exe manage.py test reporting.tests.test_media reporting.tests.test_audio_api --settings=config.test_settings --verbosity=2
```

Perintah ini memakai PostgreSQL dari `.env` dan migration asli. Pastikan role database pengujian tim memiliki izin yang sesuai. SQLite terisolasi pada penyusunan paket hanya membuktikan komponen.

Jika mengubah installer/manifest, jalankan dari root:

```powershell
py -3.12 -m unittest discover -s tools/tests -v
```

Jika mengubah logika frontend/PWA, jalankan dari `code/frontend`:

```powershell
npm.cmd test
npm.cmd run build
```

Bukti penerimaan tujuh rute/model nyata SLR11 tetap menjadi acuan. Jika konfigurasi atau pipeline model diubah, lakukan pengujian ulang sesuai dampaknya. Untuk mencoba UI SLR12 pada mesin tim, gunakan laporan tersimpan atau laporan uji; periksa koreksi, konfirmasi, submit, versi/riwayat dan notifikasi. Catat lingkungan serta hasil aktual pada bukti card.

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
