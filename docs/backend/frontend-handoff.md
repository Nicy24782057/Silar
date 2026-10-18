# Handoff frontend SLR_07 ke backend SLR_08

Frontend produksi tetap mengikuti Vue 3, Composition API, Vue Router, Vite, Fetch dan CSS pada acuan tim. Paket SLR_07 yang diterima adalah prototype HTML/CSS/ES modules dengan data contoh di memori. Handler pada `app.mjs`/`model.mjs` belum memanggil backend. Sumber prototype tersebut tidak ditimpa oleh paket ini.

Base URL lokal: **`http://localhost:8001/api/v1/`**, semua path di bawah memakai trailing slash. Buka frontend menggunakan **localhost** juga. `localhost` dan `127.0.0.1` memiliki cookie berbeda; berpindah hostname di tengah alur akan memutus sesi/CSRF.

## Layar yang dapat dihubungkan sekarang

| Layar SLR_07 | Endpoint tersedia | Hasil/interaksi |
| --- | --- | --- |
| AK01 Masuk | GET `auth/csrf/`, POST `auth/login/`, `auth/refresh/`, `auth/logout/` | Access dalam JSON; refresh hanya cookie |
| AK02 Daftar Reporter | POST `auth/register/` | 202 pesan generik; arahkan memeriksa email |
| AK03 Verifikasi email | POST `auth/otp/request/`, `auth/otp/verify/` | `EMAIL_VERIFICATION`; challenge dari email |
| AK04 Aktivasi Operator | POST `auth/operators/activate/` | Kode + password baru + konfirmasi dalam satu tindakan |
| AK05 Lupa password | POST `auth/otp/request/` | Purpose `PASSWORD_RESET`; respons generik |
| AK06 Reset password | POST `auth/password/reset/` | Kode + password baru; sesi lama dicabut |
| AK07 Profil | GET/PATCH `me/` | PATCH hanya `full_name` |
| AD01 Akun Operator | GET/POST `admin/operators/`, GET/PATCH `admin/operators/{id}/`, GET `admin/operator-permissions/`, POST `admin/operators/{id}/activation-otp/` | Admin berizin; password tidak ditentukan Admin |
| AD03 Audit | GET `admin/audit/` | Admin `view_audit`; pagination dan filter |
| AD02 kandidat assignment | GET `admin/operators/` | Admin `assign_report` saja menerima OperatorTarget; assignment laporan belum tersedia |

Layar Reporter, antrean/tindak lanjut, publikasi, portal, notifikasi dan monitoring layanan masih memerlukan API card berikutnya. Tampilkan status pengembangan saat menguji frontend nyata; jangan mengambil keberhasilan simulasi sebagai bukti endpoint tersebut sudah ada.

## Urutan sesi dan CSRF

1. Ambil `GET auth/csrf/` dengan pengiriman/penerimaan cookie diaktifkan. Simpan `data.csrf_token` untuk header `X-CSRFToken`. Browser menerima cookie `csrftoken`.
2. Pada **semua POST `auth/*`**, kirim header CSRF, `Content-Type: application/json`, body sesuai schema dan cookie dengan opsi Fetch `credentials: "include"`. Origin frontend harus masuk `CORS_ALLOWED_ORIGINS` dan `CSRF_TRUSTED_ORIGINS`.
3. Login berhasil menghasilkan `{ "data": { "access": "..." } }`. Simpan access di memori aplikasi. Cookie `silar_refresh` ditetapkan backend sebagai HttpOnly, SameSite=Lax, path `/api/v1/auth/`; Secure pada HTTPS nonlokal. Frontend tidak membaca refresh atau menyimpannya ke localStorage.
4. Untuk API privat, kirim `Authorization: Bearer <access>`. Ambil `GET me/` untuk data akun dan `effective_permissions`. Menyembunyikan tombol membantu UX; backend tetap memeriksa izin pada setiap request.
5. Saat aplikasi dimuat ulang/access kedaluwarsa, ambil CSRF jika perlu lalu `POST auth/refresh/` dengan `{}` dan cookie. Gunakan satu proses refresh bersama agar beberapa request frontend tidak mencoba memakai cookie lama sekaligus. Refresh diputar; pemakaian ulang token lama ditolak.
6. `POST auth/logout/` dengan `{}` + CSRF + cookie mengembalikan **204 tanpa JSON**. Kosongkan access di memori; jangan selalu memanggil parser JSON pada respons 204.

API akun tidak memakai Idempotency-Key dan tidak menyimpan password/token/OTP dalam ledger. Idempotency-Key/expected_revision merupakan kontrak mutasi laporan yang diimplementasikan kemudian. Hindari retry otomatis terhadap POST setelah kehilangan respons; baca profil/status yang relevan dan minta tindakan pengguna bila hasil belum diketahui.

