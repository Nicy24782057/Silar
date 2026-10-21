# Panduan Pengumpulan SLR_07 Setelah Audit

## Penempatan

Ekstrak `SLR_07_UIUX_SILAR_Perbaikan_Audit.zip` ke folder sementara. Baca MULAI_DI_SINI.txt, lalu salin folder **docs ke akar proyek SILAR** dan gabungkan dengan docs yang sudah ada. Lokasi akhirnya `SILAR/docs/uiux/README.md`. Pertahankan tambahan review lokal sebelum mengganti berkas. Daftar fungsi file ada di penempatan-berkas.md.

Jalankan `py -m http.server 8000 --directory docs/uiux/prototype` dari akar SILAR, atau gunakan python/python3. Buka http://localhost:8000 dan muat ulang penuh sebelum alur baru. Prototype tetap memakai sumber HTML/CSS/JS dan data contoh; frontend produksi mengikuti Vue 3.

## Bukti yang tersedia

| Bukti task | Lokasi | Keadaan |
| --- | --- | --- |
| Sumber desain/rancangan layar editable | docs/uiux/prototype/index.html, styles.css, app.mjs, model.mjs | Tersedia; menu dan kontras avatar diperbaiki. |
| Prototype interaktif | docs/uiux/prototype/ atau URL di bawah | Tersedia; bukan API/AI nyata. |
| README dan keterlacakan FR/NFR–API/perangkat | docs/uiux/README.md dan screens.json | Tersedia. |
| Review, temuan dan tindak lanjut | review-results.md, review-checklist.md, technical-review.md, audit-follow-up.md | Diperbarui dengan hasil pengguna, auditor dan regresi sesuai lingkup masing-masing. |
| Bukti audit browser paket awal | bukti-review/audit-sumber-2026-10-18.md | Tujuh alur lulus dan 112 kombinasi viewport dicatat; satu temuan menu dan satu kontras ditemukan. |
| Bukti teknis sumber hasil perbaikan | bukti-review/hasil-pemeriksaan-teknis.json dan hasil-regresi-audit.json | 42 dasar + 15 tambahan + 3 regresi lulus. |
| Riwayat sebelum perbaikan | bukti-review/regresi-audit-sebelum-2026-10-18.json dan hasil-pemeriksaan-teknis-2026-10-16.json | Dipertahankan sebagai bukti historis. |
| Visual ulang/perangkat dan penerimaan kelompok | bukti-review/ dan review-results.md | Belum disampaikan; langkah tersedia pada review-next-steps.md. |
| Commit final repository SILAR kelompok | Tautan pada card | Diisi setelah commit/push kelompok yang sebenarnya. |

Prototype daring: https://silar-slr07-wireframe.ntesengmajola699.chatgpt.site. Akses mengikuti izin yang berlaku. Word/PDF/PNG dapat menjadi pelengkap pilihan kelompok.

## Teks bukti untuk card

Sumber desain/prototype tersedia pada docs/uiux/prototype/; pemetaan dan pedoman implementasi ada pada README.md serta screens.json. Review awal Nicy Putra Pratama tanggal 16 Oktober dan audit eksternal 18 Oktober telah dicatat sesuai sumber. Menu ponsel setelah Buat Laporan serta kontras avatar diperbaiki. Paket hasil perbaikan lulus 60 pemeriksaan teknis. Audit browser pada paket awal mencatat tujuh alur lulus dan 112 kombinasi halaman/peran/viewport, dengan keterbatasan simulasi Linux. Visual ulang menu/avatar, pemeriksaan perangkat/usability, keputusan penerimaan kelompok dan commit GitHub kelompok masih perlu catatan aktual. Status: In Review.

## Commit yang disarankan

```text
SLR_07 Memperbaiki Menu Ponsel dan Melengkapi Hasil Audit SILAR
```

```sh
git add docs/uiux
git commit -m "SLR_07 Memperbaiki Menu Ponsel dan Melengkapi Hasil Audit SILAR"
```

Periksa perubahan sebelum commit, kemudian push sesuai branch kelompok. Pekerjaan ini tidak melakukan push ke GitHub SILAR kelompok; commit sumber prototype daring bukan penggantinya.

## Finalisasi penerimaan

1. Ulangi menu pada draft lama/baru di 360/390 px dan sesudah berganti ukuran; periksa kontras browser.
2. Catat perangkat/browser sasaran, pengalaman penggunaan, nama reviewer akhir, tanggal dan keputusan kelompok. Jika sudah dilakukan di luar ZIP, lampirkan bukti aktual.
3. Tautkan commit final dan tutup temuan berdasarkan hasilnya. Card dapat Done untuk lingkup SLR_07 tanpa menunggu frontend produksi atau AI, setelah kriteria tahap terpenuhi.

Keadaan penerimaan yang belum disampaikan dicatat eksplisit pada review-results.md; keputusan kelompok tidak diasumsikan dari hasil otomatis.
