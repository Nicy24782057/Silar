"""Bind new pending proposals to v0.8.2; retain the first failed acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]


def load(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def bind():
    proposals=load(ROOT/'data/final_reference_proposals_v0.8.2.json')
    assert all(r['review']['status']=='PENDING' and not r['review']['reviewer'] for r in proposals['records'])
    history=ROOT/'acceptance/history/pre_v0.8.2'
    if not history.exists():
        history.mkdir(parents=True)
        for name in ('review_bundle_draft.json','known_inputs.json','README.md'):
            shutil.copy2(ROOT/'acceptance'/name,history/name)
    else:
        current=load(ROOT/'acceptance/review_bundle_draft.json')
        assert all(r['review']['status']=='PENDING' for r in current['records'])
        archive=ROOT/'acceptance/history/binding_before_final_predicate_v0.8.2.json'
        if not archive.exists():write(archive,current['protocol']['binding'])
    old=load(history/'review_bundle_draft.json');known=load(history/'known_inputs.json');hashes=set(known['normalized_text_sha256'])
    sources=[]
    def collect(x):
        if isinstance(x,dict):
            if isinstance(x.get('text'),str):hashes.add(hashlib.sha256(' '.join(x['text'].casefold().split()).encode()).hexdigest())
            for v in x.values():collect(v)
        elif isinstance(x,list):
            for v in x:collect(v)
    for folder in ('data','evidence'):
        for p in sorted((ROOT/folder).rglob('*')):
            if not p.is_file() or p.suffix not in ('.json','.jsonl') or p.name in {'final_reference_proposals_v0.8.2.json','final_reference_identity_v0.8.2.json'}:continue
            if p.suffix=='.json':collect(load(p))
            else:
                for line in p.read_text().splitlines():
                    if line.strip():collect(json.loads(line))
            sources.append(p.relative_to(ROOT).as_posix())
    proposed={hashlib.sha256(' '.join(r['text'].casefold().split()).encode()).hexdigest() for r in proposals['records']}
    assert len(proposed)==50 and not proposed&hashes
    write(ROOT/'acceptance/known_inputs.json',{'schema':'slr09-known-inputs-0.8.2',
        'normalized_text_sha256':sorted(hashes),'sources':sources,'prior_hashes_retained':True,
        'scope':'Available sources only. Exact normalization does not establish semantic independence or population representativeness.'})
    files=list((ROOT/'code/active_nara_adapter').glob('*.py'))+[ROOT/p for p in (
        'code/acceptance/evaluate_acceptance.py','code/acceptance/import_review_xlsx.py',
        'config/SLR09_Konfigurasi_Integrasi_v0.7.json','config/quality_candidate_asset_lock_v0.8.2.json',
        'config/inference_environment.json','config/requirements-inference.txt','asset_manifest.json',
        'acceptance/known_inputs.json','data/final_reference_proposals_v0.8.2.json',
        'data/final_reference_identity_v0.8.2.json','data/development_review_v0.8.json',
        'data/retirement_after_FINAL081_v0.8.2.json')]
    protocol=deepcopy(old['protocol']);protocol['binding']={'candidate_version':'0.8.2',
        'files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    protocol['reference_round']='FINAL082_PENDING_HUMAN_REVIEW_BEFORE_INFERENCE'
    protocol['previous_bintang_approval_does_not_approve_this_reference']=True
    protocol.pop('prior_development_approval_does_not_approve_this_reference',None)
    write(ROOT/'acceptance/review_bundle_draft.json',{'protocol':protocol,'records':proposals['records']})
    write(ROOT/'evidence/field_fix_v082/new_kit_binding.json',{'known_texts':len(hashes),
        'records':50,'tokens':sum(len(r['gold_nara_labels']) for r in proposals['records']),
        'reference_sha256':sha(ROOT/'data/final_reference_proposals_v0.8.2.json'),
        'bundle_sha256':sha(ROOT/'acceptance/review_bundle_draft.json'),
        'normalized_exact_overlap':0,'status':'50_PENDING','new_neural_inference_executed':False,
        'quality_acceptance_approved':False})
    print(json.dumps({'known_texts':len(hashes),'records':50,'status':'PENDING','neural_inference_executed':False}))


if __name__=='__main__':bind()
