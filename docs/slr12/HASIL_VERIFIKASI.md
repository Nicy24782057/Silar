# SLR12 — Rekap implementasi dan hasil verifikasi

Dokumen dipulihkan dan diselaraskan pada 25 Oktober 2026 dari arsip paket SLR12 0.2.0 dan UI v0.4.3. Pengujian fungsi awal tercatat pada 23 Oktober 2026; verifikasi UI v0.4.3 tercatat pada 24 Oktober 2026. Pemulihan dokumen ini tidak menjalankan pengujian baru.

## Dasar bukti

- Fungsi backend SLR12 dan pengujian awal: paket `SLR12_SILAR_v0.2.0.zip`.
- Penyempurnaan frontend sampai revisi terakhir yang telah diterapkan pengguna: paket `SLR12_SILAR_UI_v0.4.3.zip`.
- Pengguna mengirim ringkasan kelulusan 34 tes pada clone Windows, melaporkan alur aplikasi dapat digunakan, dan mengonfirmasi logo Chrome/PWA berubah setelah hard refresh. Ini dicatat sebagai laporan pengguna; bukan eksekusi ulang oleh penyusun dokumen.
- Cakupan SLR12 adalah tindakan Reporter dan layanan notifikasi bersama. Dashboard pengelolaan serta pemicu event pemeriksaan/publikasi dilengkapi pada SLR13–SLR14; penerimaan lintas card mengikuti SLR15.

## Implementasi yang tersedia

| Bagian | Implementasi |
| --- | --- |
| Pemeriksaan hasil | Reporter membaca Incident Card, narasi, bukti, kategori, confidence, sumber/versi dan uncertain. Informasi yang tidak tersedia tetap dibedakan dari fakta yang terisi. |
| Koreksi field kartu | Revisi field ekstraksi membentuk kartu versi baru serta mempertahankan parent, bundle/narasi, hasil mentah AI dan flag/alasan sumber. Kategori tidak dapat disunting untuk melewati NON_EVENT. |
| Revisi narasi | Membentuk NarrativeVersion berorigin REPORTER_REVISION, menaikkan revision/input_revision, menonaktifkan kartu lama dan menuntut analisis ulang eksplisit dengan mode NARRATIVE_REVISION. |
| Perubahan bukti | Bukti asli dipertahankan; sumber aktif/bundle digunakan ketika analisis berikutnya dijalankan secara eksplisit. Hasil lama tetap memiliki sumber versinya sendiri. |
| Human Verification | Konfirmasi terikat ID kartu aktif dan sumber/hasil yang sah. Konfirmasi berulang pada versi yang sama memakai rekaman yang telah tersedia; revisi membutuhkan konfirmasi versi baru. |
| Pengiriman resmi | Submit memeriksa konfirmasi dan sumber/hasil, menetapkan kartu resmi, submitted_at dan workflow SUBMITTED. Audit serta notifikasi tersimpan dalam transaksi yang sama. Laporan tersedia melalui scope antrean pengelolaan. |
| Riwayat dan akses | Metadata versi/riwayat dipaginasi. Detail dibaca ketika dipilih. Proyeksi Reporter dibatasi hak akses dan tidak membuka catatan internal petugas atau kandidat publik yang belum diterbitkan. |
| Konsistensi dan pemulihan | Mutasi menggunakan idempotency/expected_revision dan pemeriksaan sumber/versi. Respons yang hilang dipulihkan dengan pembacaan ledger/laporan/run; formulir konflik tidak dikirim ulang atau direbase otomatis. |
| Notifikasi | Layanan bersama core.notifications.notify, daftar sesuai penerima, pagination/filter belum dibaca dan PATCH read. Penandaan berulang mempertahankan waktu baca pertama. |
| Identitas dan tema | Logo yang disediakan pengguna, gaya bersama, palet terang/gelap, preferensi browser, nilai awal perangkat dan fallback memori. Pergantian tema mempertahankan isian serta keadaan proses. |
| UI terbaru | Sidebar kiri, Detail melalui Fetch, kategori termasuk Gempa Bumi, badge status, penguncian tahap, penunjuk Bukti aktif, notifikasi ringkas serta desain Login/Registrasi/Periksa Email/OTP. |
| PWA | Cache dibatasi aset UI dan diberi versi. API, token, draft, evidence dan hasil AI tetap melewati cache privat. Pembaruan aset/logo dibedakan dari klaim pengujian instalasi baru pada perangkat fisik. |

## Lokasi kode

- Backend: `code/backend/reporting/review_services.py`, `review_views.py`, `review_serializers.py` dan `urls.py`.
- Notifikasi bersama: `code/backend/core/notifications.py`.
- Tes SLR12: `code/backend/reporting/tests/test_review.py`, `test_review_pipeline.py` dan `test_review_postgresql.py`.
- Frontend: `code/frontend/src/components/ReportReview.vue`, `VersionHistory.vue`, `ReportCardPreview.vue`, serta `src/views/DraftView.vue`, `ReportsView.vue`, `NotificationsView.vue` dan `AuthView.vue`.
- Tema/kerangka: `code/frontend/src/App.vue`, `src/theme.js`, `src/theme.css`, `src/ui.css`, `src/reports-ui.css` dan `src/auth-ui.css`.
- Panduan operasional tetap satu dokumen pada root repository: `PANDUAN_RUNNING.md`.

