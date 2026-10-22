# Implementasi SLR_10 SILAR

Pembaruan dokumentasi **23 Oktober 2026**: integrasi SLR10–SLR11 0.2.0 memiliki bukti tujuh rute, 10 run dengan relasi `OK` dan 24 tes transaksi/integrasi Windows/PostgreSQL lulus. Pelaksana juga mengonfirmasi frontend sampai hasil tersimpan, instalasi PWA, muat ulang dan notifikasi offline; tampilan yang digunakan dinilai tidak bermasalah.

Status terbaru: [HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md), [CHECKLIST_PENERIMAAN.md](CHECKLIST_PENERIMAAN.md), [INTEGRASI_SLR11.md](INTEGRASI_SLR11.md), dan [catatan penerimaan manual](bukti-uji/penerimaan-manual-20261023.md). Bukti rinci pipeline/hasil: [dokumen SLR11](../ai/slr11/BUKTI_PEKERJAAN_DAN_WAKTU_PROSES_SLR11.md). Panduan operasional tetap [PANDUAN_RUNNING.md](../../PANDUAN_RUNNING.md). Uraian versi 1.1.1 di bawah merupakan riwayat penyerahan SLR10.

Versi paket 1.1.1 (revisi penutup implementasi), 22 Oktober 2026. Paket menyediakan frontend Vue dan layanan input multimodal di atas fondasi SLR_08. Hasilnya dipakai oleh SLR_11 untuk analisis, kemudian SLR_12 untuk pemeriksaan, koreksi, konfirmasi, dan pengiriman resmi.

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
| Pemasangan | `tools/` dan `PANDUAN_RUNNING.md` | Pemasang perubahan, konfigurasi origin lokal serta server build Vue bawaan. |

## Menjalankan di Windows

Ikuti satu panduan operasional di [PANDUAN_RUNNING.md](../../PANDUAN_RUNNING.md). Gunakan Python 3.12 dan PostgreSQL 16 dengan konfigurasi lokal yang sudah berhasil; instalasi tim memakai port 5433. Panduan menjelaskan pembaruan repository, menjalankan dua server, email lokal, dan pengujian sesuai perubahan.

Installer Python tetap tersedia dan melindungi pekerjaan SLR11. Launcher root lama diganti panduan; berkas distribusi yang dihapus dicadangkan hanya jika hash-nya dikenal. Petunjuk menjalankan aplikasi tidak lagi bergantung pada launcher root.

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

FFprobe memeriksa container/stream dan FFmpeg benar-benar mendekode audio. Durasi ditentukan dari jumlah sampel PCM mono 16 kHz hasil decode, sehingga padding metadata MP3/WebM tidak menolak isi audio yang tepat 120 detik. Output decoder dibatasi ukurannya dan byte asli tetap dipertahankan. Semua stream video ditolak, termasuk attached picture/cover art. MIME container `video/mp4` dari pemilih berkas browser hanya diterima bila isinya benar-benar AAC tanpa stream video; metadata disimpan sebagai `audio/mp4`. Batas ukuran, durasi dan timeout decoder tetap memerlukan pengukuran pada perangkat tujuan. Setup mencoba memasang `Gyan.FFmpeg` melalui WinGet bila decoder Windows belum tersedia. Apabila pemasangan gagal, jalankan kembali setelah FFmpeg tersedia; aplikasi menolak format yang belum bisa didekode dengan pesan aman.

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

Rincian status pemeriksaan ada di `HASIL_VERIFIKASI.md`. Hasil Windows/PostgreSQL dan laporan manual PWA/tampilan sudah dicatat sesuai sumbernya. Model/provider pengganti pada 24 tes backend, runtime asli pada run aplikasi, serta arsip UI/PWA historis dibedakan. Review/keputusan kelompok dan pencocokan bukti commit dilakukan oleh pelaksana.

## Revisi audit 1.1.0

Rincian perubahan dan status penutupannya ada pada `REVISI_AUDIT_1.1.0.md`; audit masukan disimpan pada `ACUAN_AUDIT_20261022.md`. Pillow diselaraskan ke 13.0.0 dan diuji pada decoder PNG/JPEG. Pemasang mengenali hash v1.0.0 yang diketahui dan menaikkan pin lama tanpa menimpa perubahan lokal yang tidak dikenal. Baseline SLR_11 di `requirements-ai.txt` tetap dipertahankan dan diperiksa saat tersedia.

Recorder hanya memilih WebM/Opus atau MP4/AAC yang didukung browser; bila tidak tersedia atau izin gagal, tersedia pesan perbaikan dan kanal unggah/teks/gambar. Backend tetap memeriksa isi sebenarnya. Peringatan normalisasi NARA ditampilkan terpisah dari uncertain, hanya ketika identitas run/hasil/sumber cocok dengan kartu yang ditampilkan.

Rujukan API browser: [MediaRecorder.isTypeSupported](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static), [MediaRecorder.mimeType](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/mimeType), dan [error event](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/error_event).

## Revisi 1.1.1

Lihat [REVISI_1.1.1.md](REVISI_1.1.1.md) dan [HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md). Pengujian diulang pada validator/API audio, installer/paket, dan build yang terdampak. Pada revisi audio/kemasan 1.1.1 saat itu, source logika frontend/PWA, fondasi SLR08 dan kontrak API dipertahankan. Paket integrasi 0.2.0 kemudian melengkapi sambungan analisis/pemulihan frontend. Bukti rilis 1.1.0 berada di `bukti-uji/historis-v1.1.0/`; hasil integrasi dan laporan manual terbaru tercantum pada HASIL_VERIFIKASI.md.
