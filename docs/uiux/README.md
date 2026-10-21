# Perancangan UI UX dan Prototype SILAR

SLR_07 menghasilkan rancangan antarmuka dan simulasi interaksi sebagai pedoman frontend. Paket telah diperbarui berdasarkan audit 18 Oktober 2026: menu Buat Laporan ditutup setelah navigasi, kontras avatar diperbaiki, serta hasil review dilengkapi dengan bukti audit browser yang sesuai cakupannya. Sebanyak 60 pemeriksaan teknis lulus pada sumber hasil perbaikan. Uji visual ulang dan penerimaan kelompok masih memerlukan catatan aktual.

## Acuan dan kedudukan

- PRD SILAR versi 0.5: `docs/product/SILAR_PRD.docx`.
- Acuan Teknis SILAR rancangan 0.3 termasuk Lampiran A dan Digital Awareness A7.8: `docs/architecture/SILAR_Technical_Reference.docx`.
- Pemetaan Fitur Final SILAR 1.0: `docs/planning/SILAR_Pemetaan_Fitur_Final.md`.
- Task SLR_07 serta keputusan diskusi perancangan.

Keputusan aktif mengendalikan bagian yang berubah. Fitur lama yang dikeluarkan tidak menjadi langkah tersembunyi dalam UI. Prototype tidak mengubah acuan SLR_01–SLR_06 atau membuktikan API/model telah berjalan.

## Sumber desain dan cara membuka

Baca `MULAI_DI_SINI.txt` pada akar ZIP dan [penempatan-berkas.md](penempatan-berkas.md) untuk daftar file serta fungsinya. Paket pengumpulan disusun langsung dengan jalur `docs/uiux/`. Ekstrak ZIP ke folder sementara, lalu salin folder `docs` dari ZIP ke akar proyek SILAR. Dokumentasi utama ini berada di `docs/uiux/README.md`; sumber yang dapat diedit ada di `docs/uiux/prototype/index.html`, `styles.css`, `app.mjs`, dan `model.mjs`. Pemetaan layar ada pada `docs/uiux/screens.json`. Tidak ada package.json, README, atau konfigurasi produksi pada akar proyek yang perlu ditimpa oleh paket ini.

Dari akar proyek, jalankan `py -m http.server 8000 --directory docs/uiux/prototype` atau `python -m http.server 8000 --directory docs/uiux/prototype`, lalu buka http://localhost:8000. JavaScript memakai ES modules sehingga HTML disajikan melalui HTTP. Tidak ada dependency/build frontend tambahan untuk prototype.

Prototype daring: https://silar-slr07-wireframe.ntesengmajola699.chatgpt.site. Tautan mengikuti izin yang berlaku, bukan jaminan anggota lain otomatis mendapat akses. Panduan menyediakan unduhan paket sumber daring dan dokumen review. Salinan dokumen dalam prototype disertakan untuk unduhan; dokumentasi utama tetap berada di docs/uiux/.

Untuk pemeriksaan logika/struktur paket, jalankan `node docs/uiux/tools/check.mjs` serta `node docs/uiux/tools/review-check.mjs` dan `node docs/uiux/tools/audit-check.mjs` dari akar proyek. Sumber kerja penyusun pada Site tetap berada di dist/ dan skrip penyusun scripts/check.mjs; keduanya menghasilkan paket pengumpulan di atas. Sarana HTML/CSS/JavaScript ini tidak mengganti frontend produksi Vue 3, Composition API, Vue Router, Vite, Fetch dan CSS.

## Keputusan interaksi yang dibawa dari diskusi

1. Input multimodal dalam satu formulir, dengan sumber dan hasil yang dapat dibandingkan.
2. Rancangan rekam suara sekaligus unggah audio. Pada prototype mikrofon tidak diakses; format recorder, decoder, browser dan batas media harus divalidasi pada integrasi.
3. Penyimpanan melalui tombol Simpan Draft. Tindakan ini diterjemahkan ke layanan nyata yang sudah dirancang, bukan endpoint baru.
4. Human Verification dilakukan sebelum submit. Konfirmasi versi dan pengiriman resmi merupakan tindakan berbeda.
5. Tidak ada pertanyaan adaptif, penilaian kelengkapan otomatis, pengaitan laporan, siklus permintaan informasi tambahan, atau publikasi otomatis.

