# Hasil Review dan Perbaikan UI UX SILAR SLR_07

Review awal dilakukan oleh Nicy Putra Pratama pada Jumat, 16 Oktober 2026. Dokumentasi diperbarui pada 18 Oktober 2026 berdasarkan audit, perbaikan teknis, dan keterangan tambahan reviewer.

Laporan audit menambahkan tujuh alur browser yang lulus, pemeriksaan 112 kombinasi navigasi/viewport, serta temuan menu ponsel dan kontras avatar. Kedua masalah tersebut telah diperbaiki pada sumber dan didukung 60 pemeriksaan teknis yang lulus.

Reviewer mengonfirmasi penggunaan laptop Windows 11 dengan Google Chrome. Pemeriksaan responsivitas dilakukan melalui Chrome DevTools pada lebar 360 px dan 390 px. Screenshot pengujian dinyatakan tersedia pada folder bukti review. Kelompok telah menyepakati hasil desain setelah audit sebagai acuan implementasi frontend.

## Identitas dan sumber

| Komponen | Keterangan |
| --- | --- |
| Penguji dan pencatat | Nicy Putra Pratama. |
| Tanggal review awal | Jumat, 16 Oktober 2026. |
| Tanggal pembaruan dokumentasi | 18 Oktober 2026. |
| Perangkat pengujian | Laptop. |
| Sistem operasi | Windows 11. |
| Browser | Google Chrome; nomor versi belum dicatat. |
| Lokasi prototype | http://localhost:8000. |
| Sumber prototype | `docs/uiux/prototype/`. |
| Metode pemeriksaan responsivitas | Simulasi viewport melalui Inspect/Chrome DevTools pada laptop. |
| Lebar viewport yang dikonfirmasi | 360 px dan 390 px. |
| Tinggi viewport | Belum dicatat. |
| Pengujian pada HP fisik | Belum dilakukan berdasarkan keterangan reviewer. |
| Identitas paket / commit yang diuji | Belum dicatat secara spesifik oleh penguji. |
| Sumber identitas dan nomor langkah awal | Catatan `review-results.docx` yang sebelumnya diberikan. |
| Sumber hasil aktual | Uraian penguji pada review awal dan konfirmasi tambahan setelah audit. |
| Screenshot | Penguji menyatakan screenshot tersedia pada `docs/uiux/bukti-review/`. |
| Pengalaman penggunaan | Tulisan dinilai cukup terbaca; penyempurnaan tampilan dilanjutkan pada tahap frontend. |
| Persetujuan kelompok | Hasil desain telah disepakati sebagai acuan implementasi setelah audit. |
| Status unggah | Berkas sebelumnya sudah di-push; tambahan gambar dan berkas terbaru belum di-push saat catatan diperbarui. |

Tanggal 16 Oktober merupakan tanggal review awal. Audit dan pembaruan dokumentasi dicatat pada 18 Oktober. Tanggal pengujian ulang tidak ditetapkan secara terpisah karena belum disebutkan oleh reviewer.

Lulus berdasarkan laporan berarti penguji menyatakan hasil sesuai. Hasil tersebut dibedakan dari pemeriksaan teknis otomatis dan audit browser. Penolakan yang dipersyaratkan dinilai sesuai ketika sistem memang menahan tindakan tersebut.

Ketersediaan screenshot dicatat berdasarkan keterangan penguji. Nama berkas mengikuti bukti yang benar-benar disimpan pada folder `bukti-review/`.

## Sumber audit tambahan — 18 Oktober 2026

- Laporan: `bukti-review/audit-sumber-2026-10-18.md`.
- Rincian tindak lanjut: `audit-follow-up.md`.
- Lingkungan auditor: Linux, Chromium 153.0.8010.0.
- Viewport audit: 360 × 800, 390 × 844, 768 × 1024, dan 1366 × 768.
- Paket yang diuji auditor: SHA-256 `4a829602bf3d615679420e52ab5200b9916271191c4f4b3d86541c963fae1427`, sesuai paket sebelum perbaikan menu/avatar.
- Identitas personal auditor tidak dicantumkan dalam laporan sumber.
- Audit browser menggunakan berkas prototype melalui intersepsi permintaan, tanpa backend atau layanan AI nyata.
- Audit sumber tidak menyertakan screenshot maupun hasil visual ulang setelah perubahan sumber.

Lingkungan audit Linux/Chromium dan pengujian reviewer pada Windows 11/Google Chrome merupakan dua sumber bukti yang berbeda.

