# Catatan Pemeriksaan Teknis SLR_07

Tanggal: 16 Oktober 2026. Pemeriksaan oleh penyusun melalui inspeksi sumber dan uji otomatis Node. Hasil pengguna Nicy Putra Pratama dicatat terpisah pada review-results.md. Penyusun tidak menjalankan browser/visual QA pada revisi ini.

## Temuan dan perbaikan

| ID | Temuan | Perbaikan | Bukti yang tersedia |
| --- | --- | --- | --- |
| T07-01 / U07-05 | Sesudah revisi narasi, halaman masih menawarkan status run lama sehingga analisis revisi tidak dapat ditelusuri dari layar. | Bedakan narasi revisi yang menunggu analisis dari run terminal lama; pertahankan rekaman lama dan tampilkan aksi analisis revisi. RUNNING/UNKNOWN tetap menahan proses baru. | Uji struktur/logika lulus; U07-05 kemudian dilaporkan berhasil oleh penguji tanpa rincian screenshot. |
| T07-02 / U07-07 | Retry sesudah pemulihan run narasi revisi memakai aksi analisis sumber awal. | Retry mempertahankan aksi NARRATIVE_REVISION. | Uji logika memastikan narasi revisi dipakai setelah RECOVERY_ABORTED; laporan umum U07-07 tersedia, rincian pemulihan belum dicatat terpisah. |
| T07-03 / R07-01 | Penguji melaporkan password salah tetap berhasil masuk. Sumber login memang hanya memeriksa isian tidak kosong. | Cocokkan email/password akun contoh; tolak akun baru yang belum diverifikasi; setelah reset valid ganti password; pertahankan pesan gagal generik. Petunjuk kredensial contoh ditambahkan. | Enam pemeriksaan tambahan lulus; uji ulang manual penguji belum dilaporkan. |
| T07-04 / R07-05 | Urutan portal memakai pembalikan array laporan sehingga informasi lama mendahului publikasi baru. | Simpan urutan penerbitan pada state simulasi dan urutkan terbaru dahulu. Implementasi produksi tetap published_at DESC sesuai kontrak. | RT-10 gagal sebelum perbaikan dan lulus sesudahnya; bukan pengukuran layout browser. |

## Hasil pemeriksaan otomatis

Sebelum perbaikan login tersedia 36 pemeriksaan logika/struktur. Setelah perbaikan, perintah `node scripts/check.mjs` pada sumber penyusun selesai dengan exit code 0 dan menghasilkan **42 checks passed**. Salinan skrip dalam paket dapat dijalankan melalui `node docs/uiux/tools/check.mjs` dari akar proyek; skrip menemukan aset relatif terhadap lokasinya.

Enam pemeriksaan tambahan mencakup password salah/email tidak dikenal ditolak; pasangan akun awal benar diterima; pendaftaran perlu verifikasi sebelum login; OTP kedaluwarsa tidak mengaktifkan akun; reset menolak OTP salah/konfirmasi berbeda dan mengganti password untuk login berikutnya; serta permintaan reset generik/purpose OTP tidak tertukar.

Pemeriksaan lain mencakup bukti/bundle, konfirmasi/submit/versi, NON_EVENT, uncertain, recovery, klaim/assignment/izin, review/tindak lanjut, publikasi/close, rendering struktur, escaping, dan ketiadaan API atau penyimpanan privat nyata pada prototype. Rendering memakai stub JavaScript, bukan browser atau bukti keamanan backend.

Akun contoh dan password fiktif hanya berada dalam memori prototype untuk memeragakan interaksi. Ini bukan autentikasi produksi, bukan penyimpanan password backend, dan bukan bukti OTP/email/JWT/CSRF sebenarnya berjalan. Semua fixture kembali ke awal setelah refresh/Mulai ulang.

Selain 42 pemeriksaan dasar, `node scripts/review-check.mjs --report docs/uiux/bukti-review/hasil-pemeriksaan-teknis.json` menghasilkan **15/15 pemeriksaan teknis lulus**. RT-01 memeriksa uji ulang akun; RT-02–RT-14 mencakup publikasi, close, Admin, portal, notifikasi dan offline/PWA; RT-15 memeriksa keberadaan konten awareness. JSON memuat hasil tiap kasus, waktu eksekusi, versi Node dan hash empat aset. Skrip dapat diulang pada paket melalui tools/review-check.mjs. Keberadaan konten tidak membuktikan keterbacaan atau pemahaman pengguna.

## Paket pengumpulan

Arsip disusun dengan allowlist jalur di bawah docs/uiux/ ditambah satu petunjuk MULAI_DI_SINI.txt pada akar ZIP. Penempatan rinci tersedia pada penempatan-berkas.md. Integritas ZIP dan kesamaan byte setiap isinya dengan sumber pembentuk diperiksa oleh scripts/package.py. Arsip tidak membawa Git metadata, identitas hosting, kredensial hosting, atau konfigurasi produksi pada akar repository kelompok. Nama dan hasil review pengguna termasuk dokumentasi yang diminta; screenshot/rekaman tidak dibuat dari asumsi.

## Pemeriksaan yang belum selesai

- Uji ulang pengguna atas login/password/reset setelah perbaikan dan OTP kedaluwarsa.
- Penelusuran manual/kelompok U07-11–U07-15 yang sudah diperiksa secara teknis; U07-16 perangkat/usability, metadata aktual dan bukti visual.
- Keputusan penerimaan kelompok serta nama peserta tambahan jika ada.
- Pemeriksaan browser/visual mandiri oleh penyusun tidak dilakukan pada lingkungan ini; hasil user yang sudah dilaporkan tidak diperluas ke perangkat lain.
- Layanan akun/API/AI/upload, decoder/mikrofon, concurrency server, instalasi/cache PWA, serta penerimaan integrasi mengikuti card implementasi dan SLR_15; bukan syarat membuktikan layanan nyata lewat prototype SLR_07.

Perbaikan teknis dan laporan pengguna dipertahankan sebagai dua jenis bukti. SLR_07 belum dinyatakan Done.
