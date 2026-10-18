# Hasil verifikasi SLR_08

Tanggal: 17 Oktober 2026. Pelaksana: pemeriksaan otomatis lingkungan pengembangan paket; bukan laporan penerimaan kelompok. Data akun, bukti dan hasil model dalam test adalah fixture terisolasi.

| Pemeriksaan | Hasil |
| --- | --- |
| Migration database kosong | Lulus; accounts, core, auth, sessions, token blacklist |
| Migration menggunakan role aplikasi hasil setup | Lulus; tidak memakai superuser PostgreSQL |
| `manage.py check` | Lulus, 0 masalah |
| `makemigrations --check --dry-run` | Lulus, tidak ada perubahan model yang belum dimigrasikan |
| `manage.py test --settings=config.test_settings` | **73 test lulus** |
| `pip check` | Lulus, tidak ada dependency rusak |
| Instalasi/HTTP langsung | **9 pemeriksaan lulus**, rincian pada `bukti-review/http-smoke-result.json` |
| Pemeriksaan paket ZIP dan hash | Lihat `package-manifest.json` serta `bukti-review/package-check.json` |
| Windows launcher/browser/frontend Vue aktual | Belum dijalankan pada komputer anggota tim |
| SMTP internet, layanan AI dan deployment | Di luar hasil uji paket ini |

Test mencakup CSRF seluruh auth POST, origin/CORS, payload whitelist, respons akun generik, kode salah/kedaluwarsa/purpose/sekali pakai, counter lintas resend, kegagalan email, validator password, rotasi/blacklist refresh, logout 204, reset dan auth_version, penonaktifan, profil, tujuh izin integer, penolakan eskalasi, izin yang dicabut, proyeksi target tanpa email, audit atomik/immutable, enum SQL, FK sumber, versi unik, assignment aktif, ledger/revision/replay/expired/UNKNOWN, media privat, reservasi slot dan advisory lock pada koneksi terpisah.

Pemeriksaan HTTP memakai server Django lokal nyata, cookie jar HTTP, kotak email lokal, dan database yang dibuat installer. Alur: health, CSRF ditolak bila hilang, registrasi generik, verifikasi OTP dari email, login/password salah, profil Bearer, cookie HttpOnly/SameSite/path, refresh berputar, logout 204 dan penolakan sesi lama. Endpoint laporan yang belum dibangun dipastikan tidak menghasilkan keberhasilan fiktif.

Lingkungan uji: Linux x86_64, Python 3.12.14, PostgreSQL 16.12, versi dependency pada `requirements.txt`. PostgreSQL dibangun dari source resmi untuk host uji terisolasi; pemeriksaan larangan menjalankan proses sebagai root disesuaikan hanya pada build host tersebut karena keterbatasan UID lingkungan. SQL, transaksi, trigger, partial index dan advisory lock diuji pada PostgreSQL, bukan emulator/SQLite. Build host tersebut tidak dibundel. Tim tetap perlu menjalankan ulang test pada instalasi PostgreSQL 16 standar dan perangkat Windows sasaran.

Log final tersedia pada `bukti-review/backend-checks.txt`; laporan test per skenario pada `bukti-review/tests.json`. Log hanya memuat langkah pengujian dan status, tanpa password, token, kode atau isi email.

## Pemeriksaan kelompok berikutnya

- [ ] Jalankan setup dan test di Windows; catat Python/PostgreSQL/OS aktual.
- [ ] Hubungkan layar akun Vue; catat origin/browser/versi serta route challenge.
- [ ] Uji ulang OTP salah/kedaluwarsa, password salah dan reload/refresh/logout melalui browser.
- [ ] Uji Admin katalog/grant/revoke/nonaktif, lalu lihat efek pada sesi yang sudah masuk.
- [ ] Verifikasi SMTP internet jika mode itu dipakai dan pisahkan dari bukti email file lokal.
- [ ] Periksa UX, akses keyboard, pesan error dan Digital Awareness bersama tim frontend.
- [ ] Review kode/helper dan pembagian tanggung jawab SLR_10–SLR_14.
- [ ] Catat reviewer, temuan, perubahan, bukti manual, commit SHA serta penerimaan kelompok.
