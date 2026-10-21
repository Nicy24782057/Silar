"""Package actual FINAL082 results without modifying the frozen candidate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def included(path, root):
    return path.is_file() and '__pycache__' not in path.relative_to(root).parts and path.suffix not in {'.pyc', '.bin', '.safetensors'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'base', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    root, base, out = args.root.resolve(), args.base.resolve(), args.output.resolve()
    evidence = root / 'evidence/acceptance_v082/original_run/evidence'
    report = json.loads((evidence / 'evaluation.json').read_text())
    summary = json.loads((root / 'evidence/acceptance_v082/result_summary.json').read_text())
    assert summary['numeric_targets_met'] and not summary['all_required_checks_met']
    sys.path.insert(0, str(root / 'code/acceptance'))
    from evaluate_acceptance import validate, score, digest
    from import_review_xlsx import read_cells
    bundle = json.loads((evidence / 'reviewed_bundle_frozen.json').read_text())
    rows, _ = validate(bundle, root)
    predictions = [json.loads(line) for line in (evidence / 'predictions.jsonl').read_text().splitlines()]
    recomputed = score(rows, predictions, bundle['protocol'])
    for key in recomputed:
        assert recomputed[key] == report[key], key
    assert digest(bundle) == report['frozen_bundle_sha256']
    notebook = json.loads((root / 'notebooks/25_Uji_Penerimaan_SLR09_v0.8.2_executed.ipynb').read_text())
    assert notebook['metadata']['execution_succeeded']
    original_nb = json.loads((root / 'evidence/acceptance_v082/submission/25_original_pending_template.ipynb').read_text())
    current_nb = json.loads((root / 'notebooks/25_Uji_Penerimaan_SLR09_v0.8.2.ipynb').read_text())
    assert [c['source'] for c in original_nb['cells'] if c['cell_type'] == 'code'] == [c['source'] for c in current_nb['cells'] if c['cell_type'] == 'code']
    name = 'SLR09_Hasil_Penerimaan_FINAL082_v0.8.2'
    cells = read_cells(out / (name + '.xlsx'))
    assert float(cells['Hasil']['B22'][0]) == 170 and float(cells['Hasil']['C22'][0]) == 193
    assert float(cells['Hasil']['B23'][0]) == 7 and float(cells['Hasil']['C23'][0]) == 157
    assert [cells['Hasil'][f'E{i}'][0] for i in range(8, 17)] == ['Lulus'] * 8 + ['Belum']
    assert 'IN REVIEW' in cells['Hasil']['A4'][0]
    for i, (row, pred) in enumerate(zip(rows, predictions), 6):
        assert cells['Narasi'][f'A{i}'][0] == row['id']
        assert cells['Narasi'][f'B{i}'][0] == row['text']
        assert cells['Narasi'][f'C{i}'][0] == row['gold_label']
        assert cells['Narasi'][f'D{i}'][0] == pred['event_classifier']['label']
        assert cells['Narasi'][f'I{i}'][0] == row['review']['note']
    with zipfile.ZipFile(out / (name + '.xlsx')) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')]) == 5
    result = root / 'results/final_acceptance_v082'
    result.mkdir(parents=True, exist_ok=True)
    for file in out.glob(name + '*'):
        shutil.copy2(file, result / file.name)
    history = root / 'historical'
    history.mkdir(exist_ok=True)
    for relative in ['SLR09_STATUS_v0.8.2.md', 'CHECKPOINT_v0.8.2.md', 'RECOVERY_v0.8.2.json',
                     'Catatan_Kelanjutan_SLR09_2026-10-19.md', 'README.md', 'FILE_MANIFEST.json']:
        previous = history / (Path(relative).stem + '_before_FINAL082' + Path(relative).suffix)
        if not previous.exists():
            shutil.copy2(base / relative, previous)
    pct = lambda x: f'{x*100:.2f}%'.replace('.', ',')
    text = f'''# SLR_09 — hasil penerimaan FINAL082 v0.8.2

**Status: In Review. Semua tujuh target angka lulus; delapan dari sembilan
pemeriksaan wajib lulus.** Notebook25 sudah benar-benar menginferensikan
50/50 narasi dan671 token setelah review bintang. Workflow SUCCEEDED,
19 Oktober2026 pukul19:45:30–19:45:54 WIB. Tidak ada pelatihan, perubahan bobot,
penyesuaian cutoff, perubahan kandidat, atau perubahan acuan setelah review.

| Penilaian | Hasil FINAL082 baru | Target | Status |
| --- | ---: | ---: | --- |
| SENA macro F1 | {pct(report['sena']['macro_f1'])} | ≥85% | Lulus |
| Recall NON_EVENT | 9/10=90% | ≥90% | Lulus |
| Recall setiap kelas kejadian | masing-masing10/10=100% | ≥80% | Lulus |
| NARA macro F1 semua14 role non-O | {pct(report['nara']['macro_f1_all_14_non_o'])} | ≥75% | Lulus |
| NARA exact span F1 | {pct(report['nara']['exact_span_f1'])} | ≥60% | Lulus |
| Field nonkosong tepat | 170/193={pct(report['fields']['nonempty_exact'])} | ≥80% | Lulus |
| Isi berlebih pada field kosong | 7/157={pct(report['fields']['empty_spurious_rate'])} | ≤5% | Lulus |
| Kontrak adapter | Benar | Wajib benar | Lulus |
| Kontras simulasi/latihan/kejadian nyata | 5/6 benar | Semua benar | Belum |

## Satu hal yang menahan penerimaan

ID `FINAL082-NON_EVENT-02`: “Kecelakaan dalam latihan di Balai Suryalaya sore
ini memakai mobil properti, tanpa kejadian sungguhan.” Acuan bintang NON_EVENT,
prediksi SENA ACCIDENT, confidence0,9289269447. Cutoff0,95 sudah menandainya
sebagai confidence rendah. Flag tersebut tidak mengubah prediksi menjadi
NON_EVENT dan tidak menggantikan syarat seluruh kontras benar. Tidak ada
kesalahan SENA dengan confidence≥0,95. SENA benar49/50; empat contoh kejadian
nyata saat latihan dan satu simulasi benar. Kontrak adapter lulus.

Semua ambang angka memang terpenuhi. `metric_targets_met:false` pada laporan
evaluator asli mencakup kesembilan pemeriksaan, termasuk kontras nonnumerik.
Ringkasan tambahan mencatat `numeric_targets_met:true` secara terpisah tanpa
menulis ulang laporan asli. Keputusan asli `REQUIRES_QUALITY_IMPROVEMENT`.
SLR_09 belum memenuhi seluruh protokol; tidak ada penetapan Done otomatis.

## Mengapa uji ini diperlukan

Regresi177/207=85,51% sebelumnya memakai50 acuan FINAL081 yang sudah digunakan
untuk memperbaiki kode. Putaran FINAL082 memeriksa kandidat yang tetap pada
50 narasi baru setelah acuan direview dan dibekukan. Hasil baru170/193=88,08%
memiliki denominator dan narasi berbeda, sehingga bukan peningkatan berpasangan
terhadap85,51%. Inferensi tidak mengubah bobot; menggunakan hasil untuk tuning
kemudian melaporkannya sebagai uji baru akan menghilangkan fungsi penerimaan.

Putaran ini selesai sekali, tanpa inferensi ulang atau tuning dari hasilnya.
Tidak dibuat kit review tambahan pada tahap pelaporan ini. Jika hasil ini kelak
dipakai memperbaiki kandidat, acuan yang telah terlihat harus dinyatakan sebagai
development/regresi dan penerimaan berikutnya memakai acuan baru sesuai protokol.
Jangan menurunkan target atau mengganti label untuk menutup satu kegagalan.

## Bukti dan batas hasil

Review bintang50 APPROVED,10 tiap kelas, seluruh14 role non-O tercakup.
Excel asli SHA256 `{summary['review_sha256']}`.
Nilai kategori, field, token dan catatan reviewer dipertahankan. Ada24 edit sel
Token dan107 edit sel Narasi dibanding kit awal; perubahan status/format input
termasuk dalam hitungan sel. Reviewer/timestamp impor dicatat tanpa mengklaim
waktu edit Excel. Snapshot sumber yang terikat benar-benar disalin sebelum NN
dimuat. Prediksi dan gold tetap beku. Evaluasi lengkap disimpan bersamastdout.

Masih ada30 perbedaan field:23 field nonkosong tidak tepat dan7 field kosong
terisi;74 dari671 label token berbeda. Seluruhnya ditampilkan di Excel. Model
tidak wajib sempurna untuk lulus ambang agregat, tetapi kontras wajib tetap
berlaku. Pilot sintetis kecil tidak membuktikan ketepatan populasi laporan
lapangan, kalibrasi probabilitas, backend submission, atau targetVM.

Notebook `25_Uji_Penerimaan_SLR09_v0.8.2.ipynb` dan `_executed.ipynb` tersedia.
Eksekusi aktual memakai CPython cell executor, bukan kernel Jupyter asli.
Riwayat notebook23, koreksi scoring CLI, notebook24/24b dan80+23 tes tetap
dipertahankan. Tidak ada perubahan kode kandidat yang memerlukan pengulangan
suite tersebut pada tahap pelaporan ini. Rangkuman workbook dibuat dengan
formula yang dihitung ulang dan diverifikasi terhadap prediksi beku.

## Pemetaan push

Tambahan dibanding paketv0.8.2 sebelumnya adalah notebook25 besertaeksekusi,
review FINAL082 yang dikembalikan, snapshot sebelum inferensi, acuan/prediksi/
laporan asli, Excel hasil, status dan catatan kelanjutan. Skrip pengumpulan,
pembuatan laporan dan packaging disertakan agar bukti dapat ditelusuri.

**Bobot SENA/NARA serta kode kandidat/config tidak berubah.** Tetap gunakan
`SILAR_SENA_context_guard_v0.8.1_20261019.zip` dan
`SILAR_NARA_reviewed_pilot_20261018T001122_607337Z.zip`; tidak perlu reupload.
Paket `SLR09_Bukti_Penerimaan_v0.8.2.zip` adalah tambahan terhadap checkpoint
v0.8.2 yang terakhir diserahkan, bukan gabungan terhadap ZIP GitHub pengguna.
Jangan push ulang seluruh repository. Pemetaan final terhadap ZIP repository
sebelumnya masih menunggu file tersebut. Dua commit tracking SLR_08 dan suffix
nama lokal(3) tetap dikecualikan dari audit. Belum ada remote push/deployment.

`asset_manifest.json` serta `review_bundle_draft.json` dipertahankan sebagai
binding kandidat sebelum uji. Status terbaru dan keputusan putaran ini berada
di `acceptance/quality_assessment_FINAL082_v0.8.2.json` dan dokumen ini;
laporan v0.8.2 sebelum FINAL082 tetap menjadi riwayat.
'''
    (root / 'SLR09_STATUS_v0.8.2.md').write_text(text)
    (out / 'SLR09_Status_Terbaru_v0.8.2.md').write_text(text)
    previous_history = (history / 'Catatan_Kelanjutan_SLR09_2026-10-19_before_FINAL082.md').read_text()
    cumulative = text + '\n\n---\n\n# Riwayat sebelum penerimaan FINAL082\n\n' + previous_history
    for path in [root / 'Catatan_Kelanjutan_SLR09_2026-10-19.md', out / 'Catatan_Kelanjutan_SLR09_2026-10-19.md']:
        path.write_text(cumulative)
    (root / 'README.md').write_text('# Hasil terbaru SLR_09: FINAL082\n\nSemua tujuh target angka lulus; kontras latihan5/6, sehingga8/9 pemeriksaan. '
        'Status tetap In Review. Baca `SLR09_STATUS_v0.8.2.md`, '
        '`acceptance/quality_assessment_FINAL082_v0.8.2.json`, dan '
        '`results/final_acceptance_v082/SLR09_Hasil_Penerimaan_FINAL082_v0.8.2.xlsx`. '
        'Notebook25 sudah dieksekusi pada50 acuan bintang; kedua bobot dan kode kandidat tetap.\n\n'
        + (history / 'README_before_FINAL082.md').read_text())
    recovery = json.loads((history / 'RECOVERY_v0.8.2_before_FINAL082.json').read_text())
    recovery.update(status='COMPLETE_FINAL082_ACTUAL_EVALUATION_CONTRAST_FAILURE',new_reference_status='HUMAN_APPROVED_50_EVALUATED_ONCE',
        new_reference_neural_inference_executed=True,neural_inference_executed_v082=True,
        numeric_targets_passed=7,required_checks_passed=8,required_checks_total=9,
        final082_nonempty_correct=170,final082_nonempty_denominator=193,
        latest_assessment='acceptance/quality_assessment_FINAL082_v0.8.2.json')
    write(root / 'RECOVERY_v0.8.2.json', recovery)
    (root / 'CHECKPOINT_v0.8.2.md').write_text('# Checkpoint setelah uji FINAL082\n\n'
        'Notebook25 selesai dan sumber, gold serta prediksi dibekukan. '
        '7 target angka dan kontrak lulus; kontras latihan5/6 gagal. '
        'SLR_09 In Review; belum Done. Bobot, cutoff dan kode kandidat tetap. '
        'Tidak ada pelatihan, push, atau deployment. Tidak ada notebook yang sedang berjalan. '
        'Lihat SLR09_STATUS_v0.8.2.md dan assessmentFINAL082. '
        'Jika memperbaiki kandidat memakai kegagalan ini, tandai acuan seen/development; '
        'jangan mengulangnya sebagai penerimaan baru.\n')
    (root / 'evidence/acceptance_v082/README.md').write_text('# Bukti aktual FINAL082\n\n'
        'submission/ berisi Excel bintang asli, identitas dan diff; pre_inference_snapshot/ '
        'disalin sebelum NN dimuat. original_run/ berisi inferensi lengkap50/50 dan '
        'keputusan asli:7 target angka terpenuhi, satu kontras gagal. Tidak ada rescore, '
        'penggantian gold, tuning, atau inferensi ulang pada putaran ini. Runtime bobot '
        'tidak disertakan; kedua arsip model lama tetap identik.\n')
    checks = {'status':'SUCCEEDED','original_evaluation_recomputed_from_frozen_predictions_matches':True,
        'candidate_binding_still_matches':True,'notebook25_actual_execution_succeeded':True,
        'notebook_code_cells_unchanged':True,'spreadsheet_counts_and_states_verified':True,
        'all_50_texts_gold_predictions_and_review_notes_preserved':True,
        'xlsx_crc_and_5_native_tables_verified':True,'numeric_targets_met':True,
        'all_required_checks_met':False,'quality_acceptance_approved':False,'card_done':False}
    write(root / 'evidence/acceptance_v082/artifact_verification.json', checks)
    files = [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
             for p in sorted(root.rglob('*')) if included(p, root) and p != root / 'FILE_MANIFEST.json']
    write(root / 'FILE_MANIFEST.json',{'schema':'slr09-source-evidence-files-final082-0.8.2','revision':'0.8.2',
        'manifest_itself_excluded':True,'status':'IN_REVIEW','weights_included':False,
        'numeric_targets_met':True,'all_required_checks_met':False,'quality_acceptance_approved':False,
        'card_done':False,'remote_push_executed':False,'files':files})
    changed=[]
    for path in sorted(root.rglob('*')):
        if not included(path,root):continue
        relative=path.relative_to(root);old=base/relative
        if old.is_file() and sha(old)==sha(path):continue
        changed.append({'path':'models/slr09/'+relative.as_posix(),'status':'MODIFIED' if old.is_file() else 'NEW',
            'expected_previous_sha256':sha(old) if old.is_file() else None,'sha256':sha(path),'bytes':path.stat().st_size})
    overlay=out/'SLR09_Bukti_Penerimaan_v0.8.2.zip'
    if overlay.exists():raise ValueError('Preserve the earlier delivered overlay')
    manifest={'schema':'slr09-final082-evidence-overlay-1','basis':'PREVIOUS_DELIVERED_V082_NOT_USER_GITHUB_ZIP',
        'basis_checkpoint_sha256':'427ae75535e09d6a050cb6f0a5d0d3c9be4cf52d4f1e227dd3097750cbe5ddda',
        'status':'IN_REVIEW','numeric_targets_met':True,'all_required_checks_met':False,
        'weights_included':False,'candidate_code_config_and_model_weights_unchanged':True,
        'quality_acceptance_approved':False,'card_done':False,'remote_push_executed':False,'deletions':[],
        'audit_exclusions':['TWO_SLR08_TRACKING_COMMITS','LOCAL_FILENAME_SUFFIX_(3)'],'files':changed}
    guide='# Tambahan hasil penerimaan FINAL082\n\n7 target angka dan kontrak lulus; kontras latihan5/6 gagal. SLR_09 In Review. '
    guide+='Baca models/slr09/SLR09_STATUS_v0.8.2.md. Ini tambahan terhadap paketv0.8.2 terakhir, bukan ZIP GitHub pengguna. '
    guide+='Bobot SENA/NARA dan kode kandidat tetap; tidak perlu push ulang seluruh repo atau reupload bobot. '
    guide+='Bukti asli dan notebook25 aktual disertakan. Tidak ada push/deployment.\n'
    with zipfile.ZipFile(overlay,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_OVERLAY.md',guide)
        z.writestr('manifest_FINAL082_v0.8.2.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for item in changed:z.write(root/Path(item['path']).relative_to('models/slr09'),item['path'])
    checkpoint=out/'SLR09_Checkpoint_Pengerjaan_v0.8.2.zip'
    with zipfile.ZipFile(checkpoint,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_RECOVERY.md',guide+'\nSnapshot sumber lengkap tanpa bobot.\n')
        for path in sorted(root.rglob('*')):
            if included(path,root):z.write(path,'models/slr09/'+path.relative_to(root).as_posix())
    for archive in [overlay,checkpoint]:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert not any(n.endswith(('.bin','.safetensors','.pyc')) or '/__pycache__/' in n for n in z.namelist())
    with zipfile.ZipFile(overlay) as z:
        for item in changed:
            assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    result={'status':'SUCCEEDED','files':len(changed),'counts':dict(Counter(x['status'] for x in changed)),
        'overlay':{'path':str(overlay),'bytes':overlay.stat().st_size,'sha256':sha(overlay)},
        'checkpoint':{'path':str(checkpoint),'bytes':checkpoint.stat().st_size,'sha256':sha(checkpoint)},
        'candidate_unchanged':True,'numeric_targets_met':True,'all_required_checks_met':False}
    write(overlay.with_suffix('.verification.json'),result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
