# Audit SILAR — SLR_07 dan SLR_08

Tanggal audit: 18 Oktober 2026. Audit terhadap paket yang tersedia; tidak mengubah kode sumber, dokumen asal, atau status Kanban.

Revisi lingkup berdasarkan klarifikasi pemilik proyek: dua commit pada SLR_08 digunakan untuk melacak pengerjaan. Pemeriksaan dan pencocokan kedua commit tersebut dikecualikan dari temuan audit serta syarat Done SLR_08.

## Keputusan

| Card | Penilaian hasil pekerjaan | Rekomendasi status saat ini |
| --- | --- | --- |
| SLR_07 — UI/UX dan prototype | Sumber desain, prototype, dokumentasi, pemetaan, dan pengujian tersedia. Ditemukan masalah menu ponsel yang menutupi formulir setelah navigasi. Bukti penerimaan kelompok/perangkat sasaran belum lengkap dalam paket. | **Tetap In Review.** Perbaiki menu, uji ulang kasusnya, lalu lengkapi review dan bukti commit. |
| SLR_08 — fondasi backend/database | Implementasi fondasi tersedia dan pemeriksaan statis lulus. Paket menyertakan 73 hasil test lulus serta 9 pemeriksaan instalasi/HTTP; pengujian database belum dapat diulang dalam audit ini. Catatan penerimaan kelompok pada dokumen penyerahan belum lengkap. | **In Review untuk finalisasi bukti.** Layak menuju Done setelah bukti pengujian pada lingkungan kelompok dan penerimaan tahap fondasi dilengkapi. |

Pekerjaan tidak perlu diulang dari awal. Jika pengujian dan penerimaan kelompok sudah dilakukan di luar paket ini, cukup lengkapi bukti aktualnya. Ketidaktersediaan bukti dalam ZIP tidak berarti kegiatan tersebut pasti belum dilakukan.

Done berlaku untuk lingkup tahap. SLR_07 tidak harus menjadi frontend produksi, dan SLR_08 tidak harus menunggu pipeline AI atau seluruh endpoint bisnis. Integrasi frontend, fitur laporan, model, dan penerimaan lintas fitur tetap mengikuti SLR_09–SLR_15. Dasar: Pemetaan Fitur Final SILAR 1.0, Keputusan Pemetaan butir 4 dan Aturan Penyelarasan Kanban.

## Sumber dan metode

- `SLR_07_UIUX_SILAR_Siap_Dipindahkan.zip` — sumber HTML/CSS/JavaScript, dokumentasi UI/UX, hasil review, dan skrip pemeriksaan.
- `SLR_08_Backend_SILAR.zip` — kode Django/DRF, models, migration, layanan akun/izin/audit, dokumentasi, OpenAPI, bukti pengujian, serta salinan PRD 0.5 dan Acuan Teknis 0.3.
- Catatan card 07–08 pada `Pasted markdown(3).md`. Dua commit SLR_08 merupakan catatan pelacakan pengerjaan dan dikecualikan dari penilaian audit.

Paket diekstrak terpisah dan tidak dimodifikasi. Pemeriksaan browser memakai Chromium 153.0.8010.0 pada Linux; berkas prototype yang sama disajikan melalui intersepsi permintaan browser. Ini memeriksa rendering dan interaksi browser, tanpa menghubungkan API atau layanan eksternal. Ukuran layar disimulasikan; hasilnya bukan pengujian fisik Android maupun Chrome/Edge Windows.

## Pemeriksaan ulang SLR_07

| Pemeriksaan | Hasil audit |
| --- | --- |
| `node docs/uiux/tools/check.mjs` | **42/42 lulus.** |
| `node docs/uiux/tools/review-check.mjs` | **15/15 lulus.** |
| Navigasi dan tata letak | 112 kombinasi halaman/peran/viewport: masing-masing 28 pada 360×800, 390×844, 768×1024, dan 1366×768. Mencakup 18 kode halaman navigasi yang berbeda, bukan 112 layar unik. Tidak ditemukan luapan horizontal dokumen atau kontrol utama yang melewati lebar viewport pada kombinasi tersebut. |
| Alur browser | **7/7 lulus**, dirinci di bawah. |
| Error JavaScript pada pemeriksaan browser | Tidak ditemukan. |
| Pemeriksaan aksesibilitas otomatis | 16 pemindaian pada beberapa halaman/peran desktop dan ponsel; satu temuan unik kontras avatar pada desktop. Pemeriksaan ini tidak menyatakan seluruh antarmuka telah memenuhi standar aksesibilitas. |
| Perangkat fisik dan penerimaan pengguna | Bukti aktual belum terdapat dalam paket. |

