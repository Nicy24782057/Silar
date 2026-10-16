# Panduan Pengumpulan SLR_07

## Penempatan

Ekstrak `SLR_07_UIUX_SILAR_Siap_Dipindahkan.zip` ke folder sementara. Baca `MULAI_DI_SINI.txt`, lalu **salin folder `docs` ke akar proyek SILAR** dan gabungkan dengan docs yang sudah ada. Lokasi akhirnya harus `SILAR/docs/uiux/README.md`, bukan folder docs bertumpuk. Pertahankan tambahan review lokal sebelum mengganti berkas. Daftar setiap file dan fungsinya tersedia pada `penempatan-berkas.md`.

Dari akar SILAR, jalankan `py -m http.server 8000 --directory docs/uiux/prototype` (atau gunakan python/python3), kemudian buka http://localhost:8000. Muat ulang penuh setelah pembaruan, sebelum pengujian baru. Tidak perlu npm install atau mengubah konfigurasi frontend produksi.

## Bukti yang tersedia

| Bukti task | Lokasi dalam proyek | Keadaan |
| --- | --- | --- |
| Sumber desain/rancangan layar yang dapat diedit | docs/uiux/prototype/index.html, styles.css, app.mjs, model.mjs | Tersedia dan interaktif menggunakan data contoh. |
| File/URL prototype | docs/uiux/prototype/ atau URL di bawah | Tersedia; bukan layanan API/AI nyata. |
| README dan keterlacakan FR/NFR–API/perangkat | docs/uiux/README.md dan screens.json | Tersedia. |
| Catatan review dan tindak lanjut | docs/uiux/review-results.md, review-checklist.md, technical-review.md | Catatan pengguna dan hasil tambahan terisi; login serta urutan publikasi diperbaiki. |
| Bukti pemeriksaan teknis | docs/uiux/bukti-review/hasil-pemeriksaan-teknis.json | 15 pemeriksaan tambahan lulus; 42 dasar juga lulus. |
| Bukti manual perangkat dan keputusan kelompok | docs/uiux/bukti-review/ dan review-results.md | Diisi dari pemeriksaan nyata yang belum dilaporkan. |
| Commit repository SILAR kelompok | Tautan commit pada card | Diisi setelah commit/push kelompok. |

Prototype daring: https://silar-slr07-wireframe.ntesengmajola699.chatgpt.site. Akses mengikuti izin yang berlaku. File lokal dapat dijalankan untuk review kelompok. Word/PDF/PNG merupakan pelengkap pilihan kelompok.

## Teks bukti untuk card

Sumber desain dan prototype SILAR tersedia di `docs/uiux/prototype/`; dokumentasi dan pemetaan kebutuhan ada pada `docs/uiux/README.md` dan `screens.json`. Review awal Nicy Putra Pratama tanggal 16 Oktober 2026 telah dicatat. Pemeriksaan teknis tambahan publikasi, penutupan, Admin, Portal Publik, notifikasi/offline/PWA dan konten awareness tersedia pada hasil review dan bukti JSON. Login salah serta urutan publikasi portal telah diperbaiki; 42 pemeriksaan dasar dan 15 tambahan lulus. Finalisasi manual perangkat/usability, uji ulang akun dan penerimaan kelompok masih perlu dicatat. Tautan commit diisi setelah unggah repository SILAR kelompok.

## Commit yang disarankan

```text
SLR_07 Melengkapi Paket UI UX dan Hasil Review SILAR
```

Bila melalui terminal, dari akar repository SILAR:

```sh
git add docs/uiux
git commit -m "SLR_07 Melengkapi Paket UI UX dan Hasil Review SILAR"
```

Periksa perubahan sebelum commit, kemudian push sesuai branch kelompok. Paket ini tidak melakukan push ke GitHub SILAR kelompok. Commit Site prototype tidak menggantikan commit repository kelompok.

## Finalisasi

1. Jalankan prototype dari lokasi yang benar dan lakukan uji ulang singkat login salah/OTP kedaluwarsa.
2. Lakukan pemeriksaan perangkat dan usability U07-16; telusuri alur tambahan bersama kelompok. Panduan ada di review-next-steps.md.
3. Catat hasil aktual, lingkungan, bukti relevan dan keputusan kelompok.
4. Unggah docs/uiux/ dan cantumkan tautan commit sebenarnya pada card. Centang selesai sesuai hasil finalisasi.

Sumber HTML/CSS/JavaScript merupakan sarana prototype; frontend produksi tetap Vue 3. Prototype tidak menambahkan pertanyaan adaptif atau membuktikan backend/model telah berjalan.
