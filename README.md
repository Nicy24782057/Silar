# SILAR

Panduan terbaru SLR14: [alur dan antarmuka](docs/slr14/README.md),
[penuntasan verifikasi PostgreSQL dan integrasi API/pipeline](docs/slr14/PENUNTASAN_VERIFIKASI_20261030.md).
Implementasi SLR14 telah terintegrasi pada main e0dc889; hasil native dan
inferensi AI nyata mengikuti bukti pada panduan tersebut. Bagian versi lama di
bawah tetap menjadi catatan pemasangan/riwayatnya masing-masing.

**Platform Pelaporan Kejadian Multimodal Berbasis Kecerdasan Buatan**  
Sistem Inteligensi Laporan Adaptif dan Responsif.

SILAR menerima teks, audio, gambar, atau kombinasi kanal untuk membantu menyusun narasi dan draft Incident Card. Reporter memeriksa hasil sebelum pengiriman resmi; Operator meninjau laporan sesuai kewenangannya. Informasi yang tidak tersedia tetap tidak diisi dengan tebakan.

## Menjalankan aplikasi

Mulai dari **[PANDUAN_RUNNING.md](PANDUAN_RUNNING.md)**: perangkat lunak, setup lengkap, database, aset AI, email/Gmail, backend/frontend, pengujian dan pemecahan masalah.

Di Windows, jalankan **SETUP_SILAR.bat** dari folder utama, atau `py -3.12 tools/setup_silar.py`. Script memasang paket backend dan AI beserta frontend, lalu memeriksa hasilnya. Gunakan `--check` untuk pemeriksaan tanpa pemasangan/perubahan database. Aset model dan SMTP disiapkan mengikuti panduan.

Revisi implementasi **SLR14** dari temuan pengujian SLR15 mencakup satu halaman verifikasi email/kode, sandi minimal 15 karakter, serta tiga tahap pengelolaan laporan Operator. Penyesuaian kontrol sandi dan tombol landing page ada pada [revisi review SLR14](docs/slr14/revisi-review-20261113/README.md). Bukti pengujian paket akun sebelumnya tetap tersedia pada [catatan pengujian SLR15](docs/slr15/revisi-20261113/README.md).

## Acuan proyek

- [Acuan Teknis SILAR v0.3](docs/architecture/SILAR_Technical_Reference.docx), termasuk Lampiran A.
- [PRD SILAR v0.5](docs/product/SILAR_PRD.docx).
- [Pemetaan Fitur Final](docs/planning/SILAR_Pemetaan_Fitur_Final.md).
- [Dokumentasi SLR10](docs/slr10/README.md) dan [penghubung SLR11](docs/slr10/INTEGRASI_SLR11.md).
- [Perancangan UI/UX SLR07](docs/uiux/README.md) dan [fondasi backend SLR08](docs/backend/README.md).

## Anggota tim

| NIM | Nama |
| --- | --- |
| 24782050 | Maulana Rizki Ramadhani |
| 24782057 | Nicy Putra Pratama |
| 24782062 | Rizky Bintang Fadillah |
