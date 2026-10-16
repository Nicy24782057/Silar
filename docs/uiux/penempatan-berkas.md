# Penempatan Berkas SLR_07

## Folder tujuan

Ekstrak ZIP di folder sementara, lalu salin **folder `docs`** ke **akar proyek SILAR**. Gabungkan dengan folder `docs` yang sudah ada. Paket ini memperbarui `docs/uiux/`; simpan tambahan review lokal sebelum mengganti berkas bernama sama. `MULAI_DI_SINI.txt` di luar folder docs hanya petunjuk dan tidak wajib masuk repository.

| Lokasi akhir, relatif terhadap akar SILAR | Isi/fungsi | Kedudukan |
| --- | --- | --- |
| `docs/uiux/README.md` | Daftar layar, alur, interaksi, FR/NFR–API, perangkat dan referensi sumber. | Dokumentasi utama |
| `docs/uiux/screens.json` | Pemetaan terstruktur 25 layar dan FR01–FR26. | Keterlacakan |
| `docs/uiux/prototype/index.html` | Titik masuk prototype. | Sumber desain yang dapat diedit |
| `docs/uiux/prototype/styles.css` | Tampilan, komponen dan aturan responsif. | Sumber desain yang dapat diedit |
| `docs/uiux/prototype/app.mjs` | Layar, navigasi, dialog dan interaksi. | Sumber desain yang dapat diedit |
| `docs/uiux/prototype/model.mjs` | Data contoh dan aturan simulasi alur. | Sumber prototype yang dapat diedit |
| `docs/uiux/test-plan.md` | Langkah serta harapan U07-01–U07-16. | Pedoman review |
| `docs/uiux/review-results.md` | Hasil pengguna, hasil teknis, temuan dan tindak lanjut. | Bukti review |
| `docs/uiux/review-checklist.md` | Rekap area dan pekerjaan tersisa. | Pendukung review |
| `docs/uiux/technical-review.md` | Perbaikan dan metode pemeriksaan teknis. | Bukti tindak lanjut |
| `docs/uiux/review-next-steps.md` | Uji ulang dan pemeriksaan manual yang masih dibutuhkan. | Pedoman finalisasi |
| `docs/uiux/submission.md` | Lokasi bukti card dan usulan commit. | Pedoman pengumpulan |
| `docs/uiux/penempatan-berkas.md` | Petunjuk yang sedang dibaca. | Petunjuk penempatan |
| `docs/uiux/bukti-review/README.md` | Cara menambah screenshot/rekaman aktual. | Pedoman bukti |
| `docs/uiux/bukti-review/hasil-pemeriksaan-teknis.json` | Hasil eksekusi, ID uji dan hash aset yang diperiksa. | Bukti teknis aktual |
| `docs/uiux/tools/check.mjs` | 42 pemeriksaan logika/struktur dasar. | Pendukung, memerlukan Node.js |
| `docs/uiux/tools/review-check.mjs` | 15 pemeriksaan tambahan terhubung ke skenario review. | Pendukung, memerlukan Node.js |
| `docs/uiux/prototype/*.md` dan `prototype/screens.json` | Salinan dokumen untuk tombol unduh pada prototype lokal. | Salinan distribusi; sumber utama tetap di `docs/uiux/` |

**Lokasi yang benar:** `SILAR/docs/uiux/prototype/index.html`. Jangan menyalin folder `docs` ke dalam `docs/uiux/`, karena akan menghasilkan jalur bertumpuk. Salin seluruh folder agar tautan dan modul tetap lengkap. Word/PDF/PNG merupakan pelengkap pilihan kelompok; paket ini sudah memuat sumber editable serta prototype.

## Menjalankan dan memeriksa

Dari akar SILAR:

```sh
py -m http.server 8000 --directory docs/uiux/prototype
```

Buka http://localhost:8000. Gunakan `python` atau `python3` bila `py` tidak tersedia. Jangan membuka index.html langsung melalui file explorer karena prototype memakai ES modules. Gunakan Muat ulang penuh setelah pembaruan berkas, sebelum alur baru; state contoh akan kembali ke awal.

Pemeriksaan teknis opsional, jika Node.js tersedia:

```sh
node docs/uiux/tools/check.mjs
node docs/uiux/tools/review-check.mjs
```

Untuk menyimpan hasil eksekusi baru secara terpisah:

```sh
node docs/uiux/tools/review-check.mjs --report docs/uiux/bukti-review/hasil-pemeriksaan-teknis-ulang.json
```

Skrip tidak menjalankan browser, tidak mengukur responsivitas dan tidak menghubungi backend/AI. Instalasi frontend produksi tetap mengikuti card implementasi. Jangan memindahkan berkas prototype ke folder kode frontend produksi.

## Pengumpulan

Unggah folder `docs/uiux/` beserta isinya ke repository SILAR. Cantumkan lokasi README, sumber prototype, hasil review, serta tautan commit yang sebenarnya pada card SLR_07. Baca `submission.md`. Screenshot/rekaman aktual ditambahkan ke `bukti-review/`; file petunjuk bukan bukti screenshot.
