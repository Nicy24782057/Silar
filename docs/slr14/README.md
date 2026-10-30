# SLR14 — publikasi dan antarmuka SILAR

**Revisi terkini — alur Operator:** review tersimpan otomatis membuka Tindak
Lanjut. Pilihan publikasi langsung menampilkan formulir/pratinjau, dengan dua
aksi utama Konfirmasi isi publikasi → Publikasikan sekarang. Baca
[ALUR_OPERATOR_20261030.md](ALUR_OPERATOR_20261030.md).

**Revisi Reporter/notifikasi:** notifikasi Admin dirapikan, penanda tahap draft kembali ke
tampilan acuan, dan Periksa hasil otomatis terbuka sesudah analisis tersimpan.
Baca [REVISI_NOTIFIKASI_DAN_HASIL_20261030.md](REVISI_NOTIFIKASI_DAN_HASIL_20261030.md).

Revisi terbaru menambahkan transisi login seluruh kerangka, progres tahapan AI,
urutan laporan Lanjut/Kembali, serta halaman setelah terkirim. Baca
[ALUR_DAN_PROGRES_20261030.md](ALUR_DAN_PROGRES_20261030.md).

Audit lanjutan 30 Oktober 2026 memperbaiki panel login pada layar pendek,
melengkapi desain dan dialog Admin/Operator, keadaan pembacaan API, transisi
halaman, serta penghapusan draft milik Reporter sendiri. Baca
[AUDIT_MENYELURUH_20261030.md](AUDIT_MENYELURUH_20261030.md). Pemetaan 30 SVG
ada pada [REVISI_UI_20261030.md](REVISI_UI_20261030.md). Paket bersifat kumulatif.

Perubahan disiapkan terhadap `main` pada commit
`1af8ac6f098b1a50fc83b4c74f8b0b4bbaaf73cd` (SLR13).
Branch kerja: `codex/slr14-approved-ui`. Belum di-push atau dideploy.
Keputusan desain dan pemetaan data ada di
[KEPUTUSAN_DAN_CAKUPAN.md](KEPUTUSAN_DAN_CAKUPAN.md).

## Memasang paket perubahan

1. Hentikan frontend/backend, lalu buat branch pada clone Silar yang sudah
   menjalankan SLR13. Pertahankan perubahan lokal milik tim.
2. Ekstrak paket ke folder sementara. Gabungkan `code/` dan `docs/slr14/`
   mengikuti path yang sama pada clone; timpa hanya berkas yang disertakan.
   Jangan mengganti atau menghapus seluruh folder proyek. Konfigurasi lokal,
   database, model AI, bukti dan akun tidak disertakan dalam paket.
3. Jalankan migration `0005_report_soft_deletion`, pemeriksaan dan mulai ulang
   kedua server. Dependensi aplikasi tidak berubah. Database tetap PostgreSQL 16.

Terminal PowerShell pada `code/backend` dengan konfigurasi SLR13 yang sudah berjalan:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe verify_slr14.py
.\.venv\Scripts\python.exe manage.py runserver localhost:8001
```

Terminal lain pada `code/frontend`:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run dev
```

Jika dependensi belum terpasang, gunakan `npm.cmd ci` terlebih dahulu.
Panduan instalasi awal tetap tersedia di `PANDUAN_RUNNING.md` pada root clone.
PWA yang sudah terpasang perlu menerima build baru; gunakan pembaruan pada
**Aplikasi & Koneksi** jika tersedia, kemudian buka kembali aplikasi.

## Mencoba antarmuka

- `http://localhost:5173/`: landing page.
- `http://localhost:5173/public`: Portal Publik, tanpa akun.
- `/login` dan `/register`: akun; registrasi publik hanya untuk Reporter.
- `/reports/{id}/sent`: konfirmasi pengiriman terverifikasi, dengan tautan ke
  Laporan Saya. Halaman tidak menampilkan sukses hanya karena URL dibuka.
- Desktop/tablet akun memakai dua panel. Pada lebar sampai 640 px,
  hanya formulir kanan ditampilkan. Tidak ada banner identitas tambahan.
- Portal memakai 5 kolom di atas 1100 px, 2 kolom pada tablet, dan 1 kolom
  sampai 640 px. Ukuran halaman selalu 10 kartu; pencarian/filter kembali
  ke halaman pertama. Urutan publikasi mengikuti backend.
- Sidebar aplikasi dapat dibuka di layar kecil. Tabel dapat digeser mendatar.
- Nama, angka, ID dan informasi pada halaman aplikasi berasal dari API.
  Gambar ilustrasi tetap merupakan ilustrasi, bukan laporan nyata.

Palet dan font Inter mengikuti sumber desain. Logo menggunakan simbol dan mask
asli tanpa potongan raster berlatar. Panel identitas akun mempertahankan
gradasi, pola dan ilustrasi SVG asli. Formulir memakai kontrol HTML dengan warna
judul/label eksplisit pada kedua tema. Semua aset visual/font dilayani lokal.

## Mencoba publikasi

Gunakan Operator aktif dan terverifikasi yang memiliki `view_assigned_report`
serta `publish_report`, dan merupakan penanggung jawab saat ini. Label Admin
sendiri tidak memberi kewenangan Operator.