Ukuran viewport audit tidak digunakan untuk mengisi tinggi viewport reviewer yang belum dicatat.

## Rekap hasil

| ID | Kasus | Hasil aktual dan sumber | Status | Bukti dan tindak lanjut |
| --- | --- | --- | --- | --- |
| U07-01 | Akun, OTP, profil, pemulihan | Catatan kegagalan login awal dipertahankan. Audit browser membuktikan password salah ditolak, kredensial benar diterima, serta OTP kedaluwarsa ditolak dan akun belum terverifikasi tetap tidak dapat masuk. | Uji ulang audit browser lulus untuk kasus tersebut; logika juga lulus pemeriksaan teknis terbaru. | B07-01/B07-02/B07-03 dan RT-01. |
| U07-02 | Tujuh kombinasi kanal | Notifikasi muncul ketika sumber belum ditambahkan. Penguji menyatakan langkah kombinasi masukan dan penyimpanan teks/audio/gambar berhasil. | Lulus berdasarkan laporan. | Audio dan gambar tidak ditafsirkan sebagai dua kanal yang selalu wajib ditambahkan bersamaan. |
| U07-03 | Draft, bukti, dan bundle | Langkah penyimpanan, pemilihan bukti, pembukaan kembali draft, dan pemeriksaan perubahan sumber dinyatakan berhasil. | Lulus berdasarkan laporan. | Bukti pengujian mengacu pada folder `bukti-review/`; rincian nama screenshot mengikuti berkas aktual. |
| U07-04 | Analisis, konfirmasi, submit | Penguji menyatakan seluruh pemeriksaan berhasil. Audit juga menelusuri draft hingga submit eksplisit pada lebar 390 px. | Lulus berdasarkan laporan; alur audit browser lulus. | B07-04. Konfirmasi versi dan pengiriman laporan tetap menjadi tindakan terpisah. |
| U07-05 | Koreksi dan versi | Penguji menyatakan seluruh pemeriksaan berhasil. | Lulus berdasarkan laporan. | Mendukung alur koreksi dan konfirmasi terhadap versi laporan yang diperiksa. |
| U07-06 | NON_EVENT dan uncertain | Penguji menyatakan pemeriksaan berhasil. Pada NON_EVENT, narasi belum dikenali sebagai laporan kejadian dalam cakupan. | Lulus berdasarkan laporan. | NON_EVENT tidak menyatakan kejadian pasti tidak ada atau pelapor berbohong. |
| U07-07 | Proses dan pemulihan | Penguji menyatakan tes berhasil; RUNNING dan UNKNOWN sama-sama berada pada halaman analisis. | Lulus berdasarkan laporan sesuai perilaku simulasi. | Perbedaan makna status dan langkah pemulihan dijelaskan pada `review-next-steps.md`. Hasil pemulihan belum dirinci terpisah. |
| U07-08 | Kesalahan dan keadaan khusus | Penguji menyatakan kasus yang dicoba sesuai keputusan dan guard yang telah dikunci. | Lulus berdasarkan laporan. | Keberhasilan mencakup penolakan terhadap tindakan yang memang tidak diizinkan. |
| U07-09 | Antrean dan klaim | Pengujian dinyatakan berhasil. Setelah laporan diambil, laporan tidak tersedia bagi Operator B. | Lulus berdasarkan laporan. | Mendukung satu penanggung jawab dalam simulasi. Pengujian concurrency server mengikuti tahap implementasi backend. |
| U07-10 | Review dan tindak lanjut | Penguji menyatakan seluruh pemeriksaan berhasil dan sesuai alur. | Lulus berdasarkan laporan. | Hasil mencakup pemeriksaan dan tindak lanjut sesuai kasus yang dicoba penguji. |
| U07-11 | Kandidat dan publikasi | RT-02/RT-03 lulus. Audit menelusuri PREPARE, kandidat, sanitasi, approval, dan publish; approval ditahan sebelum sanitasi. | Lulus teknis; jalur terbit lulus audit browser pada paket awal. | B07-07. Pembatalan kandidat didukung pemeriksaan teknis tersendiri. |
| U07-12 | Penutupan | RT-04/RT-05 membuktikan guard dan jalur penutupan. Audit menguji close setelah publikasi dan penonaktifan tindakan close setelah CLOSED. | Lulus teknis; jalur close setelah publikasi lulus audit browser pada paket awal. | B07-07. Cakupan audit mengikuti jalur yang dicatat auditor. |
| U07-13 | Administrasi | Pemeriksaan teknis mencakup aktivasi Operator, resend, assignment dengan alasan, pencabutan akses, audit berizin, dan monitoring. | Lulus teknis; hasil manual terperinci belum dilaporkan. | RT-06–RT-08. Aktivasi akun dan email menggunakan simulasi. |
| U07-14 | Portal Publik | Pencarian, filter, privasi, dan urutan publikasi lulus pemeriksaan teknis. Audit memeriksa hasil publik yang baru diterbitkan. | Lulus teknis; pemeriksaan hasil publik lulus audit browser pada paket awal. | RT-09–RT-11 dan B07-07. |
| U07-15 | Notifikasi, offline, PWA | Pemeriksaan teknis mencakup penerima notifikasi, tandai dibaca, pembatasan akses, penahanan operasi offline, dan panduan PWA. | Lulus teknis; hasil manual terperinci belum dilaporkan. | RT-12–RT-14. Instalasi dan cache PWA nyata belum dibuktikan. |
| U07-16 | Responsivitas, usability, awareness | Auditor memeriksa 112 kombinasi pada empat viewport. Reviewer mengonfirmasi simulasi lebar 360/390 px melalui Chrome Windows 11 dan menilai tulisan cukup terbaca. Screenshot dinyatakan tersedia. | Hasil audit dan teknis tersedia; lingkungan serta pengalaman reviewer telah dicatat. | AR07-01–AR07-03. Rincian screenshot untuk menu/pergantian ukuran dan hasil kontras browser belum dicatat terpisah. |

