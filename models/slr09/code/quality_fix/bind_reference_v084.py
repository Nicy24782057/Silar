"""Bind fresh pending references only after the exported candidate is verified."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from train_sena_cpu import sha, write
import hashlib

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def bind(verification):
    state = load(verification / 'run_state.json')
    assert state['status'] == 'SUCCEEDED' and state['all_known_joint_regressions_met']
    proposals = load(ROOT / 'data/final_reference_proposals_v0.8.4.json')
    identity = load(ROOT / 'data/final_reference_identity_v0.8.4.json')
    assert all(r['review']['status'] == 'PENDING' and not r['review']['reviewer']
               for r in proposals['records'])
    history = ROOT / 'acceptance/history/pre_v0.8.4'
    history.mkdir(parents=True, exist_ok=False)
    for name in ('review_bundle_draft.json', 'known_inputs.json', 'README.md'):
        shutil.copy2(ROOT / 'acceptance' / name, history / name)
    old = load(history / 'review_bundle_draft.json')
    hashes = set(load(history / 'known_inputs.json')['normalized_text_sha256'])
    sources = []

    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get('text'), str):
                hashes.add(hashlib.sha256(' '.join(value['text'].casefold().split()).encode()).hexdigest())
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(old)
    for folder in ('data', 'evidence'):
        for p in sorted((ROOT / folder).rglob('*')):
            if not p.is_file() or p.suffix not in {'.json', '.jsonl'}:
                continue
            if p.name in {'final_reference_proposals_v0.8.4.json', 'final_reference_identity_v0.8.4.json'}:
                continue
            if p.suffix == '.json':
                collect(load(p))
            else:
                for line in p.read_text().splitlines():
                    if line.strip():
                        collect(json.loads(line))
            sources.append(p.relative_to(ROOT).as_posix())
    proposed = {hashlib.sha256(' '.join(r['text'].casefold().split()).encode()).hexdigest()
                for r in proposals['records']}
    assert len(proposed) == 50 and not proposed & hashes
    write(ROOT / 'acceptance/known_inputs.json', dict(schema='slr09-known-inputs-0.8.4',
        normalized_text_sha256=sorted(hashes), sources=sources, prior_hashes_retained=True,
        scope='Available sources only. Zero exact overlap does not establish semantic independence or population representativeness.'))
    lock = load(ROOT / 'config/quality_candidate_asset_lock_v0.8.4.json')
    asset_path = ROOT / 'asset_manifest.json'
    shutil.copy2(asset_path, ROOT / 'historical/asset_manifest_before_v0.8.4.json')
    asset = load(asset_path)
    asset.update(schema='slr09-repository-asset-locations-0.8.4', delivery_revision='0.8.4',
        integration_config_path='models/slr09/config/SLR09_Konfigurasi_Integrasi_v0.9.json',
        candidate_lock_path='models/slr09/config/quality_candidate_asset_lock_v0.8.4.json',
        new_gradient_training_executed=True, sena_and_nara_weights_unchanged_from_v081=False,
        nara_weights_unchanged_from_v081=True, new_v084_neural_inference_executed=True)
    asset.pop('new_v082_neural_inference_executed', None)
    asset.pop('new_v083_neural_inference_executed', None)
    asset['models'] = {name: {
        'model_id': spec['model_id'], 'archive_name': spec['archive_name'],
        'archive_sha256': spec['archive_sha256'], 'run_id': spec['run_id'], 'labels': spec['labels'],
        'weights_sha256': spec['files']['model.safetensors'],
        'weight_identity_source': 'DIRECT_ARCHIVE_AND_RUNTIME_FILE_HASH_VERIFICATION',
        'archive_included_in_this_delivery': False,
        'repository_archive_path': 'UNDECIDED_REQUIRES_USER_REPOSITORY_ZIP_COMPARISON' if name == 'sena'
            else 'models/nara/' + spec['archive_name'],
    } for name, spec in lock['models'].items()}
    asset['candidate_loading_evidence'] = dict(model_loading_verified=True,
        seen_joint_regression_records=200, environment='CODEX_CPU_REPRESENTATIVE',
        evidence_directory='models/slr09/' + verification.relative_to(ROOT).as_posix())
    asset['pipeline_verification'] = dict(revision='0.8.4',
        method='ACTUAL_EXPORTED_SENA_NARA_INFERENCE_ON_SEEN_REFERENCES',
        evidence_directory='models/slr09/' + verification.relative_to(ROOT).as_posix(),
        new_neural_inference_executed=True, original_FINAL081_FINAL082_FINAL083_retired=True,
        quality_acceptance_approved=False)
    asset['acceptance_preparation'] = dict(protocol='models/slr09/acceptance/review_bundle_draft.json',
        reference_workbook='models/slr09/acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.4.xlsx',
        status='50_NEW_PENDING_HUMAN_REFERENCE_REVIEW', new_reference_inference_executed=False,
        new_synthetic_cases=50, token_proposals=identity['tokens'],
        previous_bintang_approval_does_not_approve_these50=True)
    write(asset_path, asset)
    files = list((ROOT / 'code/active_nara_adapter').glob('*.py')) + [ROOT / p for p in (
        'code/acceptance/evaluate_acceptance.py', 'code/acceptance/import_review_xlsx.py',
        'config/SLR09_Konfigurasi_Integrasi_v0.9.json', 'config/quality_candidate_asset_lock_v0.8.4.json',
        'config/inference_environment.json', 'config/requirements-inference.txt', 'asset_manifest.json',
        'acceptance/known_inputs.json', 'data/final_reference_proposals_v0.8.4.json',
        'data/final_reference_identity_v0.8.4.json', 'data/retirement_after_FINAL083_v0.8.4.json')]
    protocol = deepcopy(old['protocol'])
    protocol['binding'] = {'candidate_version': '0.8.4',
        'files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}}
    protocol['reference_round'] = 'FINAL084_PENDING_HUMAN_REVIEW_BEFORE_INFERENCE'
    protocol['previous_bintang_approval_does_not_approve_this_reference'] = True
    write(ROOT / 'acceptance/review_bundle_draft.json', dict(protocol=protocol, records=proposals['records']))
    write(ROOT / 'evidence/quality_fix_v084/new_kit_binding.json', dict(
        created_at=datetime.now(timezone.utc).isoformat(), known_texts=len(hashes), records=50,
        tokens=identity['tokens'], normalized_exact_overlap=0,
        reference_sha256=sha(ROOT / 'data/final_reference_proposals_v0.8.4.json'),
        bundle_sha256=sha(ROOT / 'acceptance/review_bundle_draft.json'),
        status='50_PENDING', new_acceptance_inference_executed=False,
        quality_acceptance_approved=False))
    print(json.dumps({'records': 50, 'tokens': identity['tokens'], 'known_texts': len(hashes),
                      'status': '50_PENDING', 'normalized_exact_overlap': 0}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, required=True)
    bind(parser.parse_args().verification.resolve())
