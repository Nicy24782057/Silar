"""Actual joint neural regression of reloaded v0.8.3 assets on seen references.

No new acceptance inference is performed. Reviewed references and historical
raw evidence stay unchanged; training/selection exposure is explicit.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'code/active_nara_adapter'), str(ROOT / 'code/acceptance')]
from slr09_candidate_runtime import CandidateModelRunner, candidate_record, selected_assets
from slr09_runtime import validate_prediction
from evaluate_acceptance import score
from train_sena_cpu import sha, write


def load(path):
    return json.loads(path.read_text())


def verify(sena_dir, nara_dir, output):
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status='PREPARING', started_at=datetime.now(timezone.utc).isoformat(),
                 model_inference_executed=False, sena_inference_executed=False,
                 nara_inference_executed=False, training_executed=False,
                 new_independent_acceptance_executed=False,
                 quality_acceptance_approved=False, card_done=False)
    write(output / 'run_state.json', state)
    try:
        config, lock, _ = selected_assets(ROOT)
        assert lock['pipeline_revision'] == '0.8.3'
        assert config['confidence_threshold'] == 0.95
        preflight = load(ROOT / 'evidence/quality_fix_v083/resume_preflight.json')
        for relative, expected in preflight['source_file_sha256'].items():
            assert sha(ROOT / relative) == expected, relative
        write(output / 'environment.json', dict(
            python=sys.version, platform=platform.platform(),
            packages={name: importlib.metadata.version(name) for name in
                      ('torch', 'transformers', 'tokenizers', 'safetensors', 'numpy', 'nbformat')},
            environment_scope='CODEX_CPU_REPRESENTATIVE_NOT_TARGET_VM'))
        snapshot = output / 'pre_inference_snapshot'
        for path in list((ROOT / 'code/active_nara_adapter').glob('*.py')) + [ROOT / rel for rel in (
            'config/SLR09_Konfigurasi_Integrasi_v0.8.json',
            'config/quality_candidate_asset_lock_v0.8.3.json',
            'code/acceptance/evaluate_acceptance.py')]:
            target = snapshot / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        runner = CandidateModelRunner(sena_dir, nara_dir, root=ROOT, device='cpu', cpu_threads=2)
        state.update(status='INFERENCE', models=runner.model_evidence, load_seconds=runner.load_seconds)
        write(output / 'run_state.json', state)
        sets = {
            'human_regression50': ROOT / 'evidence/quality_fix_v081/guard_verification22b/human_regression_reference.json',
            'FINAL081': ROOT / 'evidence/acceptance_v081/original_run/evidence/reviewed_bundle_frozen.json',
            'FINAL082': ROOT / 'evidence/acceptance_v082/original_run/evidence/reviewed_bundle_frozen.json',
        }
        reports = {}
        completed = 0
        for name, reference in sets.items():
            target = output / name
            target.mkdir()
            bundle = load(reference)
            before = sha(reference)
            predictions = []
            with (target / 'predictions.jsonl').open('x') as stream:
                for row in bundle['records']:
                    event, sena_coverage = runner.predict_sena(row['text'])
                    validate_prediction(event)
                    tokens, nara_coverage = runner.predict_nara(row['text'])
                    item = candidate_record(row, event, tokens, config, lock)
                    item.update(nara_tokens=tokens, sena_token_coverage=sena_coverage,
                                nara_token_coverage=nara_coverage)
                    predictions.append(item)
                    stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n')
                    stream.flush()
                    completed += 1
                    state.update(records_completed=completed, sena_inference_executed=True,
                                 nara_inference_executed=True, model_inference_executed=True)
                    if completed == 1 or completed % 10 == 0:
                        write(output / 'run_state.json', state)
                        print('Actual joint seen-reference regression', completed, '/ 150', flush=True)
            report = score(bundle['records'], predictions, bundle['protocol'])
            report.update(scope='SEEN_TRAINING_AND_DEVELOPMENT_REGRESSION_NOT_INDEPENDENT_ACCEPTANCE',
                          decision='KNOWN_REGRESSION_TARGETS_MET_NEW_ACCEPTANCE_REQUIRED'
                          if report['metric_targets_met'] else 'KNOWN_REGRESSION_FAILED',
                          actual_neural_inference_executed=True, reference_sha256=before,
                          predictions_sha256=sha(target / 'predictions.jsonl'),
                          quality_acceptance_approved=False, card_done=False)
            assert sha(reference) == before
            write(target / 'evaluation.json', report)
            shutil.copy2(reference, target / 'reviewed_bundle_frozen.json')
            reports[name] = dict(checks=report['checks'], all_checks_met=report['metric_targets_met'],
                                 sena_macro_f1=report['sena']['macro_f1'],
                                 non_event_recall=report['sena']['per_class']['NON_EVENT']['recall'],
                                 sena_errors=report['sena']['errors'],
                                 nara_macro_f1=report['nara']['macro_f1_all_14_non_o'],
                                 nara_exact_span_f1=report['nara']['exact_span_f1'],
                                 fields_nonempty_exact=report['fields']['nonempty_exact'],
                                 empty_spurious_rate=report['fields']['empty_spurious_rate'])
        all_met = all(report['all_checks_met'] for report in reports.values())
        state.update(status='SUCCEEDED' if all_met else 'KNOWN_REGRESSION_FAILED',
                     reports=reports, all_seen_joint_regression_checks_met=all_met,
                     protected_source_files_unchanged=True,
                     finished_at=datetime.now(timezone.utc).isoformat())
        write(ROOT / 'evidence/quality_fix_v083/verification.json', state)
        if not all_met:
            raise RuntimeError('The reloaded candidate failed a known joint regression requirement')
        print(json.dumps(state, indent=2), flush=True)
    except Exception as error:
        import traceback
        state.update(status='FAILED', error=str(error), finished_at=datetime.now(timezone.utc).isoformat())
        (output / 'error_trace.txt').write_text(traceback.format_exc())
        raise
    finally:
        write(output / 'run_state.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sena-dir', type=Path, required=True)
    parser.add_argument('--nara-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    verify(arguments.sena_dir.resolve(), arguments.nara_dir.resolve(), arguments.output.resolve())
