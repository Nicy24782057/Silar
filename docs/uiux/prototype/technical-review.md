# Catatan Pemeriksaan Teknis SLR_07

Riwayat pemeriksaan: 16 dan 18 Oktober 2026. Penyusun memakai inspeksi sumber dan uji Node.js. Hasil pengguna Nicy Putra Pratama serta hasil browser dari laporan auditor dicatat terpisah pada review-results.md. Penyusun tidak menjalankan browser/visual QA ulang pada paket hasil perbaikan.

## Temuan dan perbaikan

| ID | Temuan | Perbaikan | Bukti yang tersedia |
| --- | --- | --- | --- |
| T07-01 / U07-05 | Sesudah revisi narasi, halaman masih menawarkan status run lama sehingga analisis revisi tidak dapat ditelusuri dari layar. | Bedakan narasi revisi yang menunggu analisis dari run terminal lama; pertahankan rekaman lama dan tampilkan aksi analisis revisi. RUNNING/UNKNOWN tetap menahan proses baru. | Uji struktur/logika lulus; U07-05 kemudian dilaporkan berhasil oleh penguji tanpa rincian screenshot. |
| T07-02 / U07-07 | Retry sesudah pemulihan run narasi revisi memakai aksi analisis sumber awal. | Retry mempertahankan aksi NARRATIVE_REVISION. | Uji logika memastikan narasi revisi dipakai setelah RECOVERY_ABORTED; laporan umum U07-07 tersedia, rincian pemulihan belum dicatat terpisah. |
| T07-03 / R07-01 | Penguji melaporkan password salah tetap berhasil masuk. Sumber login memang hanya memeriksa isian tidak kosong. | Cocokkan email/password akun contoh; tolak akun baru yang belum diverifikasi; setelah reset valid ganti password; pertahankan pesan gagal generik. Petunjuk kredensial contoh ditambahkan. | Enam pemeriksaan tambahan lulus; auditor kemudian mengonfirmasi penolakan password salah dan login benar melalui browser pada paket awal. |
| T07-04 / R07-05 | Urutan portal memakai pembalikan array laporan sehingga informasi lama mendahului publikasi baru. | Simpan urutan penerbitan pada state simulasi dan urutkan terbaru dahulu. Implementasi produksi tetap published_at DESC sesuai kontrak. | RT-10 gagal sebelum perbaikan dan lulus sesudahnya; bukan pengukuran layout browser. |
| T07-05 / A07-01 | Menu tetap terbuka setelah Buat Laporan pada ponsel. | Cabang new-report menutup menu/dialog sebelum membuka atau membuat draft. | AR07-01/AR07-02 gagal sebelum perbaikan dan lulus sesudahnya; meliputi draft lama, baru dan tidak menggandakan draft. |
| T07-06 / A07-02 | Avatar mewarisi warna redup dengan kontras 4,37:1. | Tetapkan color:var(--ink), yaitu #1d2b32 pada #edf1f2. | AR07-03 lulus; rasio sRGB 12,79:1. Pemindaian browser ulang masih terbuka. |

## Hasil pemeriksaan otomatis

Sebelum perbaikan login tersedia 36 pemeriksaan logika/struktur. Setelah perbaikan, perintah `node scripts/check.mjs` pada sumber penyusun selesai dengan exit code 0 dan menghasilkan **42 checks passed**. Salinan skrip dalam paket dapat dijalankan melalui `node docs/uiux/tools/check.mjs` dari akar proyek; skrip menemukan aset relatif terhadap lokasinya.

Enam pemeriksaan tambahan mencakup password salah/email tidak dikenal ditolak; pasangan akun awal benar diterima; pendaftaran perlu verifikasi sebelum login; OTP kedaluwarsa tidak mengaktifkan akun; reset menolak OTP salah/konfirmasi berbeda dan mengganti password untuk login berikutnya; serta permintaan reset generik/purpose OTP tidak tertukar.

