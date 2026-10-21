# Hasil terbaru — FINAL084

**Ini titik awal untuk mencari metrik terbaru kedua model.** Evaluasi: 50 narasi / 692 token acuan manusia. Status: pilot aset MVP diterima pada kriteria pengguna yang direvisi.

| Komponen | Metrik utama | Baca rincian |
| --- | --- | --- |
| SENA | Accuracy **98,00%**; macro F1 **97,99%** | [SENA: per kategori, confusion matrix dan kesalahan](SENA.md) |
| NARA | Macro F1 14 non-O **85,31%**; exact span F1 **81,86%** | [NARA: per label dan hitungan span](NARA.md) |
| Field pipeline | Tepat nonkosong **87,50%**; isi berlebih **5,75%** | [Field, 9 pemeriksaan dan perubahan batas](FIELD_DAN_KEPUTUSAN.md) |

## Pilih yang ingin dilihat

- [Ringkasan angka JSON, beserta path dan hash sumber](metrics_summary.json).
- [Bukti JSON lengkap untuk keputusan terbaru](../evidence/acceptance_FINAL084_target006_20261020/evaluation_under_limit006.json).
- [Bukti pengujian pertama dengan batas 5%](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/evaluation.json).
- [Notebook 31: inferensi aktual yang sudah dieksekusi](../notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb).
- [Notebook 32: keputusan dari prediksi tersimpan](../notebooks/32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb).
- [Excel review asli yang dipakai](../acceptance/Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx).

## Bedakan tiga hal

1. **Versi bobot:** SENA v0.8.4 dan NARA reviewed pilot 18 Oktober.
2. **Evaluasi terbaru:** FINAL084, 50 acuan manusia; ini sumber angka di halaman ini.
3. **Kriteria penerimaan:** awal 5% → revisi 6%; prediksi dan metrik tetap sama.

Hasil awal 8/9 tetap tersedia; hasil revisi 9/9 tidak menggantikan metrik lama secara diam-diam. Ringkasan ini dibangun dari JSON yang sudah ada, tanpa training atau inferensi baru.
