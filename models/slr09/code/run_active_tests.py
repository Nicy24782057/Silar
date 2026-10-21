"""Jalankan suite adapter/kandidat aktif tanpa memuat bobot neural."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args(argv)
    code = Path(__file__).resolve().parent
    sys.path.insert(0, str(code / 'tests/support'))
    sys.path.insert(0, str(code / 'active_nara_adapter'))
    suite = unittest.defaultTestLoader.discover(str(code / 'tests'), pattern='test_*.py')
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(stream.getvalue())
    summary = {'schema': 'slr09-active-contract-tests-0.2', 'tests_run': result.testsRun,
        'failures': [test.id() for test, _ in result.failures],
        'errors': [test.id() for test, _ in result.errors], 'skipped': len(result.skipped),
        'all_passed': result.wasSuccessful(), 'python': platform.python_version(),
        'model_inference_executed': False, 'training_executed': False,
        'scope': 'SYNTHETIC_CONTRACT_AND_PACKAGE_IDENTITY_NOT_NEURAL_ACCURACY'}
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / 'active_tests.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
        (args.evidence_dir / 'active_tests.txt').write_text(stream.getvalue())
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
