# Hasil Review dan Perbaikan UI UX SILAR SLR_07

Review awal Nicy Putra Pratama tanggal 16 Oktober 2026 dipertahankan. Laporan audit 18 Oktober 2026 menambahkan hasil browser pada paket awal: tujuh alur lulus, 112 kombinasi navigasi/viewport, serta temuan menu dan kontras avatar. Kedua masalah tampilan telah diperbaiki pada sumber; 60 pemeriksaan teknis paket hasil perbaikan lulus. Uji visual ulang dan penerimaan akhir kelompok masih perlu bukti aktual.

## Identitas dan sumber

- Tanggal pengujian dalam Word: 16 Oktober 2026.
- Penguji dan pencatat: Nicy Putra Pratama.
- Lokasi prototype dalam Word: localhost:8000.
- Perangkat, OS, browser/versi, viewport aktual: belum dicatat.
- Versi/commit paket yang benar-benar diuji: belum dicatat oleh penguji; jangan diganti dengan commit perbaikan yang belum diuji ulang.
- Sumber identitas dan nomor langkah: review-results.docx yang dilampirkan.
- Sumber hasil aktual: uraian penguji dalam percakapan pada 16 Oktober 2026. Tabel hasil pada Word masih berupa format awal.
- Screenshot/rekaman: belum dilampirkan pada sumber yang diterima. Word tidak berisi media tertanam.
- Nama anggota lain dan keputusan penerimaan kelompok: belum dicatat.

Lulus berdasarkan laporan berarti penguji menyatakan hasil sesuai. Itu bukan pemeriksaan browser mandiri oleh penyusun atau uji ulang paket sesudah diperbaiki. Penolakan yang dipersyaratkan dinilai sesuai ketika memang tertahan. Hasil teknis ditulis sebagai Lulus teknis dan tidak diatribusikan kepada penguji manual. Hasil manual yang belum diterima tetap belum dilaporkan.

## Sumber audit tambahan — 18 Oktober 2026

- Laporan: `bukti-review/audit-sumber-2026-10-18.md`; rincian tindak lanjut: `audit-follow-up.md`.
- Lingkungan auditor: Linux, Chromium 153.0.8010.0; viewport disimulasikan pada 360×800, 390×844, 768×1024 dan 1366×768.
- Paket yang diuji auditor: SHA-256 `4a829602bf3d615679420e52ab5200b9916271191c4f4b3d86541c963fae1427`, cocok dengan paket sebelum perbaikan menu/avatar.
- Nama personal auditor: tidak dicantumkan dalam laporan sumber. Hasil audit tidak diatribusikan kepada Nicy atau anggota kelompok lainnya.
- Audit browser menggunakan berkas prototype melalui intersepsi permintaan, tanpa backend/AI nyata. Hasilnya bukan pengujian fisik Android atau Chrome/Edge Windows.
- Audit ini tidak menyertakan screenshot, rekaman, keputusan penerimaan kelompok atau hasil visual ulang setelah perubahan sumber.

Kolom identitas sebelumnya merujuk review manual awal 16 Oktober. Lingkungan auditor di atas merupakan sumber bukti terpisah.

## Rekap hasil

