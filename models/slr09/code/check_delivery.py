"""Periksa manifest, tautan dokumentasi aktif, dan sintaks paket SLR09."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
INTERNAL_MANIFEST = 'models/slr09/FILE_MANIFEST.json'
REPOSITORY_MANIFEST = 'docs/ai/slr09/manifest_berkas_repository.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def delivery_files(root):
    files = set()
    for name in ['docs/ai/slr09', 'models/slr09']:
        files.update(p for p in (root / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    files.update(root / name for name in ['models/README.md', 'MULAI_SLR09.md'] if (root / name).is_file())
    return sorted(files)


def link_results(root):
    documents = list((root / 'docs/ai/slr09').glob('*.md'))
    documents += [root / name for name in ['models/README.md', 'models/slr09/README.md',
                  'models/slr09/SLR09_Rekap_Notebook_dan_Kesiapan_v0.1.md', 'MULAI_SLR09.md']]
    results = []
    for document in documents:
        if not document.exists():
            continue
        for href in re.findall(r'\]\(([^)]+)\)', document.read_text()):
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', href) or href.startswith('#'):
                continue
            target = (document.parent / href.split('#', 1)[0]).resolve()
            results.append({'document': str(document.relative_to(root)), 'href': href,
                'passed': target.is_relative_to(root.resolve()) and target.exists()})
    return results


def check(root=REPOSITORY_ROOT):
    root = Path(root).resolve()
    reports = []
    for name, anchor in [(INTERNAL_MANIFEST, root / 'models/slr09'), (REPOSITORY_MANIFEST, root)]:
        data = json.loads((root / name).read_text())
        invalid = []
        seen = set()
        for row in data['files']:
            path = anchor / row['path']
            if row['path'] in seen or not path.resolve().is_relative_to(anchor.resolve()):
                invalid.append({'path': row['path'], 'reason': 'DUPLICATE_OR_OUTSIDE_SCOPE'})
            elif not path.is_file() or path.is_symlink():
                invalid.append({'path': row['path'], 'reason': 'MISSING_OR_SYMLINK'})
            elif path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
                invalid.append({'path': row['path'], 'reason': 'BYTES_OR_HASH'})
            seen.add(row['path'])
        reports.append({'manifest': name, 'entries': len(data['files']), 'passed': len(data['files']) - len(invalid), 'invalid': invalid})
    links = link_results(root)
    source_errors = []
    sources = [p for p in (root / 'models/slr09').rglob('*.py') if '__pycache__' not in p.parts]
    for path in sources:
        try:
            ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as error:
            source_errors.append({'path': str(path.relative_to(root)), 'error': str(error)})
    expected = {str(p.relative_to(root)) for p in delivery_files(root)} - {REPOSITORY_MANIFEST}
    listed = {row['path'] for row in json.loads((root / REPOSITORY_MANIFEST).read_text())['files']}
    coverage = {'unlisted_files': sorted(expected - listed), 'missing_listed_files': sorted(listed - expected)}
    return {'schema': 'slr09-delivery-validation-0.2', 'manifests': reports,
        'links': links, 'python_files': len(sources), 'syntax_errors': source_errors, 'coverage': coverage,
        'all_passed': not any(row['invalid'] for row in reports) and all(row['passed'] for row in links)
            and not source_errors and not any(coverage.values()),
        'candidate_neural_inference_verified_by_this_check': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args()
    result = check(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
