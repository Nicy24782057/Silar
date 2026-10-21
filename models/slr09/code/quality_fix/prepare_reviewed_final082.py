"""Freeze the uploaded human review and the already bound source before NN use."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--review', type=Path, required=True)
    args = p.parse_args()
    root, review = args.root.resolve(), args.review.resolve()
    sys.path.insert(0, str(root / 'code/acceptance'))
    from import_review_xlsx import convert, read_cells
    from evaluate_acceptance import validate, write
    bundle = convert(review, root=root, validate_ready=True)
    rows, preflight = validate(bundle, root)
    output = root / 'evidence/acceptance_v082'
    output.mkdir(parents=True, exist_ok=False)
    submission = output / 'submission'
    submission.mkdir()
    frozen = submission / review.name
    shutil.copy2(review, frozen)
    assert sha(frozen) == sha(review)
    original = read_cells(root / 'acceptance' / review.name)
    edited = read_cells(review)
    changes = []
    for name in ['Mulai', 'Narasi', 'Token']:
        for cell in sorted(set(original[name]) | set(edited[name])):
            before = original[name].get(cell, ('', False))
            after = edited[name].get(cell, ('', False))
            if before != after:
                changes.append({'sheet': name, 'cell': cell,
                                'before': before, 'after': after})
    write(submission / 'review_diff.json', changes)
    write(submission / 'validated_reference_before_notebook.json', bundle)
    snapshot = output / 'pre_inference_snapshot'
    for relative, expected in bundle['protocol']['binding']['files_sha256'].items():
        source = root / relative
        assert sha(source) == expected, relative
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert sha(target) == expected, relative
    shutil.copy2(root / 'acceptance/review_bundle_draft.json',
                 snapshot / 'review_bundle_draft.json')
    notebook = root / 'notebooks/25_Uji_Penerimaan_SLR09_v0.8.2.ipynb'
    shutil.copy2(notebook, submission / '25_original_pending_template.ipynb')
    content = json.loads(notebook.read_text())
    code_before = [c['source'] for c in content['cells'] if c['cell_type'] == 'code']
    content['cells'][0]['source'] = [
        '# Uji penerimaan SLR_09 v0.8.2\n', '\n',
        'Acuan FINAL082 telah dikembalikan pengguna dengan 50 APPROVED dan '
        '671 token. Salinan review dan snapshot seluruh sumber terikat '
        'disimpan sebelum model dimuat. Notebook memvalidasi ulang, '
        'membekukan acuan, lalu menjalankan inferensi CPU dengan bobot '
        'SENA/NARA dan target yang tetap. Hasil eksekusi sebenarnya '
        'dicatat pada salinan _executed; penerimaan mutu tidak otomatis.\n'
    ]
    assert code_before == [c['source'] for c in content['cells'] if c['cell_type'] == 'code']
    notebook.write_text(json.dumps(content, ensure_ascii=False, indent=1) + '\n')
    identity = {
        'schema': 'slr09-final082-submission-1',
        'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': sha(review), 'frozen_copy_sha256': sha(frozen),
        'submitted_library_file_id': 'libfile_90eebecf95348191b40ff5e32251d8cd',
        'submitted_file_id': 'file_00000000db74820b92203967a7d3bf1b',
        'reviewer': sorted({x['review']['reviewer'] for x in rows}),
        'review_statuses': dict(Counter(x['review']['status'] for x in rows)),
        'changed_cells_by_sheet': dict(Counter(x['sheet'] for x in changes)),
        'preflight': preflight,
        'snapshot_created_before_model_inference': True,
        'notebook_code_cells_changed': False,
        'review_timestamps_are_import_times_not_asserted_excel_edit_times': True,
        'quality_acceptance_approved': False, 'card_done': False,
    }
    write(submission / 'submission_identity.json', identity)
    print(json.dumps(identity, ensure_ascii=False, indent=2))
    print('FROZEN_REVIEW_PATH', frozen)


if __name__ == '__main__':
    main()
