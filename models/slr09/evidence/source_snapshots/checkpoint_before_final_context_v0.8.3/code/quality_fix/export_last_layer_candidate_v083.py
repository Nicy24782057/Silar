"""Export a completed v0.8.3 development run without accepting it for production.

The old lock/config and original frozen evidence are retained. All selection
sets are seen training/development; only a later reviewed reference can support
a new acceptance run.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import zipfile

from train_sena_cpu import LABELS, sha, write

ROOT = Path(__file__).resolve().parents[2]
FILES = ('config.json', 'model.safetensors', 'tokenizer.json',
         'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt')


def load(path):
    return json.loads(Path(path).read_text())


def diagnostic_checkpoint(run, output):
    """Retain expensive failed-run weights without modifying candidate selectors."""
    state = load(run / 'run_state.json')
    selected = load(run / 'best_selection.json')
    if not state['training_executed'] or state.get('all_known_constraints_met') is True:
        raise ValueError('Diagnostic-only export requires completed unsuccessful training')
    if state['status'] not in {'FAILED', 'NO_FEASIBLE_CANDIDATE'}:
        raise ValueError('The unsuccessful run must have finished')
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(state['started_at'])
    archive = output / ('SILAR_SENA_diagnostic_v0.8.3_' + stamp.strftime('%Y%m%d') + '.zip')
    if archive.exists():
        raise ValueError('Do not overwrite diagnostic evidence')
    metadata = dict(
        schema='slr09-unsuccessful-training-checkpoint-0.8.3',
        status='DIAGNOSTIC_ONLY_NO_FEASIBLE_CANDIDATE',
        run_id=stamp.strftime('%Y%m%dT%H%M%S_%fZ'),
        selected_diagnostic_epoch=selected['epoch'],
        labels=list(LABELS), files={name: sha(run / 'best_model' / name) for name in FILES},
        training_executed=True, all_existing_references_are_training_or_development=True,
        human130_now_used_for_training=True, FINAL081_FINAL082_used_for_training=True,
        independent_acceptance_test_executed=False, confidence_threshold_unchanged=0.95,
        known_regression_constraints_met=False, candidate_selector_updated=False,
        quality_acceptance_approved=False, production_model_selected=False,
        card_done=False, production_deployed=False)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for name in FILES:
            z.write(run / 'best_model' / name, name)
        z.writestr('experiment_manifest.json', json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        for path in sorted(run.iterdir()):
            if path.is_file() and path.suffix in {'.json', '.jsonl', '.txt', '.py', '.log'}:
                z.write(path, 'development_evidence/' + path.name)
    metadata.update(archive_name=archive.name, archive_sha256=sha(archive), archive_bytes=archive.stat().st_size)
    write(archive.with_suffix('.manifest.json'), metadata)
    write(ROOT / 'evidence/quality_fix_v083/diagnostic_export_manifest.json', metadata)
    print(json.dumps(metadata, indent=2), flush=True)


def export(run, output):
    state = load(run / 'run_state.json')
    selected = load(run / 'best_selection.json')
    training = load(run / 'training_records_frozen.json')
    if not (state['status'] == 'SUCCEEDED' and state['training_executed']
            and state['all_known_constraints_met'] and selected['feasible']):
        raise ValueError('Only a completed feasible development candidate can be exported')
    prior = load(ROOT / 'config/quality_candidate_asset_lock_v0.8.2.json')
    hashes = {name: sha(run / 'best_model' / name) for name in FILES}
    if hashes['model.safetensors'] == prior['models']['sena']['files']['model.safetensors']:
        raise ValueError('Expected a distinct model after actual gradient training')
    stamp = datetime.fromisoformat(state['started_at'])
    run_id = stamp.strftime('%Y%m%dT%H%M%S_%fZ')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / ('SILAR_SENA_context_v0.8.3_' + stamp.strftime('%Y%m%d') + '.zip')
    if archive.exists():
        raise ValueError('Preserve the previous export; choose a new output directory')
    spec = {
        'model_id': 'SILAR_SENA_context_v083_' + run_id,
        'run_id': run_id, 'archive_name': archive.name,
        'labels': list(LABELS), 'files': hashes,
        'selected_epoch': selected['epoch'],
        'actual_gradient_training_executed': True,
        'trainable': 'LAST_ENCODER_BLOCK_POOLER_CLASSIFIER',
        'training_unique': len(training),
        'training_origins': dict(Counter(r['label_origin'] for r in training)),
        'warm_start_model_id': prior['models']['sena']['model_id'],
        'warm_start_archive_sha256': prior['models']['sena']['archive_sha256'],
        'inherited_manual_bias_history': {
            k: prior['models']['sena'][k]
            for k in ('inherited_manual_bias', 'additional_manual_bias')},
        'additional_manual_intercept_adjustment_this_run': 0.0,
        'classifier_bias_updated_by_gradient': True,
        'human130_now_used_for_training': True,
        'FINAL081_FINAL082_used_for_training': True,
        'all_scoring_sets_are_seen_training_or_development': True,
        'independent_acceptance_test_executed': False,
        'known_regression_constraints_met': True,
        'confidence_threshold_unchanged': 0.95,
        'probability_calibration_established': False,
        'quality_acceptance_approved': False,
        'production_model_selected': False,
    }
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for name in FILES:
            z.write(run / 'best_model' / name, name)
        z.writestr('experiment_manifest.json', json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
        for path in sorted(run.iterdir()):
            if path.is_file() and path.suffix in {'.json', '.jsonl', '.txt', '.py', '.log'}:
                z.write(path, 'development_evidence/' + path.name)
    spec['archive_sha256'] = sha(archive)
    write(archive.with_suffix('.manifest.json'), spec)
    lock = {
        'schema': 'slr09-context-assets-0.8.3',
        'status': 'DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
        'models': {'sena': spec, 'nara': deepcopy(prior['models']['nara'])},
        'pipeline_revision': '0.8.3',
        'new_gradient_training_executed': True,
        'nara_weights_unchanged': True,
        'quality_acceptance_approved': False,
    }
    config = load(ROOT / 'config/SLR09_Konfigurasi_Integrasi_v0.7.json')
    config.update(
        schema='slr09-integration-configuration-0.8',
        status='DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
        pipeline_revision='0.8.3', weights_unchanged=False,
        reference_run_id=run_id,
        reference_report_sha256=sha(run / 'best_selection.json'),
        reference_scope='SEEN_TRAINING_AND_DEVELOPMENT_NOT_INDEPENDENT_ACCEPTANCE',
        calibration_reference=spec['model_id'] + ':OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',
        previous_configuration_preserved='config/SLR09_Konfigurasi_Integrasi_v0.7.json',
        confidence_threshold=0.95, quality_acceptance_approved=False,
        production_model_selected=False, production_deployed=False,
        new_gradient_training_executed=True,
        non_event_intercept_adjustment_this_run=0.0)
    config.pop('non_event_head_bias_fitted_on_development', None)
    for name, model in lock['models'].items():
        config[name] = {key: model[key] for key in ('archive_name', 'archive_sha256', 'run_id', 'labels')}
        config[name]['weights_sha256'] = model['files']['model.safetensors']
    write(ROOT / 'config/quality_candidate_asset_lock_v0.8.3.json', lock)
    write(ROOT / 'config/SLR09_Konfigurasi_Integrasi_v0.8.json', config)
    snapshot = ROOT / 'evidence/quality_fix_v083/pre_export_source'
    snapshot.mkdir(parents=True, exist_ok=False)
    path = ROOT / 'code/active_nara_adapter/slr09_candidate_runtime.py'
    shutil.copy2(path, snapshot / path.name)
    source = path.read_text()
    for old, new in (
        ('silar-candidate-runtime-0.6.3', 'silar-candidate-runtime-0.6.4'),
        ('SLR09_Konfigurasi_Integrasi_v0.7.json', 'SLR09_Konfigurasi_Integrasi_v0.8.json'),
        ('quality_candidate_asset_lock_v0.8.2.json', 'quality_candidate_asset_lock_v0.8.3.json')):
        if source.count(old) != 1:
            raise ValueError('Unexpected runtime selector: ' + old)
        source = source.replace(old, new)
    path.write_text(source)
    evidence = {
        'status': 'SUCCEEDED', 'at_utc': datetime.now(timezone.utc).isoformat(),
        'run': run.relative_to(ROOT).as_posix(),
        'archive_name': archive.name, 'archive_bytes': archive.stat().st_size,
        'archive_sha256': spec['archive_sha256'],
        'selected_epoch': selected['epoch'],
        'source_files_verified': hashes,
        'nara_archive_unchanged': True,
        'threshold_unchanged': 0.95,
        'default_selector_scope': 'LOCAL_DEVELOPMENT_PACKAGE_ONLY',
        'new_independent_acceptance_executed': False,
        'quality_acceptance_approved': False, 'card_done': False,
        'remote_push_executed': False, 'production_deployed': False,
    }
    write(ROOT / 'evidence/quality_fix_v083/export_manifest.json', evidence)
    print(json.dumps(evidence, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diagnostic-only', action='store_true')
    arguments = parser.parse_args()
    action = diagnostic_checkpoint if arguments.diagnostic_only else export
    action(arguments.run.resolve(), arguments.output.resolve())
