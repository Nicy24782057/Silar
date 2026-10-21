"""Preserve the latest working checkpoint while retaining the verified new candidate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile
from train_sena_cpu import sha, write

ROOT=Path(__file__).resolve().parents[2]


def merge(archive,notes):
    history=ROOT/'historical/checkpoint_before_final_context_v0.8.3'
    history.mkdir(parents=True,exist_ok=False)
    bundle=json.loads((ROOT/'acceptance/review_bundle_draft.json').read_text())
    mapping=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe source path')
            if name.endswith('/') or not name.startswith('models/slr09/'):continue
            rel=Path(name).relative_to('models/slr09');data=z.read(name);target=ROOT/rel
            digest=hashlib.sha256(data).hexdigest()
            if target.is_file() and sha(target)==digest:
                disposition='ALREADY_IDENTICAL'
            elif rel.as_posix()=='code/tests/test_candidate_runtime.py':
                expected=target.read_text().replace(
                    '    PACKAGE_ROOT, RUNTIME_FILES, candidate_record, check_dependencies,',
                    '    CANDIDATE_LOCK, INTEGRATION_CONFIG, PACKAGE_ROOT, RUNTIME_FILES, candidate_record, check_dependencies,')
                expected=expected.replace("['SLR09_Konfigurasi_Integrasi_v0.8.json', 'quality_candidate_asset_lock_v0.8.3.json', 'inference_environment.json']",
                    "[INTEGRATION_CONFIG, CANDIDATE_LOCK, 'inference_environment.json']")
                expected=expected.replace("root / 'config/quality_candidate_asset_lock_v0.8.3.json'","root / 'config' / CANDIDATE_LOCK")
                assert data.decode()==expected,'Unreviewed test-source difference'
                target.write_bytes(data);disposition='REUSE_SELECTOR_CONSTANTS_IN_EXISTING_TEST'
            elif not target.exists() and rel.parts[0] in {'evidence','results','historical','sources'}:
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                disposition='PRESERVED_ADDITIONAL_EVIDENCE'
            else:
                target=history/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                disposition='PRESERVED_PREVIOUS_SOURCE_OR_CONFLICT_IN_HISTORY'
            mapping.append(dict(source_path=name,source_sha256=digest,
                destination=target.relative_to(ROOT).as_posix(),disposition=disposition))
    shutil.copy2(notes,ROOT/'historical/Catatan_Kelanjutan_before_final_v0.8.3.md')
    for rel,want in bundle['protocol']['binding']['files_sha256'].items():
        assert sha(ROOT/rel)==want,'Verified candidate binding changed during history merge: '+rel
    write(ROOT/'evidence/quality_fix_v083/checkpoint_merge.json',dict(
        merged_at=datetime.now(timezone.utc).isoformat(),
        library_checkpoint_id='libfile_adf80cd5e9548191981ca25322273261',
        library_checkpoint_version=1,checkpoint_sha256=sha(archive),
        continuation_note_library_version=6,note_sha256=sha(notes),
        verified_candidate_binding_unchanged=True,files=mapping))
    lock=json.loads((ROOT/'config/quality_candidate_asset_lock_v0.8.3.json').read_text())
    write(ROOT/'RECOVERY_v0.8.3.json',dict(schema='slr09-final-context-recovery-0.8.3',
        status='IN_REVIEW_PENDING_HUMAN_REFERENCE_REVIEW',
        latest_training='evidence/quality_fix_v083/contrast_replay_training_v083_20261020T102629_870319Z',
        latest_joint_verification='evidence/quality_fix_v083/export_verification27',
        integration_configuration='config/SLR09_Konfigurasi_Integrasi_v0.8.json',
        candidate_lock='config/quality_candidate_asset_lock_v0.8.3.json',
        model_archives={n:dict(archive_name=s['archive_name'],archive_sha256=s['archive_sha256'],
                             weights_sha256=s['files']['model.safetensors']) for n,s in lock['models'].items()},
        next_workbook='acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx',
        next_notebook='notebooks/28_Uji_Penerimaan_SLR09_v0.8.3.ipynb',
        next_reference_status='50_PENDING_685_TOKEN_PROPOSALS_NOT_INFERRED',
        prior_checkpoint_history='historical/checkpoint_before_final_context_v0.8.3',
        confidence_threshold=.95,quality_acceptance_approved=False,card_done=False,
        remote_push_executed=False,production_deployed=False))
    print(json.dumps({'source_files_preserved':len(mapping),'verified_binding_unchanged':True,
        'additional_evidence':sum(x['disposition']=='PRESERVED_ADDITIONAL_EVIDENCE' for x in mapping)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--notes',type=Path,required=True)
    a=p.parse_args();merge(a.archive.resolve(),a.notes.resolve())
