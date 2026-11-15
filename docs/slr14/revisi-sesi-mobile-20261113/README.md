# SLR14 — sesi, navigasi dan tampilan HP, 13 November 2026

Kembali ke landing page kini mempertahankan akses akun selama sesi backend masih valid. Navigasi menampilkan **Buka aplikasi**, sehingga pengguna tidak perlu memasukkan sandi lagi untuk kembali ke ruangnya. Tampilan tahap dan tab aktif juga diseragamkan mengikuti Buat Laporan. Pembukaan dokumen aplikasi di HP menampilkan logo/loading, dan formulir akun HP memiliki logo SILAR di tengah.

Revisi ini melanjutkan paket akun/setup, revisi UI, dan `SILAR_SLR14_alur_operator_13Nov2026.zip`. Implementasi tetap termasuk SLR14. SLR15 menjadi kegiatan pengujian dan pencatatan temuan.

## Navigasi akun

| Keadaan | Perilaku |
| --- | --- |
| Sesi masih diperiksa | Navigasi menampilkan Memeriksa sesi, tanpa meminta pengguna langsung login kembali. |
| Reporter sudah masuk | Buka aplikasi menuju Laporan Saya. |
| Operator/Admin sudah masuk | Buka aplikasi menuju dashboard sesuai hak aksesnya. |
| Landing atau Portal Publik dimuat ulang | Cookie sesi yang masih valid dipulihkan melalui mekanisme refresh dan pembacaan akun yang sudah ada. |
| Login dibuka dengan sesi aktif | Langsung menuju aplikasi atau tujuan lokal yang sebelumnya diminta. Guard peran/izin tetap diperiksa. |
| Sesi tidak berlaku atau pengguna sudah Keluar | Formulir login kembali diperlukan. |
| Pemeriksaan sesi terganggu jaringan | Halaman publik dapat dibaca. Periksa sesi lagi mencoba memulihkan cookie yang masih valid. |

Navigasi, hero, ajakan di bagian bawah dan footer landing mengikuti keadaan akun. Login tidak diulang hanya karena berpindah ke landing atau membuka kembali dokumen pada browser yang masih menyimpan cookie valid. Sandi dan access token tidak dipindahkan ke localStorage/sessionStorage. Masa berlaku, rotasi, validasi cookie dan logout backend tetap mengikuti konfigurasi sebelumnya.

Tujuan setelah login mempertahankan path, query dan hash lokal. Origin lain, alamat yang tidak aman, serta tujuan halaman autentikasi yang berpotensi berulang ditolak. Pemeriksaan awal memiliki batas 15 detik dan meneruskan pembatalan ke permintaan CSRF, refresh dan pembacaan akun. Kegagalan koneksi tidak memicu pengiriman ulang POST otomatis.

Permintaan data laporan publik tetap menggunakan `publicRead`, tanpa Bearer/cookie dan tanpa refresh terselubung pada fungsi tersebut. Pemeriksaan sesi untuk tombol akun merupakan proses tersendiri. Membaca publikasi tetap dapat dilakukan tanpa akun.

## Tampilan tahap dan tab

- Tahap aktif Reporter dan Operator memakai panel biru penuh dengan tulisan putih. Nomor tahap, sudut, padding dan tinggi minimum memakai aturan bersama di `navigation-ui.css`. Label panjang dapat menambah tinggi sesuai ruang yang tersedia.
- Tahap yang belum terbuka tetap mengikuti guard dan ikon kunci yang sudah ada. Penanda selesai Reporter tetap mengikuti progres sebenarnya.
- Pilihan kanal Teks/Audio/Foto, sumber pembanding, tab laporan resmi, dan filter notifikasi Reporter/Operator/Admin memakai warna biru yang sama saat aktif.
- Warna validasi, publikasi dan status penanganan tetap memiliki makna masing-masing. Revisi ini tidak mengubah isi atau proses laporan yang sebelumnya telah disetujui.
- Pada layar kecil, penanda tahap menempatkan nomor di atas label dan menyembunyikan keterangan tambahan agar tetap terbaca. Mode terang dan gelap diperiksa.

## Pembukaan dan formulir akun HP

Pada lebar hingga 640 piksel, HTML awal menampilkan logo SILAR dan animasi loading selama dokumen, rute dan sesi disiapkan. Tampilan itu dihapus sesudah aplikasi siap dirender. Tidak ada penundaan minimum buatan atau persentase rekaan, serta tidak ditampilkan ulang pada perpindahan halaman di dalam aplikasi.

