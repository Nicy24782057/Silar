"""Recompute persisted results and check separation of development/test sources."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from evaluate_acceptance import score, classification


def check(root=ROOT):
    evidence=root/'evidence/quality_fix_v05'
    old=evidence/'previous_50';new=evidence/'quality_diagnostics_v05'
    read=lambda p:json.loads(p.read_text())
    jsonl=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    bundle=read(old/'reviewed_bundle_frozen.json');pred=jsonl(new/'predictions.jsonl')
    recorded=read(new/'evaluation.json');actual=score(bundle['records'],pred,bundle['protocol'])
    for key in ('sena','nara','fields','checks','metric_targets_met'):
        assert actual[key]==recorded[key],key
    assert recorded['quality_acceptance_approved'] is False and recorded['card_done'] is False
    assert (old/'reviewed_bundle_frozen.json').read_bytes()==(new/'reviewed_bundle_frozen.json').read_bytes()
    fresh=read(new/'fresh_challenge_frozen.json')
    fresh_actual=classification(fresh['records'],read(new/'fresh_predictions.json'))
    fresh_recorded=read(new/'fresh_challenge_evaluation.json')
    for key in fresh_actual:assert fresh_actual[key]==fresh_recorded[key],key
    # Replay must leave original classifier and token predictions unchanged.
    original=jsonl(old/'predictions.jsonl');replayed=jsonl(evidence/'field_replay_final_v05/predictions.jsonl')
    assert len(original)==len(replayed)==50
    for a,b in zip(original,replayed):
        assert a['event_classifier']==b['event_classifier']
        assert a['nara_tokens']==b['nara_tokens']
    confidence_differences=[]
    for current,previous in zip(pred,original):
        assert len(current['nara_tokens'])==len(previous['nara_tokens'])
        for a,b in zip(current['nara_tokens'],previous['nara_tokens']):
            assert {k:v for k,v in a.items() if k!='confidence'}=={k:v for k,v in b.items() if k!='confidence'}
            confidence_differences.append(abs(a['confidence']-b['confidence']))
    # Different CPU/Python builds need not yield bit-identical float32 scores.
    assert max(confidence_differences)<=1e-5
    # Check old known data, auxiliary training and both diagnostics for exact overlap.
    norm=lambda s:' '.join(s.casefold().split())
    known=set()
    for part in ('train','validation'):
        known|={norm(x['text']) for x in jsonl(root/f'data/sena_{part}_reviewed.jsonl')}
    auxiliary=read(evidence/'training_run_20261019_cpu/training_auxiliary.json')
    known|={norm(x['text']) for x in auxiliary}
    pilot={norm(x['text']) for x in bundle['records']}
    fresh_texts={norm(x['text']) for x in fresh['records']}
    assert not known&pilot and not known&fresh_texts and not pilot&fresh_texts
    a=read(evidence/'training_run_20261019_cpu/development_split.json')
    b=read(evidence/'training_run_20261019_cpu_focus/development_split.json')
    assert a==b
    for folder in ('training_run_20261019_cpu','training_run_20261019_cpu_focus','prior_adjustment_20261019_cpu'):
        state=read(evidence/folder/'run_state.json')
        assert state['status']=='SUCCEEDED'
        assert not state['pilot50_used_for_training_or_checkpoint_selection']
    assert read(evidence/'contract_tests_v05/active_tests.json')['all_passed']
    assert hashlib.sha256((root/'code/active_nara_adapter/legacy_postprocessing.py').read_bytes()).hexdigest()=='06275b3aa338718689fba66984626754e6b34739156f65e378ceaad4b06bfa9f'
    result={'evidence_recomputed':True,'gold_and_legacy_helper_unchanged':True,
            'replayed_raw_predictions_unchanged':True,'nara_token_labels_and_offsets_reproduced_exactly':True,
            'nara_confidence_max_absolute_difference':max(confidence_differences),
            'nara_confidence_comparison_tolerance':1e-5,
            'exact_overlap_found':False,'development_split_unchanged':True,
            'seen_pilot_targets_met':actual['metric_targets_met'],
            'fresh_assistant_challenge_macro_f1':fresh_actual['macro_f1'],
            'fresh_challenge_human_reviewed':False,'quality_acceptance_approved':False,'card_done':False}
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':check()
