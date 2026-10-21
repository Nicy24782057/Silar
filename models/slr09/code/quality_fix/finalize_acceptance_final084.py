"""Preserve and package the first FINAL084 acceptance, with reviewed gold unchanged."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT.parents[2]
WORK=ROOT/'evidence/acceptance_v084_confirmed_20261020'
RUN=WORK/'acceptance_FINAL084/original_run'
OUT=BASE/'silar_delivery_FINAL084_20261020'
PREFIX='models/slr09/'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def read(path):return json.loads(path.read_text())


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def included(path):
    return (path.is_file() and '__pycache__' not in path.parts
        and path.suffix not in {'.pyc','.safetensors','.bin'}
        and not {'runtime','best_model'} & set(path.relative_to(ROOT).parts)
        and path.name not in {'finalize.stdout.txt','finalize_final084.stdout.txt'})


def main():
    OUT.mkdir(exist_ok=True)
    sys.path.insert(0,str(ROOT/'code/acceptance'))
    from evaluate_acceptance import validate,score,digest
    evaluation=read(RUN/'evaluation.json');workflow=read(RUN/'workflow_result.json')
    bundle=read(RUN/'reviewed_bundle_frozen.json')
    predictions=[json.loads(line) for line in (RUN/'predictions.jsonl').read_text().splitlines()]
    rows,preflight=validate(bundle,ROOT)
    assert workflow['status']=='SUCCEEDED' and workflow['records_completed']==50
    assert workflow['model_inference_executed'] and not workflow['training_executed']
    assert not evaluation['metric_targets_met'] and sum(evaluation['checks'].values())==8
    assert evaluation['checks']['empty_field_spurious_rate'] is False
    assert all(value==evaluation[key] for key,value in score(rows,predictions,bundle['protocol']).items())
    lock=read(RUN/'evaluation_lock.json')
    assert digest(bundle)==lock['bundle_sha256']
    assert sha(RUN/'predictions.jsonl')==evaluation['predictions_sha256']
    for relative,want in bundle['protocol']['binding']['files_sha256'].items():
        assert sha(ROOT/relative)==want
        assert sha(RUN.parent/'pre_inference_snapshot'/relative)==want
    notebook=read(ROOT/'notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb')
    assert notebook['metadata']['execution_succeeded']
    assert sum(len(p['nara_tokens']) for p in predictions)==692
    assert all(not p['sena_token_coverage']['truncated'] and p['nara_token_coverage']['all_regex_tokens_processed'] for p in predictions)
    source=BASE/'upload/Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx'
    assert sha(source)=='046e468d3b9cb137d39ce5886dbc0eee0325cc5d406902de745b980f02253ad4'
    assert sha(WORK/'submission'/source.name)==sha(source)
    audit=read(WORK/'submission/review_audit_before_inference.json')
    assert audit['all_50_statuses_approved'] and len(audit['semantic_changes'])==2
    spurious=[e for e in evaluation['fields']['errors'] if e['gold'] in (None,[],'')]
    assert len(spurious)==10 and evaluation['fields']['empty_denominator']==174
    assert evaluation['fields']['nonempty_denominator']==176
    assert evaluation['fields']['nonempty_exact']==154/176
    assert evaluation['fields']['empty_spurious_rate']==10/174
    write(WORK/'result_verification.json',dict(status='SUCCEEDED',records=50,tokens=692,
        all_50_human_reviews_approved=True,human_gold_unchanged=True,reviewer_corrections_preserved=2,
        saved_output_rescore_identical=True,bound_source_files_verified=21,
        source_snapshot_before_model_loading=True,notebook_actual_execution_succeeded=True,
        notebook_execution_engine=notebook['metadata']['execution_engine'],
        model_inference_executed=True,training_executed=False,all_tokens_processed=True,
        checks_passed=8,checks_total=9,metric_targets_met=False,
        quality_acceptance_approved=False,card_done=False,target_vm_verified=False,
        source_workbook_sha256=sha(source),predictions_sha256=sha(RUN/'predictions.jsonl')))
    queue=dict(status='QUALITY_IMPROVEMENT_REQUIRED',current_acceptance_immutable=True,
        current_FINAL084_reference_used_for_tuning=False,current_FINAL084_reference_retired_to_development=False,
        primary_failure='EMPTY_FIELD_SPURIOUS_RATE_10_OF_174_EXCEEDS_0.05',
        sena_false_events=evaluation['sena']['errors'],spurious_fields=spurious,
        all_field_discrepancies=evaluation['fields']['errors'],targets_unchanged=bundle['protocol']['targets'],
        required_next_actions=[
            'Reduce spurious impact descriptions for non-event activities and duplicated victim consequences.',
            'Distinguish an inspected or mentioned object from an object actually affected by the event.',
            'Preserve valid impacts, actual victims, SENA-only category, cutoff 0.95 and mandatory human verification.',
            'If FINAL084 informs any code/weight selection, retire it before tuning and require a new human-reviewed reference for the next acceptance.'],
        must_not_change='Do not rewrite reviewed gold, original predictions, metric targets or the first acceptance result to produce a pass.')
    write(WORK/'next_quality_work_queue.json',queue)

    specs=[
        ('SENA macro F1',evaluation['sena']['macro_f1'],'≥85%','sena_macro_f1'),
        ('Recall NON_EVENT',evaluation['sena']['per_class']['NON_EVENT']['recall'],'≥90%','non_event_recall'),
        ('Recall minimum empat kelas kejadian',min(evaluation['sena']['per_class'][x]['recall'] for x in ['FLOOD','EARTHQUAKE','FIRE','ACCIDENT']),'≥80%','all_event_class_recalls'),
        ('NARA macro F1 seluruh 14 non-O',evaluation['nara']['macro_f1_all_14_non_o'],'≥75%','nara_macro_f1_all_14_non_o'),
        ('NARA exact span F1',evaluation['nara']['exact_span_f1'],'≥60%','nara_exact_span_f1'),
        ('Field nonkosong tepat',evaluation['fields']['nonempty_exact'],'≥80%','fields_nonempty_exact'),
        ('Isi berlebih pada field kosong',evaluation['fields']['empty_spurious_rate'],'≤5%','empty_field_spurious_rate')]
    metrics='\n'.join(f'| {name} | {v:.2%} | {target} | {"Lulus" if evaluation["checks"][key] else "Belum lulus"} |' for name,v,target,key in specs)
    extra='\n'.join(f'| {x["id"]} | {x["field"]} | {json.dumps(x["prediction"],ensure_ascii=False)} |' for x in spurious)
    error=evaluation['sena']['errors'][0]
    assert error['id']=='FINAL084-NON_EVENT-08'
    report=f'''# Hasil penerimaan FINAL084 SLR_09 v0.8.4

**Status mutu: belum lulus. Status pekerjaan: In Review.** Uji penerimaan pertama pada FINAL084 selesai pada 20 Oktober 2026, pukul 22:38 WIB. Delapan dari sembilan pemeriksaan terpenuhi. Satu yang belum terpenuhi adalah isi berlebih pada field acuan kosong: 10/174 atau 5,75%, melebihi batas 5%.

## Hasil review manusia

Workbook yang diserahkan adalah `Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx`, reviewer Bintang. Seluruh 50 narasi berstatus APPROVED, masing-masing 10 per kelas. Semua 692 token terisi dan seluruh 14 role non-O tercakup. Teks narasi, ID, urutan/teks token, target dan cutoff lolos validasi.

Dua perubahan substantif dari usulan awal dipertahankan:

- FINAL084-EARTHQUAKE-01: Dampak menjadi `mengguncang` dari `mengguncang Kecamatan Puspareja`.
- FINAL084-EARTHQUAKE-10: token `susulan` menjadi O dari EARTHQUAKE-EVENT; token `Gempa` tetap pemicu kejadian.

Kedua perubahan adalah pilihan acuan reviewer yang valid dan bersumber dari teks. Catatan bahwa lokasi sudah berada di field Lokasi tidak menjadi larangan umum atas frasa yang boleh muncul pada dua field berbeda: peran token dan cakupan field tidak selalu satu banding satu. Misalnya, frasa korban dapat juga memberikan identitas pihak. Pada pengujian ini acuan tetap persis sesuai review, tanpa mengubah kode agar mengikuti dua koreksi tersebut.

SHA256 workbook masukan: `{sha(source)}`. Masukan asli tidak diedit; salinan identik, audit per sel dan dua perubahan acuan tersedia pada direktori submission.

## Hasil pengujian aktual

| Pemeriksaan | Hasil | Target tetap | Status |
| --- | ---: | ---: | --- |
{metrics}
| Kontrak adapter/Fusion | 0 kesalahan | 0 kesalahan | Lulus |
| Kontras simulasi/latihan dan kejadian nyata sesuai protokol | Semua benar | Semua benar | Lulus |

SENA benar pada 49/50 narasi (98%). Recall empat kelas kejadian masing-masing 100%; NON_EVENT benar 9/10, tepat memenuhi target 90%. Target memang mengizinkan satu kesalahan NON_EVENT pada sepuluh contoh; tidak ada tuntutan akurasi kategori 100% pada seluruh pilot.

Field nonkosong tepat berjumlah 154/176 (87,50%). Kecocokan pada field kosong tidak dimasukkan untuk menaikkan skor tersebut. Ada 32 perbedaan field secara keseluruhan: 22 pada acuan nonkosong dan 10 pada acuan kosong. Metrik isi berlebih menghitung sel field, bukan jumlah item di dalam sel.

## Satu kesalahan kategori

`{error['id']}`: “{error['text']}”

Acuan manusia NON_EVENT, prediksi SENA FLOOD, confidence {error['confidence']:.2%}. Ini cerita yang tidak menyatakan kejadian nyata. Kesalahan ditandai LOW_CLASSIFICATION_CONFIDENCE karena berada di bawah cutoff 0,95. Total empat narasi ditandai; tidak ada kesalahan kategori pada confidence ≥0,95 dalam 50 contoh ini. Hasil kecil ini tidak membuktikan kalibrasi atau jaminan 95% benar. Kategori tetap berasal dari SENA; FALSE-EVENT NARA tidak menggantinya.

Kasus fiksi tersebut dilaporkan pada metrik NON_EVENT. Pemeriksaan kontras khusus pada protokol mencakup keluarga simulasi, latihan murni, dan kejadian nyata saat latihan; semua contoh pada kelompok khusus itu benar. Kelulusan pemeriksaan kontras tersebut tidak menyembunyikan satu kesalahan fiksi di atas.

## Sepuluh field kosong yang terisi berlebih

| ID | Field | Prediksi |
| --- | --- | --- |
{extra}

Pola yang tersisa mencakup pengulangan frasa luka/meninggal ke dampak, objek yang sekadar diperiksa atau dipakai dalam pengaturan lalu lintas, frasa umum yang terbaca sebagai lokasi, serta aktivitas nonkejadian yang terbaca sebagai dampak. Ini diagnosis dari keluaran tersimpan, bukan perubahan gold atau implementasi.

Pada denominator tetap 174, batas 5% mengizinkan paling banyak delapan field kosong terisi. Sembilan masih 5,17%; delapan menjadi 4,60%. Perhitungan ini menjelaskan kegagalan metrik dan tidak mengizinkan penghapusan kesalahan atau perubahan acuan setelah hasil diketahui.

## Bukti dan batas kesimpulan

Notebook 31 benar-benar dieksekusi melalui CPython cell executor dan salinan `_executed` menyimpan stream serta metadata. Acuan manusia divalidasi dan dibekukan; 21 file terikat disalin sebelum pemuatan kedua model. Identitas arsip dan runtime diverifikasi. Inferensi SENA serta NARA berjalan pada seluruh 50 narasi tanpa pemotongan; 692 token diproses. Penghitungan ulang memakai prediksi tersimpan mereproduksi hasil secara identik.

Tidak ada pelatihan, perubahan bobot, penyesuaian adapter, penurunan target, atau perubahan cutoff pada tahap penerimaan ini. SENA tetap v0.8.4 dan NARA tetap reviewed pilot 20261018. Hasil lama pada 200 narasi merupakan regresi development; hasil FINAL084 ini adalah pengujian pertama pada 50 narasi baru yang sudah direview. Dua putaran tersebut tidak disamakan.

Pilot sintetis buatan asisten dengan review manusia ini bukan sampel lapangan acak yang representatif. Exact overlap terhadap sumber tersedia sudah diperiksa sebelum pengujian; independensi semantik dan keanggotaan seluruh training awal belum terbukti. Eksekusi memakai CPU representatif dan bukan verifikasi target VM/backend submission. Bukti 91 uji kontrak aktif sebelumnya tetap tersedia; kode terikat tidak berubah dan suite tidak dijalankan ulang tanpa kebutuhan.

## Kelanjutan

Prioritas perbaikan berikutnya adalah presisi field NARA, terutama sepuluh sel di atas, sambil menjaga dampak, korban dan objek yang benar. Satu false event pada cerita juga tetap menjadi catatan pengembangan. Pada checkpoint ini FINAL084 belum dipakai melatih atau memilih ulang kandidat dan belum dipensiunkan menjadi development. Jika hasilnya dipakai mengubah kandidat, pensiunkan set terlebih dahulu, pertahankan hasil pertama ini, dan gunakan acuan manusia baru untuk penerimaan berikutnya.

Persetujuan mutu, Done dan deployment tetap false. Kategori hanya dari SENA; NON_EVENT memblokir submission dan verifikasi manusia tetap wajib. Acuan PENDING dalam template merupakan usulan historis; sumber APPROVED yang benar-benar diuji berada pada `evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/reviewed_bundle_frozen.json`.
'''
    report_name='SLR09_Hasil_Penerimaan_FINAL084_v0.8.4.md'
    for p in [OUT/report_name,ROOT/report_name,WORK/report_name]:p.write_text(report)
    notes=ROOT/'Catatan_Kelanjutan_SLR09_2026-10-19.md'
    assert sha(notes)=='e0e1ade5c02ce8a73881bc16fd9b37b30c0ab3b6e4b796922282344393018d34'
    old_notes=notes.read_text()
    for name in ['SLR09_STATUS_v0.8.4.md','CHECKPOINT_v0.8.4.md']:(ROOT/name).write_text(report)
    (ROOT/'README.md').write_text('''# SLR_09 v0.8.4

Uji penerimaan pertama FINAL084 selesai: 8/9 pemeriksaan terpenuhi. SENA 49/50 benar, recall NON_EVENT 90%, field nonkosong tepat 87,50%. Isi berlebih 10/174 field (5,75%) masih di atas batas 5%. Status In Review; mutu belum lulus.

Baca [hasil penerimaan FINAL084](SLR09_Hasil_Penerimaan_FINAL084_v0.8.4.md) dan [recovery](RECOVERY_v0.8.4.json). Review manusia serta prediksi pertama dipertahankan. FINAL084 belum dipakai untuk tuning. Target/cutoff tetap; persetujuan mutu, Done dan deployment false. Template PENDING adalah riwayat usulan; acuan APPROVED yang dipakai sudah dibekukan dalam evidence penerimaan.
''')
    notes.write_text(report+'\n\n---\n\n# Riwayat sebelum hasil penerimaan FINAL084\n\n'+old_notes)
    shutil.copy2(notes,OUT/notes.name)
    shutil.copy2(source,ROOT/'acceptance'/source.name)
    shutil.copy2(ROOT/'SLR09_STATUS_v0.8.4.md',OUT/'SLR09_STATUS_v0.8.4.md')
    recovery=read(ROOT/'RECOVERY_v0.8.4.json')
    recovery.update(status='IN_REVIEW_ACCEPTANCE_FINAL084_REQUIRES_QUALITY_IMPROVEMENT',
        latest_acceptance=RUN.relative_to(ROOT).as_posix(),latest_joint_verification=RUN.relative_to(ROOT).as_posix(),
        latest_completed_notebook='notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb',
        latest_human_confirmation='evidence/acceptance_v084_confirmed_20261020/submission/review_audit_before_inference.json',
        latest_human_review_workbook='acceptance/'+source.name,
        next_work_queue='evidence/acceptance_v084_confirmed_20261020/next_quality_work_queue.json',
        next_reference_status='FINAL084_50_APPROVED_692_TOKENS_TESTED_NOT_USED_FOR_TUNING',
        next_workbook=None,next_notebook=None,new_acceptance_inference_executed=True,
        acceptance_metric_targets_met=False,checks_passed=8,checks_total=9,
        current_FINAL084_retired_to_development=False,current_FINAL084_used_for_tuning=False,
        quality_acceptance_approved=False,card_done=False,production_deployed=False,
        source_workbook_sha256=sha(source))
    write(ROOT/'RECOVERY_v0.8.4.json',recovery)
    # Verify bound inputs again after all status/report updates.
    validate(bundle,ROOT)

    previous=BASE/'silar_delivery_v084_20261020/SLR09_Checkpoint_Pengerjaan_v0.8.4.zip'
    assert sha(previous)=='12690c009f8dd5b0ae3ea09fcb058a5f8955570f94a020c996fba7edf152e577'
    history=ROOT/'historical/before_FINAL084_acceptance_v0.8.4'
    preservation=[]
    with zipfile.ZipFile(previous) as z:
        for name in z.namelist():
            if name.endswith('/'):continue
            assert '..' not in Path(name).parts
            data=z.read(name);want=hashlib.sha256(data).hexdigest()
            rel=name.removeprefix(PREFIX) if name.startswith(PREFIX) else '_archive_root/'+name
            current=ROOT/rel
            if name.startswith(PREFIX) and rel!='FILE_MANIFEST.json' and current.is_file() and sha(current)==want:destination=name
            else:
                target=history/rel;target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert target.read_bytes()==data
                else:target.write_bytes(data)
                destination=PREFIX+target.relative_to(ROOT).as_posix()
            preservation.append(dict(source=name,sha256=want,destination=destination))
    write(WORK/'checkpoint_preservation.json',dict(status='SUCCEEDED',previous_checkpoint_version=4,
        previous_checkpoint_sha256=sha(previous),preserved=preservation))
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    manifest=dict(schema='slr09-checkpoint-manifest-0.8.4',revision='0.8.4',pipeline_revision='0.8.4',
        manifest_itself_excluded=True,files=files,status='IN_REVIEW_ACCEPTANCE_FINAL084_REQUIRES_QUALITY_IMPROVEMENT',
        weights_included=False,new_gradient_training_executed=False,
        prior_v084_gradient_training_executed=True,prior_development_regression_sets_met=4,
        new_reference_status=recovery['next_reference_status'],new_acceptance_inference_executed=True,
        acceptance_metric_targets_met=False,acceptance_checks_passed=8,acceptance_checks_total=9,
        quality_acceptance_approved=False,card_done=False,remote_push_executed=False)
    write(ROOT/'FILE_MANIFEST.json',manifest)
    checkpoint=OUT/'SLR09_Checkpoint_Pengerjaan_v0.8.4.zip'
    with zipfile.ZipFile(checkpoint,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_RECOVERY.md',report)
        for p in sorted(ROOT.rglob('*')):
            if included(p):z.write(p,PREFIX+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(checkpoint) as z:
        assert z.testzip() is None
        for item in files:assert hashlib.sha256(z.read(PREFIX+item['path'])).hexdigest()==item['sha256']
        for item in preservation:assert hashlib.sha256(z.read(item['destination'])).hexdigest()==item['sha256']
    proof=OUT/'SLR09_Bukti_Penerimaan_FINAL084_v0.8.4.zip'
    proof_files=[p for p in sorted(WORK.rglob('*')) if p.is_file() and 'runtime' not in p.relative_to(WORK).parts
                 and '__pycache__' not in p.parts and p.suffix!='.pyc']
    proof_files += [ROOT/'notebooks/31_Uji_Penerimaan_SLR09_v0.8.4.ipynb',
        ROOT/'notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb',
        ROOT/'code/quality_fix/execute_notebook_cells_v06.py',Path(__file__)]
    with zipfile.ZipFile(proof,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        entries=[]
        for p in proof_files:
            name=p.relative_to(ROOT).as_posix();z.write(p,name)
            entries.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
        z.writestr('manifest.json',json.dumps(dict(status='FIRST_ACCEPTANCE_COMPLETED_8_OF_9_TARGETS_MET',files=entries,
            quality_acceptance_approved=False,card_done=False),ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(proof) as z:
        assert z.testzip() is None
        for item in json.loads(z.read('manifest.json'))['files']:
            assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    artifacts=[OUT/report_name,proof,checkpoint,OUT/notes.name,OUT/'SLR09_STATUS_v0.8.4.md']
    result=dict(status='SUCCEEDED',checks_passed=8,checks_total=9,metric_targets_met=False,
        original_workbook_unchanged=True,source_files_preserved=len(preservation),
        bound_source_files_verified=21,quality_acceptance_approved=False,card_done=False,
        artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in artifacts])
    write(OUT/'delivery_verification_FINAL084.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
