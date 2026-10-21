"""Assemble actual completed evidence and a pending reference kit; no model inference."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy_evidence(source, target):
    for p in sorted(source.rglob('*')):
        rel = p.relative_to(source)
        if not p.is_file() or any(x in rel.parts for x in ('runtime', 'cache', 'best_model', '__pycache__')):
            continue
        if p.suffix not in {'.json', '.jsonl', '.txt', '.log', '.py'}:
            continue
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and sha(dest) != sha(p):
            raise ValueError('Completed evidence changed: '+str(dest))
        shutil.copy2(p, dest)


def assemble(base, output):
    evidence = ROOT/'evidence/quality_fix_v081'
    for source, dest in [('training_context_v081','training21'),
                         ('verification_context_v081','export_verification22'),
                         ('contract_tests_v081','contract22'),
                         ('context_guard_v081','simulation_guard22b'),
                         ('verification_guard_v081','guard_verification22b'),
                         ('contract_guard_v081','guard_contract22b')]:
        state = base/source
        if not source.startswith('contract_'):
            assert load(state/'run_state.json')['status'] == 'SUCCEEDED'
        copy_evidence(state, evidence/dest)
    for number in (20, 21, 22, '22b'):
        source = base/f'notebook{number}_stdout.log'
        shutil.copy2(source, evidence/f'notebook{number}_stdout.log')
    manifest = base/'exports/SILAR_SENA_context_v0.8.1_20261019.manifest.json'
    if manifest.exists(): shutil.copy2(manifest, evidence/'export_manifest.json')
    shutil.copy2(base/'exports_guard_v081/SILAR_SENA_context_guard_v0.8.1_20261019.manifest.json',evidence/'guard_export_manifest.json')
    recovery = load(ROOT/'RECOVERY_v0.8.1.json')
    recovery.update(status='COMPLETE_MACHINE_PHASE_PENDING_HUMAN_REFERENCE_REVIEW',
        new_training21_status='SUCCEEDED', export22_verification_status='SUCCEEDED',
        extended_simulation_guard22b='SUCCEEDED',
        contract_tests_passed=71, new_reference_status='50_PENDING_NOT_INFERRED',
        quality_acceptance_approved=False, card_done=False)
    write(ROOT/'RECOVERY_v0.8.1.json', recovery)

    # Source records and old human gold remain byte-identical to the delivered v0.5.
    originals = []
    prior = base/'base_v0.5/models/slr09'
    for relative in ['data/sena_train_reviewed.jsonl','data/sena_validation_reviewed.jsonl',
                     'code/active_nara_adapter/legacy_postprocessing.py',
                     'code/active_nara_adapter/nara_data.py',
                     'code/active_nara_adapter/nara_experiment.py',
                     'code/active_nara_adapter/nara_metrics.py']:
        p = ROOT/relative
        assert sha(p) == sha(prior/relative)
        originals.append({'path':relative,'sha256':sha(p),'unchanged_from':'DELIVERED_V0.5'})
    historical = [p for p in (prior/'acceptance').glob('*.json') if p.name=='review_bundle_draft.json']
    assert historical
    # The old pilot itself is retained in the completed frozen evidence.
    old_reference = load(base/'verification_context_v081/human_regression_reference.json')
    prior_reference = load(prior/'evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json')
    assert old_reference['records'] == prior_reference['records']
    write(evidence/'source_integrity.json', {'verified_files':originals,
        'old_human_pilot_frozen_sha256':sha(base/'verification_context_v081/human_regression_reference.json'),
        'old_human_pilot_rows':len(old_reference['records']) if isinstance(old_reference,dict) else len(old_reference),
        'old_human_pilot_records_unchanged_from_v05':True,
        'training_source_matches_executed_copy':sha(ROOT/'code/quality_fix/train_context_correction_v081.py') == sha(base/'training_context_v081/executed_training_source.py')})

    bundle_path = ROOT/'acceptance/review_bundle_draft.json'
    old = load(bundle_path)
    history = ROOT/'acceptance/history/pre_v0.8.1'
    if not history.exists():
        history.mkdir(parents=True)
        for name in ['review_bundle_draft.json','known_inputs.json','README.md','Review_Acuan_SLR09.xlsx','Review_Acuan_SLR09.html']:
            p = ROOT/'acceptance'/name
            if p.exists(): shutil.copy2(p, history/name)
    proposals = load(ROOT/'data/final_reference_proposals_v0.8.1.json')
    assert len(proposals['records']) == 50
    assert all(x['review']['status']=='PENDING' and not x['review']['reviewer'] for x in proposals['records'])

    # Union the historical index with every available development/training text.
    known = load(history/'known_inputs.json')
    hashes = set(known['normalized_text_sha256'])
    source_files = []
    def collect(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get('text'),str):
                text = ' '.join(obj['text'].casefold().split())
                hashes.add(hashlib.sha256(text.encode()).hexdigest())
            for item in obj.values(): collect(item)
        elif isinstance(obj,list):
            for item in obj: collect(item)
    for directory in ('data','evidence'):
        for p in sorted((ROOT/directory).rglob('*')):
            if not p.is_file() or p.suffix not in {'.json','.jsonl'} or p.name.startswith('final_reference_'):
                continue
            if p.suffix=='.json': collect(load(p))
            else:
                for line in p.read_text(encoding='utf-8').splitlines():
                    if line.strip(): collect(json.loads(line))
            source_files.append(p.relative_to(ROOT).as_posix())
    proposed_hashes = {hashlib.sha256(' '.join(r['text'].casefold().split()).encode()).hexdigest() for r in proposals['records']}
    assert len(proposed_hashes)==50 and not (proposed_hashes & hashes)
    write(ROOT/'acceptance/known_inputs.json',{
        'schema':'slr09-known-inputs-0.8.1','normalized_text_sha256':sorted(hashes),
        'sources':source_files,'historical_hashes_preserved':True,
        'scope':'Available texts only; normalized exact matching does not establish semantic independence or membership in the unavailable original pretraining/training corpus.'})

    files = [p for p in (ROOT/'code/active_nara_adapter').glob('*.py')]
    files += [ROOT/p for p in ['code/acceptance/evaluate_acceptance.py',
        'code/acceptance/import_review_xlsx.py','config/SLR09_Konfigurasi_Integrasi_v0.6.json',
        'config/quality_candidate_asset_lock_v0.8.1.json','config/inference_environment.json',
        'config/requirements-inference.txt','acceptance/known_inputs.json',
        'data/final_reference_proposals_v0.8.1.json','data/final_reference_identity_v0.8.1.json',
        'data/development_review_v0.8.json','code/quality_fix/train_context_correction_v081.py',
        'code/quality_fix/fit_simulation_guard_v081.py','asset_manifest.json',
        'evidence/quality_fix_v081/training21/training_records_frozen.json',
        'evidence/quality_fix_v081/training21/executed_training_source.py']]
    protocol = deepcopy(old['protocol'])
    protocol['binding'] = {'candidate_version':'0.8.1','files_sha256':{
        p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    protocol['reference_round'] = 'FINAL081_PENDING_HUMAN_REVIEW_BEFORE_ACCEPTANCE_INFERENCE'
    protocol['prior_development_approval_does_not_approve_this_reference'] = True
    write(bundle_path, {'protocol':protocol,'records':proposals['records']})
    write(evidence/'acceptance_kit_binding.json',{
        'draft_sha256':sha(bundle_path),'proposals_sha256':sha(ROOT/'data/final_reference_proposals_v0.8.1.json'),
        'known_inputs_count':len(hashes),'new_records':50,'normalized_exact_overlap':0,
        'all_pending':True,'model_inference_executed':False,'quality_acceptance_approved':False})

    metrics = load(base/'context_guard_v081/metrics.json')
    evaluation = load(base/'verification_guard_v081/evaluation.json')
    v07 = load(base/'verification_guard_v081/v07_seen_evaluation.json')
    baseline = load(base/'baseline_restored_v081/v07_seen_evaluation.json')
    def small(m):
        return {'macro_f1':m['macro_f1'],'non_event_recall':m['per_class']['NON_EVENT']['recall'],
                'min_event_recall':min(v['recall'] for k,v in m['per_class'].items() if k!='NON_EVENT')}
    errors=[]
    for name, title in [('original146','Asli146 (15 masuk training)'),('scope50','Development50 v0.6 (usulan)'),('seen_v07_50','Regresi50 v0.7 (training lemah)')]:
        for row in load(base/f'context_guard_v081/predictions_{name}.json'):
            label = max(row['probabilities'],key=row['probabilities'].get)
            if label!=row['gold']:
                errors.append({'scope':title,'id':row['id'],'text':row['text'],'gold':row['gold'],
                               'prediction':label,'confidence':row['probabilities'][label]})
    notebooks=[]
    for name in ('17','17b','18','17c','17d','17e'):
        notebooks.append([f'{name} (riwayat v0.8)',
            'Eksperimen sebelum pemulihan; bobot/metadata yang tersimpan dipertahankan.',
            'Output notebook asli tidak tersedia setelah sesi terputus; tidak direka ulang.',
            'Riwayat percakapan, bukan bukti eksekusi notebook yang dipulihkan.'])
    for name,usage in [('20_Verifikasi_Bobot_Dipulihkan_v0.8.1.ipynb','Verifikasi baru model v0.8 yang benar-benar tersimpan.'),
                       ('21_Koreksi_Konteks_SENA_CPU_v0.8.1.ipynb','Training aktual 1 epoch; 1.249 contoh unik, pemilihan development.'),
                       ('22_Verifikasi_Kandidat_SLR09_v0.8.1.ipynb','Ekspor dan verifikasi kandidat pertama; digantikan penjagaan22b.'),
                       ('22b_Penguatan_Kontras_Simulasi_v0.8.1.ipynb','Pemilihan bias dengan seluruh kontras yang tersedia; ekspor, 71 tes dan verifikasi final.')]:
        notebooks.append([name,usage,'SUCCEEDED: sel CPython; salinan _executed disimpan.','Development/regresi, belum penerimaan akhir.'])
    notebooks.append(['23_Uji_Penerimaan_Akhir_SLR09_v0.8.1.ipynb','Impor Excel yang sudah direview, validasi acuan, lalu inferensi dan penilaian.',
        'BELUM DIJALANKAN: 50 acuan baru masih PENDING.','Dijalankan di sini sesudah review; tidak meminta pengguna menjalankan di laptop.'])
    sets=[]
    for key,title,n,role in [('human130','Manusia130 di luar latihan',130,'Development untuk seleksi'),
        ('original146','Label sumber asli146',146,'Regresi;15 masuk training'),
        ('adjudicated145','Acuan hasil review145',145,'Regresi;15 masuk training'),
        ('scope50','Usulan50 v0.6',50,'Development usulan asisten')]:
        s=small(metrics[key]);sets.append([title,n,s['macro_f1'],s['non_event_recall'],s['min_event_recall'],role])
    lock=load(ROOT/'config/quality_candidate_asset_lock_v0.8.1.json')
    data={'comparison':[evaluation['sena']['macro_f1'],evaluation['sena']['per_class']['NON_EVENT']['recall'],
        evaluation['nara']['macro_f1_all_14_non_o'],evaluation['nara']['exact_span_f1'],
        evaluation['fields']['nonempty_exact'],evaluation['fields']['empty_spurious_rate']],
        'dev':small(metrics['human130']),'epoch':1,'v07':small(v07),'baseline':small(baseline),
        'sets':sets,'errors':errors,'archive_name':lock['models']['sena']['archive_name'],'notebooks':notebooks,
        'v07_predictions':[{'id':r['id'],'label':r['event_classifier']['label'],'confidence':r['event_classifier']['confidence']}
            for r in load(base/'verification_guard_v081/v07_seen_predictions.json')],
        'remaining_seen_regression_errors':v07['errors'],
        'first_candidate_dev':small(load(base/'training_context_v081/metrics.json')['human130']),
        'known_contrasts':load(base/'context_guard_v081/best_selection.json')['known_contrasts'],
        'v07_remaining_note':'Regresi v0.7 masih salah '+str(len(v07['errors']))+'/50. Target numerik dan seluruh kontras simulasi/latihan pada set yang sudah dilihat terpenuhi. Ini tetap development/regresi, bukan penerimaan akhir.'}
    write(output/'report_data.json',data)
    print(json.dumps({'evidence_completed':True,'new_reference_status':'50_PENDING',
        'known_inputs':len(hashes),'remaining_seen_regression_errors':len(v07['errors']),
        'model_inference_executed':False},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assemble(a.workspace,a.output)
