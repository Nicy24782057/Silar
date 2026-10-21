"""Evaluasi kandidat beku; acuan manusia wajib tersedia sebelum inferensi.

Tidak melatih model, mengubah threshold, memberi persetujuan kelompok, atau
mengklaim narasi sintetis sebagai sampel lapangan independen.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
LABELS = ('FLOOD', 'EARTHQUAKE', 'FIRE', 'ACCIDENT', 'NON_EVENT')
FIELDS = ('location_text', 'time_text', 'occurred_at', 'involved_parties', 'impacts', 'victims', 'affected_objects')
ROLES = ('O', 'ACCIDENT-EVENT', 'AFFECTEDOBJECTS-ARG', 'DEATHVICTIM-ARG',
         'EARTHQUAKE-EVENT', 'FALSE-EVENT', 'FIRE-EVENT', 'FLOOD-EVENT',
         'INFORMATION-ARG', 'OFFICER-ARG', 'PLACE-ARG', 'REASON-ARG',
         'STREET-ARG', 'TIME-ARG', 'WOUNDVICTIM-ARG')


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normal(text):
    return ' '.join(text.casefold().split())


def person(value):
    return isinstance(value, str) and len(value.strip()) >= 2 and value.strip().casefold() not in {'belum', 'pending', 'reviewer', 'nama', 'test', 'todo', 'isi nama'}


def stamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.tzinfo is not None and parsed <= datetime.now(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        return False


def flat_spans(labels):
    spans, i = set(), 0
    while i < len(labels):
        end = i + 1
        while end < len(labels) and labels[end] == labels[i]:
            end += 1
        if labels[i] != 'O':
            spans.add((labels[i], i, end))
        i = end
    return spans


def token_items(text):
    # Sama dengan pola serving; assertion terhadap implementasi aktif dilakukan saat run.
    return list(re.finditer(r"\w+(?:[-']\w+)*|[^\w\s]", text, re.UNICODE))


def validate_fields(fields, text):
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError('Acuan field harus tepat tujuh field')
    for key, value in fields.items():
        if key in FIELDS[:3]:
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError('Field string/null tidak valid: ' + key)
        elif not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value) or len(set(value)) != len(value):
            raise ValueError('Field array tidak valid: ' + key)
        if key == 'occurred_at' and value is not None:
            # Kit tidak mempunyai parser normalisasi waktu teruji.
            raise ValueError('occurred_at pada kit ini harus null; jangan mengarang timestamp')
        for item in ([value] if isinstance(value, str) else value or []):
            if normal(item) not in normal(text):
                raise ValueError('Acuan field tidak bersumber dari narasi: ' + key)


def validate(bundle, root=ROOT):
    protocol, rows = bundle['protocol'], bundle['records']
    if protocol.get('schema') != 'slr09-acceptance-protocol-0.4':
        raise ValueError('Versi protokol tidak dikenal')
    approval = protocol.get('approval', {})
    if approval.get('status') != 'APPROVED' or not person(approval.get('reviewer')) or not stamp(approval.get('at')):
        raise ValueError('Target/cakupan dan acuan belum direview manusia; model tidak dijalankan')
    if not approval.get('limitations_accepted') is True or not approval.get('representativeness_accepted') is True:
        raise ValueError('Keterbatasan serta kecukupan cakupan MVP belum diterima reviewer')
    if not isinstance(approval.get('rationale'), str) or len(approval['rationale'].strip()) < 20:
        raise ValueError('Dasar penerimaan cakupan/target harus dicatat')
    if protocol['confidence_threshold'] != .95 or protocol['scope'] != 'MVP_ASSET_PILOT':
        raise ValueError('Cutoff/scope berubah; perlu protokol terpisah dan review ulang')
    spec = protocol['binding']
    template = json.loads((root / 'acceptance/review_bundle_draft.json').read_text())['protocol']
    if spec != template['binding']:
        raise ValueError('Binding tidak sama dengan kit; perubahan kandidat/kode memerlukan kit dan review baru')
    for relative, expected in spec['files_sha256'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or file_sha(path) != expected:
            raise ValueError('Identitas kode/model/config/data historis berubah: ' + relative)
    targets = protocol['targets']
    required = {'sena_macro_f1', 'non_event_recall', 'event_class_recall', 'nara_macro_f1_all_14_non_o',
                'nara_exact_span_f1', 'fields_nonempty_exact', 'empty_field_spurious_rate_max'}
    if set(targets) != required or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in targets.values()):
        raise ValueError('Target metrik tidak valid')
    if type(protocol.get('minimum_per_class')) is not int or protocol['minimum_per_class'] < 10:
        raise ValueError('Pilot memerlukan sedikitnya 10 acuan per kelas; bukan ukuran sampel untuk klaim populasi')
    known = json.loads((root / 'acceptance/known_inputs.json').read_text())
    known_hashes = set(known['normalized_text_sha256'])
    seen_ids, seen_text, counts, sources = set(), set(), Counter(), Counter()
    excluded = []
    approved = []
    for row in rows:
        key, text = row['id'], row['text']
        if not isinstance(key, str) or not key.strip() or key in seen_ids:
            raise ValueError('ID kosong atau duplikat')
        seen_ids.add(key)
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Narasi kosong: ' + key)
        review = row.get('review', {})
        if review.get('status') == 'DEFERRED':
            if not person(review.get('reviewer')) or not review.get('note'):
                raise ValueError('DEFERRED memerlukan reviewer dan alasan')
            excluded.append({'id': key, 'reason': review['note']})
            continue
        if review.get('status') != 'APPROVED' or not person(review.get('reviewer')) or not stamp(review.get('at')):
            raise ValueError('Acuan belum direview: ' + key)
        h = hashlib.sha256(normal(text).encode()).hexdigest()
        if h in seen_text or h in known_hashes:
            raise ValueError('Narasi duplikat/data pengembangan atau historis: ' + key)
        seen_text.add(h)
        if row['gold_label'] not in LABELS:
            raise ValueError('Kategori tidak valid: ' + key)
        origin = row.get('origin', {})
        if origin.get('kind') not in {'ASSISTANT_AUTHORED_SYNTHETIC', 'HUMAN_AUTHORED_NEW', 'NEW_FIELD_NARRATIVE'} or not origin.get('reference'):
            raise ValueError('Asal narasi harus dicatat: ' + key)
        validate_fields(row['gold_fields'], text)
        tokens = token_items(text)
        if len(row['gold_nara_labels']) != len(tokens) or not set(row['gold_nara_labels']) <= set(ROLES):
            raise ValueError('Label/token NARA tidak selaras: ' + key)
        counts[row['gold_label']] += 1
        sources[origin['kind']] += 1
        approved.append(row)
    if any(counts[label] < protocol['minimum_per_class'] for label in LABELS):
        raise ValueError('Cakupan kelas belum cukup setelah DEFERRED: ' + json.dumps(counts))
    support = Counter(x for row in approved for x in row['gold_nara_labels'])
    if any(not support[label] for label in ROLES[1:]):
        raise ValueError('Acuan baru belum mencakup semua 14 label non-O')
    required_contrasts = {('simulation', 'NON_EVENT'), ('exercise_only', 'NON_EVENT'),
                          ('real_during_exercise', 'FIRE'), ('real_during_exercise', 'ACCIDENT')}
    if not required_contrasts <= {(r.get('family'), r['gold_label']) for r in approved}:
        raise ValueError('Pasangan simulasi dan kejadian nyata saat latihan belum lengkap')
    return approved, {'records': len(approved), 'class_support': dict(counts), 'role_support': dict(support),
                      'sources': dict(sources), 'excluded': excluded,
                      'known_data_overlap': 'NO_NORMALIZED_EXACT_MATCH_IN_AVAILABLE_SOURCES',
                      'historical_initial_training_membership_verified': False,
                      'population_generalization_established': False}


def divide(a, b):
    return a / b if b else 0.0


def classification(rows, predictions):
    matrix = {a: Counter({b: 0 for b in LABELS}) for a in LABELS}
    errors, bins = [], [Counter() for _ in range(10)]
    squared, correct, flagged, captured = 0.0, 0, 0, 0
    for row, pred in zip(rows, predictions):
        p = pred['event_classifier']
        gold, guess, confidence = row['gold_label'], p['label'], p['confidence']
        matrix[gold][guess] += 1
        ok = gold == guess
        correct += ok
        low = confidence < .95
        flagged += low
        captured += low and not ok
        if not ok:
            errors.append({'id': row['id'], 'text': row['text'], 'gold': gold, 'prediction': guess,
                           'confidence': confidence, 'low_confidence': low, 'family': row.get('family'),
                           'kind': 'FALSE_EVENT' if gold == 'NON_EVENT' else 'FALSE_NON_EVENT' if guess == 'NON_EVENT' else 'WRONG_EVENT_TYPE'})
        item = bins[min(9, int(confidence * 10))]
        item['n'] += 1; item['correct'] += ok; item['confidence_sum'] += confidence
        squared += sum((p['probabilities'][label] - int(label == gold)) ** 2 for label in LABELS)
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted = sum(matrix[a][label] for a in LABELS)
        precision, recall = divide(tp, predicted), divide(tp, support)
        per_class[label] = {'precision': precision, 'recall': recall, 'f1': divide(2 * precision * recall, precision + recall), 'support': support}
    n = len(rows)
    reliability = [{'lower': i / 10, 'upper': (i + 1) / 10, 'n': x['n'],
                    'mean_confidence': divide(x['confidence_sum'], x['n']), 'accuracy': divide(x['correct'], x['n'])}
                   for i, x in enumerate(bins)]
    return {'records': n, 'accuracy': divide(correct, n), 'macro_f1': sum(v['f1'] for v in per_class.values()) / 5,
            'per_class': per_class, 'confusion_matrix': matrix, 'errors': errors,
            'false_event': sum(x['kind'] == 'FALSE_EVENT' for x in errors),
            'false_non_event': sum(x['kind'] == 'FALSE_NON_EVENT' for x in errors),
            'high_confidence_errors': sum(not x['low_confidence'] for x in errors),
            'threshold_analysis': {'cutoff': .95, 'flagged': flagged, 'errors_flagged': captured,
                                   'errors_remaining_at_or_above': len(errors) - captured, 'coverage': divide(n - flagged, n)},
            'reliability': {'ten_bin_ece': sum(x['n'] / n * abs(x['mean_confidence'] - x['accuracy']) for x in reliability),
                            'multiclass_brier_sum_over_classes': squared / n, 'bins': reliability,
                            'probability_calibration_established': False,
                            'scope': 'DIAGNOSTIC_ON_APPROVED_PILOT_NOT_PROOF_OF_95_PERCENT_CORRECTNESS'}}


def nara_scores(rows, predictions):
    matrix = {a: Counter({b: 0 for b in ROLES}) for a in ROLES}
    spans = Counter()
    errors = []
    for row, pred in zip(rows, predictions):
        gold, guess = row['gold_nara_labels'], [x['label'] for x in pred['nara_tokens']]
        if len(gold) != len(guess):
            raise ValueError('Token terpotong/tidak lengkap tidak diberi skor lulus: ' + row['id'])
        for a, b in zip(gold, guess):
            matrix[a][b] += 1
        a, b = flat_spans(gold), flat_spans(guess)
        spans.update(tp=len(a & b), fp=len(b - a), fn=len(a - b))
        if gold != guess:
            errors.append({'id': row['id'], 'text': row['text'], 'tokens': [x['original'] for x in pred['nara_tokens']],
                           'gold': gold, 'prediction': guess})
    by_label = {}
    for label in ROLES:
        tp, support = matrix[label][label], sum(matrix[label].values())
        precision = divide(tp, sum(matrix[a][label] for a in ROLES))
        recall = divide(tp, support)
        by_label[label] = {'precision': precision, 'recall': recall, 'f1': divide(2 * precision * recall, precision + recall), 'support': support}
    return {'macro_f1_all_14_non_o': sum(by_label[x]['f1'] for x in ROLES[1:]) / 14,
            'exact_span_f1': divide(2 * spans['tp'], 2 * spans['tp'] + spans['fp'] + spans['fn']),
            'span_counts': spans, 'by_label': by_label, 'confusion_matrix': matrix, 'errors': errors,
            'alignment': 'SERVING_REGEX_TOKENS_FIRST_WORDPIECE', 'all_input_tokens_processed': True,
            'comparability': 'NEW_PILOT_NOT_DIRECTLY_COMPARABLE_TO_CORPUS_TOKENIZATION_OF_HISTORICAL_79'}


def normalized_value(value):
    if isinstance(value, list):
        return sorted(normal(x) for x in value)
    return normal(value) if isinstance(value, str) else value


def field_scores(rows, predictions):
    stats = {k: Counter() for k in FIELDS}
    errors, contract_errors = [], []
    for row, pred in zip(rows, predictions):
        actual = pred['adapted_result']['nara_result']['normalized_output']
        validate_fields(actual, row['text'])
        for key in FIELDS:
            gold, guess = row['gold_fields'][key], actual[key]
            same = normalized_value(gold) == normalized_value(guess)
            s = stats[key]
            s['total'] += 1; s['exact_all'] += same
            if gold not in (None, [], ''):
                s['nonempty_gold'] += 1; s['nonempty_exact'] += same
            else:
                s['empty_gold'] += 1; s['spurious'] += guess not in (None, [], '')
            if not same:
                errors.append({'id': row['id'], 'field': key, 'gold': gold, 'prediction': guess})
        fused = pred['fusion_result']
        sena = pred['event_classifier']
        signals = fused['integration_signals']
        card = fused['incident_card_version_fields']
        if signals['blocked_by_non_event'] != (sena['label'] == 'NON_EVENT'):
            contract_errors.append({'id': row['id'], 'reason': 'NON_EVENT_SIGNAL'})
        if card['data']['event_type'] != (None if sena['label'] == 'NON_EVENT' else sena['label']):
            contract_errors.append({'id': row['id'], 'reason': 'CATEGORY_SOURCE'})
        if set(card['data']) != set(FIELDS) | {'event_type'} or any(card['data'][k] != actual[k] for k in FIELDS):
            contract_errors.append({'id': row['id'], 'reason': 'FUSION_EXTRACTION_CHANGED'})
        low_reason = 'LOW_CLASSIFICATION_CONFIDENCE' in card['uncertain_reasons']
        if low_reason != (sena['confidence'] < .95):
            contract_errors.append({'id': row['id'], 'reason': 'CONFIDENCE_THRESHOLD'})
        expected_reasons = ['LOW_CLASSIFICATION_CONFIDENCE'] if sena['confidence'] < .95 else []
        if card['uncertain_reasons'] != expected_reasons or card['uncertain'] is not bool(expected_reasons):
            contract_errors.append({'id': row['id'], 'reason': 'UNSUPPORTED_UNCERTAIN_REASON_OR_FLAG'})
    nonempty = sum(x['nonempty_gold'] for x in stats.values())
    empty = sum(x['empty_gold'] for x in stats.values())
    return {'per_field': stats, 'nonempty_exact': divide(sum(x['nonempty_exact'] for x in stats.values()), nonempty),
            'nonempty_denominator': nonempty, 'empty_spurious_rate': divide(sum(x['spurious'] for x in stats.values()), empty),
            'empty_denominator': empty, 'errors': errors, 'contract_errors': contract_errors,
            'definition': 'Exact casefold/whitespace; array order ignored, duplicates rejected; empty matches excluded from nonempty score',
            'backend_submission_tested': False}


def score(rows, predictions, protocol):
    if len(rows) != len(predictions) or [x['id'] for x in rows] != [x['id'] for x in predictions]:
        raise ValueError('ID/jumlah/urutan hasil berbeda')
    for row, pred in zip(rows, predictions):
        if pred['input_sha256'] != hashlib.sha256(row['text'].encode()).hexdigest():
            raise ValueError('Prediksi bukan untuk narasi acuan')
        if pred['sena_token_coverage'].get('truncated') or not pred['nara_token_coverage'].get('all_regex_tokens_processed') or pred['nara_token_coverage'].get('last_wordpiece_sequence_partial'):
            raise ValueError('Input terpotong tidak boleh diterima sebagai evaluasi lengkap')
    sena, nara, fields = classification(rows, predictions), nara_scores(rows, predictions), field_scores(rows, predictions)
    t = protocol['targets']
    checks = {
        'sena_macro_f1': sena['macro_f1'] >= t['sena_macro_f1'],
        'non_event_recall': sena['per_class']['NON_EVENT']['recall'] >= t['non_event_recall'],
        'all_event_class_recalls': all(sena['per_class'][x]['recall'] >= t['event_class_recall'] for x in LABELS[:-1]),
        'nara_macro_f1_all_14_non_o': nara['macro_f1_all_14_non_o'] >= t['nara_macro_f1_all_14_non_o'],
        'nara_exact_span_f1': nara['exact_span_f1'] >= t['nara_exact_span_f1'],
        'fields_nonempty_exact': fields['nonempty_exact'] >= t['fields_nonempty_exact'],
        'empty_field_spurious_rate': fields['empty_spurious_rate'] <= t['empty_field_spurious_rate_max'],
        'adapter_fusion_contract': not fields['contract_errors'],
        'simulation_vs_real_exercise_contrasts': all(r['gold_label'] == p['event_classifier']['label']
            for r, p in zip(rows, predictions) if r.get('family') in {'simulation', 'exercise_only', 'real_during_exercise'}),
    }
    return {'sena': sena, 'nara': nara, 'fields': fields, 'checks': checks,
            'metric_targets_met': all(checks.values()), 'quality_acceptance_approved': False,
            'card_done': False, 'decision': 'READY_FOR_HUMAN_ACCEPTANCE' if all(checks.values()) else 'REQUIRES_QUALITY_IMPROVEMENT',
            'scope': protocol['scope'], 'limitations': protocol['limitations']}


def run(args):
    out = Path(args.output)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Gunakan direktori bukti baru')
    out.mkdir(parents=True, exist_ok=True)
    status = {'schema': 'slr09-acceptance-workflow-0.4', 'status': 'RUNNING', 'phase': 'PREFLIGHT_REVIEW',
              'started_at': utc(), 'model_inference_executed': False, 'training_executed': False,
              'quality_acceptance_approved': False, 'card_done': False, 'target_vm_verified': False,
              'environment_scope': 'REPRESENTATIVE', 'environment_label': args.environment_label}
    runner = None
    try:
        bundle = json.loads(Path(args.review).read_text(encoding='utf-8'))
        rows, preflight = validate(bundle, args.root)
        write(out / 'reviewed_bundle_frozen.json', bundle)
        write(out / 'preflight.json', preflight)
        lock = {'frozen_at': utc(), 'bundle_sha256': digest(bundle), 'review_file_sha256': file_sha(args.review),
                'model_and_code_binding': bundle['protocol']['binding'], 'threshold': .95,
                'test_not_used_for_checkpoint_selection': True,
                'initial_training_membership_verified': False, 'notes': 'Exact overlap checks only; synthetic pilot, not a population estimate'}
        write(out / 'evaluation_lock.json', lock)
        status['frozen_bundle_sha256'] = lock['bundle_sha256']
        if args.validate_only:
            status.update(status='PREFLIGHT_SUCCEEDED', phase='NO_MODEL_REQUESTED')
            return status
        sys.path.insert(0, str(args.root / 'code/active_nara_adapter'))
        from slr09_candidate_runtime import CandidateModelRunner, candidate_record, extract_candidate_archive, selected_assets
        from silar_ai_adapter import TOKEN_PATTERN
        from slr09_runtime import validate_prediction, environment_snapshot
        # Jangan mengubah tokenisasi diam-diam saat memberi skor.
        for row in rows:
            if [(m.start(), m.end()) for m in TOKEN_PATTERN.finditer(row['text'])] != [(m.start(), m.end()) for m in token_items(row['text'])]:
                raise ValueError('Tokenisasi evaluator berbeda dari serving')
        config, asset_lock, _ = selected_assets(args.root)
        status['phase'] = 'VERIFY_ARCHIVES'
        extraction = {}
        for name, source in [('sena', args.sena_zip), ('nara', args.nara_zip)]:
            if source is None:
                raise ValueError('Path kedua arsip diperlukan')
            extraction[name] = extract_candidate_archive(source, out / 'runtime' / name, name, asset_lock['models'][name])
        write(out / 'extraction_evidence.json', extraction)
        status['phase'] = 'LOAD_MODELS'
        runner = CandidateModelRunner(out / 'runtime/sena', out / 'runtime/nara', root=args.root, device=args.device, cpu_threads=2 if args.device == 'cpu' else None)
        status['models'] = runner.model_evidence
        status['environment'] = environment_snapshot(runner.torch, runner.device)
        status['phase'] = 'INFERENCE'
        predictions = []
        with (out / 'predictions.jsonl').open('x', encoding='utf-8') as stream:
            for i, row in enumerate(rows, 1):
                event, sena_coverage = runner.predict_sena(row['text'])
                status['model_inference_executed'] = True
                validate_prediction(event)
                tokens, nara_coverage = runner.predict_nara(row['text'])
                pred = candidate_record(row, event, tokens, config, asset_lock)
                pred.update(nara_tokens=tokens, sena_token_coverage=sena_coverage, nara_token_coverage=nara_coverage)
                predictions.append(pred)
                stream.write(json.dumps(pred, ensure_ascii=False, allow_nan=False) + '\n'); stream.flush()
                status['records_completed'] = i
                if i == 1 or i % 10 == 0 or i == len(rows):
                    print('Evaluasi', i, '/', len(rows), flush=True)
        status['phase'] = 'SCORING'
        if digest(bundle) != lock['bundle_sha256'] or file_sha(args.review) != lock['review_file_sha256']:
            raise ValueError('Acuan/protokol berubah setelah inferensi dimulai')
        report = score(rows, predictions, bundle['protocol'])
        report.update(preflight=preflight, frozen_bundle_sha256=lock['bundle_sha256'], predictions_sha256=file_sha(out / 'predictions.jsonl'))
        write(out / 'evaluation.json', report)
        write(out / 'errors_for_development_next_round.json', {
            'scope': 'SEEN_TEST_ERRORS_NOT_ALLOWED_IN_A_REUSED_BLIND_TEST',
            'sena': report['sena']['errors'], 'nara': report['nara']['errors'], 'fields': report['fields']['errors'],
            'rule': 'Jika dipakai untuk perbaikan, pensiunkan test ini dan siapkan acuan penerimaan baru.'})
        status.update(status='SUCCEEDED', phase='COMPLETE', metric_targets_met=report['metric_targets_met'], decision=report['decision'])
        return status
    except Exception as error:
        status.update(status='FAILED', error={'type': type(error).__name__, 'message': str(error)})
        (out / 'error_trace.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        status['finished_at'] = utc()
        write(out / 'workflow_result.json', status)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--sena-zip', type=Path)
    p.add_argument('--nara-zip', type=Path)
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--environment-label', default='GOOGLE_COLAB_CPU')
    p.add_argument('--validate-only', action='store_true')
    args = p.parse_args(argv)
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, KeyError, OSError) as e:
        print('Evaluasi belum berhasil:', e, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