| ID | Kasus | Hasil aktual dan sumber | Status | Bukti dan tindak lanjut |
| --- | --- | --- | --- | --- |
| U07-01 | Akun, OTP, profil, pemulihan | Catatan awal tetap disimpan. Audit browser B07-01/B07-02/B07-03 membuktikan password salah ditolak, kredensial benar membuka daftar, serta OTP kedaluwarsa ditolak dan akun belum terverifikasi tetap tidak dapat masuk. | Uji ulang browser auditor lulus untuk tiga kasus tersebut; hasil awal lain berdasarkan laporan pengguna | Audit paket awal; RT-01 menguji kembali logika pada paket hasil perbaikan. Tidak dianggap penerimaan kelompok. |
| U07-02 | Tujuh kombinasi kanal | Notifikasi muncul ketika sumber belum ditambahkan; langkah kombinasi masukan, penyimpanan teks/audio/gambar, dan pemeriksaan berikutnya dinyatakan berhasil. | Lulus berdasarkan laporan | Rincian tujuh kombinasi dan screenshot belum dicatat terpisah. Permintaan sumber tidak ditafsirkan bahwa audio dan gambar keduanya wajib. |
| U07-03 | Draft, bukti dan bundle | Langkah 1–8 dinyatakan berhasil: penyimpanan, pilihan bukti, membuka kembali draft, dan pemeriksaan perubahan sumber. | Lulus berdasarkan laporan | Tidak ditafsirkan bahwa perubahan belum tersimpan boleh dianalisis. Screenshot belum dilampirkan. |
| U07-04 | Analisis, konfirmasi, submit | Penguji menyatakan seluruh pemeriksaan berhasil. | Lulus berdasarkan laporan | ID laporan dan bukti alur belum dicatat. |
| U07-05 | Koreksi dan versi | Penguji menyatakan seluruh pemeriksaan berhasil. | Lulus berdasarkan laporan | Mendukung alur koreksi pada paket yang diuji; rincian versi/screenshot belum dicatat. |
| U07-06 | NON_EVENT dan uncertain | Penguji menyatakan seluruh pemeriksaan berhasil. Pada NON_EVENT, AI belum mengenali narasi sebagai laporan kejadian dalam cakupan. | Lulus berdasarkan laporan | NON_EVENT bukan bukti tidak ada kejadian atau pelapor berbohong; bukti uncertain belum dilampirkan. |
| U07-07 | Proses dan pemulihan | Penguji menyatakan tes berhasil; RUNNING dan UNKNOWN sama-sama tetap pada halaman analisis. | Lulus berdasarkan laporan | Menunggu sesuai simulasi; perbedaan makna dan pemulihan dijelaskan pada review-next-steps.md. Detail pemulihan belum dicatat terpisah. |
| U07-08 | Kesalahan dan keadaan khusus | Seluruh kasus dinyatakan telah dicoba dan sesuai keputusan/guard yang dikunci, termasuk penolakan yang memang diharapkan. | Lulus berdasarkan laporan | Keberhasilan tidak berarti semua tindakan langsung diterima. Bukti tiap keadaan belum dilampirkan. |
| U07-09 | Antrean dan klaim | Pengujian dinyatakan berhasil; setelah diambil, laporan tidak tersedia bagi Operator B. | Lulus berdasarkan laporan | Mendukung satu penanggung jawab dalam simulasi; bukan bukti concurrency server. |
| U07-10 | Review dan tindak lanjut | Seluruh tes dinyatakan berhasil dan sesuai hasil pemeriksaan. | Lulus berdasarkan laporan | Rincian outcome/tindak lanjut dan screenshot belum dicatat terpisah. |
| U07-11 | Kandidat dan publikasi | RT-02/RT-03 lulus. Audit browser B07-07 menelusuri PREPARE, kandidat, sanitasi, approval dan publish; approval ditahan sebelum sanitasi. Pembatalan kandidat tetap didukung bukti teknis yang terpisah. | Lulus teknis; jalur terbit lulus browser auditor pada paket awal | Kelompok belum menyampaikan hasil penelusuran mandiri/penerimaan. |
| U07-12 | Penutupan | RT-04/RT-05 membuktikan guard dan jalur internal/terbit. B07-07 menguji close setelah publikasi dan tindakan close dinonaktifkan setelah CLOSED. | Lulus teknis; jalur close terbit lulus browser auditor pada paket awal | Tidak memperluas cakupan B07-07 ke semua variasi guard. |
| U07-13 | Administrasi | Akun baru belum aktif dan tidak menerima password Admin; resend hanya Admin. Aktivasi fixture tersedia. Assignment wajib alasan, akses lama dicabut, pencabutan izin/nonaktif berlaku berikutnya. Draft/isi privat dibatasi, audit tidak merender narasi, monitoring tidak menjalankan model. | Lulus teknis; manual belum dilaporkan | RT-06–RT-08. Aktivasi hanya simulasi akun contoh, bukan layanan email/OTP nyata. |
| U07-14 | Portal Publik | Pencarian/filter/privasi/urutan lulus RT-09–RT-11. B07-07 memeriksa hasil publik yang baru diterbitkan melalui browser. | Lulus teknis; pemeriksaan hasil publik lulus browser auditor pada paket awal | Audit tidak merinci uji browser semua kombinasi pencarian/filter; penerimaan kelompok belum dicatat. |
| U07-15 | Notifikasi, offline, PWA | Pemicu notifikasi dan pembatasan penerima sesuai; tandai dibaca bekerja. Notifikasi lama tidak memulihkan akses setelah assignment. Offline menahan operasi; panduan menjelaskan batas PWA. | Lulus teknis; manual belum dilaporkan | RT-12–RT-14. Bukan uji instalasi/cache atau jaringan PWA nyata. |
| U07-16 | Responsivitas, usability, awareness | Auditor memeriksa 112 kombinasi pada empat viewport, tanpa luapan horizontal; Escape dan putaran Tab/Shift+Tab pada dialog lulus. Ditemukan menu menutup formulir dan kontras avatar kurang. Perbaikan keduanya lulus regresi handler/CSS. | Sebagian; kode diperbaiki dan uji teknis lulus; visual ulang/perangkat/usability terbuka | AR07-01–AR07-03; rasio avatar 12,79:1. Hasil viewport Linux bukan tes fisik Android/Windows. |

## Rincian U07-01

Nomor langkah mengikuti Word yang dikirim penguji.

