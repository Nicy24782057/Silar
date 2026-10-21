"""Build a code/evidence overlay against the previous prepared package.

Does not read or change a remote repository, include weights, delete files or
declare quality acceptance. The manifest exposes the expected local base.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build(base,output):
    files=[]
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or '__pycache__' in relative.parts or path.suffix in {'.pyc','.safetensors','.bin'}:continue
        original=base/relative
        if original.is_file() and sha(path)==sha(original):continue
        if path.suffix=='.zip':raise ValueError('Unexpected ZIP/weight in source overlay: '+str(relative))
        files.append({'path':'models/slr09/'+relative.as_posix(),
                      'status':'MODIFIED' if original.is_file() else 'NEW',
                      'expected_previous_sha256':sha(original) if original.is_file() else None,
                      'sha256':sha(path),'bytes':path.stat().st_size})
    manifest={'schema':'slr09-source-evidence-overlay-0.5',
              'basis':'PREVIOUS_PREPARED_V0.4.1_PACKAGE_NOT_YET_COMPARED_WITH_USER_REPOSITORY_ZIP',
              'status':'IN_REVIEW','quality_acceptance_approved':False,'card_done':False,
              'remote_push_executed':False,'weights_included':False,
              'files':files}
    if output.exists():raise ValueError('Choose a new output archive')
    output.parent.mkdir(parents=True,exist_ok=True)
    readme='''# Overlay perbaikan dan bukti SLR_09 v0.5

Status mutu masih In Review. Semua metrik pada 50 narasi lama tercapai,
tetapi diagnostik 24 narasi tambahan masih menemukan kegagalan SENA.

Laporan utama: models/slr09/SLR09_STATUS_v0.5.md.
Excel: models/slr09/results/quality_fix_v05/SLR09_Hasil_Perbaikan_v0.5.xlsx.
Notebook 11, 11b dan 12 beserta output nyata ada pada models/slr09/notebooks/.

Ini overlay file baru/berubah terhadap paket kerja v0.4.1. Ini bukan seluruh
repository dan belum diverifikasi terhadap ZIP GitHub yang akan dikirim.
Manifest mencatat hash basis untuk pemeriksaan sebelum penggabungan.
Tidak ada file yang dihapus dan tidak ada push/deployment.

ZIP bobot eksperimen dipisahkan. Identitasnya ada pada konfigurasi v0.2 dan
quality_candidate_asset_lock_v0.5.json. Kandidat tersebut belum diterima
untuk mutu atau produksi. Konfigurasi v0.1 tetap sebagai riwayat.

Commit hanya file baru/berubah setelah paket ditinjau dan basis dicocokkan.
Tidak perlu mengunggah ulang seluruh repository. Pengecualian dua commit
tracking SLR_08 dan suffix nama lokal (3) tetap berlaku.
'''
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_OVERLAY.md',readme)
        z.writestr('manifest_overlay_v0.5.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for item in files:z.write(ROOT/Path(item['path']).relative_to('models/slr09'),item['path'])
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    info={'archive':str(output),'sha256':sha(output),'bytes':output.stat().st_size,'files':len(files),
          'modified':sum(x['status']=='MODIFIED' for x in files),'new':sum(x['status']=='NEW' for x in files)}
    print(json.dumps(info,indent=2))
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.base,a.output)
