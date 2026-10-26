# Hasil verifikasi patch Operator/Admin

Tanggal: 25 Oktober 2026. Dasar kode: `07a50f2380d97dca4af2d78712cc003e1267594f` pada repositori `Nicy24782057/Silar`.

| Pemeriksaan | Hasil |
| --- | --- |
| Build frontend produksi | Berhasil, termasuk pemisahan halaman menjadi berkas JavaScript yang dimuat saat diperlukan. |
| Tes frontend | **79 lulus**, 0 gagal. Termasuk pengujian lama dan pengujian hak menu/tindakan, nama, filter, keputusan, serta syarat penutupan. |
| Tes backend terpilih pada PostgreSQL 16 | **154 lulus**, 0 gagal. Meliputi workspace baru, akun, layanan inti, API laporan, filter, review Reporter, dan guard PostgreSQL yang terkait. |
| Alur browser dengan frontend dan backend sebenarnya | **13 pemeriksaan lulus**, tanpa kesalahan JavaScript halaman. |
| Pemasangan dan pemulihan | **7 pemeriksaan lulus** pada salinan proyek terpisah. |
| Pemeriksaan whitespace/diff sumber | Lulus. |

## Alur browser yang diperiksa

1. Login Admin melalui halaman bersama dan menu administratif sesuai izin.
2. Daftar Operator menggunakan nama lengkap sebenarnya.
3. Admin membuat Operator yang menunggu aktivasi melalui API akun yang sudah ada.
4. Aktivasi OTP, penetapan kata sandi oleh pemilik, dan login Operator dari halaman yang sama.
5. Perubahan nama akun dengan alasan/riwayat; penonaktifan menolak sesi akun yang sudah ada; akun dapat diaktifkan kembali.
6. Pembacaan Incident Card resmi dan pencatatan review INCONCLUSIVE secara terpisah dari hasil AI.
7. Pembuatan/penyelesaian tindak lanjut, keputusan internal, penutupan eksplisit, dan pembacaan setelah CLOSED.
8. Monitoring Admin hanya menampilkan metadata pada ruang kerja baru; pengalihan mencabut pembacaan privat petugas lama.
9. Klaim antrean membuka laporan resmi untuk akun yang mengklaim.
10. Daftar dan rincian audit hanya baca.
11. Monitoring layanan menampilkan hasil pengukuran sebenarnya.
12. Tata letak layar kecil dan navigasi tanpa halaman melebar ke samping. Tabel lebar dapat digulir pada area tabel.
13. Login Reporter dan rute daftar laporan lama tetap tersedia.

Viewport browser: desktop **1366 × 900** dan layar kecil **390 × 844**. Tampilan desktop, layar kecil, formulir pengalihan, akun, dan detail laporan diperiksa dari hasil render browser. Akun/laporan uji hanya dibuat pada database pengujian, bukan ditanam pada aplikasi.

## Perlindungan backend yang diperiksa

- Antrean hanya memuat laporan resmi dan ringkasan yang diizinkan, tanpa isi Reporter privat.
- Dua klaim bersamaan menghasilkan tepat satu penanggung jawab saat ini.
- Izin tindakan dan assignment diperiksa server, termasuk sebelum replay idempotensi. Revisi usang tidak menghasilkan perubahan samping.
- Pengalihan mempertahankan assignment historis, mengakhiri assignment lama, dan menolak akses/replay petugas lama.
- Ketiga hasil review dapat disimpan dengan alasan dan aktor/waktu, tanpa menyunting Incident Card resmi.
- PREPARE hanya untuk VALID; INVALID/INCONCLUSIVE tetap internal. PREPARE tidak membuat kandidat atau menerbitkan laporan.
- Review/keputusan ditolak saat ada kandidat aktif atau status publikasi yang menguncinya.
- Penutupan memerlukan review sah, tindak lanjut terminal, publikasi INTERNAL/PUBLISHED, dan tanpa kandidat aktif. CLOSED tetap terbaca bagi yang berhak dan menolak mutasi.
- Audit/notifikasi berada dalam transaksi tindakan; pemantauan tidak mengeluarkan rahasia atau isi laporan privat.
- Perubahan akun mempertahankan alasan serta izin sebelum/sesudah di audit, dan nama baru muncul pada target penugasan.

## Pemeriksaan pemasang

1. Mode `--check` tidak menulis berkas proyek.
2. Instalasi membuat cadangan, mengganti sumber/build yang sesuai, dan pemulihan mengembalikan isi awal.
3. Pemasangan berulang menghasilkan cadangan terpisah dan tetap dapat dipulihkan.
4. Fondasi yang tidak lengkap menyebabkan pemasang berhenti sebelum membuat cadangan/perubahan.
5. Payload yang berubah/rusak ditolak sebelum penyalinan.
6. Tujuan berupa tautan simbolis ditolak.
7. Kegagalan penyalinan di tengah pemasangan memulihkan sumber dan build sebelumnya.

Marker `.env`, pesan OTP lama, bukti privat, dan model tetap identik sebelum/sesudah pemasangan dan pemulihan pada pengujian tersebut. Pemasang tidak menjalankan Django atau perintah database.

## Batas hasil ini

Ini bukan uji langsung pada Windows, database, akun, HP fisik, atau folder proyek lokal Anda. Pemasang memeriksa fondasi sumber, bukan isi/skema database secara langsung. Proyek dasar harus sudah berjalan dengan migration SLR08–SLR12 yang sesuai.

Inferensi model AI lengkap, pengiriman SMTP internet, instalasi PWA fisik, serta penerbitan portal publik tidak dijalankan ulang sebagai bagian verifikasi patch tampilan ini. Layanan yang sudah ada dipertahankan. Kandidat/sanitasi/approval/penerbitan berada di SLR14; penerimaan lintas alur publikasi tetap dilengkapi pada SLR14/SLR15.

Sumber tes workspace/frontend yang relevan disertakan pada `files/code/.../tests`. Infrastruktur browser/PostgreSQL sementara, kredensial uji, pesan OTP uji, dan tangkapan layar internal tidak disertakan dalam paket.
