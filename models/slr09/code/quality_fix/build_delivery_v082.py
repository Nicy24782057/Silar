"""Source/evidence overlay over delivered v0.8.1; model archives stay unchanged."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from train_sena_cpu import sha,write
ROOT=Path(__file__).resolve().parents[2]


def included(p):
    return p.is_file() and '__pycache__' not in p.relative_to(ROOT).parts and p.suffix not in {'.pyc','.safetensors','.bin'}


def build(base,artifacts,output,checkpoint):
    if output.exists():raise ValueError('Preserve the delivered archive; choose a new output')
    result=ROOT/'results/acceptance_v082';result.mkdir(parents=True,exist_ok=True)
    for name in ['SLR09_Hasil_Uji_dan_Perbaikan_v0.8.2.xlsx','result_workbook_verification_v082.json',
                 'new_kit_verification_v082.json','SLR09_Hasil_Uji_dan_Perbaikan_v0.8.2_formula_scan.ndjson',
                 'Review_Penerimaan_Akhir_SLR09_v0.8.2_formula_scan.ndjson']:
        shutil.copy2(artifacts/name,result/name)
    shutil.copy2(artifacts/'Review_Penerimaan_Akhir_SLR09_v0.8.2.xlsx',ROOT/'acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.2.xlsx')
    previews=result/'previews';previews.mkdir(exist_ok=True)
    for p in artifacts.glob('*v0.8.2_*.png'):shutil.copy2(p,previews/p.name)
    history=ROOT/'historical/FILE_MANIFEST_v0.8.1.json'
    if not history.exists():shutil.copy2(base/'FILE_MANIFEST.json',history)
    files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
           for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    write(ROOT/'FILE_MANIFEST.json',{'schema':'slr09-source-evidence-files-0.8.2','revision':'0.8.2',
        'manifest_itself_excluded':True,'status':'IN_REVIEW','weights_included':False,
        'first_acceptance_target_failed':True,'first_acceptance_field_exact':[163,207],
        'final_known_regression_field_exact':[177,207],'original_reference_retired':True,
        'new_reference_status':'50_PENDING_671_TOKENS_NOT_INFERRED',
        'new_gradient_training_executed':False,'new_neural_inference_executed_v082':False,
        'quality_acceptance_approved':False,'card_done':False,'remote_push_executed':False,'files':files})
    changed=[]
    for p in sorted(ROOT.rglob('*')):
        if not included(p):continue
        relative=p.relative_to(ROOT);old=base/relative
        if old.is_file() and sha(old)==sha(p):continue
        if p.suffix=='.zip':raise ValueError('Changed archive must remain separate: '+str(relative))
        changed.append({'path':'models/slr09/'+relative.as_posix(),'status':'MODIFIED' if old.is_file() else 'NEW',
            'expected_previous_sha256':sha(old) if old.is_file() else None,'sha256':sha(p),'bytes':p.stat().st_size})
    manifest={'schema':'slr09-source-evidence-overlay-0.8.2',
        'basis':'PREVIOUS_DELIVERED_V081_NOT_USER_GITHUB_ZIP',
        'basis_checkpoint_sha256':'57adb7d1e7a8aeccee9bc702c1b02abb298f3c37c28565e57d5a256a0ef79c1c',
        'status':'IN_REVIEW','quality_acceptance_approved':False,'card_done':False,
        'remote_push_executed':False,'production_deployed':False,'weights_included':False,
        'sena_nara_archives_unchanged':True,'deletions':[],
        'audit_exclusions':['TWO_SLR08_TRACKING_COMMITS','LOCAL_FILENAME_SUFFIX_(3)'],'files':changed}
    guide='''# Perubahan SLR_09 v0.8.2

Baca models/slr09/SLR09_STATUS_v0.8.2.md dan Excel di results/acceptance_v082/.
Review bintang50 APPROVED telah dipakai untuk inferensi aktual notebook23.
Workflow aslinya gagal pada SCORING; seluruh keluaran dan kode asli tetap ada.
Penilaian dilengkapi tanpa NN baru dari prediksi beku: field163/207=78,74%,
gagal target80%. Komposisi field diperbaiki, regresi kini177/207=85,51%.
Seluruh9 pemeriksaan pada50 ini dan regresi50 lama memenuhi;80 tes kontrak
dan23 tes evaluator lulus. Gold, label token, probabilitas, dan bobot tetap.

Hasil sesudah perbaikan adalah regresi pada data yang sudah dipakai memperbaiki
kode. Status tetap In Review. Kit FINAL08250 narasi/671 token masih PENDING dan
belum diinferensikan. Notebook25 menunggu review baru; persetujuan lama tidak
mengesahkan acuan baru. Tidak ada penetapan Done atau persetujuan mutu otomatis.

Konfigurasi aktifv0.7, lockv0.8.2, adapter0.5.2/komposisi0.3.1/runner0.6.3.
Arsip SENA context_guard_v0.8.1 dan NARA reviewed_pilot tetap identik; tidak
perlu mengunggah ulang bobot yang sama. Perubahan hanya kode/config/data/bukti.

Ini overlay terhadap sumberv0.8.1 yang sudah disiapkan, bukan ZIP GitHub pengguna.
Manifest mencatat semua file baru/berubah dan hash basis. Cocokkan ZIP repository
pengguna sebelum penggabungan/push akhir; jangan menimpa seluruh repository.
Tidak ada penghapusan, remote push, deployment, atau perubahan Kanban. Dua
commit tracking SLR_08 dan suffix lokal(3) dikecualikan dari temuan audit.

Notebook23,24,24b beserta keluaran aktual tetap ada;25 belum dieksekusi.24/24b
mengaudit replay CLI yang sudah dijalankan dan menjalankan tes. Sel memakai
CPython cell executor; bukan klaim kernel Jupyter asli atau NN baru di v0.8.2.
'''
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_OVERLAY.md',guide)
        z.writestr('manifest_overlay_v0.8.2.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for item in changed:z.write(ROOT/Path(item['path']).relative_to('models/slr09'),item['path'])
    write(output.with_suffix('.manifest.json'),manifest)
    with zipfile.ZipFile(checkpoint,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_RECOVERY.md',guide+'\nSnapshot ini memuat sumber lengkap; bobot tetap terpisah.\n')
        for p in sorted(ROOT.rglob('*')):
            if included(p):z.write(p,'models/slr09/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        for item in changed:
            assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
            previous=base/Path(item['path']).relative_to('models/slr09')
            assert (sha(previous) if previous.is_file() else None)==item['expected_previous_sha256']
    with zipfile.ZipFile(checkpoint) as z:
        assert z.testzip() is None
        assert not any(n.endswith(('.bin','.safetensors','.pyc')) or '/__pycache__/' in n for n in z.namelist())
    report={'status':'SUCCEEDED','overlay':{'path':str(output),'bytes':output.stat().st_size,'sha256':sha(output),
        'files':len(changed),'counts':dict(Counter(x['status'] for x in changed))},
        'checkpoint':{'path':str(checkpoint),'bytes':checkpoint.stat().st_size,'sha256':sha(checkpoint)},
        'crc_and_hashes_verified':True,'basis_hashes_verified':True,'weights_unchanged':True,
        'quality_acceptance_approved':False,'remote_push_executed':False}
    write(output.with_suffix('.verification.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','artifacts','output','checkpoint'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.base,a.artifacts,a.output,a.checkpoint)
