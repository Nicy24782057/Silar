# Data pengembangan dan identitas acuan

| Kelompok | Isi |
| --- | --- |
| sena_train_reviewed.jsonl dan sena_validation_reviewed.jsonl | Partisi hasil review untuk eksperimen SENA awal. |
| scope_*, matched_pairs_*, mvp_seen_* dan quality_fix_* | Data/split, pasangan konteks dan diagnostik pengembangan per versi. |
| final_reference_proposals_* dan final_reference_identity_* | Proposal sebelum review serta identitas acuan penerimaan setiap putaran. |
| retirement_* dan diagnostic_retirement_* | Catatan bahwa acuan yang telah dilihat untuk perbaikan berubah menjadi development/regresi. |
| input_manifest.json dan standards_review_* | Identitas input dan catatan standar eksperimen. |

Proposal bukan label manusia final. Acuan FINAL084 yang benar-benar diuji berada pada [reviewed_bundle_frozen.json](../evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/reviewed_bundle_frozen.json); workbook asalnya berada di acceptance/.
