# Rencana dan Panduan Pengujian SLR_07

Status: panduan pengujian yang digunakan dalam review bertahap. Hasil awal U07-01–U07-10 ada di review-results.md; U07-11–U07-16 belum dilaporkan. Jangan menganggap seluruh panduan sudah dijalankan. Pengujian ini memeriksa alur, tampilan, kejelasan pesan, serta kemudahan penggunaan prototype. Simulasi tidak membuktikan autentikasi, API, AI, keamanan server, pengiriman email, upload, atau instalasi PWA nyata telah berjalan. Penerimaan terintegrasi mengikuti SLR_15.

## Persiapan

1. Buka prototype daring atau paket melalui HTTP sebagaimana README.
2. Siapkan satu penguji dan satu pencatat; gunakan data fiktif.
3. Catat tanggal, nama penguji, perangkat, sistem operasi, browser, dan versinya.
4. Pilih peran dan keadaan melalui bar Ruang Review. Kontrol tersebut merupakan alat simulasi dan bukan menu produk produksi.
5. Gunakan Mulai ulang sebelum kasus terpisah. Jangan mereset di tengah kasus yang berlanjut.
6. Refresh mereset fixture. Gunakan keadaan Respons hilang untuk menguji pemulihan, bukan refresh browser. Dua browser tidak berbagi state prototype dan tidak membuktikan klaim atomik pada server.
7. Catat hasil aktual dan bukti pada review-results.md. Kegagalan yang sengaja ditahan dianggap sesuai jika pesan dan tindakan berikutnya benar; tombol nonaktif atau penolakan aman dapat menjadi bentuk perilakunya.

Data acuan: tombol Gunakan contoh mengisi cerita banjir di Jalan Melati sejak pagi. Informasi korban belum diketahui; waktu tersebut tidak menjadi tanggal pasti. Hasil analisis menggunakan fixture banjir, bukan pemahaman model atas teks bebas. Kode OTP fixture: 123456. Akun awal pelapor@contoh.test memakai password Silar123!. Untuk registrasi gunakan email fiktif lain, misalnya uji@contoh.test, dengan password minimal delapan karakter dan konfirmasi sama. Sesudah verifikasi gunakan password pendaftaran; sesudah reset gunakan password baru. Validator produksi mengikuti backend.

## U07-01 — Akun, OTP, profil, dan pemulihan

Acuan: AK01–AK07; FR01 dan kontribusi FR02; NFR05, NFR06.

1. Pilih Akun → pendaftaran. Kirim formulir kosong, lalu coba password dan konfirmasi yang berbeda.
2. Isi nama/email fiktif serta password yang sama; lanjutkan dan buka Email contoh → Verifikasi Email.
3. Masukkan 123456 pada Alur normal. Pada percobaan terpisah, pilih OTP salah dan OTP kedaluwarsa lewat menu Uji keadaan pada bar Ruang Review, lalu coba kode 123456. Tidak perlu menunggu masa berlaku nyata pada prototype.
4. Coba kirim ulang kode dan periksa petunjuk menggunakan email terbaru serta cooldown contoh.
5. Telusuri Lupa Password → Email contoh → Reset Password; coba kode salah dan password tidak cocok sebelum alur normal.
6. Masuk dengan isian contoh, ubah nama pada Profil Saya, periksa email/peran tidak dapat diubah, kemudian keluar.

Harapan: validasi jelas, pesan permintaan kode tidak mengungkap keberadaan akun, OTP salah/kedaluwarsa tidak berhasil, dan pengguna memahami langkah pemulihan. Verifikasi email/aktivasi bukan langkah verifikasi laporan dan bukan 2FA login. Pengiriman email dan enforcement sesi nyata belum diuji.

## U07-02 — Masukan multimodal

Acuan: RP02; FR03, FR04; NFR02, NFR03, NFR05, NFR06.

1. Reporter → Buat Laporan; coba Simpan Draft tanpa masukan.
2. Pada percobaan terpisah, uji tujuh kombinasi: teks; audio; gambar; teks+audio; teks+gambar; audio+gambar; teks+audio+gambar.
3. Gunakan teks fiktif, PNG/JPEG contoh, dan audio contoh. Coba unggah audio serta dialog Rekam suara → Gunakan Rekaman Contoh.
4. Periksa nama berkas, pratinjau, penanda belum tersimpan, pilihan sumber, dan petunjuk hak atas bukti.
5. Periksa penjelasan sebelum analisis: audio memakai Whisper lokal; Gemini relevan ketika ada gambar atau minimal dua kanal asli yang valid; audio asli tidak dikirim ke Gemini.

