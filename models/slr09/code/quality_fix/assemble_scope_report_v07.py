"""Assemble the Excel inputs from actual records, preserving review identity."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
from evaluate_acceptance import score,classification
from train_sena_cpu import LABELS,write,sha

def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def minimum(m):return min(m['per_class'][c]['recall'] for c in LABELS[:-1])

def assemble(work,output):
    previous=read(ROOT/'evidence/quality_fix_v05/report_data.json')
    diag=work/'quality_diagnostics_v07';run=work/'training_matched_v07'
    state=read(diag/'run_state.json');trainstate=read(run/'run_state.json')
    assert state['status']==trainstate['status']=='SUCCEEDED'
    bundle=read(diag/'reviewed_bundle_frozen.json');predictions=lines(diag/'predictions.jsonl')
    actual=score(bundle['records'],predictions,bundle['protocol']);recorded=read(diag/'evaluation.json')
    for key in ('sena','nara','fields','checks','metric_targets_met'):assert actual[key]==recorded[key],key
    v06=read(work/'quality_diagnostics_v06/run_state.json')['diagnostic_summary']
    fresh=read(diag/'new50_frozen.json');fresh_predictions=read(diag/'new50_predictions.json')
    fresh_actual=classification(fresh['records'],fresh_predictions);fresh_recorded=read(diag/'new50_evaluation.json')
    for key in fresh_actual:assert fresh_actual[key]==fresh_recorded[key],key
    seen=read(diag/'seen74_reference.json');seen_predictions=read(diag/'seen74_predictions.json')
    seen_actual=classification(seen['records'],seen_predictions)
    for key in seen_actual:assert seen_actual[key]==read(diag/'seen74_evaluation.json')[key],key
    assert sha(ROOT/'data/frozen_new_diagnostic_v0.7.json')==read(ROOT/'data/scope_v07_split_guard.json')['new50_sha256']
    assert not trainstate['v07_new50_used_for_training_or_selection']
    tests=read(work/'contract_tests_v07/active_tests.json');assert tests['all_passed']
    field_before=read(ROOT/'evidence/quality_fix_v05/quality_diagnostics_v05/evaluation.json')
    assert actual['nara']==field_before['nara'] and actual['fields']==field_before['fields']
    hm=read(run/'best_development_metrics.json');selection=read(run/'best_selection.json')
    errors=[]
    for name,data in [('Development manusia146',read(run/'best_human_development_predictions.json'))]:
        for row in data:
            guess=max(row['probabilities'],key=row['probabilities'].get);confidence=row['probabilities'][guess]
            if guess!=row['gold']:errors.append({'scope':name,'id':row['id'],'text':row['text'],'gold':row['gold'],
                'prediction':guess,'confidence':confidence,'high_confidence':confidence>=.95})
    for name,result in [('Regresi manusia50 lama',actual['sena']),('Development asisten74',seen_actual),('Diagnostik baru50 v0.7',fresh_actual)]:
        errors += [dict(row,scope=name,high_confidence=row['confidence']>=.95) for row in result['errors']]
    comparison=previous['comparison']
    comparison[0]['after']=actual['sena']['macro_f1'];comparison[1]['after']=actual['sena']['per_class']['NON_EVENT']['recall']
    notebooks=previous['notebooks']
    added=[
      ('13_Perbaikan_Konteks_SENA_CPU_v0.6','Latihan tambahan cakupan konteks','Development manusia146 + asisten128; diagnostik50 belum lulus'),
      ('13b_Penyeimbangan_Kelas_SENA_v0.6','Analisis dan fitting bias pada development','Bias +3.4 gagal menjaga recall kejadian nyata'),
      ('14_Verifikasi_SENA_dan_Regresi_SLR09_v0.6','Ekspor, tes kontrak, inferensi nyata','50 baru v0.6 sudah dilihat dan kemudian dipindah ke development'),
      ('15_Latihan_Pasangan_Konteks_SENA_v0.7','Latihan pasangan dengan loss pemisahan konteks','Manusia146 dan asisten74 untuk seleksi; label tambahan PENDING'),
      ('16_Verifikasi_Kandidat_SLR09_v0.7','Ekspor, tes, reproduksi dev, regresi dan diagnostik','50 baru v0.7 tidak dipakai memilih model; belum acuan manusia')]
    for stem,usage,scope in added:
        nb=read(ROOT/'notebooks'/(stem+'_executed.ipynb'))
        assert nb['metadata']['execution_succeeded'] is True,stem
        assert all(c.get('execution_count') for c in nb['cells'] if c['cell_type']=='code')
        notebooks.append({'name':stem+'.ipynb','usage':usage,'execution':'Dijalankan di sini (CPython)','scope':scope})
    new_rows=[]
    for row,pred in zip(fresh['records'],fresh_predictions):
        event=pred['event_classifier'];assert row['id']==pred['id']
        new_rows.append({'id':row['id'],'text':row['text'],'proposed_label':row['gold_label'],
            'prediction':event['label'],'confidence':event['confidence'],'family':row['family']})
    summary={'records':50,'macro_f1':fresh_actual['macro_f1'],
        'non_event_recall':fresh_actual['per_class']['NON_EVENT']['recall'],
        'min_event_recall':minimum(fresh_actual),'errors':len(fresh_actual['errors']),
        'false_event':fresh_actual['false_event'],'false_non_event':fresh_actual['false_non_event'],
        'targets_met':fresh_recorded['classification_targets_met'],'human_reference_reviewed':False}
    old24=read(ROOT/'evidence/quality_fix_v05/quality_diagnostics_v05/fresh_challenge_evaluation.json')
    history=[['v0.5, 24 lama',24,old24['macro_f1'],old24['per_class']['NON_EVENT']['recall'],minimum(old24),'Kini development'],
        ['v0.6, 24 lama',24,v06['seen24']['macro_f1'],v06['seen24']['non_event_recall'],v06['seen24']['minimum_event_recall'],'Kini development'],
        ['v0.6, 50 baru',50,v06['new50']['macro_f1'],v06['new50']['non_event_recall'],v06['new50']['minimum_event_recall'],'Kini development'],
        ['v0.7, 74 lama',74,seen_actual['macro_f1'],seen_actual['per_class']['NON_EVENT']['recall'],minimum(seen_actual),'Dipakai seleksi']]
    data={'schema':'slr09-report-data-0.7','status':'IN REVIEW','quality_acceptance_approved':False,'card_done':False,
        'comparison':comparison,'development':previous['development'],
        'latest_development':{'name':'Pasangan konteks v0.7','macro_f1':hm['macro_f1'],
            'non_event_recall':hm['per_class']['NON_EVENT']['recall'],'min_event_recall':minimum(hm),'best_epoch':selection['epoch']},
        'history':history,'fresh':summary,'new_rows':new_rows,'sena_errors':errors,
        'notebooks':notebooks,'tests':f"{tests['tests_run']}/{tests['tests_run']} lulus",
        'next_action':'Review label development dan lakukan penerimaan baru dengan acuan manusia sebelum Done.',
        'frozen_diagnostic_sha256':sha(ROOT/'data/frozen_new_diagnostic_v0.7.json'),
        'model_id':state['models']['sena']['model_id'],'model_weights_sha256':state['models']['sena']['files']['model.safetensors'],
        'verification':{'scores_recomputed':True,'development_export_reproduced':True,'nara_and_fields_unchanged':True,
            'new50_used_for_selection':False,'legacy_helper_unchanged':sha(ROOT/'code/active_nara_adapter/legacy_postprocessing.py')=='06275b3aa338718689fba66984626754e6b34739156f65e378ceaad4b06bfa9f'}}
    assert data['verification']['legacy_helper_unchanged']
    write(output,data);print(json.dumps({'fresh':summary,'development':data['latest_development'],'evidence_verified':True},indent=2))
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assemble(a.work,a.output)
