"""Apply the user's post-result 6% criterion to saved outputs; never load models."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from evaluate_acceptance import score, validate, digest, write

USER_MESSAGE='hmm kalau standar Isi berlebih pada field kosong kita ubah menjadi ≤6% bagaimana? apakah ada perubahan yang signifikan? jadi kita cukupkan training dan test nya kemudian anda berikan model sena dan nara versi paling terbaru yang digunakan tadi. dan juga notebook dan data riview yang dipakai untuk mengevaluasi ini'
USER_MESSAGE_AT='2026-10-20T22:51:37+07:00'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(root):
    root=Path(root).resolve()
    source=root/'evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run'
    out=root/'evidence/acceptance_FINAL084_target006_20261020'
    out.mkdir(parents=True,exist_ok=False)
    files=['evaluation.json','reviewed_bundle_frozen.json','predictions.jsonl','evaluation_lock.json','workflow_result.json']
    frozen={name:sha(source/name) for name in files}
    original=json.loads((source/'evaluation.json').read_text())
    bundle=json.loads((source/'reviewed_bundle_frozen.json').read_text())
    predictions=[json.loads(x) for x in (source/'predictions.jsonl').read_text().splitlines()]
    assert all(value==original[key] for key,value in score(bundle['records'],predictions,bundle['protocol']).items())
    assert sum(original['checks'].values())==8 and not original['metric_targets_met']
    assert bundle['protocol']['targets']['empty_field_spurious_rate_max']==.05
    assert len(predictions)==50
    decision=dict(schema='slr09-explicit-user-target-revision-0.8.4',
        created_at=datetime.now(timezone.utc).isoformat(),status='APPROVED_BY_EXPLICIT_USER_CHAT',
        user_message=USER_MESSAGE,user_message_at=USER_MESSAGE_AT,
        approver='USER_VIA_CHAT_IDENTITY_NOT_INFERRED_FROM_REVIEWER_NAME',
        metric='empty_field_spurious_rate_max',old_target=.05,new_target=.06,
        changed_after_original_result_was_observed=True,
        original_acceptance_result_preserved=True,all_other_targets_unchanged=True,
        confidence_threshold_unchanged=.95,human_annotations_unchanged=True,
        model_weights_and_inference_code_unchanged=True,training_and_testing_phase_closed=True,
        additional_training_requested=False,additional_model_inference_requested=False,
        quality_acceptance_scope='MVP_ASSET_PILOT',
        quality_acceptance_basis='USER_REQUEST_TO_FINISH_TRAINING_AND_TESTING_WITH_REVISED_6_PERCENT_LIMIT',
        production_deployed=False,target_vm_verified=False,card_done=False,
        original_evidence_sha256=frozen,
        original_source_workbook_sha256='046e468d3b9cb137d39ce5886dbc0eee0325cc5d406902de745b980f02253ad4')
    write(out/'user_target_revision.json',decision)
    write(root/'acceptance/target_revision_FINAL084_limit006.json',decision)
    revised=deepcopy(bundle)
    p=revised['protocol']
    p['targets']['empty_field_spurious_rate_max']=.06
    p['previous_target_approval']=deepcopy(bundle['protocol']['approval'])
    p['approval']=dict(status='APPROVED',reviewer='Pengguna melalui pesan chat',at=USER_MESSAGE_AT,
        limitations_accepted=bundle['protocol']['approval']['limitations_accepted'],
        representativeness_accepted=bundle['protocol']['approval']['representativeness_accepted'],
        rationale='Pengguna meminta batas isi berlebih menjadi 6% dan mengakhiri training serta pengujian setelah mengetahui hasil FINAL084. Acuan manusia dan target lainnya tetap. Penerimaan ini terbatas pada pilot aset MVP.',
        source='EXPLICIT_USER_CHAT_TARGET_REVISION_AFTER_RESULT')
    p['target_revision_decision']='acceptance/target_revision_FINAL084_limit006.json'
    revised['target_revision']={'old_limit':.05,'new_limit':.06,'source':'USER_CHAT',
        'original_bundle_sha256':digest(bundle),'new_neural_inference_executed':False}
    assert revised['records']==bundle['records']
    rows,preflight=validate(revised,root)
    result=score(rows,predictions,p)
    assert result['metric_targets_met'] and all(result['checks'].values())
    assert [k for k in result['checks'] if result['checks'][k]!=original['checks'][k]]==['empty_field_spurious_rate']
    for key in ['sena','nara','fields']:assert result[key]==original[key]
    result.update(decision='ACCEPTED_MVP_ASSET_PILOT_UNDER_EXPLICIT_USER_REVISED_TARGET',
        quality_acceptance_approved=True,quality_acceptance_scope='MVP_ASSET_PILOT',card_done=False,
        source='SAVED_ORIGINAL_FINAL084_PREDICTIONS',saved_predictions_rescored=True,
        original_acceptance_repeated=False,new_model_inference_executed=False,new_training_executed=False,
        target_changed_after_observing_result=True,training_and_testing_phase_closed=True,
        user_target_revision=decision,preflight=preflight,
        original_result_sha256=frozen['evaluation.json'],original_predictions_sha256=frozen['predictions.jsonl'],
        interpretation='Only the acceptance criterion changes; model performance and all reviewed labels are identical. This is not a new independent test.')
    write(out/'reviewed_bundle_with_revised_target.json',revised)
    write(out/'evaluation_under_limit006.json',result)
    denominator=original['fields']['empty_denominator']
    summary=dict(status='SUCCEEDED',observed_empty_spurious_rate=result['fields']['empty_spurious_rate'],
        spurious_fields=10,empty_reference_fields=denominator,old_limit=.05,new_limit=.06,
        limit_change_percentage_points=1,allowed_spurious_fields_old=math.floor(.05*denominator),
        allowed_spurious_fields_new=math.floor(.06*denominator),original_checks_passed=8,revised_checks_passed=9,
        checks_total=9,model_predictions_identical=True,all_numerical_metrics_identical=True,
        original_result_preserved=True,training_and_testing_phase_closed=True,
        saved_predictions_rescored=True,new_model_inference_executed=False,new_training_executed=False,
        quality_acceptance_approved=True,quality_acceptance_scope='MVP_ASSET_PILOT',
        production_deployed=False,target_vm_verified=False,card_done=False)
    for name,want in frozen.items():assert sha(source/name)==want
    write(out/'decision_comparison.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary
