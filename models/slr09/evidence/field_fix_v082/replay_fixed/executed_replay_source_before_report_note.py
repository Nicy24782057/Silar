"""Replay deterministic fields from frozen actual SENA/NARA outputs; no new inference."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'code/active_nara_adapter'),str(ROOT/'code/acceptance')]
from slr09_candidate_runtime import selected_assets,candidate_record
from evaluate_acceptance import score,write,file_sha


def load(p):return json.loads(p.read_text())


def replay(source,reference,out,config,lock):
    rows=load(reference)['records'];pred=[json.loads(x) for x in source.read_text().splitlines()]
    assert len(rows)==len(pred)==50
    results=[]
    for row,p in zip(rows,pred):
        assert row['id']==p['id']
        new=candidate_record(row,p['event_classifier'],p['nara_tokens'],config,lock)
        new.update(nara_tokens=p['nara_tokens'],sena_token_coverage=p['sena_token_coverage'],nara_token_coverage=p['nara_token_coverage'])
        assert new['event_classifier']==p['event_classifier']
        assert new['nara_tokens']==p['nara_tokens']
        results.append(new)
    out.mkdir(parents=True,exist_ok=False)
    with (out/'predictions.jsonl').open('x') as stream:
        for p in results:stream.write(json.dumps(p,ensure_ascii=False)+'\n')
    report=score(rows,results,load(reference)['protocol'])
    report.update(scope='KNOWN_REFERENCE_DETERMINISTIC_REGRESSION_AFTER_FIELD_REPAIR_NOT_BLIND_ACCEPTANCE',
        neural_inference_executed=False,weights_changed=False,reference_sha256=file_sha(reference),
        original_neural_predictions_sha256=file_sha(source),replay_predictions_sha256=file_sha(out/'predictions.jsonl'),
        sena_and_nara_raw_outputs_unchanged=True,quality_acceptance_approved=False,card_done=False)
    write(out/'evaluation.json',report);shutil.copy2(reference,out/'reference_frozen.json')
    return report


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    config,lock,_=selected_assets(ROOT)
    original=load(ROOT/'evidence/acceptance_v081/original_run/evidence/workflow_result.json')
    for name in ('sena','nara'):
        assert lock['models'][name]['files']==original['models'][name]['files']
    snapshot=out/'snapshot'
    files=list((ROOT/'code/active_nara_adapter').glob('*.py'))+[ROOT/'code/acceptance/evaluate_acceptance.py',
        ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.7.json',ROOT/'config/quality_candidate_asset_lock_v0.8.2.json']
    for p in files:
        target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    current=replay(ROOT/'evidence/acceptance_v081/original_run/evidence/predictions.jsonl',
        ROOT/'evidence/acceptance_v081/original_run/evidence/reviewed_bundle_frozen.json',out/'reviewed50',config,lock)
    old=replay(ROOT/'evidence/quality_fix_v081/guard_verification22b/predictions.jsonl',
        ROOT/'evidence/quality_fix_v081/guard_verification22b/human_regression_reference.json',out/'previous50',config,lock)
    before=load(ROOT/'evidence/acceptance_v081/scoring_completed/evaluation.json')
    assert current['metric_targets_met'] and old['metric_targets_met']
    assert old['fields']['nonempty_exact']>=175/191
    assert old['fields']['empty_spurious_rate']<=2/159
    write(out/'run_state.json',{'status':'SUCCEEDED','at':datetime.now(timezone.utc).isoformat(),
        'model_inference_executed':False,'actual_neural_outputs_reused':True,'training_executed':False,
        'sena_and_nara_weights_unchanged':True,'current50_retired_to_development':True,
        'before_nonempty_exact':before['fields']['nonempty_exact'],'after_nonempty_exact':current['fields']['nonempty_exact'],
        'previous50_regression_targets_met':True,'current50_regression_targets_met':True,
        'quality_acceptance_approved':False,'card_done':False})
    print(json.dumps({'before_fields':before['fields']['nonempty_exact'],'after_fields':current['fields']['nonempty_exact'],
        'after_nonempty_denominator':current['fields']['nonempty_denominator'],
        'current_checks':current['checks'],'previous50_checks':old['checks'],
        'quality_acceptance_approved':False,'new_model_inference_executed':False},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
