# Implementasi SLR_10 SILAR

Versi paket 1.1.0 (revisi audit), 22 Oktober 2026. Paket menyediakan frontend Vue dan layanan input multimodal di atas fondasi SLR_08. Hasilnya dipakai oleh SLR_11 untuk analisis, kemudian SLR_12 untuk pemeriksaan, koreksi, konfirmasi, dan pengiriman resmi.

## Acuan dan posisi sumber

- PRD 0.5: `docs/product/SILAR_PRD.docx`.
- Acuan Teknis 0.3, terutama A4.4–A4.7, A6.2/A6.5/A6.6, A7.2–A7.6: `docs/architecture/SILAR_Technical_Reference.docx`.
- Pemetaan 1.0: `docs/planning/SILAR_Pemetaan_Fitur_Final.md`.
- Desain aktif: `docs/uiux/`, termasuk perbaikan menu dan avatar pada sumber repository.
- Baseline sumber ZIP: `8f805afcfe32b6f46b94043a55e196e23b824f7f`. SHA ini adalah acuan sebelum penambahan SLR_10, bukan bukti commit hasil baru.

Dokumen dan bukti historis SLR_07/SLR_08 dipertahankan. Manifest/hasil tes lama pada `docs/backend/` berlaku untuk paket fondasi ketika diuji; rilis SLR_10 mengikuti manifest serta hasil pemeriksaan dalam folder ini.

## Isi implementasi

| Bagian | Lokasi | Perilaku |
| --- | --- | --- |
| Frontend | `code/frontend/src/` | Composition API, Router, layout, akun, profil, draft, teks/audio/gambar, evidence, bundle, analisis dan pembacaan hasil. |
| API input | `code/backend/reporting/` | Daftar/detail/pembuatan draft, upload/list evidence, akses media privat dan pembuatan bundle. |
| Fondasi | `code/backend/accounts/`, `core/`, `common/` | Model dan layanan SLR_08 digunakan kembali. Tidak ada model laporan kedua atau migration pengganti. |
| PWA | `code/frontend/public/`, `tools/service-worker.js` | Manifest, ikon, precache aset UI, cache versi dan pemberitahuan offline. |
| Pengujian | `code/backend/reporting/tests/`, `code/frontend/tests/` | Akses, validasi decoder, pemulihan sumber, revision, idempotency dan batas cache. |
| Pemasangan | `tools/` dan BAT akar | Pemasang perubahan, konfigurasi origin lokal serta server build Vue bawaan. |

## Menjalankan di Windows

Ikuti `MULAI_DI_SINI.txt`. Gunakan Python 3.13 yang sudah terpasang dan PostgreSQL 16 dengan konfigurasi `.env` yang sudah berhasil. Jangan mengulang inisialisasi database atau menghapus migration. Tidak ada password akun bawaan dalam paket.

Pemasangan ke repository lama dilakukan dari folder ekstraksi melalui `PASANG_KE_REPO.bat`. Pemasang memeriksa hash sumber dan konflik sebelum menyalin, menggabungkan penambahan URL/app dengan konfigurasi yang sudah ada, serta mencadangkan berkas yang berubah dalam `.slr10-backups/`. Folder itu diabaikan Git. Berkas `ai_pipeline/` dan route analisis milik rekan tidak diganti.

Dari repository tujuan jalankan `SIAPKAN_SLR10.bat`. Skrip memasang `requirements-slr10.txt` bersama `requirements-ai.txt` apabila tersedia dalam satu resolver, menjalankan `check`, `migrate` dan `bootstrap_silar`, lalu menggunakan build bawaan atau membangun ulang jika npm tersedia. Konfigurasi lokal hanya menyelaraskan origin serta path akun dan lokasi decoder; kredensial database/JWT/OTP dipertahankan.

Jalankan backend dan frontend pada terminal terpisah:

```bat
JALANKAN_BACKEND.bat
JALANKAN_FRONTEND_BAWAAN.bat
```

Buka `http://localhost:5173`. Server frontend bawaan memproksi `/api/` ke Django `localhost:8001`; cookie dan CSRF memakai hostname localhost yang sama. Server bawaan hanya mengikat loopback dan ditujukan untuk pengembangan/demo lokal. Deployment menggunakan web server/HTTPS yang disiapkan pada SLR_16.

Untuk pengembangan frontend menggunakan Node.js LTS:

```bat
cd code\frontend
npm ci
npm run dev
```

Frontend produksi dibangun melalui `npm run build`. `npm run preview` dan server Python bawaan menyajikan build yang sama. Node 20.19+ atau 22.12+ sesuai engine Vite; Node.js LTS digunakan untuk penyiapan baru. Versi paket dikunci dalam package-lock.json.

## Alur yang sudah disediakan

1. Daftar Reporter, ambil email terbaru, verifikasi OTP, kemudian masuk. Registrasi/request OTP memberi pesan generik tanpa kode atau challenge pada respons publik.
2. Masuk menggunakan backend nyata; access berada dalam memori, refresh pada cookie HttpOnly. Reload memulihkan sesi melalui refresh yang diputar.
3. Buat draft kosong, lalu simpan satu bukti per request. Teks asli dan byte media tetap dipertahankan.
4. Baca metadata evidence, termasuk item yang belum masuk bundle. Media diambil setelah tindakan pengguna dan disajikan melalui blob URL sementara; URL dicabut saat halaman ditinggalkan.
5. Pilih bukti, lalu simpan menjadi bundle melalui POST eksplisit. Bundle baru mengganti sumber aktif tanpa menimpa bukti dan snapshot sebelumnya.
6. Permintaan analisis memakai kontrak SLR_11. Informasi Gemini ditampilkan untuk rute yang relevan sebelum analisis. Hasil dibaca kembali melalui ReportDetail.
7. Bila respons mutasi hilang, jangan mengirim ulang otomatis. Antarmuka meminta pembacaan keadaan/bukti tersimpan sebelum tindakan berikutnya. RUNNING/UNKNOWN tetap menahan analisis baru.

Daftar memakai pagination. Metadata evidence lebih lanjut diambil melalui tombol Muat bukti berikutnya; pastikan seluruh halaman yang diperlukan diperiksa saat memulihkan draft. Membaca daftar tidak membuat bundle atau mengubah revision/input_revision.

## Profil media yang diterapkan

Angka A7.3 diterapkan sebagai batas awal: teks 5.000 karakter Unicode, satu teks dan satu audio serta tiga gambar per bundle, 5 MiB/12 MP per gambar, 10 MiB/120 detik per audio, total 25 MiB termasuk byte UTF-8 teks.

PNG/JPEG statis diperiksa dengan Pillow melalui verify dan load; ekstensi dan MIME dicocokkan dengan isi. Animasi PNG tidak diterima pada profil ini. File asli tidak ditulis ulang.

| Audio | Container/codec yang diterima |
| --- | --- |
| WAV | PCM yang didukung decoder; fallback tanpa FFmpeg hanya WAV PCM yang dapat dibaca modul wave Python. |
| MP3 | MP3. |
| M4A dan MP4 | AAC saja, tanpa video atau cover gambar. |
| WebM | Opus saja, tanpa video atau cover gambar. |
| OGG, ALAC, Vorbis | Ditolak sebelum disimpan sebagai bukti audio valid. |

FFprobe memeriksa container/stream dan FFmpeg benar-benar mendekode audio. Rekaman WebM yang tidak memiliki durasi pada header dinilai dari waktu hasil decode. Semua stream video ditolak, termasuk attached picture/cover art. MIME container `video/mp4` dari pemilih berkas browser hanya diterima bila isinya benar-benar AAC tanpa stream video; metadata disimpan sebagai `audio/mp4`. Batas ukuran, durasi dan timeout decoder tetap memerlukan pengukuran pada perangkat tujuan. Setup mencoba memasang `Gyan.FFmpeg` melalui WinGet bila decoder Windows belum tersedia. Apabila pemasangan gagal, jalankan kembali setelah FFmpeg tersedia; aplikasi menolak format yang belum bisa didekode dengan pesan aman.

