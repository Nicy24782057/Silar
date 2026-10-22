# Revisi SLR10 1.1.1

22 Oktober 2026. Revisi terhadap paket 1.1.0 berdasarkan audit lanjutan dan arahan pemilik proyek.

| Temuan | Penyelesaian |
| --- | --- |
| A10-01: MP3/WebM tepat 120 detik ditolak akibat metadata padding | Validator menghitung sampel hasil decode mono 16 kHz; maksimal 120 detik. Tiga tes validator dan dua tes API ditambahkan, serta 15 kasus dibandingkan dengan decoder SLR11 aktual. |
| A10-02: launcher root dan petunjuk terpisah | Tujuh launcher root dan MULAI_DI_SINI.txt diganti PANDUAN_RUNNING.md. README menjadi ringkasan proyek; rujukan aktif dan pesan script diperbarui. Script Python tetap dapat dipanggil langsung. |
| A10-03: aset build lama/file kosong | Dist dibangun bersih; sepuluh aset JS lama dan code/New Dokumen Teks.txt tidak disertakan. Manifest dibuat ulang setelah build. |
| Pemasangan pembaruan | Installer mengenali riwayat 1.0.0/1.1.0, melakukan preflight pada berkas yang dihapus, dan mencadangkan penghapusan yang hash-nya dikenal. Perubahan lokal yang tidak dikenal menghentikan preflight. |

## Perubahan utama

- `code/backend/reporting/media.py`: batas berdasarkan hasil decode, output PCM dibatasi, metadata container bukan penentu durasi akhir.
- `code/backend/reporting/tests/`: fixture durasi dan regresi validator/API.
- `tools/install_slr10.py`, `build_release_manifest.py`, `setup_slr10.py`: dukungan kemasan tanpa launcher root, riwayat manifest, backup/penghapusan terarah, dan pesan panduan.
- `PANDUAN_RUNNING.md`, `README.md`, `docs/slr10/`: satu panduan operasional, versi/status aktual, serta arsip bukti lama.
- `code/frontend/package.json` dan lockfile: metadata versi 1.1.1; dependency dan source logika frontend tetap sama. Build disertakan untuk penggunaan lokal.

Launcher bawaan SLR08 di subfolder backend dan dokumen fondasi historis tetap dipertahankan. Penyederhanaan berlaku pada launcher root yang ditunjukkan dalam screenshot. Acuan Teknis, PRD, source UI/UX, model/migration fondasi, serta kontrak API tetap sama.

## Status

- [x] Perbaikan audio diterapkan dan pengujian bagian yang berubah lulus.
- [x] Perbandingan 15 kasus batas dengan decoder SLR11 sesuai.
- [x] Satu panduan running menggantikan launcher root.
- [x] Build frontend berhasil dan source logika sebelumnya tetap sama.
- [x] Unit installer untuk perubahan penghapusan/preservasi lulus.
- [x] Empat skenario paket lengkap, hash manifest, backup/preservasi, dan reinstall diperiksa.
- [ ] Penerimaan repository gabungan terbaru di Windows/PostgreSQL dan perangkat sasaran dicatat tim.
- [ ] Alur frontend sampai hasil AI sebenarnya diterima bersama SLR11.
- [ ] Review serta Commit SHA/URL pekerjaan tim dicatat setelah dilakukan.

Rincian hasil aktual terdapat pada HASIL_VERIFIKASI.md. Langkah menjalankan aplikasi dan pembaruan hanya diarahkan ke PANDUAN_RUNNING.md di root. Penyusunan paket ini tidak melakukan commit/push, mengubah database pengguna, atau menyatakan SLR11 Done.
