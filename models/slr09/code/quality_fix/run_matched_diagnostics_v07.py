"""Verify the exported SENA and run frozen diagnostics without fitting.

Old pilot is seen regression. Retired assistant74 is fitted development. New50 has assistant-proposed
references frozen before training. Nothing here grants human acceptance.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'code/active_nara_adapter'),str(ROOT/'code/acceptance')]
from slr09_candidate_runtime import (CandidateModelRunner,candidate_record,selected_assets,
    extract_candidate_archive,INTEGRATION_CONFIG,CANDIDATE_LOCK)
from slr09_runtime import environment_snapshot,sha256_file,validate_prediction
from evaluate_acceptance import score,classification,write
from train_scope_sena_v06 import LABELS,score_probs


def run(args):
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    state={'schema':'slr09-matched-diagnostics-0.7','status':'PREPARING',
           'started_at':datetime.now(timezone.utc).isoformat(),
           'training_executed':False,'parameter_fitting_executed':False,'model_inference_executed':False,
           'quality_acceptance_approved':False,'card_done':False,
           'new_human_reference_review_completed':False,'fresh50_used_for_model_selection':False,'retired74_used_for_model_selection':True}
    write(out/'run_state.json',state)
    try:
        config,lock,_=selected_assets()
        split_guard=json.loads((ROOT/'data/scope_v07_split_guard.json').read_text())
        if sha256_file(args.fresh)!=split_guard['new50_sha256']:raise ValueError('Frozen diagnostic changed')
        fresh=json.loads(args.fresh.read_text());seen=json.loads(args.seen.read_text())
        if fresh['status']!='ASSISTANT_PROPOSED_REFERENCE_NOT_HUMAN_ACCEPTED':raise ValueError('Fresh reference status mismatch')
        bundle_bytes=(args.previous/'reviewed_bundle_frozen.json').read_bytes();bundle=json.loads(bundle_bytes)
        (out/'reviewed_bundle_frozen.json').write_bytes(bundle_bytes)
        (out/'new50_frozen.json').write_bytes(args.fresh.read_bytes())
        (out/'seen74_reference.json').write_bytes(args.seen.read_bytes())
        write(out/'configuration_frozen.json',config);write(out/'asset_lock_frozen.json',lock)
        write(out/'nara_extraction.json',extract_candidate_archive(args.nara_archive,out/'runtime/nara','nara',lock['models']['nara']))
        write(out/'binding.json',{'code_sha256':{str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/'code/active_nara_adapter').glob('*.py'))},
          'configuration_sha256':sha256_file(ROOT/'config'/INTEGRATION_CONFIG),
          'asset_lock_sha256':sha256_file(ROOT/'config'/CANDIDATE_LOCK),'new50_sha256':sha256_file(args.fresh),
          'fresh_references_frozen_before_training':True,'fresh_human_review_completed':False})
        runner=CandidateModelRunner(args.sena_dir,out/'runtime/nara',device='cpu',cpu_threads=2)
        state['models']=runner.model_evidence
        # Reproduce development predictions from the actual exported weights.
        development={}
        for name,filename in [('human','human_development_frozen.json'),('scope','scope_development_frozen.json')]:
            rows=json.loads((args.training_run/filename).read_text())
            expected=json.loads((args.training_run/f'best_{name}_development_predictions.json').read_text())
            probs=[]
            with runner.torch.inference_mode():
                for start in range(0,len(rows),16):
                    encoded=runner.sena_tokenizer([r['text'] for r in rows[start:start+16]],padding=True,truncation=True,max_length=192,return_tensors='pt')
                    probs+=runner.torch.softmax(runner.sena_model(**encoded).logits,-1).tolist()
            guesses=[LABELS[max(range(5),key=lambda i:p[i])] for p in probs]
            expected_guesses=[max(r['probabilities'],key=r['probabilities'].get) for r in expected]
            if guesses!=expected_guesses:raise ValueError('Export changed development labels: '+name)
            max_delta=max(abs(p[i]-r['probabilities'][c]) for p,r in zip(probs,expected) for i,c in enumerate(LABELS))
            if max_delta>1e-5:raise ValueError('Export probability mismatch: '+name)
            actual=score_probs(rows,probs)
            recorded=json.loads((args.training_run/('best_development_metrics.json' if name=='human' else 'best_scope_development_metrics.json')).read_text())
            if actual!=recorded:raise ValueError('Development metrics do not reproduce: '+name)
            development[name]={'metrics':actual,'labels_reproduced':True,'confidence_max_absolute_delta':max_delta}
        write(out/'development_export_verification.json',development)
        state.update(status='INFERENCE',model_inference_executed=True)
        old_predictions=[]
        with (out/'predictions.jsonl').open('x') as stream:
            for i,row in enumerate(bundle['records'],1):
                event,sc=runner.predict_sena(row['text']);tokens,nc=runner.predict_nara(row['text'])
                validate_prediction(event)
                pred=candidate_record(row,event,tokens,config,lock)
                pred.update(nara_tokens=tokens,sena_token_coverage=sc,nara_token_coverage=nc)
                old_predictions.append(pred);stream.write(json.dumps(pred,ensure_ascii=False)+'\n');stream.flush()
                if i%10==0:print('Old pilot',i,'/',len(bundle['records']),flush=True)
        report=score(bundle['records'],old_predictions,bundle['protocol'])
        report.update(scope='SEEN_HUMAN_REVIEWED_PILOT_REGRESSION_NOT_NEW_ACCEPTANCE',
                      quality_acceptance_approved=False,card_done=False,decision='REGRESSION_DIAGNOSTIC_ONLY')
        write(out/'evaluation.json',report)
        summaries={}
        for name,data,scope in [('seen74',seen,'RETIRED_ASSISTANT_REFERENCE_FITTED_DEVELOPMENT'),('new50',fresh,'ONE_SHOT_NEW_ASSISTANT_REFERENCE_DIAGNOSTIC_NOT_HUMAN_ACCEPTANCE')]:
            predictions=[]
            for i,row in enumerate(data['records'],1):
                event,coverage=runner.predict_sena(row['text'])
                if coverage['truncated']:raise ValueError('Diagnostic input truncated: '+row['id'])
                predictions.append({'id':row['id'],'event_classifier':event,'sena_token_coverage':coverage})
                if i%10==0:print(name,i,'/',len(data['records']),flush=True)
            write(out/(name+'_predictions.json'),predictions)
            result=classification(data['records'],predictions)
            result.update(scope=scope,human_reference_reviewed=False,used_for_training_or_checkpoint_selection=(name=='seen74'),
                          quality_acceptance_approved=False,card_done=False)
            result['classification_targets_met']=(result['macro_f1']>=.85 and result['per_class']['NON_EVENT']['recall']>=.90
                 and all(result['per_class'][c]['recall']>=.80 for c in LABELS[:-1]))
            write(out/(name+'_evaluation.json'),result)
            summaries[name]={'accuracy':result['accuracy'],'macro_f1':result['macro_f1'],
                              'non_event_recall':result['per_class']['NON_EVENT']['recall'],
                              'minimum_event_recall':min(result['per_class'][c]['recall'] for c in LABELS[:-1]),
                              'targets_met':result['classification_targets_met'],'errors':len(result['errors'])}
        state.update(status='SUCCEEDED',old_pilot_records=len(old_predictions),seen74_records=len(seen['records']),new50_records=len(fresh['records']),
                     old_pilot_metric_targets_met=report['metric_targets_met'],diagnostic_summary=summaries,
                     environment=environment_snapshot(runner.torch,runner.device))
        print(json.dumps({'old50_targets_met':report['metric_targets_met'],**summaries,'quality_acceptance_approved':False},indent=2),flush=True)
        return state
    except Exception as error:
        state.update(status='FAILED',error={'type':type(error).__name__,'message':str(error)})
        (out/'error_trace.txt').write_text(traceback.format_exc());raise
    finally:
        state['finished_at']=datetime.now(timezone.utc).isoformat();write(out/'run_state.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('previous','seen','fresh','sena-dir','nara-archive','training-run','output'):p.add_argument('--'+key,type=Path,required=True)
    print(json.dumps(run(p.parse_args()),indent=2))
