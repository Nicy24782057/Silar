# Hasil verifikasi lokal Windows SLR_08

Tanggal pengujian: **17–18 Oktober 2026**.

Dokumen ini merangkum output terminal dan screenshot yang disampaikan pelaksana pengujian pada komputer Windows lokal. Catatan pengujian lingkungan penyusunan paket tetap tersedia pada [hasil-verifikasi.md](hasil-verifikasi.md); dokumen ini menambahkan bukti lingkungan Windows.

Status: fondasi backend berjalan dan pengujian yang dicatat di bawah berhasil. Commit dan push dibuktikan dengan SHA serta tautan commit aktual pada card SLR_08 setelah pengunggahan.

## Lingkungan

| Komponen | Nilai yang teramati |
| --- | --- |
| OS | Windows, build 10.0.26200.9711 |
| Python | 3.13.15, virtual environment lokal |
| Django | 5.2.18 |
| Django REST Framework | 3.16.1 |
| PostgreSQL | 16.15; port 5433 pada instalasi penguji |
| Backend | http://localhost:8001/ |
| Base API | http://localhost:8001/api/v1/ |
| Alat pengujian | CMD, Windows PowerShell, curl dan browser untuk halaman health |
| Email pengujian | Mode file, folder privat `code/backend/private_outbox/` |

Port PostgreSQL mengikuti instalasi masing-masing anggota. Versi PowerShell, versi browser dan viewport belum dicatat. Pengujian form frontend melalui browser belum dilakukan.

## Hasil pengujian

| Pemeriksaan | Hasil dan sumber bukti |
| --- | --- |
| Setup dan migration, 17 Oktober | Setup selesai, migration accounts/core/framework berhasil, system check 0 masalah. |
| Health, 17 Oktober | Respons JSON menunjukkan status dan database READY, scope SLR_08 dan PostgreSQL mayor 16. Backend dijalankan kembali pada 18 Oktober. |
| Registrasi Reporter, 17 Oktober | POST auth/register/ menghasilkan HTTP 202 dan pesan generik. Respons ini membuktikan permintaan diterima; akun tetap memerlukan verifikasi. |
| Email dan verifikasi OTP Reporter | Berkas email lokal diterbitkan dan dibuka. Penguji melaporkan verifikasi selesai; login Reporter terverifikasi kemudian berhasil. Respons verifikasi tidak dilampirkan sebagai rekaman terpisah. |
| Login Admin dan profil, 17–18 Oktober | Login dan GET me/ berhasil. Profil menunjukkan role ADMIN dan is_active True. Log HTTP 18 Oktober menunjukkan 200. |
| Profil tanpa autentikasi, 17 Oktober | GET me/ tanpa token menghasilkan HTTP 401, AUTH_REQUIRED. |
| Refresh, 18 Oktober | POST auth/refresh/ dan pembacaan profil dengan access token hasil refresh berhasil, HTTP 200. |
| Logout, 18 Oktober | POST auth/logout/ menghasilkan HTTP 204. Refresh berikutnya dari sesi tersebut ditolak HTTP 401. |
| Audit Admin, 18 Oktober | GET admin/audit/ menghasilkan HTTP 200. Pencarian ACCOUNT_LOGOUT untuk akun Admin penguji menemukan event yang tercatat. |
| Login Reporter dan profil, 18 Oktober | Login dan GET me/ menghasilkan HTTP 200. Peran akun diperiksa sebagai REPORTER. |
| Pembatasan audit, 18 Oktober | Reporter yang telah login ditolak mengakses GET admin/audit/ dengan HTTP 403. |
| Pemeriksaan Git, 18 Oktober | git check-ignore mengonfirmasi .env, .venv, private_outbox, private_media dan model_assets diabaikan. git ls-files untuk jalur tersebut tidak menampilkan berkas terlacak pada saat pemeriksaan. |

Pada 18 Oktober, screenshot terminal juga menunjukkan refresh berhasil, logout 204, refresh setelah logout 401, audit Admin 200, event logout ditemukan, login Reporter berhasil dan penolakan audit Reporter 403.

### Tes otomatis Windows

Perintah yang dijalankan pada 17 Oktober:

```bat
cd code\backend
UJI_BACKEND.bat
```

Hasil output penguji:

```text
Found 73 test(s).
System check identified no issues (0 silenced).
Ran 73 tests in 4.322s
OK
```

Runner membuat database pengujian terpisah dan menghapusnya setelah selesai. Skenario tersedia dalam [accounts/tests.py](../../code/backend/accounts/tests.py) dan [core/tests.py](../../code/backend/core/tests.py).

Tes otomatis mencakup OTP salah/kedaluwarsa/purpose/sekali pakai/resend, pembatasan request, aktivasi Operator, reset dan pencabutan sesi, normalisasi email, payload whitelist, cookie/CSRF/CORS, izin eksplisit, kepemilikan/assignment, audit, constraint dan keutuhan versi, storage privat, transaksi/revision/idempotency serta reservasi RUNNING/UNKNOWN. Cakupan tes otomatis tersebut dibedakan dari penelusuran API manual pada tabel di atas.

## Konfigurasi, cara menjalankan dan handoff

- Setup, konfigurasi, cara menjalankan serta pengujian: [README.md](README.md).
- Panduan menghubungkan rancangan akun SLR_07 ke API: [frontend-handoff.md](frontend-handoff.md).
- Kontrak endpoint, payload dan response: [openapi.json](openapi.json).
- Model dan layanan bersama: [database-dan-layanan.md](database-dan-layanan.md).
- Penyerahan serta keterlacakan card: [penyerahan.md](penyerahan.md).

Acuan paket berasal dari commit SLR_07 `f7943313fa01eb70c3b41c1ad3efe63d02430f8c`. Nilai itu merupakan commit sumber acuan, bukan bukti commit pekerjaan backend baru.

Prototype SLR_07 yang diperiksa memakai data contoh di memori. Layanan akun dan audit backend mengikuti pemetaan layar serta kontrak pada handoff; integrasi form frontend aktual masih perlu dilakukan dan diuji oleh tim. Endpoint bisnis laporan dan pipeline AI dilanjutkan pada SLR_10–SLR_14.

## Batas hasil dan bukti commit

- Pengiriman email SMTP internet belum diuji; OTP pengujian menggunakan berkas email lokal.
- Pengujian browser/frontend terintegrasi, layanan AI, deployment dan penerimaan kelompok belum dinyatakan selesai.
- Dokumen ini tidak memuat password, kode OTP, token atau isi berkas email.
- Setelah dokumen dan kode benar-benar di-commit serta di-push, catat hasil `git rev-parse HEAD` dan URL commit pada bagian **Bukti Pekerjaan** card SLR_08.
- Commit yang dirujuk harus sudah tersedia di repository kelompok dan mencakup berkas hasil pengujian ini. SHA pekerjaan tidak diisi dengan nilai acuan SLR_07.
