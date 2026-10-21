"""Continue last-block training with verified frozen features and seen replay."""
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


def normal(text):
    return ' '.join(text.casefold().split())


def load(path):
    return json.loads(path.read_text())


def run(root, previous, cache, original_warm, output):
    import torch
    from safetensors import safe_open
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed
    output.mkdir(parents=True, exist_ok=False)
    state = dict(schema='slr09-cached-last-block-context-0.8.3', status='PREPARING',
        started_at=datetime.now(timezone.utc).isoformat(), training_executed=False,
        quality_acceptance_approved=False, card_done=False, new_acceptance_inference_executed=False)
    write(output/'run_state.json', state)
    try:
        parent = load(previous/'run_state.json')
        assert parent['status'] in {'FAILED', 'NO_FEASIBLE_CANDIDATE'}
        manifest = load(cache/'manifest.json')
        assert manifest['status']=='SUCCEEDED'
        assert sha(cache/'features.safetensors') == manifest['features_sha256']
        assert sha(cache/'index.json') == manifest['index_sha256']
        for name in ('training_records_frozen.json','scoring_sets_frozen.json'):
            key = 'training_records_sha256' if name.startswith('training') else 'scoring_sets_sha256'
            assert sha(previous/name) == manifest[key]
            shutil.copy2(previous/name, output/name)
        assert sha(original_warm/'model.safetensors') == manifest['warm_start_weight_sha256']
        # The reusable prefix must still be bit-identical in the parent weights.
        with safe_open(original_warm/'model.safetensors',framework='pt',device='cpu') as original, \
                safe_open(previous/'best_model/model.safetensors',framework='pt',device='cpu') as student:
            for key in original.keys():
                if key.startswith(('bert.encoder.layer.11.','bert.pooler.','classifier.')):
                    continue
                assert torch.equal(original.get_tensor(key),student.get_tensor(key)), key
        set_seed(284)
        torch.set_num_threads(2)
        model = AutoModelForSequenceClassification.from_pretrained(previous/'best_model',local_files_only=True)
        tokenizer = AutoTokenizer.from_pretrained(previous/'best_model',local_files_only=True)
        for p in model.parameters(): p.requires_grad=False
        for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier]:
            for p in module.parameters(): p.requires_grad=True
        cache_index = load(cache/'index.json')
        cached = safe_open(cache/'features.safetensors',framework='pt',device='cpu')
        train = load(output/'training_records_frozen.json')
        sets = load(output/'scoring_sets_frozen.json')
        teacher_raw = load(previous/'baseline_training_probabilities.json')
        assert len(train)==len(teacher_raw)
        teacher = {normal(r['text']):p for r,p in zip(train,teacher_raw)}
        def features(rows,cap):
            values = [cached.get_tensor(cache_index[hashlib.sha256(r['text'].encode()).hexdigest()][str(cap)]) for r in rows]
            length=max(v.shape[0] for v in values)
            hidden=torch.zeros(len(rows),length,values[0].shape[1]);mask=torch.zeros(len(rows),length,dtype=torch.long)
            for i,value in enumerate(values):hidden[i,:value.shape[0]]=value;mask[i,:value.shape[0]]=1
            return hidden,model.bert.get_extended_attention_mask(mask,mask.shape)
        def logits(rows,cap):
            hidden,mask=features(rows,cap)
            final=model.bert.encoder.layer[-1](hidden,attention_mask=mask)[0]
            return model.classifier(model.dropout(model.bert.pooler(final)))
        def probs(rows):
            model.eval();result=[]
            with torch.inference_mode():
                for offset in range(0,len(rows),16):result.extend(torch.softmax(logits(rows[offset:offset+16],512),-1).tolist())
            return result
        missing={normal(r['text']):r for rows in sets.values() for r in rows if normal(r['text']) not in teacher}
        teacher.update(zip(missing,probs(list(missing.values()))))
        cfg=dict(seed=284,cpu_threads=2,max_epochs=8,batch_size=8,
            trainable='LAST_ENCODER_BLOCK_POOLER_CLASSIFIER',encoder_lr=1e-5,head_lr=5e-5,
            gradient_method='DETERMINISTIC_FROZEN_PREFIX_CACHE_LAST_BLOCK_BACKPROP',
            teacher_kl=.5,known_context_additional_draws=5,new_weak_pairs_additional_draws=2,
            new_context_loss_weight=4.,confidence_cutoff_unchanged=.95,
            all_existing_references_used_for_training_or_selection=True,
            independent_validation_or_acceptance_claimed=False,
            selection='ALL_ORIGINAL_EIGHT_CLASS_GATES_ALL_CONTRASTS_AND_CONTEXT40_ACCURACY_1',
            parent_run_status=parent['status'],parent_selected_epoch=load(previous/'best_selection.json')['epoch'],
            parent_weight_sha256=sha(previous/'best_model/model.safetensors'),
            training_source_sha256=sha(Path(__file__)))
        write(output/'training_config.json',cfg)
        write(output/'frozen_prefix_manifest.json',manifest)
        write(output/'parent_run_state.json',parent)
        shutil.copy2(Path(__file__),output/'executed_training_source.py')
        for name in ('reference_retirement.json','baseline_evaluation.json','baseline_training_probabilities.json'):
            shutil.copy2(previous/name,output/name)
        state.update(training_unique=len(train),training_origins=dict(Counter(r['label_origin'] for r in train)),
            parent_run_directory=previous.relative_to(root).as_posix(),cached_prefix_verified=True)
        write(output/'run_state.json',state)
        # Confirm the cached path against the complete current model before gradients.
        sample=train[:8];model.eval()
        with torch.inference_mode():
            x=tokenizer([r['text'] for r in sample],padding=True,truncation=True,max_length=512,return_tensors='pt')
            delta=float((torch.softmax(model(**x).logits,-1)-torch.softmax(logits(sample,512),-1)).abs().max())
        assert delta<=1e-5,delta
        write(output/'cached_forward_verification.json',dict(max_probability_delta=delta,records=len(sample)))
        def evaluate():
            unique={normal(r['text']):r for rows in sets.values() for r in rows}
            prediction_cache=dict(zip(unique,probs(list(unique.values()))))
            scores={};contrasts={};predictions={};regressions=0
            for name,rows in sets.items():
                ps=[prediction_cache[normal(r['text'])] for r in rows]
                guesses=[LABELS[max(range(5),key=lambda i:p[i])] for p in ps]
                scores[name]=metrics([r['final'] for r in rows],guesses)
                contrasts[name]=[r['id'] for r,p in zip(rows,guesses)
                    if r.get('family') in {'simulation','exercise_only','real_during_exercise','exercise_contrast'} and p!=r['final']]
                for row,guess in zip(rows,guesses):
                    old=teacher[normal(row['text'])]
                    before=LABELS[max(range(5),key=lambda i:old[i])]
                    regressions+=int(before==row['final'] and guess!=row['final'])
                predictions[name]=[dict(id=r['id'],text=r['text'],gold=r['final'],probabilities=dict(zip(LABELS,p))) for r,p in zip(rows,ps)]
            feasible=all(m['targets_met'] for name,m in scores.items() if name!='context40_now_training') and all(not e for e in contrasts.values()) and scores['context40_now_training']['accuracy']==1.
            return dict(metrics=scores,contrast_errors=contrasts,feasible=feasible,
                regressions_with_overlapping_sets=regressions),predictions
        initial,_=evaluate();write(output/'continuation_initial_evaluation.json',initial)
        head=list(model.classifier.parameters());head_ids={id(p) for p in head}
        other=[p for p in model.parameters() if p.requires_grad and id(p) not in head_ids]
        optimizer=torch.optim.AdamW([dict(params=other,lr=cfg['encoder_lr']),dict(params=head,lr=cfg['head_lr'])],weight_decay=.01)
        hard=[r for r in train if r['label_origin']=='ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING']
        new_pairs=[r for r in train if r['label_origin']=='NEW_ASSISTANT_WEAK_TRAINING']
        curriculum=train+hard*cfg['known_context_additional_draws']+new_pairs*cfg['new_weak_pairs_additional_draws']
        cfg['draws_per_epoch']=len(curriculum);write(output/'training_config.json',cfg)
        best=None;history=[]
        for epoch in range(1,cfg['max_epochs']+1):
            order=list(curriculum);random.Random(cfg['seed']+epoch).shuffle(order)
            model.eval()
            for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier,model.dropout]:module.train()
            loss_sum=0.;started=time.monotonic()
            for offset in range(0,len(order),8):
                batch=order[offset:offset+8];optimizer.zero_grad(set_to_none=True)
                observed=logits(batch,192);gold=torch.tensor([LABELS.index(r['final']) for r in batch])
                weights=torch.tensor([4. if r['label_origin'] in {'NEW_ASSISTANT_WEAK_TRAINING','ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING'} else 2. if r['label_origin']=='REVIEWED_FINAL_NOW_TRAINING' else .25 if 'ASSISTANT' in r['label_origin'] else 1. for r in batch])
                target=torch.tensor([teacher[normal(r['text'])] for r in batch]);keep=(target.argmax(-1)==gold).float()
                ce=(torch.nn.functional.cross_entropy(observed,gold,reduction='none')*weights).sum()/weights.sum()
                kl=torch.nn.functional.kl_div(torch.log_softmax(observed,-1),target,reduction='none').sum(-1)
                loss=ce+cfg['teacher_kl']*(kl*keep).sum()/keep.sum().clamp_min(1.)
                assert torch.isfinite(loss)
                loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step()
                loss_sum+=float(loss.detach())
                if offset==0 or offset%400==0:
                    state.update(status='TRAINING',training_executed=True,gradient_updates_executed=True,
                        epoch=epoch,step=offset//8+1,steps_per_epoch=(len(order)+7)//8)
                    write(output/'run_state.json',state)
                    print('Cached training',epoch,state['step'],'/',state['steps_per_epoch'],'loss',round(float(loss.detach()),4),flush=True)
            result,predictions=evaluate()
            result.update(epoch=epoch,seconds=time.monotonic()-started,training_loss_mean=loss_sum/((len(order)+7)//8))
            history.append(result);write(output/'training_history.json',history)
            print(json.dumps(dict(epoch=epoch,feasible=result['feasible'],context40=result['metrics']['context40_now_training']['accuracy'],contrast_errors={n:e for n,e in result['contrast_errors'].items() if e},failed_class_sets=[n for n,m in result['metrics'].items() if n!='context40_now_training' and not m['targets_met']])),flush=True)
            key=(result['feasible'],-result['regressions_with_overlapping_sets'],sum(m['macro_f1'] for m in result['metrics'].values()))
            if best is None or key>best:
                best=key;model.save_pretrained(output/'best_model',safe_serialization=True);tokenizer.save_pretrained(output/'best_model')
                write(output/'best_selection.json',result)
                for name,pred in predictions.items():write(output/f'predictions_{name}.json',pred)
            if result['feasible']:break
        selected=load(output/'best_selection.json')
        state.update(status='SUCCEEDED' if selected['feasible'] else 'NO_FEASIBLE_CANDIDATE',
            selected_epoch=selected['epoch'],all_known_constraints_met=selected['feasible'],
            finished_at=datetime.now(timezone.utc).isoformat())
        write(output/'run_state.json',state)
        if not selected['feasible']:raise RuntimeError('Cached continuation did not meet the unchanged known constraints')
        print(json.dumps(state,indent=2),flush=True)
    except Exception as error:
        state.update(status='FAILED',error=str(error),finished_at=datetime.now(timezone.utc).isoformat())
        write(output/'run_state.json',state)
        (output/'error_trace.txt').write_text(traceback.format_exc())
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','previous','cache','original-warm','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    run(a.root.resolve(),a.previous.resolve(),a.cache.resolve(),a.original_warm.resolve(),a.output.resolve())