## Hasil verifikasi fungsi awal

| Pemeriksaan | Hasil tercatat | Bukti |
| --- | --- | --- |
| Backend komponen | 53 tes lulus: 24 regresi input, 27 API SLR12, dua sambungan revisi narasi-pipeline | [backend-komponen.txt](bukti-uji/backend-komponen.txt) |
| Clone Windows pengguna | 34 tes dilaporkan lulus dalam 10,403 detik; ringkasan dari pengguna | [backend-windows-ringkasan-pengguna.txt](bukti-uji/backend-windows-ringkasan-pengguna.txt) |
| Frontend/PWA pada UI awal | 55 tes lulus | [frontend-unit.txt](bukti-uji/frontend-unit.txt) |
| Build UI awal | Berhasil, 57 modul | [frontend-build.txt](bukti-uji/frontend-build.txt) |
| Browser UI awal | 22 skenario lulus, tanpa runtime error | [browser-results.json](bukti-uji/browser-results.json) |

Angka arsip ini dipisahkan berdasarkan versi dan lingkungan. Tes Windows bukan tambahan independen yang dijumlahkan dengan 53 tes backend komponen. Angka frontend/browser versi awal juga tidak dijumlahkan dengan hasil regresi versi terbaru.

### Cakupan backend

Tes SLR12 mencakup konfirmasi terikat versi, konfirmasi berulang, koreksi dengan sumber/flag tetap, konfirmasi ulang setelah revisi, submit tanpa/sesudah konfirmasi, submit replay, notifikasi satu kali, penyerahan ke scope antrean dan penguncian setelah submit.

Revisi narasi memeriksa perubahan sumber, tidak adanya inferensi otomatis saat penyimpanan, pemeliharaan versi lama dan perubahan narasi saat run UNKNOWN tetap menahan reservasi. Guard menolak NON_EVENT, kategori/unknown field, timestamp tanpa zona, patch tidak sah, sumber/run tidak lengkap, preparation FAILED dengan kartu tersisa, revision/parent usang, pemilik lain serta replay setelah kewenangan berubah.

Rollback diuji ketika audit atau notifikasi gagal: versi, pointer/status, audit dan ledger baru tidak tertinggal sebagai sukses. Pembacaan versi/riwayat memeriksa pagination, referensi milik laporan yang sama, versi asli dan proyeksi yang tidak membuka catatan petugas/kandidat publik internal. Notifikasi memeriksa penerima, filter, read berulang dan revision laporan yang tidak berubah.

### Cakupan browser pada arsip UI awal

1. Build produksi dan tema awal; penggantian tema lewat keyboard mempertahankan email/password tanpa POST tambahan.
2. Navigasi SLR10 dan preferensi tema bertahan saat berpindah/memuat ulang laporan.
3. Form koreksi bertahan saat tema diganti dan menghasilkan versi baru.
4. Konfirmasi versi dan pengiriman resmi merupakan tindakan terpisah; versi resmi terkunci.
5. Notifikasi penerima bisa dibaca; notifikasi akun lain tidak muncul.
6. Kartu/narasi/bukti versi lama dan perbandingan induk tidak dicampur dengan hasil aktif terbaru.
7. NON_EVENT tetap ditahan dan kategori tidak menjadi field yang dapat diedit.
8. Revisi narasi menonaktifkan kartu lama; analisis ulang mengirim mode yang benar secara eksplisit.
9. Respons koreksi diputus setelah backend commit. Pergantian tema saat respons masih ditahan menjaga isian/keadaan proses; pemulihan menggunakan pembacaan tanpa POST ganda.
10. Konflik revisi mempertahankan isian lokal dan menolak pengiriman form lama tanpa rebase otomatis.
11. Menu serta pembacaan pada 390/320 px tanpa overflow horizontal.
12. Penolakan storage memakai preferensi perangkat; pilihan manual tetap bekerja selama navigasi sesi.
13. Batas cache aset PWA dan perilaku offline. Aset mark SVG dan PNG PWA tercakup sebagai aset antarmuka.
14. Penyimpanan keterangan menutup form; perubahan teks mempertahankan satu sumber aktif dan teks asli di arsip setelah reload.
15. Penggantian audio mempertahankan satu audio aktif, teks aktif dan rekaman lama di arsip.
16. Tiga gambar ikut otomatis; gambar keempat ditolak sebelum POST upload.
17. Informasi/persetujuan Gemini diperiksa sebelum persiapan; satu klik membentuk bundle TAI yang tepat dan retry eksplisit memakai bundle yang sama.
18. Respons bundle diputus sesudah commit: analisis tidak terkirim, pembacaan memulihkan keadaan, lalu retry eksplisit tidak menggandakan bundle.
19. Draft lama dengan 22 teks membaca seluruh halaman sebelum tulis; hanya teks terbaru aktif, semua versi sebelumnya tetap ada di arsip.
20. Filter status, urutan waktu dan pagination daftar memakai query server; jumlah serta item sesuai hasil API, termasuk keadaan kosong.
21. Daftar laporan dibaca pada kedua mode dan viewport 390/320 px; kontrol tema dapat dioperasikan dengan keyboard dan kontrol filter tidak melebar keluar layar.
22. Pada sesi masuk tersendiri, halaman hasil menampilkan tujuh field, uncertain dan sumber yang tepat; status pemeriksaan/publikasi bisa dibuka, form koreksi menerima fokus keyboard, dan cache hanya memuat aset publik UI.