## Bentuk payload

```json
{
  "full_name": "Nama Pelapor",
  "email": "pelapor@example.com",
  "password": "password-pilihan-pengguna",
  "password_confirm": "password-pilihan-pengguna"
}
```

Payload di atas untuk register. Login hanya menerima `email,password`. Request OTP menerima `email,purpose` dengan `EMAIL_VERIFICATION` atau `PASSWORD_RESET`. Verifikasi menerima `challenge_id,code`; aktivasi/reset menambahkan `password,password_confirm`. Kode berupa string enam digit agar nol di depan tetap utuh.

Respons register/request OTP selalu `{data:{message:string}}` pada 202. **Jangan mengharapkan `challenge_id`, `user_id`, `expires_at` atau kode pada respons publik.** Email membawa tautan frontend dengan query `challenge_id` saja dan kode terpisah. Halaman akun membaca challenge dari tautan/email. Default route `/verify-email`, `/activate-operator`, `/reset-password` dapat disesuaikan melalui `FRONTEND_*_PATH` di backend; tim harus menyamakannya dengan Vue Router. Resend membuat challenge baru di email terbaru.

Respons akun:

```json
{
  "data": {
    "id": "UUID-dari-backend",
    "full_name": "Nama Pelapor",
    "email": "pelapor@example.com",
    "role": "REPORTER",
    "email_verified_at": "2026-10-17T10:00:00Z",
    "is_active": true,
    "effective_permissions": []
  }
}
```

Contoh ID di atas merupakan penanda penjelasan, bukan UUID yang dikirim. DTO lengkap dan tipe dapat diimpor dari [openapi.json](openapi.json). Semua kunci response schema hadir; nilai nullable tetap `null`. Daftar menggunakan `{count,next,previous,results}`, bukan envelope `data`. Query pagination `page` positif, `page_size` 1–100.

OperatorCreate menerima `full_name,email,permission_ids`. Ambil ID integer dari katalog tujuh permission; jangan hardcode angka. Role Operator ditetapkan backend, akun awal nonaktif, password belum dapat dipakai. Admin `manage_operator` memperoleh OperatorAccount termasuk `permission_ids`; Admin `assign_report` saja memperoleh OperatorTarget tanpa email/ID permission. Pengiriman ulang aktivasi Admin menghasilkan metadata challenge pada 202, tanpa kode; kegagalan pengiriman menghasilkan 503.

## Perbedaan dengan simulasi SLR_07

| Simulasi prototype | Kontrak backend yang digunakan |
| --- | --- |
| Nama `name` pada fixture | `full_name` |
| ID contoh seperti `op-a` | UUID dari backend; permission ID tetap integer |
| Pergantian peran melalui kontrol demo | Login akun nyata, GET `me/`, izin eksplisit |
| Kode/challenge contoh tersedia di simulasi | Kode/challenge dari email; nilai tidak ditampilkan API publik |
| Data berubah langsung dalam browser | Mutasi melalui API, kemudian baca hasil yang telah commit |
| String sederhana untuk beberapa field kartu | Skema A4.22 memakai array string dan nilai nullable; API fitur menyusul |
| Simulasi RUNNING/UNKNOWN/offline | Status backend dan penanganan koneksi aktual; belum berarti pipeline tersedia |

## Penanganan hasil dan kesalahan

```json
{
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "Periksa isian permintaan.",
    "fields": { "full_name": ["Field wajib diisi."] },
    "request_id": "UUID-korelasi"
  }
}
```

Gunakan `fields` untuk pesan dekat input; `message` untuk konteks; `request_id` untuk bantuan teknis. 400 = schema/input; 401 = kredensial/token; 403 = izin atau CSRF; 404 = tidak tersedia/di luar scope; 409 = konflik/replay laporan; 422 = challenge/transisi tidak sah; 429 = pembatasan, baca `Retry-After`; 503 = layanan belum tersedia. Jangan mengubah 429/503 menjadi notifikasi sukses.

Header `X-Request-ID`, `Retry-After` dan `Idempotency-Replayed` diekspos melalui CORS. API privat memakai `Cache-Control: no-store`. Service worker/PWA tim harus melewati cache untuk auth, API privat dan media; mode offline hanya tampilan dasar, operasi laporan memerlukan koneksi.

## Uji bersama yang masih perlu dilakukan

Catat browser/versi, OS, viewport dan origin. Telusuri registrasi–email–verifikasi–login, aktivasi Operator, kode salah/kedaluwarsa, resend, reset dan sesi lama, reload/refresh, logout 204, pencabutan permission serta penonaktifan akun. Pastikan route challenge aktual dapat dibuka, keyboard/fokus dan pesan error dipahami pengguna. Bukti manual serta penerimaan kelompok dimasukkan ke checklist penyerahan.
