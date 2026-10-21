"""Deliver the exact evaluated assets and close training/testing under the user's criterion."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT.parents[2]
OUT=BASE/'silar_handoff_FINAL084_limit006_20261020'
RUN=ROOT/'evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run'
POLICY=ROOT/'evidence/acceptance_FINAL084_target006_20261020'
PREFIX='models/slr09/'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(path.read_text())


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def include(path):
    return (path.is_file() and '__pycache__' not in path.parts
        and path.suffix not in {'.pyc','.safetensors','.bin'}
        and not {'runtime','best_model'} & set(path.relative_to(ROOT).parts)
        and path.name not in {'finalize.stdout.txt','finalize_final084.stdout.txt','handoff006.stdout.txt'})


def main():
    OUT.mkdir(exist_ok=True)
    old=read(RUN/'evaluation.json');new=read(POLICY/'evaluation_under_limit006.json')
    comparison=read(POLICY/'decision_comparison.json');decision=read(POLICY/'user_target_revision.json')
    bundle=read(RUN/'reviewed_bundle_frozen.json')
    assert comparison['revised_checks_passed']==9 and comparison['new_model_inference_executed'] is False
    assert new['quality_acceptance_approved'] and new['quality_acceptance_scope']=='MVP_ASSET_PILOT'
    for key in ['sena','nara','fields']:assert old[key]==new[key]
    for name,want in decision['original_evidence_sha256'].items():assert sha(RUN/name)==want
    for rel,want in bundle['protocol']['binding']['files_sha256'].items():assert sha(ROOT/rel)==want
    locks=read(ROOT/'config/quality_candidate_asset_lock_v0.8.4.json')['models']
    model_paths={
        'sena':BASE/'silar_delivery_v084_20261020'/locks['sena']['archive_name'],
        'nara':BASE/'silar_assets_final083'/locks['nara']['archive_name']}
    for name,path in model_paths.items():assert sha(path)==locks[name]['archive_sha256']
    original_excel=ROOT/'acceptance/Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx'
    assert sha(original_excel)==decision['original_source_workbook_sha256']
    notebook32=read(ROOT/'notebooks/32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb')
    assert notebook32['metadata']['execution_succeeded']

    report=f'''# Keputusan akhir model SENA–NARA FINAL084

Tahap training dan pengujian model ditutup sesuai permintaan pengguna pada 20 Oktober 2026 pukul 22:51:37 WIB. Batas isi berlebih pada field kosong direvisi dari ≤5% menjadi ≤6%. Aset MVP diterima berdasarkan kriteria revisi ini: seluruh 9 pemeriksaan terpenuhi. Tidak ada training, perubahan bobot, perubahan label manusia, atau inferensi baru setelah keputusan pengguna.

## Dampak perubahan batas

| Komponen | Batas awal | Batas revisi |
| --- | ---: | ---: |
| Maksimum isi berlebih | 5% | 6% |
| Hasil model yang sama | 10/174 = 5,75% | 10/174 = 5,75% |
| Field berlebih yang diizinkan pada 174 acuan kosong | 8 | 10 |
| Pemeriksaan terpenuhi | 8/9 | 9/9 |
| Keputusan metrik | Belum memenuhi seluruh target | Memenuhi seluruh target revisi |

Kenaikan batas sebesar satu poin persentase hanya mengubah toleransi dan keputusan penerimaan. Tidak ada peningkatan kinerja yang dapat diklaim dari revisi ini: semua prediksi dan nilai metrik identik. Tidak ada uji signifikansi atau hasil baru yang digunakan untuk mengklaim perbaikan statistik. Keputusan dibuat setelah hasil diketahui dan dicatat sebagai penerimaan pilot dengan kriteria pengguna yang direvisi, bukan uji independen baru.

## Nilai hasil tetap

- SENA: 49/50 narasi benar (98%); macro F1 {new['sena']['macro_f1']:.2%}; recall NON_EVENT 90%; recall keempat kelas kejadian masing-masing 100%.
- NARA: macro F1 seluruh 14 label non-O {new['nara']['macro_f1_all_14_non_o']:.2%}; exact span F1 {new['nara']['exact_span_f1']:.2%}.
- Field nonkosong tepat: 154/176 = 87,50%; isi berlebih pada acuan kosong: 10/174 = 5,75%.
- Kontrak adapter/Fusion serta kontras simulasi/latihan yang ditetapkan protokol tetap terpenuhi. Cutoff confidence tetap 0,95, kategori hanya dari SENA, dan verifikasi manusia selalu wajib.

Hasil penerimaan pertama dengan batas 5% tetap utuh dalam `original_run/evaluation.json`, termasuk status 8/9. Perhitungan keputusan dengan batas 6% memakai prediksi tersimpan yang sama dan disimpan terpisah di `evidence/acceptance_FINAL084_target006_20261020/`. Notebook 32 merekam perhitungan tersebut tanpa memuat model.

## Model yang diserahkan

| Aset | Berkas persis yang digunakan | SHA256 arsip |
| --- | --- | --- |
| SENA v0.8.4 | {locks['sena']['archive_name']} | `{locks['sena']['archive_sha256']}` |
| NARA reviewed pilot | {locks['nara']['archive_name']} | `{locks['nara']['archive_sha256']}` |

NARA yang digunakan adalah bobot reviewed pilot 18 Oktober 2026, bersama adapter 0.5.3, postprocessing 0.3.1, composition 0.3.1 dan victim guard 0.5.0. Seluruh kode tersebut disertakan dalam paket evaluasi. Tanggal model NARA dipertahankan sesuai identitas aslinya. Bobot tidak diganti atau diberi nomor versi baru akibat perubahan batas penerimaan.

## Notebook dan data review

Paket `SLR09_Notebook_dan_Data_Evaluasi_FINAL084_v0.8.4.zip` berisi:

- Notebook 31 sumber dan salinan `_executed`: eksekusi inferensi aktual pada 50 acuan FINAL084, dengan hasil awal 8/9 pada batas 5%.
- Notebook 32 sumber dan salinan `_executed`: keputusan akhir pada batas 6% dari prediksi tersimpan, tanpa training atau inferensi baru.
- Excel review asli `Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx`, 50 APPROVED dan 692 token, SHA256 `{sha(original_excel)}`.
- JSON acuan manusia yang dibekukan, seluruh prediksi JSONL, hasil metrik awal, keputusan revisi, audit review, lock, lingkungan inferensi dan snapshot sumber sebelum model dimuat.
- Evaluator, importer, runtime SENA/NARA, adapter/postprocessing, tokenizer role contract, konfigurasi terkunci dan requirements yang dipakai. Semua 21 file yang terikat pada pengujian disertakan dengan hash identik.

Excel dan acuan pertama tetap mencatat target 5% yang berlaku ketika review dan pengujian pertama dilakukan. Persetujuan batas baru 6% berada pada berkas keputusan terpisah; label acuan dan target lama tidak ditulis ulang.

## Cakupan penyelesaian

Training dan pengujian aset model selesai. Penerimaan mutu berlaku untuk pilot aset MVP dengan kriteria revisi pengguna. Pilot terdiri dari 50 narasi sintetis yang direview manusia; perubahan batas tidak membuktikan peningkatan generalisasi atau kalibrasi confidence. Deployment, target VM/backend submission, dan status Done untuk keseluruhan proyek tidak diklaim oleh serah terima model ini. Konfigurasi yang dibekukan sebelum pengujian mempertahankan metadata historisnya; keputusan penerimaan terkini berada pada berkas revisi dan recovery terkini.
'''
    report_name='SLR09_Keputusan_Akhir_FINAL084_Batas6persen.md'
    (ROOT/report_name).write_text(report);(OUT/report_name).write_text(report)
    notes=ROOT/'Catatan_Kelanjutan_SLR09_2026-10-19.md'
    assert sha(notes)=='10fdd252d567cdd24930e61f78f754effd74b53ef4f979dde9ff1c1b7d185b0f'
    prior_notes=notes.read_text()
    notes.write_text(report+'\n\n---\n\n# Riwayat sebelum keputusan pengguna tentang batas 6%\n\n'+prior_notes)
    shutil.copy2(notes,OUT/notes.name)
    for name in ['SLR09_STATUS_v0.8.4.md','CHECKPOINT_v0.8.4.md']:(ROOT/name).write_text(report)
    shutil.copy2(ROOT/'SLR09_STATUS_v0.8.4.md',OUT/'SLR09_STATUS_v0.8.4.md')
    (ROOT/'README.md').write_text('''# SLR_09 v0.8.4 — serah terima model

Tahap training dan pengujian model selesai sesuai keputusan pengguna. Seluruh 9 pemeriksaan memenuhi batas revisi isi berlebih ≤6%; prediksi tetap 10/174 = 5,75%. Tidak ada model atau label yang diubah setelah revisi. Hasil pertama 8/9 pada batas 5% tetap tersimpan.

Baca [keputusan akhir](SLR09_Keputusan_Akhir_FINAL084_Batas6persen.md) dan [recovery](RECOVERY_v0.8.4.json). Notebook 31 merekam inferensi asli; notebook 32 hanya menghitung keputusan dari keluaran tersimpan. Penerimaan berlaku untuk pilot aset MVP. Verifikasi manusia tetap wajib; deployment dan keseluruhan proyek Done tidak termasuk keputusan ini.
''')
    rec=read(ROOT/'RECOVERY_v0.8.4.json')
    rec.update(status='MODEL_TRAINING_AND_EVALUATION_CLOSED_USER_ACCEPTED_MVP_LIMIT006',
        training_and_testing_phase_closed=True,further_training_requested=False,further_model_testing_requested=False,
        current_target_revision='acceptance/target_revision_FINAL084_limit006.json',
        latest_policy_evaluation='evidence/acceptance_FINAL084_target006_20261020/evaluation_under_limit006.json',
        original_acceptance_result_preserved=True,original_acceptance_metric_targets_met=False,
        original_acceptance_checks_passed=8,original_empty_field_spurious_limit=.05,
        current_empty_field_spurious_limit=.06,acceptance_metric_targets_met=True,checks_passed=9,checks_total=9,
        quality_acceptance_approved=True,quality_acceptance_scope='MVP_ASSET_PILOT',
        quality_acceptance_basis='EXPLICIT_USER_CHAT_TARGET_REVISION_AND_REQUEST_TO_FINISH_TRAINING_TESTING',
        latest_completed_notebook='notebooks/32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb',
        latest_model_inference_notebook='notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb',
        next_work_queue=None,next_workbook=None,next_notebook=None,
        next_reference_status='FINAL084_EVALUATED_ACCEPTED_UNDER_USER_LIMIT006_NO_FURTHER_TRAINING_TESTING',
        standards_lowered=True,standards_revision_explicitly_approved_by_user=True,
        post_result_target_revision=True,new_model_inference_after_target_revision=False,
        new_gradient_training_after_target_revision=False,card_done=False,production_deployed=False,
        current_FINAL084_used_for_tuning=False,current_FINAL084_retired_to_development=False,
        prior_checkpoint_history='historical/before_user_limit006_handoff_v0.8.4')
    write(ROOT/'RECOVERY_v0.8.4.json',rec)

    # A focused reproducibility package, with model archives delivered separately.
    selected={ROOT/rel for rel in bundle['protocol']['binding']['files_sha256']}
    selected.update(ROOT/'notebooks'/name for name in [
        '31_Uji_Penerimaan_SLR09_v0.8.4.ipynb','31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb',
        '32_Keputusan_Akhir_FINAL084_Batas6persen.ipynb','32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb'])
    selected.update([ROOT/'acceptance/review_bundle_draft.json',ROOT/'acceptance/target_revision_FINAL084_limit006.json',
        original_excel,ROOT/'code/acceptance/apply_target_revision_final084.py',
        ROOT/'code/quality_fix/execute_notebook_cells_v06.py',ROOT/report_name])
    for folder in [ROOT/'evidence/acceptance_v084_confirmed_20261020',POLICY]:
        selected.update(p for p in folder.rglob('*') if include(p) and p.name!='checkpoint_preservation.json')
    package_readme='''# Notebook dan data evaluasi FINAL084

Model SENA dan NARA diserahkan sebagai dua ZIP terpisah. Arsip model tidak digabung ulang di paket kecil ini. Nama dan hash model ada di MANIFEST.json serta keputusan akhir.

Semua sumber proyek berada di models/slr09/. Buka notebooks/31_Uji_Penerimaan_SLR09_v0.8.4_executed.ipynb untuk melihat inferensi aktual pertama, dan notebooks/32_Keputusan_Akhir_FINAL084_Batas6persen_executed.ipynb untuk keputusan dari prediksi tersimpan pada batas 6%. Salinan tanpa akhiran _executed adalah sumber notebook yang bersesuaian. Notebook 32 tidak memuat atau melatih model.

Data review asli ada di models/slr09/acceptance/Review_Penerimaan_Akhir_SLR09_v0_8_4.xlsx. JSON acuan persis yang diuji, prediksi per narasi, hasil 8/9 pada batas lama, lock dan workflow ada di models/slr09/evidence/acceptance_v084_confirmed_20261020/acceptance_FINAL084/original_run/. Hasil 9/9 pada batas baru berada di models/slr09/evidence/acceptance_FINAL084_target006_20261020/.

Excel asli tetap menampilkan target lama 5%; batas 6% disetujui setelah hasil pertama diketahui dan dicatat terpisah pada acceptance/target_revision_FINAL084_limit006.json. Semua label manusia, prediksi dan metrik tetap. Konfigurasi dan metadata sebelum inferensi dipertahankan agar 21 file terikat identik dengan pengujian asli.

Untuk membaca hasil tidak perlu menjalankan ulang model. Training dan testing sudah ditutup sesuai permintaan. Jika diperlukan reproduksi teknis terpisah, notebook 31 menggunakan variabel lingkungan SLR09_PACKAGE_ROOT (path absolut models/slr09), SLR09_WORK_DIR (direktori keluaran baru), SLR09_REVIEW_XLSX (Excel di atas), SLR09_SENA_ARCHIVE dan SLR09_NARA_ARCHIVE (kedua ZIP model). Gunakan requirements pada config/requirements-inference.txt dan versi lingkungan yang direkam dalam workflow_result.json. Direktori keluaran baru wajib dipakai agar bukti awal tidak tertimpa. Notebook 31 mereproduksi protokol awal 5%; keputusan 6% dibaca dari notebook 32 yang telah dieksekusi. Notebook 32 juga melindungi direktori hasil yang sudah ada.

Kode normalisasi NARA, adapter, composition, victim guard, runtime, evaluator dan importer disertakan. Bobot NARA saja tidak mencakup seluruh proses field yang dievaluasi; gunakan kode pendamping tersebut untuk mereproduksi proses yang sama.
'''
    kit=OUT/'SLR09_Notebook_dan_Data_Evaluasi_FINAL084_v0.8.4.zip'
    kit_entries=[dict(path=PREFIX+p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(selected)]
    kit_manifest=dict(schema='slr09-final084-evaluation-handoff-0.8.4',files=kit_entries,
        models={name:dict(archive_name=spec['archive_name'],archive_sha256=spec['archive_sha256'],
            model_id=spec['model_id'],weights_sha256=spec['files']['model.safetensors'],archive_embedded=False)
            for name,spec in locks.items()},original_review_sha256=sha(original_excel),
        original_limit=.05,revised_limit=.06,training_and_testing_phase_closed=True,
        new_model_inference_executed=False,quality_acceptance_scope='MVP_ASSET_PILOT')
    with zipfile.ZipFile(kit,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_EVALUASI.md',package_readme)
        for p in sorted(selected):z.write(p,PREFIX+p.relative_to(ROOT).as_posix())
        z.writestr('MANIFEST.json',json.dumps(kit_manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(kit) as z:
        assert z.testzip() is None
        for entry in kit_entries:assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
        for rel,want in bundle['protocol']['binding']['files_sha256'].items():
            assert hashlib.sha256(z.read(PREFIX+rel)).hexdigest()==want
        assert z.read(PREFIX+original_excel.relative_to(ROOT).as_posix())==original_excel.read_bytes()
    write(POLICY/'handoff_package_verification.json',dict(status='SUCCEEDED',archive_name=kit.name,
        files=len(kit_entries),bound_source_files_identical=21,original_notebook31_unchanged=True,
        original_review_unchanged=True,models_separately_verified_against_locked_archives=True,
        new_model_inference_executed=False,new_training_executed=False))

    previous=BASE/'silar_delivery_FINAL084_20261020/SLR09_Checkpoint_Pengerjaan_v0.8.4.zip'
    assert sha(previous)=='ebb55e0d91d8b553fa2c8697c4a8f9b84201f9d18463219fed449db467b938ce'
    history=ROOT/'historical/before_user_limit006_handoff_v0.8.4'
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
    write(POLICY/'checkpoint_preservation.json',dict(status='SUCCEEDED',previous_checkpoint_version=5,
        previous_checkpoint_sha256=sha(previous),preserved=preservation))
    entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(ROOT.rglob('*')) if include(p) and p!=ROOT/'FILE_MANIFEST.json']
    write(ROOT/'FILE_MANIFEST.json',dict(schema='slr09-checkpoint-manifest-0.8.4',revision='0.8.4',files=entries,
        manifest_itself_excluded=True,weights_included=False,status=rec['status'],training_and_testing_phase_closed=True,
        original_acceptance_checks_passed=8,original_limit=.05,revised_acceptance_checks_passed=9,revised_limit=.06,
        quality_acceptance_approved=True,quality_acceptance_scope='MVP_ASSET_PILOT',
        new_gradient_training_executed=False,new_model_inference_after_revision=False,card_done=False,production_deployed=False))
    checkpoint=OUT/'SLR09_Checkpoint_Pengerjaan_v0.8.4.zip'
    with zipfile.ZipFile(checkpoint,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_RECOVERY.md',report)
        for p in sorted(ROOT.rglob('*')):
            if include(p):z.write(p,PREFIX+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(checkpoint) as z:
        assert z.testzip() is None
        for entry in entries:assert hashlib.sha256(z.read(PREFIX+entry['path'])).hexdigest()==entry['sha256']
        for entry in preservation:assert hashlib.sha256(z.read(entry['destination'])).hexdigest()==entry['sha256']
    for name,want in decision['original_evidence_sha256'].items():assert sha(RUN/name)==want
    artifacts=[kit,OUT/report_name,checkpoint,OUT/notes.name,OUT/'SLR09_STATUS_v0.8.4.md']
    result=dict(status='SUCCEEDED',training_and_testing_phase_closed=True,revised_checks_passed=9,checks_total=9,
        original_result_preserved=True,new_training_executed=False,new_model_inference_executed=False,
        prior_checkpoint_files_preserved=len(preservation),portable_package_bound_files_verified=21,
        quality_acceptance_approved=True,quality_acceptance_scope='MVP_ASSET_PILOT',
        existing_model_artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in model_paths.values()],
        artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in artifacts])
    write(OUT/'handoff_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
