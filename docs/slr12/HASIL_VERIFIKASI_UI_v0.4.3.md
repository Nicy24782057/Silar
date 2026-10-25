# Hasil verifikasi UI SILAR 0.4.3

Tanggal: 24 Oktober 2026. Dasar implementasi: UI 0.4.2. Acuan visual: empat SVG lampiran pengguna mengenai Login, Registrasi, Setelah Registrasi dan Verifikasi OTP.

## Perubahan

| Bagian | Hasil |
| --- | --- |
| Layout akun | Desktop dua panel: identitas SILAR di kiri, formulir proporsional di kanan, tanpa sidebar pelapor. Di HP/tablet sempit, formulir satu kolom dan logo ringkas di header. Tema terang/gelap tersedia. |
| Identitas | Ilustrasi, logo dan wordmark berasal dari SVG pengguna. Tekstur bitmap besar diganti gradien SVG; ikon/ilustrasi vector dan logo dipertahankan. Aset hasil sekitar 823 kB (gzip build sekitar 288 kB), dari referensi sekitar 9 MB. Gambar memakai contain agar logo/teks tidak terpotong. |
| Login | Email/kata sandi, lupa sandi, registrasi dan verifikasi email tersedia. Login tetap memanggil layanan akun dan membuka halaman sesuai peran/tujuan yang diizinkan. |
| Registrasi | Empat field, validasi pengulangan kata sandi dan petunjuk berikutnya. Sesudah respons 202, tampil Periksa Email dan tiga langkah. Respons umum backend dipertahankan; tidak mengklaim akun pasti dibuat atau email pasti terkirim. |
| Sesudah registrasi | Petunjuk membuka pesan terbaru, tautan, lalu kode dari pesan yang sama; resend eksplisit memakai email yang diisi saat registrasi. Keadaan tampilan berada di memori dan tidak menyimpan isian privat secara offline. |
| OTP | Satu input enam digit dengan numeric inputmode dan one-time-code autocomplete. ID berasal dari tautan dan tidak menjadi isian manual. Tanpa ID, format salah atau query ganda, verifikasi dikunci. Keabsahan tetap diputuskan backend. |
| Resend | Formulir email terpisah dari formulir kode. Email yang belum lengkap pada resend tidak menghalangi verifikasi kode. Keadaan memproses, pesan umum, kesalahan dan Retry-After mengikuti layanan; tidak ada hitungan masa berlaku yang dibuat sendiri. |
| Berhasil | Setelah verifikasi, tersedia Lanjut ke Login. Verifikasi dan pembuatan sesi login tetap tindakan terpisah. Kode dan kata sandi dibersihkan setelah percobaan/perubahan konteks tautan. |
| Bantuan lokal | Petunjuk private_outbox tampil otomatis hanya pada development di loopback, atau flag opt-in. Produksi menyembunyikannya secara bawaan. Folder tidak dijadikan tautan/endpoint publik. |
| Halaman terkait | Lupa/reset kata sandi dan formulir aktivasi Operator memakai tampilan akun yang sama. Tautan pemulihan/aktivasi yang hilang diberi petunjuk sesuai tujuannya. |

Paket mempertahankan sidebar kiri, notifikasi ringkas, filter termasuk Gempa Bumi, popup detail melalui Fetch, riwayat versi, penguncian tahap, pemulihan draft dan penunjuk Bukti aktif dari UI 0.4.2. Backend, endpoint, migrasi dan dependensi aplikasi tidak diubah.

## Hasil aktual

| Pemeriksaan | Hasil | Bukti pada `bukti-uji/ui-v0.4.3/` |
| --- | --- | --- |
| Unit frontend/PWA | 73 lulus, 0 gagal; termasuk 4 tes baru untuk tautan dan batas bantuan lokal | `frontend-tests.txt` |
| Build produksi Vite 7.3.7 | Berhasil, 68 modul | `frontend-build.txt` |
| Browser pada server development | 54 skenario lulus, 0 runtime error: 15 akun dan 39 regresi UI sebelumnya | `browser-checks.txt`, `browser-results.json` |
| Browser pada build produksi | 3 pemeriksaan lulus, 0 runtime error | `production-checks.txt`, `production-results.json` |
| Tampilan akun | 1366×768 dan lebar 736/390/320 px; dua tema dan peralihan tema saat isian terisi | Rekap browser yang sama |

