# Menuntaskan verifikasi PostgreSQL 16

Lanjutan 29 Oktober 2026. Gunakan clone SILAR yang sudah menjalankan SLR13
dan PostgreSQL mayor 16. Perintah ini menguji backend, tanpa menjalankan
inferensi AI atau pengiriman email eksternal.

## Satu perintah pada Windows

Buka terminal di `code/backend`, kemudian jalankan:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py
```

Gunakan venv dan konfigurasi database lokal yang sudah dipakai pada SLR13.
Dependensi backend tidak berubah. Role PostgreSQL untuk pengujian perlu
izin membuat database uji. Perintah tidak memberikan izin atau mengganti
konfigurasi PostgreSQL secara otomatis.

Pada Linux/macOS, gunakan interpreter venv proyek, misalnya:

```bash
./.venv/bin/python verify_slr14.py
```

## Yang diperiksa

1. Koneksi benar-benar memakai PostgreSQL mayor 16. SQLite, mayor lain,
   serta migration core/accounts yang dinonaktifkan ditolak.
2. Database uji baru dibuat dengan nama acak `test_silar_slr14_...`.
   Konfigurasi TEST NAME/MIRROR yang menunjuk ke database aplikasi tidak
   digunakan. Perintah tidak menjalankan migration pada database aplikasi.
3. Migration asli harus memasang trigger laporan, histori, kandidat,
   penugasan, anggota bundle dan ledger. Constraint versi/metadata publikasi
   serta bentuk JSON harus tersedia dan aktif pada database uji.
4. Suite mencakup publikasi SLR14, klaim/ruang kerja SLR13, review Reporter,
   constraint dasar, konkurensi, filter dan guard perintah verifikasi.
   Pada paket ini terdapat 143 tes; dua tes konkurensi publikasi, tiga tes penghapusan, dan tes
   klaim serentak wajib ditemukan.
5. Tidak ada tes yang boleh gagal, error, dilewati atau ditandai expected
   failure. Suite kosong juga tidak dapat menghasilkan status lulus.

Django membersihkan database uji setelah pengujian normal selesai. Bukti uji
dan email pengujian memakai folder sementara. Kunci penandatanganan sementara
hanya berlaku di proses pengujian; berkas konfigurasi dan akun aplikasi
tidak diubah.

## Membaca hasil

| Status | Makna | Exit code |
| --- | --- | --- |
| PASSED | PostgreSQL 16, migration/guard dan seluruh tes selesai tanpa pengecualian | 0 |
| FAILED | Tes gagal, error, dilewati, expected failure, atau tidak ada tes berjalan | 1 |
| BLOCKED | Pengujian belum dapat selesai, misalnya koneksi/izin/dependensi belum siap | 2 |

Laporan JSON tersimpan secara otomatis di
`docs/slr14/hasil-postgresql/verifikasi-....json`. Lokasinya juga tercetak
pada terminal. Laporan memuat versi database, nama database uji, jumlah tes,
status guard dan nama tes yang gagal/dilewati, tanpa password, token atau DSN.

Untuk menentukan lokasi laporan sendiri:

```powershell
.\.venv\Scripts\python.exe verify_slr14.py --report hasil-slr14.json
```

Setelah menjalankannya, laporan JSON tersebut dapat dibagikan untuk
menentukan apakah SLR14 sudah memenuhi penerimaan native PostgreSQL 16.

## Hasil di lingkungan pengerjaan

Guard perintah sudah diuji, termasuk penolakan SQLite, mayor PostgreSQL
yang salah, migration nonaktif, tes wajib yang hilang, hasil skip, suite
kosong dan TEST NAME/MIRROR yang menunjuk data aplikasi.

94 tes komponen berhasil dan 5 tes khusus PostgreSQL dilewati pada suite
komponen. Percobaan perintah native menemukan 143 tes, lalu berhenti dengan
status BLOCKED karena tidak ada server PostgreSQL 16 yang bisa diakses.
Tidak ada database uji yang dibuat pada percobaan tersebut. Ini belum
merupakan hasil lulus untuk transaksi, trigger atau konkurensi PostgreSQL.