1. Buka **Penanganan Saya → Detail Laporan → Review**. Pilih hasil dan simpan
   review beserta alasan; hasil tidak dipilih otomatis.
2. Untuk review **VALID** atas versi resmi, buka **Keputusan**, pilih
   **Siapkan publikasi**, isi alasan lalu simpan. Tindakan ini belum membuat kandidat.
3. Pada panel **Informasi untuk Portal Publik**, siapkan isi kandidat. Periksa
   semua informasi, hilangkan informasi privat, lalu buka pratinjau. Kategori
   mengikuti versi resmi. Waktu pasti boleh kosong; bila diisi, sertakan zona waktu.
4. Simpan kandidat, setujui versi tersimpan melalui konfirmasi, kemudian
   terbitkan melalui tindakan terpisah. Kandidat dan versi yang baru disetujui
   belum dapat dibaca melalui API publik.
5. Perbaikan kandidat tersimpan memakai pembatalan beralasan, keputusan
   Siapkan publikasi kembali, dan kandidat pengganti. Parent mengikuti versi
   terakhir, termasuk versi yang dibatalkan. Isi versi tidak ditimpa.
6. Versi terbit lama tetap terlihat selama penggantinya disiapkan/disetujui.
   Setelah pengganti terbit, pointer publik berpindah ke pengganti. Penarikan
   versi terbit tidak tersedia. Review dikunci setelah publikasi pertama.
7. Respons tindakan yang terputus menahan tindakan baru dan menyediakan
   **Periksa hasil tindakan**, memakai kunci serta payload permintaan yang sama.
   Laporan tertutup tidak menerima perubahan publikasi baru.

## Menghapus laporan yang belum dikirim

Pada **Laporan Saya** atau detail draft, pilih **Hapus** dan konfirmasi.
Hanya laporan milik akun tersebut yang belum dikirim yang dapat dihapus.
Bukti dan audit tetap tersimpan; laporan hilang dari daftar dan tidak dapat
dilanjutkan. Jika analisis masih berjalan/belum pasti, selesaikan pemeriksaan
keadaannya dahulu. Detail kontrak, keamanan, replay dan migration ada pada
[API_HAPUS_DRAFT.md](API_HAPUS_DRAFT.md).

## Kontrak yang dipertahankan

Seluruh path berikut berada di bawah `/api/v1/`:

| Metode | Path | Fungsi |
| --- | --- | --- |
| DELETE | `reports/{id}/` | Hapus logis draft sendiri yang belum dikirim; tambahan SLR14 |
| POST | `reports/{id}/publication-decision/` | INTERNAL atau PREPARE |
| POST | `reports/{id}/publication-versions/` | Kandidat baru; `parent_id` wajib, nullable |
| POST | `reports/{id}/publication-versions/{version}/approve/` | Persetujuan kandidat DRAFT |
| POST | `reports/{id}/publication-versions/{version}/publish/` | Penerbitan kandidat APPROVED |
| POST | `reports/{id}/publication-versions/{version}/cancel/` | Pembatalan beralasan |
| GET | `public/reports/` | Daftar versi terbit saat ini |
| GET | `public/reports/{id}/` | Detail informasi publik |

Mutasi privat memerlukan Bearer, `Idempotency-Key` UUID dan `expected_revision`.
Izin dan penugasan terkini diperiksa sebelum replay; perubahan memakai transaksi,
lock laporan, ledger dan audit. Replay terminal dipulihkan sebelum pemeriksaan
revisi/lifecycle. Tidak ada PATCH isi publikasi atau endpoint statistik baru.
URL keputusan workspace SLR13 tetap berfungsi melalui layanan guard yang sama dan mempertahankan respons `report`/`message` bagi klien lama.

PublicReport tepat sembilan field: `id`, `event_type`, `summary`,
`general_location`, `time_text`, `occurred_at`, `general_impact`,
`handling_update`, `published_at`. Proyeksi menggunakan allowlist eksplisit,
termasuk untuk JSON historis. Informasi opsional kosong tidak ditebak.

Parameter daftar publik: `q`, `event_type`, `general_location`, `page`,
`page_size`. Pencarian hanya atas ringkasan, lokasi umum, dampak umum dan
perkembangan penanganan; filter digabung dengan AND. Urutan tetap
`published_at` menurun, lalu ID laporan. Ringkasan jumlah menggunakan `count`
dari daftar dalam lingkup terkait, bukan menghitung kartu pada halaman aktif.

Pembacaan Portal Publik menghilangkan Bearer/cookie dan tidak memulihkan sesi.
Cache PWA hanya berisi antarmuka/aset. Token, data laporan, media privat dan
respons API tidak dimasukkan ke cache atau penyimpanan browser.

Hasil pengujian dan batas verifikasi tersedia di
[HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md).

Petunjuk perintah verifikasi PostgreSQL 16 dan laporan hasilnya tersedia di
[UJI_POSTGRESQL16.md](UJI_POSTGRESQL16.md). Perintah menolak hasil skip sebagai
penerimaan penuh dan memakai database uji baru yang terpisah dari data aplikasi.
