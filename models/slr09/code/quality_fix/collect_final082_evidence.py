"""Preserve notebook 25's actual run and summarize its unchanged decision."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    root, run = args.root.resolve(), args.run.resolve()
    sys.path.insert(0, str(root / 'code/acceptance'))
    from evaluate_acceptance import validate, digest, write
    source = run / 'evidence'
    bundle = json.loads((source / 'reviewed_bundle_frozen.json').read_text())
    rows, _ = validate(bundle, root)
    report = json.loads((source / 'evaluation.json').read_text())
    state = json.loads((source / 'workflow_result.json').read_text())
    lock = json.loads((source / 'evaluation_lock.json').read_text())
    predictions = [json.loads(line) for line in (source / 'predictions.jsonl').read_text().splitlines()]
    assert state['status'] == 'SUCCEEDED' and state['records_completed'] == 50
    assert state['model_inference_executed'] and not state['training_executed']
    assert digest(bundle) == lock['bundle_sha256'] == report['frozen_bundle_sha256']
    assert sha(source / 'predictions.jsonl') == report['predictions_sha256']
    prepared = json.loads((root / 'evidence/acceptance_v082/submission/validated_reference_before_notebook.json').read_text())
    for a, b in zip(prepared['records'], rows):
        for key in ['id', 'text', 'gold_label', 'gold_fields', 'gold_nara_labels']:
            assert a[key] == b[key], (a['id'], key)
    for relative, expected in bundle['protocol']['binding']['files_sha256'].items():
        assert sha(root / relative) == expected
        assert sha(root / 'evidence/acceptance_v082/pre_inference_snapshot' / relative) == expected
    target = root / 'evidence/acceptance_v082/original_run'
    target.mkdir(exist_ok=False)
    shutil.copy2(run / 'reviewed_reference.json', target / 'reviewed_reference.json')
    shutil.copytree(source, target / 'evidence', ignore=shutil.ignore_patterns('runtime'))
    shutil.copy2(run.parent / 'final_acceptance_v082_notebook25_stdout.txt', target / 'notebook25_stdout.txt')
    contrast = []
    for row, pred in zip(rows, predictions):
        if row.get('family') in {'simulation', 'exercise_only', 'real_during_exercise'}:
            contrast.append({'id': row['id'], 'text': row['text'], 'family': row['family'],
                'gold_label': row['gold_label'], 'prediction': pred['event_classifier']['label'],
                'confidence': pred['event_classifier']['confidence'],
                'correct': row['gold_label'] == pred['event_classifier']['label']})
    numeric_keys = [key for key in report['checks'] if key not in
                    {'adapter_fusion_contract', 'simulation_vs_real_exercise_contrasts'}]
    assessment = {
        'schema': 'slr09-final082-actual-acceptance-result-1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'run_started_at_utc': state['started_at'], 'run_finished_at_utc': state['finished_at'],
        'status': 'IN_REVIEW', 'workflow_status': state['status'],
        'records': len(rows), 'tokens': sum(len(x['gold_nara_labels']) for x in rows),
        'reviewer': sorted({r['review']['reviewer'] for r in rows}),
        'model_inference_executed': True, 'training_executed': False,
        'numeric_targets_met': all(report['checks'][key] for key in numeric_keys),
        'numeric_targets_passed': sum(report['checks'][key] for key in numeric_keys),
        'numeric_targets_total': len(numeric_keys),
        'required_checks_passed': sum(report['checks'].values()), 'required_checks_total': len(report['checks']),
        'all_required_checks_met': report['metric_targets_met'],
        'original_evaluator_metric_targets_met_includes_non_numeric_checks': True,
        'decision': report['decision'],
        'quality_acceptance_approved': False, 'card_done': False,
        'model_code_config_changed_after_review': False,
        'reference_used_for_repairs_or_checkpoint_selection': False,
        'review_sha256': json.loads((root / 'evidence/acceptance_v082/submission/submission_identity.json').read_text())['source_sha256'],
        'bundle_sha256': digest(bundle), 'predictions_sha256': report['predictions_sha256'],
        'simulation_contrasts': contrast,
        'next_step': 'Resolve the failed exercise-only contrast under the existing protocol before quality acceptance; do not lower targets or relabel the frozen reference.',
        'remote_push_executed': False, 'production_deployed': False,
    }
    write(root / 'acceptance/quality_assessment_FINAL082_v0.8.2.json', assessment)
    write(root / 'evidence/acceptance_v082/result_summary.json', assessment)
    print(json.dumps(assessment, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
