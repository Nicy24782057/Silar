# Hasil Review dan Perbaikan UI UX SILAR SLR_07

Review pengguna U07-01–U07-10 sudah dicatat. Pemeriksaan teknis tambahan telah dilakukan untuk U07-11–U07-15, uji ulang teknis akun, dan keberadaan konten awareness pada U07-16. Sebanyak 42 pemeriksaan dasar dan 15 pemeriksaan tambahan lulus. Temuan login dan urutan publikasi portal telah diperbaiki. Pemeriksaan visual perangkat serta penerimaan kelompok masih perlu dicatat.

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

## Rekap hasil

| ID | Kasus | Hasil aktual dari penguji | Status | Bukti dan tindak lanjut |
| --- | --- | --- | --- | --- |
| U07-01 | Akun, OTP, profil, pemulihan | Formulir kosong meminta pengisian; password harus cocok dan minimal delapan karakter; pendaftaran/OTP benar berhasil; OTP salah ditolak; waktu kirim ulang terlihat; lupa password, profil dan field terkunci dinyatakan berhasil. Password salah dilaporkan tetap dapat masuk. Cara uji OTP kedaluwarsa belum dipahami. | Sebagian; perlu uji ulang | R07-01/R07-02. Perbaikan simulasi login lulus uji teknis; uji ulang pengguna belum dilaporkan. |
| U07-02 | Tujuh kombinasi kanal | Notifikasi muncul ketika sumber belum ditambahkan; langkah kombinasi masukan, penyimpanan teks/audio/gambar, dan pemeriksaan berikutnya dinyatakan berhasil. | Lulus berdasarkan laporan | Rincian tujuh kombinasi dan screenshot belum dicatat terpisah. Permintaan sumber tidak ditafsirkan bahwa audio dan gambar keduanya wajib. |
| U07-03 | Draft, bukti dan bundle | Langkah 1–8 dinyatakan berhasil: penyimpanan, pilihan bukti, membuka kembali draft, dan pemeriksaan perubahan sumber. | Lulus berdasarkan laporan | Tidak ditafsirkan bahwa perubahan belum tersimpan boleh dianalisis. Screenshot belum dilampirkan. |
| U07-04 | Analisis, konfirmasi, submit | Penguji menyatakan seluruh pemeriksaan berhasil. | Lulus berdasarkan laporan | ID laporan dan bukti alur belum dicatat. |
| U07-05 | Koreksi dan versi | Penguji menyatakan seluruh pemeriksaan berhasil. | Lulus berdasarkan laporan | Mendukung alur koreksi pada paket yang diuji; rincian versi/screenshot belum dicatat. |
| U07-06 | NON_EVENT dan uncertain | Penguji menyatakan seluruh pemeriksaan berhasil. Pada NON_EVENT, AI belum mengenali narasi sebagai laporan kejadian dalam cakupan. | Lulus berdasarkan laporan | NON_EVENT bukan bukti tidak ada kejadian atau pelapor berbohong; bukti uncertain belum dilampirkan. |
| U07-07 | Proses dan pemulihan | Penguji menyatakan tes berhasil; RUNNING dan UNKNOWN sama-sama tetap pada halaman analisis. | Lulus berdasarkan laporan | Menunggu sesuai simulasi; perbedaan makna dan pemulihan dijelaskan pada review-next-steps.md. Detail pemulihan belum dicatat terpisah. |
| U07-08 | Kesalahan dan keadaan khusus | Seluruh kasus dinyatakan telah dicoba dan sesuai keputusan/guard yang dikunci, termasuk penolakan yang memang diharapkan. | Lulus berdasarkan laporan | Keberhasilan tidak berarti semua tindakan langsung diterima. Bukti tiap keadaan belum dilampirkan. |
| U07-09 | Antrean dan klaim | Pengujian dinyatakan berhasil; setelah diambil, laporan tidak tersedia bagi Operator B. | Lulus berdasarkan laporan | Mendukung satu penanggung jawab dalam simulasi; bukan bukti concurrency server. |
| U07-10 | Review dan tindak lanjut | Seluruh tes dinyatakan berhasil dan sesuai hasil pemeriksaan. | Lulus berdasarkan laporan | Rincian outcome/tindak lanjut dan screenshot belum dicatat terpisah. |
| U07-11 | Kandidat dan publikasi | PREPARE/kandidat/approval tidak langsung terbit; checklist sanitasi wajib; versi yang disetujui baru muncul setelah publish. Field privat ditolak. Pembatalan kandidat DRAFT/APPROVED mempertahankan versi terbit. Review sesudah publikasi ditolak. | Lulus teknis; manual belum dilaporkan | RT-02/RT-03 pada bukti-review/hasil-pemeriksaan-teknis.json. |
| U07-12 | Penutupan | Close ditahan sebelum syarat lengkap. Jalur INTERNAL dan PUBLISHED dapat ditutup dengan catatan; review, tindak lanjut, publikasi dan assignment sesudah CLOSED ditolak. Riwayat tetap terbaca. | Lulus teknis; manual belum dilaporkan | RT-04/RT-05. |
| U07-13 | Administrasi | Akun baru belum aktif dan tidak menerima password Admin; resend hanya Admin. Aktivasi fixture tersedia. Assignment wajib alasan, akses lama dicabut, pencabutan izin/nonaktif berlaku berikutnya. Draft/isi privat dibatasi, audit tidak merender narasi, monitoring tidak menjalankan model. | Lulus teknis; manual belum dilaporkan | RT-06–RT-08. Aktivasi hanya simulasi akun contoh, bukan layanan email/OTP nyata. |
| U07-14 | Portal Publik | Pencarian empat field publik, kapitalisasi dan filter gabungan sesuai; hasil kosong dijelaskan. Informasi privat tidak terender. Waktu kejadian/publikasi dibedakan. Urutan terbaru diperbaiki dan lulus uji ulang. | Lulus teknis setelah perbaikan; manual belum dilaporkan | RT-09–RT-11; temuan R07-05/T07-04. |
| U07-15 | Notifikasi, offline, PWA | Pemicu notifikasi dan pembatasan penerima sesuai; tandai dibaca bekerja. Notifikasi lama tidak memulihkan akses setelah assignment. Offline menahan operasi; panduan menjelaskan batas PWA. | Lulus teknis; manual belum dilaporkan | RT-12–RT-14. Bukan uji instalasi/cache atau jaringan PWA nyata. |
| U07-16 | Responsivitas, usability, awareness | Keberadaan pesan kategori, kepemilikan bukti, privasi, Gemini, OTP, sanitasi dan pemulihan diperiksa pada proyeksi HTML. Tata letak, keyboard, fokus, kontras dan pemahaman pengguna belum diperiksa melalui browser. | Sebagian teknis; review perangkat/usability terbuka | RT-15 untuk konten. Catat hasil perangkat sasaran dan review kelompok secara manual. |

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
| 7b | Cara mencoba kode kedaluwarsa belum dipahami. | Belum dikonfirmasi |
| 8 | Ada waktu tunggu kirim ulang. | Lulus berdasarkan laporan |
| 9 | Lupa password dinyatakan berhasil. | Lulus berdasarkan laporan |
| 10 | Password salah dilaporkan tetap berhasil login. Perlu dibedakan password salah pada Masuk dari password baru yang sah pada Reset Password. | Temuan R07-01; menunggu uji ulang |
| 11–12 | Profil/keluar dan field email/peran terkunci dinyatakan berhasil. | Lulus berdasarkan laporan |