Pemeriksaan lain mencakup bukti/bundle, konfirmasi/submit/versi, NON_EVENT, uncertain, recovery, klaim/assignment/izin, review/tindak lanjut, publikasi/close, rendering struktur, escaping, dan ketiadaan API atau penyimpanan privat nyata pada prototype. Rendering memakai stub JavaScript, bukan browser atau bukti keamanan backend.

Akun contoh dan password fiktif hanya berada dalam memori prototype untuk memeragakan interaksi. Ini bukan autentikasi produksi, bukan penyimpanan password backend, dan bukan bukti OTP/email/JWT/CSRF sebenarnya berjalan. Semua fixture kembali ke awal setelah refresh/Mulai ulang.

Selain 42 pemeriksaan dasar, `node scripts/review-check.mjs --report docs/uiux/bukti-review/hasil-pemeriksaan-teknis.json` menghasilkan **15/15 pemeriksaan teknis lulus**. RT-01 memeriksa uji ulang akun; RT-02–RT-14 mencakup publikasi, close, Admin, portal, notifikasi dan offline/PWA; RT-15 memeriksa keberadaan konten awareness. JSON memuat hasil tiap kasus, waktu eksekusi, versi Node dan hash empat aset. Skrip dapat diulang pada paket melalui tools/review-check.mjs. Keberadaan konten tidak membuktikan keterbacaan atau pemahaman pengguna.

## Audit 18 Oktober dan regresi terbaru

Audit sumber pada bukti-review/audit-sumber-2026-10-18.md memeriksa paket awal dengan SHA-256 yang cocok. Hasil browser auditor mencakup tujuh alur, 112 kombinasi halaman/peran/viewport dan 16 pemindaian aksesibilitas; rincian serta batasnya ada di audit-follow-up.md. Hasil tersebut tidak dianggap pemeriksaan visual ulang sumber terbaru.

Sesudah perbaikan menu/avatar, 42 pemeriksaan dasar dan 15 tambahan dijalankan kembali. Tiga regresi audit juga lulus melalui `node scripts/audit-check.mjs --report docs/uiux/bukti-review/hasil-regresi-audit.json`. Skrip menguji handler menu dua cabang dan menghitung warna CSS. Bukti sebelum perbaikan 0/3 lulus dipertahankan. Total sumber terbaru: 60 pemeriksaan teknis lulus; bukan 60 skenario browser.

Laporan 16 Oktober disimpan sebagai hasil-pemeriksaan-teknis-2026-10-16.json. Laporan teknis terbaru dan regresi memuat waktu serta hash aset yang diperiksa agar paket lama dan baru tidak tertukar.

## Paket pengumpulan

Arsip disusun dengan allowlist jalur di bawah docs/uiux/ ditambah satu petunjuk MULAI_DI_SINI.txt pada akar ZIP. Penempatan rinci tersedia pada penempatan-berkas.md. Integritas ZIP dan kesamaan byte setiap isinya dengan sumber pembentuk diperiksa oleh scripts/package.py. Arsip tidak membawa Git metadata, identitas hosting, kredensial hosting, atau konfigurasi produksi pada akar repository kelompok. Nama dan hasil review pengguna termasuk dokumentasi yang diminta; screenshot/rekaman tidak dibuat dari asumsi.

## Finalisasi yang memerlukan bukti aktual

- Visual ulang menu draft lama/baru pada 360/390 px dan setelah pergantian ukuran; pemindaian kontras browser sesudah perbaikan.
- Review pada perangkat/browser sasaran dan pengalaman penggunaan kelompok. Bukti audit Linux berupa viewport simulasi dipertahankan sesuai lingkupnya.
- Nama reviewer akhir, tanggal, keputusan penerimaan, tindak lanjut kelompok dan commit GitHub SILAR yang sebenarnya.
- Implementasi layanan akun/API/AI/PWA nyata dan penerimaan integrasi tetap mengikuti card implementasi/SLR_15; bukan syarat membuktikan layanan produksi melalui prototype SLR_07.

A07-01/A07-02 selesai pada tingkat kode dan regresi teknis. A07-03 telah diperbarui secara dokumentasi berdasarkan bukti yang diterima, tetapi penerimaan kelompok belum disampaikan. SLR_07 tetap In Review sampai finalisasi sesuai task.
