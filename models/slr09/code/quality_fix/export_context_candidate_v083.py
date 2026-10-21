"""Export a feasible v0.8.3 development checkpoint, preserving prior candidates."""
import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import zipfile

from train_sena_cpu import LABELS, sha, write

ROOT = Path(__file__).resolve().parents[2]
FILES = ('config.json', 'model.safetensors', 'tokenizer.json',
         'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt')


def export(run, output, warm_start):
    state = json.loads((run / 'run_state.json').read_text())
    selection = json.loads((run / 'best_selection.json').read_text())
    config = json.loads((run / 'training_config.json').read_text())
    if not (state['status'] == 'SUCCEEDED' and state['training_executed']
            and selection['feasible'] and state['all_known_constraints_met']):
        raise ValueError('Only a completed, feasible development candidate can be exported')
    stamp = datetime.fromisoformat(state['started_at'])
    run_id = stamp.strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'SILAR_SENA_context_v0.8.3_{stamp:%Y%m%d}.zip'
    previous = json.loads((ROOT / 'config/quality_candidate_asset_lock_v0.8.2.json').read_text())
    if sha(warm_start / 'model.safetensors') != previous['models']['sena']['files']['model.safetensors']:
        raise ValueError('Warm-start weight identity differs from the original candidate')
    from safetensors import safe_open
    import torch
    changed, unchanged = [], []
    with safe_open(warm_start / 'model.safetensors', framework='pt', device='cpu') as before, \
            safe_open(run / 'best_model/model.safetensors', framework='pt', device='cpu') as after:
        if set(before.keys()) != set(after.keys()):
            raise ValueError('Training changed the weight tensor structure')
        for key in before.keys():
            (unchanged if torch.equal(before.get_tensor(key), after.get_tensor(key)) else changed).append(key)
    allowed = ('bert.encoder.layer.11.', 'bert.pooler.', 'classifier.')
    if not changed or any(not key.startswith(allowed) for key in changed):
        raise ValueError('Gradient updates occurred outside the declared trainable modules')
    write(run / 'weight_update_boundary.json', dict(
        status='SUCCEEDED', changed_tensors=changed, unchanged_tensor_count=len(unchanged),
        allowed_prefixes=list(allowed), frozen_layers_bit_identical=True,
        warm_start_weight_sha256=sha(warm_start / 'model.safetensors')))
    spec = {
        'model_id': 'SILAR_SENA_context_v083_' + run_id,
        'run_id': run_id, 'archive_name': archive.name, 'labels': list(LABELS),
        'files': {name: sha(run / 'best_model' / name) for name in FILES},
        'selected_epoch': selection['epoch'],
        'trainable_modules': config['trainable'],
        'training_unique': state['training_unique'],
        'training_origins': state['training_origins'],
        'training_draws_per_epoch': config.get('draws_per_epoch', state['training_unique']),
        'gradient_method': config.get('gradient_method', 'FULL_FORWARD_LAST_BLOCK_BACKPROP'),
        'warm_start_archive_sha256': previous['models']['sena']['archive_sha256'],
        'human130_never_used_for_training': False,
        'human130_now_training_and_seen_selection': True,
        'FINAL081_FINAL082_retired_to_training_and_seen_regression': True,
        'new_gradient_training_executed': True,
        'new_manual_bias_fit_executed': False,
        'quality_acceptance_approved': False, 'production_model_selected': False,
        'independent_acceptance_test_executed': False,
    }
    if spec['files']['model.safetensors'] == previous['models']['sena']['files']['model.safetensors']:
        raise ValueError('The exported model must contain the new gradient updates')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for name in FILES:
            z.write(run / 'best_model' / name, name)
        z.writestr('experiment_manifest.json', json.dumps(spec, indent=2) + '\n')
        for p in sorted(run.iterdir()):
            if p.is_file() and p.suffix in {'.json', '.jsonl', '.txt', '.py'}:
                z.write(p, 'development_evidence/' + p.name)
    spec['archive_sha256'] = sha(archive)
    write(archive.with_suffix('.manifest.json'), spec)
    lock = {'schema': 'slr09-context-assets-0.8.3',
            'status': 'DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
            'models': {'sena': spec, 'nara': previous['models']['nara']},
            'quality_acceptance_approved': False, 'pipeline_revision': '0.8.3',
            'nara_weights_unchanged': True, 'new_gradient_training_executed': True}
    write(ROOT / 'config/quality_candidate_asset_lock_v0.8.3.json', lock)
    integration = json.loads((ROOT / 'config/SLR09_Konfigurasi_Integrasi_v0.7.json').read_text())
    integration.update(schema='slr09-integration-configuration-0.8',
        pipeline_revision='0.8.3', weights_unchanged=False,
        confidence_threshold=.95,
        reference_run_id=run_id,
        reference_report_sha256=sha(run / 'best_selection.json'),
        reference_scope='ALL_KNOWN_REFERENCES_NOW_TRAINING_OR_SEEN_SELECTION_NOT_ACCEPTANCE',
        selection_basis='KNOWN_DEVELOPMENT_CONSTRAINTS_LAST_ENCODER_BLOCK_GRADIENT_TRAINING',
        calibration_reference=spec['model_id'] + ':OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',
        previous_configuration_preserved='config/SLR09_Konfigurasi_Integrasi_v0.7.json',
        new_gradient_training_executed=True)
    integration.pop('non_event_head_bias_fitted_on_development', None)
    for name, model in lock['models'].items():
        integration[name] = {k: model[k] for k in ('archive_name', 'archive_sha256', 'run_id', 'labels')}
        integration[name]['weights_sha256'] = model['files']['model.safetensors']
    write(ROOT / 'config/SLR09_Konfigurasi_Integrasi_v0.8.json', integration)
    # Only candidate selection references change; SENA/Fusion/adapter logic stays intact.
    for relative in ('code/active_nara_adapter/slr09_candidate_runtime.py',
                     'code/tests/test_candidate_runtime.py'):
        p = ROOT / relative
        text = p.read_text().replace('SLR09_Konfigurasi_Integrasi_v0.7.json',
                                    'SLR09_Konfigurasi_Integrasi_v0.8.json')
        text = text.replace('quality_candidate_asset_lock_v0.8.2.json',
                            'quality_candidate_asset_lock_v0.8.3.json')
        text = text.replace('silar-candidate-runtime-0.6.3', 'silar-candidate-runtime-0.6.4')
        p.write_text(text)
    write(ROOT / 'evidence/quality_fix_v083/candidate_export.json', {
        'status': 'SUCCEEDED', 'archive_name': archive.name,
        'archive_sha256': spec['archive_sha256'], 'bytes': archive.stat().st_size,
        'model_id': spec['model_id'], 'selected_epoch': selection['epoch'],
        'quality_acceptance_approved': False, 'card_done': False})
    print(json.dumps({'archive': str(archive), 'model_id': spec['model_id'],
                      'bytes': archive.stat().st_size, 'selected_epoch': selection['epoch']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--warm-start', type=Path, required=True)
    args = parser.parse_args()
    export(args.run.resolve(), args.output.resolve(), args.warm_start.resolve())
