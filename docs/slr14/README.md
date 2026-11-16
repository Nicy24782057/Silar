# SLR14 — penyederhanaan kewenangan Operator

Revisi yang disepakati 16 November 2026. Admin cukup mengisi **nama lengkap dan
email** saat membuat Operator. Pilihan izin, kolom jumlah izin dan tindakan
pengaturan izin dihapus dari Manajemen Operator.

## Kebijakan akses

Setiap akun berperan `OPERATOR` yang aktif dan terverifikasi memiliki paket tetap:
`view_queue`, `view_assigned_report`, `claim_report`, `review_report`,
`manage_followup`, `publish_report`, `close_report`.

Kebijakan berdasarkan peran ini juga berlaku bagi akun lama dengan grant kosong
atau sebagian, tanpa migrasi data/schema. Grant lama tetap tersimpan untuk
riwayat, tetapi tidak menentukan paket Operator. Grant Admin yang keliru melekat
pada Operator tidak memperluas paket tersebut.

Antrean hanya menampilkan ringkasan yang diizinkan. Isi/bukti privat dan tindakan
penanganan tetap memerlukan penugasan aktif sebagai penanggung jawab. Pengalihan
mencabut akses penanggung jawab sebelumnya. Persetujuan publikasi versi tepat,
review VALID, revisi, idempotency, transaksi, audit, serta guard CLOSED tetap
diperiksa. Operator tidak mendapat kewenangan Admin. Admin tetap membutuhkan
grant eksplisit untuk kewenangannya dan tidak otomatis menjadi Operator.

Akun menunggu aktivasi/nonaktif tidak memperoleh akses. Admin tetap dapat
mengirim ulang aktivasi serta mengaktifkan kembali/menonaktifkan akun yang sudah
terverifikasi. OTP dan penetapan sandi oleh pemilik email tetap berlaku.

## Kontrak API

Semua path di bawah diawali `/api/v1/`. Kontrak lengkap: [OpenAPI](../../backend/openapi.json).

| Operasi | Request / perilaku |
| --- | --- |
| `POST admin/operators/` | Hanya `full_name` dan `email`; akun menunggu aktivasi. |
| `PATCH admin/operators/{id}/` | `full_name` dan/atau `is_active`; `reason` opsional dicatat pada audit. `reason` saja ditolak. |
| `GET admin/operators/`, `GET admin/operators/{id}/` | `permission_ids` adalah metadata baca saja untuk paket tetap tujuh izin, termasuk pada akun nonaktif. `effective_permissions` hanya terisi bagi akun aktif dan terverifikasi. |
| `GET me/` | `effective_permissions` berisi ketujuh kewenangan bagi Operator yang memenuhi syarat. |
| `GET admin/operator-permissions/` | Katalog baca saja dipertahankan untuk metadata dan riwayat audit lama. |

`permission_ids` pada POST/PATCH ditolak dengan HTTP 400, termasuk array kosong.
Frontend dan backend perlu diperbarui bersama. Frontend lama yang masih mengirim
field tersebut harus diperbarui; server tidak menafsirkan pilihan izin sebagian.
`permission_ids` pada respons bukan bukti kelayakan akses: gunakan
`effective_permissions`, penugasan dan kondisi laporan terkini.

## Acuan teknis

Revisi ini menggantikan ketentuan pengaturan izin Operator secara individual
pada Technical Reference Bagian 4.4, A5.7 dan DTO/endpoint Operator A6, serta
handoff awal. Lihat [adendum Technical Reference](../../architecture/ADENDUM_OPERATOR_20261116.md).
Ketentuan lain pada dokumen tersebut tetap berlaku. Implementasi berada pada
SLR14; hasil uji dan penerimaan terintegrasi tetap dicatat pada SLR15.

## Pemeriksaan setelah diterapkan

1. Admin membuat akun menggunakan nama/email, lalu pemilik menyelesaikan OTP dan
   membuat sandi sendiri. Tidak ada pilihan izin di formulir atau daftar akun.
2. Operator baru dan lama dapat mengklaim, mereview, menentukan penayangan,
   mengelola tindak lanjut dan menutup laporan sesuai syarat bisnis.
3. Operator lain tidak dapat membaca bukti atau mengubah laporan yang sudah
   ditugaskan. Pengalihan memindahkan akses penanganan.
4. Penonaktifan akun menghentikan akses; aktivasi kembali memulihkan paket tetap.
5. Riwayat izin lama tetap dapat dibaca Admin, tetapi tidak dapat diubah.

Tidak ada perubahan dependensi atau migration untuk revisi ini. Panduan setup
tetap mengikuti [PANDUAN_RUNNING.md](../../../PANDUAN_RUNNING.md).

Hasil dan batas verifikasi: [HASIL_UJI.md](HASIL_UJI.md).