Pengujian memakai Vue, API Django 5.2.18, SQLite terisolasi dan akun/laporan/hasil analisis sintetis. Registrasi, resend, penolakan tautan lama/ID asing/OTP salah, konsumsi OTP yang benar, penolakan pemakaian ulang kode, login/logout, lupa sandi dan reset sandi dijalankan melalui layanan backend lokal sebenarnya. Email ditulis melalui backend berkas privat .eml dan dibaca hanya oleh skrip QA; tidak ada pengiriman ke penerima eksternal.

Untuk memeriksa pembatalan kode lama setelah resend tanpa menunggu waktu, konfigurasi QA terisolasi memakai OTP_RESEND_SECONDS=0. Konfigurasi aplikasi pengguna tidak diubah. Status 429/Retry-After diperiksa dengan respons terkontrol. Beberapa tampilan HP Periksa Email memakai respons registrasi umum yang diintersepsi; pengujian registrasi nyata tercatat pada skenario terpisah.

Build produksi diperiksa melalui vite preview yang terhubung ke backend lokal: Login dan aset fingerprint termuat, bantuan direktori lokal tidak muncul secara bawaan, OTP tanpa tautan dikunci, dan login membuka halaman/ sidebar pelapor. Inferensi AI tidak dipanggil ulang pada pengujian akun.

Rekap request hanya memuat metode/path atau metadata aman; tidak memuat kata sandi, kode OTP, token, cookie maupun isi email. Screenshot dipakai untuk pemeriksaan internal dan tidak dimasukkan dalam paket.

## Skenario browser

