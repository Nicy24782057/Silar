"""Create a distinct archive/config from a completed development run."""
import argparse,json,zipfile
from pathlib import Path
from train_sena_cpu import sha,write,LABELS
ROOT=Path(__file__).resolve().parents[2]
FILES=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt']
def export(run,out):
 s=json.loads((run/'run_state.json').read_text());assert s['status']=='SUCCEEDED' and s['training_executed']
 selected=json.loads((run/'best_selection.json').read_text());out.mkdir(parents=True,exist_ok=True);p=out/'SILAR_SENA_context_v0.8.1_20261019.zip';assert not p.exists()
 run_id=s['started_at'].split('.')[0].replace('-','').replace(':','');spec={'model_id':'SILAR_SENA_context_v081_'+run_id,'run_id':run_id,'archive_name':p.name,'labels':list(LABELS),'files':{n:sha(run/'best_model'/n) for n in FILES},'selected_epoch':selected['epoch'],'selected_checkpoint_has_this_run_gradient':selected['epoch']>0,'inherited_manual_bias':2.5,'additional_manual_bias':selected['additional_bias'],'training_unique':1249,'human_training':623,'assistant_weak_training':626,'v07_50_used_for_weak_training':True,'human130_never_used_for_training':True,'quality_acceptance_approved':False,'production_model_selected':False}
 with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for n in FILES:z.write(run/'best_model'/n,n)
  z.writestr('experiment_manifest.json',json.dumps(spec,indent=2))
  for f in run.iterdir():
   if f.is_file() and f.suffix in ('.json','.jsonl','.txt','.py'):z.write(f,'development_evidence/'+f.name)
 spec['archive_sha256']=sha(p);write(p.with_suffix('.manifest.json'),spec)
 old=json.loads((ROOT/'config/quality_candidate_asset_lock_v0.8.json').read_text());lock={'schema':'slr09-context-assets-0.8.1','status':'DEVELOPMENT_CANDIDATE_NOT_ACCEPTED','models':{'sena':spec,'nara':old['models']['nara']},'quality_acceptance_approved':False};write(ROOT/'config/quality_candidate_asset_lock_v0.8.1.json',lock)
 c=json.loads((ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.5.json').read_text());c.update(schema='slr09-integration-configuration-0.6',status='DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',calibration_reference=spec['model_id']+':OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',reference_scope='HUMAN130_DEVELOPMENT_AND_KNOWN_REGRESSION_NOT_INDEPENDENT_ACCEPTANCE',confidence_threshold=.95,quality_acceptance_approved=False,production_model_selected=False,production_deployed=False)
 for name,v in lock['models'].items():c[name]={k:v[k] for k in ('archive_name','archive_sha256','run_id','labels')};c[name]['weights_sha256']=v['files']['model.safetensors']
 write(ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.6.json',c)
 for rel in ('code/active_nara_adapter/slr09_candidate_runtime.py','code/tests/test_candidate_runtime.py'):
  f=ROOT/rel;t=f.read_text()
  for old in ('v0.4','v0.5'):t=t.replace('SLR09_Konfigurasi_Integrasi_'+old+'.json','SLR09_Konfigurasi_Integrasi_v0.6.json')
  for old in ('v0.7','v0.8'):t=t.replace('quality_candidate_asset_lock_'+old+'.json','quality_candidate_asset_lock_v0.8.1.json')
  t=t.replace('silar-candidate-runtime-0.6.0','silar-candidate-runtime-0.6.2').replace('silar-candidate-runtime-0.5.0','silar-candidate-runtime-0.6.2');f.write_text(t)
 print(json.dumps({'archive':str(p),'bytes':p.stat().st_size,'sha256':spec['archive_sha256'],'selection':selected},indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.run,a.output)