## Temuan dan tindak lanjut

| ID | Temuan/kebutuhan | Tindakan yang telah dilakukan | Status lanjutan |
| --- | --- | --- | --- |
| R07-01 / T07-03 | Password salah tetap masuk. Inspeksi sumber menemukan login hanya memeriksa isian tidak kosong. | Simulasi mencocokkan email/password akun contoh, menahan akun pendaftaran sebelum verifikasi, dan mengganti password setelah reset yang valid. Pemeriksaan otomatis ditambahkan. | Perbaikan teknis selesai; uji ulang manual penguji belum dilaporkan. Belum ditutup sebagai Lulus manual. |
| R07-02 | Cara uji OTP kedaluwarsa belum dipahami. | Panduan menggunakan Uji keadaan → OTP kedaluwarsa tersedia pada review-next-steps.md. Guard lulus uji otomatis. | Penguji mencoba 123456 pada keadaan kedaluwarsa dan mencatat pesan/halaman berikutnya. |
| R07-03 | RUNNING/UNKNOWN sama-sama tampak menunggu. | Dicatat sebagai perilaku simulasi yang diharapkan; perbedaan makna, Periksa Status dan pemulihan dijelaskan. | Tambahkan bukti pesan/pemulihan saat melengkapi rincian review. Tidak dicatat sebagai layanan nyata yang macet. |
| R07-04 | Hasil manual U07-11–U07-16, metadata perangkat dan penerimaan kelompok belum disampaikan. | Lima skenario diperiksa secara teknis, konten awareness diperiksa sebagian; bukti JSON disertakan. | Lengkapi pemeriksaan browser/kelompok tanpa mengganti hasil teknis menjadi hasil manual. |
| R07-05 / T07-04 | Portal membalik urutan array laporan sehingga publikasi lama muncul sebelum publikasi baru. | Simulasi menyimpan urutan penerbitan setiap versi dan mengurutkan terbaru dahulu. | RT-10 gagal sebelum perbaikan dan lulus sesudahnya; uji ulang tampilan browser masih terbuka. |