1. Login dua panel mengikuti referensi tanpa sidebar pelapor atau pemotongan logo.
2. Isian registrasi bertahan saat tema berganti; konfirmasi sandi berbeda ditolak sebelum POST.
3. Registrasi melalui backend menampilkan Periksa Email dan tiga langkah tanpa mengklaim email pasti terkirim.
4. Kirim ulang dari Periksa Email memakai alamat pendaftaran dan respons umum layanan.
5. Verifikasi tanpa tautan, format salah atau query ganda dikunci dan tidak mengirim OTP.
6. UUID pada tautan belum membuktikan keabsahan backend; tautan lama dan ID asing ditolak.
7. Permintaan ulang di halaman OTP adalah formulir terpisah dan menghasilkan tautan terbaru.
8. OTP salah tidak menyelesaikan verifikasi; input kirim ulang yang belum sah tidak menghalangi formulir kode.
9. OTP benar menyelesaikan verifikasi melalui backend; masuk tetap tindakan terpisah.
10. Kode yang sudah dikonsumsi tidak bisa dipakai ulang; akun terverifikasi dapat Login dan Keluar.
11. Lupa sandi dan reset sandi tetap memakai alur akun serta tautan kode yang berlaku.
12. Aktivasi Operator mempertahankan isian sandi dan kunci tautan; tautan pemulihan tidak mengarah ke resend yang salah.
13. Resend mengikuti kesalahan serta Retry-After layanan tanpa hitungan waktu yang dibuat sendiri.
14. Keempat tampilan akun dapat dipakai pada 736, 390 dan 320 px tanpa luapan.
15. Offline menahan formulir akun dan mempertahankan isian; data rahasia tidak disimpan di storage.
16. Login dan daftar nyata melalui API; detail tidak dibaca sebelum dipilih.
17. Sidebar kiri dan logo utuh pada aset PNG asli serta aset persegi.
18. Kontrol lengkap satu baris pada desktop 1024 px; judul tetap 18 px.
19. Warna teks dan status pada dua tema; pergantian tema bertahan.
20. Kategori Gempa Bumi dan status digabungkan pada query API.
21. Pagination dan muat ulang mempertahankan halaman yang sedang dibaca.
22. Detail hanya GET, no-store, menampilkan Incident Card dan mengembalikan fokus.
23. Respons detail terlambat tidak menimpa laporan yang dipilih berikutnya.
24. Detail dengan ID tidak cocok ditolak dan dapat dibaca ulang.
25. Popup laporan terkirim memakai kartu resmi dan tindakan hanya baca.
26. Edit popup membuka rincian nyata pada tahap Periksa hasil.
27. Isian koreksi bertahan saat tema dan tahap berubah; simpan membentuk versi baru.
28. Riwayat versi dan perbandingan induk tetap membaca API.
29. Konfirmasi dan kirim terpisah; tombol kirim terlihat sebelum konfirmasi.
30. Pengiriman nyata mengunci versi resmi dan menyimpan notifikasi.
31. Notifikasi ringkas: empat baris 76 px, pesan dan metadata di kiri, tindakan di kanan.
32. Baca dan belum dibaca berbeda tanpa mengandalkan warna; kontras kedua tema memadai.
33. Tandai dibaca, filter dan muat ulang tetap menggunakan API notifikasi sebenarnya.
34. Buka laporan menuju rincian yang benar dan tidak menandai pesan secara otomatis.
35. Notifikasi pada 736, 390 dan 320 px tidak meluap; tindakan turun dan memiliki target sentuh 44 px.
36. Pesan panjang, tanpa laporan terkait dan muat halaman berikutnya tetap terbaca utuh.
37. Kegagalan menandai pesan tidak mengubah status baca dan menampilkan kesalahan.
38. Keadaan kosong dan gagal memuat tetap menyediakan filter atau muat ulang.
39. Saat offline status tersimpan tetap dibaca dan tindakan perubahan ditahan.
40. Profil menyimpan nama dan memperbarui identitas akun.
41. Buat laporan tidak membuat draft sampai tombol eksplisit ditekan.
42. Tahap aktif berwarna biru dengan teks putih pada kedua tema.
43. Satu teks aktif, penggantian masuk arsip, draft pulih tanpa unggah ulang.
44. Audio WAV tersimpan melalui API dan mendapat receipt serta sorotan sumber aktif.
45. Unggah dua gambar menandai keduanya; analisis tetap eksplisit.
46. RUNNING dan UNKNOWN tetap di tahap 1; pemulihan membaca keadaan tanpa analisis baru.
47. NON_EVENT dapat diperiksa tetapi tahap 3 dan tindakan lanjut tetap terkunci.
48. Versi kartu baru mengunci kemajuan; revisi narasi tetap dapat dianalisis ulang di tahap 2.
49. Unggahan parsial dan gagal tidak dianggap semua berhasil atau membuka tahap berikutnya.
50. Daftar dan dialog tetap terjangkau pada 736, 390 dan 320 px.
51. Menu HP mengelola fokus, Escape dan tema; rincian tanpa luapan.
52. Pada HP penyimpanan langsung memperlihatkan Bukti aktif dan tombol kembali ke formulir.
53. Offline menahan tindakan dan tetap mempertahankan isian.
54. Aplikasi dan Koneksi mempertahankan informasi instalasi dan batas offline.

### Build produksi

1. Build produksi memuat Login dan aset identitas dari bundle tanpa sidebar pelapor.
2. Bantuan folder lokal tidak muncul secara bawaan pada build produksi; OTP tanpa tautan terkunci.
3. Login pada build produksi terhubung ke backend dan membuka sidebar kiri pelapor.

## Batas pemeriksaan

SMTP nyata, aplikasi email/perangkat fisik, pengiriman ulang berbasis waktu pada produksi serta penerimaan PostgreSQL 16 tidak diulang pada revisi UI ini. Aktivasi Operator diperiksa pada tampilan/kunci tautan; konsumsi kode aktivasi Operator nyata tidak diulang. Verifikasi akun pada browser memakai backend yang sama dengan aplikasi melalui SQLite QA, bukan database pengguna.

Hasil analisis awal untuk regresi pelaporan berasal dari fixture. Tujuh rute produksi serta inferensi Whisper/Gemini/SENA/NARA tidak diuji ulang. Pemasangan PWA fisik juga tidak diulang. Perbaikan PWA tetap memakai aset UI dan melewati API/data privat.

Paket tidak menimpa `public/brand/`, `public/icons/` atau manifest PWA pengguna. Satu panduan operasional tetap berada di root: `PANDUAN_RUNNING.md`. Tidak ada commit atau push yang dilakukan pada repository pengguna.
