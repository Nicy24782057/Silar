# Revisi alur, progres analisis, dan konfirmasi pengiriman

Permintaan lanjutan pengguna setelah audit menyeluruh: memperhalus perpindahan
dari login, memperlihatkan progres analisis, menegaskan urutan Lanjut/Kembali,
dan menyediakan halaman khusus setelah laporan terkirim. Palet dan identitas
mengikuti desain yang sudah disepakati.

Umpan balik lanjutan memperbarui penanda tahap dan membuka hasil secara otomatis.
Bukti terbaru ada pada [REVISI_NOTIFIKASI_DAN_HASIL_20261030.md](REVISI_NOTIFIKASI_DAN_HASIL_20261030.md).

## Perilaku yang berubah

1. **Login ke halaman berikutnya.** Transisi membungkus kerangka halaman akun,
   publik dan ruang aplikasi, sehingga sidebar serta isi masuk sebagai satu
   tampilan. Fade keluar 200 ms dan masuk 280 ms; halaman internal tetap memakai
   transisi sebelumnya. Elemen yang sedang keluar tidak menerima interaksi.
   Reduced motion menonaktifkan gerakan dan transisi.
2. **Analisis AI.** Panel animasi memuat persentase tahapan selesai, nama tahap,
   dan daftar pemeriksaan. GET memakai ledger key yang sama dengan POST analisis,
   kemudian mengikat run yang sesuai laporan, bundle, mode dan revisi input.
   Tidak ada POST analisis ulang otomatis. Poll berhenti saat terminal, gagal,
   konteks ditinggalkan, atau komponen dilepas. Respons pembacaan terlambat tidak
   mengganti progres analisis lain.
3. **Urutan laporan.** Penanda tiga tahap menjadi informasi posisi. Pengguna
   berpindah lewat Lanjut/Kembali. Setelah analisis selesai dan pembacaan hasil
   tersimpan berhasil, **Periksa hasil terbuka otomatis**. Koreksi yang belum
   disimpan menahan perpindahan. Tombol tidak aktif selama operasi berjalan.
   Versi & riwayat dibuka dalam dialog tanpa memindahkan tahap formulir.
4. **Setelah pengiriman.** Setelah server menyimpan dan pembacaan membuktikan
   `submitted_at` beserta versi resmi, pengguna masuk ke `/reports/{id}/sent`.
   Pesan utama: **Laporan Anda sudah terkirim**. Tersedia nomor/waktu kirim,
   **Ke Laporan Saya**, dan **Lihat rincian laporan**. Halaman bertahan sampai
   pengguna memilih tindakan; tidak ada pengalihan berdasarkan timer.

Draft yang dibuka kembali tetap meneruskan keadaan tersimpan yang sah: hasil
analisis dapat dilanjutkan dari Periksa hasil, dan versi yang telah dikonfirmasi
dapat dilanjutkan dari Konfirmasi & kirim. Hal ini mempertahankan pekerjaan
sebelumnya. Tidak ada penanda tahap yang dapat diklik untuk melompati urutan.
Laporan resmi yang dibuka sebagai rincian menggunakan navigasi hanya baca,
bukan langkah pembuatan yang dapat dikirim ulang.

## Arti persentase

Persentase menunjukkan **jumlah tahapan yang telah selesai**, bukan perkiraan
waktu atau persentase token/model yang diproses. Waktu setiap tahap dapat berbeda.
Angka tidak bertambah berdasarkan timer.

- Rute teks/foto: pemeriksaan sumber → narasi → SENA → NARA → Fusion →
  penyimpanan → pembacaan hasil (7 tahap).
- Rute dengan audio menambah Whisper (8 tahap).
- Analisis narasi revisi tidak mengulangi Whisper/Gemini; daftar mengikuti mode
  yang benar-benar dijalankan.
- Data `stage`, `status` dan `timings_ms` pada API yang sudah ada menjadi bukti
  kemajuan. 100% memerlukan run SUCCEEDED dan pembacaan hasil yang sesuai sumber
  aktif; keberhasilan komputasi tidak otomatis mengonfirmasi/mengirim laporan.
- Bila pembacaan progres gagal, angka terakhir dipertahankan dengan pesan status.
  Hasil belum pasti tidak ditampilkan sebagai sukses, dan tidak memicu retry POST.

Halaman terkirim juga memverifikasi API pada kunjungan langsung dan refresh.
URL milik draft yang belum dikirim kembali ke formulir; URL saja tidak cukup
untuk memperlihatkan keberhasilan. Konfirmasi versi dan submit tetap dua tindakan
terpisah, dengan pemeriksaan revisi/izin backend yang sudah ada.

## Verifikasi

- **103 tes frontend lulus**, termasuk delapan kasus progres/rute, referensi
  request, run lama, persaingan run, sumber tidak sesuai, dan penahanan 100%.
- Browser mengamati transisi kerangka login untuk Reporter, Operator dan Admin.
- Respons API bertahap yang dikendalikan QA membuktikan 0/42/71/100, angka tetap
  saat tahap tetap, satu POST, dan pembukaan hasil otomatis setelah dibaca. Ini pengujian UI
  terhadap data API uji, bukan inferensi model nyata.
- Konfirmasi/submit menggunakan API lokal; halaman berhasil, refresh, kunjungan
  URL draft belum terkirim dan rincian resmi diuji. Enam kombinasi tema/lebar
  halaman berhasil dan progres sampai 320 px diperiksa.
- Regresi 174 kombinasi aplikasi serta 60 kombinasi portal/tahap pelaporan lulus,
  termasuk input teks/WAV/PNG, koreksi v2, permintaan gagal/kosong/lambat dan
  respons antar-ID. Tidak ada error runtime atau luapan halaman pada pemeriksaan.
- Build produksi dan PWA lulus: 60 aset UI di cache; tidak ada data API, media,
  laporan, akun atau kredensial di cache.

Bukti revisi alur awal: `bukti/alur-progres-pengiriman.txt`,
`browser-matriks-alur.txt`, `browser-reporter-alur.txt`, `pwa-alur.txt`.
Bukti terkini yang menggantikan kewajiban Lanjut setelah analisis:
`bukti/notifikasi-dan-hasil.txt`, `browser-reporter-notifikasi.txt`, dan
`pwa-notifikasi.txt`.
Batas penerimaan PostgreSQL 16 dan inferensi AI asli tetap dijelaskan pada
[HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md). Revisi ini tidak mengubah backend,
kontrak API atau dependensi.

## Memasang

Paket kumulatif mencakup seluruh revisi sebelumnya. Jika paket audit sebelumnya
sudah terpasang dan migration 0005 telah berjalan, revisi alur ini tidak menambah
migration baru. Gabungkan berkas menurut path, mulai ulang frontend/backend,
lalu gunakan build/PWA terbaru sesuai [README.md](README.md).
