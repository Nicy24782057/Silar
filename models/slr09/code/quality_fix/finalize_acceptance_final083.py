"""Preserve the first FINAL083 acceptance result without changing candidate or gold."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT.parents[2]
WORK = ROOT / 'evidence/acceptance_v083_confirmed_20261020'
RUN = WORK / 'acceptance_FINAL083/original_run'
OUT = BASE / 'silar_delivery_FINAL083_20261020'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def included(path):
    relative = path.relative_to(ROOT).as_posix()
    return (path.is_file() and '__pycache__' not in path.parts
            and path.suffix not in {'.pyc', '.safetensors', '.bin'}
            and not relative.startswith('evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run/runtime/'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / 'code/acceptance'))
    from evaluate_acceptance import validate, score, digest
    evaluation = read(RUN / 'evaluation.json')
    workflow = read(RUN / 'workflow_result.json')
    bundle = read(RUN / 'reviewed_bundle_frozen.json')
    predictions = [json.loads(line) for line in (RUN / 'predictions.jsonl').read_text().splitlines()]
    rows, preflight = validate(bundle, ROOT)
    assert workflow['status'] == 'SUCCEEDED' and workflow['records_completed'] == 50
    assert workflow['model_inference_executed'] and not workflow['training_executed']
    assert not evaluation['metric_targets_met'] and not evaluation['quality_acceptance_approved']
    assert sum(evaluation['checks'].values()) == 6
    # Re-score the same saved outputs only; do not rerun neural inference or alter evidence.
    rescored = score(rows, predictions, bundle['protocol'])
    for key, value in rescored.items():
        assert value == evaluation[key], key
    lock = read(RUN / 'evaluation_lock.json')
    assert digest(bundle) == lock['bundle_sha256']
    assert SHA(RUN / 'predictions.jsonl') == evaluation['predictions_sha256']
    for relative, want in bundle['protocol']['binding']['files_sha256'].items():
        assert SHA(ROOT / relative) == want
        assert SHA(WORK / 'acceptance_FINAL083/pre_inference_snapshot' / relative) == want
    notebook = read(ROOT / 'notebooks/28_Uji_Penerimaan_SLR09_v0.8.3_executed.ipynb')
    assert notebook['metadata']['execution_succeeded']
    assert sum(len(p['nara_tokens']) for p in predictions) == 685
    assert all(not p['sena_token_coverage']['truncated'] and p['nara_token_coverage']['all_regex_tokens_processed'] for p in predictions)
    approval = read(WORK / 'submission/explicit_chat_approval.json')
    assert approval['user_message'] == 'oke setuju dan lanjut'
    final_workbook = WORK / 'submission/Review_Penerimaan_Akhir_SLR09_v0.8.3_Final_Disetujui.xlsx'
    assert SHA(final_workbook) == approval['final_workbook_sha256']
    assert SHA(WORK / 'acceptance_FINAL083' / final_workbook.name) == SHA(final_workbook)
    false_fields = [e for e in evaluation['fields']['errors'] if e['gold'] in (None, [], '')]
    assert len(false_fields) == 11
    queue = dict(status='QUALITY_IMPROVEMENT_REQUIRED', original_acceptance_result_immutable=True,
        candidate_has_been_tuned_on_FINAL083=False, reference_has_been_retired_to_development=False,
        sena_false_events=evaluation['sena']['errors'], spurious_fields=false_fields,
        required_actions=[
            'Improve SENA discrimination of peragaan/getaran buatan/bukan gempa sungguhan versus a real earthquake.',
            'Improve SENA discrimination of banjir pada latihan/ditiru/permukiman tetap kering versus actual flooding.',
            'Reduce NARA reporting-only, negated, synthetic-object and fictional-location extractions using the existing role/field contract.',
            'Preserve true event classes, literal victims, cutoff 0.95, NARA extraction and human verification contracts.',
        ],
        rule_before_tuning='Before using these errors to change weights/code, retire FINAL083 to development, preserve its original human labels and results, and prepare a new human-reviewed reference before another acceptance run.',
        acceptance_targets_unchanged=bundle['protocol']['targets'])
    write(WORK / 'next_quality_work_queue.json', queue)
    verification = dict(status='SUCCEEDED', records=50, tokens=685, all_50_human_reviews_approved=True,
        explicit_two_token_corrections_recorded=True, saved_output_rescore_identical=True,
        bound_source_files_verified=len(bundle['protocol']['binding']['files_sha256']),
        source_snapshot_before_model_loading=True, notebook_actual_execution_succeeded=True,
        notebook_execution_engine=notebook['metadata']['execution_engine'],
        model_inference_executed=True, training_executed=False, contract_errors=0,
        metric_targets_met=False, checks_passed=6, checks_total=9,
        quality_acceptance_approved=False, card_done=False, target_vm_verified=False,
        original_model_archives_unchanged=True, final_reference_sha256=SHA(final_workbook),
        predictions_sha256=SHA(RUN / 'predictions.jsonl'))
    write(WORK / 'result_verification.json', verification)
    checks = [
        ('SENA macro F1', evaluation['sena']['macro_f1'], '≥85%', 'sena_macro_f1'),
        ('Recall NON_EVENT', evaluation['sena']['per_class']['NON_EVENT']['recall'], '≥90%', 'non_event_recall'),
        ('Recall minimum empat kelas kejadian', min(evaluation['sena']['per_class'][x]['recall'] for x in ['FLOOD','EARTHQUAKE','FIRE','ACCIDENT']), '≥80%', 'all_event_class_recalls'),
        ('NARA macro F1 seluruh 14 non-O', evaluation['nara']['macro_f1_all_14_non_o'], '≥75%', 'nara_macro_f1_all_14_non_o'),
        ('NARA exact span F1', evaluation['nara']['exact_span_f1'], '≥60%', 'nara_exact_span_f1'),
        ('Field nonkosong tepat', evaluation['fields']['nonempty_exact'], '≥80%', 'fields_nonempty_exact'),
        ('Isi berlebih pada field kosong', evaluation['fields']['empty_spurious_rate'], '≤5%', 'empty_field_spurious_rate'),
    ]
    metrics = '\n'.join(f'| {name} | {value:.2%} | {target} | {"Lulus" if evaluation["checks"][key] else "Belum lulus"} |' for name,value,target,key in checks)
    error_rows = '\n'.join(f'| {e["id"]} | {e["gold"]} | {e["prediction"]} | {e["confidence"]:.2%} | Ya |' for e in evaluation['sena']['errors'])
    field_rows = '\n'.join(f'| {e["id"]} | {e["field"]} | {json.dumps(e["prediction"],ensure_ascii=False)} |' for e in false_fields)
    report = f'''# Hasil uji penerimaan FINAL083 SLR_09 v0.8.3

**Status mutu: belum lulus. Status pekerjaan: In Review.** Eksekusi pengujian selesai pada 20 Oktober 2026. Enam dari sembilan pemeriksaan terpenuhi. Tiga yang belum terpenuhi ialah recall NON_EVENT, isi berlebih pada field kosong, dan kontras simulasi/latihan dengan kejadian nyata.

## Acuan dan koreksi yang disetujui

Reviewer pada Excel: Bintang. Sebanyak 50 narasi dan 685 token sudah APPROVED, dengan 10 narasi tiap kelas dan seluruh 14 role non-O. Pesan pengguna “oke setuju dan lanjut” pada 20 Oktober 2026 pukul 21:10:35 WIB mengesahkan dua koreksi yang sebelumnya diusulkan:

- Token!D531, peserta pada FINAL083-NON_EVENT-01: O menjadi OFFICER-ARG.
- Token!D574, penyebutan gempa kedua pada FINAL083-NON_EVENT-03: O menjadi FALSE-EVENT.

Perbandingan menyeluruh memastikan hanya dua nilai label itu berubah. ID, teks, kategori, field, keputusan review, rumus, freeze panes, tabel dan dropdown dipertahankan. Berkas masukan asli tersimpan sebagai bukti. SHA256 Excel final: `{SHA(final_workbook)}`.

## Hasil terukur

| Pemeriksaan | Hasil | Target | Status |
| --- | ---: | ---: | --- |
{metrics}
| Kontrak adapter dan Fusion | 0 kesalahan | 0 kesalahan | Lulus |
| Kontras simulasi/latihan dan kejadian nyata | 2 salah | Semua benar | Belum lulus |

SENA benar pada 48/50 narasi (96%). Empat kelas kejadian masing-masing memiliki recall 100%; NON_EVENT benar 8/10. Field nonkosong tepat adalah 158/188, sedangkan isi berlebih terjadi pada 11/162 field acuan kosong. Metrik field tidak menggunakan kecocokan kosong untuk menaikkan skor nonkosong.

## Dua kesalahan kategori

| ID | Acuan | Prediksi SENA | Confidence | Ditandai di bawah cutoff |
| --- | --- | --- | ---: | --- |
{error_rows}

Narasi pertama menyatakan getaran buatan dalam peragaan serta bukan gempa sungguhan. Narasi kedua menyatakan banjir dalam latihan yang ditiru dengan kolam kecil, sementara permukiman tetap kering. Keduanya beracuan NON_EVENT. Prediksi SENA masih mengikuti kata kejadian pada dua konteks tersebut.

Cutoff tetap 0,95. Kedua kesalahan mempunyai flag LOW_CLASSIFICATION_CONFIDENCE. Total lima narasi ditandai di bawah cutoff, termasuk kedua kesalahan. Tidak terdapat kesalahan kategori pada confidence ≥0,95 dalam pilot ini. Temuan pada 50 narasi tersebut tidak membuktikan kalibrasi probabilitas atau jaminan akurasi 95% di lapangan. Kategori tetap berasal dari SENA dan tidak diganti oleh FALSE-EVENT NARA.

## Isi berlebih pada acuan kosong

Semua baris di bawah memiliki acuan kosong pada field terkait.

| ID | Field | Isi prediksi |
| --- | --- | --- |
{field_rows}

Pola yang perlu diperbaiki mencakup keterangan pelaporan yang terbaca sebagai dampak, pengulangan keterangan korban ke field dampak, objek pada simulasi, dan lokasi rekaan. Daftar lengkap 41 perbedaan field serta kesalahan token NARA tersedia dalam evaluation.json. Acuan manusia tidak disesuaikan dengan keluaran model.

## Bukti dan cakupan

Notebook 28 benar-benar dieksekusi lewat CPython cell executor. Salinan `_executed` menyimpan stream dan metadata eksekusi, tanpa klaim kernel Jupyter asli. Acuan divalidasi dan dibekukan, lalu 21 berkas sumber terikat disalin sebelum pemuatan model. Kedua arsip dimuat setelah pemeriksaan SHA256. Inferensi SENA dan NARA berjalan pada seluruh 50 narasi tanpa pemotongan; semua 685 token diproses. Penghitungan ulang dari prediksi tersimpan memberikan hasil yang identik.

Bobot SENA tetap SILAR_SENA_context_v0.8.3_20261020.zip dan NARA tetap SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip. Tidak ada pelatihan atau perubahan implementasi kandidat pada tahap ini. Pengujian memakai CPU lingkungan representatif, bukan bukti target VM atau backend submission.

Pilot terdiri dari 50 narasi sintetis buatan asisten yang diperiksa manusia. Tidak ada exact overlap ternormalisasi terhadap sumber tersedia. Keanggotaan seluruh sumber pada training awal belum dapat dibuktikan dan generalisasi populasi belum ditetapkan.

## Kelanjutan

Prioritas berikutnya ialah dua pola false event SENA dan presisi field NARA. Hasil penerimaan pertama, sumber review dan label manusia tetap dipertahankan. Jika kesalahan FINAL083 dipakai mengubah model atau kode, set ini harus dipensiunkan menjadi development/regresi dan uji penerimaan berikutnya memerlukan acuan manusia baru. Pada checkpoint ini, FINAL083 belum dipakai melatih atau memilih ulang kandidat.

Persetujuan mutu, Done dan deployment tetap false. Hasil lengkap tersedia dalam SLR09_Bukti_Penerimaan_FINAL083_v0.8.3.zip.
'''
    report_name = 'SLR09_Hasil_Penerimaan_FINAL083_v0.8.3.md'
    (OUT / report_name).write_text(report)
    (ROOT / report_name).write_text(report)
    (WORK / report_name).write_text(report)
    history = ROOT / 'historical/before_FINAL083_acceptance_v0.8.3'
    for name in ['README.md','CHECKPOINT_v0.8.3.md','SLR09_STATUS_v0.8.3.md','RECOVERY_v0.8.3.json','Catatan_Kelanjutan_SLR09_2026-10-19.md','FILE_MANIFEST.json']:
        target=history/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise ValueError('Do not overwrite prior checkpoint history')
        shutil.copy2(ROOT/name,target)
    (ROOT / 'SLR09_STATUS_v0.8.3.md').write_text(report)
    (ROOT / 'CHECKPOINT_v0.8.3.md').write_text(report)
    (ROOT / 'README.md').write_text('# SLR_09 v0.8.3\n\nUji penerimaan FINAL083 selesai. Status In Review: 6/9 pemeriksaan lulus. Recall NON_EVENT 80% dan isi berlebih 6,79% belum memenuhi target; dua kontras simulasi salah.\n\nBaca [hasil penerimaan](SLR09_Hasil_Penerimaan_FINAL083_v0.8.3.md). Acuan final sudah disetujui dan dibekukan. Tidak ada pelatihan atau perubahan kandidat pada tahap penerimaan ini.\n')
    latest_note=BASE/'silar_review_audit_delivery_20261020/Catatan_Kelanjutan_SLR09_2026-10-19.md'
    assert SHA(latest_note)=='6cd6959b84a81184fb1cfbe9caef87bedd675cdd5a6cf00a96be989e2bdcc2cf'
    shutil.copy2(latest_note,ROOT/'historical/Catatan_Kelanjutan_before_FINAL083_result_v0.8.3.md')
    notes = report + '\n\n---\n\n# Riwayat sebelum hasil penerimaan FINAL083\n\n' + latest_note.read_text()
    (ROOT/'Catatan_Kelanjutan_SLR09_2026-10-19.md').write_text(notes)
    recovery=read(ROOT/'RECOVERY_v0.8.3.json')
    recovery.update(status='IN_REVIEW_ACCEPTANCE_FINAL083_REQUIRES_QUALITY_IMPROVEMENT',
        latest_acceptance='evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run',
        latest_completed_notebook='notebooks/28_Uji_Penerimaan_SLR09_v0.8.3_executed.ipynb',
        latest_human_confirmation='evidence/acceptance_v083_confirmed_20261020/submission/explicit_chat_approval.json',
        next_work_queue='evidence/acceptance_v083_confirmed_20261020/next_quality_work_queue.json',
        next_reference_status='FINAL083_50_APPROVED_685_TOKENS_TESTED_NOT_YET_USED_FOR_TUNING',
        next_workbook=None,next_notebook=None,new_acceptance_inference_executed=True,
        acceptance_metric_targets_met=False,checks_passed=6,checks_total=9,
        quality_acceptance_approved=False,card_done=False,production_deployed=False)
    write(ROOT/'RECOVERY_v0.8.3.json',recovery)
    shutil.copy2(final_workbook,ROOT/'acceptance'/final_workbook.name)
    output_excel=BASE/'outputs/89b81e051aff'/final_workbook.name
    output_excel.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(final_workbook,output_excel)
    # Recheck every bound file after metadata/report changes.
    validate(bundle,ROOT)
    source_checkpoint=BASE/'silar_recovered/SLR09_Checkpoint_Pengerjaan_v0.8.3.zip'
    assert SHA(source_checkpoint)=='8fa8b344852da34accc8176702ed41755b28b9ff8b24f3c9f3461b21a7039229'
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=SHA(p))
           for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    manifest=read(history/'FILE_MANIFEST.json')
    manifest.update(files=files,status='IN_REVIEW',new_reference_status=recovery['next_reference_status'],
        new_acceptance_inference_executed=True,acceptance_metric_targets_met=False,
        quality_acceptance_approved=False,card_done=False)
    write(ROOT/'FILE_MANIFEST.json',manifest)
    checkpoint=OUT/'SLR09_Checkpoint_Pengerjaan_v0.8.3.zip'
    with zipfile.ZipFile(checkpoint,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_RECOVERY.md',report)
        for p in sorted(ROOT.rglob('*')):
            if included(p):z.write(p,'models/slr09/'+p.relative_to(ROOT).as_posix())
    # Prove the previous checkpoint's source/evidence survives in place or history.
    preserved=[]
    with zipfile.ZipFile(source_checkpoint) as old,zipfile.ZipFile(checkpoint) as new:
        assert new.testzip() is None
        for name in old.namelist():
            if name.endswith('/'):continue
            data=old.read(name);want=hashlib.sha256(data).hexdigest()
            if name in new.namelist() and hashlib.sha256(new.read(name)).hexdigest()==want:
                destination=name
            elif name.startswith('models/slr09/'):
                destination='models/slr09/historical/before_FINAL083_acceptance_v0.8.3/'+name.removeprefix('models/slr09/')
                assert hashlib.sha256(new.read(destination)).hexdigest()==want,name
            else:
                destination='models/slr09/historical/before_FINAL083_acceptance_v0.8.3/SLR09_STATUS_v0.8.3.md'
                assert hashlib.sha256(new.read(destination)).hexdigest()==want,name
            preserved.append(dict(source=name,sha256=want,destination=destination))
        packed=read(ROOT/'FILE_MANIFEST.json')
        for row in packed['files']:
            assert hashlib.sha256(new.read('models/slr09/'+row['path'])).hexdigest()==row['sha256']
    write(OUT/'checkpoint_preservation_verification.json',dict(status='SUCCEEDED',previous_library_checkpoint_version=2,
          previous_checkpoint_sha256=SHA(source_checkpoint),preserved=preserved))
    proof=OUT/'SLR09_Bukti_Penerimaan_FINAL083_v0.8.3.zip'
    proof_files=[p for p in sorted(WORK.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                 and 'runtime' not in p.relative_to(WORK).parts and p.suffix!='.pyc']
    with zipfile.ZipFile(proof,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        entries=[]
        for p in proof_files:
            name='acceptance_FINAL083_evidence/'+p.relative_to(WORK).as_posix();z.write(p,name)
            entries.append(dict(path=name,bytes=p.stat().st_size,sha256=SHA(p)))
        for p in [ROOT/'notebooks/28_Uji_Penerimaan_SLR09_v0.8.3.ipynb',ROOT/'notebooks/28_Uji_Penerimaan_SLR09_v0.8.3_executed.ipynb',ROOT/'code/quality_fix/execute_notebook_cells_v06.py',Path(__file__)]:
            name=p.relative_to(ROOT).as_posix();z.write(p,name);entries.append(dict(path=name,bytes=p.stat().st_size,sha256=SHA(p)))
        z.writestr('manifest.json',json.dumps(dict(status='ACCEPTANCE_COMPLETED_TARGETS_NOT_MET',files=entries,
                    quality_acceptance_approved=False,card_done=False),ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(proof) as z:
        assert z.testzip() is None
        for row in json.loads(z.read('manifest.json'))['files']:
            assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    for name in ['Catatan_Kelanjutan_SLR09_2026-10-19.md','SLR09_STATUS_v0.8.3.md']:
        shutil.copy2(ROOT/name,OUT/name)
    deliverables=[OUT/report_name,proof,checkpoint,OUT/'Catatan_Kelanjutan_SLR09_2026-10-19.md',OUT/'SLR09_STATUS_v0.8.3.md',output_excel]
    summary=dict(status='SUCCEEDED',acceptance_metric_targets_met=False,source_files_preserved=len(preserved),
                 bound_source_files_verified=21,artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=SHA(p)) for p in deliverables])
    write(OUT/'delivery_verification_FINAL083.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