Harapan: minimal satu sumber dipersyaratkan; sumber dipilih jelas; informasi privasi/pemrosesan sesuai kanal. Rekaman adalah placeholder dan tidak mengakses mikrofon. Format decoder, batas media, dan pipeline sebenarnya diuji pada integrasi, bukan dinilai dari fixture ini.

## U07-03 — Draft, bukti tersimpan, dan bundle

Acuan: RP01–RP02; FR03, FR04; NFR04, NFR05.

1. Masukkan teks dan gambar → Simpan Draft; periksa daftar bukti dan pilihan aktif.
2. Lepaskan pilihan gambar lalu simpan; pastikan gambar tetap ada sebagai bukti tersimpan.
3. Pilih kembali bukti dan simpan untuk membentuk pilihan sumber baru.
4. Kembali ke Laporan Saya lalu buka draft dalam sesi yang sama.
5. Simpan lagi tanpa perubahan; kemudian ubah teks dan coba Analisis sebelum menyimpan perubahan.

Harapan: melepas pilihan tidak menghapus bukti; penyimpanan tanpa perubahan tidak menggandakan sumber; perubahan belum tersimpan menahan analisis. Pada implementasi, baca seluruh halaman bukti terunggah sebelum membentuk bundle saat recovery; fixture tidak membuktikan pagination/API upload tersebut.

## U07-04 — Analisis, pemeriksaan, konfirmasi, dan submit

Acuan: RP03–RP05; FR05–FR14; NFR05, NFR06.

1. Pilih Alur normal → Reporter → Buat Laporan → Gunakan contoh → Simpan Draft → Analisis.
2. Bandingkan sumber, narasi, kategori, lokasi, waktu, dampak, dan korban. Buka informasi analisis dan sumber turunan.
3. Coba Kirim Laporan sebelum konfirmasi.
4. Klik Konfirmasi Versi Ini; pastikan laporan belum masuk pengiriman resmi.
5. Klik Kirim Laporan, periksa detail/riwayat, kemudian ganti ke Operator dan periksa antrean.
6. Kembali ke Reporter dan coba menemukan tindakan penyuntingan versi resmi.

Harapan: analisis, konfirmasi, dan submit terpisah; submit memerlukan versi aktif yang dikonfirmasi; versi resmi terkunci. Informasi tidak diketahui tetap belum tersedia; korban kosong bukan nol; waktu relatif tidak ditebak sebagai tanggal. Tidak ada pertanyaan adaptif, completeness score, pengaitan laporan, atau auto dispatch.

## U07-05 — Koreksi dan versi

Acuan: RP02–RP04; FR11–FR13; NFR04, NFR05.

1. Siapkan draft yang sudah dianalisis dan dikonfirmasi tetapi belum dikirim.
2. Koreksi Informasi → ubah lokasi/dampak → simpan; periksa nomor versi dan coba Kirim Laporan tanpa konfirmasi baru.
3. Periksa kategori tidak dapat diubah melalui koreksi field.
4. Pada draft terpisah, pilih Ubah Narasi → revisi → simpan. Temukan dan jalankan Analisis Narasi Revisi.
5. Periksa hasil baru dan kebutuhan konfirmasi ulang. Ubah kembali sumber melalui Kembali ke Input → Simpan Draft.

Harapan: versi dan konfirmasi konsisten; hasil lama tidak dipakai untuk mengirim versi baru. Revisi narasi meminta analisis SENA/NARA/Fusion, bukan pengolahan ulang Whisper/Gemini. Jika aksi analisis ulang tidak tersedia atau tersangkut status lama, catat temuan. UI tidak membuktikan komponen AI sebenarnya dijalankan.

## U07-06 — NON_EVENT dan uncertain

Acuan: RP03–RP04; FR09–FR13; NFR05.

1. Pada draft tersimpan, pilih Hasil NON_EVENT sebelum Analisis.
2. Periksa penjelasan; coba konfirmasi/kirim, lalu telusuri koreksi narasi dan analisis ulang menggunakan Alur normal.
3. Pada percobaan terpisah, pilih Hasil uncertain sebelum Analisis.
4. Periksa penanda/penjelasan, konfirmasi versi, dan kirim.

Harapan: NON_EVENT menahan pengiriman dengan arah perbaikan tanpa menyebut pelapor berbohong; uncertain boleh dikirim jika guard lain terpenuhi dan penandanya tidak hilang. Kedua keadaan tidak dijadikan dimensi status laporan tambahan.

