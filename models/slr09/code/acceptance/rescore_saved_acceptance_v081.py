"""Complete scoring of immutable predictions after a scoring-only bug fix."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
from evaluate_acceptance import score,write,file_sha,digest


def run(source,out,snapshot):
    out.mkdir(parents=True,exist_ok=False)
    bundle=json.loads((source/'reviewed_bundle_frozen.json').read_text())
    lock=json.loads((source/'evaluation_lock.json').read_text())
    assert digest(bundle)==lock['bundle_sha256']
    for relative,expected in bundle['protocol']['binding']['files_sha256'].items():
        assert file_sha(snapshot/relative)==expected,relative
    predictions=[json.loads(line) for line in (source/'predictions.jsonl').read_text().splitlines()]
    assert len(predictions)==len(bundle['records'])==50
    original=json.loads((source/'workflow_result.json').read_text())
    assert original['phase']=='SCORING' and original['records_completed']==50
    report=score(bundle['records'],predictions,bundle['protocol'])
    report.update(scope='FIRST_FROZEN_CANDIDATE_ORIGINAL_PREDICTIONS_SCORING_COMPLETED',
        original_workflow_status=original['status'],original_workflow_preserved=True,
        scoring_instrumentation_changed_after_inference=True,
        scoring_fix='Validate joined scalar source components; preserve exact-match criteria and mark invalid model values as contract failures.',
        gold_changed_after_inference=False,model_weights_or_predictions_changed=False,
        model_inference_executed_by_rescoring=False,
        reference_file_sha256=file_sha(source/'reviewed_bundle_frozen.json'),
        predictions_sha256=file_sha(source/'predictions.jsonl'),
        original_frozen_binding=bundle['protocol']['binding'],
        scoring_source_sha256=file_sha(Path(__file__).with_name('evaluate_acceptance.py')))
    write(out/'evaluation.json',report)
    shutil.copy2(source/'predictions.jsonl',out/'predictions.jsonl')
    shutil.copy2(source/'reviewed_bundle_frozen.json',out/'reviewed_bundle_frozen.json')
    write(out/'workflow_result.json',{'status':'SCORING_COMPLETED_FROM_FROZEN_PREDICTIONS',
        'at':datetime.now(timezone.utc).isoformat(),'original_run_failed_at_scoring':True,
        'records':50,'original_inference_executed':True,'new_model_inference_executed':False,
        'training_executed':False,'gold_changed':False,'metric_targets_met':report['metric_targets_met'],
        'quality_acceptance_approved':False,'card_done':False})
    print(json.dumps({'checks':report['checks'],'metric_targets_met':report['metric_targets_met'],
        'fields_nonempty_exact':report['fields']['nonempty_exact'],'quality_acceptance_approved':False},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','snapshot'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.source,a.output,a.snapshot)