Pada URL ruang privat, pengguna tanpa sesi valid menuju login dan pengguna dengan sesi valid langsung menuju ruang yang diizinkan. Shortcut PWA tetap menggunakan alamat awal yang sudah ada. URL landing/Portal Publik tetap membuka halaman publik, dengan tombol akun mengikuti hasil pemeriksaan sesi.

Logo berada di tengah di atas formulir login, registrasi dan verifikasi pada HP. Kontrol sandi, kolom dan tombol tetap memakai komponen sebelumnya. Tampilan dua panel desktop/tablet tetap digunakan. Loading dan halaman akun mengikuti tema, serta animasi menghormati preferensi reduced motion.

Jika sesi tidak mendapat jawaban dalam 15 detik, loading berakhir dengan petunjuk pemeriksaan koneksi. Ini batas permintaan awal, bukan perubahan masa berlaku sesi. Jika inisialisasi rute gagal, layar pembuka menyediakan tombol Muat ulang.

## Verifikasi

Tes frontend: **122 lulus, 0 gagal/skip**. Build produksi berhasil. Log tersedia di [bukti/frontend-tests.txt](bukti/frontend-tests.txt) dan [bukti/frontend-build.txt](bukti/frontend-build.txt).

Pemeriksaan browser produksi mencakup 150 keadaan tampilan dan 16 alur utama. Matriks sesi/tampilan (144 keadaan dan 10 alur) serta pemeriksaan notifikasi/batas sesi (6 keadaan dan 6 alur) dijalankan dalam bagian terpisah. Pemulihan awal juga diperiksa ulang pada build akhir, termasuk penolakan akun setelah refresh berhasil yang harus kembali ke login tanpa refresh kedua. Hasil gabungan tersedia pada [bukti/browser-result.json](bukti/browser-result.json). Pengujian menggunakan backend PostgreSQL uji terpisah dan build produksi melalui Vite preview. Pemulihan sesi, logout dan publikasi memakai endpoint nyata. Model hanya diganti test double untuk menyiapkan laporan uji, tanpa inferensi AI asli atau pengiriman SMTP eksternal.

Matriks tampilan menggunakan navigasi aplikasi normal agar tidak membuat ratusan refresh dokumen buatan. Pembatasan backend tetap aktif. Kasus muat ulang, pembukaan konteks browser baru dengan cookie, gangguan jaringan, sesi tidak berlaku dan tenggat permintaan diuji secara terpisah. Pemeriksaan PWA mencakup service worker dan cache UI produksi, bukan pemasangan pada perangkat fisik atau splash bawaan sistem operasi.

Tidak ada perubahan source backend, dependency, migration, endpoint, status laporan atau masa berlaku sesi. Kelompok lengkap 152 tes backend SLR14 tidak dijalankan ulang untuk perubahan frontend ini.

## Memasang dan mencoba

1. Hentikan frontend, ekstrak ZIP ke folder sementara, lalu gabungkan berkas sesuai path pada clone yang sudah berisi paket sebelumnya. Jangan mengganti seluruh folder repository.
2. Dari `code/frontend`, jalankan `npm.cmd test`, `npm.cmd run build`, lalu `npm.cmd run dev`. Backend tetap berjalan seperti biasa.
3. Buka ulang halaman. PWA yang terpasang perlu menerima pembaruan build melalui Aplikasi & Koneksi lalu dibuka kembali.
4. Login sebagai Reporter, buka landing dan pilih Buka aplikasi. Ulangi untuk Operator/Admin. Coba muat ulang landing dan buka login saat sesi aktif.
5. Pada HP, buka URL aplikasi melalui browser atau PWA. Periksa loading dan logo di atas formulir ketika belum login. Setelah login, buka kembali tanpa memasukkan sandi lagi selama cookie/sesi masih valid.
6. Tekan Keluar, kemudian buka ruang privat. Formulir login harus muncul kembali. Coba panel tahap dan pilihan tab pada mode terang/gelap.

Alternatif penyalinan adalah `git apply --check PERUBAHAN_SLR14_SESI_HP.patch`, lalu `git apply PERUBAHAN_SLR14_SESI_HP.patch` dari root clone. Pilih satu cara. Patch menggunakan preimage berkas paket terdahulu, dengan hash sebelumnya dan hash baru di `DAFTAR_PERUBAHAN.json`. Perubahan lokal lain perlu digabungkan terlebih dahulu.

Tidak ada commit, push, deployment atau perubahan board oleh penyusun. Nama commit yang sesuai setelah review: `fix(slr14): seragamkan navigasi dan pulihkan sesi dengan tampilan pembuka mobile`.