Tujuh alur yang diuji melalui antarmuka browser:

1. Password salah ditolak dan halaman masuk dipertahankan.
2. Kredensial fixture yang benar membuka daftar laporan.
3. OTP kedaluwarsa ditolak; akun yang belum diverifikasi tetap tidak dapat masuk. Pengujian mengikuti tautan pada Email contoh.
4. Reporter menyelesaikan contoh draft → analisis → konfirmasi → submit eksplisit pada lebar 390 px.
5. Dialog pemeriksaan dapat dibuka dan ditutup melalui Escape.
6. Tab dan Shift+Tab berputar di dalam dialog pemeriksaan setelah fokus awal selesai dipasang.
7. Operator mengklaim, mereview, menentukan PREPARE, membuat kandidat, memeriksa sanitasi, menyetujui, menerbitkan, memeriksa hasil publik, dan menutup laporan. Persetujuan ditahan sebelum sanitasi; setelah CLOSED tindakan penutupan dinonaktifkan.

### A07-01 — Menu ponsel tetap terbuka setelah memilih Buat Laporan

**Prioritas: perlu diperbaiki sebelum Done.**

- Reproduksi: gunakan lebar 390 atau 360 px → Reporter → buka navigasi → pilih **Buat Laporan**.
- Aktual: halaman RP02 terbuka, tetapi sidebar beserta overlay tetap menutupi formulir. Tombol pembuka navigasi juga berada di balik sidebar. Pengguna harus menutup overlay atau menekan Escape untuk melanjutkan.
- Harapan: pemilihan tujuan menutup menu sehingga formulir langsung dapat digunakan.
- Lokasi: `docs/uiux/prototype/app.mjs`, handler klik, cabang `a === 'new-report'` pada baris 60. Cabang tersebut belum mengatur `menuOpen=false`, sedangkan cabang navigasi biasa sudah melakukannya.
- Perbaikan yang disarankan: tutup menu pada cabang `new-report`; uji ulang saat membuka draft yang sudah ada dan saat membuat draft baru. Periksa pula perilaku setelah beralih ukuran layar.
- Kaitan: NFR06 / AC-N06 dan U07-16.

### A07-02 — Kontras teks avatar desktop sedikit di bawah ambang pemeriksaan

**Prioritas: perbaikan kecil.**

Pemeriksaan otomatis mendeteksi teks `.user-avatar` berukuran 12 px dengan warna `#64727a` pada latar `#edf1f2`, rasio sekitar **4,36:1**. Ambang yang digunakan alat untuk teks kecil ialah 4,5:1. Temuan yang sama berulang pada halaman yang memakai sidebar; bukan delapan cacat yang berbeda. Gelapkan warna teks avatar, misalnya menggunakan warna teks utama, lalu periksa kembali. Lokasi: `docs/uiux/prototype/styles.css` dan pewarisan warna dari sidebar.

### A07-03 — Finalisasi review belum tercatat lengkap

`docs/uiux/review-checklist.md`, `review-next-steps.md`, dan `submission.md` masih menyatakan bukti perangkat/usability, keputusan kelompok, serta commit repository kelompok perlu dilengkapi. Hasil audit otomatis ini dapat ditambahkan sebagai bukti teknis, tetapi tidak menggantikan keputusan penerimaan kelompok atau pengalaman penggunaan pada perangkat sasaran.

## Pemeriksaan ulang SLR_08

