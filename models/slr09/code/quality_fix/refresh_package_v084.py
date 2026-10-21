"""Reconcile resume pointers before first delivery; preserve all model/test evidence."""
import hashlib
import json
import os
import zipfile
from finalize_development_v084 import ROOT, OUT, EV, PREFIX, included, sha, read, write


def main():
    rec=read(ROOT/'RECOVERY_v0.8.4.json')
    lock=read(ROOT/'config/quality_candidate_asset_lock_v0.8.4.json')
    rec.update(schema='slr09-final-context-recovery-0.8.4',
        latest_training='evidence/quality_fix_v084/training29',
        latest_joint_verification='evidence/quality_fix_v084/export_verification30',
        integration_configuration=rec['active_configuration'],candidate_lock=rec['active_candidate_lock'],
        prior_checkpoint_history='historical/before_development_v0.8.4_checkpoint',
        model_archives={name:dict(archive_name=spec['archive_name'],archive_sha256=spec['archive_sha256'],
            weights_sha256=spec['files']['model.safetensors']) for name,spec in lock['models'].items()})
    write(ROOT/'RECOVERY_v0.8.4.json',rec)
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(ROOT.rglob('*')) if included(p) and p!=ROOT/'FILE_MANIFEST.json']
    manifest=read(ROOT/'FILE_MANIFEST.json');manifest.update(revision='0.8.4',files=files)
    write(ROOT/'FILE_MANIFEST.json',manifest)
    target=OUT/'SLR09_Checkpoint_Pengerjaan_v0.8.4.zip'
    tmp=target.with_suffix('.repack.tmp')
    with zipfile.ZipFile(tmp,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(ROOT/'SLR09_STATUS_v0.8.4.md','README_RECOVERY.md')
        for p in sorted(ROOT.rglob('*')):
            if included(p):z.write(p,PREFIX+p.relative_to(ROOT).as_posix())
    preservation=read(EV/'checkpoint_preservation.json')['preserved']
    with zipfile.ZipFile(tmp) as z:
        assert z.testzip() is None
        for item in files:assert hashlib.sha256(z.read(PREFIX+item['path'])).hexdigest()==item['sha256']
        for item in preservation:assert hashlib.sha256(z.read(item['destination'])).hexdigest()==item['sha256']
    os.replace(tmp,target)
    result=read(OUT/'delivery_verification_v084.json')
    for item in result['artifacts']:
        if item['path']==str(target):item.update(bytes=target.stat().st_size,sha256=sha(target))
    write(OUT/'delivery_verification_v084.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
