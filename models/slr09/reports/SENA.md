# SENA — hasil evaluasi terbaru

**Putaran: FINAL084.** Model `SILAR_SENA_context_v0.8.4_20261020.zip`. Evaluasi pada 50 narasi sintetis yang direview manusia, 10 per kategori. Ini hasil pilot aset MVP.

| Metrik | Hasil |
| --- | --- |
| Accuracy | **98,00% — 49/50 narasi** |
| Macro F1 lima kategori | **97,99%** |
| Recall NON_EVENT | 90,00% |
| Recall setiap kelas kejadian | 100% |

## Precision, recall dan F1 per kategori

| Kategori | Precision | Recall | F1 | Support narasi |
| --- | --- | --- | --- | --- |
| FLOOD | 90,91% | 100,00% | 95,24% | 10 |
| EARTHQUAKE | 100,00% | 100,00% | 100,00% | 10 |
| FIRE | 100,00% | 100,00% | 100,00% | 10 |
| ACCIDENT | 100,00% | 100,00% | 100,00% | 10 |
| NON_EVENT | 100,00% | 90,00% | 94,74% | 10 |

## Confusion matrix

Baris adalah kategori acuan manusia; kolom adalah prediksi SENA.

| Acuan / prediksi | FLOOD | EARTHQUAKE | FIRE | ACCIDENT | NON_EVENT |
| --- | --- | --- | --- | --- | --- |
| FLOOD | 10 | 0 | 0 | 0 | 0 |
| EARTHQUAKE | 0 | 10 | 0 | 0 | 0 |
| FIRE | 0 | 0 | 10 | 0 | 0 |
| ACCIDENT | 0 | 0 | 0 | 10 | 0 |
| NON_EVENT | 1 | 0 | 0 | 0 | 9 |

## Kesalahan yang masih ada

ID `FINAL084-NON_EVENT-08`: acuan **NON_EVENT**, prediksi **FLOOD**, confidence 81,80%. Narasi: “Gempa dan banjir hanya muncul dalam cerita yang dibaca guru di Sekolah Puspanirmala siang ini.” Confidence di bawah 0,95, sehingga aturan low confidence tetap berlaku. Ini satu false event; hasil tidak disembunyikan oleh keputusan penerimaan.

## Sumber persis

- [JSON keputusan terbaru — baca bagian sena](../evidence/acceptance_FINAL084_target006_20261020/evaluation_under_limit006.json).
- [JSON pengujian pertama — metrik SENA identik](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/evaluation.json).
- [Prediksi setiap narasi](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/predictions.jsonl).
- [Notebook 31 yang sudah dieksekusi](../notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb).

Accuracy bukan F1. Hasil 50 contoh ini tidak membuktikan accuracy pada populasi lapangan atau kalibrasi probabilitas. Penyesuaian batas field 5% menjadi 6% tidak mengubah angka SENA.
