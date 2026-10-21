"""Last-block SENA replay. All inputs are explicitly retired development data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import time
import traceback
from train_sena_cpu import LABELS, metrics, sha, write


def load(path):
    return json.loads(path.read_text())


def norm(text):
    return ' '.join(text.casefold().split())


def run(root, prepared, cache, warm, output):
    import torch
    from safetensors import safe_open
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed
    output.mkdir(parents=True, exist_ok=False)
    state=dict(schema='slr09-development-replay-0.8.4',status='PREPARING',
               started_at=datetime.now(timezone.utc).isoformat(),training_executed=False,
               quality_acceptance_approved=False,card_done=False,new_acceptance_inference_executed=False)
    write(output/'run_state.json',state)
    try:
        retirement=load(prepared/'reference_retirement.json')
        assert retirement['new_status']=='DEVELOPMENT_AND_REGRESSION_NOT_FRESH_ACCEPTANCE'
        manifest=load(cache/'manifest.json')
        assert manifest['status']=='SUCCEEDED' and sha(warm/'model.safetensors')==manifest['warm_start_weight_sha256']
        assert sha(cache/'features.safetensors')==manifest['features_sha256']
        assert sha(cache/'index.json')==manifest['index_sha256']
        for name,key in [('training_records_frozen.json','training_records_sha256'),('scoring_sets_frozen.json','scoring_sets_sha256')]:
            assert sha(prepared/name)==manifest[key]
            shutil.copy2(prepared/name,output/name)
        train=load(output/'training_records_frozen.json');sets=load(output/'scoring_sets_frozen.json')
        assert len(train)==1733 and len({norm(x['text']) for x in train})==1733
        assert len(sets['FINAL083_seen_development'])==50
        set_seed(384);torch.set_num_threads(2)
        model=AutoModelForSequenceClassification.from_pretrained(warm,local_files_only=True)
        tokenizer=AutoTokenizer.from_pretrained(warm,local_files_only=True)
        assert len(model.bert.encoder.layer)==12
        for p in model.parameters():p.requires_grad=False
        for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier]:
            for p in module.parameters():p.requires_grad=True
        index=load(cache/'index.json');features_file=safe_open(cache/'features.safetensors',framework='pt',device='cpu')
        def logits(rows,cap):
            values=[features_file.get_tensor(index[hashlib.sha256(x['text'].encode()).hexdigest()][str(cap)]) for x in rows]
            length=max(v.shape[0] for v in values);hidden=torch.zeros(len(rows),length,values[0].shape[1]);mask=torch.zeros(len(rows),length,dtype=torch.long)
            for i,value in enumerate(values):hidden[i,:value.shape[0]]=value;mask[i,:value.shape[0]]=1
            extended=model.bert.get_extended_attention_mask(mask,mask.shape)
            final=model.bert.encoder.layer[-1](hidden,attention_mask=extended)[0]
            return model.classifier(model.dropout(model.bert.pooler(final)))
        def probs(rows):
            model.eval();result=[]
            with torch.inference_mode():
                for offset in range(0,len(rows),16):result.extend(torch.softmax(logits(rows[offset:offset+16],512),-1).tolist())
            return result
        model.eval();sample=train[:8]
        with torch.inference_mode():
            batch=tokenizer([r['text'] for r in sample],padding=True,truncation=True,max_length=512,return_tensors='pt')
            delta=float((torch.softmax(model(**batch).logits,-1)-torch.softmax(logits(sample,512),-1)).abs().max())
        assert delta<=1e-5,delta
        write(output/'cached_forward_verification.json',dict(records=8,max_probability_delta=delta))
        teacher=dict(zip((norm(x['text']) for x in train),probs(train)))
        missing={norm(x['text']):x for rows in sets.values() for x in rows if norm(x['text']) not in teacher}
        teacher.update(zip(missing,probs(list(missing.values()))))
        write(output/'baseline_training_probabilities.json',[teacher[norm(x['text'])] for x in train])
        prior_hard={norm(x['text']) for x in load(prepared/'previous_hard_replay_records.json')}
        hard=[x for x in train if norm(x['text']) in prior_hard or x['label_origin']=='REVIEWED_FINAL083_RETIRED_TO_DEVELOPMENT']
        curriculum=train+hard*6
        cfg=dict(seed=384,cpu_threads=2,max_epochs=6,batch_size=8,encoder_lr=1e-5,head_lr=5e-5,teacher_kl=.5,
                 trainable='LAST_ENCODER_BLOCK_POOLER_CLASSIFIER',gradient_method='DETERMINISTIC_FROZEN_PREFIX_CACHE_LAST_BLOCK_BACKPROP',
                 hard_replay_unique=len(hard),additional_draws_per_hard_example=6,draws_per_epoch=len(curriculum),
                 confidence_cutoff_unchanged=.95,independent_validation_or_acceptance_claimed=False,
                 selection='ALL_PRIOR_CLASS_GATES_ALL_PRIOR_CONTRASTS_CONTEXT40_AND_FINAL083_ACCURACY_1',
                 parent_weight_sha256=sha(warm/'model.safetensors'),training_source_sha256=sha(Path(__file__)))
        write(output/'training_config.json',cfg);write(output/'reference_retirement.json',retirement)
        write(output/'frozen_prefix_manifest.json',manifest);write(output/'hard_replay_records.json',hard)
        shutil.copy2(Path(__file__),output/'executed_training_source.py')
        def evaluate():
            unique={norm(x['text']):x for rows in sets.values() for x in rows}
            observed=dict(zip(unique,probs(list(unique.values()))));scores={};contrasts={};predictions={};regressions=0
            for name,rows in sets.items():
                pp=[observed[norm(x['text'])] for x in rows];guesses=[LABELS[max(range(5),key=lambda i:p[i])] for p in pp]
                scores[name]=metrics([x['final'] for x in rows],guesses)
                contrasts[name]=[x['id'] for x,g in zip(rows,guesses) if x.get('family') in {'simulation','exercise_only','real_during_exercise','exercise_contrast'} and g!=x['final']]
                regressions+=sum(LABELS[max(range(5),key=lambda i:teacher[norm(x['text'])][i])]==x['final'] and g!=x['final'] for x,g in zip(rows,guesses))
                predictions[name]=[dict(id=x['id'],text=x['text'],gold=x['final'],probabilities=dict(zip(LABELS,p))) for x,p in zip(rows,pp)]
            strict={'context40_now_training','FINAL083_seen_development'}
            feasible=all(m['targets_met'] for n,m in scores.items() if n not in strict) and all(not e for e in contrasts.values()) and all(scores[n]['accuracy']==1. for n in strict)
            return dict(metrics=scores,contrast_errors=contrasts,feasible=feasible,regressions_with_overlapping_sets=regressions),predictions
        baseline,_=evaluate();write(output/'baseline_evaluation.json',baseline)
        head=list(model.classifier.parameters());head_ids={id(p) for p in head};other=[p for p in model.parameters() if p.requires_grad and id(p) not in head_ids]
        optimizer=torch.optim.AdamW([dict(params=other,lr=cfg['encoder_lr']),dict(params=head,lr=cfg['head_lr'])],weight_decay=.01)
        best=None;history=[]
        for epoch in range(1,cfg['max_epochs']+1):
            order=list(curriculum);random.Random(cfg['seed']+epoch).shuffle(order);model.eval()
            for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier,model.dropout]:module.train()
            losses=0.;started=time.monotonic();completed=0
            for offset in range(0,len(order),8):
                rows=order[offset:offset+8];optimizer.zero_grad(set_to_none=True);observed=logits(rows,192)
                gold=torch.tensor([LABELS.index(x['final']) for x in rows])
                weights=torch.tensor([4. if x['label_origin'] in {'NEW_ASSISTANT_WEAK_TRAINING','ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING'} else 2. if x['label_origin'] in {'REVIEWED_FINAL_NOW_TRAINING','REVIEWED_FINAL083_RETIRED_TO_DEVELOPMENT'} else .25 if 'ASSISTANT' in x['label_origin'] else 1. for x in rows])
                target=torch.tensor([teacher[norm(x['text'])] for x in rows]);keep=(target.argmax(-1)==gold).float()
                ce=(torch.nn.functional.cross_entropy(observed,gold,reduction='none')*weights).sum()/weights.sum()
                kl=torch.nn.functional.kl_div(torch.log_softmax(observed,-1),target,reduction='none').sum(-1)
                loss=ce+cfg['teacher_kl']*(kl*keep).sum()/keep.sum().clamp_min(1.)
                assert torch.isfinite(loss)
                loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step();losses+=float(loss.detach());completed+=1
                if completed==1 or completed%50==0:
                    state.update(status='TRAINING',training_executed=True,gradient_updates_executed=True,epoch=epoch,steps_completed=completed,steps_per_epoch=(len(order)+7)//8)
                    write(output/'run_state.json',state);print('Replay training',epoch,completed,'/',state['steps_per_epoch'],'loss',round(float(loss.detach()),4),flush=True)
            result,predictions=evaluate();result.update(epoch=epoch,steps_completed=completed,seconds=time.monotonic()-started,training_loss_mean=losses/completed)
            history.append(result);write(output/'training_history.json',history)
            print(json.dumps(dict(epoch=epoch,feasible=result['feasible'],FINAL083_seen=result['metrics']['FINAL083_seen_development']['accuracy'],contrast_errors={n:e for n,e in result['contrast_errors'].items() if e},failed_class_sets=[n for n,m in result['metrics'].items() if not m['targets_met']])),flush=True)
            key=(result['feasible'],-result['regressions_with_overlapping_sets'],result['metrics']['FINAL083_seen_development']['accuracy'],sum(m['macro_f1'] for m in result['metrics'].values()))
            if best is None or key>best:
                best=key;model.save_pretrained(output/'best_model',safe_serialization=True);tokenizer.save_pretrained(output/'best_model')
                write(output/'best_selection.json',result)
                for name,pred in predictions.items():write(output/f'predictions_{name}.json',pred)
            if result['feasible']:break
        selected=load(output/'best_selection.json')
        state.update(status='SUCCEEDED' if selected['feasible'] else 'NO_FEASIBLE_CANDIDATE',training_unique=len(train),selected_epoch=selected['epoch'],steps_completed=selected['steps_completed'],finished_at=datetime.now(timezone.utc).isoformat())
        write(output/'run_state.json',state)
        if not selected['feasible']:raise RuntimeError('Development replay did not meet the unchanged constraints')
        print(json.dumps(state,indent=2),flush=True)
    except Exception as error:
        state.update(status='FAILED',error=str(error),finished_at=datetime.now(timezone.utc).isoformat());write(output/'run_state.json',state)
        (output/'error_trace.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','prepared','cache','warm','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.root.resolve(),a.prepared.resolve(),a.cache.resolve(),a.warm.resolve(),a.output.resolve())
