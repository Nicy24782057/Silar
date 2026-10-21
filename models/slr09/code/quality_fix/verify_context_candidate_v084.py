"""Reload both locked archives and verify seen regressions, never new acceptance."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'code/active_nara_adapter'), str(ROOT / 'code/acceptance')]
from slr09_candidate_runtime import (CandidateModelRunner, candidate_record, selected_assets,
    extract_candidate_archive, INTEGRATION_CONFIG, CANDIDATE_LOCK)
from slr09_runtime import environment_snapshot
from evaluate_acceptance import score
from train_sena_cpu import LABELS, metrics, sha, write


def normal(text):
    return ' '.join(text.casefold().split())


def run(args):
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    state = dict(schema='slr09-context-export-verification-0.8.4', status='PREPARING',
        started_at=datetime.now(timezone.utc).isoformat(), model_inference_executed=False,
        new_acceptance_inference_executed=False, quality_acceptance_approved=False, card_done=False)
    write(out / 'run_state.json', state)
    try:
        config, lock, profile = selected_assets()
        write(out / 'configuration_frozen.json', config)
        write(out / 'candidate_lock_frozen.json', lock)
        for source in list((ROOT / 'code/active_nara_adapter').glob('*.py')) + [
                ROOT / 'config' / INTEGRATION_CONFIG, ROOT / 'config' / CANDIDATE_LOCK,
                ROOT / 'code/acceptance/evaluate_acceptance.py', Path(__file__)]:
            target = out / 'pre_inference_snapshot' / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        extracts = {}
        for name, archive in [('sena', args.sena_archive), ('nara', args.nara_archive)]:
            extracts[name] = extract_candidate_archive(archive, out / 'runtime' / name, name, lock['models'][name])
        write(out / 'archive_extraction.json', extracts)
        runner = CandidateModelRunner(out / 'runtime/sena', out / 'runtime/nara', cpu_threads=2)
        state.update(status='VERIFYING_SEEN_SENA', model_inference_executed=True)
        write(out / 'run_state.json', state)
        sets = json.loads((args.training_run / 'scoring_sets_frozen.json').read_text())
        selected = json.loads((args.training_run / 'best_selection.json').read_text())
        comparison = {}
        # Reproduce the training evaluator's exact representative and batch
        # order for overlapping records. Do not infer the same text repeatedly.
        unique = {normal(r['text']): r for rows in sets.values() for r in rows}
        unique_rows = list(unique.values())
        raw = []
        with runner.torch.inference_mode():
            for offset in range(0, len(unique_rows), 16):
                batch = runner.sena_tokenizer([r['text'] for r in unique_rows[offset:offset+16]],
                    padding=True, truncation=True, max_length=512, return_tensors='pt')
                raw.extend(runner.torch.softmax(runner.sena_model(**batch).logits, -1).tolist())
                if offset % 160 == 0:
                    print('Exported SENA unique references:', min(offset+16, len(unique_rows)),
                          '/', len(unique_rows), flush=True)
        cached = dict(zip(unique, raw))
        for name, rows in sets.items():
            expected = json.loads((args.training_run / f'predictions_{name}.json').read_text())
            probabilities = [cached[normal(row['text'])] for row in rows]
            guesses = [LABELS[max(range(5), key=lambda i: p[i])] for p in probabilities]
            old = [max(r['probabilities'], key=r['probabilities'].get) for r in expected]
            delta = max(abs(p[i] - r['probabilities'][label])
                        for p, r in zip(probabilities, expected) for i, label in enumerate(LABELS))
            if guesses != old or delta > 1e-5:
                raise ValueError(f'Exported predictions differ from selection for {name}: {delta}')
            observed = metrics([r['final'] for r in rows], guesses)
            if observed != selected['metrics'][name]:
                raise ValueError('Exported metrics differ from selection: ' + name)
            comparison[name] = {'records': len(rows), 'labels_identical': True,
                                'max_probability_delta': delta, 'metrics': observed}
            print('Exported SENA verified:', name, len(rows), flush=True)
        write(out / 'sena_export_verification.json', comparison)
        sources = {
            'human_regression50': ROOT / 'evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json',
            'FINAL081_seen': ROOT / 'evidence/acceptance_v081/original_run/evidence/reviewed_bundle_frozen.json',
            'FINAL082_seen': ROOT / 'evidence/acceptance_v082/original_run/evidence/reviewed_bundle_frozen.json',
            'FINAL083_seen': ROOT / 'evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run/reviewed_bundle_frozen.json',
        }
        reports = {}
        for name, source in sources.items():
            bundle = json.loads(source.read_text())
            predictions = []
            with (out / f'predictions_{name}.jsonl').open('x') as stream:
                for i, row in enumerate(bundle['records'], 1):
                    event, sc = runner.predict_sena(row['text'])
                    tokens, nc = runner.predict_nara(row['text'])
                    pred = candidate_record(row, event, tokens, config, lock)
                    pred.update(nara_tokens=tokens, sena_token_coverage=sc, nara_token_coverage=nc)
                    predictions.append(pred)
                    stream.write(json.dumps(pred, ensure_ascii=False) + '\n')
                    stream.flush()
                    if i % 10 == 0:
                        print('Seen joint regression:', name, i, '/50', flush=True)
            report = score(bundle['records'], predictions, bundle['protocol'])
            report.update(scope='KNOWN_SEEN_TRAINING_REGRESSION_NOT_ACCEPTANCE',
                original_reference_sha256=sha(source), quality_acceptance_approved=False, card_done=False)
            write(out / f'evaluation_{name}.json', report)
            reports[name] = report
        write(out / 'joint_regression_summary.json', {
            'sets': {name: report['metric_targets_met'] for name, report in reports.items()},
            'all_known_joint_regressions_met': all(r['metric_targets_met'] for r in reports.values()),
            'new_acceptance_inference_executed': False, 'quality_acceptance_approved': False})
        state.update(status='SUCCEEDED',
            all_known_joint_regressions_met=all(r['metric_targets_met'] for r in reports.values()),
            environment=environment_snapshot(runner.torch, runner.device))
    except Exception as error:
        state.update(status='FAILED', error=str(error))
        (out / 'error_trace.txt').write_text(traceback.format_exc())
        raise
    finally:
        state['finished_at'] = datetime.now(timezone.utc).isoformat()
        write(out / 'run_state.json', state)
    print(json.dumps(state, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('training-run', 'sena-archive', 'nara-archive', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    run(parser.parse_args())