Navigasi, perangkat/browser sasaran, dan visual berikut merupakan rancangan awal untuk review. Warna netral dengan aksen hijau serta tanda merek pada wireframe bersifat sementara, bukan penetapan identitas merek final.

## Daftar layar dan keterlacakan API

Semua path berikut relatif terhadap `/api/v1/`. ID menandai layar atau interaksi; dialog dapat digunakan agar pemeriksaan tidak membutuhkan perpindahan halaman berlebihan. Beberapa state dipadatkan dalam prototype untuk simulasi, sedangkan payload dan keputusan produksi tetap mengikuti kontrak SLR_06.

| ID | Layar atau interaksi | FR | Acuan API |
| --- | --- | --- | --- |
| AK01 | Masuk | FR01 | `POST auth/login/`<br>`GET auth/csrf/`<br>`POST auth/refresh/`<br>`POST auth/logout/` |
| AK02 | Daftar Reporter | FR01 | `POST auth/register/` |
| AK03 | Verifikasi Email | FR01 | `POST auth/otp/verify/`<br>`POST auth/otp/request/` |
| AK04 | Aktivasi Operator | FR01, FR02 | `POST auth/operators/activate/` |
| AK05 | Lupa Password | FR01 | `POST auth/otp/request/` |
| AK06 | Reset Password | FR01 | `POST auth/password/reset/` |
| AK07 | Profil | FR01 | `GET me/`<br>`PATCH me/` |
| RP01 | Laporan Saya | FR03, FR14 | `GET reports/?scope=owned` |
| RP02 | Buat atau Lanjutkan Draft | FR03, FR04 | `POST reports/`<br>`POST reports/{r}/evidence/`<br>`GET reports/{r}/evidence/`<br>`GET evidence/{id}/media/`<br>`POST reports/{r}/bundles/` |
| RP03 | Analisis dan Pemulihan | FR05, FR06, FR07, FR08, FR09, FR10 | `POST reports/{r}/analyses/`<br>`GET requests/`<br>`GET requests/{key}/`<br>`GET reports/{r}/analysis-runs/{id}/`<br>`GET reports/{r}/` |
| RP04 | Pemeriksaan Koreksi Konfirmasi dan Pengiriman | FR11, FR12, FR13 | `POST reports/{r}/narratives/revisions/`<br>`POST reports/{r}/cards/revisions/`<br>`POST reports/{r}/human-verifications/`<br>`POST reports/{r}/submit/` |
| RP05 | Detail Status dan Riwayat | FR14 | `GET reports/{r}/`<br>`GET reports/{r}/versions/`<br>`GET reports/{r}/versions/{kind}/{id}/`<br>`GET reports/{r}/history/`<br>`GET reports/{r}/reviews/` |
| OP01 | Antrean Laporan | FR16 | `GET operator/queue/`<br>`POST reports/{r}/claim/` |
| OP02 | Laporan Tugas Operator | FR16, FR17 | `GET operator/assigned/` |
| OP03 | Pemeriksaan dan Tindak Lanjut | FR17, FR18, FR24 | `GET reports/{r}/`<br>`GET reports/{r}/reviews/`<br>`POST reports/{r}/reviews/`<br>`GET reports/{r}/follow-ups/`<br>`POST reports/{r}/follow-ups/`<br>`PATCH reports/{r}/follow-ups/{id}/`<br>`POST reports/{r}/close/` |
| OP04 | Keputusan Internal atau Publikasi | FR20 | `POST reports/{r}/publication-decision/` |
| OP05 | Kandidat Sanitasi Persetujuan dan Penerbitan | FR21 | `POST reports/{r}/publication-versions/`<br>`POST reports/{r}/publication-versions/{id}/approve/`<br>`POST reports/{r}/publication-versions/{id}/publish/`<br>`POST reports/{r}/publication-versions/{id}/cancel/` |
| AD01 | Pengelolaan Operator | FR02 | `GET admin/operators/`<br>`POST admin/operators/`<br>`GET admin/operators/{id}/`<br>`PATCH admin/operators/{id}/`<br>`GET admin/operator-permissions/`<br>`POST admin/operators/{id}/activation-otp/` |
| AD02 | Monitoring dan Penugasan | FR19 | `GET admin/reports/`<br>`GET reports/{r}/`<br>`GET admin/operators/`<br>`POST admin/reports/{r}/assignments/` |
| AD03 | Audit | FR23 | `GET admin/audit/` |
| AD04 | Monitoring Layanan | FR26 | `GET admin/services/` |
| PB01 | Daftar dan Pencarian Publik | FR22 | `GET public/reports/` |
| PB02 | Detail Publik | FR22 | `GET public/reports/{r}/` |
| UM01 | Notifikasi | FR15 | `GET notifications/`<br>`PATCH notifications/{id}/read/` |
| UM02 | Instalasi PWA dan Koneksi | FR25 |  |

