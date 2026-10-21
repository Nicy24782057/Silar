# Hasil Verifikasi Lokal Windows dan Tindak Lanjut Audit SLR_08

| Identitas dokumen | Keterangan |
| --- | --- |
| Card | SLR_08 — fondasi backend, database, autentikasi dan kontrol akses SILAR |
| Tanggal pengujian | 17–18 Oktober 2026 |
| Tanggal revisi dokumentasi | 21 Oktober 2026 |
| Dasar revisi | Audit SILAR SLR_07 dan SLR_08, 18 Oktober 2026; temuan A08-01 dan A08-02 |
| Lokasi dokumen dalam repository | `docs/backend/hasil-uji-windows.md` |
| Status pengujian yang tercatat | Setup, migration, 73 tes otomatis dan pemeriksaan API yang dirinci di bawah berhasil |
| Status penerimaan kelompok | Belum tercatat; dokumen ini tidak menyatakan persetujuan kelompok atau perpindahan card ke Done |

## 1. Tujuan dan lingkup

Dokumen ini mencatat pengujian fondasi SLR_08 pada komputer Windows lokal dan menindaklanjuti kebutuhan bukti pada audit. Cakupan utama adalah FR01 untuk layanan akun, FR23 untuk audit bersama, serta NFR01 untuk kontrol akses. Model, constraint, storage privat, revision, idempotency dan reservasi proses menjadi fondasi layanan berikutnya.

Hasil di sini berasal dari output terminal, screenshot dan laporan pelaksana yang disampaikan pada 17–18 Oktober 2026. Penyuntingan dokumen pada 21 Oktober 2026 tidak mencakup eksekusi ulang backend. Bukti lingkungan penyusunan paket tetap dipertahankan pada [hasil-verifikasi.md](hasil-verifikasi.md); hasil Windows ini melengkapinya.

Penerimaan tahap fondasi mengikuti lingkup SLR_08. Implementasi layar frontend, endpoint bisnis laporan dan pipeline AI dilanjutkan pada card terkait. Pengujian integrasi lintas fitur dan penerimaan menyeluruh mengikuti SLR_15.

## 2. Lingkungan pengujian

| Komponen | Konfigurasi atau nilai yang teramati |
| --- | --- |
| OS | Windows, build `10.0.26200.9711` |
| Python | `3.13.15`, melalui virtual environment lokal |
| Django | `5.2.18` |
| Django REST Framework | `3.16.1` |
| PostgreSQL | `16.15`, host `127.0.0.1`, port `5433` |
| Service database | `postgresql-x64-16` berjalan |
| Database aplikasi lokal | `silar_local` |
| Direktori backend | `code/backend/` |
| Server backend | `http://localhost:8001/` |
| Base API | `http://localhost:8001/api/v1/` |
| Alat pengujian | CMD, Windows PowerShell, `curl.exe` dan browser untuk halaman health |
| Email OTP pengujian | Mode file pada direktori privat `code/backend/private_outbox/` |

Instalasi PostgreSQL 16 pada port 5433 berhasil diakses melalui `psql` dan mengembalikan `server_version` sebesar `16.15`. Setup kemudian berhasil memakai koneksi tersebut. Port ini mengikuti instalasi komputer penguji dan bukan ketentuan port untuk semua anggota.

Versi PowerShell, versi browser dan viewport tidak tercatat dalam bukti yang diterima. Pengujian browser pada sesi ini terbatas pada halaman health; pengujian formulir frontend yang terhubung ke API belum didokumentasikan.

## 3. Sumber dan keterlacakan bukti

| Sumber | Penggunaan dalam dokumen |
| --- | --- |
| Output setup dan migration Windows, 17 Oktober | Bukti koneksi PostgreSQL 16, penerapan migration dan bootstrap izin/group |
| Output `UJI_BACKEND.bat`, 17 Oktober | Bukti 73 tes otomatis lulus pada lingkungan Windows |
| Output PowerShell dan `curl.exe`, 17–18 Oktober | Bukti registrasi, login/profil, refresh/logout serta pembatasan akses |
| Screenshot terminal, 18 Oktober | Bukti tambahan refresh, logout, audit Admin, event logout dan penolakan audit Reporter |
| Laporan pelaksana mengenai email/OTP | Bukti email lokal dibuka dan verifikasi dilaporkan selesai; respons verifikasi tidak direkam terpisah |
| Audit SILAR, 18 Oktober | Sumber temuan A08-01/A08-02 dan hasil pemeriksaan paket; bukan eksekusi ulang tes Windows |

