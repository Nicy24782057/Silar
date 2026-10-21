"""Run actual local inference on a seen regression pilot and fresh challenge.

No fitting or model selection occurs here. Neither output grants acceptance.
The fresh challenge has assistant-proposed labels, not human-reviewed gold.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'code/active_nara_adapter'), str(ROOT/'code/acceptance')]
from slr09_candidate_runtime import (CandidateModelRunner, candidate_record,
    extract_candidate_archive, selected_assets, INTEGRATION_CONFIG, CANDIDATE_LOCK)
from slr09_runtime import environment_snapshot, sha256_file, validate_prediction
from evaluate_acceptance import score, write, classification


def run(args):
    out=args.output
    out.mkdir(parents=True,exist_ok=False)
    state={'status':'PREPARING','training_executed':False,'model_inference_executed':False,
           'quality_acceptance_approved':False,'card_done':False,
           'independent_human_acceptance_test_executed':False,
           'started_at':datetime.now(timezone.utc).isoformat()}
    write(out/'run_state.json',state)
    try:
        config,lock,_=selected_assets()
        source_bytes=(args.previous/'reviewed_bundle_frozen.json').read_bytes()
        bundle=json.loads(source_bytes)
        fresh_bytes=args.challenge.read_bytes()
        challenge=json.loads(fresh_bytes)
        if challenge['status']!='ASSISTANT_PROPOSED_REFERENCE_NOT_HUMAN_ACCEPTED':
            raise ValueError('Unexpected challenge reference status')
        write(out/'configuration_frozen.json',config)
        write(out/'asset_lock_frozen.json',lock)
        (out/'reviewed_bundle_frozen.json').write_bytes(source_bytes)
        (out/'fresh_challenge_frozen.json').write_bytes(fresh_bytes)
        extraction=extract_candidate_archive(args.nara_archive,out/'runtime/nara','nara',lock['models']['nara'])
        write(out/'nara_extraction.json',extraction)
        code={str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/'code/active_nara_adapter').glob('*.py'))}
        write(out/'code_binding.json',{'files_sha256':code,
            'integration_sha256':sha256_file(ROOT/'config'/INTEGRATION_CONFIG),
            'asset_lock_sha256':sha256_file(ROOT/'config'/CANDIDATE_LOCK),
            'references_frozen_before_inference':True,
            'pilot_used_for_field_fix_development':True,
            'fresh_reference_is_not_human_reviewed':True})
        state['status']='INFERENCE'
        runner=CandidateModelRunner(args.sena_dir,out/'runtime/nara',device='cpu',cpu_threads=2)
        state['models']=runner.model_evidence
        predictions=[]
        with (out/'predictions.jsonl').open('x') as stream:
            for index,row in enumerate(bundle['records'],1):
                event,sena_coverage=runner.predict_sena(row['text'])
                tokens,nara_coverage=runner.predict_nara(row['text'])
                validate_prediction(event)
                pred=candidate_record(row,event,tokens,config,lock)
                pred.update(nara_tokens=tokens,sena_token_coverage=sena_coverage,nara_token_coverage=nara_coverage)
                stream.write(json.dumps(pred,ensure_ascii=False)+'\n');stream.flush()
                predictions.append(pred)
                state.update(model_inference_executed=True,records_completed=index)
                if index==1 or index%10==0:
                    write(out/'run_state.json',state)
                    print('Seen pilot inference',index,'/',len(bundle['records']),flush=True)
        report=score(bundle['records'],predictions,bundle['protocol'])
        report.update(scope='SEEN_PILOT_REGRESSION_ACTUAL_NEW_MODEL_INFERENCE',
                      decision='REGRESSION_DIAGNOSTIC_ONLY',quality_acceptance_approved=False,card_done=False,
                      independent_human_acceptance_test_executed=False)
        write(out/'evaluation.json',report)
        fresh=[]
        for row in challenge['records']:
            event,coverage=runner.predict_sena(row['text'])
            if coverage['truncated']:raise ValueError('Challenge input truncated')
            fresh.append({'id':row['id'],'event_classifier':event,'sena_token_coverage':coverage})
        write(out/'fresh_predictions.json',fresh)
        diagnostic=classification(challenge['records'],fresh)
        diagnostic.update(scope='ONE_SHOT_FRESH_ASSISTANT_LABELED_CHALLENGE_NOT_ACCEPTANCE',
                          quality_acceptance_approved=False,card_done=False,
                          used_for_model_or_checkpoint_selection=False,
                          human_reference_reviewed=False)
        write(out/'fresh_challenge_evaluation.json',diagnostic)
        state.update(status='SUCCEEDED',seen_pilot_metric_targets_met=report['metric_targets_met'],
                     fresh_challenge_records=len(fresh),environment=environment_snapshot(runner.torch,runner.device))
        print(json.dumps({'seen_pilot':{'sena_macro_f1':report['sena']['macro_f1'],
              'non_event_recall':report['sena']['per_class']['NON_EVENT']['recall'],
              'fields_nonempty_exact':report['fields']['nonempty_exact'],
              'empty_spurious_rate':report['fields']['empty_spurious_rate'],
              'checks':report['checks']},'fresh_challenge':{'accuracy':diagnostic['accuracy'],
              'macro_f1':diagnostic['macro_f1'],'non_event_recall':diagnostic['per_class']['NON_EVENT']['recall']},
              'quality_acceptance_approved':False},ensure_ascii=False,indent=2),flush=True)
    except Exception as exc:
        state.update(status='FAILED',error={'type':type(exc).__name__,'message':str(exc)})
        (out/'error_trace.txt').write_text(traceback.format_exc())
        raise
    finally:
        state['finished_at']=datetime.now(timezone.utc).isoformat()
        write(out/'run_state.json',state)
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--challenge',type=Path,required=True)
    p.add_argument('--sena-dir',type=Path,required=True)
    p.add_argument('--nara-archive',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
