"""Development replay of an already seen pilot; no new neural inference.

SENA/NARA raw predictions and reviewed references stay byte-for-byte in their
source files. Only the adapter is rerun. This is never an acceptance run.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'code/active_nara_adapter'), str(ROOT / 'code/acceptance')]
from slr09_candidate_runtime import candidate_record
from silar_ai_adapter import ADAPTER_VERSION
from evaluate_acceptance import score, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source_bytes = (args.source / 'predictions.jsonl').read_bytes()
    bundle_bytes = (args.source / 'reviewed_bundle_frozen.json').read_bytes()
    bundle = json.loads(bundle_bytes)
    before = [json.loads(line) for line in source_bytes.splitlines() if line.strip()]
    # Model identities belong to the source predictions, not to whatever new
    # candidate happens to be active when a reviewer reruns this replay.
    config = {'confidence_threshold': .95,
              'calibration_reference': 'HISTORICAL_PILOT_USER_SELECTED_CUTOFF_0.95_NOT_RECALIBRATED'}
    after = []
    for row, previous in zip(bundle['records'], before):
        if row['id'] != previous['id']:
            raise ValueError('Source order/ID mismatch')
        lock = {'models': {name: {'model_id': previous['adapted_result'][name + '_result']['model_version']}
                           for name in ('sena', 'nara')}}
        prediction = candidate_record(row, deepcopy(previous['event_classifier']),
                                      deepcopy(previous['nara_tokens']), config, lock)
        for key in ('nara_tokens', 'sena_token_coverage', 'nara_token_coverage'):
            prediction[key] = deepcopy(previous[key])
        after.append(prediction)
    report = score(bundle['records'], after, bundle['protocol'])
    report.update(scope='SEEN_PILOT_DEVELOPMENT_REPLAY_NOT_ACCEPTANCE',
                  decision='DEVELOPMENT_DIAGNOSTIC_ONLY', quality_acceptance_approved=False,
                  card_done=False, new_model_inference_executed=False,
                  adapter_version=ADAPTER_VERSION,
                  source_predictions_sha256=hashlib.sha256(source_bytes).hexdigest(),
                  source_review_sha256=hashlib.sha256(bundle_bytes).hexdigest(),
                  gold_or_raw_predictions_modified=False)
    (args.output / 'predictions.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in after))
    write(args.output / 'evaluation.json', report)
    print(json.dumps({'scope': report['scope'], 'adapter_version': ADAPTER_VERSION,
                      'nonempty_exact': report['fields']['nonempty_exact'],
                      'empty_spurious_rate': report['fields']['empty_spurious_rate'],
                      'checks': report['checks']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