## Rincian U07-01

Nomor langkah mengikuti catatan review awal yang diberikan penguji.

| Langkah | Catatan aktual | Status |
| --- | --- | --- |
| 1 | Membuka akun/pendaftaran merupakan pengantar pengujian. | Tidak diberi hasil tersendiri. |
| 2 | Formulir kosong menampilkan permintaan pengisian. | Lulus berdasarkan laporan. |
| 3 | Muncul notifikasi terkait kesamaan konfirmasi password dan ketentuan minimal delapan karakter. | Lulus berdasarkan laporan. |
| 4–5 | Pendaftaran dengan konfirmasi password yang sesuai berhasil dan menampilkan pemberitahuan. Pembukaan email contoh tidak dirinci terpisah. | Lulus berdasarkan laporan untuk alur yang dijelaskan. |
| 6 | Kode benar diterima dan pengguna dapat melanjutkan ke proses masuk. | Lulus berdasarkan laporan. |
| 7a | Kode salah menampilkan pesan bahwa kode tidak dapat digunakan. | Lulus berdasarkan laporan. |
| 7b | Pada review awal, cara menguji kode kedaluwarsa belum dipahami. Audit 18 Oktober kemudian membuktikan kode kedaluwarsa ditolak dan akun tetap belum terverifikasi. | Lulus audit browser paket awal, B07-03. |
| 8 | Terdapat waktu tunggu sebelum pengiriman ulang kode. | Lulus berdasarkan laporan. |
| 9 | Lupa password dinyatakan berhasil. | Lulus berdasarkan laporan. |
| 10 | Review awal menemukan password salah tetap berhasil masuk. Setelah perbaikan, audit membuktikan password salah ditolak dan kredensial benar diterima. | Temuan awal dipertahankan; uji ulang audit browser lulus, B07-01/B07-02. |
| 11–12 | Profil/keluar dan field email/peran yang terkunci dinyatakan berhasil. | Lulus berdasarkan laporan. |

## Temuan dan tindak lanjut

