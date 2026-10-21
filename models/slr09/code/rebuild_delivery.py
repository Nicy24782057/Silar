"""Bangun ulang manifest dan ZIP penyerahan; tidak memasukkan bobot besar."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile
from check_delivery import (
    INTERNAL_MANIFEST, REPOSITORY_MANIFEST, REPOSITORY_ROOT,
    check, delivery_files, link_results, sha,
)


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def build(root, output):
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root):
        raise ValueError('ZIP keluaran harus di luar direktori sumber paket')
    if output.exists():
        raise ValueError('ZIP keluaran sudah ada; gunakan nama revisi baru')
    links = link_results(root)
    if not all(row['passed'] for row in links):
        raise ValueError('Ada tautan aktif yang belum dapat diresolusikan')
    internal_root = root / 'models/slr09'
    manifest_metadata = json.loads((internal_root / 'asset_manifest.json').read_text())
    revision = manifest_metadata.get('delivery_revision', '0.2')
    smoke = manifest_metadata.get('candidate_loading_evidence', {})
    smoke_available = smoke.get('status') == 'SUCCEEDED'
    rows = [{'path': str(p.relative_to(internal_root)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
            for p in delivery_files(root) if p.is_relative_to(internal_root) and p != root / INTERNAL_MANIFEST]
    write(root / INTERNAL_MANIFEST, {'schema': 'slr09-notebook-snapshot-0.2', 'revision': revision,
        'weights_included': False, 'training_executed_in_revision': False,
        'candidate_neural_inference_evidence_available': smoke_available,
        'new_neural_inference_executed_by_packaging': False,
        'selected_threshold_for_integration': .95, 'production_deployed': False, 'files': rows})
    tests = json.loads((internal_root / 'evidence/revision_v0.2/active_tests.json').read_text())
    if not tests['all_passed']:
        raise ValueError('Suite aktif belum lulus')
    write(root / 'docs/ai/slr09/pemeriksaan_paket_repository.json', {
        'schema': 'slr09-repository-overlay-checks-0.2', 'revision': revision, 'all_passed': True,
        'source_zip_sha256': '9eb32ae2be066b856882ae91ff4a68a0427099ec5689b45428c6f90716ab07d9',
        'all_source_package_files_byte_identical': False,
        'source_versioned_file_manifest_verified': True,
        'all_location_references_resolve': True, 'active_local_link_count': len(links),
        'active_contract_test_count': tests['tests_run'], 'active_contract_tests_passed': True,
        'selected_option': 'A', 'confidence_threshold': .95,
        'model_weights_included': False, 'new_neural_inference_executed_by_packaging': False,
        'candidate_loading_evidence_available': smoke_available,
        'candidate_loading_evidence': smoke,
        'training_executed': False, 'quality_acceptance_approved': False,
        'git_commit_executed': False, 'git_push_executed': False, 'production_deployed': False,
        'scope': 'DELIVERY_INTEGRITY_AND_SYNTHETIC_CONTRACTS_NOT_FULL_SLR09_ACCEPTANCE'})
    rows = [{'path': str(p.relative_to(root)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
            for p in delivery_files(root) if p != root / REPOSITORY_MANIFEST]
    write(root / REPOSITORY_MANIFEST, {'schema': 'slr09-repository-overlay-manifest-0.2',
        'revision': revision, 'model_weights_included': False, 'files': rows})
    checks = check(root)
    if not checks['all_passed']:
        raise ValueError(json.dumps(checks, ensure_ascii=False))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in delivery_files(root):
            archive.write(path, str(path.relative_to(root)))
        for directory in ['models/sena/', 'models/nara/']:
            archive.writestr(directory, '')
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('CRC ZIP gagal')
        for path in delivery_files(root):
            if archive.read(str(path.relative_to(root))) != path.read_bytes():
                raise ValueError('Isi ZIP tidak sama dengan sumber final')
    return {'file': str(output), 'bytes': output.stat().st_size, 'sha256': sha(output), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPOSITORY_ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
