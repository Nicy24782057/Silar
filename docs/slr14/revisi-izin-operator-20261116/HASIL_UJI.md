# Hasil pengujian revisi Operator

16 November 2026. Basis kode: `785a2762a9f7dcbd8ecfb1522165995e6c02b0cd` (`SLR_15 Mutu AI`).
Implementasi revisi ini berada pada branch lokal SLR14 dan belum dipush.

| Pemeriksaan | Hasil |
| --- | --- |
| Backend `accounts core reporting`, PostgreSQL 16 | 268 tes lulus; 0 gagal, 0 skip. |
| Frontend `npm test`, Node 24.22.1 | 123 tes lulus; 0 gagal, 0 skip. |
| Frontend `npm run build` | Berhasil. |
| Django `check` | Tidak ada masalah. |
| Django `makemigrations --check --dry-run` | Tidak ada perubahan schema. |
| Browser Chromium 153.0.8010.0 | 10 kombinasi ukuran/tema dan 7 pemeriksaan alur lulus; tidak ada kesalahan JavaScript halaman. |
| OpenAPI JSON, field request dan tautan dokumen baru | Valid. |
| Patch terhadap basis kode | Diperiksa saat pembuatan ZIP; seluruh isi hasil penerapan dibandingkan dengan berkas revisi. |

Tes backend mencakup paket tetap untuk Operator lama/baru, akun belum aktif,
penonaktifan pada token yang sudah diterbitkan, batas kewenangan Admin,
penugasan/pengalihan, guard status, sanitasi, approval, penerbitan, audit,
notifikasi dan replay. Konfigurasi `permission_ids` dari klien ditolak tanpa
menjalankan perubahan akun lain yang disertakan dalam request tersebut.

Formulir diperiksa pada lebar 1440, 1024, 768, 390 dan 320 piksel, masing-masing
pada tema terang dan gelap. Kolom nama/email tetap di dalam layar; tidak ada
pilihan izin atau kolom jumlah izin. Dialog pada layar pendek dapat digulir.

Pemeriksaan alur browser:

1. Daftar akun tanpa pengaturan/jumlah izin dan tanpa pembacaan katalog yang tidak diperlukan.
2. Riwayat perubahan izin lama tetap terbaca menggunakan label katalog.
3. Pembuatan akun benar-benar hanya mengirim nama dan email, lalu menampilkan status menunggu aktivasi.
4. Aktivasi OTP dan penetapan sandi oleh pemilik pada tampilan HP memberikan tujuh kewenangan.
5. Operator baru mengklaim, mereview, memilih internal, mencatat/menyelesaikan tindak lanjut dan menutup laporan melalui antarmuka HP.
6. Operator lama dengan grant sebagian memperoleh paket lengkap, tetapi ditolak saat membuka laporan milik penanggung jawab lain.
7. Admin dapat menonaktifkan dan mengaktifkan kembali akun tanpa pemilihan izin.

Pengujian memakai database dan akun uji terpisah. OTP diterima melalui kotak
email lokal. Inferensi AI nyata, SMTP eksternal dan deployment server tidak
dijalankan dalam revisi izin ini. Bukti ini tidak menggantikan penerimaan
terintegrasi SLR15 maupun verifikasi deployment SLR16.

Perintah pengulangan pada `code/backend`, dengan PostgreSQL 16 serta `.env`
pengembangan yang sudah disiapkan:

```powershell
.\.venv\Scripts\python.exe manage.py test accounts core reporting --settings=config.test_settings --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Pada `code/frontend`:

```powershell
npm.cmd test
npm.cmd run build
```

Database pengujian memerlukan hak membuat/menghapus database uji pada instance
lokal. Langkah review manual tersedia pada README revisi ini.