| Langkah | Catatan aktual | Status |
| --- | --- | --- |
| 1 | Membuka akun/pendaftaran adalah pengantar; tidak dicatat terpisah. | Tidak diberi hasil tersendiri |
| 2 | Formulir kosong menampilkan permintaan pengisian. | Lulus berdasarkan laporan |
| 3 | Muncul notifikasi password harus sama dan minimal delapan karakter. | Lulus berdasarkan laporan |
| 4–5 | Pendaftaran dengan konfirmasi sama berhasil dan ada pemberitahuan. Pembukaan email contoh tidak dirinci terpisah. | Lulus berdasarkan laporan untuk alur yang dijelaskan |
| 6 | Kode benar diterima dan pengguna dapat melanjutkan ke proses masuk. | Lulus berdasarkan laporan |
| 7a | Kode salah menampilkan pesan kode tidak dapat digunakan. | Lulus berdasarkan laporan |
| 7b | Pada 16 Oktober cara uji belum dipahami. Audit browser 18 Oktober mencoba tautan Email contoh; kode kedaluwarsa ditolak dan akun tetap belum terverifikasi. | Lulus pada audit browser paket awal (B07-03) |
| 8 | Ada waktu tunggu kirim ulang. | Lulus berdasarkan laporan |
| 9 | Lupa password dinyatakan berhasil. | Lulus berdasarkan laporan |
| 10 | Catatan kegagalan awal dipertahankan. Sesudah perbaikan login, auditor membuktikan password salah tetap di halaman Masuk dan kredensial benar membuka daftar. | Uji ulang browser paket awal lulus (B07-01/B07-02) |
| 11–12 | Profil/keluar dan field email/peran terkunci dinyatakan berhasil. | Lulus berdasarkan laporan |

## Temuan dan tindak lanjut

| ID | Temuan/kebutuhan | Tindakan yang telah dilakukan | Status lanjutan |
| --- | --- | --- | --- |
| R07-01 / T07-03 | Password salah tetap masuk. Inspeksi sumber menemukan login hanya memeriksa isian tidak kosong. | Simulasi mencocokkan email/password akun contoh, menahan akun pendaftaran sebelum verifikasi, dan mengganti password setelah reset yang valid. Pemeriksaan otomatis ditambahkan. | Perbaikan teknis dan uji browser auditor B07-01/B07-02 lulus pada paket awal; keputusan kelompok tetap terpisah. |
| R07-02 | Cara uji OTP kedaluwarsa belum dipahami. | Panduan menggunakan Uji keadaan → OTP kedaluwarsa tersedia pada review-next-steps.md. Guard lulus uji otomatis. | Audit browser B07-03 mengonfirmasi penolakan kode kedaluwarsa pada paket awal; catatan awal tetap dipertahankan. |
| R07-03 | RUNNING/UNKNOWN sama-sama tampak menunggu. | Dicatat sebagai perilaku simulasi yang diharapkan; perbedaan makna, Periksa Status dan pemulihan dijelaskan. | Tambahkan bukti pesan/pemulihan saat melengkapi rincian review. Tidak dicatat sebagai layanan nyata yang macet. |
| R07-04 | Pada review awal, bukti U07-11–U07-16 belum lengkap dan penerimaan kelompok belum tersedia. | Hasil teknis dan hasil browser auditor yang sesuai lingkup telah ditambahkan; bukti perangkat sasaran dan penerimaan kelompok belum disampaikan. | Lengkapi pemeriksaan browser/kelompok tanpa mengganti hasil teknis menjadi hasil manual. |
| R07-05 / T07-04 | Portal membalik urutan array laporan sehingga publikasi lama muncul sebelum publikasi baru. | Simulasi menyimpan urutan penerbitan setiap versi dan mengurutkan terbaru dahulu. | RT-10 gagal sebelum perbaikan dan lulus sesudahnya; uji ulang tampilan browser masih terbuka. |

## Hasil browser dari laporan audit

| ID bukti | Alur yang benar-benar dicatat auditor | Hasil | Hubungan review |
| --- | --- | --- | --- |
| B07-01 | Login dengan password salah. | Ditolak; halaman Masuk dipertahankan. | U07-01 / R07-01. |
| B07-02 | Login dengan kredensial fixture benar. | Daftar laporan terbuka. | U07-01. |
| B07-03 | OTP kedaluwarsa melalui Email contoh; mencoba masuk sebelum verifikasi. | Kode ditolak dan akun belum terverifikasi tetap tidak dapat masuk. | U07-01 / R07-02. |
| B07-04 | Reporter: draft → analisis → konfirmasi → submit eksplisit, lebar 390 px. | Alur selesai sesuai urutan. | U07-03/U07-04. |
| B07-05 | Membuka dialog pemeriksaan dan menekan Escape. | Dialog terbuka lalu tertutup. | Bagian keyboard U07-16. |
| B07-06 | Tab dan Shift+Tab setelah fokus awal dialog terpasang. | Fokus berputar di dalam dialog pemeriksaan. | Bagian keyboard U07-16. |
| B07-07 | Operator: klaim → review → PREPARE → kandidat → sanitasi → approval → publish → periksa hasil publik → close. | Lulus; approval ditahan sebelum sanitasi dan close dinonaktifkan setelah CLOSED. | Bagian U07-09/U07-10/U07-11/U07-12/U07-14. |

