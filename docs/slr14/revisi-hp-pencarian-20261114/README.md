# SLR14 — revisi HP yang disetujui dan pencarian Reporter

Paket ini menerapkan revisi SVG yang telah disetujui, melanjutkan `SILAR_SLR14_login_mobile_ACC_13Nov2026.zip` beserta paket terdahulunya. Implementasi tetap SLR14; SLR15 digunakan untuk pengujian dan pencatatan temuan.

## Perubahan

- Landing HP memakai susunan satu kolom dari SVG: navigasi ringkas, ilustrasi utuh, kategori dua kolom, ringkasan fitur vertikal, serta alur, SENA/NARA, tanggung jawab, portal, ajakan dan footer yang nyaman dibaca. Headline mempertahankan warna kata Situasi dan garis aksen desktop. Navigasi situs berfungsi pada landing dan Portal Publik, termasuk keyboard Escape, penutupan ketika fokus/klik berpindah, dan perubahan ukuran layar.
- Nama lengkap konsisten: SILAR — Sistem Inteligensi Laporan Adaptif dan Responsif. Header ruang akun HP hanya memakai ikon tiga garis, sedangkan logo/nama lengkap tetap di dalam panel navigasi. Menu, peran dan izin tetap mengikuti akun.
- Grafik status Reporter mengikuti lebar HP. Lima legenda, termasuk nilai nol, tetap tampil vertikal. Warna dan proporsi menggunakan jumlah yang sama dengan desktop, bukan memotong grafik lebar tetap. Status bernilai nol tidak diberi ruas batang palsu.
- Filter memiliki label terlihat dan kolom satu baris penuh di HP. Antrean tetap tanpa filter tahap. Reporter mempertahankan filter langsung saat pilihan berubah, serta Muat ulang. Pencarian teks memakai tombol Cari. Workspace mempertahankan pencarian ID dan filter yang sudah tersedia.
- Tabel laporan berubah menjadi kartu pada lebar hingga 760 piksel. ID, kategori, tanggal, status dan tindakan berada dalam satu kelompok; laporan resmi juga menampilkan versi dan penanggung jawab sesuai halaman/izin. Tabel tetap digunakan di layar lebih lebar. Tombol Detail, Hapus draft, klaim, ringkasan dan penugasan mempertahankan guard sebelumnya.
- Reporter dapat mencari kata kunci teks/narasi atau ID di seluruh laporan miliknya. Pencarian digabungkan dengan filter dan diterapkan sebelum pagination. Lihat [kontrak pencarian](KONTRAK_PENCARIAN.md).

Halaman login, registrasi, verifikasi, sandi, pembuka 1,2 detik dan pemulihan sesi dari paket sebelumnya tetap digunakan. Navigasi landing mengenali sesi aktif melalui Buka aplikasi. Revisi ini tidak mengubah alur review/publikasi, status backend, data publik yang diizinkan, model AI, dependency, migration atau masa berlaku sesi.

## Memasang

1. Hentikan backend dan frontend. Ekstrak paket ke folder sementara, lalu gabungkan berkas sesuai path ke clone yang sudah memakai paket terakhir. Jangan mengganti seluruh folder repository atau konfigurasi lokal.
2. Dari `code/backend`, jalankan kembali `.\.venv\Scripts\python.exe manage.py runserver localhost:8001`. Backend harus memuat revisi endpoint sebelum pencarian dipakai.
3. Dari `code/frontend`, jalankan `npm.cmd test`, `npm.cmd run build`, lalu `npm.cmd run dev`.
4. Buka ulang browser. Untuk PWA produksi, ambil pembaruan build melalui Aplikasi & Koneksi lalu buka kembali. Tidak diperlukan pemasangan dependency atau migration baru.

Alternatif penggabungan adalah `git apply --check PERUBAHAN_SLR14_HP_PENCARIAN.patch` lalu `git apply PERUBAHAN_SLR14_HP_PENCARIAN.patch` dari root clone. Pilih satu cara. Patch diuji terhadap hash berkas paket terakhir; perubahan lokal lain perlu digabungkan bila preimage tidak cocok.

## Mencoba

- Periksa landing di HP terang/gelap, buka menu, ikuti Alur pelaporan/Portal Publik, dan pastikan ilustrasi serta tombol tidak terpotong. Coba masuk kembali melalui Buka aplikasi dengan sesi valid.
- Reporter: bandingkan grafik desktop/HP pada akun yang sama; semua status dan proporsi harus sama. Filter dan kartu harus terbaca tanpa geser kanan.
- Cari kata yang memang ada pada teks/narasi, misalnya Jalan Melati. Coba huruf besar/kecil, ID pendek dan UUID lengkap. Hasil pada halaman berikutnya harus mempertahankan kata kunci/filter. Pencarian tidak menjangkau laporan akun lain atau draft yang telah dihapus.
- Draft foto/audio tanpa teks/narasi belum dapat dicari berdasarkan isi. Gunakan ID atau filter. Tidak ada analisis AI baru saat mencari.
- Buka Detail pada kartu, lalu pastikan ID laporan yang terbuka cocok. Coba penghapusan draft milik sendiri yang belum dikirim. Laporan resmi tidak menampilkan Hapus.
- Operator/Admin: periksa antrean, Penanganan Saya, serta Monitoring dan Penugasan sesuai izin. Label filter, metadata dan tindakan tetap terbaca pada HP. Periksa juga desktop/tablet serta halaman akun yang sebelumnya telah disetujui.

## Verifikasi

Frontend: 123 tes lulus dan build produksi berhasil. PostgreSQL: 17 tes pencarian/filter lulus. Browser build produksi: 98 pemeriksaan tata letak dan 13 alur lulus tanpa page error, pada tujuh lebar layar dalam tema terang/gelap, termasuk emulasi sentuhan HP. Pencarian lintas halaman, pembatasan pemilik, Detail yang sesuai, penghapusan draft sendiri, kombinasi filter, serta Buka aplikasi diuji melalui antarmuka. Hasil ada pada `bukti/browser-result.json`; log tes/build ada pada folder bukti. Ilustrasi landing juga diperiksa utuh dalam mode animasi biasa maupun kurangi animasi. Pengujian memakai database terpisah dan fixture model eksplisit. Ini tidak membuktikan inferensi AI nyata atau pengiriman SMTP eksternal. Kelompok lengkap 152 tes backend tidak dijalankan ulang untuk revisi ini.

Tidak ada commit, push, deployment atau perubahan board oleh penyusun. Usulan commit setelah review: `feat(slr14): terapkan revisi mobile dan pencarian laporan milik reporter`.