## Pemeriksaan teknis tambahan

Pemeriksaan dilakukan pada 16 Oktober 2026 oleh penyusun menggunakan Node.js, model simulasi, handler klik dan proyeksi HTML dengan stub DOM. Ini bukan pemeriksaan browser atau pengujian backend. Hasil tiap uji, waktu eksekusi, versi Node dan hash empat aset tersimpan pada `bukti-review/hasil-pemeriksaan-teknis.json`.

- Pemeriksaan dasar: 42 lulus melalui `tools/check.mjs`.
- Pemeriksaan tambahan: 15 lulus melalui `tools/review-check.mjs`.
- Uji ulang teknis R07-01/R07-02: password salah ditolak dan OTP kedaluwarsa tidak mengaktifkan akun (RT-01).
- Publikasi sampai offline/PWA: RT-02–RT-14, sesuai lingkup tiap baris rekap.
- Digital Awareness: RT-15 hanya memeriksa keberadaan konten, bukan pemahaman/keterbacaan pengguna.

## Keputusan saat ini

Sumber desain, prototype, pemetaan kebutuhan, dokumentasi penempatan dan hasil review tersedia untuk dipindahkan ke `docs/uiux/`. Review pengguna dipertahankan, perbaikan teknis dicatat, dan pemeriksaan tambahan sudah diisi dengan hasil eksekusi nyata.

Penerimaan akhir kelompok belum dicatat. Finalisasi manual meliputi uji ulang login/OTP pada browser, pemeriksaan U07-16 pada perangkat sasaran dan penelusuran/review kelompok atas alur yang sebelumnya hanya diperiksa secara teknis. Tambahkan lingkungan, bukti relevan serta keputusan kelompok setelah dilakukan. Status card tetap review lanjutan sampai kriteria tersebut terpenuhi; tidak ada hasil manual atau persetujuan yang diasumsikan.

Commit GitHub SILAR kelompok diisi setelah kelompok melakukan commit/push yang sebenarnya. Riwayat kegagalan awal tetap dipertahankan sebagai bukti perbaikan.