NFR05 dan NFR06 merupakan kebutuhan utama desain pada seluruh alur. NFR02 diterapkan pada bukti, antrean, proyeksi per peran dan publikasi; NFR03 pada informasi Gemini sebelum analisis. Semua NFR tetap dipetakan ke kontribusi desain atau perilaku sistem yang relevan: NFR01 adalah kontrol akses backend; NFR04 keutuhan sumber dan versi; NFR07 pengambilan daftar/detail; NFR08 kapasitas yang terukur; NFR09 mutu AI; NFR10 konsistensi status serta pemulihan. Prototype tidak menggantikan penerimaan NFR backend atau evaluasi model.

## Alur Reporter

Laporan Saya → Buat/Lanjutkan Draft → Simpan Sumber → Analisis → Periksa/Koreksi → Konfirmasi Versi → Kirim → Detail dan Riwayat.

Pada implementasi, Simpan Draft dapat mencakup pembuatan Report jika belum ada, penyimpanan setiap item bukti secara terpisah, dan pembentukan bundle dari pilihan eksplisit. Mutasi pada Report yang sama harus mengelola revision terbaru; jangan mengunggah paralel dengan expected_revision usang. Bukti yang sudah commit dibaca kembali dari daftar evidence sampai semua halaman selesai; tidak diunggah ulang karena respons hilang. Melepas pilihan bukti tidak menghapus bukti tersimpan.

Perubahan bukti membentuk bundle baru. Koreksi narasi menghasilkan versi narasi dan meminta analisis SENA/NARA/Fusion kembali, tanpa mengulang Whisper/Gemini untuk mode narasi revisi. Koreksi field hanya menggunakan whitelist, mempertahankan hasil mentah, serta memerlukan konfirmasi baru. Kategori bukan field koreksi Reporter.

Informasi yang tidak ditemukan tetap belum tersedia. Array korban kosong tidak berarti nol korban. Waktu relatif tidak diubah menjadi tanggal pasti tanpa sumber. Hasil lengkap berarti seluruh tahap dan referensi hasil sah, bukan seluruh field kejadian terisi.

## Empat dimensi status

| Dimensi | Nilai kontrak |
| --- | --- |
| Kesiapan | DRAFT, PROCESSING, AWAITING_CONFIRMATION, READY, BLOCKED, FAILED |
| Penanganan | NOT_SUBMITTED, SUBMITTED, ASSIGNED, IN_REVIEW, FOLLOW_UP, CLOSED |
| Pemeriksaan | NOT_REVIEWED, VALID, INVALID, INCONCLUSIVE |
| Publikasi | NOT_DECIDED, INTERNAL, PENDING_APPROVAL, APPROVED, PUBLISHED |

