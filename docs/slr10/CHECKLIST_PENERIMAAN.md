# Checklist pemeriksaan SLR_10

Kode dan hasil otomatis ditinjau bersama bukti lingkungan aktual. Status tersedia tidak otomatis menyatakan penerimaan Windows, perangkat fisik, pipeline AI atau review kelompok selesai.

| Bagian | Bukti paket | Verifikasi kelompok berikutnya |
| --- | --- | --- |
| Vue/Router/Vite/Fetch/CSS | Source, lockfile dan build dist. | Pasang di laptop, jalankan dan periksa origin/cookie. |
| Akun/OTP/profil/logout | Halaman Vue dan layanan SLR_08; tes komponen/browser yang tercatat. | Gunakan akun lokal; email terbaru, OTP salah/expired, resend, reset dan aktivasi Operator. |
| Draft dan multimodal | API reporting dan formulir asli. | Uji berkas perangkat sasaran, minimal satu kanal saat bundle/analisis. |
| Evidence dan media privat | Upload/daftar/byte media, decoder dan tes kepemilikan. | Dua akun Reporter berbeda; akses silang harus ditolak. |
| Pemulihan sebelum bundle | GET evidence tanpa mutasi dan tes tab ditutup. | Simpan lebih dari satu halaman bukti, tutup tab sebelum bundle, baca seluruh halaman yang diperlukan tanpa upload ulang. |
| Snapshot bundle | Pemilihan eksplisit, versi, hash dan transaksi. | Ganti pilihan; versi lama tetap terbaca dan konfirmasi lama tidak dipakai pada sumber baru. |
| NFR07 | Daftar ringkas, pagination dan media on demand. | Network panel: daftar tidak mengambil byte media atau raw AI. |
| Analisis/pemulihan | Request UI dan pembacaan hasil model core. | Integrasikan kode/aset SLR_11; uji tujuh rute dan hasil AI nyata. |
| PWA | Manifest, ikon, SW versi dan pemeriksaan cache/offline. | Instalasi Chrome/Edge/Android yang sebenarnya; cache API/data privat harus kosong. |
| Responsif/awareness | Tampilan diperiksa pada viewport yang tercatat. | Android/Windows fisik, keyboard/fokus dan pemahaman pesan. |
| Database fondasi | Model/migration SLR_08 tetap; tes reporting dapat dijalankan pada PostgreSQL 16. | Ikuti bagian pengujian di PANDUAN_RUNNING.md pada PostgreSQL 16 asli; catat output aktual. |
| Dokumentasi/commit | Petunjuk dan hasil paket tersedia. | Isi reviewer, tanggal keputusan kelompok, Commit SHA/URL hasil commit dan push yang benar-benar dilakukan. |

## Catatan Git

Periksa `git status` serta daftar berkas sebelum commit. .env, .venv, private_outbox, private_media, model_assets, node_modules dan backup lokal tidak disertakan. Build dist disertakan dalam ZIP untuk mencoba aplikasi, tetapi diabaikan Git; source dan package-lock menjadi hasil utama frontend.

Sebelum commit, periksa berkas yang berubah, ditambahkan, dan dihapus melalui `git status --short` serta `git diff --name-status`. Pilih perubahan revisi ini, termasuk penghapusan launcher root, tanpa memasukkan pekerjaan rekan yang belum direview. Setelah commit/push benar-benar berhasil, catat SHA/URL pada card. Penyusunan ZIP tidak menjalankan operasi Git pada repository tim.

## Penutupan audit 1.1.0

Checklist rinci per R10-01 sampai R10-05 ada di REVISI_AUDIT_1.1.0.md. Hasil versi 1.0.0 berada dalam bukti-uji/historis-v1.0.0 dan tidak dipakai sebagai kelulusan baru. Setup dan halaman login Windows 1.0.0 yang diperlihatkan pemilik proyek belum menggantikan pengujian revisi 1.1.0.

Jika Node/npm belum terpasang, build bawaan tetap dapat dicoba dengan Python. Tes frontend dan pembangunan ulang pada laptop memerlukan Node sesuai engines package.json; jangan menandai langkah npm lulus bila belum dijalankan.

## Revisi 1.1.1

- [x] Durasi dihitung dari sampel decode dan kasus tepat/melebihi 120 detik diuji.
- [x] Launcher root diganti satu PANDUAN_RUNNING.md.
- [x] Source installer melindungi penghapusan berkas distribusi lama dengan hash dan backup.
- [ ] Penerimaan repository gabungan terbaru di Windows/PostgreSQL dan perangkat sasaran dicatat tim.
- [ ] Alur frontend sampai hasil AI nyata diterima bersama SLR11.
- [ ] Review dan Commit SHA/URL hasil pekerjaan tim dicatat setelah benar-benar dibuat.

Hasil revisi serta pemeriksaan paket final dirinci pada HASIL_VERIFIKASI.md dan REVISI_1.1.1.md. Checklist implementasi tidak menyatakan pengujian lingkungan tim telah dijalankan.
