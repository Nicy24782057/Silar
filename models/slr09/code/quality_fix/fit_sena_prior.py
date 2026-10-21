"""Fit one SENA head intercept on development data, never on pilot/fresh tests.

This changes a classifier parameter, not the Fusion confidence cutoff. The
development score is fitted performance and cannot be called an independent
validation or a probability-calibration result.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from train_sena_cpu import LABELS, metrics, write, sha


def fit(source, output):
    output.mkdir(parents=True,exist_ok=False)
    state={'status':'PREPARING','source':'DEVELOPMENT_FITTED_NON_EVENT_HEAD_INTERCEPT_FROM_CPU_FOCUS_RUN',
           'training_executed':False,'parameter_fit_executed':False,
           'encoder_gradient_training_executed':False,'development_is_used_for_fitting':True,
           'pilot50_used_for_training_or_checkpoint_selection':False,
           'fresh_challenge_used_for_selection':False,'independent_acceptance_test_executed':False,
           'quality_acceptance_approved':False,'started_at':datetime.now(timezone.utc).isoformat()}
    write(output/'run_state.json',state)
    records=json.loads((source/'best_development_predictions.json').read_text())
    config={'parameter':'classifier.bias[NON_EVENT]','candidates':[round(i*.05,2) for i in range(101)],
            'selection':'SMALLEST_NONNEGATIVE_BIAS_MEETING_ALL_UNCHANGED_DEVELOPMENT_TARGETS',
            'development_exploration_after_round2':True,'probability_calibration_established':False,
            'fusion_confidence_threshold_unchanged':.95,'targets':{'macro_f1':.85,'non_event_recall':.90,'min_event_recall':.80},
            'source_weights_sha256':sha(source/'best_model/model.safetensors'),
            'source_predictions_sha256':sha(source/'best_development_predictions.json')}
    write(output/'training_config.json',config)
    grid=[]
    for bias in config['candidates']:
        pred=[max(LABELS,key=lambda c:math.log(max(r['probabilities'][c],1e-30))+(bias if c=='NON_EVENT' else 0)) for r in records]
        grid.append({'bias':bias,**metrics([r['gold'] for r in records],pred)})
    write(output/'development_bias_grid.json',grid)
    feasible=[x for x in grid if x['targets_met']]
    if not feasible:
        state.update(status='NO_FEASIBLE_DEVELOPMENT_SETTING',parameter_fit_executed=False)
        write(output/'run_state.json',state)
        raise RuntimeError('No head intercept meets the unchanged development targets')
    selected=feasible[0]['bias']
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(source/'best_model',local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(source/'best_model',local_files_only=True,use_safetensors=True)
    if model.config.id2label!={i:c for i,c in enumerate(LABELS)}:raise ValueError('Label order mismatch')
    with torch.no_grad():model.classifier.bias[LABELS.index('NON_EVENT')].add_(selected)
    model.eval()
    encoded=tokenizer([r['text'] for r in records],padding=True,truncation=True,max_length=192,return_tensors='pt')
    probabilities=[]
    with torch.inference_mode():
        for start in range(0,len(records),16):
            p=torch.softmax(model(**{k:v[start:start+16] for k,v in encoded.items()}).logits,-1)
            probabilities+=p.tolist()
    predictions=[LABELS[max(range(5),key=lambda j:p[j])] for p in probabilities]
    actual=metrics([r['gold'] for r in records],predictions)
    if not actual['targets_met']:raise RuntimeError('Actual model does not reproduce feasible grid result')
    model.save_pretrained(output/'best_model',safe_serialization=True)
    tokenizer.save_pretrained(output/'best_model')
    write(output/'best_development_metrics.json',actual)
    write(output/'best_development_predictions.json',[{'id':r['id'],'text':r['text'],'gold':r['gold'],'probabilities':dict(zip(LABELS,p))} for r,p in zip(records,probabilities)])
    write(output/'baseline_development_metrics.json',json.loads((source/'best_development_metrics.json').read_text()))
    write(output/'development_split.json',json.loads((source/'development_split.json').read_text()))
    state.update(status='SUCCEEDED',parameter_fit_executed=True,selected_non_event_head_bias=selected,
                 model_exported=True,finished_at=datetime.now(timezone.utc).isoformat())
    write(output/'run_state.json',state)
    print(json.dumps({'bias_added_to_non_event_head':selected,'development':actual,
          'development_is_fitted_not_independent':True,'fusion_confidence_cutoff':.95},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();fit(a.source,a.output)
