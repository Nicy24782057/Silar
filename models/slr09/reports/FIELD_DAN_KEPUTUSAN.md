# Field, adapter/Fusion dan keputusan akhir

Hasil ini mengukur keluaran pipeline field, bukan metrik token NARA saja.

| Metrik | Hasil |
| --- | --- |
| Field nonkosong tepat | **154/176 = 87,50%** |
| Isi berlebih pada acuan kosong | **10/174 = 5,75%** |
| Batas awal | ≤5%; 8/9 pemeriksaan lulus |
| Batas revisi pengguna | ≤6%; **9/9 pemeriksaan lulus** |
| Prediksi, label manusia dan metrik berubah? | Tidak |
| Training/inferensi baru karena revisi batas? | Tidak |

## Rincian per field

| Field | Tepat / acuan nonkosong | Ketepatan nonkosong | Isi berlebih / acuan kosong | Isi berlebih |
| --- | --- | --- | --- | --- |
| location_text | 42/47 | 89,36% | 1/3 | 33,33% |
| time_text | 46/47 | 97,87% | 0/3 | 0,00% |
| occurred_at | Tidak ada acuan nonkosong | — | 0/50 | 0,00% |
| involved_parties | 23/24 | 95,83% | 1/26 | 3,85% |
| impacts | 16/28 | 57,14% | 5/22 | 22,73% |
| victims | 8/8 | 100,00% | 0/42 | 0,00% |
| affected_objects | 19/22 | 86,36% | 3/28 | 10,71% |

occurred_at memiliki 50 acuan kosong; kesesuaian null tidak membuktikan kemampuan normalisasi timestamp. Skor nonkosong 87,50% mengecualikan acuan kosong. Pada impacts, hasil tepat adalah 16/28 dan isi berlebih 5/22; kelemahan itu tetap terlihat pada penerimaan pilot.

## Sembilan pemeriksaan

| Pemeriksaan | Batas awal 5% | Batas revisi 6% |
| --- | --- | --- |
| sena_macro_f1 | Lulus | Lulus |
| non_event_recall | Lulus | Lulus |
| all_event_class_recalls | Lulus | Lulus |
| nara_macro_f1_all_14_non_o | Lulus | Lulus |
| nara_exact_span_f1 | Lulus | Lulus |
| fields_nonempty_exact | Lulus | Lulus |
| empty_field_spurious_rate | Belum lulus | Lulus |
| adapter_fusion_contract | Lulus | Lulus |
| simulation_vs_real_exercise_contrasts | Lulus | Lulus |

Cutoff confidence tetap 0,95, NON_EVENT memblokir submission dan Human Verification selalu wajib. Batas field kosong direvisi setelah hasil pertama diketahui; keputusan 9/9 adalah perubahan toleransi, bukan peningkatan kinerja statistik atau test independen baru.

## Sumber persis

- [JSON evaluasi keputusan 6% — bagian fields dan checks](../evidence/acceptance_FINAL084_target006_20261020/evaluation_under_limit006.json).
- [Perbandingan keputusan awal dan revisi](../evidence/acceptance_FINAL084_target006_20261020/decision_comparison.json).
- [Persetujuan revisi batas pengguna](../acceptance/target_revision_FINAL084_limit006.json).
- [Notebook 32 yang sudah dieksekusi](../notebooks/32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb).
- [Dokumen keputusan akhir](../SLR09_Keputusan_Akhir_FINAL084_Batas6persen.md).

Penerimaan berlaku untuk MVP_ASSET_PILOT. Backend submission dan VM tujuan tidak diuji oleh perhitungan field ini.