NON_EVENT merupakan label hasil SENA yang menahan pengiriman. uncertain merupakan penanda Fusion dan dapat dikirim setelah konfirmasi sesuai syarat; konfirmasi tidak menghilangkannya. RUNNING/UNKNOWN adalah keadaan rekaman proses/request dan tidak mengganti empat dimensi status laporan.

## Operator dan Admin

Antrean hanya memuat ReportSummary tanpa identitas, alamat privat, narasi, bukti, atau keluaran mentah. Setelah klaim, detail hanya tersedia bagi penanggung jawab saat ini, Reporter pemilik, dan Admin sesuai izin. Operator lain tidak memperoleh akses melalui daftar, detail, media, riwayat, atau notifikasi lama. MVP tidak menggunakan pembagian wilayah/unit.

Review mencatat VALID/INVALID/INCONCLUSIVE beserta alasan internal. Reporter membaca proyeksi ringkas tanpa alasan internal. Tindak lanjut bukan chat atau permintaan jawaban kepada Reporter. Tindakan PENDING mencegah penutupan; pembatalan memerlukan alasan. Admin mengelola akun/izin/penugasan, monitoring dan audit; Admin tidak otomatis menjadi pelaksana pemeriksaan, publikasi atau close.

Akun Operator awal belum aktif. Admin tidak menetapkan password; pemilik mengaktifkannya melalui email. Resend aktivasi merupakan tindakan Admin dan berbeda dari permintaan OTP publik. Penonaktifan atau pencabutan izin berlaku pada akses berikutnya, tanpa menghapus riwayat. Monitoring ringkas tidak otomatis memberikan view_private_evidence; draft tetap privat bagi Reporter.

## Publikasi

Review VALID → keputusan PREPARE → pembentukan kandidat → pemeriksaan sanitasi → approval versi tepat → publish. Tidak ada penerbitan otomatis dari hasil AI, konfirmasi Reporter, atau review saja. Isi kandidat tersimpan tidak disunting langsung dalam prototype; batalkan kandidat aktif dan buat versi baru apabila isi perlu diubah.

Pembatalan hanya untuk kandidat DRAFT/APPROVED. Versi yang sudah PUBLISHED tidak ditarik pada MVP. Versi terbit sebelumnya tetap dibaca portal selama kandidat pengganti disiapkan atau dibatalkan. Review dikunci setelah publikasi pertama. CLOSED terminal untuk seluruh mutasi penanganan, publikasi, dan assignment.

Portal hanya memuat allowlist data publik; pencarian menggunakan summary/general_location/general_impact/handling_update, dengan kategori dan lokasi umum sebagai filter. Urutan produksi mengikuti published_at DESC. Prototype menggunakan urutan penerbitan dalam sesi agar publikasi baru tampil lebih dahulu; urutan simulasi itu bukan field API tambahan. Waktu kejadian dan waktu publikasi dibedakan. Gambar asli, transkrip, identitas serta kontak tidak menjadi data publik. Publikasi tidak menjamin verifikasi lapangan atau anonimitas otomatis.

## Keadaan dan pemulihan

| Keadaan | Perilaku UI |
| --- | --- |
| Kosong | Pesan sesuai konteks dan tindakan yang tersedia. |
| Input/media tidak valid | Pesan dekat tindakan; sumber gagal tidak dianggap berhasil tersimpan. |
| NON_EVENT | Konfirmasi/submit ditahan; koreksi narasi dan analisis ulang tersedia. |
| uncertain | Penanda dan penjelasan tetap ditampilkan selama pemeriksaan. |
| RUNNING | Analisis baru ditahan; pembacaan status tidak menjalankan inferensi. |
| UNKNOWN | Hasil belum dapat dipastikan; analisis baru ditahan sampai pemulihan teknis sah. |
| Respons hilang | Baca requests/run/Report sebelum retry atau melanjutkan tindakan. |
| SUCCEEDED | Baca hasil tersimpan tanpa membuat analisis atau laporan baru. |
| FAILED diketahui | Tampilkan sebab aman; retry eksplisit setelah sebab diperbaiki dan tanpa run aktif. |
| Konflik revision | Ambil detail terbaru dan periksa ulang sebelum tindakan. |
| Konflik klaim | Beri pesan aman dan perbarui antrean. |
| Kapasitas penuh | Tidak membuat run atau menganggap request telah mengantre di worker. |
| Akses ditolak | Tidak membuka isi yang di luar kewenangan. |
| Offline | Operasi laporan ditahan; tidak menjanjikan draft/sinkronisasi offline. |
| OTP salah/kedaluwarsa | Pesan aman, penggunaan email terbaru, resend sesuai purpose dan metadata backend. |

