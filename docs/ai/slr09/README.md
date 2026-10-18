# Dokumentasi SLR09

**Workflow:** baca rekap -> periksa notebook dan hasil -> cocokkan identitas model -> lengkapi review/pemuatan -> catat commit.

| Berkas | Isi |
| --- | --- |
| `SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md` | Hasil evaluasi, batas metrik dan kesiapan card. |
| `SLR09_Penempatan_Berkas_dan_Model.md` | Panduan menyalin isi paket dan menempatkan kedua model. |
| `pemeriksaan_paket_repository.json` | Bukti konsistensi byte/path paket penyerahan. |

Paket kerja lengkap berada di `models/slr09/`. Semua path relatif seperti `code/`, `config/`, `data/`, `results/`, `sources/`, `evidence/` dan `notebooks/` di laporan utama dihitung dari **models/slr09/**. Struktur internal sengaja dipertahankan agar skrip dan snapshot notebook tetap sesuai. Data raw proyek tetap mengikuti `data/raw/` yang sudah ada.

Identitas model serta lokasi arsip tersedia pada `models/slr09/asset_manifest.json`; penjelasan model lengkap pada `models/README.md`. Arsip bobot besar ditambahkan terpisah pada `models/sena/` dan `models/nara/` sesuai nama hasil ekspor.

Paket disusun berdasarkan pemeriksaan baca saja repository https://github.com/Nicy24782057/Silar pada commit `f7943313fa01eb70c3b41c1ad3efe63d02430f8c`. Hanya `models/README.md` yang menjadi pengganti berkas existing; path lain dalam paket merupakan penambahan terhadap snapshot tersebut. Tidak ada commit, push atau deployment yang dijalankan.