## U07-07 — RUNNING, UNKNOWN, respons hilang, dan retry

Acuan: RP03; FR05–FR10; NFR05, NFR10.

1. Untuk setiap keadaan, mulai dari draft tersimpan dan pilih keadaan sebelum Analisis.
2. Proses RUNNING → Periksa Status; coba memulai analisis baru. Harapannya tetap menunggu dan tidak membuat proses kedua.
3. Proses UNKNOWN → Periksa Status. Harapannya hasil belum pasti dan analisis baru ditahan, bukan otomatis dinyatakan gagal.
4. Gunakan Simulasi pemulihan teknis untuk keadaan aktif tersebut; pilih Alur normal lalu Coba Analisis Lagi secara eksplisit.
5. Respons hilang, hasil tersimpan → Analisis → Periksa Status. Harapannya hasil tersimpan ditemukan tanpa analisis kedua.
6. Ulangi pemulihan pada analisis narasi revisi bila relevan; retry harus tetap memakai narasi revisi.

Harapan: UI tidak menjanjikan proses bertahan setelah tab ditutup, pembacaan status tidak menjalankan AI, dan retry tidak dilakukan sebelum keadaan aman. Tombol pemulihan adalah kontrol lab; bukan fitur Admin produksi atau bukti proses server benar-benar dihentikan.

## U07-08 — Kesalahan dan keadaan khusus

Acuan: layar terkait; NFR05, NFR06, NFR10.

| Keadaan | Tindakan | Harapan |
| --- | --- | --- |
| Berkas tidak didukung | Pilih keadaan, lalu Simpan Draft | Berkas tidak dianggap tersimpan; tindakan perbaikan jelas. |
| Kapasitas penuh | Pilih keadaan, lalu Analisis | Tidak membuat run baru atau mengklaim sudah mengantre di worker. |
| AI belum siap | Pilih keadaan, lalu Analisis | Pesan aman menyebut layanan belum siap. |
| Konflik versi | Pilih keadaan sebelum simpan/konfirmasi/review | Periksa keadaan terbaru sebelum mengulang; tidak menganggap mutasi berhasil. |
| Daftar kosong | Buka daftar dengan keadaan tersebut | Pesan sesuai konteks dan aksi yang relevan. |
| Akses ditolak | Aktifkan keadaan dan buka layar | Tidak merender data yang tidak diizinkan. |

Periksa juga keadaan loading/berhasil dan letak pesan. Kapasitas, timeout, batas media, serta performa nyata bukan hasil pengujian ini.

## U07-09 — Antrean dan klaim

Acuan: OP01–OP03; FR16, FR17; NFR01, NFR02, NFR05.

1. Operator A → Antrean. Periksa ringkasan sebelum mengambil laporan.
2. Ambil Laporan → periksa detail dan daftar tugas sendiri.
3. Ganti Operator B → periksa antrean/tugas dan ketiadaan detail laporan yang sudah diambil A.
4. Pada percobaan terpisah, pilih Konflik klaim lalu coba mengambil laporan yang tersedia.

Harapan: antrean tidak membuka identitas/kontak, alamat privat, narasi, media, atau raw AI. Hanya satu penanggung jawab; Operator lain tidak dapat mengklaim atau membuka detail. Konflik disimulasikan dari kontrol, bukan dua browser. Penegakan izin dan klaim atomik server diuji pada integrasi.

## U07-10 — Review dan tindak lanjut

Acuan: OP03, RP05; FR17, FR18; NFR02, NFR05.

1. Operator penanggung jawab → Catat Pemeriksaan. Coba simpan tanpa alasan.
2. Uji Valid, Tidak valid, dan Belum dapat dipastikan pada percobaan terpisah.
3. Ganti Reporter → periksa ringkasan review dan ketiadaan alasan internal.
4. Kembali ke Operator → Catat tindak lanjut → simpan sebagai belum selesai.
5. Coba Selesai; pada item lain coba Batalkan tanpa alasan, kemudian dengan alasan.

Harapan: alasan review wajib; Reporter hanya melihat proyeksi yang diizinkan. INVALID/INCONCLUSIVE tetap internal; kandidat aktif perlu dibatalkan sebelum outcome tersebut. Tindak lanjut bukan chat/permintaan jawaban tambahan; pembatalan wajib beralasan. Operator tidak menyunting sumber/hasil mentah Reporter.

