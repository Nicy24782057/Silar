# SLR_08 – Implementasi Fondasi Backend dan Database SILAR

## Tujuan

Menyiapkan database, layanan akun, autentikasi, kontrol akses dan audit bersama sebagai fondasi implementasi fitur sesuai ERD, Data Dictionary dan kontrak API.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR01, FR23 |
| NFR utama | NFR01 |
| FR pendukung | FR02, FR03, FR04, FR10, FR13, FR15, FR16, FR17, FR18, FR19, FR21, FR24, FR25, FR26 |
| NFR pendukung | NFR02, NFR04, NFR10 |
| Acuan penerimaan utama | AC-F01, AC-F23, AC-N01 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan PRD dan Lampiran A Acuan Teknis hasil SLR_06. Dapat berjalan paralel dengan SLR_07 dan SLR_09; fondasi ini digunakan SLR_10–SLR_14.

## Task Detail

- [ ] Menyiapkan Django, DRF, environment dan koneksi PostgreSQL; menetapkan versi paket berdasarkan kompatibilitas dan mencatatnya.
- [ ] Menetapkan Custom User UUID sebelum migration awal, email unik yang dinormalisasi, Group/Permission, auth_version dan konfigurasi blacklist JWT sesuai rancangan.
- [ ] Mengimplementasikan Django Models, foreign key, pointer siklik, constraint dan indeks mengikuti A4/A8; menjaga bukti, versi, assignment dan audit historis.
- [ ] Membuat serta menjalankan migration pada database uji, kemudian memeriksa constraint versi, assignment aktif, idempotency dan reservasi run/slot RUNNING atau UNKNOWN.
- [ ] Mengimplementasikan FR01: registrasi Reporter, login, verifikasi email OTP, resend, aktivasi akun dan reset akses sesuai challenge serta kontrak A6/A7.
- [ ] Mengimplementasikan access/refresh JWT, rotasi/logout/pencabutan, cookie dan CSRF sesuai rancangan; verifikasi email menjadi syarat akses fungsi laporan privat.
- [ ] Memverifikasi kode OTP salah/kedaluwarsa, pembatasan request dan respons aman; OTP verifikasi/aktivasi/reset dipisahkan dari 2FA login sesuai PRD.
- [ ] Menerapkan NFR01: pemeriksaan peran, izin, kepemilikan serta assignment pada baca, mutasi dan replay; menyiapkan pola pemeriksaan izin untuk layanan berikutnya.
- [ ] Menyiapkan storage media privat, lokasi aset model dan konfigurasi akses melalui backend sesuai rancangan.
- [ ] Menyiapkan pola validasi, whitelist payload, error response, expected_revision, transaksi dan ledger idempotency yang digunakan layanan fitur.
- [ ] Mengimplementasikan FR23: model serta layanan audit bersama yang mencatat aktor, peran, objek, versi dan waktu, dengan akses baca terbatas dan tanpa nilai rahasia.
- [ ] Memverifikasi migration, autentikasi, OTP, pembatasan akses dan pencatatan audit dasar menggunakan skenario yang sesuai kontrak.
- [ ] Mendokumentasikan konfigurasi, cara menjalankan backend, hasil verifikasi dan bukti commit pekerjaan kelompok.

## Batasan Pekerjaan

Cakupan card adalah fondasi database, akun, keamanan dan layanan bersama. Endpoint bisnis laporan, pipeline AI, antarmuka frontend serta aturan tindakan khusus dibangun pada SLR_10–SLR_14. Integrasi fitur menambahkan event audit melalui layanan bersama.

## Bukti Pekerjaan

Diisi setelah hasil pekerjaan tersedia:

- Kode backend, Django Models dan migration.
- Layanan akun/OTP/JWT, kontrol akses dan audit dasar.
- Hasil verifikasi constraint, autentikasi serta izin.
- Petunjuk menjalankan backend dan Commit SHA/URL setelah dibuat kelompok.

## Kriteria Selesai

Fondasi backend berjalan, migration dan constraint terverifikasi, FR01 tersedia pada layanan akun, akses privat dibatasi, layanan audit bersama tersedia, dan hasil verifikasi serta petunjuk menjalankan terdokumentasi. Penerimaan fitur yang melibatkan UI dan event bisnis dilengkapi pada card pendukung serta SLR_15.

