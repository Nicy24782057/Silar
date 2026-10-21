"""Development correction from preserved v08 weights. No final acceptance data.

V07 synthetic50 now enters weak training and seen regression, explicitly.
Human130 remains outside gradients. Source730 labels stay immutable.
"""
import argparse,json,math,random,time,traceback,shutil
from collections import defaultdict
from pathlib import Path
from datetime import datetime,timezone
from train_sena_cpu import LABELS,write,sha
from train_scope_sena_v06 import score_probs,shifted,normal

def run(root,warm,out):
 out.mkdir(parents=True,exist_ok=False)
 state={'schema':'slr09-context-correction-0.8.1','status':'PREPARING','source':'PRESERVED_V08_WITH_INHERITED_BIAS2.5',
  'training_executed':False,'quality_acceptance_approved':False,'card_done':False,
  'human130_used_for_training':False,'v07_assistant50_used_for_weak_training':True,
  'pilot50_used_for_training':False,'pilot50_used_for_regression_selection':True,
  'new_acceptance_reference_read_or_inferred':False,'started_at':datetime.now(timezone.utc).isoformat()}
 write(out/'run_state.json',state)
 try:
  identity=json.loads((warm/'source_manifest.json').read_text())
  for n,h in identity['files'].items():assert sha(warm/n)==h,n
  assert identity['manual_non_event_bias_to_remove']==0 and identity['inherited_manual_non_event_bias']==2.5
  write(out/'warm_start_identity.json',identity)
  source={r['id']:r for part in ('train','validation') for line in (root/f'data/sena_{part}_reviewed.jsonl').read_text().splitlines() for r in [json.loads(line)]}
  split=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/development_split.json').read_text())
  human=[dict(source[i]) for i in split['validation_ids']]
  approved=json.loads((root/'data/development_review_v0.8.json').read_text());assert approved['approved_records']==39 and approved['deferred_records']==1
  review={r['id']:r for r in approved['records']}
  human_train=[dict(source[i],label_origin='HUMAN_SOURCE') for i in split['training_ids']]
  human_train += [dict(r,label_origin='OWNER_APPROVED') for r in review.values() if r['review']['status']=='APPROVED']
  development=[r for r in human if r['id'] not in review]
  adjudicated=[dict(r,final=review[r['id']]['final'] if r['id'] in review else r['final']) for r in human if r['id'] not in review or review[r['id']]['review']['status']!='DEFERRED']
  weak=json.loads((root/'evidence/quality_fix_v05/training_run_20261019_cpu/training_auxiliary.json').read_text())+json.loads((root/'data/matched_pairs_v07_training.json').read_text())['records']
  seen=[dict(r,final=r['gold_label'],label_origin='ASSISTANT_SEEN_V07',reference_human_reviewed=False) for r in json.loads((root/'data/frozen_new_diagnostic_v0.7.json').read_text())['records']]
  train=human_train+[dict(r,label_origin='ASSISTANT_OTHER') for r in weak]+seen
  scope=[r for r in json.loads((root/'data/mvp_seen_development_v07.json').read_text())['records'] if r['id'] not in review]
  pilot=json.loads((root/'evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json').read_text())['records']
  regression=[dict(r,final=r['gold_label']) for r in pilot]
  assert (len(train),len(human_train),len(development),len(scope),len(seen),len(human),len(adjudicated))==(1249,623,130,50,50,146,145)
  sets={'human130':development,'original146':human,'adjudicated145':adjudicated,'scope50':scope,'seen_v07_50':seen,'human_regression50':regression}
  texts={normal(r['text']) for r in train};assert len(texts)==len(train)
  for name in ('human130','scope50','human_regression50'):assert not texts&{normal(r['text']) for r in sets[name]},name
  overlaps={name:sum(normal(r['text']) in texts for r in rows) for name,rows in sets.items()}
  assert overlaps['original146']==15 and overlaps['adjudicated145']==15 and overlaps['seen_v07_50']==50
  write(out/'split_retirement.json',{'training_unique':1249,'human_training':623,'assistant_weak_training':626,'untouched_human_development':130,
   'training_overlap_by_scoring_set':overlaps,'original146_is_mixed_seen_regression':True,'original146_labels_unchanged':True,
   'v07_50_role':'ASSISTANT_WEAK_TRAINING_AND_SEEN_REGRESSION_NOT_BLIND_TEST','new_final_reference_read_or_inferred':False})
  cfg={'seed':113,'cpu_threads':2,'max_length':192,'batch_size_maximum':8,'max_epochs':3,'patience':2,
   'encoder_layers':'LAST_FOUR','encoder_lr':5e-6,'head_lr':2e-5,'non_event_class_multiplier':1.5,
   'human_weight':1.,'owner39_weight':1.5,'weak_v07_weight':.5,'other_weak_weight':.25,'hard_training_ne_weight_multiplier':2.,
   'owner_or_hard_training_human_repeats':3,'weak_seen_v07_repeats':6,'pair_margin':2.,'pair_loss_coefficient':.35,
   'inherited_manual_bias':2.5,'manual_bias_removed':0.,'additional_bias_grid':[i/10 for i in range(-10,31)],
   'selection_priority':['MAX_WORST_TARGET_RATIO_SIX_SETS_AND_CONTRASTS','MAX_MEAN_CAPPED_RATIO','MIN_ABS_ADDITIONAL_BIAS','MAX_HUMAN130_F1'],
   'targets_unchanged':{'macro_f1':.85,'non_event_recall':.9,'event_class_recall':.8,'regression_contrasts':1.},
   'confidence_cutoff_unchanged':.95,'probability_calibration_established':False,'exploratory_development_fitting':True,
   'training_source_sha256':sha(Path(__file__)),'approval_sha256':sha(root/'data/development_review_v0.8.json')}
  write(out/'training_config.json',cfg);write(out/'training_records_frozen.json',train);write(out/'review_decision_frozen.json',approved)
  shutil.copy2(Path(__file__),out/'executed_training_source.py')
  for name,rows in sets.items():write(out/f'frozen_{name}.json',rows)
  import torch
  from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
  set_seed(cfg['seed']);torch.set_num_threads(2)
  tokenizer=AutoTokenizer.from_pretrained(warm,local_files_only=True)
  model,info=AutoModelForSequenceClassification.from_pretrained(warm,local_files_only=True,use_safetensors=True,output_loading_info=True)
  assert not any(info.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs'))
  assert model.config.id2label==dict(enumerate(LABELS))
  for p in model.parameters():p.requires_grad=False
  for layer in model.bert.encoder.layer[-4:]:
   for p in layer.parameters():p.requires_grad=True
  for module in (model.bert.pooler,model.classifier):
   for p in module.parameters():p.requires_grad=True
  def encode(rows):return tokenizer([r['text'] for r in rows],padding=True,truncation=True,max_length=192,return_tensors='pt')
  def probabilities(rows):
   model.eval();result=[]
   with torch.inference_mode():
    for i in range(0,len(rows),16):result+=torch.softmax(model(**encode(rows[i:i+16])).logits,-1).tolist()
   return result
  hp=probabilities(human_train);ne=[(r,p) for r,p in zip(human_train,hp) if r['final']=='NON_EVENT']
  hard={r['id'] for r,p in sorted(ne,key=lambda x:(x[1][4],x[0]['id']))[:math.ceil(len(ne)*.25)]}
  write(out/'training_only_negative_mining.json',{'scope':'HUMAN_TRAIN623_ONLY','selected_ids':sorted(hard),'development_used':False})
  pairs=defaultdict(list);units=[]
  for r in train:
   if 'pair_id' in r:pairs[r['pair_id']].append(r)
   else:
    repeat=6 if r['label_origin']=='ASSISTANT_SEEN_V07' else 3 if r['label_origin']=='OWNER_APPROVED' or r['id'] in hard else 1
    units += [[r]]*repeat
  assert len(pairs)==256 and all({r['polarity'] for r in p}=={'P','N'} for p in pairs.values())
  units+=list(pairs.values());write(out/'sampling_plan.json',{'unique_training_records':len(train),'draws_per_epoch':sum(map(len,units)),'new_human_data_created_by_repetition':False})
  def batches(epoch):
   order=list(units);random.Random(cfg['seed']+epoch).shuffle(order);output=[];batch=[]
   for unit in order:
    if len(batch)+len(unit)>8:output.append(batch);batch=[]
    batch+=unit
   if batch:output.append(batch)
   return output
  head=list(model.classifier.parameters());headids={id(p) for p in head};other=[p for p in model.parameters() if p.requires_grad and id(p) not in headids]
  optimizer=torch.optim.AdamW([{'params':other,'lr':cfg['encoder_lr']},{'params':head,'lr':cfg['head_lr']}],weight_decay=.01)
  schedule=[batches(i) for i in range(1,4)];total=sum(map(len,schedule));warmup=max(1,int(.05*total))
  scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda s:(s+1)/warmup if s<warmup else max(0.,(total-s)/max(1,total-warmup)))
  unique={normal(r['text']):r for rows in sets.values() for r in rows};unique_rows=list(unique.values());contrast={r['id'] for r in regression if r.get('family') in {'simulation','exercise_only','real_during_exercise'}};assert len(contrast)>=4
  def evaluate():
   cache=dict(zip(unique,probabilities(unique_rows)));raw={name:[cache[normal(r['text'])] for r in rows] for name,rows in sets.items()};grid=[]
   for b in cfg['additional_bias_grid']:
    ps={name:shifted(p,b) for name,p in raw.items()};ms={name:score_probs(sets[name],p) for name,p in ps.items()}
    cp=[(r,p) for r,p in zip(regression,ps['human_regression50']) if r['id'] in contrast]
    ca=sum(LABELS[max(range(5),key=lambda i:p[i])]==r['final'] for r,p in cp)/len(cp)
    ratios=[ca]+[m['predeclared_selection_metric'] for m in ms.values()]
    grid.append({'bias':b,'joint_score':min(ratios),'mean_capped_ratio':sum(min(1.,x) for x in ratios)/len(ratios),'contrast_accuracy':ca,'metrics':ms})
   best=dict(max(grid,key=key));best['feasible_bias_values']=[g['bias'] for g in grid if g['joint_score']>=1.]
   return best,{name:shifted(p,best['bias']) for name,p in raw.items()},grid
  def key(x):return x['joint_score'],x['mean_capped_ratio'],-abs(x['bias']),x['metrics']['human130']['macro_f1']
  best_key=None;history=[];stale=0
  def save(epoch,s,ps,grid):
   nonlocal best_key
   best_key=key(s);params={k:v.detach().cpu() for k,v in model.state_dict().items()};params['classifier.bias']=params['classifier.bias'].clone();params['classifier.bias'][4]+=s['bias']
   model.save_pretrained(out/'best_model',state_dict=params,safe_serialization=True);tokenizer.save_pretrained(out/'best_model')
   write(out/'best_selection.json',{'epoch':epoch,'additional_bias':s['bias'],'inherited_bias':2.5,'joint_score':s['joint_score'],'contrast_accuracy':s['contrast_accuracy'],'feasible_bias_values':s['feasible_bias_values'],'all_development_targets_met':s['joint_score']>=1.,'quality_acceptance_approved':False})
   write(out/'metrics.json',s['metrics']);write(out/'selected_bias_grid.json',grid)
   for name,rows in sets.items():write(out/f'predictions_{name}.json',[{'id':r['id'],'text':r['text'],'gold':r['final'],'probabilities':dict(zip(LABELS,p))} for r,p in zip(rows,ps[name])])
   state.update(best_epoch=epoch,best_joint_score=s['joint_score'])
  s,ps,grid=evaluate();save(0,s,ps,grid);write(out/'baseline_evaluation.json',s)
  state.update(status='TRAINING',training_unique_records=len(train),human_training=623,weak_training=626,human_development=130,trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad));write(out/'run_state.json',state)
  class_weight=torch.tensor([1.,1.,1.,1.,1.5])
  for epoch,bs in enumerate(schedule,1):
   start=time.time();model.train();loss_sum=0.
   for step,batch in enumerate(bs,1):
    optimizer.zero_grad(set_to_none=True);logits=model(**encode(batch)).logits;gold=torch.tensor([LABELS.index(r['final']) for r in batch])
    weights=torch.tensor([({'OWNER_APPROVED':1.5,'HUMAN_SOURCE':1.,'ASSISTANT_SEEN_V07':.5,'ASSISTANT_OTHER':.25}[r['label_origin']])*(2. if r['id'] in hard else 1.) for r in batch])
    ce=(torch.nn.functional.cross_entropy(logits,gold,weight=class_weight,reduction='none')*weights).sum()/weights.sum()
    idx=defaultdict(dict)
    for i,r in enumerate(batch):
     if 'pair_id' in r:idx[r['pair_id']][r['polarity']]=i
    terms=[]
    for p in idx.values():
     assert set(p)=={'P','N'};c=LABELS.index(batch[p['P']]['pair_category']);delta=(logits[p['P'],c]-logits[p['P'],4])-(logits[p['N'],c]-logits[p['N'],4]);terms.append(torch.relu(2.-delta))
    pair=torch.stack(terms).mean() if terms else logits.sum()*0.;loss=ce+.35*pair;assert torch.isfinite(loss)
    loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step();scheduler.step();state['training_executed']=True;loss_sum+=float(loss.detach())
    if step==1 or step%10==0:state.update(epoch=epoch,step=step,steps_in_epoch=len(bs),loss=float(loss.detach()));write(out/'run_state.json',state);print(f'epoch {epoch} step {step}/{len(bs)} loss {float(loss.detach()):.4f}',flush=True)
   s,ps,grid=evaluate();history.append({'epoch':epoch,'seconds':time.time()-start,'training_loss':loss_sum/step,**s});write(out/'training_history.json',history)
   if key(s)>best_key:save(epoch,s,ps,grid);stale=0
   else:stale+=1
   print(json.dumps({'epoch':epoch,'joint_target_ratio':s['joint_score'],'additional_bias':s['bias'],'human130_ne':s['metrics']['human130']['per_class']['NON_EVENT']['recall'],'v07_seen_flood':s['metrics']['seen_v07_50']['per_class']['FLOOD']['recall'],'regression_ne':s['metrics']['human_regression50']['per_class']['NON_EVENT']['recall']}),flush=True)
   if stale>=2 or s['joint_score']>=1.:break
  state.update(status='SUCCEEDED',epochs_completed=len(history),finished_at=datetime.now(timezone.utc).isoformat());write(out/'run_state.json',state);return state
 except Exception as e:
  state.update(status='FAILED',error=str(e));write(out/'run_state.json',state);(out/'error_trace.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for a in ('root','warm-start','output'):p.add_argument('--'+a,type=Path,required=True)
 a=p.parse_args();print(json.dumps(run(a.root,a.warm_start,a.output),indent=2))
