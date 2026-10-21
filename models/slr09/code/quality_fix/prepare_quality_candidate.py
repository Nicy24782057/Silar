"""Create a separately identified development candidate; keep v0.1 frozen."""
import argparse
import json
from pathlib import Path
from export_quality_model import export
from train_sena_cpu import write, sha

ROOT=Path(__file__).resolve().parents[2]


def prepare(run,exports):
    state=json.loads((run/'run_state.json').read_text())
    run_id=state['started_at'].split('.')[0].replace('-','').replace(':','')
    model_id='SILAR_SENA_quality_cpu_v05_'+run_id
    spec=export(run,exports/'SILAR_SENA_quality_cpu_v05_20261019.zip',model_id,run_id)
    previous=json.loads((ROOT/'config/candidate_asset_lock.json').read_text())
    lock={'schema':'slr09-quality-candidate-assets-0.5','status':'DEVELOPMENT_NOT_QUALITY_ACCEPTED',
          'models':{'sena':spec,'nara':previous['models']['nara']},
          'previous_candidate_lock_preserved':'config/candidate_asset_lock.json',
          'previous_sena_candidate_weights_available':False,
          'sena_is_a_new_baseline_derived_model':True}
    write(ROOT/'config/quality_candidate_asset_lock_v0.5.json',lock)
    config=json.loads((ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.1.json').read_text())
    config.update(schema='slr09-integration-configuration-0.2',status='DEVELOPMENT_CANDIDATE_NOT_QUALITY_ACCEPTED',
        adapter_version='silar-adapter-0.5.0',victim_guard_version='silar-victim-guard-0.5.0',
        postprocessing_version='silar-postprocessing-0.3.0',composition_version='silar-nara-composition-0.2.0',
        calibration_reference=model_id+':USER_SELECTED_OPERATING_CUTOFF_0.95_NOT_PROBABILITY_CALIBRATED',
        reference_run_id=run_id,reference_report_sha256=sha(run/'best_development_metrics.json'),
        reference_scope='FITTED_DEVELOPMENT146_NOT_INDEPENDENT_VALIDATION_OR_TEST',
        selection_basis='EXISTING_USER_SELECTED_OPERATING_CUTOFF_CARRIED_FORWARD_WITHOUT_CALIBRATION_CLAIM',
        probability_calibration_fitted=False,
        non_event_head_bias_fitted_on_development=state['selected_non_event_head_bias'],
        quality_acceptance_approved=False,production_model_selected=False,production_deployed=False,
        previous_configuration_preserved='config/SLR09_Konfigurasi_Integrasi_v0.1.json')
    for name in ('sena','nara'):
        model=lock['models'][name]
        config[name]={key:model[key] for key in ('archive_name','archive_sha256','run_id','labels')}
        config[name].update(weights_sha256=model['files']['model.safetensors'],
                            weight_identity_source='DIRECT_LOCAL_SAFETENSORS_SHA256')
    write(ROOT/'config/SLR09_Konfigurasi_Integrasi_v0.2.json',config)
    print('Development candidate configuration prepared. No production or quality approval granted.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--exports',type=Path,required=True)
    a=p.parse_args();prepare(a.run,a.exports)
