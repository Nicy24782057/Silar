"""Package verified development work without promoting it to quality acceptance."""
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
OUT = BASE / 'silar_delivery_v084_20261020'
EV = ROOT / 'evidence/quality_fix_v084'
OLD_RUN = ROOT / 'evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run'
PREFIX = 'models/slr09/'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def included(path):
    return (path.is_file() and '__pycache__' not in path.parts
            and path.suffix not in {'.pyc', '.safetensors', '.bin'}
            and 'runtime' not in path.relative_to(ROOT).parts
            and 'best_model' not in path.relative_to(ROOT).parts
            and path != EV / 'finalize.stdout.txt')


def main():
    OUT.mkdir(exist_ok=True)
    old = read(OLD_RUN / 'evaluation.json')
    new = read(EV / 'export_verification30/evaluation_FINAL083_seen.json')
    joint = read(EV / 'export_verification30/joint_regression_summary.json')
    training = read(EV / 'training29/run_state.json')
    export = read(EV / 'candidate_export.json')
    tests = read(EV / 'active_tests30/active_tests.json')
    wb = read(EV / 'workbook_qa/verification.json')
    identity = read(ROOT / 'data/final_reference_identity_v0.8.4.json')
    bundle = read(ROOT / 'acceptance/review_bundle_draft.json')
    assert joint['all_known_joint_regressions_met'] and not joint['new_acceptance_inference_executed']
    assert tests['all_passed'] and tests['tests_run'] == 91
    assert training['status'] == 'SUCCEEDED' and training['steps_completed'] == 309
    assert wb['all_pending'] and wb['reviewer_blank'] and identity['tokens'] == 692
    assert sha(Path(export['archive'])) == export['archive_sha256']
    sys.path.insert(0, str(ROOT / 'code/acceptance'))
    from evaluate_acceptance import score, digest
    prior_bundle = read(OLD_RUN / 'reviewed_bundle_frozen.json')
    prior_predictions = [json.loads(x) for x in (OLD_RUN / 'predictions.jsonl').read_text().splitlines()]
    assert all(value == old[key] for key, value in score(prior_bundle['records'], prior_predictions, prior_bundle['protocol']).items())
    assert digest(prior_bundle) == read(OLD_RUN / 'evaluation_lock.json')['bundle_sha256']
    assert sha(OLD_RUN / 'predictions.jsonl') == old['predictions_sha256']
    snapshot = OLD_RUN.parent / 'pre_inference_snapshot'
    for relative, expected in prior_bundle['protocol']['binding']['files_sha256'].items():
        assert sha(snapshot / relative) == expected
    assert bundle['protocol']['targets'] == prior_bundle['protocol']['targets']
    assert bundle['protocol']['confidence_threshold'] == .95
    for relative, expected in bundle['protocol']['binding']['files_sha256'].items():
        assert sha(ROOT / relative) == expected
    notes_path = ROOT / 'Catatan_Kelanjutan_SLR09_2026-10-19.md'
    assert sha(notes_path) == 'e066d3b9f0b26f721b5a31d7c401bf893c02199d026b92b5de13b7d731a5730f'
    prior_notes = notes_path.read_text()
    retirement = read(ROOT / 'data/retirement_after_FINAL083_v0.8.4.json')
    assert datetime.fromisoformat(retirement['retired_at']) < datetime.fromisoformat(training['started_at'])
    proposals = read(ROOT / 'data/final_reference_proposals_v0.8.4.json')
    assert datetime.fromisoformat(proposals['created_at']) > datetime.fromisoformat(training['finished_at'])
    fresh_ids = {r['id'] for r in proposals['records']}
    for p in (EV / 'export_verification30').glob('predictions_*.jsonl'):
        assert not fresh_ids & {json.loads(x)['id'] for x in p.read_text().splitlines()}

    write(EV / 'development_disposition.json', dict(
        status='DEVELOPMENT_REGRESSION_VERIFIED_FRESH_HUMAN_REFERENCE_REQUIRED',
        note='The evaluator decision field READY_FOR_HUMAN_ACCEPTANCE is a generic metric result; all four reports explicitly have seen-development scope and do not authorize acceptance.',
        original_FINAL083_result_preserved=True, original_FINAL083_snapshot_files_verified=len(prior_bundle['protocol']['binding']['files_sha256']),
        all_known_joint_regressions_met=True, new_acceptance_inference_executed=False,
        quality_acceptance_approved=False, card_done=False, production_deployed=False))
    decision = dict(schema='slr09-standards-review-0.8.4', created_at=datetime.now(timezone.utc).isoformat(),
        user_question='oke lanjut. dan apakah kita seharusnya menurunkan standar? karena yang namanya model pasti ada bias kan',
        disposition='TARGETS_AND_CUTOFF_UNCHANGED', user_approved_lower_targets=False,
        targets=deepcopy(bundle['protocol']['targets']), confidence_threshold=.95,
        reasoning=[
            'Possible model bias must be measured; observed mistakes alone do not establish systematic bias.',
            'NON_EVENT target 0.90 on ten cases already permits one error; one case changes observed recall by ten percentage points.',
            'Review tolerances against operational error costs and verification burden before a new evaluation, not after seeing a failed result merely to obtain a pass.',
            'Confidence cutoff 0.95 is an operating rule, not a guarantee of 95 percent correctness; no probability calibration has been established.',
            'Known cases used to train or select a candidate remain development evidence; a fresh human-reviewed reference is required.'],
        sources=[
            {'title':'NIST AI RMF 1.0', 'url':'https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf',
             'use':'Risk tolerance depends on application and context; validity limits and deployment conditions must be documented.'},
            {'title':'On Calibration of Modern Neural Networks (Guo et al., 2017)',
             'url':'https://proceedings.mlr.press/v70/guo17a.html',
             'use':'Neural-network confidence may be poorly calibrated; a softmax threshold is distinct from established accuracy.'}])
    write(ROOT / 'data/standards_review_v0.8.4.json', decision)

    metrics = [
        ('SENA macro F1',old['sena']['macro_f1'],new['sena']['macro_f1'],'≥85%'),
        ('Recall NON_EVENT',old['sena']['per_class']['NON_EVENT']['recall'],new['sena']['per_class']['NON_EVENT']['recall'],'≥90%'),
        ('NARA macro F1 seluruh 14 non-O',old['nara']['macro_f1_all_14_non_o'],new['nara']['macro_f1_all_14_non_o'],'≥75%'),
        ('NARA exact span F1',old['nara']['exact_span_f1'],new['nara']['exact_span_f1'],'≥60%'),
        ('Field nonkosong tepat',old['fields']['nonempty_exact'],new['fields']['nonempty_exact'],'≥80%'),
        ('Isi berlebih pada field kosong',old['fields']['empty_spurious_rate'],new['fields']['empty_spurious_rate'],'≤5%')]
    table = '\n'.join(f'| {name} | {before:.2%} | {after:.2%} | {target} |' for name,before,after,target in metrics)
    regressions=[]
    for name in joint['sets']:
        e=read(EV / f'export_verification30/evaluation_{name}.json')
        regressions.append(f'| {name} | {e["sena"]["accuracy"]:.2%} | {e["fields"]["nonempty_exact"]:.2%} | {e["fields"]["empty_spurious_rate"]:.2%} | 9/9 |')
    regression_table='\n'.join(regressions)
    report=f'''# Perbaikan SLR_09 v0.8.4 — 20 Oktober 2026

**Status pekerjaan: In Review. Kandidat pengembangan terverifikasi; penerimaan baru belum dijalankan.** Target mutu dan cutoff 0,95 tetap. FINAL083 sudah dipensiunkan menjadi development/regresi sebelum dipakai memperbaiki model. Hasil penerimaan pertama dan seluruh acuan manusia tetap tersimpan.

## Apakah standar perlu diturunkan?

Rekomendasi saat ini: pertahankan target. Model dapat memiliki bias, tetapi kesalahan pada beberapa contoh belum membuktikan bias sistematis. Kesalahan, bias, dan ketidakpastian sampel perlu diperiksa terpisah. Standar tidak harus 100%; target NON_EVENT kita sudah 90%. Pada hanya 10 contoh NON_EVENT, satu kesalahan masih diperbolehkan dan satu contoh mengubah recall sebesar 10 poin persentase. Hasil pilot ini belum cukup untuk menentukan kinerja populasi.

Toleransi bisa ditinjau bila biaya false event, kejadian yang terlewat, field yang keliru, serta beban verifikasi manusia sudah jelas. Rekomendasi tersebut merupakan penerapan prinsip toleransi risiko yang bergantung pada konteks dalam [NIST AI RMF 1.0](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf). Perubahan target perlu ditetapkan sebelum uji baru, bukan untuk mengubah hasil gagal menjadi lulus. Pertanyaan pengguna belum dianggap sebagai persetujuan menurunkan target.

Cutoff confidence 0,95 berbeda dari target recall 90%. Confidence model belum terkalibrasi sebagai peluang kebenaran; tidak ada klaim bahwa nilai 0,95 menjamin 95% benar. Lihat penelitian primer [Guo dkk. (2017)](https://proceedings.mlr.press/v70/guo17a.html). Tidak ada kalibrasi probabilitas baru yang dipasang pada pekerjaan ini.

## Perubahan yang dijalankan

- SENA dilanjutkan dari arsip v0.8.3 pada 1.733 narasi unik, termasuk 50 acuan FINAL083 yang sudah direview. Satu epoch dengan 309 langkah gradient selesai. Replay memakai 123 contoh sulit dengan enam pengulangan tambahan. Embedding dan encoder lapisan 0–10 tetap beku; hanya lapisan 11, pooler, dan classifier berubah. Pemeriksaan tensor memastikan 20 tensor berubah dan 181 tetap identik.
- NARA tetap memakai bobot yang sama. Adapter 0.5.3 dan postprocessing 0.3.1 menyaring kata pelaporan murni, frasa ketiadaan kejadian, serta penghubung yang berdiri sendiri dari field dampak. Frasa yang memuat kerusakan nyata dan frasa campuran tetap dipertahankan. Role neural mentah tidak diganti oleh aturan ini.
- Arsip SENA hasil ekspor dimuat ulang bersama arsip NARA terkunci. Seluruh 486 teks unik acuan SENA yang sudah dilihat direproduksi dengan label identik dan selisih probabilitas maksimum dalam toleransi 1e-5. Inferensi gabungan aktual dijalankan pada empat set lama, total 200 narasi.

## Perbandingan pada FINAL083 yang kini sudah dilihat

Kolom v0.8.3 adalah hasil penerimaan pertama. Kolom v0.8.4 adalah regresi setelah set ini dipakai dalam pengembangan; ini bukan perbandingan pada acuan baru yang independen.

| Metrik | v0.8.3, penerimaan pertama | v0.8.4, development | Target tetap |
| --- | ---: | ---: | ---: |
{table}

Kategori benar meningkat dari 48/50 menjadi 50/50 pada set yang sudah dilihat. Dua contoh peragaan gempa dan banjir tiruan dalam latihan kini NON_EVENT. Recall empat kelas kejadian tetap 100%. Ketepatan field nonkosong meningkat dari 158/188 menjadi 159/188; field kosong yang terisi berlebih turun dari 11/162 menjadi 7/162. Tujuh kesalahan field kosong masih tersimpan dalam evidence dan tidak dihapus dari pelaporan.

Kontras latihan/simulasi dengan kejadian sungguhan yang sebelumnya memiliki dua kesalahan kini terpenuhi pada set tersebut. Kontrak adapter/Fusion tidak menghasilkan kesalahan. Seluruh sembilan pemeriksaan terpenuhi pada empat set regresi berikut.

| Acuan pengembangan | Kategori benar | Field nonkosong tepat | Isi berlebih | Pemeriksaan |
| --- | ---: | ---: | ---: | ---: |
{regression_table}

Hasil pengembangan tersebut tidak memberi persetujuan mutu atau membuktikan generalisasi. Field `decision` generik dari scorer pada berkas regresi harus dibaca bersama `scope=KNOWN_SEEN_TRAINING_REGRESSION_NOT_ACCEPTANCE`; disposisi proyek tetap menunggu acuan baru.

## Acuan baru dan aturan Excel

`Review_Penerimaan_Akhir_SLR09_v0.8.4.xlsx` memuat FINAL084: 50 narasi sintetis baru, 10 per kategori, 692 token dan seluruh 14 role non-O. Semuanya PENDING, nama reviewer kosong, dan model belum memprediksi acuan ini. Usulan disusun setelah pelatihan selesai. Tidak ditemukan exact overlap ternormalisasi dengan 2.991 teks sumber tersedia; independensi semantik dan representativitas lapangan tidak diklaim.

Isi reviewer pada Mulai!B5. Periksa kategori dan seluruh field pada Narasi serta semua label pada Token. APPROVED berarti seluruh acuan pada ID tersebut sudah diperiksa; DEFERRED membutuhkan alasan. Gunakan `|` untuk beberapa item array. Nilai yang tidak didukung teks tetap kosong; waktu relatif tetap literal dan occurred_at tetap null. ID, narasi, posisi serta teks token dipertahankan. Pedoman lengkap berada di `acceptance/README.md`.

Workbook sudah dirender dan diperiksa pada ketiga tab. Seluruh nilai cocok dengan usulan, 24 rumus diperiksa tanpa error, tabel/dropdown/freeze panes terverifikasi, dan batas kelengkapan APPROVED/DEFERRED/token kosong diuji dengan fixture yang dipulihkan. Importer memblokir reviewer kosong maupun acuan PENDING. Fixture tidak disimpan sebagai review manusia.

Notebook 29 dan 30 benar-benar dieksekusi melalui CPython cell executor dan salinan `_executed` menyimpan hasil. Notebook 31 untuk penerimaan FINAL084 tersedia tetapi belum dieksekusi. Tahap penerimaan akan memvalidasi review/binding dan membekukan sumber sebelum memuat model. Pengguna tidak perlu melatih model di laptop.

## Identitas dan batas pekerjaan

- SENA: `{export['model_id']}`; SHA256 arsip `{export['archive_sha256']}`.
- NARA tetap `SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip`, SHA256 `bce9feba0dd2ae4518880708085f44286ae8d1dd7e50f4eb452e36824f967798`.
- Konfigurasi aktif `config/SLR09_Konfigurasi_Integrasi_v0.9.json`, lock `config/quality_candidate_asset_lock_v0.8.4.json`.
- 91 uji kontrak aktif lulus, tanpa failure, error, atau skip. Inferensi aktual memakai CPU representatif, bukan bukti target VM/backend submission.
- Kategori hanya dari SENA; NON_EVENT memblokir submission; human verification selalu wajib. Field kosong tidak menambah ketidakpastian dengan sendirinya. Persetujuan mutu, Done dan deployment tetap false.

Checkpoint memuat sumber, notebook, Excel, bukti pelatihan/regresi, acuan manusia lama serta hasil penerimaan pertama. Bobot neural berada pada arsip model terpisah. Langkah berikutnya adalah review manusia atas FINAL084 dan pengujian penerimaan pada kandidat yang sudah diikat, dengan target yang sama.
'''
    report_name='SLR09_STATUS_v0.8.4.md'
    (ROOT/report_name).write_text(report)
    (ROOT/'CHECKPOINT_v0.8.4.md').write_text(report)
    (OUT/report_name).write_text(report)
    (ROOT/'README.md').write_text('''# SLR_09 v0.8.4

Status In Review. Pelatihan lanjutan SENA dan perbaikan presisi field NARA selesai. Inferensi gabungan pada 200 narasi pengembangan memenuhi semua pemeriksaan; 91 uji kontrak lulus. Target dan cutoff 0,95 tetap.

Baca [status terkini](SLR09_STATUS_v0.8.4.md) dan [recovery](RECOVERY_v0.8.4.json). FINAL083 sudah menjadi development; hasil penerimaan pertamanya tetap tersimpan. FINAL084 berisi 50 narasi dan 692 token, semuanya PENDING dan belum diprediksi model. Notebook 31 menunggu acuan manusia. Persetujuan mutu, Done dan deployment tetap false.
''')
    notes=report+'\n\n---\n\n# Riwayat sampai hasil penerimaan FINAL083\n\n'+prior_notes
    notes_path.write_text(notes)
    shutil.copy2(notes_path,OUT/notes_path.name)
    recovery=read(ROOT/'RECOVERY_v0.8.3.json')
    current_lock=read(ROOT/'config/quality_candidate_asset_lock_v0.8.4.json')
    recovery.update(schema='slr09-final-context-recovery-0.8.4',
        status='IN_REVIEW_DEVELOPMENT_V084_VERIFIED_FINAL084_REVIEW_PENDING',
        latest_training='evidence/quality_fix_v084/training29',
        latest_joint_verification='evidence/quality_fix_v084/export_verification30',
        integration_configuration='config/SLR09_Konfigurasi_Integrasi_v0.9.json',
        candidate_lock='config/quality_candidate_asset_lock_v0.8.4.json',
        model_archives={name:dict(archive_name=spec['archive_name'],archive_sha256=spec['archive_sha256'],
            weights_sha256=spec['files']['model.safetensors']) for name,spec in current_lock['models'].items()},
        prior_checkpoint_history='historical/before_development_v0.8.4_checkpoint',
        pipeline_revision='0.8.4',active_configuration='config/SLR09_Konfigurasi_Integrasi_v0.9.json',
        active_candidate_lock='config/quality_candidate_asset_lock_v0.8.4.json',
        latest_completed_notebook='notebooks/30_Verifikasi_Ekspor_SLR09_v0.8.4_executed.ipynb',
        latest_training_notebook='notebooks/29_Penguatan_NON_EVENT_SENA_v0.8.4_executed.ipynb',
        latest_regression='evidence/quality_fix_v084/export_verification30',
        next_work_queue='acceptance/README.md',next_reference_status='FINAL084_50_PENDING_692_TOKENS_NO_INFERENCE',
        next_workbook='acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.4.xlsx',
        next_notebook='notebooks/31_Uji_Penerimaan_SLR09_v0.8.4.ipynb',
        prior_acceptance_preserved=True,prior_FINAL083_retired_to_development=True,
        new_acceptance_inference_executed=False,acceptance_metric_targets_met=False,
        checks_passed=None,checks_total=9,known_regression_sets_passed=4,known_regression_records=200,
        standards_lowered=False,confidence_threshold=.95,quality_acceptance_approved=False,
        card_done=False,production_deployed=False,sena_model_archive=export['archive'].split('/')[-1],
        sena_model_archive_sha256=export['archive_sha256'])
    write(ROOT/'RECOVERY_v0.8.4.json',recovery)

    # Preserve every byte of the prior durable checkpoint, in place or history.
    previous=BASE/'silar_delivery_FINAL083_20261020/SLR09_Checkpoint_Pengerjaan_v0.8.3.zip'
    assert sha(previous)=='a596e3db954d475a59ed4895628100692135e17f32399aaee043f6573b6b2462'
    history=ROOT/'historical/before_development_v0.8.4_checkpoint'
    preservation=[]
    with zipfile.ZipFile(previous) as oldzip:
        for name in oldzip.namelist():
            if name.endswith('/'):continue
            assert '..' not in Path(name).parts
            data=oldzip.read(name);want=hashlib.sha256(data).hexdigest()
            rel=name.removeprefix(PREFIX) if name.startswith(PREFIX) else '_archive_root/'+name
            current=ROOT/rel
            if name.startswith(PREFIX) and rel!='FILE_MANIFEST.json' and current.is_file() and sha(current)==want:
                destination=name
            else:
                target=history/rel;target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert target.read_bytes()==data
                else:target.write_bytes(data)
                destination=PREFIX+target.relative_to(ROOT).as_posix()
            preservation.append(dict(source=name,sha256=want,destination=destination))
    write(EV/'checkpoint_preservation.json',dict(status='SUCCEEDED',previous_library_checkpoint_version=3,
        previous_checkpoint_sha256=sha(previous),preserved=preservation))
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    manifest=read(ROOT/'FILE_MANIFEST.json')
    manifest.update(schema='slr09-checkpoint-manifest-0.8.4',revision='0.8.4',files=files,status='IN_REVIEW',pipeline_revision='0.8.4',
        new_reference_status=recovery['next_reference_status'],new_acceptance_inference_executed=False,
        acceptance_metric_targets_met=False,known_joint_regressions_met=True,quality_acceptance_approved=False,card_done=False)
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
    deliverables=[Path(export['archive']),BASE/'outputs/89b81e051aff/Review_Penerimaan_Akhir_SLR09_v0.8.4.xlsx',
                  OUT/report_name,checkpoint,OUT/notes_path.name]
    result=dict(status='SUCCEEDED',previous_checkpoint_files_preserved=len(preservation),
        original_acceptance_snapshot_files_verified=21,records_in_known_joint_regression=200,
        known_joint_regressions_met=True,active_contract_tests=91,fresh_records=50,fresh_tokens=692,
        new_acceptance_inference_executed=False,quality_acceptance_approved=False,card_done=False,
        artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in deliverables])
    write(OUT/'delivery_verification_v084.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
