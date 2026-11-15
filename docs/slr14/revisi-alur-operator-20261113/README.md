# SLR14 — perbaikan alur Operator, 13 November 2026

Pengelolaan laporan sekarang mengikuti **Pemeriksaan → Keputusan penayangan → Penanganan & penyelesaian**. Sebelumnya, tindak lanjut tampil sebelum keputusan, review yang sudah tersimpan masih terasa belum selesai, dan alasan wajib publikasi berada jauh dari tombol konfirmasi. Revisi ini memperjelas langkah berikutnya tanpa menambah status atau mengubah kontrak backend.

## Perilaku yang disepakati

| Tindakan | Hasil pada antarmuka |
| --- | --- |
| Simpan review | Setelah review yang tepat terbaca tersimpan, otomatis buka Keputusan penayangan dan tampilkan bukti bahwa review telah tersimpan. |
| Tetap internal | Isi alasan internal, lalu Simpan keputusan & lanjut. Setelah keputusan terbaca tersimpan, otomatis buka Penanganan & penyelesaian. |
| Tinjau untuk publikasi | Langsung buka formulir dan pratinjau; alasan publikasi berada dalam formulir yang sama. |
| Isian publikasi belum lengkap | Tampilkan syarat yang kurang dekat tombol. Tautan syarat memfokuskan kolom atau centang yang dimaksud. Waktu pasti boleh kosong; jika diisi harus menyertakan zona waktu. |
| Konfirmasi isi publikasi | Simpan keputusan, versi dan persetujuan terhadap isi yang diperiksa. Informasi belum terbit. |
| Publikasikan sekarang | Perlu centang versi tersimpan dan tindakan eksplisit. Setelah versi yang sama terbaca terbit, otomatis buka Penanganan & penyelesaian. |
| Penanganan | Tindak lanjut opsional. Tidak ada catatan tindak lanjut yang dibuat otomatis. |
| Selesaikan penanganan laporan | Periksa syarat penutupan, lalu konfirmasi dengan catatan internal. Tindak lanjut yang sudah ada harus diselesaikan atau dibatalkan. |
| Respons terputus | Tahan tindakan baru dan periksa ledger serta keadaan tersimpan. Perpindahan otomatis hanya setelah hasil yang sesuai terverifikasi. Pemulihan tidak otomatis mengirim mutasi berikutnya. |

Tahap kedua dan ketiga tetap mengikuti syarat review yang sudah ada. Tahap Penanganan yang dapat dibuka bukan tanda bahwa tindak lanjut wajib dibuat. Tombol penutupan tetap mengikuti seluruh syarat dari backend. Operator dapat kembali membaca bagian sebelumnya; mutasi tetap diperiksa terhadap izin, penugasan, versi dan keadaan laporan terkini.

Keputusan internal tidak otomatis menutup laporan. Sebelum tindakan penutupan sebenarnya, status penanganan tetap memakai status yang sudah ada, termasuk `IN_REVIEW`. Revisi ini tidak mengubah enum, label status backend, endpoint, dependency atau migration.

## Notifikasi penutupan untuk Reporter

Backend yang sudah ada mengirim satu notifikasi aplikasi `REPORT_CLOSED` setelah penutupan berhasil, dengan pesan **Penanganan laporan telah ditutup.** Reporter dapat mengetahui bahwa laporan ditutup, tetapi pesan itu tidak memuat alasan.

`closure_note` adalah catatan internal petugas. Respons detail laporan milik Reporter maupun notifikasinya tidak memuat catatan tersebut. Antarmuka Operator sekarang menamai kolom itu **Catatan penutupan internal** agar kegunaannya jelas. Revisi ini tidak membuka catatan lama atau menambah alasan yang dapat dilihat Reporter. Jika alasan penutupan perlu ditampilkan kelak, isi, kewenangan dan kontrak datanya perlu disepakati tersendiri.

## Hasil verifikasi

