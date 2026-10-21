# Notebook historis

Folder ini hanya memuat notebook lama beserta salinan _executed yang memang tersedia. Satu README ini menjelaskan seluruh subfolder; setiap subfolder berisi berkas .ipynb.

| Subfolder | Tahap | Jumlah notebook | Isi |
| --- | --- | ---: | --- |
| [00_tanggapmakna/](00_tanggapmakna/) | Sumber awal TanggapMakna | 7 | Notebook feasibility, evaluasi lokal, Fusion dan blind historis sebelum susunan SILAR final. |
| [01_pilot_18okt/](01_pilot_18okt/) | Reviewed pilot — 18 Oktober | 9 | Notebook 00–08: pelatihan awal, fine-tune SENA/NARA, evaluasi review dan analisis cutoff. |
| [02_pemuatan_v02_v04/](02_pemuatan_v02_v04/) | Pemuatan v0.2–v0.4 | 2 | Notebook 09–10: pemeriksaan pemuatan kandidat dan rancangan penerimaan awal. |
| [03_perbaikan_v05/](03_perbaikan_v05/) | Perbaikan v0.5 | 6 | Notebook 11, 11b dan 12: fine-tune CPU, fokus NON_EVENT dan verifikasi regresi. |
| [04_perbaikan_v06/](04_perbaikan_v06/) | Perbaikan v0.6 | 6 | Notebook 13, 13b dan 14: konteks, penyeimbangan kelas dan verifikasi. |
| [05_perbaikan_v07/](05_perbaikan_v07/) | Perbaikan v0.7 | 4 | Notebook 15–16: pasangan konteks dan verifikasi kandidat. |
| [06_penerimaan_v081/](06_penerimaan_v081/) | v0.8.1 / FINAL081 | 10 | Notebook 20–23: verifikasi bobot, koreksi konteks, penguatan kontras dan penerimaan FINAL081. |
| [07_penerimaan_v082/](07_penerimaan_v082/) | v0.8.2 / FINAL082 | 6 | Notebook 24, 24b dan 25: perbaikan komposisi field dan penerimaan FINAL082. |
| [08_penerimaan_v083/](08_penerimaan_v083/) | v0.8.3 / FINAL083 | 9 | Notebook 26, 26b, 26c, 27 dan 28: training konteks/cache, penguatan, ekspor dan penerimaan FINAL083. |
| [09_draf_dan_sumber_asli/](09_draf_dan_sumber_asli/) | Draf dan sumber asli | 8 | Sumber notebook sebelum run dan salinan tahap antara yang berbeda dari notebook akhirnya; bukan hasil final aktif. |

## Catatan membaca riwayat

Nama _executed menandai salinan hasil eksekusi yang tersedia. Draf/sumber awal dipisahkan karena belum tentu sama dengan sumber yang akhirnya dieksekusi. Notebook 17–17e dan keluaran asli 26b yang tidak tersedia tidak direka ulang.

Isi notebook lama dipertahankan byte-identik. Path workspace di dalam notebook merupakan rekaman susunan saat eksperimen; lokasi arsip sekarang tercatat pada FILE_MANIFEST.json di folder induk.

Hasil mentah dan snapshot kode/data berada di [evidence/](../evidence/README.md), sedangkan laporan/grafik lama berada di [results/](../results/README.md). Salinan metadata dan README checkpoint yang berulang tidak menjadi isi folder historical.

Dataset antar putaran berbeda. FINAL081–083 kemudian menjadi data pengembangan/regresi; angka putaran tersebut tidak dipakai sebagai hasil akhir model. Putaran terbaru adalah FINAL084, dengan notebook 29–32 di [notebooks/](../notebooks/README.md) dan angka pada [reports/](../reports/README.md).
