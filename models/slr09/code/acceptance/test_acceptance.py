"""Uji metrik dan penolakan acuan; seluruh prediksi fixture, bukan AI aktual."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluate_acceptance import ROOT, LABELS, FIELDS, validate, score, token_items, run, classification

sys.path.insert(0, str(ROOT / 'code/active_nara_adapter'))
from silar_ai_adapter import TOKEN_PATTERN


def reviewed():
    x = json.loads((ROOT / 'acceptance/review_bundle_draft.json').read_text())
    # Identitas ini hanya fixture dalam memori; tidak pernah disimpan sebagai review pengguna.
    now = datetime.now(timezone.utc).isoformat()
    x['protocol']['approval'].update(status='APPROVED', reviewer='FIXTURE ONLY', at=now,
        limitations_accepted=True, representativeness_accepted=True, rationale='Synthetic unit fixture; not a real group approval.')
    for row in x['records']:
        row['review'].update(status='APPROVED', reviewer='FIXTURE ONLY', at=now)
    return x


def perfect(rows):
    result = []
    for row in rows:
        label = row['gold_label']
        probs = {x:.98 if x==label else .005 for x in LABELS}
        fields = deepcopy(row['gold_fields'])
        result.append({'id':row['id'], 'input_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),
            'event_classifier':{'label':label,'confidence':.98,'probabilities':probs},
            'sena_token_coverage':{'truncated':False},
            'nara_token_coverage':{'all_regex_tokens_processed':True,'last_wordpiece_sequence_partial':False},
            'nara_tokens':[{'label':v,'original':m.group()} for v,m in zip(row['gold_nara_labels'],token_items(row['text']))],
            'adapted_result':{'nara_result':{'normalized_output':fields}},
            'fusion_result':{'integration_signals':{'blocked_by_non_event':label=='NON_EVENT'},
              'incident_card_version_fields':{'data':{'event_type':None if label=='NON_EVENT' else label,**deepcopy(fields)},'uncertain':False,'uncertain_reasons':[]}}})
    return result


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.bundle=reviewed()
        self.rows=self.bundle['records']
        self.pred=perfect(self.rows)

    def test_draft_rejected_before_model_load(self):
        x=json.loads((ROOT/'acceptance/review_bundle_draft.json').read_text())
        with self.assertRaisesRegex(ValueError,'belum direview'):
            validate(x)

    def test_approved_fixture_validates_full_coverage(self):
        rows,report=validate(self.bundle)
        self.assertEqual(len(rows),50)
        self.assertEqual(set(report['role_support']),set(x['label'] for p in self.pred for x in p['nara_tokens']))

    def test_empty_binding_cannot_disable_identity_guard(self):
        self.bundle['protocol']['binding']={'files_sha256':{}}
        with self.assertRaisesRegex(ValueError,'Binding'):
            validate(self.bundle)

    def test_known_input_cannot_become_held_out(self):
        known=json.loads((ROOT/'data/sena_validation_reviewed.jsonl').read_text().splitlines()[0])
        self.rows[0]['text']=known['text'].upper()
        with self.assertRaisesRegex(ValueError,'historis'):
            validate(self.bundle)

    def test_duplicates_rejected_even_with_new_id(self):
        self.rows[1]['text']='  '+self.rows[0]['text'].upper()+'  '
        with self.assertRaisesRegex(ValueError,'duplikat'):
            validate(self.bundle)

    def test_unreviewed_row_cannot_be_silently_omitted(self):
        self.rows[0]['review']['status']='PENDING'
        with self.assertRaisesRegex(ValueError,'belum direview'):
            validate(self.bundle)

    def test_deferred_preserved_and_coverage_cannot_silently_drop(self):
        self.rows[0]['review'].update(status='DEFERRED',note='Ambiguous fixture')
        with self.assertRaisesRegex(ValueError,'Cakupan kelas'):
            validate(self.bundle)

    def test_unfounded_field_rejected(self):
        self.rows[0]['gold_fields']['location_text']='Lokasi buatan tidak ada pada sumber'
        with self.assertRaisesRegex(ValueError,'bersumber'):
            validate(self.bundle)

    def test_tokenization_matches_active_serving(self):
        for text in [r['text'] for r in self.rows]+["anak-anak O'Brien pukul 10:30, RT 03/RW 04."]:
            self.assertEqual([m.group() for m in token_items(text)],[m.group() for m in TOKEN_PATTERN.finditer(text)])

    def test_perfect_fixture_meets_metrics_without_auto_acceptance(self):
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertTrue(report['metric_targets_met'])
        self.assertFalse(report['quality_acceptance_approved'])
        self.assertFalse(report['card_done'])
        self.assertEqual(report['nara']['macro_f1_all_14_non_o'],1)
        self.assertEqual(report['fields']['nonempty_exact'],1)

    def test_synthetic_false_event_fails_critical_contrast(self):
        i=next(i for i,r in enumerate(self.rows) if r['family']=='simulation')
        p=self.pred[i]
        p['event_classifier']={'label':'FIRE','confidence':.98,'probabilities':{x:.98 if x=='FIRE' else .005 for x in LABELS}}
        p['fusion_result']['integration_signals']['blocked_by_non_event']=False
        p['fusion_result']['incident_card_version_fields']['data']['event_type']='FIRE'
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertEqual(report['sena']['false_event'],1)
        self.assertEqual(report['sena']['high_confidence_errors'],1)
        self.assertFalse(report['checks']['simulation_vs_real_exercise_contrasts'])
        self.assertFalse(report['metric_targets_met'])

    def test_empty_matches_do_not_hide_missing_nonempty_fields(self):
        for p in self.pred:
            empty={x:None if x in FIELDS[:3] else [] for x in FIELDS}
            p['adapted_result']['nara_result']['normalized_output']=empty
            p['fusion_result']['incident_card_version_fields']['data'].update(empty)
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertEqual(report['fields']['nonempty_exact'],0)
        self.assertFalse(report['checks']['fields_nonempty_exact'])

    def test_truncation_refuses_quality_pass(self):
        self.pred[0]['nara_token_coverage']['last_wordpiece_sequence_partial']=True
        with self.assertRaisesRegex(ValueError,'terpotong'):
            score(self.rows,self.pred,self.bundle['protocol'])

    def test_wrong_input_hash_refused(self):
        self.pred[0]['input_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'bukan untuk'):
            score(self.rows,self.pred,self.bundle['protocol'])

    def test_threshold_equality_does_not_flag_low(self):
        for p in self.pred:
            label=p['event_classifier']['label']
            p['event_classifier'].update(confidence=.95,probabilities={x:.95 if x==label else .0125 for x in LABELS})
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertEqual(report['sena']['threshold_analysis']['flagged'],0)
        self.assertTrue(report['checks']['adapter_fusion_contract'])

    def test_invalid_uncertain_flag_detected(self):
        self.pred[0]['fusion_result']['incident_card_version_fields']['uncertain']=True
        report=score(self.rows,self.pred,self.bundle['protocol'])
        self.assertFalse(report['checks']['adapter_fusion_contract'])

    def test_failures_export_failed_without_inference_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            args=SimpleNamespace(root=ROOT,review=ROOT/'acceptance/review_bundle_draft.json',output=base/'evidence',validate_only=True,
                                 environment_label='UNIT_FIXTURE',sena_zip=None,nara_zip=None,device='cpu')
            with self.assertRaises(ValueError):
                run(args)
            report=json.loads((args.output/'workflow_result.json').read_text())
            self.assertEqual(report['status'],'FAILED')
            self.assertFalse(report['model_inference_executed'])
            self.assertFalse(report['quality_acceptance_approved'])

    def test_misclassification_calibration_diagnostics_have_correct_denominator(self):
        report=classification(self.rows,self.pred)
        self.assertAlmostEqual(report['reliability']['ten_bin_ece'],.02)
        self.assertAlmostEqual(report['reliability']['multiclass_brier_sum_over_classes'],.0005)

    def test_driver_fixture_end_to_end_does_not_auto_accept(self):
        import slr09_candidate_runtime as runtime
        import slr09_runtime
        by_text={r['text']:(r,p) for r,p in zip(self.rows,self.pred)}
        class FakeRunner:
            model_evidence={'scope':'UNIT_FIXTURE_NO_MODEL_WEIGHTS'}
            torch=None
            device='cpu'
            def __init__(self,*a,**kw):pass
            def predict_sena(self,text):
                p=by_text[text][1]
                return deepcopy(p['event_classifier']),deepcopy(p['sena_token_coverage'])
            def predict_nara(self,text):
                p=by_text[text][1]
                return deepcopy(p['nara_tokens']),deepcopy(p['nara_token_coverage'])
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            ref=base/'review.json';ref.write_text(json.dumps(self.bundle))
            args=SimpleNamespace(root=ROOT,review=ref,output=base/'evidence',validate_only=False,
                environment_label='UNIT_FIXTURE',sena_zip=base/'fake-sena',nara_zip=base/'fake-nara',device='cpu')
            with patch.object(runtime,'CandidateModelRunner',FakeRunner), \
                 patch.object(runtime,'extract_candidate_archive',return_value={'scope':'UNIT_FIXTURE'}), \
                 patch.object(runtime,'candidate_record',side_effect=lambda row,*a:deepcopy(by_text[row['text']][1])), \
                 patch.object(slr09_runtime,'environment_snapshot',return_value={'scope':'UNIT_FIXTURE'}):
                status=run(args)
            report=json.loads((args.output/'evaluation.json').read_text())
            self.assertEqual(status['status'],'SUCCEEDED')
            self.assertTrue(report['metric_targets_met'])
            self.assertFalse(report['card_done'])
            self.assertTrue((args.output/'evaluation_lock.json').is_file())

    def test_archive_failure_exports_failed_after_freezing_review(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            ref=base/'review.json';ref.write_text(json.dumps(self.bundle))
            args=SimpleNamespace(root=ROOT,review=ref,output=base/'evidence',validate_only=False,
                environment_label='UNIT_FIXTURE',sena_zip=base/'missing-sena.zip',nara_zip=base/'missing-nara.zip',device='cpu')
            with self.assertRaises((OSError, ValueError)):
                run(args)
            report=json.loads((args.output/'workflow_result.json').read_text())
            self.assertEqual(report['status'],'FAILED')
            self.assertFalse(report['model_inference_executed'])
            self.assertTrue((args.output/'evaluation_lock.json').is_file())


if __name__=='__main__':
    unittest.main(verbosity=2)
