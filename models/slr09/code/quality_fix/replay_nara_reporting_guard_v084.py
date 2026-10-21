"""Replay saved neural outputs on seen references; not a new neural acceptance test."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'code/active_nara_adapter'),str(ROOT/'code/acceptance')]
from slr09_candidate_runtime import candidate_record
from evaluate_acceptance import score,file_sha,write


def run():
    out=ROOT/'evidence/quality_fix_v084/reporting_guard_replay'
    out.mkdir(parents=True,exist_ok=False)
    config=json.loads((ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.8.json').read_text())
    lock=json.loads((ROOT/'config/quality_candidate_asset_lock_v0.8.3.json').read_text())
    sources={
      'human_regression50':('evidence/quality_fix_v05/previous_50/reviewed_bundle_frozen.json','evidence/quality_fix_v083/export_verification27/predictions_human_regression50.jsonl'),
      'FINAL081_seen':('evidence/acceptance_v081/original_run/evidence/reviewed_bundle_frozen.json','evidence/quality_fix_v083/export_verification27/predictions_FINAL081_seen.jsonl'),
      'FINAL082_seen':('evidence/acceptance_v082/original_run/evidence/reviewed_bundle_frozen.json','evidence/quality_fix_v083/export_verification27/predictions_FINAL082_seen.jsonl'),
      'FINAL083_seen':('evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run/reviewed_bundle_frozen.json','evidence/acceptance_v083_confirmed_20261020/acceptance_FINAL083/original_run/predictions.jsonl')}
    summary={}
    for name,(reference_path,prediction_path) in sources.items():
        reference=ROOT/reference_path;source=ROOT/prediction_path
        bundle=json.loads(reference.read_text());old=[json.loads(x) for x in source.read_text().splitlines()]
        assert [x['id'] for x in bundle['records']]==[p['id'] for p in old]
        predictions=[]
        for row,previous in zip(bundle['records'],old):
            p=candidate_record(row,previous['event_classifier'],previous['nara_tokens'],config,lock)
            p.update(nara_tokens=previous['nara_tokens'],sena_token_coverage=previous['sena_token_coverage'],nara_token_coverage=previous['nara_token_coverage'])
            predictions.append(p)
        report=score(bundle['records'],predictions,bundle['protocol'])
        report.update(scope='SEEN_DEVELOPMENT_SAVED_OUTPUT_REPLAY',model_inference_executed=False,
                      source_reference_sha256=file_sha(reference),source_predictions_sha256=file_sha(source))
        write(out/f'evaluation_{name}.json',report)
        with (out/f'predictions_{name}.jsonl').open('x') as stream:
            for p in predictions:stream.write(json.dumps(p,ensure_ascii=False)+'\n')
        summary[name]={'nonempty_exact':report['fields']['nonempty_exact'],'empty_spurious_rate':report['fields']['empty_spurious_rate'],'checks':report['checks']}
    write(out/'summary.json',dict(scope='SEEN_OUTPUT_REPLAY_NOT_ACCEPTANCE',sets=summary,
          model_inference_executed=False,new_acceptance_inference_executed=False,
          quality_acceptance_approved=False))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':run()
