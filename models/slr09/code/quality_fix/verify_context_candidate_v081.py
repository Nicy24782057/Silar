"""Verify exported archives against known development/regression only."""
import argparse,json,sys,traceback,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'code/active_nara_adapter'),str(ROOT/'code/acceptance')]
from slr09_candidate_runtime import CandidateModelRunner,candidate_record,selected_assets,extract_candidate_archive,INTEGRATION_CONFIG,CANDIDATE_LOCK
from slr09_runtime import sha256_file,environment_snapshot
from evaluate_acceptance import score,classification,write
from train_sena_cpu import LABELS
from train_scope_sena_v06 import score_probs

def run(a):
 out=a.output;out.mkdir(parents=True,exist_ok=False)
 state={'schema':'slr09-export-verification-0.8.1','status':'PREPARING','started_at':datetime.now(timezone.utc).isoformat(),'model_inference_executed':False,'new_final_reference_inferred':False,'quality_acceptance_approved':False,'card_done':False}
 write(out/'run_state.json',state)
 try:
  config,lock,_=selected_assets();write(out/'config_frozen.json',config);write(out/'lock_frozen.json',lock)
  snap=out/'snapshot'
  for f in list((ROOT/'code/active_nara_adapter').glob('*.py'))+[ROOT/'config'/INTEGRATION_CONFIG,ROOT/'config'/CANDIDATE_LOCK,ROOT/'config/inference_environment.json']:
   p=snap/f.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,p)
  ext={}
  for name,p in [('sena',a.sena_archive),('nara',a.nara_archive)]:ext[name]=extract_candidate_archive(p,out/'runtime'/name,name,lock['models'][name])
  write(out/'archive_extraction.json',ext)
  runner=CandidateModelRunner(out/'runtime/sena',out/'runtime/nara',device='cpu',cpu_threads=2);state['models']=runner.model_evidence
  if a.training_run:
   metrics={};verification={}
   for name in ('human130','original146','adjudicated145','scope50','seen_v07_50','human_regression50'):
    rows=json.loads((a.training_run/f'frozen_{name}.json').read_text());expected=json.loads((a.training_run/f'predictions_{name}.json').read_text());probs=[]
    with runner.torch.inference_mode():
     for i in range(0,len(rows),16):
      x=runner.sena_tokenizer([r['text'] for r in rows[i:i+16]],padding=True,truncation=True,max_length=192,return_tensors='pt');probs+=runner.torch.softmax(runner.sena_model(**x).logits,-1).tolist()
    guesses=[LABELS[max(range(5),key=lambda j:p[j])] for p in probs];assert guesses==[max(r['probabilities'],key=r['probabilities'].get) for r in expected],name
    delta=max(abs(p[i]-r['probabilities'][c]) for p,r in zip(probs,expected) for i,c in enumerate(LABELS));assert delta<=1e-5,(name,delta)
    metrics[name]=score_probs(rows,probs);verification[name]={'labels_identical':True,'max_probability_delta':delta}
   assert metrics==json.loads((a.training_run/'metrics.json').read_text())
   write(out/'development_metrics_reproduced.json',metrics);write(out/'development_verification.json',verification)
  bundle=json.loads((ROOT/'evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json').read_text());write(out/'human_regression_reference.json',bundle);pred=[]
  state['model_inference_executed']=True
  with (out/'predictions.jsonl').open('x') as f:
   for i,row in enumerate(bundle['records'],1):
    event,sc=runner.predict_sena(row['text']);tokens,nc=runner.predict_nara(row['text']);p=candidate_record(row,event,tokens,config,lock);p.update(nara_tokens=tokens,sena_token_coverage=sc,nara_token_coverage=nc);pred.append(p);f.write(json.dumps(p,ensure_ascii=False)+'\n');f.flush()
    if i%10==0:print('Known human regression',i,'/50',flush=True)
  report=score(bundle['records'],pred,bundle['protocol']);report.update(scope='KNOWN_HUMAN_REGRESSION_NOT_FINAL_ACCEPTANCE',quality_acceptance_approved=False,card_done=False);write(out/'evaluation.json',report)
  seen=json.loads((ROOT/'data/frozen_new_diagnostic_v0.7.json').read_text());vp=[]
  for row in seen['records']:
   event,coverage=runner.predict_sena(row['text']);assert not coverage['truncated'];vp.append({'id':row['id'],'event_classifier':event,'sena_token_coverage':coverage})
  v=classification(seen['records'],vp);v.update(scope='ASSISTANT_REFERENCE_ALREADY_SEEN_NOT_HUMAN_ACCEPTANCE',used_for_current_weak_training=bool(a.training_run),quality_acceptance_approved=False)
  write(out/'v07_seen_predictions.json',vp);write(out/'v07_seen_evaluation.json',v)
  state.update(status='SUCCEEDED',human_regression_targets_met=report['metric_targets_met'],environment=environment_snapshot(runner.torch,runner.device))
  print(json.dumps({'old_human50_targets':report['metric_targets_met'],'old_human50_sena':report['sena']['macro_f1'],'v07_seen_flood':v['per_class']['FLOOD']['recall'],'quality_acceptance_approved':False},indent=2))
 except Exception as e:state.update(status='FAILED',error=str(e));(out/'error_trace.txt').write_text(traceback.format_exc());raise
 finally:state['finished_at']=datetime.now(timezone.utc).isoformat();write(out/'run_state.json',state)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('sena-archive','nara-archive','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--training-run',type=Path);run(p.parse_args())
