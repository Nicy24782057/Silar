# Kontrak pencarian laporan milik Reporter

Tambahan opsional pada `GET /api/v1/reports/`: parameter `q`. Bentuk hasil daftar, jumlah, next/previous, izin, autentikasi, filter, dan pagination yang sudah ada tetap digunakan. Kontrak ini melanjutkan endpoint bisnis SLR14. `docs/backend/openapi.json` khusus fondasi SLR08 dan tidak diperluas menjadi spesifikasi bisnis lengkap oleh revisi ini.

| Parameter | Aturan |
| --- | --- |
| scope | `owned`; hanya Reporter untuk fitur kata kunci ini. |
| q | Opsional, maksimal 100 karakter dan 8 kata setelah whitespace dipisahkan. Kosong/whitespace mempertahankan daftar tanpa pencarian. Karakter kontrol ditolak. |
| Filter yang sudah ada | workflow_status, preparation_status, validation_status, publication_status, event_type, ordering, page, page_size. |

Contoh: `/api/v1/reports/?scope=owned&q=Jalan%20Melati&page_size=5`.

Pencarian tidak membedakan huruf besar/kecil. Setiap kata harus cocok dengan salah satu sumber yang boleh dicari pada laporan yang sama. ID dapat memakai potongan heksadesimal, UUID lengkap, dengan/tanpa tanda hubung, atau awalan #. Parameter harus di-URL-encode secara normal. Kata yang cocok pada sumber berbeda tetap dapat digabungkan untuk satu laporan.

Query terlebih dahulu dibatasi ke pemilik dan laporan yang belum dihapus. Draft mencari pada narasi aktif serta bukti teks dalam bundle aktif. Sebelum bundle pertama dibuat, bukti teks yang telah disimpan juga dapat dicari. Bukti di luar bundle aktif dan narasi versi lama tidak menjadi kecocokan pencarian. Laporan terkirim memakai narasi dan bundle pada kartu versi resmi. File foto/audio tidak dibaca ulang, dan tidak ada inferensi AI, OCR, transkripsi baru, atau efek tulis.

Pencarian mencakup sumber teks/narasi, bukan nama berkas, data akun, catatan internal petugas, atau semua versi riwayat. Draft yang hanya berisi foto/audio tanpa teks/narasi dapat ditemukan berdasarkan ID atau filter. Ringkasan kartu JSON hasil ekstraksi/revisi tidak menjadi indeks terpisah bila kata tersebut tidak ada pada sumber teks/narasi.

Filter pencarian dijalankan sebelum count, pengurutan dan pagination. Subquery Exists mencegah penggandaan laporan saat beberapa bukti cocok. Hasil tetap ringkasan daftar yang sudah ada, tanpa menambahkan isi bukti/narasi ke respons daftar. Status 400/INVALID_PAYLOAD digunakan untuk q tidak sah dan pemakaian kata kunci pada scope selain owned; scope yang tidak diizinkan tetap mengikuti guard 403. API pencarian ID workspace Operator/Admin tetap mengikuti kontrak sebelumnya.

Ringkasan dashboard tetap menghitung seluruh laporan akun. Daftar di bawahnya mengikuti pencarian/filter yang diterapkan. Mengosongkan kata kunci dan menekan Cari menghapus batas pencarian; Atur ulang filter juga menghapus kata kunci. Pergantian halaman dan Muat ulang mempertahankan query yang berhasil diterapkan.
