# Revisi temuan SLR15 — akun, Operator dan setup

Dasar perubahan: main `7af81c8e448e12eead2b54a4e6aad72b9e2a781e`. Perubahan ini merupakan tindak lanjut diskusi dan persetujuan pengguna, bukan perubahan status board atau deployment.

## Perilaku yang diperbarui

- Login memiliki satu tautan **Verifikasi akun**. Reporter langsung menuju formulir email/kode setelah registrasi, tanpa wajib membuka tautan email.
- Backend memilih peran/keperluan dari akun tersimpan. Operator undangan memasukkan kode, kemudian membuat sandi. Tidak ada pilihan menjadi Operator melalui halaman publik.
- Email menonjolkan kode, menyediakan versi HTML/teks, dan memiliki judul verifikasi atau aktivasi yang jelas. Mode SMTP/berkas tetap harus dikonfigurasi sesuai panduan.
- Sandi baru minimal 15 karakter, dengan pemeriksaan pola sederhana dan alasan penolakan yang membantu. Penghitungan panjang pada petunjuk menggunakan karakter Unicode.
- Operator memiliki tiga tahap **Pemeriksaan → Tindak lanjut → Keputusan**. Pemeriksaan menyatukan sumber dan formulir review. Riwayat berada pada dialog tersendiri. Setelah review terkonfirmasi tersimpan, tahap berikutnya terbuka otomatis.
- Publikasi tetap memakai pratinjau, konfirmasi dan tindakan menerbitkan. Tindak lanjut dapat dilewati tanpa membuat catatan fiktif. Pembatasan izin dan sumber privat tetap diperiksa backend.
- `SETUP_SILAR.bat`/`tools/setup_silar.py` menjadi pintu setup lengkap, termasuk paket AI/frontend dan pemeriksaan akhir. Pintu lama mengarah ke sana. `--check` hanya memeriksa lingkungan.
- Panduan menjalankan aplikasi ditulis ulang dari instalasi baru sampai pengujian. Riwayat panduan lama disimpan di `docs/archive/`.

## Menerapkan pembaruan

Gabungkan berkas sesuai path pada clone dasar tersebut, lalu jalankan migration akun baru dan bangun ulang frontend. Instruksi lengkap ada pada [panduan utama](../../../PANDUAN_RUNNING.md) dan `MULAI_DI_SINI.txt`.

Migration baru: `accounts.0002_emailotp_activation_auth_version_and_more`. Migration menambah empat field teknis pada OTP; tidak mengubah peran atau sandi pengguna yang sudah ada. Aturan baru diperiksa saat membuat/mengganti sandi.

## Kontrak dan bukti

- [Kontrak akun](KONTRAK_AKUN.md), termasuk bentuk respons dan kompatibilitas endpoint lama.
- [Hasil verifikasi](HASIL_VERIFIKASI.md).
- Manifest paket: `DAFTAR_PERUBAHAN.json`.

Model/provider pada tes pipeline menggunakan simulasi yang dinyatakan secara eksplisit. Pengujian aplikasi dengan model asli, penerimaan SLR15 dan pengiriman SMTP eksternal tetap memerlukan bukti terpisah. Kredensial, bobot model, database, venv, media privat dan hasil build tidak disertakan dalam paket.
