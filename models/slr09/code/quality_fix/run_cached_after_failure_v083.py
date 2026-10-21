"""Continue only if the original bounded experiment ends without a candidate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(os.environ['SLR09_PACKAGE_ROOT']).resolve()
previous = Path(os.environ['SLR09_PREVIOUS_TRAINING']).resolve()
while True:
    state = json.loads((previous/'run_state.json').read_text())
    if state['status'] in {'SUCCEEDED','FAILED','NO_FEASIBLE_CANDIDATE'}:
        break
    print('Waiting for the original experiment to finish; status:',state['status'],flush=True)
    time.sleep(15)
if state['status']=='SUCCEEDED':
    print('ORIGINAL_CANDIDATE_FEASIBLE_CACHED_CONTINUATION_NOT_NEEDED',flush=True)
else:
    print('ORIGINAL_EXPERIMENT_FINISHED_WITHOUT_FEASIBLE_CANDIDATE_CONTINUING',flush=True)
    command=[sys.executable,'-u',str(root/'code/quality_fix/execute_notebook_cells_v06.py'),
        str(root/'notebooks/26b_Pelatihan_Konteks_Dengan_Cache_v0.8.3.ipynb')]
    raise SystemExit(subprocess.call(command))
