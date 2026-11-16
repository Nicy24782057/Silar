# Adendum Technical Reference — paket kewenangan Operator

Disepakati pada revisi SLR14, 16 November 2026. Adendum ini menjadi acuan terkini
untuk ketentuan izin Operator pada Bagian 4.4, A5.7 dan DTO/endpoint Operator A6.
Dokumen sumber Word tidak ditulis ulang pada revisi ini.

Admin mengelola identitas, aktivasi dan status akun Operator. Admin tidak lagi
memilih, menambah atau mencabut kewenangan Operator satu per satu. Seluruh akun
berperan OPERATOR yang aktif dan terverifikasi memperoleh paket tujuh kewenangan
penanganan yang sama, termasuk akun lama dengan grant sebagian atau kosong.

Paket tersebut mencakup antrean, pembacaan laporan yang ditugaskan, klaim,
review/validasi, tindak lanjut, publikasi dan penutupan. Kewenangan bukan akses ke
semua bukti: kepemilikan/penugasan terkini, ruang lingkup privat, review VALID,
status, versi, idempotency, sanitasi, approval dan audit tetap diperiksa.
Penonaktifan akun menghentikan akses. Kewenangan Admin tetap terpisah dan
memerlukan grant eksplisit.

Request pembuatan Operator hanya menerima nama dan email. Request perubahan
menerima nama/status serta alasan opsional; `permission_ids` tidak diterima.
Respons akun mempertahankan `permission_ids` sebagai metadata paket tetap yang
hanya dapat dibaca. Katalog tetap tersedia untuk membaca riwayat audit.

Rincian request, respons, penerapan akun lama dan pemeriksaan tersedia pada
[kontrak revisi SLR14](../slr14/revisi-izin-operator-20261116/README.md) dan
[OpenAPI](../backend/openapi.json). Bagian Technical Reference lain tetap berlaku.