## U07-11 — Kandidat, sanitasi, approval, dan publikasi

Acuan: OP04–OP05, PB01–PB02; FR20–FR22; NFR02, NFR05.

1. Gunakan laporan terbuka dengan review Valid. Internal / Publikasi → Lanjutkan persiapan publikasi (PREPARE).
2. Pastikan kandidat belum otomatis dibuat dan belum muncul di portal.
3. Susun ringkasan, lokasi umum, waktu, dampak, dan pembaruan penanganan yang aman menggunakan data fiktif. Jangan memakai identitas asli.
4. Buat Kandidat; periksa versi dan ketidaktersediaan penyuntingan langsung isi tersimpan.
5. Coba Setujui sebelum pemeriksaan sanitasi dicentang. Periksa kemungkinan identifikasi dari kombinasi isi; sanitasi bukan pemeriksaan otomatis yang dijamin.
6. Centang pemeriksaan → Setujui Versi Ini; pastikan belum terbit. Klik Terbitkan → periksa portal.
7. Saat laporan masih terbuka, PREPARE kembali → buat kandidat pengganti dengan isi berbeda. Pastikan portal tetap membaca versi terbit sebelumnya.
8. Batalkan kandidat dengan alasan dan periksa versi lama tetap terbit. Ulangi untuk kandidat APPROVED yang belum PUBLISHED.
9. Jika perlu mengubah isi kandidat, batalkan lalu PREPARE/buat versi baru. Uji penolakan review ulang setelah publikasi pertama.

Harapan: arah, kandidat, approval, dan publish terpisah; approval berlaku pada versi tepat. Pembatalan tidak menarik versi terbit, dan publikasi tidak otomatis menutup laporan. Tidak ada withdraw pada MVP.

## U07-12 — Penutupan

Acuan: OP03, AD02; FR24; NFR05, NFR10.

1. Coba Tutup Laporan sebelum ada review.
2. Coba saat tindak lanjut PENDING, keputusan publikasi belum final, atau kandidat masih aktif.
3. Pada jalur internal dan jalur terbit yang terpisah, lengkapi syarat: review tersedia; tindak lanjut seluruhnya selesai/dibatalkan; INTERNAL/PUBLISHED; tanpa kandidat aktif.
4. Isi catatan penutupan dan tutup.
5. Coba review, tindak lanjut, publikasi, dan assignment Admin setelah CLOSED; buka kembali riwayat.

Harapan: syarat penutupan ditegakkan pada simulasi; CLOSED terminal bagi mutasi penanganan, publikasi, dan penugasan. Riwayat tetap dapat dibaca sesuai izin.

## U07-13 — Akun Operator, izin, assignment, dan monitoring Admin

Acuan: AD01–AD04, AK04; FR02, FR19, FR23, FR26; NFR01, NFR02, NFR05.

1. Admin → Pengelolaan Operator → buat akun fiktif; periksa status belum aktif dan ketiadaan password yang ditetapkan Admin.
2. Telusuri aktivasi melalui Akun → Email contoh → Aktivasi Operator. Resend aktivasi dilakukan dari Admin.
3. Kelola akun: cabut izin atau nonaktifkan Operator A; ganti peran ke Operator A dan periksa akses berikutnya. Pulihkan untuk percobaan selanjutnya.
4. Admin → monitoring → laporan resmi terbuka → Tugaskan / Alihkan ke B dengan alasan. Coba dahulu tanpa alasan.
5. Periksa akses A dicabut dan B mendapat tugas. Notifikasi lama tidak boleh mengembalikan akses A.
6. Bandingkan monitoring dengan Izin bukti privat tidak dicentang/dicentang; periksa draft Reporter tidak muncul.
7. Buka audit dan monitoring layanan; periksa tidak ada rahasia atau kendali menjalankan ulang model.

Harapan: akses mengikuti izin dan assignment saat ini; Admin tidak otomatis menjadi Operator penanganan. Aktivasi placeholder memperagakan akun contoh, bukan membuktikan konsumsi OTP/sesi nyata. Monitoring layanan hanya informasi status/metadata.

## U07-14 — Portal Publik

Acuan: PB01–PB02; FR22; NFR02, NFR05, NFR06.

1. Publik → daftar → detail laporan yang terbit.
2. Cari kata pada ringkasan/lokasi umum/dampak/pembaruan penanganan; uji variasi huruf besar/kecil dan kata tanpa hasil.
3. Coba filter kategori, lokasi umum, dan kombinasinya; periksa urutan publikasi terbaru.
4. Bedakan waktu kejadian dan waktu publikasi; periksa ketiadaan identitas, kontak, media asli, transkrip, hasil AI mentah, dan catatan internal.

