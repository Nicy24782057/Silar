# SLR_13 — Task Detail dan Bukti Pekerjaan

Tanggal pembaruan: 25 Oktober 2026.

Dasar status: implementasi dan hasil verifikasi paket Operator/Admin hingga Update 03. Hasil pengujian berasal dari lingkungan pengujian terpisah; pengujian langsung pada perangkat kelompok dicatat sebagai bukti tambahan ketika tersedia.

## Tujuan

Mengimplementasikan antrean, klaim, review, validasi, tindak lanjut, penugasan, keputusan internal/publikasi, penutupan dan monitoring sesuai kewenangan Operator/Admin.

## Keterlacakan Fitur

| Peran card | Kebutuhan / kriteria |
| --- | --- |
| FR utama | FR02, FR16, FR17, FR18, FR19, FR20, FR24, FR26 |
| NFR utama | — |
| FR pendukung | FR01, FR10, FR13, FR15, FR21, FR23 |
| NFR pendukung | NFR01, NFR02, NFR04, NFR05, NFR06, NFR07, NFR10 |
| Acuan penerimaan utama | AC-F02, AC-F16, AC-F17, AC-F18, AC-F19, AC-F20, AC-F24, AC-F26 |
| Acuan pendukung | Kriteria AC untuk kebutuhan pendukung pada PRD |

Card utama mengoordinasikan penyelesaian kebutuhan. Kontribusi card pendukung dan penerimaan terintegrasi mengikuti pemetaan final serta SLR_15.

## Dependensi

Menggunakan fondasi akun/izin/audit SLR_08 dan laporan resmi serta layanan notifikasi SLR_12. SLR_14 melengkapi proses kandidat/penerbitan publikasi; pengujian guard publikasi/close dilakukan bersama SLR_14 dan SLR_15.

## Task Detail

- [x] Mengimplementasikan dashboard Operator dan Admin sesuai desain SLR_07.
- [x] Mengimplementasikan FR02: Admin mengelola akun dan izin Operator, aktivasi serta penonaktifan menggunakan layanan akun SLR_08 dan mempertahankan riwayat.
- [x] Mengimplementasikan FR16: antrean ringkas laporan resmi yang belum diklaim dalam kewenangan, tanpa PII; klaim atomik menghasilkan satu penanggung jawab.
- [x] Menerapkan pembatasan setelah assignment: detail privat, bukti dan tindakan hanya untuk penanggung jawab saat ini sesuai izin; ringkasan antrean mengikuti kontrak.
- [x] Mengimplementasikan FR17: pembacaan versi resmi, bukti, narasi dan hasil AI tanpa menyunting isi Reporter atau hasil mentah.
- [x] Mengimplementasikan FR18: review VALID/INVALID/INCONCLUSIVE, alasan, aktor/waktu, perubahan status serta tindak lanjut PENDING/DONE/CANCELLED sesuai guard.
- [x] Mengimplementasikan FR19: monitoring laporan resmi, penugasan dan pengalihan oleh Admin dengan alasan serta assignment historis; izin administratif tidak otomatis memberi kewenangan Operator.
- [x] Mengimplementasikan FR20: keputusan INTERNAL atau arah PREPARE sesuai hasil review dan izin; INVALID/INCONCLUSIVE tetap internal, dan keputusan layak publikasi belum menerbitkan laporan.
- [x] Mengimplementasikan FR24: close eksplisit dengan review yang sah, tindak lanjut selesai/dibatalkan, publikasi INTERNAL/PUBLISHED serta tanpa kandidat aktif; CLOSED menolak mutasi dan tetap mengizinkan pembacaan sesuai hak.
- [x] Mengimplementasikan FR26: pembacaan status/metadata layanan terukur sesuai izin tanpa rahasia, akses draft Reporter, perubahan model atau tindakan menjalankan ulang analisis privat.
- [x] Mengimplementasikan antarmuka baca audit FR23 sesuai izin menggunakan layanan bersama SLR_08; seluruh tindakan pengelolaan dicatat melalui layanan tersebut.
- [x] Menambahkan pemicu notifikasi FR15 untuk assignment, perubahan relevan, penanganan dan penutupan melalui layanan SLR_12, sesuai penerima.
- [x] Menerapkan expected_revision, transaksi, pemeriksaan akses replay dan perlindungan terhadap klaim/pengalihan/penutupan berulang.
- [ ] Memverifikasi hak akses, klaim bersamaan, hilangnya akses setelah pengalihan, tiga hasil review, tindak lanjut, keputusan INTERNAL dan close; memeriksa guard setelah publikasi bersama SLR_14.
- [ ] Mendokumentasikan hasil pekerjaan/verifikasi dan mencatat bukti commit kelompok.

## Catatan checklist

Tiga belas poin implementasi dicentang berdasarkan bukti pengujian yang dirinci dalam HASIL_VERIFIKASI.md. Pembatasan akses privat pada bukti ini merujuk ruang kerja Operator/Admin yang ditambahkan oleh patch.

