# SLR14 — desain login HP yang telah disetujui

Revisi ini menerapkan pratinjau SVG SILAR yang telah disetujui: header biru dengan logo, pattern dan ilustrasi login desktop yang sama, serta panel formulir melengkung. Registrasi dan OTP mengikuti tambahan arahan untuk menempatkan formulir lebih tinggi. Paket melanjutkan `SILAR_SLR14_sesi_dan_tampilan_HP_13Nov2026.zip` beserta pendahulunya; implementasi tetap SLR14 dan pengujian menjadi temuan SLR15.

## Tampilan

| Layar | Susunan HP |
| --- | --- |
| Login | Header ilustrasi 327 piksel; panel melengkung mulai sekitar y=295. |
| Registrasi, kode/OTP, aktivasi Operator, lupa/atur ulang sandi | Header ringkas 220 piksel; panel mulai sekitar y=188, agar formulir lebih tinggi. |
| Lebar mulai 641 piksel | Dua panel desktop/tablet yang sudah ada. |

Kolom tetap setinggi 50 piksel pada HP, dengan ukuran teks 16 piksel agar tidak memicu pembesaran kolom otomatis di browser iOS. Ikon mata berada di dalam kolom dan mempunyai area tekan 44 piksel. Formulir panjang bergulir secara alami; tidak dipotong atau dipaksa muat dengan mengecilkan kolom. Kontrol kembali ke beranda dan tema berada di header. Ilustrasi diturunkan dari SVG desktop asli dengan batas gambar utuh, bukan gambar generatif baru. Pattern memakai elemen kontur dan aksen asli. Tema terang/gelap memakai pasangan ilustrasi yang sesuai.

## Layar pembuka

Pada pembukaan dokumen browser HP maupun PWA, logo dan pattern berada pada latar gradasi SILAR dengan pesan Menyiapkan aplikasi. Sesuai persetujuan terbaru, tampilan bertahan minimum sekitar **1,2 detik**, dilanjutkan pemudaran **0,2 detik** bila animasi diizinkan. Ini menggantikan perilaku paket sebelumnya yang tidak memiliki minimum.

Waktu penyiapan rute/sesi dihitung dalam minimum yang sama. Jika penyiapan sudah lebih lama, aplikasi tidak menunggu minimum kedua. Antarmuka di balik layar pembuka belum dapat menerima input sampai pembukaan selesai. Preferensi reduced motion menonaktifkan putaran dan pemudaran. Perpindahan rute di dalam aplikasi tidak mengulang pembuka. URL awal PWA, halaman publik, batas pemeriksaan sesi dan tombol Muat ulang ketika inisialisasi gagal mengikuti mekanisme sebelumnya.

Kembali ke landing tetap mempertahankan akses akun selama cookie/sesi backend masih valid. Tombol Buka aplikasi kembali ke ruang sesuai peran. Logout dan masa berlaku sesi tetap berlaku.

## Verifikasi

Tes frontend: **122 lulus**; build produksi berhasil. Log berada di folder [bukti](bukti/). Pemeriksaan browser produksi **75 keadaan tampilan dan 9 alur berhasil**, tanpa error JavaScript halaman. Hasil dicatat pada [browser-result.json](bukti/browser-result.json). Pengujian memakai Chromium dan backend PostgreSQL uji terpisah. Alur akun memakai endpoint sebenarnya dan pesan email lokal, tanpa pengiriman email eksternal. Fixture laporan memakai test double model; tidak ada klaim inferensi AI nyata dari revisi frontend ini.

Pemeriksaan meliputi tampilan akun 320–1440 piksel pada mode terang/gelap, layar pendek, gulir ke tombol, ikon mata, registrasi/kode, aktivasi Operator, pemulihan sandi, pemulihan sesi landing, minimum pembuka, reduced motion dan cache UI service worker produksi. Ini pemeriksaan browser, bukan pengujian pemasangan PWA pada perangkat fisik atau splash bawaan sistem operasi.

Tidak ada perubahan source backend, migration, dependency, endpoint, izin, status laporan atau masa berlaku sesi. Kelompok 152 tes backend tidak dijalankan ulang karena perubahan ini hanya frontend/dokumentasi.

## Memasang dan mencoba

1. Hentikan frontend, ekstrak ZIP ke folder sementara, lalu gabungkan berkas sesuai path ke clone yang sudah memakai paket sesi/HP terakhir. Jangan mengganti seluruh repository.
2. Dari `code/frontend`, jalankan `npm.cmd test`, `npm.cmd run build`, lalu `npm.cmd run dev`. Jalankan backend seperti biasa.
3. Buka ulang browser HP. Untuk PWA produksi, terima pembaruan melalui Aplikasi & Koneksi lalu buka kembali. Service worker tidak aktif pada server dev.
4. Periksa login, Buat akun, Verifikasi akun dan Lupa sandi pada terang/gelap. Registrasi/kode dimulai lebih tinggi. Gulir sampai tombol/tautan terakhir dan coba keyboard perangkat.
5. Coba alur kode Reporter dan Operator, konfirmasi sandi serta ikon mata. Pada tablet/desktop, pastikan dua panel tetap utuh.
6. Setelah login, buka landing dan Buka aplikasi, lalu muat ulang. Sesi yang masih valid tidak meminta sandi lagi. Sesudah Keluar, akses privat kembali memerlukan login.

Alternatif penyalinan adalah `git apply --check PERUBAHAN_SLR14_LOGIN_HP.patch`, lalu `git apply PERUBAHAN_SLR14_LOGIN_HP.patch` dari root clone. Pilih satu cara. Manifest mencatat hash sebelumnya/baru; perubahan lokal lain perlu digabungkan bila tidak cocok.

Tidak ada commit, push, deployment atau perubahan board oleh penyusun. Usulan commit setelah review: `fix(slr14): terapkan desain akun mobile dan ringkas header registrasi OTP`.