| ID | Temuan/kebutuhan | Tindakan yang telah dilakukan | Status lanjutan |
| --- | --- | --- | --- |
| R07-01 / T07-03 | Password salah tetap dapat masuk. | Simulasi mencocokkan email/password akun contoh, menahan akun sebelum verifikasi, dan menggunakan password baru setelah reset yang valid. Pemeriksaan otomatis ditambahkan. | Perbaikan lulus audit browser pada paket awal dan pemeriksaan teknis terbaru. |
| R07-02 | Cara menguji OTP kedaluwarsa belum dipahami. | Panduan penggunaan keadaan OTP kedaluwarsa tersedia pada `review-next-steps.md`. Guard juga diperiksa secara otomatis. | Audit B07-03 mengonfirmasi penolakan kode kedaluwarsa; catatan awal tetap dipertahankan. |
| R07-03 | RUNNING dan UNKNOWN sama-sama tampak menunggu. | Perbedaan makna status, tindakan Periksa Status, dan langkah pemulihan dijelaskan dalam panduan. | Perilaku simulasi telah dijelaskan. Hasil pemulihan belum dirinci terpisah oleh penguji. |
| R07-04 | Pada review awal, bukti lanjutan dan penerimaan kelompok belum lengkap. | Hasil teknis dan audit ditambahkan. Reviewer kemudian memberikan rincian lingkungan, pengalaman penggunaan, informasi screenshot, dan konfirmasi persetujuan kelompok. | Persetujuan desain telah dicatat. Rujukan screenshot dan commit tambahan mengikuti berkas aktual yang diunggah kelompok. |
| R07-05 / T07-04 | Publikasi lama dapat muncul sebelum publikasi baru akibat urutan array laporan. | Simulasi menyimpan urutan penerbitan setiap versi dan menampilkan publikasi terbaru terlebih dahulu. | RT-10 gagal sebelum perbaikan dan lulus setelah perbaikan. Hasil visual ulang khusus urutan publikasi belum dirinci. |

## Hasil browser dari laporan audit

| ID bukti | Alur yang dicatat auditor | Hasil | Hubungan review |
| --- | --- | --- | --- |
| B07-01 | Login dengan password salah. | Ditolak; pengguna tetap pada halaman Masuk. | U07-01 / R07-01. |
| B07-02 | Login dengan kredensial akun contoh yang benar. | Daftar laporan terbuka. | U07-01. |
| B07-03 | OTP kedaluwarsa melalui Email contoh; mencoba masuk sebelum verifikasi. | Kode ditolak dan akun belum terverifikasi tetap tidak dapat masuk. | U07-01 / R07-02. |
| B07-04 | Reporter: draft → analisis → konfirmasi → submit eksplisit pada lebar 390 px. | Alur selesai sesuai urutan. | U07-03 / U07-04. |
| B07-05 | Membuka dialog pemeriksaan dan menekan Escape. | Dialog terbuka lalu tertutup. | Bagian keyboard U07-16. |
| B07-06 | Menggunakan Tab dan Shift+Tab setelah fokus awal dialog terpasang. | Fokus berputar di dalam dialog pemeriksaan. | Bagian keyboard U07-16. |
| B07-07 | Operator: klaim → review → PREPARE → kandidat → sanitasi → approval → publish → periksa hasil publik → close. | Alur lulus; approval ditahan sebelum sanitasi dan close dinonaktifkan setelah CLOSED. | U07-09 / U07-10 / U07-11 / U07-12 / U07-14. |

Semua B07 merupakan hasil pada paket awal yang dilaporkan auditor. Hasil tersebut tetap dicatat sesuai paket dan cakupan pengujiannya.

Persetujuan kelompok terhadap desain dicatat berdasarkan konfirmasi penanggung jawab setelah audit.

## Temuan audit dan penyelesaiannya

| ID | Hasil setelah tindak lanjut | Status bukti |
| --- | --- | --- |
| A07-01 | Menu ditutup pada aksi Buat Laporan, baik membuka draft lama maupun membuat draft baru. Membuka ulang tidak menggandakan draft. | AR07-01/AR07-02 lulus. Reviewer mengonfirmasi pemeriksaan pada lebar 360/390 px dan ketersediaan screenshot. Rincian bukti setiap kasus dan pergantian ukuran belum dicatat terpisah. |
| A07-02 | Warna teks avatar menjadi `#1d2b32` pada latar `#edf1f2`. Perhitungan kontras menghasilkan 12,79:1. | AR07-03 lulus. Angka tersebut berasal dari perhitungan teknis CSS; hasil pengukuran ulang melalui browser belum dilaporkan. |
| A07-03 | Identitas reviewer, lingkungan Windows 11/Chrome, simulasi lebar 360/390 px, pengalaman keterbacaan, dan persetujuan desain telah dicatat. | Rincian utama telah diperbarui berdasarkan keterangan reviewer. Versi Chrome, identitas paket yang diuji, rujukan screenshot, dan tautan commit pembaruan belum dicantumkan. |

## Pemeriksaan teknis tambahan

Pemeriksaan 16 Oktober dipertahankan pada `bukti-review/hasil-pemeriksaan-teknis-2026-10-16.json`.