Kontrol di bar Ruang Review adalah fasilitas demonstrasi, terpisah dari produk. Tombol simulasi pemulihan teknis bukan fitur Konsol Admin. Pada sistem nyata, pengelola teknis membuktikan proses lama berhenti dan mengesahkan status terminal; Reporter baru kemudian dapat retry. Satu request tidak menjamin proses berlanjut setelah tab ditutup.

## Digital Awareness

- Panduan input: hak atas bukti, empat kategori, format, koneksi dan informasi faktual.
- Gemini: informasi masukan yang dapat keluar sebelum analisis, audio asli tetap lokal, tanpa klaim bukti otomatis anonim.
- AI/manusia: confidence bukan kebenaran; konfirmasi Reporter, review Operator, publikasi dan penutupan dibedakan.
- Akun: OTP/password dirahasiakan; tautan email membawa challenge_id saja; OTP akun bukan 2FA login. Alamat aplikasi dan pengirim resmi dikunci saat deployment.
- Publikasi: periksa identitas, alamat dan identifikasi dari gabungan lokasi/waktu/ringkasan; pertimbangkan tuduhan tanpa dukungan dan risiko salinan di luar aplikasi.
- Pemulihan: pesan menyebut tindakan berikutnya dan tidak meminta bukti rahasia dikirim ke konverter eksternal.

## Perangkat dan responsivitas

Acuan SLR_07 telah ditetapkan sebagai berikut; penetapan sasaran tidak berarti pengujian kompatibilitas selesai.

| Perangkat sasaran | Browser | Prioritas penggunaan | Viewport acuan |
| --- | --- | --- | --- |
| Ponsel Android | Google Chrome | Reporter dan Portal Publik | 390 × 844 CSS px |
| Laptop/desktop Windows | Google Chrome | Operator, Admin dan pemeriksaan seluruh peran | 1366 × 768 CSS px |
| Laptop/desktop Windows | Microsoft Edge | Kompatibilitas | 1366 × 768 CSS px |

Tambahkan pemeriksaan ukuran 360 × 800 dan 768 × 1024 CSS px melalui browser. Simulasi ukuran dibedakan dari pengujian perangkat nyata. Auditor telah mencatat Linux/Chromium 153.0.8010.0 dan empat viewport simulasi pada paket awal; bukti perangkat fisik/browser sasaran serta hasil visual ulang paket setelah perbaikan belum disampaikan.

Kriteria responsif mengikuti AC-N06: alur utama dapat digunakan tanpa kontrol tertutup atau informasi penting terpotong. Form/panel menyesuaikan layar; menu ponsel dapat dibuka/ditutup; tabel menggulir dalam area sendiri; dialog dan tindakan tetap dapat dijangkau saat keyboard tampil; teks/label/pesan/status terbaca dan status tidak hanya bergantung warna. Tindakan sesuai izin tetap dapat dijangkau ketika ukuran berubah. CSS rancangan menyesuaikan pada 760 px dan 1100 px; kelulusannya dibuktikan melalui U07-16.

## Data contoh dan batas teknis prototype

State dan akun contoh berada dalam memori sesi; refresh/Mulai ulang mengembalikannya ke fixture awal. Tidak ada API, AI, email, upload server, mikrofon, cookie autentikasi, atau cache PWA nyata. Pemilihan gambar hanya membuat pratinjau lokal. Rekaman suara merupakan placeholder. Kategori default pada analisis contoh adalah banjir; label bukan hasil pemahaman teks pengguna. Skenario NON_EVENT dan uncertain ditetapkan oleh kontrol review. Nilai confidence dan waktu proses bukan hasil evaluasi model.