Dokumen ini merupakan ringkasan bukti yang telah disampaikan. Salinan mentah output dan screenshot Windows belum dilampirkan sebagai berkas terpisah dalam dokumen ini. Bukti yang diringkas tidak dinyatakan otomatis sudah tersedia di repository.

Paket acuan yang dicatat audit adalah `SLR_08_Backend_SILAR.zip`, dengan SHA-256:

```text
e604b09c398d95a7e66680ccf519f6580c5e6666814ebffacc29fb6ecb23faf9
```

Hash tersebut mengidentifikasi ZIP yang diaudit. Pemeriksaan hash atau commit sumber pada direktori Windows saat tes belum tercatat, sehingga hash ZIP tidak diperlakukan sebagai bukti kesamaan setiap berkas lokal yang diuji. Lengkapi identitas sumber Windows dari catatan aktual yang tersedia; pengujian kode yang telah berubah memerlukan bukti pengujian versi tersebut.

Commit `f7943313fa01eb70c3b41c1ad3efe63d02430f8c` adalah acuan SLR_07 pada paket dan bukan SHA implementasi backend SLR_08. Sesuai klarifikasi lingkup audit, pencocokan dua commit lama SLR_08 tidak dijadikan temuan atau syarat penutupan tambahan.

## 4. Hasil pemeriksaan lokal

Semua path API pada tabel ini relatif terhadap `/api/v1/`, kecuali `/health/`.

| ID | Tanggal | Pemeriksaan | Hasil aktual | Penilaian |
| --- | --- | --- | --- | --- |
| W08-01 | 17 Oktober | Setup, migration dan bootstrap | `SETUP_LOKAL.bat` selesai; migration `accounts`, `core` dan framework berstatus OK; system check 0 masalah; katalog 13 izin dan tiga Group tersedia | Lulus berdasarkan output terminal |
| W08-02 | 17–18 Oktober | Ketersediaan backend dan database | `/health/` menunjukkan `status: READY`, `database: READY`, `scope: SLR_08` dan PostgreSQL mayor 16; backend kembali dapat diakses pada 18 Oktober | Lulus berdasarkan respons dan konfirmasi penguji |
| W08-03 | 17 Oktober | Registrasi Reporter | `POST auth/register/` mengembalikan HTTP 202 dengan pesan generik mengenai pengiriman petunjuk/kode | Lulus untuk penerimaan permintaan; HTTP 202 tidak membuktikan verifikasi akun |
| W08-04 | 17–18 Oktober | Email lokal dan verifikasi OTP | Berkas email lokal dibuat dan dibuka; pelaksana melaporkan verifikasi selesai; login Reporter kemudian berhasil | Verifikasi dilaporkan selesai; respons endpoint OTP tidak dilampirkan terpisah |
| W08-05 | 17–18 Oktober | Login Admin dan profil | Login serta `GET me/` berhasil; profil menunjukkan `role: ADMIN` dan `is_active: True`; log 18 Oktober menunjukkan HTTP 200 | Lulus berdasarkan output dan log HTTP |
| W08-06 | 17 Oktober | Profil tanpa autentikasi | `GET me/` tanpa token menghasilkan HTTP 401 dengan kode `AUTH_REQUIRED` | Lulus; akses privat ditolak sesuai harapan |
| W08-07 | 18 Oktober | Refresh sesi | `POST auth/refresh/` berhasil; access token hasil refresh dapat dipakai membaca profil; HTTP 200 | Lulus berdasarkan output dan screenshot |
| W08-08 | 18 Oktober | Logout dan penolakan refresh berikutnya | `POST auth/logout/` menghasilkan HTTP 204; refresh berikutnya dari sesi tersebut ditolak HTTP 401 | Lulus untuk pencabutan refresh sesi yang diuji |
| W08-09 | 18 Oktober | Pembacaan audit oleh Admin | `GET admin/audit/` menghasilkan HTTP 200; pencarian `ACCOUNT_LOGOUT` untuk aktor Admin penguji menemukan event | Lulus untuk pencatatan dan pembacaan event yang diperiksa |
| W08-10 | 18 Oktober | Login dan profil Reporter | Login serta `GET me/` menghasilkan HTTP 200; peran diperiksa sebagai `REPORTER` | Lulus berdasarkan output dan screenshot |
| W08-11 | 18 Oktober | Pembatasan audit untuk Reporter | Reporter yang telah login menerima HTTP 403 saat mengakses `GET admin/audit/` | Lulus; akses lintas peran ditolak sesuai harapan |
| W08-12 | 18 Oktober | Pengecualian berkas privat dari Git | `git check-ignore` cocok untuk `.env`, `.venv/`, `private_outbox/`, `private_media/` dan `model_assets/`; `git ls-files` atas jalur tersebut tidak menghasilkan berkas terlacak | Lulus pada keadaan repository saat diperiksa |

