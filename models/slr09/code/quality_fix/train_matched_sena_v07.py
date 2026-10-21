"""Bounded paired-scope experiment. Targets unchanged; no human acceptance.

The old assistant24 and v0.6 diagnostic50 are now development, explicitly.
New v0.7 diagnostic50 and original pilot50 never enter fitting or selection.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime,timezone
import json
import random
from pathlib import Path
import time
import traceback
from train_sena_cpu import LABELS,write,sha
from train_scope_sena_v06 import score_probs,shifted,joint,normal

def run(root,warm,out):
    out.mkdir(parents=True,exist_ok=False)
    state={'schema':'slr09-matched-training-0.7','status':'PREPARING',
        'source':'V06_EPOCH1_WARM_START_MANUAL_NE_BIAS_1.5_REMOVED_BEFORE_GRADIENTS',
        'training_executed':False,'quality_acceptance_approved':False,'card_done':False,
        'seen24_used_for_selection':True,'v06_new50_used_for_selection':True,
        'v07_new50_used_for_training_or_selection':False,
        'pilot50_used_for_training_or_checkpoint_selection':False,
        'assistant_examples_human_reviewed':False,'started_at':datetime.now(timezone.utc).isoformat()}
    write(out/'run_state.json',state)
    try:
        identity=json.loads((warm/'source_manifest.json').read_text())
        for name,digest in identity['files'].items():
            if sha(warm/name)!=digest:raise ValueError('Warm identity changed: '+name)
        if identity['manual_non_event_bias_to_remove']!=1.5:raise ValueError('Unexpected warm bias')
        write(out/'warm_start_identity.json',identity)
        source={r['id']:r for part in ('train','validation') for s in (root/f'data/sena_{part}_reviewed.jsonl').read_text().splitlines()
                if s.strip() for r in [json.loads(s)]}
        split=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/development_split.json').read_text())
        human_train=[dict(source[i],label_origin='PREVIOUS_HUMAN_REVIEWED_SOURCE') for i in split['training_ids'] if i in source]
        human=[source[i] for i in split['validation_ids']]
        old_aux=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/training_auxiliary.json').read_text())
        paired=json.loads((root/'data/matched_pairs_v07_training.json').read_text())['records']
        scope=json.loads((root/'data/mvp_seen_development_v07.json').read_text())['records']
        train=human_train+[dict(r,label_origin='ASSISTANT_PROPOSAL_NOT_HUMAN_GOLD') for r in old_aux+paired]
        assert len(human_train)==584 and len(human)==146 and len(train)==1160 and len(scope)==74
        groups=[{normal(r['text']) for r in rows} for rows in (train,human,scope)]
        assert all(not groups[i]&groups[j] for i in range(3) for j in range(i+1,3))
        guard=json.loads((root/'data/scope_v07_split_guard.json').read_text())
        assert sha(root/'data/frozen_new_diagnostic_v0.7.json')==guard['new50_sha256']
        config={'seed':79,'cpu_threads':2,'max_length':192,'batch_size_maximum':8,'max_epochs':3,'patience':1,
          'trainable_encoder_layers':'LAST_FOUR_ONLY','encoder_learning_rate':1e-5,'head_learning_rate':2e-5,
          'non_event_class_weight_multiplier':1.,'assistant_loss_weight':.5,
          'pair_loss_coefficient':.25,'pair_margin':2.,
          'pair_loss':'relu(margin - ((event-NE)_positive - (event-NE)_negative))',
          'weight_decay':.01,'warmup_fraction':.05,'linear_learning_rate_decay':True,
          'manual_warm_bias_removed':1.5,'bias_grid':[round(-.5+i*.1,2) for i in range(11)],
          'selection':'MAXIMUM_WORST_TARGET_RATIO_HUMAN146_AND_RETIRED_ASSISTANT74; TIE_HUMAN_MACRO_F1_THEN_SMALLEST_ABS_BIAS',
          'targets_unchanged':{'macro_f1':.85,'non_event_recall':.90,'event_class_recall':.80},
          'checkpoint_and_bias_fitting_data':'DEVELOPMENT_ONLY_NOT_INDEPENDENT',
          'confidence_cutoff_unchanged':.95,'probability_calibration_established':False,
          'training_source_sha256':sha(Path(__file__)),
          'training_auxiliary_sha256':sha(root/'data/matched_pairs_v07_training.json'),
          'assistant_development_sha256':sha(root/'data/mvp_seen_development_v07.json'),
          'prospective_diagnostic_sha256_not_loaded_for_fitting':guard['new50_sha256']}
        for name,data in [('training_config',config),('training_records_frozen',train),('human_development_frozen',human),('scope_development_frozen',scope)]:write(out/(name+'.json'),data)
        write(out/'development_split.json',{'human_training_ids':[r['id'] for r in human_train],
            'human_development_ids':[r['id'] for r in human],'assistant_training_records':len(old_aux)+len(paired),
            'assistant_development_records':len(scope),'new_human_review_completed':False,
            'seen24_and_v06_new50_retired_into_development':True,'v07_new50_used':False})
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
        set_seed(config['seed']);torch.set_num_threads(2)
        tokenizer=AutoTokenizer.from_pretrained(warm,local_files_only=True,trust_remote_code=False)
        model,loading=AutoModelForSequenceClassification.from_pretrained(warm,local_files_only=True,use_safetensors=True,output_loading_info=True)
        if any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):raise ValueError('Incomplete model load')
        if model.config.id2label!={i:c for i,c in enumerate(LABELS)}:raise ValueError('Wrong label order')
        with torch.no_grad():model.classifier.bias[4]-=1.5
        for p in model.parameters():p.requires_grad=False
        for layer in model.bert.encoder.layer[-4:]:
            for p in layer.parameters():p.requires_grad=True
        for module in (model.bert.pooler,model.classifier):
            for p in module.parameters():p.requires_grad=True
        head=list(model.classifier.parameters());headids={id(p) for p in head}
        other=[p for p in model.parameters() if p.requires_grad and id(p) not in headids]
        optimizer=torch.optim.AdamW([{'params':other,'lr':1e-5},{'params':head,'lr':2e-5}],weight_decay=.01)
        singles=[[r] for r in train if 'pair_id' not in r]
        pairs=defaultdict(list)
        for row in train:
            if 'pair_id' in row:pairs[row['pair_id']].append(row)
        assert len(pairs)==256 and all({r['polarity'] for r in rows}=={'P','N'} for rows in pairs.values())
        units=singles+list(pairs.values())
        def batches(epoch):
            order=list(units);random.Random(config['seed']+epoch).shuffle(order)
            result=[];batch=[]
            for unit in order:
                if len(batch)+len(unit)>8:result.append(batch);batch=[]
                batch+=unit
            if batch:result.append(batch)
            return result
        schedules=[batches(epoch) for epoch in range(1,4)]
        total=sum(map(len,schedules));warmup=max(1,int(total*.05))
        def lr_scale(step):return (step+1)/warmup if step<warmup else max(0.,(total-step)/max(1,total-warmup))
        scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lr_scale)
        counts=Counter(r['final'] for r in train)
        class_weights=torch.tensor([len(train)/(5*counts[c]) for c in LABELS])
        def encode(rows):return tokenizer([r['text'] for r in rows],padding=True,truncation=True,max_length=192,return_tensors='pt')
        def probabilities(rows):
            model.eval();output=[]
            with torch.inference_mode():
                for i in range(0,len(rows),16):output+=torch.softmax(model(**encode(rows[i:i+16])).logits,-1).tolist()
            return output
        def evaluate():
            hp,sp=probabilities(human),probabilities(scope);grid=[]
            for b in config['bias_grid']:
                h,s=score_probs(human,shifted(hp,b)),score_probs(scope,shifted(sp,b))
                grid.append({'bias':b,'joint_score':joint(h,s),'human':h,'scope':s})
            return max(grid,key=lambda r:(r['joint_score'],r['human']['macro_f1'],-abs(r['bias']))),hp,sp,grid
        best_key=None;history=[];stale=0
        def save_candidate(epoch,selected,hp,sp,grid):
            nonlocal best_key
            best_key=(selected['joint_score'],selected['human']['macro_f1'],-abs(selected['bias']))
            params={k:v.detach().cpu() for k,v in model.state_dict().items()}
            params['classifier.bias']=params['classifier.bias'].clone();params['classifier.bias'][4]+=selected['bias']
            model.save_pretrained(out/'best_model',state_dict=params,safe_serialization=True);tokenizer.save_pretrained(out/'best_model')
            write(out/'best_selection.json',{'epoch':epoch,'bias':selected['bias'],'joint_score':selected['joint_score'],
                'all_development_targets_met':selected['joint_score']>=1.,'human_reference_approval_of_auxiliary':False})
            write(out/'best_development_metrics.json',selected['human']);write(out/'best_scope_development_metrics.json',selected['scope'])
            write(out/'best_bias_grid.json',grid)
            for name,rows,p in [('human',human,hp),('scope',scope,sp)]:
                write(out/f'best_{name}_development_predictions.json',[
                    {'id':r['id'],'text':r['text'],'gold':r['final'],'probabilities':dict(zip(LABELS,v))}
                    for r,v in zip(rows,shifted(p,selected['bias']))])
            state.update(best_epoch=epoch,selected_head_bias=selected['bias'],best_joint_score=selected['joint_score'])
        selected,hp,sp,grid=evaluate();save_candidate(0,selected,hp,sp,grid)
        write(out/'baseline_metrics.json',{'human':score_probs(human,hp),'scope':score_probs(scope,sp)})
        state.update(status='TRAINING',training_records=len(train),human_development_records=146,
            assistant_development_records=74,matched_training_pairs=256,
            trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))
        write(out/'run_state.json',state)
        for epoch,epoch_batches in enumerate(schedules,1):
            started=time.time();model.train();loss_sum=pair_sum=0.
            for step,batch in enumerate(epoch_batches,1):
                optimizer.zero_grad(set_to_none=True);logits=model(**encode(batch)).logits
                gold=torch.tensor([LABELS.index(r['final']) for r in batch])
                weight=torch.tensor([1. if r['label_origin']=='PREVIOUS_HUMAN_REVIEWED_SOURCE' else .5 for r in batch])
                ce=(torch.nn.functional.cross_entropy(logits,gold,weight=class_weights,reduction='none')*weight).sum()/weight.sum()
                idx=defaultdict(dict)
                for i,r in enumerate(batch):
                    if 'pair_id' in r:idx[r['pair_id']][r['polarity']]=i
                terms=[]
                for p in idx.values():
                    assert set(p)=={'P','N'}
                    c=LABELS.index(batch[p['P']]['pair_category'])
                    delta=(logits[p['P'],c]-logits[p['P'],4])-(logits[p['N'],c]-logits[p['N'],4])
                    terms.append(torch.relu(2.-delta))
                pair_loss=torch.stack(terms).mean() if terms else logits.sum()*0.
                loss=ce+.25*pair_loss
                if not torch.isfinite(loss):raise RuntimeError('Non-finite loss')
                loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step();scheduler.step()
                state['training_executed']=True;loss_sum+=float(loss.detach());pair_sum+=float(pair_loss.detach())
                if step==1 or step%10==0:
                    state.update(epoch=epoch,step=step,steps_in_epoch=len(epoch_batches),loss=float(loss.detach()))
                    write(out/'run_state.json',state);print(f'epoch {epoch} step {step}/{len(epoch_batches)} loss {float(loss.detach()):.4f} pair {float(pair_loss.detach()):.4f}',flush=True)
            selected,hp,sp,grid=evaluate()
            history.append({'epoch':epoch,'training_loss':loss_sum/step,'pair_loss':pair_sum/step,'seconds':time.time()-started,**selected})
            write(out/'training_history.json',history)
            key=(selected['joint_score'],selected['human']['macro_f1'],-abs(selected['bias']))
            if key>best_key:save_candidate(epoch,selected,hp,sp,grid);stale=0
            else:stale+=1
            print(json.dumps({'epoch':epoch,'human_f1':selected['human']['macro_f1'],
                'human_ne_recall':selected['human']['per_class']['NON_EVENT']['recall'],
                'mvp_development_f1':selected['scope']['macro_f1'],
                'mvp_development_ne_recall':selected['scope']['per_class']['NON_EVENT']['recall'],
                'mvp_development_min_event_recall':min(selected['scope']['per_class'][c]['recall'] for c in LABELS[:-1]),
                'bias':selected['bias'],'joint_target_ratio':selected['joint_score']},ensure_ascii=False),flush=True)
            if stale>=config['patience'] or selected['joint_score']>=1.:break
        state.update(status='SUCCEEDED',epochs_completed=len(history),model_exported=True,finished_at=datetime.now(timezone.utc).isoformat())
        write(out/'run_state.json',state);return state
    except Exception as error:
        state.update(status='FAILED',error={'type':type(error).__name__,'message':str(error)})
        write(out/'run_state.json',state);(out/'error_trace.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','warm-start','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.root,a.warm_start,a.output),indent=2))
