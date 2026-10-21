"""Export a separately identified development candidate from a completed run."""
import argparse
import json
from pathlib import Path
import zipfile
from train_sena_cpu import LABELS,sha,write
ROOT=Path(__file__).resolve().parents[2]
FILES=('config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt')


def prepare(run,output):
    state=json.loads((run/'run_state.json').read_text())
    if state['status']!='SUCCEEDED' or not (state['training_executed'] or state.get('parameter_fit_executed')):raise ValueError('Training or development parameter fit is not complete')
    selection=json.loads((run/'best_selection.json').read_text())
    run_id=state['started_at'].split('.')[0].replace('-','').replace(':','')
    archive=output/'SILAR_SENA_scope_v0.6_20261019.zip'
    output.mkdir(parents=True,exist_ok=True)
    if archive.exists():raise ValueError('Use a new model archive path')
    spec={'model_id':'SILAR_SENA_scope_v06_'+run_id,'run_id':run_id,'archive_name':archive.name,
          'labels':list(LABELS),'files':{name:sha(run/'best_model'/name) for name in FILES},
          'origin':state['source'],'selected_epoch':selection['epoch'],
          'non_event_head_bias':selection['bias'],'selection_data':'HUMAN146_AND_ASSISTANT_SCOPE128_DEVELOPMENT',
          'auxiliary_human_review_completed':False,'new50_used_for_training_or_selection':False,
          'quality_acceptance_approved':False,'production_model_selected':False}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for name in FILES:z.write(run/'best_model'/name,name)
        z.writestr('experiment_manifest.json',json.dumps(spec,ensure_ascii=False,indent=2))
        for p in sorted(run.iterdir()):
            if p.is_file() and p.suffix in {'.json','.txt'}:z.write(p,'development_evidence/'+p.name)
    spec['archive_sha256']=sha(archive)
    write(archive.with_suffix('.manifest.json'),spec)
    previous=json.loads((ROOT/'config/quality_candidate_asset_lock_v0.5.json').read_text())
    lock={'schema':'slr09-scope-candidate-assets-0.6','status':'DEVELOPMENT_NOT_HUMAN_ACCEPTED',
          'models':{'sena':spec,'nara':previous['models']['nara']},
          'previous_v05_lock_preserved':True,'quality_acceptance_approved':False}
    write(ROOT/'config/quality_candidate_asset_lock_v0.6.json',lock)
    config=json.loads((ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.2.json').read_text())
    config.update(schema='slr09-integration-configuration-0.3',status='DEVELOPMENT_CANDIDATE_NOT_HUMAN_ACCEPTED',
                  calibration_reference=spec['model_id']+':USER_OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',
                  reference_run_id=run_id,reference_report_sha256=sha(run/'best_selection.json'),
                  reference_scope='FITTED_DEVELOPMENT_HUMAN146_AND_ASSISTANT128_NOT_INDEPENDENT_TEST',
                  selection_basis='PRIOR_USER_CUTOFF_UNCHANGED_MODEL_AND_INTERCEPT_SELECTED_ON_DEVELOPMENT',
                  non_event_head_bias_fitted_on_development=selection['bias'],
                  previous_configuration_preserved='config/SLR09_Konfigurasi_Integrasi_v0.2.json',
                  auxiliary_human_review_completed=False,quality_acceptance_approved=False,
                  production_model_selected=False,production_deployed=False)
    for name,model in lock['models'].items():
        config[name]={key:model[key] for key in ('archive_name','archive_sha256','run_id','labels')}
        config[name].update(weights_sha256=model['files']['model.safetensors'],weight_identity_source='DIRECT_LOCAL_RUNTIME_HASH_VERIFICATION')
    write(ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.3.json',config)
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':spec['archive_sha256'],
                      'model_id':spec['model_id'],'selected_epoch':selection['epoch'],'selected_bias':selection['bias'],
                      'quality_acceptance_approved':False},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.run,a.output)
