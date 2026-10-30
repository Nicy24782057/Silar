# Audit menyeluruh antarmuka dan penghapusan draft

Revisi lanjutan setelah laporan pengguna tentang ilustrasi login bertumpuk,
keadaan fetch yang belum lengkap, serta halaman Admin/Operator yang belum
mengikuti seluruh bagian desain. Paket bersifat kumulatif terhadap SLR13.

## Sumber yang diperiksa

ZIP `SILAR_Seluruh_Role_Palet_Terang (2)(2).zip`:
`f83c5b3fa7f9290114e4fa131952e756d962fb0a123dd179f59644b501ec0b27`.
Seluruh 30 SVG dan lima panduan Markdown diperiksa. SVG dibuka sebagai dokumen
interaktif untuk membaca tab, form, dialog dan keadaan yang tidak tampak pada
pratinjau gambar biasa. Tersedia 60 tangkapan sumber (dua tema), tujuh tab
Operator, dan dialog Tambah Operator. Pemetaan 30 file ke halaman/komponen
ada pada [REVISI_UI_20261030.md](REVISI_UI_20261030.md).

Nama, angka, ID, bukti dan keluaran AI contoh pada sumber tidak dipindahkan
menjadi data aplikasi. Tujuh ringkasan laporan pada panduan Admin berarti tujuh
baris data contoh, bukan tujuh kartu statistik tambahan.

## Perbaikan

| Bagian | Implementasi dan pemeriksaan |
| --- | --- |
| Panel login | SVG, logo/mask, pola dan palet sumber tetap digunakan. Tinggi ruang teks, ilustrasi, dan kartu privasi dihitung terpisah; ilustrasi diperkecil pada layar pendek agar tidak saling menimpa. Desktop/tablet tetap dua panel; sampai 640 px hanya form kanan. |
| Reporter | Empat tahap pelaporan dipertahankan; loading/gagal/kosong, retry GET, pembacaan ID yang dipilih, filter/pagination, serta input multimodal diuji kembali. Tombol Hapus ditambah pada daftar dan detail untuk laporan sendiri yang belum dikirim. |
| Dashboard petugas | Proporsi tabel/kolom samping, tindakan banner, kartu akses Operator, tipografi dan warna diselaraskan. Angka/aktivitas berasal dari API sesuai izin. Tautan laporan terbaru Admin menuju ringkasan administratif. |
| Admin | Ringkasan administratif berada dalam dialog; penugasan memakai revisi serta petugas terbaru. Tambah/izin Operator memakai nama–email sejajar dan tujuh izin dalam dua kolom pada desktop; identitas akun lama hanya baca. Dialog memiliki header sesuai sumber dan isi dapat digulir pada ponsel. |
| Bukti Operator | Teks, audio dan foto berada pada kartu terpisah. Dialog langsung memperlihatkan keadaan memuat, lalu hasil atau kegagalan dan retry untuk berkas yang sama; URL blob dibersihkan saat konteks berubah/ditutup. |
| Narasi & AI | Narasi resmi, kartu SENA dan NARA dengan proporsi sumber; skor asli dengan format Indonesia, kelompok field, dan keluaran mentah melalui dialog. Informasi tidak tersedia tidak ditebak. |
| Review/tindak lanjut/keputusan | Form dan panel acuan mengikuti susunan sumber; hasil review awal kosong. Link acuan membuka Bukti/AI. Tindak lanjut/keputusan tetap mengikuti guard. Panel publikasi tetap di bawah keputusan, tujuh tab dipertahankan. |
| Riwayat/audit | Label manusia pada tabel; kode/metadata asal tetap di rincian. Peristiwa teknis Operator dapat diperluas. Respons audit lama diabaikan setelah filter baru. |
| Transisi | Pergantian halaman memakai fade/geser pendek, menjaga ruang selama perpindahan, dan menghormati reduced motion. Navigasi anchor publik dan perpindahan antar-ID diuji. |
| Respons hilang | Review dipulihkan lewat pembacaan request; klaim, penugasan dan DELETE memakai key/payload semula. Perubahan akun yang tidak memiliki ledger dibaca ulang; tidak dikirim ulang otomatis. |

Keputusan B untuk isi detail publik tetap berlaku. Field publik dibatasi oleh
kontrak yang sudah disepakati; sumber privat tidak ditambahkan demi meniru data
contoh. Izin administratif tidak menjadi izin membaca bukti atau bertindak
sebagai Operator. Penambahan kontrak DELETE dijelaskan terpisah pada
[API_HAPUS_DRAFT.md](API_HAPUS_DRAFT.md).

## Bukti implementasi

- [Login pada ukuran contoh 1535 × 727](bukti/audit-login-layar-pendek-terang.png)
- [Login tablet pendek](bukti/audit-login-tablet-pendek.png)
- [Tambah Operator](bukti/audit-admin-tambah-operator.png)
- [Dialog Admin pada ponsel](bukti/audit-admin-dialog-ponsel.png)
- [Review Operator](bukti/audit-operator-review.png)
- [Narasi & AI](bukti/audit-operator-ai-terang.png)
- [Keputusan dan panel publikasi](bukti/audit-operator-keputusan.png)
- [Konfirmasi penghapusan](bukti/audit-hapus-draft.png)

Perbandingan piksel otomatis berlaku untuk panel identitas 680 × 900: nol
piksel statis berbeda dalam dua tema, dengan area animasi dikecualikan. Halaman
lain diperiksa melalui render, tata letak, tema, breakpoint dan interaksi;
hasil itu tidak dinyatakan sebagai perbandingan piksel seluruh aplikasi.

## Memasang

Paket ini menambah migration `0005_report_soft_deletion`. Hentikan server,
gabungkan berkas berdasarkan path, lalu jalankan `manage.py migrate` sebelum
memulai backend. Petunjuk lengkap ada pada [README.md](README.md).
Hasil tes serta batas PostgreSQL dan uji tambahan AI ada di
[HASIL_VERIFIKASI.md](HASIL_VERIFIKASI.md).
