# Revisi audit SLR_10 — 1.1.0

> Arsip rilis 1.1.0. Petunjuk operasional aktif kini berada di `../../PANDUAN_RUNNING.md`; hasil terbaru pada `HASIL_VERIFIKASI.md`.

Tanggal: 22 Oktober 2026. Menggantikan paket implementasi 1.0.0 pada bagian SLR_10. Status: revisi kode dan verifikasi komponen; penerimaan gabungan Windows/PostgreSQL/SLR_11 belum ditutup.

| ID | Implementasi | Bukti dan status |
| --- | --- | --- |
| R10-01 | Validator, pemilih berkas dan recorder memakai WAV PCM, MP3, WebM/Opus dan M4A/MP4-AAC. OGG, ALAC, Vorbis serta semua stream video/cover ditolak. Byte asli, batas dan hash dipertahankan. | Regresi decoding dan API lulus. Loader SLR_11 dan tujuh rute gabungan belum dijalankan pada rilis ini. |
| R10-02 | Pin Pillow 13.0.0; installer memperbarui pin 12.3.0 yang diketahui, mempertahankan pin gabungan 13.0.0 serta menghentikan konflik lain. Setup menyelesaikan kedua requirements dalam satu resolver bila AI tersedia. | Instalasi SLR_10, pip check dan decoder PNG/JPEG pada Pillow 13.0.0 lulus. Resolver lengkap requirements-ai.txt belum diverifikasi karena sumber lengkap SLR_11 tidak tersedia. |
| R10-03 | Ketiga harness SLR_07 membaca import dengan LF maupun CRLF. | Setiap jenis akhir baris: check 42, review-check 15, audit-check 3 lulus. Total 120 eksekusi pemeriksaan, berbeda dari tes Vue/browser. |
| R10-04 | Peringatan NARA berlabel ramah; fallback aman untuk kode baru. UI mencocokkan identitas run/hasil/bundle/narasi. Uncertain tidak diubah. Run gagal atau sumber berbeda diberi penjelasan dan tidak mencampurkan metadata baru. | Tes helper lulus; pemeriksaan browser menggunakan respons NARA sintetis yang ditandai secara eksplisit dalam bukti. Tidak mengklaim inferensi AI nyata. |
| R10-05 | Regresi komponen/frontend, build, prototype dan pemasang diperbarui; bukti historis dipisahkan dari rilis ini. | Hasil aktual dirangkum di HASIL_VERIFIKASI.md. PostgreSQL 16 port 5433, perangkat Windows/Android dan inferensi nyata tetap diverifikasi pada kode gabungan tim. |

## Berkas utama yang berubah

- Backend: reporting/media.py; reporting/tests/audio_fixtures.py, test_media.py, test_audio_api.py; requirements.txt.
- Frontend: src/domain.js, audio.js, analysis.js, components/AudioRecorder.vue, AnalysisResult.vue, views/DraftView.vue; tes domain/audio/analysis; versi package dan lockfile; build dist.
- Pemasang: tools/install_slr10.py, setup_slr10.py, build_release_manifest.py, tests/test_install_slr10.py; UJI_SLR10.bat; manifest distribusi.
- Prototype: docs/uiux/tools/check.mjs, review-check.mjs, audit-check.mjs. Model dan rancangan layar SLR_07 tidak diganti.
- Dokumentasi: petunjuk awal, README, API, penghubung SLR_11, checklist, hasil dan bukti pengujian.

## Pemasangan pembaruan

1. Hentikan dua server lokal dengan Ctrl+C.
2. Ekstrak ZIP revisi di folder sementara dan jalankan PASANG_KE_REPO.bat dari hasil ekstraksi.
3. Pilih root repository Silar yang sudah digunakan. Installer mengenali hash rilis 1.0.0 dan mendukung perbedaan LF/CRLF untuk sumber teks yang diketahui. Perubahan lokal yang tidak dikenal tetap menghentikan preflight sebelum penyalinan.
4. Jalankan SIAPKAN_SLR10.bat dari repository tujuan. Venv dan database tetap digunakan. .env hanya diselaraskan untuk origin/path/decoder yang diizinkan; koneksi database dan secret dipertahankan.
5. Jalankan kembali kedua server, buka localhost:5173 dan tekan Ctrl+F5 untuk memuat aset revisi.
6. Jalankan pengujian pada lingkungan tujuan serta uji bersama SLR_11 sebelum menutup checklist. Commit dan push dilakukan sendiri oleh anggota kelompok.

Tidak ada penghapusan database/venv, perubahan bobot AI, inferensi otomatis atau operasi Git pada pemasang.

## Checklist penutupan

- [x] Profil format/codec SLR_10, recorder dan panduan diperbarui serta diuji pada ruang lingkup yang tersedia.
- [x] Pillow 13.0.0 dan perlindungan installer diterapkan; PNG/JPEG dan tes komponen lulus.
- [x] Ketiga harness prototype lulus pada LF dan CRLF.
- [x] Peringatan NARA dan pemisahan identitas sumber diterapkan serta diuji dengan fixture.
- [ ] Pembacaan semua format oleh ai_pipeline.sources.load_sources pada kode gabungan.
- [ ] Resolver lengkap requirements-slr10.txt bersama requirements-ai.txt milik tim.
- [ ] Regresi PostgreSQL 16 dengan migrasi, trigger dan lock asli pada versi revisi.
- [ ] Tujuh rute sampai hasil AI nyata, konflik/replay/pemulihan analisis pada kode gabungan.
- [ ] Browser/perangkat sasaran dan pemasangan PWA nyata diverifikasi kelompok.
- [ ] Review dan Commit SHA/URL kode revisi yang benar-benar dibuat kelompok.
