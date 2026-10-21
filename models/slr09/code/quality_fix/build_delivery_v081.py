"""Prepare source/evidence delivery against delivered v0.5; no git or remote actions."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import zipfile

from train_sena_cpu import sha,write

ROOT=Path(__file__).resolve().parents[2]


def included(p):
    rel=p.relative_to(ROOT)
    return p.is_file() and '__pycache__' not in rel.parts and p.suffix not in {'.pyc','.safetensors','.bin'}


def build(base,artifacts,output,checkpoint,workspace):
    result=ROOT/'results/quality_fix_v081';result.mkdir(parents=True,exist_ok=True)
    for name in ['SLR09_Hasil_Perbaikan_v0.8.1.xlsx','report_data.json',
                 'report_workbook_verification.json','acceptance_workbook_verification.json',
                 'SLR09_Hasil_Perbaikan_v0.8.1_formula_scan.ndjson',
                 'Review_Penerimaan_Akhir_SLR09_v0.8.1_formula_scan.ndjson']:
        shutil.copy2(artifacts/name,result/name)
    previews=result/'previews';previews.mkdir(exist_ok=True)
    for p in artifacts.glob('*.png'):
        if not p.name.startswith('source_'):shutil.copy2(p,previews/p.name)
    shutil.copy2(artifacts/'Review_Penerimaan_Akhir_SLR09_v0.8.1.xlsx',ROOT/'acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.1.xlsx')
    log=workspace/'acceptance_tests_v081.txt'
    text=log.read_text();assert 'Ran 20 tests' in text and text.strip().endswith('OK')
    shutil.copy2(log,ROOT/'evidence/quality_fix_v081/acceptance_tests.txt')
    write(ROOT/'evidence/quality_fix_v081/acceptance_tests.json',{
        'tests_run':20,'all_passed':True,'scope':'UNIT_FIXTURES_NOT_ACTUAL_ACCEPTANCE_INFERENCE',
        'saved_human_approvals_created':False,'new_final_reference_inferred':False})
    # Preserve the original manifest rather than silently discarding its history.
    history=ROOT/'historical/FILE_MANIFEST_v0.4.1.json'
    if not history.exists():shutil.copy2(ROOT/'FILE_MANIFEST.json',history)
    items=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
           for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    write(ROOT/'FILE_MANIFEST.json',{'schema':'slr09-source-evidence-files-0.8.1','revision':'0.8.1',
        'manifest_itself_excluded':True,'status':'IN_REVIEW','weights_included':False,
        'training21_executed':True,'development_guard22b_executed_without_new_gradients':True,
        'new_acceptance_reference_inferred':False,'quality_acceptance_approved':False,'card_done':False,
        'remote_push_executed':False,'files':items})
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if not included(p):continue
        rel=p.relative_to(ROOT);old=base/rel
        if old.is_file() and sha(old)==sha(p):continue
        if p.suffix=='.zip':raise ValueError('Changed archive must be separate: '+str(rel))
        files.append({'path':'models/slr09/'+rel.as_posix(),'status':'MODIFIED' if old.is_file() else 'NEW',
            'expected_previous_sha256':sha(old) if old.is_file() else None,'sha256':sha(p),'bytes':p.stat().st_size})
    manifest={'schema':'slr09-source-evidence-overlay-0.8.1',
        'basis':'PREVIOUS_DELIVERED_V05_OVER_V041_NOT_USER_GITHUB_ZIP','status':'IN_REVIEW',
        'quality_acceptance_approved':False,'card_done':False,'remote_push_executed':False,
        'production_deployed':False,'weights_included':False,'deletions':[],
        'old_history_preserved':True,'new_reference_status':'50_PENDING_NOT_INFERRED',
        'audit_exclusions':['TWO_SLR08_TRACKING_COMMITS','LOCAL_FILENAME_SUFFIX_(3)'],
        'files':files}
    guide='''# Paket perubahan SLR_09 v0.8.1

Mulai dari models/slr09/SLR09_STATUS_v0.8.1.md. Excel hasil dan rekap notebook
ada di models/slr09/results/quality_fix_v081/. Formulir review baru ada pada
models/slr09/acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.1.xlsx.

Training, penyesuaian bias development, pemuatan kedua arsip, dan verifikasi
aktual selesai melalui notebook20,21,22,22b. Sel Python dijalankan via CPython
cell executor; bukan klaim eksekusi kernel Jupyter asli. Notebook23 belum
dijalankan karena50 acuan baru masih memerlukan review manusia. Persetujuan39
development lama tidak mengesahkan50 acuan baru. Status tetap In Review.

Manifest overlay berisi file baru/berubah terhadap paket v0.5 terdahulu serta
hash basis tiap file. ZIP repository pengguna belum dibandingkan. Jangan
menimpa seluruh repository; cocokkan basis, lalu terapkan file yang berubah.
Tidak ada penghapusan atau remote push. FILE_MANIFEST di dalam models/slr09
memeriksa isi paket model; manifest tingkat repository mengikuti integrasi
ke ZIP pengguna. Dua commit tracking SLR_08 dan suffix lokal(3) dikecualikan.

Bobot SENA terakhir SILAR_SENA_context_guard_v0.8.1_20261019.zip terpisah,
sekitar412 MB. Identitasnya ada pada asset_manifest dan lock v0.8.1. Gunakan
mekanisme aset repository setelah perbandingan ZIP sesuai cara proyek menyimpan
aset model. NARA tidak berubah,
sehingga aset NARA yang identik tidak perlu diunggah ulang. Kandidat belum
diterima untuk mutu atau produksi. Tidak ada deployment atau perubahan Kanban.
'''
    if output.exists():raise ValueError('Use a new output; preserve delivered archive')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr('README_OVERLAY.md',guide)
        archive.writestr('manifest_overlay_v0.8.1.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for item in files:archive.write(ROOT/Path(item['path']).relative_to('models/slr09'),item['path'])
    write(output.with_suffix('.manifest.json'),manifest)
    # The checkpoint is a full model-source snapshot, with model weights separate.
    with zipfile.ZipFile(checkpoint,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr('README_RECOVERY.md',guide+'\nIni snapshot sumber lengkap, bukan overlay.\n')
        for p in sorted(ROOT.rglob('*')):
            if included(p):archive.write(p,'models/slr09/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for item in files:
            from hashlib import sha256
            assert sha256(archive.read(item['path'])).hexdigest()==item['sha256']
            rel=Path(item['path']).relative_to('models/slr09');previous=base/rel
            assert (sha(previous) if previous.is_file() else None)==item['expected_previous_sha256']
    with zipfile.ZipFile(checkpoint) as archive:
        assert archive.testzip() is None
        assert not any(n.endswith(('.bin','.safetensors','.pyc')) or '/__pycache__/' in n for n in archive.namelist())
    result={'status':'SUCCEEDED','overlay':{'path':str(output),'sha256':sha(output),'bytes':output.stat().st_size,
        'files':len(files),'counts':dict(Counter(x['status'] for x in files))},
        'checkpoint':{'path':str(checkpoint),'sha256':sha(checkpoint),'bytes':checkpoint.stat().st_size},
        'crc_and_content_hashes_verified':True,'basis_hashes_verified':True,
        'weights_included':False,'remote_push_executed':False,'quality_acceptance_approved':False}
    write(output.with_suffix('.verification.json'),result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','artifacts','output','checkpoint','workspace'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.base,a.artifacts,a.output,a.checkpoint,a.workspace)