Harapan: pencarian/filter sesuai field publik; tidak ada hasil diberikan dengan pesan jelas. Halaman hanya memuat allowlist publik, bukan seluruh data laporan.

## U07-15 — Notifikasi, offline, dan PWA

Acuan: UM01–UM02; FR15, FR25; NFR02, NFR05, NFR06.

1. Picu submit/review/assignment/publikasi/close yang sesuai; buka notifikasi peran penerima.
2. Tandai dibaca dan buka laporan dari notifikasi.
3. Setelah pengalihan tugas, coba notifikasi lama Operator sebelumnya; akses tidak boleh terbuka lagi.
4. Pilih Offline → periksa pesan dan penahanan operasi laporan. Kembalikan Alur normal untuk melanjutkan.
5. Buka panduan instalasi PWA dan periksa penjelasan batas offline.

Harapan: notifikasi di dalam aplikasi, tidak ada klaim push/SMS/email pembaruan laporan. Tidak ada penyimpanan/sinkronisasi draft offline; aset tampilan dasar dibedakan dari data laporan. Instalasi/cache, cookie, dan koneksi nyata memerlukan implementasi terkait.

## U07-16 — Responsivitas, usability, dan Digital Awareness

Acuan: seluruh layar; NFR05/NFR06 utama, NFR02/NFR03 pendukung.

1. Periksa Reporter/Publik pada ponsel serta Operator/Admin pada desktop. Acuan awal 390 × 844 dan 1366 × 768; coba layar lebih sempit.
2. Catat perangkat/browser/versi aktual. Sasaran yang ditetapkan adalah Chrome Android dan Chrome/Edge Windows, dengan ukuran tambahan 360 × 800 dan 768 × 1024. Penetapan sasaran belum membuktikan kompatibilitas lulus.
3. Buka menu, tabel, input file, pratinjau, dialog, dan formulir saat keyboard ponsel tampil.
4. Gunakan Tab/Enter; periksa fokus terlihat, label, urutan navigasi, pesan error, kontras, tombol tutup, dan status yang tidak hanya berupa warna.
5. Minta anggota mencoba membuat laporan tanpa arahan. Catat titik bingung, kesalahan, waktu yang diamati, dan komentar; tidak menambahkan target angka penerimaan baru.
6. Periksa penjelasan empat kategori; kepemilikan bukti; Gemini; keterbatasan AI; OTP; sanitasi publik; dan bantuan pemulihan pada tindakan yang relevan.

7. Regresi A07-01: pada 390 dan 360 px, buka menu → Buat Laporan; uji draft yang sudah ada dan draft baru setelah submit. Pastikan menu/overlay langsung tertutup; membuka ulang tidak menambah draft. Beralih ukuran desktop/ponsel dan periksa kembali.
8. Regresi A07-02: periksa avatar desktop sesudah warna diperbaiki; catat hasil kontras browser/alat yang digunakan. Perhitungan CSS terbaru 12,79:1 tidak menggantikan pemeriksaan browser.

Harapan: alur dapat diselesaikan, kontrol dapat dijangkau, informasi tidak terpotong, dan pengguna memahami langkah berikutnya serta batas sistem. Browser/visual QA tidak dapat digantikan pemeriksaan struktur JavaScript.

## Penilaian dan bukti

- Lulus: langkah benar-benar dicoba dan hasil aktual sesuai harapan pada lingkup prototype.
- Perlu perbaikan: ditemukan penyimpangan; catat layar, reproduksi, dampak, penanggung jawab, dan tindak lanjut.
- Belum diuji: belum dicoba atau alat/perangkat belum tersedia; jelaskan jika perlu.
- Belum dilaporkan: hasil aktual belum diterima; tidak otomatis berarti gagal atau belum pernah dicoba.
- Gunakan ID turunan U07-02a dan seterusnya untuk kombinasi/percobaan yang perlu hasil terpisah.
- Bukti dapat berupa screenshot atau rekaman singkat dengan nama file jelas, menggunakan data fiktif.
- Setelah perbaikan, uji ulang kasus terdampak dan catat bukti baru. Jangan mengganti hasil awal seolah-olah tidak pernah gagal.
- Card belum Done sebelum review kelompok, pemeriksaan perangkat sasaran, serta tindak lanjut selesai sesuai task.
