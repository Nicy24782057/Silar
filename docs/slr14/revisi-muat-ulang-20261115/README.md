# SLR14 — tombol Muat ulang pada Laporan Saya

Pada desktop, kolom tombol Muat ulang sebelumnya berukuran 110 piksel, sedangkan tombol memiliki lebar minimum 178 piksel. Akibatnya, tombol melampaui kolom dan terpotong oleh panel daftar. Sebelum perbaikan, masalah ini direproduksi pada viewport 1440 piksel dengan sekitar 68 piksel tombol berada di luar panel.

Kolom tindakan sekarang mengikuti lebar isi dan batas minimum tombol melalui `max-content`. Tiga filter tetap menggunakan pembagian ruang yang ada. Aturan dua kolom pada panel sempit dan satu kolom pada HP tetap digunakan. Tombol Muat ulang maupun keadaan Memuat… mendapat ruang yang cukup, termasuk ikon dan area kliknya.

Perubahan aplikasi hanya satu aturan pada `code/frontend/src/mobile-reviewed.css`. Revisi ini merupakan implementasi SLR14 dari temuan pengujian SLR15.

## Memasang dan mencoba

Paket ini melanjutkan `SILAR_SLR14_revisi_HP_dan_pencarian_14Nov2026.zip`. Hentikan frontend, lalu gabungkan berkas sesuai path ke proyek yang sudah menggunakan paket tersebut. Dari `code/frontend`, jalankan `npm.cmd run build`, kemudian `npm.cmd run dev`.

Sebagai alternatif, jalankan `git apply --check PERBAIKAN_SLR14_MUAT_ULANG.patch` lalu `git apply PERBAIKAN_SLR14_MUAT_ULANG.patch` dari root proyek. Gunakan salah satu cara penggabungan. Patch diuji terhadap isi persis paket 14 November. Jika ada perubahan lokal pada berkas yang sama, periksa dan gabungkan perbedaannya terlebih dahulu.

Di Laporan Saya, pastikan tombol terbaca utuh pada desktop, tablet dan HP. Pilih kategori/status, gunakan pencarian, lalu tekan Muat ulang. Pilihan yang sudah diterapkan harus tetap sama dan daftar dibaca kembali. Keadaan Memuat… harus terbaca selama permintaan berjalan. Untuk PWA produksi, terima pembaruan build melalui Aplikasi & Koneksi.

## Verifikasi

- Build produksi berhasil.
- Sebelum perbaikan, pemotongan tombol berhasil direproduksi.
- Sesudah perbaikan, 60 pemeriksaan tata letak lulus tanpa tombol/filter terpotong, saling menimpa atau melampaui panel. Cakupan: 16 lebar viewport dari 320 hingga 1640 piksel, batas ukuran panel untuk container query, keadaan loading, serta emulasi sentuhan HP. Pemeriksaan mencakup mode terang dan gelap.
- Tiga alur tombol lulus: loading dan pemulihan keadaan siap, pemeliharaan kata kunci/filter saat reload, dan aktivasi menggunakan keyboard.
- Tidak ada page error atau panggilan API di luar fixture yang disiapkan.

Pengujian ini memakai Chromium/Playwright pada build produksi dengan respons API lokal yang disimulasikan untuk mengisolasi tata letak. Backend, inferensi AI dan email tidak diuji ulang dalam perbaikan CSS ini. Bukti tersedia di `bukti/frontend-build.txt`, `bukti/browser-before.json` dan `bukti/browser-result.json`. Screenshot digunakan untuk pemeriksaan internal dan tidak disertakan dalam paket.

## Commit dan pencatatan card

Saran commit untuk perbaikan ini:

```text
fix(slr14): perbaiki tombol muat ulang pada Laporan Saya
```

Jika seluruh revisi antarmuka dan pencarian paket sebelumnya belum di-commit dan akan digabung menjadi satu commit, judul yang mencakup semuanya:

```text
feat(slr14): selaraskan antarmuka responsif dan pencarian laporan
```

[Catatan bukti pekerjaan](BUKTI_PEKERJAAN_SLR14.md) dapat ditempel sebagai tambahan pada card SLR14 setelah SHA/URL commit tersedia. Penyusun belum melakukan commit, push atau perubahan card GitHub.