Poin verifikasi masih terbuka karena pengujian lokal hak akses, klaim bersamaan, pengalihan, review, tindak lanjut, keputusan dan close sudah tersedia, sedangkan penerimaan melalui alur penerbitan SLR_14 yang sebenarnya belum diselesaikan bersama SLR_15. Pengujian guard terhadap keadaan kandidat/publikasi pada tingkat layanan tidak menggantikan pengujian terintegrasi tersebut.

Poin dokumentasi/commit masih terbuka karena dokumentasi sudah disiapkan pada paket ini, tetapi commit kelompok belum dibuat atau diberikan dalam percakapan. Cantumkan SHA/URL yang sebenarnya setelah commit, lalu perbarui poin tersebut pada card.

## Batasan Pekerjaan

Cakupan card adalah pengelolaan laporan resmi dan keputusan arah publikasi. Kandidat, sanitasi, approval dan penerbitan berada pada SLR_14. Monitoring Admin bersifat baca; pemulihan run tertinggal mengikuti prosedur teknis SLR_11.

## Bukti Pekerjaan

### 1. Implementasi dashboard dan akun

- Dashboard Operator memiliki pintasan Antrean dapat diklaim, Dalam penanganan, Perlu direview dan Tindak lanjut pending.
- Dashboard Admin memiliki pintasan Laporan resmi, Belum ditugaskan, Operator aktif dan Laporan ditutup. Keempatnya membuka daftar dengan filter yang sesuai; jumlah 0 tetap dapat diklik.
- Admin membuat akun Operator menggunakan nama lengkap dan email, memberikan izin, memantau aktivasi, serta mengubah status akun dengan riwayat.
- Pemilik akun Operator mengaktifkan akun melalui OTP dan menetapkan kata sandinya sendiri.
- Nama penanggung jawab berasal dari akun yang memenuhi syarat penugasan.

### 2. Implementasi pengelolaan laporan

- Antrean dan klaim, pembacaan versi resmi, review tiga hasil, tindak lanjut, keputusan INTERNAL/PREPARE dan close.
- Penugasan/pengalihan disertai alasan dan assignment historis.
- Tindak Lanjut dan Keputusan terkunci sampai review resmi tersimpan.
- Pembatasan ruang kerja mengikuti izin dan assignment saat ini. Admin tidak memperoleh kewenangan Operator hanya karena rolenya.
- Pemeriksaan revisi, transaksi, replay, audit dan notifikasi menyertai tindakan yang relevan.

### 3. Lokasi kode dan tes

| Area | Berkas utama |
| --- | --- |
| API dan aturan penanganan | code/backend/reporting/workspace_services.py; workspace_views.py; workspace_urls.py |
| Integrasi akun dan audit | code/backend/accounts/serializers.py; accounts/services.py; core/audit.py; config/urls.py |
| Tampilan dan hak navigasi | code/frontend/src/workspace.js; workspace.css; router.js; App.vue; views/Workspace*.vue |
| Komponen ruang kerja | code/frontend/src/components/WorkspaceAssignment.vue; WorkspaceEvidence.vue; WorkspaceStatus.vue |
| Tes backend | code/backend/reporting/tests/test_workspace.py; test_workspace_update02.py; test_workspace_update03.py |
| Tes frontend | code/frontend/tests/workspace.test.js; workspace-update02.test.js; workspace-update03.test.js |

### 4. Hasil verifikasi tercatat

- Patch awal: 154 tes backend terpilih, 79 tes frontend, 13 pemeriksaan browser dan 7 pemeriksaan pemasang lulus.
- Update 02: 21 tes backend workspace, 83 tes frontend, 12 pemeriksaan browser dan 8 pemeriksaan pemasang lulus.
- Update 03: 24 tes backend workspace, 88 tes frontend, 10 pemeriksaan browser dan 8 pemeriksaan pemasang lulus.
- Build frontend produksi berhasil pada ketiga tahap.
- Tahap-tahap tersebut memiliki cakupan yang tumpang tindih dan tidak dijumlahkan sebagai jumlah tes unik.
- Keluaran tes Update 03 serta ringkasan tahap sebelumnya tersedia di folder bukti-uji.

### 5. Bukti commit kelompok

Status: belum dicatat. Commit belum dibuat pada repositori kelompok oleh pekerjaan dokumentasi ini.

Setelah commit implementasi tersedia, catat SHA lengkap dan URL commit pada card SLR_13. Jika bukti juga dicatat di repositori, gunakan commit dokumentasi berikutnya untuk merujuk SHA implementasi tersebut.

## Pekerjaan yang masih terbuka

1. Menyelesaikan uji terintegrasi publikasi dan guard close bersama SLR_14/SLR_15.
2. Membuat commit kelompok untuk implementasi dan dokumentasi, lalu mencatat SHA/URL yang sebenarnya.
3. Menambahkan bukti uji perangkat kelompok jika hasil pengujian langsung sudah tersedia.

## Kriteria Selesai

Tindakan Operator/Admin sesuai PRD dan kontrak; klaim/assignment konsisten; status, alasan, audit serta notifikasi tercatat; monitoring aman; keputusan internal dan close dapat diverifikasi. Perilaku publikasi serta guard lintas alur dilengkapi SLR_14 dan diuji menyeluruh pada SLR_15.

Status keseluruhan: menunggu penyelesaian integrasi dan bukti commit. Card belum dinyatakan selesai penuh.

