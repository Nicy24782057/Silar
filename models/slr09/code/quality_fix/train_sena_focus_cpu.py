"""Eksperimen baru SENA CPU dari baseline; pilot 50 tidak dipakai untuk fit/seleksi.

Validation lama 620 kini menjadi sumber development, dinyatakan eksplisit.
Model baru tidak diklaim sama dengan kandidat lama yang bobotnya belum tersedia.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import random
import time
import zipfile

LABELS=('FLOOD','EARTHQUAKE','FIRE','ACCIDENT','NON_EVENT')

def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def metrics(gold,pred):
    per={}
    for c in LABELS:
        tp=sum(a==c and b==c for a,b in zip(gold,pred))
        support=sum(a==c for a in gold); pp=sum(b==c for b in pred)
        precision=tp/pp if pp else 0;recall=tp/support if support else 0
        per[c]={'support':support,'precision':precision,'recall':recall,'f1':2*tp/(support+pp) if support+pp else 0}
    macro=sum(x['f1'] for x in per.values())/5
    minimum=min(macro/.85,per['NON_EVENT']['recall']/.90,min(per[x]['recall'] for x in LABELS[:-1])/.80)
    return {'accuracy':sum(a==b for a,b in zip(gold,pred))/len(gold),'macro_f1':macro,'per_class':per,
            'predeclared_selection_metric':minimum,'targets_met':minimum>=1}

def auxiliary():
    # Bantuan pelatihan berlabel asisten, bukan gold manusia atau data uji.
    rows=[]
    for label,event in zip(LABELS[:-1],['banjir','gempa','kebakaran','kecelakaan']):
        pairs=[
            (f'Peserta mengikuti simulasi {event} di kompleks pelatihan. Tidak ada kejadian nyata.',f'Saat simulasi di kompleks pelatihan, {event} sungguhan terjadi dan menimbulkan kerusakan.'),
            (f'Materi kelas membahas cara menghadapi {event}, tanpa melaporkan peristiwa tertentu.',f'Kelas diliburkan karena {event} terjadi pagi tadi dan bangunan harus diperiksa.'),
            (f'Tidak terjadi {event} di wilayah itu, menurut laporan pemeriksaan petugas.',f'Petugas menyatakan {event} terjadi di wilayah itu dan sedang ditangani.'),
            (f'Warga berlatih mencegah {event}. Kegiatan ini hanya persiapan, bukan laporan peristiwa.',f'Warga sedang bersiap saat {event} benar-benar terjadi di sekitar permukiman.'),
            (f'Bagaimana jika terjadi {event}? Pertanyaan ini hanya contoh dalam diskusi.',f'Diskusi dihentikan setelah warga melaporkan {event} yang baru terjadi di sekitar lokasi.'),
            (f'Sebuah cerita rekaan menampilkan {event} di negeri khayalan. Semua adegan bersifat fiksi.',f'Di dekat lokasi syuting film, {event} nyata terjadi dan petugas melakukan penanganan.'),
            (f'Kemungkinan {event} masih berupa peringatan untuk pekan berikutnya. Belum ada peristiwa yang dilaporkan.',f'Setelah peringatan pekan lalu, {event} terjadi kemarin dan merusak fasilitas warga.'),
            (f'Jumlah {event} tahunan dibahas sebagai statistik umum, bukan laporan peristiwa tertentu.',f'Data petugas mencatat {event} baru di Desa Puspasari tadi malam dengan korban terluka.'),
        ]
        for i,(negative,positive) in enumerate(pairs):
            rows += [{'id':f'AUX-{label}-{i}-N','text':negative,'final':'NON_EVENT','source':'ASSISTANT_AUTHORED_TRAINING_AUXILIARY_NOT_HUMAN_GOLD'},
                     {'id':f'AUX-{label}-{i}-P','text':positive,'final':label,'source':'ASSISTANT_AUTHORED_TRAINING_AUXILIARY_NOT_HUMAN_GOLD'}]
    return rows

def run(root,archive,out,warm_start):
    out.mkdir(parents=True,exist_ok=False)
    status={'status':'PREPARING','training_executed':False,'independent_acceptance_test_executed':False,
            'pilot50_used_for_training_or_checkpoint_selection':False,'source':'WARM_START_FROM_NEW_CPU_EXPERIMENT_ROUND1_NOT_MISSING_PREVIOUS_CANDIDATE',
            'started_at':datetime.now(timezone.utc).isoformat()}
    write(out/'run_state.json',status)
    spec=json.loads((root/'code/active_nara_adapter/asset_lock.json').read_text())['models']['sena']
    assert sha(archive)==spec['archive_sha256']
    source=out/'baseline';source.mkdir()
    with zipfile.ZipFile(archive) as z:
        for name,h in spec['files'].items():
            b=z.read(name);assert hashlib.sha256(b).hexdigest()==h
            (source/name).write_bytes(b)
    warm_files = {name:sha(warm_start/name) for name in ['config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt']}
    write(out/'warm_start_identity.json',{'files_sha256':warm_files,'source_run':'training_run_20261019_cpu','selection_scope':'DEVELOPMENT_NOT_ACCEPTANCE'})
    source=warm_start
    # Split development terlebih dahulu. Exact duplicates menjadi satu unit.
    indexed={}
    for part in ['train','validation']:
        for line in (root/f'data/sena_{part}_reviewed.jsonl').read_text().splitlines():
            r=json.loads(line);key=' '.join(r['text'].casefold().split())
            if key in indexed:assert indexed[key]['final']==r['final']
            indexed[key]=r
    by_class=defaultdict(list)
    for r in indexed.values():by_class[r['final']].append(r)
    train,val=[],[]
    for label in LABELS:
        group=sorted(by_class[label],key=lambda r:hashlib.sha256(('42:'+r['text']).encode()).hexdigest())
        count=max(1,round(.20*len(group)));val+=group[:count];train+=group[count:]
    aux=auxiliary()
    aux_keys={' '.join(x['text'].casefold().split()) for x in aux}
    assert not aux_keys&set(indexed)
    train+=aux
    write(out/'development_split.json',{'training_ids':[r['id'] for r in train],'validation_ids':[r['id'] for r in val],
        'training_records':len(train),'validation_records':len(val),'auxiliary_assistant_labeled_records':len(aux),
        'old_validation620_retired_as_untouched_validation':True,'validation_is_development_not_blind_test':True,
        'historical_baseline_training_membership_verified':False,'pilot50_used':False})
    write(out/'training_auxiliary.json',aux)
    config={'seed':42,'max_length':192,'batch_size':8,'max_epochs':6,'patience':2,
            'trainable_encoder_layers':'LAST_FOUR_ONLY','encoder_learning_rate':2e-5,'head_learning_rate':5e-5,
            'non_event_loss_weight_multiplier':2.5,'weight_decay':.01,'selection':'max min(macroF1/.85, NON_EVENT recall/.90, min event recall/.80)',
            'selection_data':'DEVELOPMENT_VALIDATION_ONLY'}
    write(out/'training_config.json',config)
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
    set_seed(42);torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(source,local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(source,local_files_only=True,use_safetensors=True)
    for p in model.parameters():p.requires_grad=False
    for layer in model.bert.encoder.layer[-4:]:
        for p in layer.parameters():p.requires_grad=True
    for module in [model.bert.pooler,model.classifier]:
        for p in module.parameters():p.requires_grad=True
    def encoded(records):
        x=tokenizer([r['text'] for r in records],padding=True,truncation=True,max_length=config['max_length'],return_tensors='pt')
        return x,torch.tensor([LABELS.index(r['final']) for r in records])
    xtrain,ytrain=encoded(train);xval,yval=encoded(val)
    counts=Counter(r['final'] for r in train)
    weights=torch.tensor([len(train)/(5*counts[c])*(2.5 if c=='NON_EVENT' else 1) for c in LABELS],dtype=torch.float32)
    criterion=torch.nn.CrossEntropyLoss(weight=weights)
    head=list(model.classifier.parameters());head_ids={id(p) for p in head}
    others=[p for p in model.parameters() if p.requires_grad and id(p) not in head_ids]
    optimizer=torch.optim.AdamW([{'params':others,'lr':2e-5},{'params':head,'lr':5e-5}],weight_decay=.01)
    status.update(status='TRAINING',trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),training_records=len(train),validation_records=len(val))
    write(out/'run_state.json',status)
    def evaluate():
        model.eval();pred=[];probs=[]
        with torch.inference_mode():
            for start in range(0,len(val),16):
                logit=model(**{k:v[start:start+16] for k,v in xval.items()}).logits
                prob=torch.softmax(logit,-1);pred+=prob.argmax(-1).tolist();probs+=prob.tolist()
        return metrics([LABELS[i] for i in yval.tolist()],[LABELS[i] for i in pred]),probs
    history=[];best=-1;stale=0
    initial,initial_probs=evaluate();write(out/'baseline_development_metrics.json',initial)
    best=initial['predeclared_selection_metric'];status['best_epoch']=0
    model.save_pretrained(out/'best_model',safe_serialization=True);tokenizer.save_pretrained(out/'best_model')
    write(out/'best_development_metrics.json',initial)
    write(out/'best_development_predictions.json',[{'id':r['id'],'text':r['text'],'gold':r['final'],'probabilities':dict(zip(LABELS,p))} for r,p in zip(val,initial_probs)])
    for epoch in range(1,7):
        model.train();order=torch.randperm(len(train));loss_total=0;started=time.time()
        for step,start in enumerate(range(0,len(train),8),1):
            ids=order[start:start+8];optimizer.zero_grad(set_to_none=True)
            logits=model(**{k:v[ids] for k,v in xtrain.items()}).logits
            loss=criterion(logits,ytrain[ids]);loss.backward();torch.nn.utils.clip_grad_norm_(others+head,1.)
            optimizer.step();status['training_executed']=True
            loss_total+=float(loss.detach())
            if step==1 or step%10==0:
                status.update(epoch=epoch,step=step,steps_in_epoch=(len(train)+7)//8,loss=float(loss.detach()))
                write(out/'run_state.json',status)
                print(f'epoch {epoch} step {step}/{status["steps_in_epoch"]} loss {float(loss.detach()):.4f}',flush=True)
        result,probs=evaluate();history.append({'epoch':epoch,'mean_training_loss':loss_total/step,'seconds':time.time()-started,**result})
        write(out/'training_history.json',history)
        print('development',epoch,json.dumps(result),flush=True)
        if result['predeclared_selection_metric']>best:
            best=result['predeclared_selection_metric'];stale=0
            model.save_pretrained(out/'best_model',safe_serialization=True);tokenizer.save_pretrained(out/'best_model')
            write(out/'best_development_metrics.json',result)
            write(out/'best_development_predictions.json',[{'id':r['id'],'text':r['text'],'gold':r['final'],'probabilities':dict(zip(LABELS,p))} for r,p in zip(val,probs)])
            status['best_epoch']=epoch
        else:stale+=1
        if stale>=2 or result['targets_met']:break
    status.update(status='SUCCEEDED',finished_at=datetime.now(timezone.utc).isoformat(),epochs_completed=len(history),best_development_selection=best,
        model_exported=True,quality_acceptance_approved=False)
    write(out/'run_state.json',status)
    print(json.dumps(status,indent=2))
    return status

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--warm-start',type=Path,required=True)
    args=p.parse_args();run(args.root,args.archive,args.output,args.warm_start)
