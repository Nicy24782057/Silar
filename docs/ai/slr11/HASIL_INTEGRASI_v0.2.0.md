# Hasil integrasi SLR10 dan SLR11 — 0.2.0

Tanggal: 22 Oktober 2026. Basis repository `main`: `6b3a6ce7b9108bbf7fd175814f56d6ffb75f3f88`. Sumber AI: paket awal SLR11 tanggal 21 Oktober 2026. **Integrasi source tersedia dan telah diperiksa pada tingkat komponen; penerimaan PostgreSQL serta inferensi nyata pada source gabungan masih perlu dicatat tim.**

## Perubahan yang selesai

- Modul `ai_pipeline/`, requirements AI dan dokumentasi awal dipasang bersama `reporting`; endpoint akun dan input tetap tersedia. Tidak ada model laporan atau migration kedua.
- Settings/URL digabung secara terarah. AI tetap divalidasi ketika diperlukan; AI yang belum siap tidak menghalangi akun, draft dan bukti.
- Frontend menyediakan pembacaan request analisis per halaman, termasuk pilihan metadata kedaluwarsa, detail request, run terminal dan detail Report terbaru. Pembacaan ini memakai GET dan tidak mengulang inferensi.
- Body JSON mutasi yang terputus serta hasil gateway yang belum pasti diperlakukan sebagai `RESPONSE_UNKNOWN`. `REQUEST_RUNNING`/`REQUEST_UNKNOWN` menahan tindakan sampai pembacaan keadaan tersimpan. Error AI yang sudah diketahui mempertahankan kode backend.
- Panduan running tetap satu di root dan mencakup konfigurasi AI yang sudah tersedia. .env, venv, database dan model tidak dikemas atau direset.
- Commit terbaru `6b3a6ce` sudah menghapus tujuh launcher di `tools/windows/`; integrasi mengikuti perubahan tersebut dan melengkapi perapihan 19 salinan bukti aktif setelah arsip identiknya dipastikan tersedia. Metadata distribusi SLR10 diselaraskan dengan kemasan 119 berkas/37 penghapusan historis. Manifest tersebut tetap mencatat distribusi SLR10 1.1.1; paket integrasi memiliki manifest sendiri.

## Pemeriksaan aktual

| Pemeriksaan | Hasil | Cakupan dan batas |
| --- | --- | --- |
| Regresi backend yang digabung | 74 tes lulus, 0 skipped | 30 tes komponen SLR11 dan 44 reporting. SQLite terisolasi; tidak membuktikan trigger/lock PostgreSQL. |
| Sambungan input ke analisis | 9 tes lulus | Tujuh rute melalui endpoint draft/upload/bundle hingga run/card persisten, paritas serializer, akses pemilik, recovery/replay, sumber berubah, known failure, UNKNOWN, NON_EVENT/uncertain dan expiry. Memakai APIClient Django/DRF dalam proses. Runtime/provider serta kapasitas PostgreSQL diganti eksplisit pada mode SQLite. |
| Frontend | 35 tes lulus, 0 skipped | Termasuk 11 regresi baru untuk body/transport/gateway terputus serta pembacaan request/run/draft tanpa POST ulang. |
| Build Vue/PWA | Berhasil, 45 modul | Memuat UI pemulihan baru. Build bukan bukti browser/perangkat fisik. |
| Unit installer SLR10 | 14 tes lulus | Kontrak installer historis dan perlindungan konfigurasi sesuai fixture. |
| Resolver Windows/Python 3.12 | Berhasil, 64 paket | Requirements SLR10+AI, termasuk Pillow 13.0.0 dan pin stack SLR09. Resolusi bukan bukti instalasi/inferensi Windows. |
| Django check | Berhasil | Kedua modul dan endpoint akun dimuat tanpa memuat bobot atau menghubungi provider. |
| Pemasang paket integrasi | 8 skenario lulus | Preflight, existing SLR11, LF/CRLF, preservasi, konflik, path dan rollback diperiksa pada repository sementara. |

Bukti aktual berada di `evidence/integrasi-v0.2.0/`. Angka 83 backend merupakan 74 tes regresi ditambah 9 tes sambungan pada dua eksekusi; bukan satu suite PostgreSQL. Double hanya berada pada test, dan tidak menjadi fallback runtime aplikasi.

## Keterbatasan dan penerimaan tim

1. Binary PostgreSQL 16.2 tersedia, tetapi proses tidak dapat beralih dari UID root: `runuser` ditolak dengan `cannot set groups: Operation not permitted`. Cluster pengujian tidak dimulai. Lima belas tes transaksi/API asli SLR11 serta sembilan tes sambungan tersedia untuk PostgreSQL 16 tim. Mode aplikasi tetap PostgreSQL.
2. Bobot model lokal dan key Gemini proyek tidak ada dalam checkout pengujian ini. Inferensi SENA/NARA/Whisper/Gemini pada source gabungan belum dijalankan. Smoke versi awal dalam `evidence/` tetap menjadi bukti historis pada lingkungannya; tidak dihitung ulang sebagai hasil integrasi baru.
3. Browser/perangkat fisik dan kualitas audio Indonesia alami masih mengikuti pengujian lingkungan sasaran. Hasil frontend otomatis/build tidak menggantikannya.
4. Waktu proses fixture bukan ukuran latensi/kapasitas model. Pengukuran target serta penerimaan lintas kebutuhan mengikuti SLR15.
5. Source dibuat pada branch kerja lokal; tidak ada commit atau push ke repository kelompok. Commit SHA/URL diisi setelah tim menerapkan hasilnya.

Tidak ada perubahan source SLR09, threshold/label, training, fondasi akun/core/common, migration atau dokumen acuan. Perubahan field, Human Verification, konfirmasi dan submit resmi tetap mengikuti SLR12.

## Urutan uji pada lingkungan tim

Ikuti satu `PANDUAN_RUNNING.md` di root. Pertahankan Python 3.12, PostgreSQL 16 pada port lokal 5433, venv, .env dan model yang sebelumnya berhasil. Setelah source diterapkan, setup yang ada menyelesaikan requirements gabungan serta build frontend tanpa mengunduh model otomatis.

Dari direktori backend dengan venv aktif:

```powershell
python manage.py check
python manage.py test reporting.tests ai_pipeline.tests --settings=config.test_settings --verbosity=2
```

Selanjutnya jalankan aplikasi melalui dua terminal seperti panduan root. Uji T, A, I, TA, TI, AI dan TAI dengan aset/kunci nyata; periksa referensi sumber, narasi, label/confidence, NARA, uncertain/NON_EVENT dan kartu tersimpan. Putuskan respons lalu baca riwayat request; jangan mengirim POST otomatis. Catat hasil aktual pada versi kode yang diterapkan sebelum menandai card Done.

Pemeriksaan aplikasi dimulai pada basis `997eb73`. Saat penyerahan, basis diperbarui ke `6b3a6ce`, yang hanya menghapus tujuh BAT. Hash seluruh berkas backend/frontend dipastikan tetap sama; tidak diperlukan pengulangan tes aplikasi untuk perubahan basis ini. Pemasang diuji ulang terhadap basis terbaru dan kompatibilitas sumber lama.