| Pemeriksaan | Hasil audit |
| --- | --- |
| Instalasi versi dependency pada requirements | Berhasil. |
| Pemeriksaan kompatibilitas dependency | Lulus; tidak ada dependency rusak. |
| Parsing seluruh sumber Python | Lulus. |
| `manage.py check` | Lulus, 0 masalah. |
| `makemigrations --check --dry-run` | Tidak ada perubahan model yang memerlukan migration baru. Pemeriksaan riwayat migration pada database tidak dapat dikonfirmasi karena database audit tidak tersedia. |
| Integritas manifest paket | **68/68 berkas cocok** ukuran dan SHA-256. |
| Inventaris OpenAPI dan URL Django | **16 path cocok**, setelah penyamaan penulisan parameter path. |
| Inventaris test | **73 nama test dalam kode cocok dengan 73 kasus pada laporan test bawaan.** |
| Pengujian database pada audit ini | Terhalang sebelum skenario dijalankan karena koneksi PostgreSQL tidak tersedia. Tidak ada hasil eksekusi ulang 73 test yang diklaim. |
| Bukti runtime bawaan paket | `tests.json` mencatat 73 lulus; `http-smoke-result.json` mencatat 9 pemeriksaan lulus. Keduanya merupakan hasil yang disertakan pada paket. |

Inspeksi kode menemukan komponen fondasi yang sesuai lingkup card: Custom User UUID, email dinormalisasi, OTP terikat purpose, validator password, JWT dengan auth_version, rotasi/blacklist refresh, CSRF pada auth POST, pembacaan izin aktif, pembatasan akses pemilik/assignment, storage privat, helper revision/idempotency, pencatatan audit, dan migration/constraint integritas. Pemeriksaan statis ini tidak menggantikan verifikasi transaksi dan constraint pada database yang berjalan.

Lingkungan audit dapat memasang dependency dan binary PostgreSQL 16, tetapi pembatasan identitas proses mencegah menjalankan server sebagai akun sistem non-root. Mekanisme pemeriksaan PostgreSQL tidak diubah. Karena itu, percobaan test berhenti pada persiapan database dan tidak diperlakukan sebagai kegagalan 73 skenario aplikasi.

### A08-01 — Penerimaan tahap fondasi belum tercatat lengkap

`docs/backend/penyerahan.md` masih mengosongkan reviewer dan penerimaan kelompok. Temuan ini terbatas pada dokumentasi penerimaan tahap fondasi.

Tindak lanjut: catat reviewer, tanggal review, serta keputusan penerimaan kelompok. Jika review sudah dilakukan di luar paket, cukup tautkan atau lampirkan bukti aktualnya.

### A08-02 — Verifikasi pada lingkungan kelompok perlu ditautkan

`docs/backend/hasil-verifikasi.md` mencatat bahwa hasil lama memakai PostgreSQL 16.12 pada host pengembangan dengan penyesuaian pemeriksaan UID root, serta meminta pengujian ulang pada PostgreSQL 16 standar dan perangkat kelompok. Bukti tersebut belum tercakup dalam ZIP yang diaudit.

Jika pengujian pada komputer kelompok sudah dilakukan, lampirkan hasilnya, versi Python/PostgreSQL, tanggal, dan identitas paket yang diuji. Jika belum, jalankan setup, migration, serta `UJI_BACKEND.bat` pada PostgreSQL 16 standar. Penerimaan fondasi tidak perlu menunggu penyelesaian seluruh layar Vue atau layanan AI pada card berikutnya.

## Syarat penutupan yang disarankan

| Card | Langkah minimum untuk menutup temuan |
| --- | --- |
| SLR_07 | Perbaiki menu ponsel dan uji ulang; rapikan kontras avatar; catat pemeriksaan perangkat/usability serta keputusan kelompok; tautkan commit final ke card. |
| SLR_08 | Tautkan hasil pengujian pada PostgreSQL 16 standar milik kelompok; isi reviewer, tanggal review, dan penerimaan tahap fondasi. |

Setelah bukti tersebut tersedia dan temuan diselesaikan, masing-masing card dapat dipindahkan ke Done sesuai lingkupnya. Bukti integrasi menyeluruh tetap dikumpulkan pada SLR_15. Audit ini tidak memindahkan card secara otomatis.

## Identitas paket yang diaudit

| Paket | SHA-256 |
| --- | --- |
| SLR_07_UIUX_SILAR_Siap_Dipindahkan.zip | `4a829602bf3d615679420e52ab5200b9916271191c4f4b3d86541c963fae1427` |
| SLR_08_Backend_SILAR.zip | `e604b09c398d95a7e66680ccf519f6580c5e6666814ebffacc29fb6ecb23faf9` |

Gunakan identitas ini untuk membedakan paket yang diaudit dari revisi berikutnya. Screenshot pemeriksaan hanya digunakan selama audit; laporan ini tidak menyertakan screenshot akun atau data pribadi.
