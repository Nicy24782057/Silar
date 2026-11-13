# Kontrak revisi akun — 13 November 2026

Tambahan terhadap kontrak akun SLR08. API laporan/publikasi serta proyeksi publik sembilan field tetap mengikuti kontrak yang ada. Skema mesin berada pada `docs/backend/openapi.json`.

## Halaman dan alur

Login menampilkan satu tautan **Verifikasi akun**, menuju `/verify-email`. `/activate-operator` tetap dapat dibuka sebagai alamat kompatibilitas dan menampilkan formulir email/kode yang sama. Pengguna tidak memilih atau mengirim peran.

Reporter yang baru mendaftar langsung menuju formulir kode, dengan email dibawa melalui memori selama perpindahan halaman. Kode yang benar memverifikasi email dan menampilkan tombol login. Tidak ada login otomatis.

Operator harus sudah dibuat oleh Admin. Kode yang benar membuka formulir kata sandi. Backend mengonsumsi kode dan menerbitkan bukti aktivasi sekali pakai. Akun tetap nonaktif sampai bukti tersebut digunakan untuk menyimpan sandi yang memenuhi aturan.

## Endpoint tambahan

### GET `/api/v1/auth/account-policy/`

Respons `200`, tanpa data akun:

```json
{"data":{"password_min_length":15,"otp_resend_seconds":60,"otp_ttl_seconds":600,"otp_max_attempts":5,"otp_window_seconds":900}}
```

Durasi OTP mengikuti settings aktif. Formulir membaca endpoint ini untuk petunjuk dan jeda. Backend tetap menentukan pembatasan sebenarnya.

### POST `/api/v1/auth/account/verify/`

Memerlukan CSRF dan origin yang sah sebagaimana endpoint akun lainnya. Body hanya:

```json
{"email":"pemilik@example.com","code":"012345"}
```

Backend menentukan tujuan dari akun yang sudah tersimpan: Reporter aktif tetapi belum terverifikasi, atau Operator undangan yang belum aktif/terverifikasi. Kode dicocokkan hanya dengan akun dan tujuan tersebut. Kode reset sandi tidak dapat digunakan di sini. Field tambahan, termasuk `role`, ditolak.

Respons Reporter `200`:

```json
{"data":{"message":"Email berhasil diverifikasi. Silakan masuk.","next":"LOGIN"}}
```

Respons Operator `200` menggunakan `next: SET_PASSWORD`, `message`, `activation_token` dan `expires_at`. Bukti berbentuk UUID, titik dan rahasia acak. Bukti hanya diberikan setelah kode benar; bukan token sesi/login, tidak membawa izin dan tidak mengubah peran. Masa berlakunya berakhir pada waktu kedaluwarsa OTP asal, bukan sepuluh menit baru sejak formulir sandi dibuka.

Kode salah/tidak berlaku, email tidak memenuhi syarat atau tidak dikenal menghasilkan `422 OTP_INVALID` tanpa menjelaskan keberadaan/peran akun. Pemeriksaan kelima tidak membuka kesempatan tak terbatas pada endpoint lain. Melewati batas menghasilkan `429 RATE_LIMITED` dengan `Retry-After`.

### POST `/api/v1/auth/operators/activate/` — bentuk tambahan

```json
{"activation_token":"BUKTI_DARI_RESPONS_VERIFIKASI","password":"SANDI_BARU_PILIHAN_PEMILIK","password_confirm":"SANDI_YANG_SAMA"}
```

Placeholder di atas harus diganti oleh aplikasi dengan nilai aktual; bukan contoh token atau sandi untuk digunakan.

Backend mengunci akun dan rekaman OTP, memeriksa tujuan, status akun, waktu kedaluwarsa, pencabutan, versi autentikasi, digest dan penggunaan sebelumnya. Sandi tidak layak menghasilkan `400` tanpa menghabiskan bukti. Keberhasilan menyimpan sandi menandai bukti terpakai dan mengaktifkan Operator secara atomik. Pemakaian ulang bukti ditolak. Respons sukses tidak menerbitkan sesi login.

Bentuk lama `challenge_id, code, password, password_confirm` tetap diterima untuk kompatibilitas. Kedua bentuk tidak boleh dicampur. Endpoint `/auth/otp/verify/` dan `/auth/password/reset/` lama tetap tersedia; reset sandi masih dibuka dari tautan email.

## Permintaan kode umum

`POST /api/v1/auth/otp/request/` menerima tujuan tambahan `ACCOUNT_VERIFICATION`, dengan email. Backend memilih EMAIL_VERIFICATION atau ACCOUNT_ACTIVATION sesuai akun yang sudah dibuat. Permintaan tidak membuat akun Operator baru.

Respons publik tetap generik `202`, termasuk alamat yang tidak memenuhi syarat. Tidak mengembalikan challenge, kode, ID pengguna atau peran. Tujuan lama EMAIL_VERIFICATION dan PASSWORD_RESET tetap diterima.

Batas kirim dan pemeriksaan dibagi dengan endpoint lama untuk akun/tujuan yang sama. Pergantian IP, halaman, tujuan alias, atau permintaan kirim ulang tidak mengosongkan counter pemeriksaan. Kirim ulang kode aktivasi juga mencabut bukti aktivasi yang belum diselesaikan, termasuk setelah OTP asal dikonsumsi.

## Penyimpanan dan pengiriman

Migration `accounts.0002_emailotp_activation_auth_version_and_more` menambah metadata bukti aktivasi pada EmailOTP, beserta constraint bentuknya. Rahasia bukti disimpan sebagai HMAC, tanpa teks asli. Kode/bukti/sandi tidak ditulis pada audit atau ledger. Frontend menyimpan bukti hanya dalam memori komponen dan menghapusnya saat keluar halaman. Reload formulir sandi memerlukan kode baru.

Email memuat teks biasa dan HTML, kode yang terlihat jelas, judul sesuai keperluan, serta tautan pembantu. Backend SMTP yang ada dipakai untuk pengiriman sungguhan; mode berkas hanya menulis `.eml`. Pengiriman ke Gmail memerlukan konfigurasi SMTP di mesin pemilik. Tidak ada pengiriman email eksternal dalam verifikasi paket ini.

## Aturan sandi

Registrasi, aktivasi Operator, reset sandi dan perintah pembuatan Admin memakai validator backend yang sama. Minimum baru 15 karakter. Pemeriksaan juga menolak sandi umum, seluruhnya angka, variasi sederhana identitas akun dengan angka/simbol, pola berulang, dan urutan mudah ditebak. Gabungan kata yang kebetulan memuat bagian nama tidak otomatis ditolak. Tidak ada kewajiban campuran huruf besar, angka dan simbol.

Formulir menjelaskan alasan penolakan, memberi petunjuk frasa, mendukung paste/password manager, dan menyediakan tampil/sembunyikan sandi. Keterangan panjang terpenuhi tidak disebut jaminan sandi kuat. Validator bukan jaminan mampu mendeteksi semua sandi yang mudah ditebak atau seluruh sandi yang pernah bocor.
