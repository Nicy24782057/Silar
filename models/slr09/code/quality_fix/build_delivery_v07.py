"""Incremental source/evidence package against delivered v0.5; no remote action."""
import argparse
import json
from pathlib import Path
import zipfile
from train_sena_cpu import sha
ROOT=Path(__file__).resolve().parents[2]

def build(base,output):
    if output.exists():raise ValueError('Choose a new archive; preserve previous evidence')
    files=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or '__pycache__' in rel.parts or p.suffix in {'.pyc','.safetensors','.bin'}:continue
        old=base/rel
        if old.is_file() and sha(old)==sha(p):continue
        if p.suffix=='.zip':raise ValueError('Model/archive must remain separate: '+str(rel))
        files.append({'path':'models/slr09/'+rel.as_posix(),'status':'MODIFIED' if old.is_file() else 'NEW',
            'expected_previous_sha256':sha(old) if old.is_file() else None,'sha256':sha(p),'bytes':p.stat().st_size})
    manifest={'schema':'slr09-source-evidence-overlay-0.7',
        'basis':'PREVIOUS_DELIVERED_V05_OVER_V041_NOT_USER_GITHUB_ZIP',
        'status':'IN_REVIEW','quality_acceptance_approved':False,'card_done':False,
        'remote_push_executed':False,'production_deployed':False,'weights_included':False,
        'old_notebook_and_configuration_history_preserved':True,
        'audit_exclusions':['TWO_SLR08_TRACKING_COMMITS','LOCAL_FILENAME_SUFFIX_(3)'],
        'files':files}
    readme='''# Perubahan SLR_09 v0.6–v0.7

Laporan terbaru: models/slr09/SLR09_STATUS_v0.7.md.
Excel: models/slr09/results/quality_fix_v07/SLR09_Hasil_Perbaikan_v0.7.xlsx.
Status mutu masih In Review. Target dan cutoff 0.95 tetap.

Notebook 13, 13b, 14, 15, dan 16 beserta hasil eksekusi nyata ada pada
models/slr09/notebooks/. Sel Python dijalankan melalui CPython cell executor;
ini bukan klaim eksekusi kernel Jupyter asli. Metadata mencatatnya.
Riwayat notebook 09–12 ada dalam paket terdahulu dan tetap dipertahankan.

Ini file baru/berubah terhadap paket v0.5 yang sudah disiapkan, bukan seluruh
repository. Manifest mencatat hash basis. Cocokkan dengan ZIP repository
pengguna sebelum penggabungan akhir. Tidak ada penghapusan atau remote push.

Kandidat pengembangan terakhir memakai konfigurasi v0.4 dan lock v0.7.
Arsip bobot SENA terpisah dari paket kode. NARA tidak dilatih ulang.
Kandidat belum disetujui sebagai model produksi. Jangan mengganti status
In Review menjadi Done hanya karena tes kode atau regresi lama lulus.

Review Data di Excel mempertahankan 40 baris dan keputusan manusia yang
ada. Label tambahan asisten tidak disetujui otomatis. Hasil 24 lama dan
50 diagnostik v0.6 kini development dan tidak boleh disebut uji akhir baru.
Pilot penerimaan berikutnya perlu acuan manusia dibekukan sebelum inferensi
serta binding kandidat/kode baru. Kit lama terikat kandidat terdahulu.

Untuk push nanti, commit file baru/berubah pada manifest setelah basis
dicocokkan. Bobot disimpan terpisah sesuai mekanisme aset proyek. Tidak perlu
mengunggah ulang seluruh repository. Dua commit tracking SLR_08 dan suffix
nama lokal (3) tetap dikecualikan dari temuan audit.
'''
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('README_OVERLAY.md',readme)
        z.writestr('manifest_overlay_v0.7.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for item in files:z.write(ROOT/Path(item['path']).relative_to('models/slr09'),item['path'])
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    info={'archive':str(output),'sha256':sha(output),'bytes':output.stat().st_size,
        'files':len(files),'new':sum(f['status']=='NEW' for f in files),'modified':sum(f['status']=='MODIFIED' for f in files)}
    print(json.dumps(info,indent=2));return info

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.base,a.output)