Pengujian setelah perbaikan dilakukan pada 18 Oktober 2026 menggunakan Node.js, model simulasi, handler klik, proyeksi HTML dengan stub DOM, dan perhitungan warna CSS.

Hasil tiap uji, waktu eksekusi, versi Node, dan hash empat aset tersimpan pada `bukti-review/hasil-pemeriksaan-teknis.json`.

| Kelompok pemeriksaan | Skrip / bukti | Hasil |
| --- | --- | --- |
| Pemeriksaan dasar | `tools/check.mjs` | 42 lulus. |
| Pemeriksaan tambahan | `tools/review-check.mjs` | 15 lulus. |
| Regresi audit menu/avatar | `tools/audit-check.mjs` | 3 lulus. |
| Total pemeriksaan teknis | `hasil-pemeriksaan-teknis.json` dan `hasil-regresi-audit.json` | 60 lulus. |

Cakupan pemeriksaan tambahan:

- RT-01: password salah ditolak dan OTP kedaluwarsa tidak mengaktifkan akun.
- RT-02–RT-05: kandidat, publikasi, dan penutupan sesuai guard.
- RT-06–RT-08: administrasi, assignment, dan pembatasan akses.
- RT-09–RT-11: Portal Publik, urutan publikasi, pencarian/filter, dan privasi.
- RT-12–RT-14: notifikasi, pembatasan operasi offline, dan panduan PWA.
- RT-15: keberadaan konten Digital Awareness.

Pemeriksaan teknis tersebut merupakan bukti pengujian logika dan sumber prototype. Pemeriksaan ini tidak menggantikan penilaian tampilan, pemahaman pengguna, atau pengujian backend.

Pembaruan dokumen ini mencatat hasil yang telah tersedia dan keterangan tambahan reviewer; tidak dihitung sebagai pelaksanaan pengujian baru.

## Keputusan saat ini

Kelompok telah menyepakati hasil perancangan UI/UX dan prototype SILAR setelah audit sebagai acuan implementasi frontend.

Sumber desain, prototype, pemetaan kebutuhan, dokumentasi, dan hasil review tersedia. Masalah menu ponsel dan kontras avatar telah diperbaiki serta lulus regresi teknis. Reviewer telah mengonfirmasi lingkungan pengujian, simulasi lebar 360/390 px, ketersediaan screenshot, dan penilaian bahwa tulisan cukup terbaca.

Penyempurnaan tampilan dilanjutkan pada tahap frontend. Temuan yang menghalangi penggunaan tetap perlu ditangani dan dicatat pada tahap yang relevan.

| Data penerimaan | Keadaan aktual |
| --- | --- |
| Review awal pengguna | Nicy Putra Pratama; Jumat, 16 Oktober 2026; http://localhost:8000. |
| Pembaruan dokumentasi | 18 Oktober 2026. |
| Review teknis eksternal | Audit 18 Oktober 2026; Linux/Chromium 153.0.8010.0; identitas personal auditor tidak dicantumkan. |
| Lingkungan reviewer | Laptop Windows 11 dengan Google Chrome; versi Chrome belum dicatat. |
| Pemeriksaan responsivitas reviewer | Simulasi viewport melalui Chrome DevTools pada lebar 360 px dan 390 px. |
| Bukti visual reviewer | Screenshot dinyatakan tersedia pada folder `bukti-review/`; rujukan berkas per kasus belum dicantumkan. |
| Pengalaman penggunaan | Tulisan dinilai cukup terbaca oleh reviewer; penyempurnaan visual dilanjutkan pada implementasi frontend. |
| Kontras avatar | Perhitungan teknis 12,79:1; hasil pembacaan ulang melalui browser belum dicatat. |
| Persetujuan kelompok | Desain disepakati sebagai acuan implementasi setelah audit, berdasarkan konfirmasi penanggung jawab. |
| Keputusan review | Diterima sebagai acuan desain; kelengkapan bukti penutupan masih ditindaklanjuti. |
| Status card | In Review selama rincian bukti dan commit pembaruan belum dilengkapi. |
| Commit sebelumnya | Berkas sebelumnya sudah di-push berdasarkan keterangan reviewer. |
| Commit tambahan gambar dan dokumentasi | Belum di-push saat pembaruan catatan ini. |

Persetujuan desain telah dicatat. Penutupan akhir mengikuti kelengkapan rujukan screenshot, rincian lingkungan yang belum tercatat, hasil kontras browser, dan tautan commit pembaruan.