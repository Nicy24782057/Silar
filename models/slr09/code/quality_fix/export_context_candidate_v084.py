"""Export the completed v0.8.4 development candidate; preserve all older assets."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import zipfile
from train_sena_cpu import LABELS,sha,write
ROOT=Path(__file__).resolve().parents[2]
FILES=('config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt')


def run():
    import torch
    from safetensors import safe_open
    training=ROOT/'evidence/quality_fix_v084/training29'
    warm=ROOT/'evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run/runtime/sena'
    state=json.loads((training/'run_state.json').read_text());best=json.loads((training/'best_selection.json').read_text());cfg=json.loads((training/'training_config.json').read_text())
    assert state['status']=='SUCCEEDED' and state['training_executed'] and best['feasible']
    old=json.loads((ROOT/'config/quality_candidate_asset_lock_v0.8.3.json').read_text())
    assert sha(warm/'model.safetensors')==old['models']['sena']['files']['model.safetensors']
    changed=[];unchanged=[]
    with safe_open(warm/'model.safetensors',framework='pt',device='cpu') as before,safe_open(training/'best_model/model.safetensors',framework='pt',device='cpu') as after:
        assert set(before.keys())==set(after.keys())
        for key in before.keys():
            (unchanged if torch.equal(before.get_tensor(key),after.get_tensor(key)) else changed).append(key)
    allowed=('bert.encoder.layer.11.','bert.pooler.','classifier.')
    assert changed and all(k.startswith(allowed) for k in changed)
    write(training/'weight_update_boundary.json',dict(status='SUCCEEDED',changed_tensors=changed,unchanged_tensor_count=len(unchanged),frozen_layers_bit_identical=True,allowed_prefixes=allowed))
    stamp=datetime.fromisoformat(state['started_at']);run_id=stamp.strftime('%Y%m%dT%H%M%SZ')
    out=ROOT.parents[2]/'silar_delivery_v084_20261020';out.mkdir(parents=True,exist_ok=True)
    archive=out/f'SILAR_SENA_context_v0.8.4_{stamp:%Y%m%d}.zip'
    train=json.loads((training/'training_records_frozen.json').read_text())
    spec=dict(model_id='SILAR_SENA_context_v084_'+run_id,run_id=run_id,archive_name=archive.name,
        labels=list(LABELS),files={n:sha(training/'best_model'/n) for n in FILES},selected_epoch=best['epoch'],
        trainable_modules=cfg['trainable'],training_unique=len(train),training_origins=dict(Counter(x['label_origin'] for x in train)),
        training_draws_per_epoch=cfg['draws_per_epoch'],gradient_method=cfg['gradient_method'],
        warm_start_archive_sha256=old['models']['sena']['archive_sha256'],
        FINAL081_FINAL082_FINAL083_retired_to_training_and_seen_regression=True,
        new_gradient_training_executed=True,new_manual_bias_fit_executed=False,
        quality_acceptance_approved=False,production_model_selected=False,independent_acceptance_test_executed=False)
    assert spec['files']['model.safetensors']!=old['models']['sena']['files']['model.safetensors']
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n in FILES:z.write(training/'best_model'/n,n)
        z.writestr('experiment_manifest.json',json.dumps(spec,indent=2)+'\n')
        for p in sorted(training.iterdir()):
            if p.is_file() and p.suffix in {'.json','.jsonl','.txt','.py'}:z.write(p,'development_evidence/'+p.name)
    spec['archive_sha256']=sha(archive);write(archive.with_suffix('.manifest.json'),spec)
    lock=dict(schema='slr09-context-assets-0.8.4',status='DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
              models={'sena':spec,'nara':deepcopy(old['models']['nara'])},quality_acceptance_approved=False,
              pipeline_revision='0.8.4',nara_weights_unchanged=True,new_gradient_training_executed=True)
    write(ROOT/'config/quality_candidate_asset_lock_v0.8.4.json',lock)
    integration=json.loads((ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.8.json').read_text())
    integration.update(schema='slr09-integration-configuration-0.9',pipeline_revision='0.8.4',
        adapter_version='silar-adapter-0.5.3',postprocessing_version='silar-postprocessing-0.3.1',
        confidence_threshold=.95,reference_run_id=run_id,reference_report_sha256=sha(training/'best_selection.json'),
        reference_scope='ALL_KNOWN_REFERENCES_NOW_TRAINING_OR_SEEN_SELECTION_NOT_ACCEPTANCE',
        calibration_reference=spec['model_id']+':OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',
        previous_configuration_preserved='config/SLR09_Konfigurasi_Integrasi_v0.8.json',
        new_gradient_training_executed=True,probability_calibration_fitted=False)
    for name,model in lock['models'].items():
        integration[name]={k:model[k] for k in ['archive_name','archive_sha256','run_id','labels']}
        integration[name]['weights_sha256']=model['files']['model.safetensors']
    write(ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.9.json',integration)
    runtime=ROOT/'code/active_nara_adapter/slr09_candidate_runtime.py'
    text=runtime.read_text().replace('SLR09_Konfigurasi_Integrasi_v0.8.json','SLR09_Konfigurasi_Integrasi_v0.9.json').replace('quality_candidate_asset_lock_v0.8.3.json','quality_candidate_asset_lock_v0.8.4.json').replace('silar-candidate-runtime-0.6.4','silar-candidate-runtime-0.6.5')
    runtime.write_text(text)
    write(ROOT/'evidence/quality_fix_v084/candidate_export.json',dict(status='SUCCEEDED',archive=str(archive),
          archive_sha256=spec['archive_sha256'],bytes=archive.stat().st_size,model_id=spec['model_id'],selected_epoch=best['epoch'],
          changed_tensors=len(changed),unchanged_tensors=len(unchanged),quality_acceptance_approved=False,card_done=False))
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=spec['archive_sha256'],
          changed_tensors=len(changed),unchanged_tensors=len(unchanged)),indent=2))


if __name__=='__main__':run()
