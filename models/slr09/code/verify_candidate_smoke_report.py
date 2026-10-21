"""Verifikasi bukti smoke tersimpan; tidak menjalankan training/inferensi."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code/active_nara_adapter'))
from silar_ai_adapter import EXTRACTION_FIELDS
from slr09_runtime import validate_prediction


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(report, source_package=None):
    report = Path(report)
    checks = []
    def require(name, condition):
        if not condition:
            raise ValueError('Bukti tidak cocok: ' + name)
        checks.append({'name': name, 'passed': True})
    read = lambda name: json.loads((report / name).read_text())
    workflow, summary = read('workflow_result.json'), read('smoke/run_summary.json')
    config, lock = read('SLR09_Konfigurasi_Integrasi_v0.1.json'), read('candidate_asset_lock.json')
    extraction, snapshot = read('extraction_evidence.json'), read('source_snapshot.json')
    current = json.loads((ROOT / 'config/SLR09_Konfigurasi_Integrasi_v0.1.json').read_text())
    require('workflow_and_runtime_succeeded', workflow['status'] == summary['status'] == 'SUCCEEDED')
    require('no_training_reported', not workflow['training_executed'] and not summary['training_executed'])
    require('scope_consistent_representative', workflow['environment_scope'] == summary['environment_scope'] == 'REPRESENTATIVE')
    require('inference_and_fusion_executed', all(summary[k] for k in ['model_inference_executed', 'sena_inference_executed', 'nara_inference_executed', 'fusion_executed']))
    require('input_hash', summary['input_sha256'] == digest(report / 'smoke_inputs.jsonl'))
    require('prediction_hash', summary['predictions_sha256'] == digest(report / 'smoke/predictions.jsonl'))
    require('configuration_hash', summary['configuration_sha256'] == digest(report / 'SLR09_Konfigurasi_Integrasi_v0.1.json'))
    require('candidate_lock_hash', summary['candidate_lock_sha256'] == digest(report / 'candidate_asset_lock.json'))
    require('selected_configuration_unchanged', config == current)
    require('threshold_095', summary['confidence_threshold'] == config['confidence_threshold'] == .95)
    versions, profile = read('dependency_versions.json'), read('inference_environment.json')
    require('dependency_versions_match_profile', all(versions[k].split('+', 1)[0] == profile['pinned_packages'][k] for k in profile['guard_packages']))
    require('dependency_versions_match_runtime', all(versions[k] == summary['environment']['packages'][k] for k in profile['guard_packages']))
    for name in ['sena', 'nara']:
        spec, observed, loaded = lock['models'][name], extraction[name], summary['models'][name]
        require(name + '_archive_hash', observed['archive_sha256_observed'] == spec['archive_sha256'] == config[name]['archive_sha256'])
        require(name + '_runtime_file_hashes', observed['files'] == loaded['files'] == spec['files'])
        require(name + '_selected_weights', loaded['files']['model.safetensors'] == config[name]['weights_sha256'])
        require(name + '_label_order', observed['labels'] == loaded['labels'] == config[name]['labels'])
        require(name + '_identity', loaded['model_id'] == observed['model_id'] == spec['model_id'] and loaded['run_id'] == spec['run_id'] == config[name]['run_id'])
    if source_package is not None:
        source_package = Path(source_package)
        require('source_package_identity', digest(source_package) == snapshot['source_package_sha256'])
        with zipfile.ZipFile(source_package) as archive:
            payload = {name: archive.read(name).decode() for name in snapshot['files_sha256']}
            require('all_source_snapshot_files_match', all(hashlib.sha256(value.encode()).hexdigest() == snapshot['files_sha256'][name] for name, value in payload.items()))
            bundle = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            require('source_bundle_identity', bundle == snapshot['bundle_sha256'] == workflow['source_bundle_sha256'])
    inputs = [json.loads(line) for line in (report / 'smoke_inputs.jsonl').read_text().splitlines() if line.strip()]
    predictions = [json.loads(line) for line in (report / 'smoke/predictions.jsonl').read_text().splitlines() if line.strip()]
    require('record_counts', len(predictions) == len(inputs) == summary['records_expected'] == summary['records_completed'] == workflow['records_completed'])
    require('record_ids_exactly_match', len({r['id'] for r in predictions}) == len(inputs) and {r['id'] for r in inputs} == {r['id'] for r in predictions})
    input_by_id = {row['id']: row for row in inputs}
    diagnostic_rows = []
    for row in predictions:
        key, event = row['id'], row['event_classifier']
        validate_prediction(event)
        require(key + '_input_identity', row['input_sha256'] == hashlib.sha256(input_by_id[key]['text'].encode()).hexdigest())
        adapted, fusion = row['adapted_result'], row['fusion_result']
        card = fusion['incident_card_version_fields']
        require(key + '_seven_and_eight_fields', set(adapted['nara_result']['normalized_output']) == set(EXTRACTION_FIELDS) and set(card['data']) == set(EXTRACTION_FIELDS) | {'event_type'})
        require(key + '_category_and_block_signal', card['data']['event_type'] == (None if event['label'] == 'NON_EVENT' else event['label']) and fusion['integration_signals']['blocked_by_non_event'] is (event['label'] == 'NON_EVENT'))
        expected_reasons = ['LOW_CLASSIFICATION_CONFIDENCE'] if event['confidence'] < config['confidence_threshold'] else []
        require(key + '_uncertainty_rule', card['uncertain_reasons'] == expected_reasons and card['uncertain'] is bool(expected_reasons))
        require(key + '_candidate_output_versions', all(adapted[name + '_result']['model_version'] == lock['models'][name]['model_id'] + '|' + config['adapter_version'] for name in ['sena', 'nara']))
        diagnostic_rows.append({'id': key, 'text': input_by_id[key]['text'], 'prediction': event['label'], 'confidence': event['confidence'], 'uncertain': card['uncertain'], 'uncertain_reasons': card['uncertain_reasons'], 'input_is_synthetic': True, 'formal_gold_label_assigned': False})
    return {'schema': 'slr09-saved-smoke-audit-0.1', 'run_id': workflow['run_id'], 'all_passed': True,
        'checks': checks, 'checks_passed': len(checks), 'training_executed_by_audit': False,
        'neural_inference_repeated_by_audit': False, 'new_quality_metrics_computed': False,
        'source_snapshot_against_zip_verified': source_package is not None,
        'environment_scope': summary['environment_scope'], 'candidate_loading_verified_in_reported_environment': True,
        'target_vm_verified': False, 'quality_acceptance_approved': False,
        'observed_labels': sorted({r['prediction'] for r in diagnostic_rows}),
        'non_event_prediction_seen': any(r['prediction'] == 'NON_EVENT' for r in diagnostic_rows),
        'low_confidence_prediction_seen': any(r['confidence'] < .95 for r in diagnostic_rows),
        'diagnostic_rows': diagnostic_rows,
        'quality_observation': 'SMOKE-SYNTHETIC-002 menyebut simulasi; diprediksi FIRE ber-confidence tinggi tanpa uncertain. Perlu review mutu; bukan gold atau skor test independen.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, required=True)
    parser.add_argument('--source-package', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.report_dir, args.source_package)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'all_passed': result['all_passed'], 'checks_passed': result['checks_passed'],
                      'records': len(result['diagnostic_rows']), 'scope': result['environment_scope']}, indent=2))


if __name__ == '__main__':
    main()
