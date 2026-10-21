"""Actual CPU correction of one SENA encoder block, pooler and classifier.

All known references used here are development/training, including human130.
No claim of a held-out score is made. Original gold/source files stay intact.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import shutil
import time
import traceback
from train_sena_cpu import LABELS, metrics, sha, write


def normal(text): return ' '.join(text.casefold().split())


def contexts():
    pairs = [
        ('{e} dalam peragaan hanya memakai properti; tidak ada peristiwa nyata di lapangan.', 'Saat peragaan berlangsung, {e} sungguhan terjadi di lapangan; petugas menghentikan latihan.'),
        ('Petugas mempraktikkan penanganan {e}; kerusakan hanya tiruan dan tidak terjadi kejadian sungguhan.', 'Petugas sedang berlatih ketika {e} nyata merusak bangunan, meskipun tidak ada korban.'),
        ('Laporan {e} itu merupakan skenario latihan, bukan kejadian yang benar-benar terjadi.', 'Laporan {e} itu benar terjadi setelah latihan usai; kerusakan diperiksa petugas.'),
        ('Video latihan menampilkan {e} menggunakan properti, tanpa kejadian sungguhan.', 'Video latihan terhenti karena {e} betulan terjadi di luar lokasi dan warga meminta bantuan.'),
        ('Peserta baru belajar menghadapi {e}; sampai selesai tidak terjadi peristiwa nyata.', 'Peserta selesai belajar ketika {e} terjadi di dekat gedung dan petugas menangani kerusakan.'),
        ('Dalam materi praktik, {e} diperagakan dengan alat bantu. Adegan itu tidak nyata.', 'Di dekat tempat praktik, {e} nyata menyebabkan kerusakan. Peristiwa ini bukan adegan latihan.'),
        ('Pemeriksaan memastikan kabar {e} berasal dari latihan; yang rusak hanyalah properti.', 'Pemeriksaan memastikan {e} terjadi sungguhan; properti latihan aman, tetapi bangunan warga rusak.'),
        ('Keterangan {e} pada lembar simulasi tidak menyatakan adanya kejadian sungguhan.', 'Keterangan petugas menyatakan {e} sungguhan terjadi saat simulasi; tidak ada korban jiwa.'),
    ]
    diagnostic_positive = [
        'Latihan penyelamatan dihentikan: {e} yang sesungguhnya baru terjadi dan warga dievakuasi.',
        'Tidak ada korban jiwa, tetapi {e} benar-benar terjadi dan petugas memeriksa bangunan rusak.',
        'Semua orang selamat setelah {e} terjadi di sebelah pusat pelatihan. Bantuan sedang dikirim.',
        'Informasi {e} telah diperiksa di lokasi dan ternyata benar; pesan ini bukan pengumuman latihan.',
        'Skenario yang dibaca peserta berbeda dari {e} sungguhan yang sedang ditangani di luar gedung.',
        'Tadi malam {e} merusak fasilitas di kampung, meskipun tidak ada orang yang terluka.',
        'Tim yang semula mengira hanya latihan menemukan {e} nyata dan meminta bantuan segera.',
        'Peristiwa {e} memang terjadi pagi ini. Kabar bahwa semuanya hanya peragaan sudah dibantah petugas.',
    ]
    rows = []; diagnostic = []
    for label, event in zip(LABELS[:-1], ['banjir','gempa','kebakaran','kecelakaan']):
        for i, pair in enumerate(pairs, 1):
            for polarity, text, gold in [('N',pair[0],'NON_EVENT'),('P',pair[1],label)]:
                rows.append(dict(id=f'CTX083-{label}-{i:02d}-{polarity}', text=text.format(e=event),
                    final=gold, label_origin='NEW_ASSISTANT_WEAK_TRAINING'))
        for i,text in enumerate(diagnostic_positive,1):
            diagnostic.append(dict(id=f'DIAG083-{label}-{i:02d}',text=text.format(e=event),
                final=label,family='context_diagnostic',label_origin='ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING'))
    negatives = [
        'Panitia memastikan benturan mobil dalam latihan kecelakaan hanyalah peragaan; tidak berlangsung kejadian nyata.',
        'Simulasi gempa memakai efek getaran. Pernyataan tentang bangunan runtuh hanya bagian naskah kegiatan.',
        'Air untuk latihan banjir disiapkan dalam kolam buatan; tidak terjadi banjir sungguhan di kampung.',
        'Adegan kebakaran pada pelatihan menggunakan alat peraga, tanpa adanya peristiwa nyata.',
        'Kendaraan yang tampak rusak itu properti kelas pertolongan kecelakaan, bukan akibat kecelakaan sungguhan.',
        'Tulisan gempa sungguhan pada contoh formulir hanya bahan belajar dan tidak melaporkan suatu kejadian.',
        'Petugas menyelesaikan peragaan tanggap banjir. Kerusakan dan korban yang ditampilkan semuanya tiruan.',
        'Suara ledakan dan api di layar adalah rekaman latihan kebakaran; petugas memastikan lokasi sekarang aman tanpa kejadian nyata.',
    ]
    diagnostic += [dict(id=f'DIAG083-NON_EVENT-{i:02d}',text=t,final='NON_EVENT',family='exercise_only',
        label_origin='ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING') for i,t in enumerate(negatives,1)]
    return rows, diagnostic


def run(root, warm, out):
    out.mkdir(parents=True,exist_ok=False)
    state=dict(schema='slr09-last-layer-context-0.8.3',status='PREPARING',started_at=datetime.now(timezone.utc).isoformat(),
        training_executed=False,quality_acceptance_approved=False,card_done=False,new_acceptance_inference_executed=False)
    write(out/'run_state.json',state)
    try:
        lock=json.loads((root/'config/quality_candidate_asset_lock_v0.8.2.json').read_text())
        for n,h in lock['models']['sena']['files'].items(): assert sha(warm/n)==h,n
        legacy=root/'evidence/quality_fix_v081/simulation_guard22b'
        sets={name:json.loads((legacy/f'frozen_{name}.json').read_text()) for name in
            ['human130','original146','adjudicated145','scope50','seen_v07_50','human_regression50']}
        base=json.loads((root/'evidence/quality_fix_v081/training21/training_records_frozen.json').read_text())
        # Deduplication prefers later human adjudication, without editing source files.
        indexed={normal(r['text']):dict(r) for r in base}
        for name,origin in [('adjudicated145','KNOWN_HUMAN_ADJUDICATED_NOW_TRAINING'),
                            ('scope50','KNOWN_ASSISTANT_SCOPE_NOW_TRAINING'),
                            ('human_regression50','KNOWN_HUMAN_REGRESSION_NOW_TRAINING')]:
            for r in sets[name]: indexed[normal(r['text'])]=dict(r,label_origin=origin)
        retirement=[]
        for name,folder in [('FINAL081','acceptance_v081'),('FINAL082','acceptance_v082')]:
            p=root/'evidence'/folder/'original_run/evidence/reviewed_bundle_frozen.json'
            rows=json.loads(p.read_text())['records']; assert len(rows)==50 and all(r['review']['status']=='APPROVED' for r in rows)
            sets[name]=[dict(r,final=r['gold_label']) for r in rows]
            for r in rows: indexed[normal(r['text'])]=dict(r,final=r['gold_label'],label_origin='REVIEWED_FINAL_NOW_TRAINING')
            retirement.append(dict(round=name,source_sha256=sha(p),ids=[r['id'] for r in rows],role='TRAINING_AND_SEEN_REGRESSION'))
        weak,diagnostic=contexts(); sets['context40_now_training']=diagnostic
        for r in weak+diagnostic:
            assert normal(r['text']) not in indexed
            indexed[normal(r['text'])]=r
        train=list(indexed.values())
        cfg=dict(seed=183,cpu_threads=2,max_epochs=3,batch_size=8,training_max_length=192,inference_max_length=512,
            trainable='LAST_ENCODER_BLOCK_POOLER_CLASSIFIER',encoder_lr=5e-6,head_lr=3e-5,
            preserve_correct_teacher_kl=.5,weak_weight=.25,new_context_weight=3.,human_weight=1.,reviewed_final_weight=2.,
            selection='ALL_EIGHT_KNOWN_CLASS_GATES_AND_ALL_CONTRASTS_AND_CONTEXT40_CORRECT_THEN_MIN_REGRESSIONS_THEN_MAX_MEAN_F1',
            all_existing_references_used_for_training_or_selection=True,human130_now_used_for_training=True,
            independent_validation_or_acceptance_claimed=False,confidence_cutoff_unchanged=.95,
            targets_unchanged=dict(macro_f1=.85,non_event_recall=.9,each_event_recall=.8),source_sha256=sha(Path(__file__)))
        write(out/'training_config.json',cfg);write(out/'training_records_frozen.json',train);write(out/'scoring_sets_frozen.json',sets)
        write(out/'reference_retirement.json',dict(retired_before_gradients=True,rounds=retirement,
            human130_role='NOW_TRAINING_NOT_HELD_OUT',context40_role='NOW_ASSISTANT_WEAK_TRAINING_NOT_HUMAN_ACCEPTANCE'))
        write(root/'data/retirement_after_FINAL082_v0.8.3.json',dict(retired_before_gradients=True,rounds=retirement,human130_now_training=True))
        shutil.copy2(Path(__file__),out/'executed_training_source.py')
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
        set_seed(cfg['seed']);torch.set_num_threads(2)
        tokenizer=AutoTokenizer.from_pretrained(warm,local_files_only=True,trust_remote_code=False)
        model=AutoModelForSequenceClassification.from_pretrained(warm,local_files_only=True,use_safetensors=True)
        assert model.config.id2label==dict(enumerate(LABELS))
        for p in model.parameters():p.requires_grad=False
        for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier]:
            for p in module.parameters():p.requires_grad=True
        def encode(rows,limit=512):return tokenizer([r['text'] for r in rows],padding=True,truncation=True,max_length=limit,return_tensors='pt')
        def probs(rows):
            model.eval(); result=[]
            with torch.inference_mode():
                for i in range(0,len(rows),16):result.extend(torch.softmax(model(**encode(rows[i:i+16])).logits,-1).tolist())
            return result
        state.update(status='BASELINE_INFERENCE',training_unique=len(train),training_origins=dict(Counter(r['label_origin'] for r in train)))
        write(out/'run_state.json',state);print('Baseline inference on',len(train),'known training narratives',flush=True)
        teacher=probs(train); teacher_by_key={normal(r['text']):p for r,p in zip(train,teacher)}
        write(out/'baseline_training_probabilities.json',teacher)
        # A historically DEFERRED item can still appear in an unchanged legacy
        # scoring set. Record its baseline for comparison, never train on it.
        missing={normal(r['text']):r for rows in sets.values() for r in rows if normal(r['text']) not in teacher_by_key}
        teacher_by_key.update(zip(missing,probs(list(missing.values()))))
        def evaluate():
            unique={normal(r['text']):r for rows in sets.values() for r in rows}; raw=probs(list(unique.values()));cache=dict(zip(unique,raw))
            scores={}; contrast={}; regressions=0; predictions={}
            for name,rows in sets.items():
                ps=[cache[normal(r['text'])] for r in rows];pred=[LABELS[max(range(5),key=lambda i:p[i])] for p in ps]
                scores[name]=metrics([r['final'] for r in rows],pred)
                contrast[name]=[r['id'] for r,p in zip(rows,pred) if r.get('family') in {'simulation','exercise_only','real_during_exercise','exercise_contrast'} and p!=r['final']]
                for r,p in zip(rows,pred):
                    old=teacher_by_key[normal(r['text'])];before=LABELS[max(range(5),key=lambda i:old[i])]
                    regressions+=int(before==r['final'] and p!=r['final'])
                predictions[name]=[dict(id=r['id'],text=r['text'],gold=r['final'],probabilities=dict(zip(LABELS,p))) for r,p in zip(rows,ps)]
            feasible=all(m['targets_met'] for n,m in scores.items() if n!='context40_now_training') and all(not a for a in contrast.values()) and scores['context40_now_training']['accuracy']==1.
            return dict(metrics=scores,contrast_errors=contrast,feasible=feasible,regressions_with_overlapping_sets=regressions),predictions
        baseline,bp=evaluate();write(out/'baseline_evaluation.json',baseline)
        head=list(model.classifier.parameters());ids={id(p) for p in head};other=[p for p in model.parameters() if p.requires_grad and id(p) not in ids]
        optimizer=torch.optim.AdamW([dict(params=other,lr=cfg['encoder_lr']),dict(params=head,lr=cfg['head_lr'])],weight_decay=.01)
        history=[];best=None
        for epoch in range(1,cfg['max_epochs']+1):
            order=list(train);random.Random(cfg['seed']+epoch).shuffle(order)
            model.eval()
            for module in [model.bert.encoder.layer[-1],model.bert.pooler,model.classifier,model.dropout]:module.train()
            loss_sum=0.;start=time.monotonic()
            for offset in range(0,len(order),8):
                batch=order[offset:offset+8];optimizer.zero_grad(set_to_none=True)
                logits=model(**encode(batch,192)).logits;gold=torch.tensor([LABELS.index(r['final']) for r in batch])
                weights=torch.tensor([3. if r['label_origin'] in {'NEW_ASSISTANT_WEAK_TRAINING','ASSISTANT_DIAGNOSTIC_RETIRED_TO_WEAK_TRAINING'} else 2. if r['label_origin']=='REVIEWED_FINAL_NOW_TRAINING' else .25 if 'ASSISTANT' in r['label_origin'] else 1. for r in batch])
                teacher_p=torch.tensor([teacher_by_key[normal(r['text'])] for r in batch]); keep=(teacher_p.argmax(-1)==gold).float()
                ce=(torch.nn.functional.cross_entropy(logits,gold,reduction='none')*weights).sum()/weights.sum()
                kl=torch.nn.functional.kl_div(torch.log_softmax(logits,-1),teacher_p,reduction='none').sum(-1)
                loss=ce+.5*(kl*keep).sum()/keep.sum().clamp_min(1.)
                assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(other+head,1.);optimizer.step()
                state.update(status='TRAINING',training_executed=True,gradient_updates_executed=True,epoch=epoch,step=offset//8+1,steps_per_epoch=(len(order)+7)//8)
                loss_sum+=float(loss.detach())
                if offset==0 or offset%80==0:write(out/'run_state.json',state);print('epoch',epoch,'step',state['step'],'/',state['steps_per_epoch'],'loss',round(float(loss.detach()),4),flush=True)
            result,predictions=evaluate();result.update(epoch=epoch,seconds=time.monotonic()-start,training_loss_mean=loss_sum/((len(order)+7)//8))
            history.append(result);write(out/'training_history.json',history)
            print(json.dumps(dict(epoch=epoch,feasible=result['feasible'],contrast_errors={n:a for n,a in result['contrast_errors'].items() if a},context40=result['metrics']['context40_now_training']['accuracy'],failed_class_sets=[n for n,m in result['metrics'].items() if not m['targets_met']])),flush=True)
            key=(result['feasible'],-result['regressions_with_overlapping_sets'],sum(m['macro_f1'] for m in result['metrics'].values()))
            if best is None or key>best:
                best=key;model.save_pretrained(out/'best_model',safe_serialization=True);tokenizer.save_pretrained(out/'best_model')
                write(out/'best_selection.json',result)
                for name,pred in predictions.items():write(out/f'predictions_{name}.json',pred)
            if result['feasible']:break
        selected=json.loads((out/'best_selection.json').read_text())
        state.update(status='SUCCEEDED' if selected['feasible'] else 'NO_FEASIBLE_CANDIDATE',selected_epoch=selected['epoch'],all_known_constraints_met=selected['feasible'],finished_at=datetime.now(timezone.utc).isoformat())
        write(out/'run_state.json',state);print(json.dumps(state,indent=2),flush=True)
        if not selected['feasible']:raise RuntimeError('No candidate satisfies existing regression constraints; no candidate export.')
    except Exception as error:
        state.update(status='FAILED',error=str(error),finished_at=datetime.now(timezone.utc).isoformat());write(out/'run_state.json',state)
        (out/'error_trace.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for a in ['root','warm-start','output']:p.add_argument('--'+a,type=Path,required=True)
    a=p.parse_args();run(a.root.resolve(),a.warm_start.resolve(),a.output.resolve())