| Pemeriksaan | Hasil |
| --- | --- |
| Tes frontend | 114 lulus, 0 gagal/skip; [log](bukti/frontend-tests.txt) |
| Build produksi | Berhasil; [log](bukti/frontend-build.txt) |
| Tes backend yang relevan | 35 lulus pada PostgreSQL 16; [log](bukti/backend-tests.txt) |
| Browser Chromium dengan animasi aktif | 64 keadaan halaman/ukuran/tema, 12 pemeriksaan alur, 0 page error; [hasil](bukti/browser-result.json) |
| Patch pemasangan | Diperiksa terhadap isi paket sebelumnya, diterapkan pada salinan sementara, lalu hasilnya dibandingkan per berkas. |
| Isi ZIP | CRC dan kesamaan berkas diperiksa; daftar hash tersedia di `DAFTAR_PERUBAHAN.json`. |

Matriks browser memeriksa lebar 1440, 1100, 820, 640, 390 dan 320 piksel pada mode terang/gelap. Pemeriksaan meliputi Pemeriksaan, Keputusan, formulir/pratinjau publikasi, Penanganan dan Riwayat tanpa overflow horizontal. Tampilan desktop dan ponsel juga ditinjau secara visual melalui tangkapan layar internal; gambar itu tidak disertakan dalam paket.

Alur nyata melalui UI mencakup review menuju Keputusan, konfirmasi yang belum menerbitkan informasi, publikasi eksplisit menuju Penanganan, keputusan internal dengan status tetap `IN_REVIEW`, penutupan tanpa tindak lanjut, tindak lanjut tertunda yang memblokir penutupan, review Tidak valid, laporan terbit/tertutup yang sudah ada, serta notifikasi penutupan dan batas data Reporter/Admin. Dua skenario memutus respons setelah mutasi benar-benar commit: keputusan internal dan publikasi. Keduanya pulih lewat pembacaan hasil tanpa penggandaan mutasi.

Backend berjalan pada database PostgreSQL uji terpisah. Model AI diganti test double hanya untuk menyiapkan laporan uji; tidak ada inferensi model asli atau SMTP eksternal. Kelompok lengkap 152 tes SLR14 dan tes akun/setup dari paket sebelumnya tidak dijalankan ulang untuk revisi frontend ini. Verifikasi ini tidak menyatakan kesamaan piksel dengan ZIP desain asli yang tidak tersedia, pengujian perangkat fisik, atau penerimaan keseluruhan SLR15.

## Memasang paket lanjutan

Paket ini melanjutkan `SILAR_SLR15.zip` (akun/Operator/setup) dan `SILAR_SLR14_revisi_UI_13Nov2026.zip` (kontrol sandi dan landing page) yang telah diterapkan. Nama arsip akun terdahulu tetap dipertahankan sebagai riwayat; implementasi perbaikannya termasuk SLR14.

1. Hentikan frontend. Ekstrak ZIP baru ke folder sementara, lalu gabungkan berkas mengikuti path pada clone Silar. Jangan mengganti seluruh folder proyek.
2. Dari `code/frontend`, jalankan `npm.cmd test` dan `npm.cmd run build`, kemudian `npm.cmd run dev`.
3. Buka ulang aplikasi. Untuk PWA yang terpasang, ambil pembaruan build melalui Aplikasi & Koneksi lalu buka kembali.
4. Gunakan laporan yang berbeda untuk mencoba jalur internal dan publikasi. Pastikan review otomatis menuju Keputusan, alasan publikasi terlihat dekat konfirmasi, dan Penanganan terbuka setelah keputusan/publikasi berhasil.
5. Coba tutup laporan tanpa tindak lanjut, kemudian periksa notifikasi pada akun Reporter pemilik laporan. Catatan penutupan internal tidak ditampilkan kepada Reporter.

Tidak ada pemasangan dependency atau migration tambahan untuk revisi alur ini. Konfigurasi, database, venv dan model lokal yang sudah tersedia tetap dipakai.

Alternatif penyalinan berkas adalah `git apply --check PERUBAHAN_SLR14_OPERATOR.patch`, lalu `git apply PERUBAHAN_SLR14_OPERATOR.patch` dari root clone. Pilih satu cara. Patch menggunakan preimage source paket terdahulu; jika berkas sudah diedit lagi, gabungkan perbedaannya terlebih dahulu. Manifest merekam hash sebelumnya dan hash isi baru. Manifest paket lama tetap mendokumentasikan versi saat paket tersebut dibuat.

Belum ada commit, push, deployment atau perubahan board oleh penyusun. Nama commit lanjutan yang sesuai: `fix(slr14): perjelas alur keputusan dan penyelesaian laporan operator`.