Semua B07 merupakan hasil pada paket awal yang dilaporkan auditor, bukan pengujian ulang visual oleh penyusun pada paket setelah perbaikan. Cakupan yang tidak disebut tetap mengikuti bukti teknis/hasil pengguna masing-masing.

## Temuan audit dan penyelesaiannya

| ID | Hasil setelah tindak lanjut | Status bukti |
| --- | --- | --- |
| A07-01 | Menu ditutup pada aksi Buat Laporan, baik membuka draft lama maupun membuat draft baru; membuka ulang tidak menggandakan draft. | AR07-01/AR07-02 lulus; visual ulang 360/390 px dan peralihan viewport belum dicatat. |
| A07-02 | Warna avatar menjadi #1d2b32 pada #edf1f2; perhitungan kontras 12,79:1. | AR07-03 lulus; pemindaian browser ulang belum dilakukan. |
| A07-03 | Hasil audit, lingkungan, bukti, tindak lanjut dan status penerimaan diperbarui pada dokumen terkait. | Perangkat sasaran, nama reviewer akhir, keputusan kelompok dan commit GitHub kelompok masih perlu data aktual. |

## Pemeriksaan teknis tambahan

Pemeriksaan 16 Oktober dipertahankan pada hasil-pemeriksaan-teknis-2026-10-16.json. Pengujian diulang pada 18 Oktober 2026 setelah perbaikan, menggunakan Node.js, model simulasi, handler klik dan proyeksi HTML dengan stub DOM. Ini bukan pemeriksaan browser atau pengujian backend. Hasil tiap uji, waktu eksekusi, versi Node dan hash empat aset tersimpan pada `bukti-review/hasil-pemeriksaan-teknis.json`.

- Pemeriksaan dasar: 42 lulus melalui `tools/check.mjs`.
- Pemeriksaan tambahan: 15 lulus melalui `tools/review-check.mjs`.
- Uji ulang teknis R07-01/R07-02: password salah ditolak dan OTP kedaluwarsa tidak mengaktifkan akun (RT-01).
- Publikasi sampai offline/PWA: RT-02–RT-14, sesuai lingkup tiap baris rekap.
- Digital Awareness: RT-15 hanya memeriksa keberadaan konten, bukan pemahaman/keterbacaan pengguna.
- Regresi audit: 3 lulus melalui tools/audit-check.mjs; hasil terbaru pada bukti-review/hasil-regresi-audit.json. Total paket hasil perbaikan: 60 pemeriksaan teknis lulus.

## Keputusan saat ini

Paket diperbarui untuk temuan audit SLR_07. Sumber desain, prototype, pemetaan dan hasil review tersedia; masalah menu/avatar diperbaiki dan uji regresi teknis lulus. Hasil browser auditor sudah dicatat sesuai paket dan cakupannya.

| Data penerimaan | Keadaan aktual |
| --- | --- |
| Review awal pengguna | Nicy Putra Pratama; 16 Oktober 2026; localhost:8000. |
| Review teknis eksternal | Laporan audit 18 Oktober 2026; Linux/Chromium 153.0.8010.0; identitas personal auditor tidak dicantumkan. |
| Uji ulang visual setelah perbaikan menu/avatar | Belum dilaporkan; tersedia langkah reproduksi pada review-next-steps.md. |
| Perangkat fisik/browser sasaran dan pengalaman penggunaan kelompok | Bukti aktual belum disampaikan. |
| Nama reviewer akhir dan tanggal penerimaan kelompok | Belum disampaikan; tidak disamakan dengan penguji awal atau auditor. |
| Keputusan penerimaan kelompok | Belum disampaikan; card tetap In Review. |
| Commit final GitHub SILAR kelompok | Belum disampaikan; diisi setelah commit/push yang sebenarnya. |

Untuk menutup A07-03, tambahkan catatan aktual kelompok dan tautan bukti, atau hasil pemeriksaan baru bila kegiatan belum dilakukan. Ketiadaan catatan tidak menyatakan kegiatan pasti belum pernah dilakukan. Done berlaku untuk lingkup desain/prototype SLR_07, tanpa menunggu frontend produksi atau pipeline AI. Riwayat temuan awal tetap disimpan.
