"""Package final v0.8.3 source/evidence against the unexecuted recovery ZIP.

Neural weight directories are always excluded. This is not a comparison with
the user's current GitHub checkout and performs no commit/push/deployment.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from train_sena_cpu import sha, write

ROOT = Path(__file__).resolve().parents[2]


def included(path):
    if not path.is_file():
        return False
    parts = path.relative_to(ROOT).parts
    return (not any(part in {'__pycache__', 'best_model', 'runtime', '.pytest_cache'} for part in parts)
            and path.suffix not in {'.pyc', '.safetensors', '.bin'})


def build(base_archive, run, output):
    state = json.loads((run / 'run_state.json').read_text())
    if state['status'] not in {'SUCCEEDED', 'FAILED', 'NO_FEASIBLE_CANDIDATE'}:
        raise ValueError('Do not package an unfinished training run as a final result')
    if not (ROOT / 'SLR09_STATUS_v0.8.3.md').is_file():
        raise ValueError('Final actual-results status is required')
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / 'SLR09_Checkpoint_Pengerjaan_v0.8.3.zip'
    overlay = output / 'SLR09_Perubahan_dan_Bukti_v0.8.3.zip'
    for path in (checkpoint, overlay):
        if path.exists():
            raise ValueError('Do not overwrite a completed deliverable: ' + str(path))
    old_manifest = ROOT / 'FILE_MANIFEST.json'
    history = ROOT / 'historical/FILE_MANIFEST_before_v0.8.3_execution.json'
    history.parent.mkdir(exist_ok=True)
    if not history.exists():
        shutil.copy2(old_manifest, history)
    files = [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
             for p in sorted(ROOT.rglob('*')) if included(p) and p != old_manifest]
    source_manifest = dict(
        schema='slr09-source-evidence-files-0.8.3', revision='0.8.3',
        manifest_itself_excluded=True, status='IN_REVIEW',
        actual_training_status=state['status'], training_executed=state['training_executed'],
        known_constraints_met=state.get('all_known_constraints_met', False),
        weights_included=False, confidence_threshold=0.95,
        independent_acceptance_executed=False, quality_acceptance_approved=False,
        card_done=False, remote_push_executed=False, production_deployed=False,
        files=files)
    write(old_manifest, source_manifest)
    changed = []
    with zipfile.ZipFile(base_archive) as base:
        baseline = {name: hashlib.sha256(base.read(name)).hexdigest()
                    for name in base.namelist() if not name.endswith('/')}
    protected = []
    for name, expected in baseline.items():
        if not name.startswith('models/slr09/'):
            continue
        relative = Path(name).relative_to('models/slr09')
        if (relative.parts[0] in {'data', 'sources', 'evidence'}
                or relative.name in {'legacy_postprocessing.py', 'nara_data.py',
                                     'nara_experiment.py', 'nara_metrics.py'}):
            path = ROOT / relative
            assert path.is_file() and sha(path) == expected, 'Protected original changed: ' + name
            protected.append(name)
    for path in sorted(ROOT.rglob('*')):
        if not included(path):
            continue
        relative = 'models/slr09/' + path.relative_to(ROOT).as_posix()
        current = sha(path)
        previous = baseline.get(relative)
        if current == previous:
            continue
        changed.append(dict(path=relative, status='MODIFIED' if previous else 'NEW',
                            expected_previous_sha256=previous,
                            sha256=current, bytes=path.stat().st_size))
    manifest = dict(
        schema='slr09-source-evidence-overlay-0.8.3',
        basis='PRIOR_DELIVERED_V083_UNEXECUTED_CHECKPOINT_NOT_USER_GITHUB_ZIP',
        base_archive_name=base_archive.name, base_archive_sha256=sha(base_archive),
        status='IN_REVIEW', actual_training_status=state['status'],
        quality_acceptance_approved=False, card_done=False,
        remote_push_executed=False, production_deployed=False,
        weights_included=False, deletions=[],
        audit_exclusions=['TWO_SLR08_TRACKING_COMMITS', 'LOCAL_FILENAME_SUFFIX_(3)'],
        files=changed)
    guide = (ROOT / 'SLR09_STATUS_v0.8.3.md').read_text()
    guide += '\n\nPaket perubahan hanya file baru/berubah terhadap checkpoint v0.8.3 sebelum eksekusi. '
    guide += 'Ini belum dicocokkan dengan ZIP repository GitHub pengguna. Tidak ada penghapusan, push atau deployment. '
    guide += 'Bobot terpisah dari paket sumber. Pertahankan arsip dan bukti versi sebelumnya.\n'
    with zipfile.ZipFile(overlay, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('README_OVERLAY.md', guide)
        z.writestr('manifest_overlay_v0.8.3.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        for item in changed:
            path = ROOT / Path(item['path']).relative_to('models/slr09')
            z.write(path, item['path'])
    with zipfile.ZipFile(checkpoint, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('README_RECOVERY.md', guide)
        for path in sorted(ROOT.rglob('*')):
            if included(path):
                z.write(path, 'models/slr09/' + path.relative_to(ROOT).as_posix())
    for path in (overlay, checkpoint):
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert not any('/__pycache__/' in n or '/best_model/' in n or '/runtime/' in n
                           or n.endswith(('.pyc', '.safetensors', '.bin')) for n in z.namelist())
            if path == overlay:
                for item in changed:
                    assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
            else:
                delivered = json.loads(z.read('models/slr09/FILE_MANIFEST.json'))
                for item in delivered['files']:
                    assert hashlib.sha256(z.read('models/slr09/' + item['path'])).hexdigest() == item['sha256']
    report = dict(status='SUCCEEDED', at_utc=datetime.now(timezone.utc).isoformat(),
                  base_archive_sha256=manifest['base_archive_sha256'],
                  changed_files=len(changed), change_counts=dict(Counter(x['status'] for x in changed)),
                  source_files=len(files), crc_and_sha256_verified=True,
                  protected_originals_preserved=True,
                  protected_original_files_verified=len(protected),
                  weights_in_source_package=False,
                  training_status=state['status'], quality_acceptance_approved=False,
                  card_done=False, remote_push_executed=False,
                  artifacts=[dict(filename=p.name, bytes=p.stat().st_size, sha256=sha(p))
                             for p in (checkpoint, overlay)])
    write(output / 'SLR09_Verifikasi_Paket_v0.8.3.json', report)
    write(output / 'SLR09_Perubahan_dan_Bukti_v0.8.3.manifest.json', manifest)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-archive', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    build(arguments.base_archive.resolve(), arguments.run.resolve(), arguments.output.resolve())