Pengujian logout membuktikan penolakan refresh setelah logout. Hasil tersebut tidak menyatakan access token lama langsung tidak berlaku; perilaku access token mengikuti konfigurasi dan mekanisme pencabutan backend.

## 5. Hasil 73 tes otomatis Windows

Perintah dijalankan melalui CMD dari akar repository SILAR pada 17 Oktober 2026:

```bat
cd code\backend
UJI_BACKEND.bat
```

Cuplikan output aktual, dengan baris progres dipadatkan:

```text
Found 73 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
Ran 73 tests in 4.322s
OK
Destroying test database for alias 'default'...
```

Sebanyak **73 tes lulus dalam 4,322 detik**. Runner membuat database pengujian terpisah dan menghapusnya setelah selesai. Sumber skenario tersedia pada [accounts/tests.py](../../code/backend/accounts/tests.py) dan [core/tests.py](../../code/backend/core/tests.py).

Cakupan tes yang dicatat pada paket meliputi normalisasi email, validasi password dan payload, OTP salah/kedaluwarsa/purpose/sekali pakai/resend, pembatasan request, aktivasi Operator, reset akses, JWT/rotasi/blacklist, cookie/CSRF/CORS, izin eksplisit, kepemilikan/assignment, audit, constraint dan keutuhan riwayat, storage privat, transaksi/revision/idempotency serta reservasi RUNNING/UNKNOWN.

Cakupan otomatis tersebut dibedakan dari pengujian API manual pada Bagian 4. Hasil tes tidak diubah menjadi klaim bahwa seluruh skenario telah ditelusuri manual melalui frontend.

Audit 18 Oktober tidak dapat mengulang tes database karena PostgreSQL pada lingkungan audit tidak tersedia. Hambatan lingkungan audit itu berbeda dari hasil tes Windows yang lulus dan tidak dicatat sebagai kegagalan 73 skenario aplikasi.

## 6. Tindak lanjut temuan audit

| Temuan | Perbaikan dokumentasi pada revisi ini | Status dan tindak lanjut aktual |
| --- | --- | --- |
| A08-01 — penerimaan tahap fondasi belum tercatat | Bukti teknis dipisahkan dari persetujuan kelompok; keadaan penerimaan dinyatakan pada Bagian 7 | Tetap terbuka sampai reviewer, tanggal, keputusan dan bukti review nyata dicatat pada `penyerahan.md` atau ditautkan dari sana |
| A08-02 — verifikasi pada lingkungan kelompok perlu ditautkan | Hasil Windows pada PostgreSQL 16.15, migration, 73 tes dan pemeriksaan API dihimpun dalam dokumen ini | Bukti runtime Windows terdokumentasi; tambahkan tautan dokumen ini dari `hasil-verifikasi.md` dan `penyerahan.md`, serta lengkapi identitas sumber Windows yang benar-benar diuji |

Audit tidak mencatat perubahan kode backend yang wajib dibuat sebagai tindak lanjut A08-01/A08-02. Revisi dokumen ini tidak mengubah kode, migration, konfigurasi lokal ataupun hasil historis pengujian.