Batas media, dukungan audio, TTL, retry interval dan kapasitas dalam SLR_06 masih memerlukan validasi. Angka cooldown 60 detik pada demo merupakan fixture usulan, bukan hasil pengujian konfigurasi. Pada implementasi, pesan dan kontrol mengikuti respons backend, izin saat ini, guard transisi, revision dan idempotency.

## Pemeriksaan yang tersedia

Perbaikan password salah dilakukan setelah laporan penguji. Simulasi sekarang mencocokkan email/password akun contoh, menahan login akun pendaftaran yang belum diverifikasi, serta mengganti password setelah reset valid. Akun awal: pelapor@contoh.test / Silar123!; OTP fixture: 123456. Untuk registrasi gunakan email fiktif lain dan password contoh sendiri, kemudian verifikasi; sesudah reset gunakan password baru. Operator/Admin tetap ditinjau melalui kontrol peran lab. Ini bukan autentikasi backend dan bukan bukti keamanan produksi.

Pemeriksaan `node docs/uiux/tools/check.mjs` (atau scripts/check.mjs pada sumber penyusun) menghasilkan 42 checks passed setelah perbaikan. Enam tambahan pada skrip dasar memeriksa penolakan kredensial salah, akun benar, registrasi/verifikasi, OTP kedaluwarsa, reset dan pemisahan purpose. Skrip review-check.mjs menambahkan 15 pemeriksaan terhubung ke U07-01/U07-11–U07-16; semuanya lulus secara teknis. Rendering struktur memakai stub Node, bukan browser. Audit 18 Oktober kemudian membuktikan kasus login/OTP melalui browser pada paket awal. Sesudah perbaikan menu/avatar, 42 dasar dan 15 tambahan diulang serta 3 regresi audit lulus: total 60 pemeriksaan teknis. Uji visual ulang paket terbaru belum dilakukan oleh penyusun.

## Review dan tindak lanjut

Hasil awal tersedia pada [review-results.md](review-results.md), panduan lengkap pada [test-plan.md](test-plan.md), checklist pada [review-checklist.md](review-checklist.md), dan cara mencoba OTP kedaluwarsa/password serta kasus tersisa pada [review-next-steps.md](review-next-steps.md). Catatan perbaikan teknis terpisah pada [technical-review.md](technical-review.md). Panduan pengumpulan tersedia pada [submission.md](submission.md).

Penguji awal Nicy Putra Pratama, 16 Oktober 2026, localhost:8000. Audit tambahan 18 Oktober menggunakan Linux/Chromium 153.0.8010.0 pada paket awal: tujuh alur browser lulus; 112 kombinasi halaman/peran/viewport diperiksa; ditemukan menu dan kontras avatar yang kemudian diperbaiki. Nama personal auditor tidak dicantumkan. Hasil sumber dan tindak lanjut ada di [audit-follow-up.md](audit-follow-up.md). Uji browser lama, hasil Node.js terbaru, perangkat fisik dan penerimaan kelompok dicatat terpisah.

Bukti terbaru: [hasil-pemeriksaan-teknis.json](bukti-review/hasil-pemeriksaan-teknis.json) untuk 15 uji tambahan dan [hasil-regresi-audit.json](bukti-review/hasil-regresi-audit.json) untuk tiga regresi menu/kontras. Bukti historis dan sumber audit dipertahankan di bukti-review/. Nama reviewer akhir, keputusan kelompok, hasil perangkat serta commit GitHub kelompok belum disampaikan.

Simpan bukti aktual di [bukti-review/](bukti-review/), isi temuan dan uji ulang, serta catat keputusan kelompok sebelum Done. Word boleh digunakan kelompok untuk review; README tetap menunjuk lokasi hasil aktual. Belum ada push ke GitHub SILAR kelompok dari pekerjaan ini. Dokumen Word, PDF atau PNG bukan pengganti sumber desain/prototype yang dapat diperiksa.
