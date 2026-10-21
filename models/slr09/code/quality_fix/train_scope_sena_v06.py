"""Train contextual SENA from verified pre-bias weights on CPU.

Human references remain unchanged. Additional training/development labels are
assistant proposals. Neither the seen 24 nor the new 50 are used for checkpoint
or intercept selection. No human quality approval is granted by this script.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path
import time
import traceback

from train_sena_cpu import LABELS, metrics, write, sha


def normal(text):return ' '.join(text.casefold().split())


def score_probs(rows, probabilities):
    return metrics([r['final'] for r in rows],[LABELS[max(range(5),key=lambda j:p[j])] for p in probabilities])


def shifted(probabilities,bias):
    output=[]
    for p in probabilities:
        weighted=[v*math.exp(bias if i==4 else 0.) for i,v in enumerate(p)]
        total=sum(weighted);output.append([v/total for v in weighted])
    return output


def joint(human,scope):
    return min(human['predeclared_selection_metric'],scope['predeclared_selection_metric'])


def run(root,warm,out):
    out.mkdir(parents=True,exist_ok=False)
    status={'schema':'slr09-scope-training-0.6','status':'PREPARING',
      'source':'VERIFIED_CPU_FOCUS_CHECKPOINT_BEFORE_V05_NON_EVENT_BIAS',
      'training_executed':False,'quality_acceptance_approved':False,'card_done':False,
      'seen24_used_for_training_or_selection':False,'new50_used_for_training_or_selection':False,
      'pilot50_used_for_training_or_checkpoint_selection':False,
      'assistant_examples_human_reviewed':False,'started_at':datetime.now(timezone.utc).isoformat()}
    write(out/'run_state.json',status)
    try:
        spec=json.loads((warm/'source_manifest.json').read_text())
        for name,h in spec['files'].items():
            if sha(warm/name)!=h:raise ValueError('Warm start identity mismatch: '+name)
        write(out/'warm_start_identity.json',spec)
        source={r['id']:r for part in ('train','validation')
                for line in (root/f'data/sena_{part}_reviewed.jsonl').read_text().splitlines()
                if line.strip() for r in [json.loads(line)]}
        split=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/development_split.json').read_text())
        train=[dict(source[i],label_origin='PREVIOUS_HUMAN_REVIEWED_SOURCE') for i in split['training_ids'] if i in source]
        human=[source[i] for i in split['validation_ids']]
        old_aux=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/training_auxiliary.json').read_text())
        aux=json.loads((root/'data/scope_v06_training.json').read_text())['records']
        scope=json.loads((root/'data/scope_v06_development.json').read_text())['records']
        train += [dict(r,label_origin='ASSISTANT_PROPOSAL_NOT_HUMAN_GOLD') for r in old_aux+aux]
        assert len(human)==146 and len(train)==1128 and len(scope)==128
        groups=[{normal(r['text']) for r in rows} for rows in (train,human,scope)]
        assert all(not groups[a]&groups[b] for a in range(3) for b in range(a+1,3))
        for rows in (train,human,scope):assert len({r['id'] for r in rows})==len(rows)
        config={'seed':67,'cpu_threads':2,'max_length':192,'batch_size':8,'max_epochs':4,'patience':2,
          'trainable_encoder_layers':'LAST_FOUR_ONLY','encoder_learning_rate':1e-5,'head_learning_rate':3e-5,
          'non_event_class_weight_multiplier':1.5,'assistant_loss_weight':.75,
          'weight_decay':.01,'warmup_fraction':.10,'linear_learning_rate_decay':True,
          'bias_grid':[round(-.5+i*.1,2) for i in range(21)],
          'selection':'MAXIMUM_WORST_TARGET_RATIO_ACROSS_HUMAN146_AND_ASSISTANT_SCOPE128; TIE_HUMAN_MACRO_F1_THEN_SMALLEST_ABS_BIAS',
          'targets_unchanged':{'macro_f1':.85,'non_event_recall':.90,'event_class_recall':.80},
          'checkpoint_and_bias_fitting_data':'DEVELOPMENT_ONLY_NOT_INDEPENDENT',
          'confidence_cutoff_unchanged':.95,'probability_calibration_established':False,
          'training_source_sha256':sha(Path(__file__)),
          'training_auxiliary_sha256':sha(root/'data/scope_v06_training.json'),
          'assistant_development_sha256':sha(root/'data/scope_v06_development.json')}
        write(out/'training_config.json',config)
        write(out/'training_records_frozen.json',train)
        write(out/'human_development_frozen.json',human)
        write(out/'scope_development_frozen.json',scope)
        write(out/'development_split.json',{'human_training_ids':[r['id'] for r in train if r['label_origin']=='PREVIOUS_HUMAN_REVIEWED_SOURCE'],
             'human_development_ids':[r['id'] for r in human],
             'assistant_training_records':len(aux)+len(old_aux),'assistant_development_records':len(scope),
             'new_human_review_completed':False,'seen24_or_new50_used':False})
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
        set_seed(config['seed']);torch.set_num_threads(config['cpu_threads'])
        tokenizer=AutoTokenizer.from_pretrained(warm,local_files_only=True,trust_remote_code=False)
        model,loading=AutoModelForSequenceClassification.from_pretrained(warm,local_files_only=True,use_safetensors=True,output_loading_info=True)
        if any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):raise RuntimeError('Incomplete warm-start loading')
        if model.config.id2label!={i:c for i,c in enumerate(LABELS)}:raise ValueError('Label order mismatch')
        for p in model.parameters():p.requires_grad=False
        for layer in model.bert.encoder.layer[-4:]:
            for p in layer.parameters():p.requires_grad=True
        for module in (model.bert.pooler,model.classifier):
            for p in module.parameters():p.requires_grad=True
        head=list(model.classifier.parameters());head_ids={id(p) for p in head}
        other=[p for p in model.parameters() if p.requires_grad and id(p) not in head_ids]
        optimizer=torch.optim.AdamW([{'params':other,'lr':config['encoder_learning_rate']},
                                    {'params':head,'lr':config['head_learning_rate']}],weight_decay=config['weight_decay'])
        total_steps=((len(train)+7)//8)*config['max_epochs'];warmup=max(1,int(total_steps*.10))
        def lr_scale(step):
            if step<warmup:return (step+1)/warmup
            return max(0.,(total_steps-step)/max(1,total_steps-warmup))
        scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lr_scale)
        counts=Counter(r['final'] for r in train)
        class_weights=torch.tensor([len(train)/(5*counts[c])*(1.5 if c=='NON_EVENT' else 1.) for c in LABELS])
        def encode(rows):return tokenizer([r['text'] for r in rows],padding=True,truncation=True,max_length=192,return_tensors='pt')
        def probabilities(rows):
            model.eval();probs=[]
            with torch.inference_mode():
                for start in range(0,len(rows),16):probs+=torch.softmax(model(**encode(rows[start:start+16])).logits,-1).tolist()
            return probs
        def evaluate():
            hp,sp=probabilities(human),probabilities(scope)
            grid=[]
            for b in config['bias_grid']:
                h,s=score_probs(human,shifted(hp,b)),score_probs(scope,shifted(sp,b))
                grid.append({'bias':b,'joint_score':joint(h,s),'human':h,'scope':s})
            selected=max(grid,key=lambda x:(x['joint_score'],x['human']['macro_f1'],-abs(x['bias'])))
            return selected,hp,sp,grid
        best_key=None;history=[];stale=0
        def save_candidate(epoch,selected,hp,sp,grid):
            nonlocal best_key
            best_key=(selected['joint_score'],selected['human']['macro_f1'],-abs(selected['bias']))
            exported={k:v.detach().cpu() for k,v in model.state_dict().items()}
            exported['classifier.bias']=exported['classifier.bias'].clone()
            exported['classifier.bias'][4]+=selected['bias']
            model.save_pretrained(out/'best_model',state_dict=exported,safe_serialization=True)
            tokenizer.save_pretrained(out/'best_model')
            write(out/'best_development_metrics.json',selected['human'])
            write(out/'best_scope_development_metrics.json',selected['scope'])
            write(out/'best_selection.json',{'epoch':epoch,'bias':selected['bias'],'joint_score':selected['joint_score'],
                                           'all_development_targets_met':selected['joint_score']>=1.,'human_reference_approval_of_auxiliary':False})
            write(out/'best_bias_grid.json',grid)
            for name,rows,probs in [('human',human,hp),('scope',scope,sp)]:
                shifted_probs=shifted(probs,selected['bias'])
                write(out/f'best_{name}_development_predictions.json',[{'id':r['id'],'text':r['text'],'gold':r['final'],'probabilities':dict(zip(LABELS,p))} for r,p in zip(rows,shifted_probs)])
            status.update(best_epoch=epoch,selected_head_bias=selected['bias'],best_joint_score=selected['joint_score'])
        selected,hp,sp,grid=evaluate();save_candidate(0,selected,hp,sp,grid)
        write(out/'baseline_metrics.json',{'human':score_probs(human,hp),'scope':score_probs(scope,sp)})
        status.update(status='TRAINING',training_records=len(train),human_development_records=len(human),assistant_development_records=len(scope),trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))
        write(out/'run_state.json',status)
        for epoch in range(1,config['max_epochs']+1):
            started=time.time();model.train();order=torch.randperm(len(train));loss_sum=0.
            for step,start in enumerate(range(0,len(train),8),1):
                batch=[train[int(i)] for i in order[start:start+8]]
                inputs=encode(batch);gold=torch.tensor([LABELS.index(r['final']) for r in batch])
                weight=torch.tensor([1. if r['label_origin']=='PREVIOUS_HUMAN_REVIEWED_SOURCE' else .75 for r in batch])
                optimizer.zero_grad(set_to_none=True)
                logits=model(**inputs).logits
                loss=(torch.nn.functional.cross_entropy(logits,gold,weight=class_weights,reduction='none')*weight).sum()/weight.sum()
                if not torch.isfinite(loss):raise RuntimeError('Non-finite training loss')
                loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step();scheduler.step()
                status['training_executed']=True;loss_sum+=float(loss.detach())
                if step==1 or step%10==0:
                    status.update(epoch=epoch,step=step,steps_in_epoch=(len(train)+7)//8,loss=float(loss.detach()))
                    write(out/'run_state.json',status)
                    print(f'epoch {epoch} step {step}/{status["steps_in_epoch"]} loss {float(loss.detach()):.4f}',flush=True)
            selected,hp,sp,grid=evaluate()
            history.append({'epoch':epoch,'training_loss':loss_sum/step,'seconds':time.time()-started,**selected})
            write(out/'training_history.json',history)
            key=(selected['joint_score'],selected['human']['macro_f1'],-abs(selected['bias']))
            if key>best_key:save_candidate(epoch,selected,hp,sp,grid);stale=0
            else:stale+=1
            print(json.dumps({'epoch':epoch,'human_f1':selected['human']['macro_f1'],'human_ne_recall':selected['human']['per_class']['NON_EVENT']['recall'],
                 'scope_f1':selected['scope']['macro_f1'],'scope_ne_recall':selected['scope']['per_class']['NON_EVENT']['recall'],
                 'scope_min_event_recall':min(selected['scope']['per_class'][c]['recall'] for c in LABELS[:-1]),
                 'bias':selected['bias'],'joint_target_ratio':selected['joint_score']},ensure_ascii=False),flush=True)
            if stale>=config['patience'] or selected['joint_score']>=1.:break
        status.update(status='SUCCEEDED',epochs_completed=len(history),model_exported=True,
                      finished_at=datetime.now(timezone.utc).isoformat())
        write(out/'run_state.json',status)
        return status
    except Exception as error:
        status.update(status='FAILED',error={'type':type(error).__name__,'message':str(error)})
        write(out/'run_state.json',status);(out/'error_trace.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--warm-start',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.root,a.warm_start,a.output),indent=2))