## 7. Catatan penerimaan kelompok

| Unsur penerimaan | Keadaan berdasarkan bukti yang tersedia |
| --- | --- |
| Hasil teknis fondasi | Tersedia sesuai Bagian 4 dan 5 |
| Nama reviewer kelompok | Belum tercatat |
| Tanggal review kelompok | Belum tercatat; tidak disamakan dengan tanggal tes atau tanggal revisi dokumen |
| Keputusan kelompok | Belum tercatat |
| Bukti atau tautan review kelompok | Belum dilampirkan |
| Penutupan A08-01 | Belum dinyatakan selesai |

Pelaksana tes tidak otomatis dianggap sebagai reviewer yang memberikan persetujuan. Isi keputusan penerimaan berdasarkan review kelompok yang benar-benar dilakukan. Bila review sebelumnya sudah berlangsung di luar paket, lampirkan atau tautkan catatan aktualnya melalui [penyerahan.md](penyerahan.md), lalu perbarui bagian ini agar kedua dokumen konsisten.

## 8. Dokumentasi dan keselarasan dengan SLR_07

| Keperluan | Acuan dalam repository |
| --- | --- |
| Konfigurasi, setup, menjalankan dan menguji backend | [README.md](README.md) |
| Handoff layanan akun dan pemetaan rancangan SLR_07 ke API | [frontend-handoff.md](frontend-handoff.md) |
| Endpoint, payload dan response | [openapi.json](openapi.json) |
| Model, database dan layanan bersama | [database-dan-layanan.md](database-dan-layanan.md) |
| Bukti lingkungan penyusunan paket | [hasil-verifikasi.md](hasil-verifikasi.md) |
| Review dan penyerahan kelompok | [penyerahan.md](penyerahan.md) |

Prototype SLR_07 yang menjadi acuan menggunakan data contoh di memori. Hasil login/registrasi API pada dokumen ini tidak membuktikan formulir prototype sudah terhubung ke backend. Integrasi frontend memakai kontrak dan handoff yang tersedia, lalu diuji pada card implementasi terkait.

Temuan menu ponsel dan kontras avatar pada audit merupakan tindak lanjut SLR_07. Temuan tersebut tidak dicatat sebagai perubahan kontrak API SLR_08. Penerimaan fondasi backend tidak perlu menunggu seluruh frontend atau pipeline AI selesai.

## 9. Batas hasil dan pencatatan repository

- OTP pengujian menggunakan email lokal berbasis file; pengiriman SMTP internet belum diuji pada bukti ini.
- Pengujian frontend terintegrasi, layanan AI, deployment dan penerimaan lintas fitur tidak dinyatakan selesai melalui laporan fondasi ini.
- Password, kode OTP, access/refresh token, rahasia `.env` dan isi email privat tidak dimasukkan ke dokumen atau bukti publik.
- Pemeriksaan Git pada Bagian 4 berlaku pada 18 Oktober; hasil tersebut tidak menyatakan keadaan staging atau push pada tanggal berikutnya.
- Tempatkan dokumen ini sebagai `docs/backend/hasil-uji-windows.md`. Tambahkan tautan relatif `[Hasil uji Windows](hasil-uji-windows.md)` pada `hasil-verifikasi.md` dan `penyerahan.md` tanpa menghapus hasil lama atau catatan reviewer yang sudah ada.
- Setelah commit dan push benar-benar dilakukan, catat SHA/URL aktual pada card SLR_08 sebagai pelacakan pekerjaan. Jangan mengisi bukti backend dengan commit acuan SLR_07 atau menyatakan push selesai berdasarkan tersedianya file revisi ini.

## 10. Riwayat revisi

| Tanggal | Perubahan |
| --- | --- |
| 21 Oktober 2026 | Mempertahankan hasil tes 17–18 Oktober; menambahkan sumber dan batas bukti, identitas paket acuan, pemetaan A08-01/A08-02, keadaan penerimaan kelompok, serta petunjuk tautan antar-dokumen; tidak menambahkan hasil tes atau persetujuan yang belum dilaporkan |
