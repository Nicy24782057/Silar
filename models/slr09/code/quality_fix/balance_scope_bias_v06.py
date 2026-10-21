"""Exploratory development-only intercept fit with two separate guard sets.

This extends the first training run's bounded intercept search after observing
development results. It is not preregistered independent evidence. Neither
the previous24 nor the new50 diagnostic is read or used for selection.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
from train_sena_cpu import LABELS,metrics,write,sha
from train_scope_sena_v06 import shifted,joint


def balance(source,output):
    output.mkdir(parents=True,exist_ok=False)
    source_state=json.loads((source/'run_state.json').read_text())
    if source_state['status']!='SUCCEEDED':raise ValueError('Source training not complete')
    old_selection=json.loads((source/'best_selection.json').read_text())
    state={'schema':'slr09-scope-intercept-fit-0.6','status':'PREPARING',
           'source':'SCOPE_TRAINED_CPU_MODEL_WITH_JOINT_DEVELOPMENT_INTERCEPT_FIT',
           'started_at':datetime.now(timezone.utc).isoformat(),
           'training_executed':False,'parameter_fit_executed':False,'source_gradient_training_executed':True,
           'quality_acceptance_approved':False,'card_done':False,
           'seen24_used_for_training_or_selection':False,'new50_used_for_training_or_selection':False,
           'assistant_examples_human_reviewed':False}
    write(output/'run_state.json',state)
    hp=json.loads((source/'best_human_development_predictions.json').read_text())
    sp=json.loads((source/'best_scope_development_predictions.json').read_text())
    hg=[x['gold'] for x in hp];sg=[x['gold'] for x in sp]
    hpv=[[x['probabilities'][c] for c in LABELS] for x in hp]
    spv=[[x['probabilities'][c] for c in LABELS] for x in sp]
    config={'additional_bias_grid':[round(-1.5+i*.1,2) for i in range(46)],
            'source_initial_bias':old_selection['bias'],
            'selection':'MAX_WORST_TARGET_RATIO_ON_HUMAN146_AND_ASSISTANT128; TIE_MIN_ABS_ADDITIONAL_BIAS_THEN_HUMAN_F1',
            'exploratory_extension_after_development_inspection':True,
            'no_new_diagnostic_used':True,'fusion_confidence_cutoff_unchanged':.95,
            'source_weights_sha256':sha(source/'best_model/model.safetensors'),
            'parameter_fitting_source_sha256':sha(Path(__file__)),
            'probability_calibration_established':False,
            'targets_unchanged':{'macro_f1':.85,'non_event_recall':.90,'event_class_recall':.80}}
    write(output/'training_config.json',config)
    def metric(gold,probs):return metrics(gold,[LABELS[max(range(5),key=lambda i:p[i])] for p in probs])
    grid=[]
    for b in config['additional_bias_grid']:
        hm,sm=metric(hg,shifted(hpv,b)),metric(sg,shifted(spv,b))
        grid.append({'additional_bias':b,'joint_score':joint(hm,sm),'human':hm,'scope':sm})
    selected=max(grid,key=lambda x:(x['joint_score'],-abs(x['additional_bias']),x['human']['macro_f1']))
    write(output/'development_intercept_grid.json',grid)
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(source/'best_model',local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(source/'best_model',local_files_only=True,use_safetensors=True)
    with torch.no_grad():model.classifier.bias[4]+=selected['additional_bias']
    model.save_pretrained(output/'best_model',safe_serialization=True);tokenizer.save_pretrained(output/'best_model')
    for name,rows,probabilities in [('human',hp,hpv),('scope',sp,spv)]:
        for record,p in zip(rows,shifted(probabilities,selected['additional_bias'])):record['probabilities']=dict(zip(LABELS,p))
        write(output/f'best_{name}_development_predictions.json',rows)
    write(output/'best_development_metrics.json',selected['human'])
    write(output/'best_scope_development_metrics.json',selected['scope'])
    write(output/'best_selection.json',{'epoch':old_selection['epoch'],
        'bias':round(old_selection['bias']+selected['additional_bias'],2),
        'initial_bias':old_selection['bias'],'additional_bias':selected['additional_bias'],
        'joint_score':selected['joint_score'],'all_development_targets_met':selected['joint_score']>=1.,
        'human_reference_approval_of_auxiliary':False,'exploratory_development_fit':True})
    for name in ('human_development_frozen.json','scope_development_frozen.json','development_split.json','warm_start_identity.json'):
        shutil.copy2(source/name,output/name)
    for name in ('training_config.json','training_history.json','run_state.json'):
        shutil.copy2(source/name,output/('source_'+name))
    state.update(status='SUCCEEDED',parameter_fit_executed=True,model_exported=True,
                 selected_additional_bias=selected['additional_bias'],selected_total_bias=round(old_selection['bias']+selected['additional_bias'],2),
                 best_joint_score=selected['joint_score'],finished_at=datetime.now(timezone.utc).isoformat())
    write(output/'run_state.json',state)
    print(json.dumps({'additional_bias':selected['additional_bias'],'total_bias':state['selected_total_bias'],
        'human_macro_f1':selected['human']['macro_f1'],'human_non_event_recall':selected['human']['per_class']['NON_EVENT']['recall'],
        'human_minimum_event_recall':min(selected['human']['per_class'][c]['recall'] for c in LABELS[:-1]),
        'scope_macro_f1':selected['scope']['macro_f1'],'joint_target_ratio':selected['joint_score'],
        'all_development_targets_met':selected['joint_score']>=1.,'quality_acceptance_approved':False},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();balance(a.source,a.output)
