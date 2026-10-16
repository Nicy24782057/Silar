# Langkah Review Lanjutan SLR_07

Dokumen ini menjelaskan tindak lanjut catatan Nicy Putra Pratama tanggal 16 Oktober 2026. Pemeriksaan teknis tambahan U07-11–U07-15 sudah selesai dan dicatat pada review-results.md. Dokumen ini adalah panduan finalisasi manual; langkah berikut belum dianggap sudah dilakukan oleh penguji.

## Menggunakan paket baru

1. Ekstrak ZIP ke folder sementara, lalu salin folder docs di dalamnya ke akar proyek Silar. Dokumentasi berada di docs/uiux/ dan sumber prototype di docs/uiux/prototype/.
2. Dari akar proyek jalankan `py -m http.server 8000 --directory docs/uiux/prototype` atau `python -m http.server 8000 --directory docs/uiux/prototype`.
3. Buka http://localhost:8000. Setelah mengganti sumber, muat ulang penuh sekali sebelum putaran baru. Ini mereset data contoh; jangan dilakukan di tengah alur yang ingin dipertahankan.
4. Akun awal Reporter: email `pelapor@contoh.test`, password `Silar123!`. Ini contoh publik untuk simulasi dalam memori, bukan akun server. Gunakan data fiktif dan jangan memakai password asli.
5. Untuk pendaftaran, gunakan email fiktif lain seperti `uji@contoh.test`. Sesudah verifikasi, masuk dengan password pendaftaran. Sesudah reset, gunakan password baru. Refresh/Mulai ulang mengembalikan akun contoh ke awal.

## Uji ulang password salah

1. Mulai ulang → Alur normal → Akun → Masuk.
2. Isi pelapor@contoh.test dengan password Salah123! → Masuk.
3. Harapan: email/password ditolak; tetap di halaman Masuk dan tidak masuk ke Reporter.
4. Coba email yang sama dengan password Silar123!.
5. Harapan: masuk ke Laporan Saya sebagai Reporter.
6. Catat hasil dan screenshot sebagai uji ulang R07-01; pertahankan catatan awal password salah diterima.

Password salah pada login berbeda dari password baru pada Reset Password. Password baru yang memenuhi syarat dan cocok dengan konfirmasinya memang boleh diterima bersama OTP valid. Uji negatif reset adalah kode salah/kedaluwarsa, password terlalu pendek, atau konfirmasi berbeda. Setelah reset berhasil, password lama ditolak dan password baru digunakan.

## Cara mencoba OTP kedaluwarsa

1. Pilih Akun → Verifikasi Email.
2. Pada bar Ruang Review, pilih Uji keadaan → OTP kedaluwarsa.
3. Masukkan 123456 lalu klik Verifikasi Email.
4. Harapan: pesan kode kedaluwarsa/tidak dapat digunakan; tidak beralih sebagai verifikasi berhasil.
5. Catat pesan, halaman dan screenshot untuk U07-01 langkah 7b.
6. Kembalikan Uji keadaan ke Alur normal sebelum menguji keberhasilan berikutnya; ikuti alur kirim ulang yang tersedia.

Pada prototype tidak perlu menunggu masa berlaku kode nyata; kontrol review menyimulasikan kedaluwarsa. Pengiriman dan masa berlaku OTP sebenarnya diperiksa saat implementasi akun.

## RUNNING dan UNKNOWN

- RUNNING menunjukkan proses masih berjalan; UNKNOWN menunjukkan hasil belum dapat dipastikan. Keduanya menahan analisis baru.
- Klik Periksa Status. Kedua keadaan sengaja tidak diselesaikan timer prototype.
- Untuk melanjutkan simulasi: Simulasi pemulihan teknis → Alur normal → Coba Analisis Lagi secara eksplisit.
- Kontrol itu alat lab. Pada aplikasi nyata pengelola teknis membuktikan proses lama berhenti dan mengesahkan keadaan terminal; bukan tombol retry Admin.
- Respons hilang, hasil tersimpan diuji tersendiri: pilih keadaan → Analisis → Periksa Status; hasil ditemukan tanpa analisis kedua.

## Penelusuran manual lanjutan

| ID | Cara melanjutkan | Hasil yang harus dicatat |
| --- | --- | --- |
| U07-11 | Operator penanggung jawab → review Valid → PREPARE → buat kandidat → sanitasi → setujui → terbitkan; uji pembatalan kandidat pengganti. | Kandidat/approval belum langsung terbit; pembatalan mempertahankan versi publik sebelumnya. |
| U07-12 | Coba close sebelum syarat lengkap; selesaikan tindak lanjut/keputusan; close dengan catatan; coba mutasi setelah CLOSED. | Penolakan sebelum syarat lengkap, close yang sah, dan penahanan perubahan sesudah CLOSED. |
| U07-13 | Admin → akun Operator → aktivasi contoh → cabut izin/nonaktifkan → assignment ke Operator lain dengan alasan → audit/monitoring. | Izin/assignment baru berlaku, akses lama hilang, draft tidak terbuka, monitoring tidak menjalankan AI. |
| U07-14 | Publik → daftar/detail → pencarian → filter kategori/lokasi → kata tanpa hasil. | Hasil sesuai field publik; data privat tidak muncul; waktu kejadian/publikasi dibedakan. |
| U07-15 | Notifikasi sesudah tindakan → tandai dibaca → notifikasi lama sesudah assignment → Offline → panduan PWA. | Notifikasi tidak menambah akses; operasi laporan ditahan saat offline; batas PWA dijelaskan. |
| U07-16 | Chrome Android dan Chrome/Edge Windows; 390×844 dan 1366×768; tambahan 360×800 dan 768×1024; menu/form/tabel/dialog/keyboard/Tab. | Perangkat/browser/versi dan viewport aktual, screenshot, kemudahan penggunaan serta Digital Awareness. |

Untuk U07-11–U07-15, hasil teknis yang tersedia dapat menjadi acuan penelusuran kelompok. U07-16 tetap memerlukan pemeriksaan perangkat/usability. Langkah lengkap dan acuan FR/NFR ada pada test-plan.md. Isi hasil aktual setelah dicoba; belum dilaporkan tidak otomatis berarti gagal atau belum pernah dicoba.

## Bukti dan finalisasi

Simpan screenshot/rekaman data fiktif di docs/uiux/bukti-review/. Catat hasil, lingkungan, ID laporan bila relevan, temuan, perbaikan dan uji ulang pada review-results.md. Versi/commit harus merujuk paket yang benar-benar diuji. Lengkapi nama peserta serta keputusan kelompok setelah review. Card tetap berjalan sampai kriteria SLR_07 terpenuhi.