## Verifikasi UI terbaru: v0.4.3

Rincian lingkungan, perubahan, skenario dan batas pelaksanaan tersedia pada [HASIL_VERIFIKASI_UI_v0.4.3.md](HASIL_VERIFIKASI_UI_v0.4.3.md).

| Pemeriksaan | Hasil tercatat | Bukti |
| --- | --- | --- |
| Unit frontend/PWA | 73 lulus, 0 gagal | [frontend-tests.txt](bukti-uji/ui-v0.4.3/frontend-tests.txt) |
| Build produksi | Berhasil, 68 modul | [frontend-build.txt](bukti-uji/ui-v0.4.3/frontend-build.txt) |
| Browser development | 54 skenario lulus, 0 runtime error | [browser-checks.txt](bukti-uji/ui-v0.4.3/browser-checks.txt), [browser-results.json](bukti-uji/ui-v0.4.3/browser-results.json) |
| Browser build produksi | 3 pemeriksaan lulus, 0 runtime error | [production-checks.txt](bukti-uji/ui-v0.4.3/production-checks.txt), [production-results.json](bukti-uji/ui-v0.4.3/production-results.json) |

Angka 57 pemeriksaan browser pada ringkasan revisi terbaru terdiri atas 54 skenario development dan 3 pemeriksaan build produksi.

## Lingkungan dan batas pengujian

- Pengujian komponen awal menggunakan Linux, Python 3.12.14, Django 5.2.18, DRF 3.16.1 dan SQLite terisolasi. Migration/trigger PostgreSQL pada core serta migration accounts tidak dipakai untuk hasil komponen tersebut; hasil ini tidak membuktikan row lock/constraint PostgreSQL.
- Dua tes sambungan revisi narasi-pipeline menggunakan runtime/provider pengganti secara eksplisit. Pada sumber TAI, revisi narasi dikonsumsi SENA/NARA/Fusion; Whisper/transkripsi dan Gemini/pembentukan narasi tidak dipanggil ulang.
- Pengujian browser memakai akun/laporan sintetis dan hasil analisis fixture. Penolakan konfigurasi AI yang belum siap merupakan hasil yang diharapkan pada skenario tertentu, bukan bukti inferensi model nyata.
- Lima tes PostgreSQL tersedia pada test_review_postgresql.py. Ringkasan 34 tes Windows berasal dari pengguna dan dicatat terpisah; log per kasus serta inventaris dependensi mesin pengguna tidak tersedia pada arsip tersebut.
- UI terbaru diuji dengan Chromium 153.0.8010.0, Django 5.2.18, Vue 3.5.44 dan Vite 7.3.7. Alur akun menggunakan backend email berkas lokal. Untuk skenario resend, konfigurasi QA terisolasi memakai OTP_RESEND_SECONDS=0; konfigurasi pengguna tidak diubah.
- Ukuran HP/tablet adalah simulasi viewport browser. Bukti ini tidak menambah klaim pengujian perangkat fisik, pemasangan PWA baru, splash screen, SMTP produksi atau seluruh browser sasaran.
- Pengguna mengonfirmasi logo pada Chrome/PWA telah berubah setelah hard refresh. Pernyataan tersebut dicatat sebagai laporan pembaruan aset, terpisah dari pengujian instalasi baru.
- Screenshot internal pada revisi UI terbaru tidak menjadi lampiran paket ini. Bukti visual lama menggambarkan versi UI saat itu dan tidak dipakai sebagai gambar tampilan v0.4.3.
- Inferensi tujuh rute produksi serta model Whisper/Gemini/SENA/NARA tidak diulang untuk pemulihan dokumen atau revisi tampilan ini. Bukti SLR11 tetap digunakan sesuai cakupannya.

## Penutupan administrasi card

Bagian Bukti Pekerjaan dapat merujuk dokumen ini bersama laporan UI v0.4.3 dan log terkait. Checklist diselaraskan dengan pekerjaan yang telah dilaksanakan dan lingkup pengujian yang tercatat. Commit SHA/URL diisi oleh kelompok. Pemicu pemeriksaan/publikasi serta penerimaan terintegrasi tetap mengikuti SLR13–SLR15 sesuai pemetaan card.
