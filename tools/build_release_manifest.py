"""Rebuild the distribution plan; never reads secrets or executes Git operations."""
import argparse
import hashlib
import json
from pathlib import Path

TEXT_SUFFIXES = {'.py','.js','.mjs','.vue','.css','.json','.txt','.md','.bat','.html','.webmanifest','.example'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def known_hashes(path):
    if not path.is_file():
        return set()
    raw = path.read_bytes()
    values = {digest(raw)}
    if path.suffix in TEXT_SUFFIXES or path.name == '.gitignore':
        lf = raw.replace(b'\r\n', b'\n')
        values |= {digest(lf), digest(lf.replace(b'\n', b'\r\n'))}
    return values


def build(root, previous, baseline=None):
    old = json.loads((previous/'tools/release-manifest.json').read_text())
    names = set(old['files'])
    for folder in ('code/frontend','code/backend/reporting','docs/slr10','tools'):
        for path in (root/folder).rglob('*'):
            if path.is_file() and not any(part in {'node_modules','__pycache__','.venv'} for part in path.relative_to(root).parts):
                names.add(path.relative_to(root).as_posix())
    names |= {p.name for p in root.glob('*.bat')}
    names |= {'docs/uiux/tools/check.mjs','docs/uiux/tools/review-check.mjs','docs/uiux/tools/audit-check.mjs'}
    names.discard('tools/release-manifest.json')
    records = {}
    for name in sorted(names):
        source = root/name
        if not source.is_file():
            continue
        record = {'sha256':digest(source.read_bytes())}
        equivalents = known_hashes(source)
        if len(equivalents) > 1:
            record['equivalent_sha256'] = sorted(equivalents)
        baseline_hash = old['files'].get(name,{}).get('baseline_sha256')
        if baseline is not None and (baseline/name).is_file():
            baseline_hash = digest((baseline/name).read_bytes())
        if baseline_hash:
            record['baseline_sha256'] = baseline_hash
        accepted = known_hashes(previous/name)
        if baseline is not None:
            accepted |= known_hashes(baseline/name)
        if accepted:
            record['accepted_previous_sha256'] = sorted(accepted)
        records[name] = record
    manifest = {'version':'1.1.0','baseline':old['baseline'],'previous_versions':['1.0.0'],
        'previous_manifest_sha256':sorted(known_hashes(previous/'tools/release-manifest.json')),'files':records}
    (root/'tools/release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return len(records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    print('Manifest files:',build(args.root.resolve(),args.previous.resolve(),args.baseline.resolve() if args.baseline else None))
