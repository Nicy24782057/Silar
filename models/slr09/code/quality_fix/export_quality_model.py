"""Export only safetensors runtime files with explicit development provenance."""
import argparse
import json
from pathlib import Path
import zipfile
from train_sena_cpu import sha, write, LABELS

FILES=('config.json','model.safetensors','tokenizer.json','tokenizer_config.json',
       'special_tokens_map.json','vocab.txt')


def export(run_dir, output, model_id, run_id):
    state=json.loads((run_dir/'run_state.json').read_text())
    if state['status']!='SUCCEEDED' or not (state['training_executed'] or state.get('parameter_fit_executed')):
        raise ValueError('Cannot export an unfinished training run')
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('Use a new archive path')
    spec={'model_id':model_id,'run_id':run_id,'archive_name':output.name,
          'labels':list(LABELS),'files':{name:sha(run_dir/'best_model'/name) for name in FILES},
          'origin':state['source'],'selection_scope':'DEVELOPMENT_VALIDATION_NOT_ACCEPTANCE',
          'quality_acceptance_approved':False,'production_model_selected':False}
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for name in FILES:
            archive.write(run_dir/'best_model'/name,name)
        archive.writestr('experiment_manifest.json',json.dumps(spec,ensure_ascii=False,indent=2))
        for name in ('run_state.json','training_config.json','development_split.json',
                     'training_auxiliary.json','training_history.json',
                     'best_development_metrics.json','baseline_development_metrics.json',
                     'warm_start_identity.json','development_bias_grid.json'):
            if (run_dir/name).exists():archive.write(run_dir/name,'development_evidence/'+name)
    spec['archive_sha256']=sha(output)
    write(output.with_suffix('.manifest.json'),spec)
    print(json.dumps({'archive':str(output),'bytes':output.stat().st_size,
                      'sha256':spec['archive_sha256'],'model_id':model_id},indent=2),flush=True)
    return spec


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model-id',required=True)
    p.add_argument('--run-id',required=True)
    a=p.parse_args();export(a.run_dir,a.output,a.model_id,a.run_id)
