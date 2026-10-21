"""Run export verification only after a successful, recorded training run."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root=Path(os.environ['SLR09_PACKAGE_ROOT']).resolve()
training=Path(os.environ['SLR09_TRAINING_RUN']).resolve()
print('Waiting for a feasible recorded development candidate before export',flush=True)
while True:
    try:state=json.loads((training/'run_state.json').read_text())
    except (FileNotFoundError,json.JSONDecodeError):time.sleep(5);continue
    if state['status']=='SUCCEEDED':break
    if state['status'] in {'FAILED','NO_FEASIBLE_CANDIDATE','INTERRUPTED_FOR_REPLAY_CORRECTION'}:
        raise RuntimeError('Training did not complete with a feasible candidate; nothing exported')
    time.sleep(10)
recorded=root/'notebooks/26c_Penguatan_Kontras_Lama_v0.8.3_executed.ipynb'
for _ in range(30):
    if recorded.exists():
        try:
            if json.loads(recorded.read_text())['metadata'].get('execution_succeeded') is True:break
        except json.JSONDecodeError:pass
    time.sleep(1)
else:raise RuntimeError('Training succeeded but its actual notebook record is not complete')
command=[sys.executable,'-u',str(root/'code/quality_fix/execute_notebook_cells_v06.py'),
    str(root/'notebooks/27_Verifikasi_Ekspor_SENA_NARA_v0.8.3.ipynb')]
raise SystemExit(subprocess.call(command))