## Keamanan dan PWA

Role dan kepemilikan diperiksa backend pada setiap pembacaan/mutasi, termasuk replay. Admin tidak diberi akses draft Reporter. Detail sesudah submit memakai proyeksi sesuai izin. API dan media memiliki Cache-Control no-store. Nama asli tidak menjadi path media dan file_key tidak dikirim kepada frontend.

PWA hanya memuat daftar aset UI yang dibangun. API, media, token, draft dan hasil AI tidak disimpan ke Cache Storage, localStorage, sessionStorage atau IndexedDB. Tidak ada offline draft atau sinkronisasi latar belakang. Service worker memakai versi cache dan hanya membersihkan cache berawalan `silar-ui-` milik aplikasi.

## Keterlacakan dan penerimaan

| Kebutuhan | Kontribusi SLR_10 | Pemeriksaan |
| --- | --- | --- |
| FR03 / AC-F03 | Draft online, formulir dan API teks/audio/gambar. | Membuat draft, kanal valid, validasi, simpan dan buka kembali. |
| FR04 / AC-F04 | Evidence asli, metadata, media privat, pilihan dan bundle immutable. | Pemulihan sebelum bundle, akses silang ditolak, snapshot sumber dipertahankan. |
| FR25 / AC-F25 | Manifest, service worker dan offline UI. | Tidak ada data privat di cache; operasi laporan tetap online. |
| NFR07 / AC-N07 | Ringkasan, pagination, detail/media on demand. | Respons daftar tidak mengekspansi narasi/media/PII. |
| FR01, NFR01/02 | Antarmuka akun serta pemeriksaan akses input. | Akun/OTP/JWT/CSRF menggunakan fondasi nyata. |
| FR05/06/10, NFR03/05/10 | Pemberitahuan Gemini, permintaan/status/hasil serta bantuan pemulihan. | Integrasi penuh memakai kode dan aset SLR_11. |
| FR23, NFR04 | Event audit dalam transaksi dan sumber versi tetap. | Report create, upload dan bundle tercatat tanpa isi bukti/rahasia pada audit. |
| NFR06 | Layout responsif dan menu ponsel. | Simulasi viewport dicatat pada hasil browser; perangkat fisik diverifikasi kelompok. |

Rincian status pemeriksaan ada di `HASIL_VERIFIKASI.md`. Review kelompok, Windows/PostgreSQL, perangkat sasaran dan bukti commit/push dicatat setelah pelaksanaan sebenarnya. Tidak ada commit atau push otomatis ke repository kelompok dari penyusunan paket ini.

## Revisi audit 1.1.0

Rincian perubahan dan status penutupannya ada pada `REVISI_AUDIT_1.1.0.md`; audit masukan disimpan pada `ACUAN_AUDIT_20261022.md`. Pillow diselaraskan ke 13.0.0 dan diuji pada decoder PNG/JPEG. Pemasang mengenali hash v1.0.0 yang diketahui dan menaikkan pin lama tanpa menimpa perubahan lokal yang tidak dikenal. Baseline SLR_11 di `requirements-ai.txt` tetap dipertahankan dan diperiksa saat tersedia.

Recorder hanya memilih WebM/Opus atau MP4/AAC yang didukung browser; bila tidak tersedia atau izin gagal, tersedia pesan perbaikan dan kanal unggah/teks/gambar. Backend tetap memeriksa isi sebenarnya. Peringatan normalisasi NARA ditampilkan terpisah dari uncertain, hanya ketika identitas run/hasil/sumber cocok dengan kartu yang ditampilkan.

Rujukan API browser: [MediaRecorder.isTypeSupported](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static), [MediaRecorder.mimeType](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/mimeType), dan [error event](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/error_event).
