"""Bind unseen pending proposals to the frozen v0.8.3 development candidate."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/active_nara_adapter'))
from slr09_candidate_runtime import selected_assets


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def bind():
    config, lock, _ = selected_assets(ROOT)
    assert lock['pipeline_revision'] == '0.8.3' and config['confidence_threshold'] == 0.95
    proposals = load(ROOT / 'data/final_reference_proposals_v0.8.3.json')
    assert len(proposals['records']) == 50
    assert all(r['review']['status'] == 'PENDING' and not r['review']['reviewer']
               for r in proposals['records'])
    history = ROOT / 'acceptance/history/pre_v0.8.3'
    history.mkdir(parents=True, exist_ok=False)
    for name in ('review_bundle_draft.json', 'known_inputs.json', 'README.md'):
        shutil.copy2(ROOT / 'acceptance' / name, history / name)
    old = load(history / 'review_bundle_draft.json')
    known = load(history / 'known_inputs.json')
    hashes = set(known['normalized_text_sha256'])
    sources = []

    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get('text'), str):
                text = ' '.join(value['text'].casefold().split())
                hashes.add(hashlib.sha256(text.encode()).hexdigest())
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    for folder in ('data', 'evidence'):
        for path in sorted((ROOT / folder).rglob('*')):
            if not path.is_file() or path.suffix not in {'.json', '.jsonl'}:
                continue
            if path.name in {'final_reference_proposals_v0.8.3.json', 'final_reference_identity_v0.8.3.json'}:
                continue
            if path.suffix == '.json':
                collect(load(path))
            else:
                for line in path.read_text().splitlines():
                    if line.strip():
                        collect(json.loads(line))
            sources.append(path.relative_to(ROOT).as_posix())
    proposed = {hashlib.sha256(' '.join(r['text'].casefold().split()).encode()).hexdigest()
                for r in proposals['records']}
    assert len(proposed) == 50 and not proposed & hashes
    write(ROOT / 'acceptance/known_inputs.json', dict(
        schema='slr09-known-inputs-0.8.3', normalized_text_sha256=sorted(hashes),
        sources=sources, prior_hashes_retained=True,
        scope='Available sources only. Exact normalization does not establish semantic independence or population representativeness.'))

    asset_path = ROOT / 'asset_manifest.json'
    shutil.copy2(asset_path, history / 'asset_manifest.json')
    asset = load(asset_path)
    asset.update(schema='slr09-repository-asset-locations-0.8.3',
                 integration_config_path='models/slr09/config/SLR09_Konfigurasi_Integrasi_v0.8.json',
                 candidate_lock_path='models/slr09/config/quality_candidate_asset_lock_v0.8.3.json',
                 delivery_revision='0.8.3', new_gradient_training_executed=True,
                 sena_and_nara_weights_unchanged_from_v081=False,
                 nara_weights_unchanged=True, quality_acceptance_approved=False,
                 card_done=False, remote_push_executed=False,
                 production_deployed=False, production_model_selected=False)
    for name, spec in lock['models'].items():
        asset['models'][name].update({key: spec[key] for key in
            ('model_id', 'archive_name', 'archive_sha256', 'run_id', 'labels')})
        asset['models'][name]['weights_sha256'] = spec['files']['model.safetensors']
    asset['candidate_loading_evidence'] = dict(
        evidence_directory='models/slr09/evidence/quality_fix_v083',
        scope='SEEN_TRAINING_AND_DEVELOPMENT_NOT_INDEPENDENT_ACCEPTANCE',
        verification_report='models/slr09/evidence/quality_fix_v083/verification.json')
    asset['acceptance_preparation'] = dict(
        protocol='models/slr09/acceptance/review_bundle_draft.json',
        reference_workbook='models/slr09/acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx',
        status='50_NEW_PENDING_HUMAN_REFERENCE_REVIEW',
        new_reference_inference_executed=False, new_synthetic_cases=50,
        token_proposals=sum(len(r['gold_nara_labels']) for r in proposals['records']),
        previous_approvals_do_not_approve_these50=True)
    asset['pipeline_verification'] = dict(
        revision='0.8.3', evidence_directory='models/slr09/evidence/quality_fix_v083',
        method='ACTUAL_RELOADED_CANDIDATE_NEURAL_INFERENCE_ON_SEEN_REFERENCES',
        new_independent_acceptance_executed=False, quality_acceptance_approved=False)
    write(asset_path, asset)

    files = list((ROOT / 'code/active_nara_adapter').glob('*.py')) + [ROOT / rel for rel in (
        'code/acceptance/evaluate_acceptance.py', 'code/acceptance/import_review_xlsx.py',
        'config/SLR09_Konfigurasi_Integrasi_v0.8.json', 'config/quality_candidate_asset_lock_v0.8.3.json',
        'config/inference_environment.json', 'config/requirements-inference.txt',
        'asset_manifest.json', 'acceptance/known_inputs.json',
        'data/final_reference_proposals_v0.8.3.json', 'data/final_reference_identity_v0.8.3.json',
        'data/retirement_after_FINAL082_v0.8.3.json')]
    protocol = deepcopy(old['protocol'])
    protocol['approval'] = dict(status='PENDING', reviewer='', at='',
                                limitations_accepted=False, representativeness_accepted=False, rationale='')
    protocol['binding'] = dict(candidate_version='0.8.3',
                              files_sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)})
    protocol['reference_round'] = 'FINAL083_PENDING_HUMAN_REVIEW_BEFORE_INFERENCE'
    protocol['previous_approvals_do_not_approve_this_reference'] = True
    write(ROOT / 'acceptance/review_bundle_draft.json', dict(protocol=protocol, records=proposals['records']))
    write(ROOT / 'evidence/quality_fix_v083/new_kit_binding.json', dict(
        at_utc=datetime.now(timezone.utc).isoformat(), known_text_hashes=len(hashes),
        records=50, tokens=sum(len(r['gold_nara_labels']) for r in proposals['records']),
        reference_sha256=sha(ROOT / 'data/final_reference_proposals_v0.8.3.json'),
        bundle_sha256=sha(ROOT / 'acceptance/review_bundle_draft.json'),
        normalized_exact_overlap=0, status='50_PENDING',
        new_reference_inference_executed=False, quality_acceptance_approved=False))
    print(json.dumps({'known_text_hashes': len(hashes), 'status': '50_PENDING',
                      'class_support': dict(Counter(r['gold_label'] for r in proposals['records']))}, indent=2))


if __name__ == '__main__':
    bind()
