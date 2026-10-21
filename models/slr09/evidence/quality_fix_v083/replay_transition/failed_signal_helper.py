"""Preserve two completed cached epochs, then expand known hard replay if needed."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root=Path(os.environ['SLR09_PACKAGE_ROOT']).resolve()
previous=Path(os.environ['SLR09_PREVIOUS_TRAINING']).resolve()
while True:
    try:
        state=json.loads((previous/'run_state.json').read_text())
        history=json.loads((previous/'training_history.json').read_text())
    except (FileNotFoundError,json.JSONDecodeError):
        time.sleep(5);continue
    if state['status']=='SUCCEEDED':
        print('CACHED_CANDIDATE_ALREADY_FEASIBLE_NO_REPLAY_CHANGE',flush=True)
        raise SystemExit(0)
    if len(history)>=2 and (state.get('epoch',0)>=3 or state['status'] in {'FAILED','NO_FEASIBLE_CANDIDATE'}):
        break
    print('Waiting for completed second epoch and an immutable selected checkpoint',flush=True)
    time.sleep(10)
if state['status'] not in {'FAILED','NO_FEASIBLE_CANDIDATE'}:
    matches=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            if (entry/'comm').read_text().strip() not in {'python','python3'}:continue
            command=(entry/'cmdline').read_bytes()
            if b'/train_cached_context_v083.py\x00' in command and str(previous).encode() in command and b'--output\x00' in command:
                matches.append(int(entry.name))
        except OSError:continue
    if len(matches)!=1:raise RuntimeError('Expected exactly the owned cached-training child, refusing to interrupt')
    pid=matches[0]
    os.kill(pid,signal.SIGINT)
    for _ in range(30):
        if not Path(f'/proc/{pid}').exists():break
        time.sleep(1)
    else:raise RuntimeError('Owned training child did not exit; no new training started')
    (previous/'run_state_before_replay_correction.json').write_text(json.dumps(state,indent=2)+'\n')
    state.update(status='INTERRUPTED_FOR_REPLAY_CORRECTION',
        finished_at=datetime.now(timezone.utc).isoformat(),completed_epochs=len(history),
        selected_epoch=json.loads((previous/'best_selection.json').read_text())['epoch'],
        discarded_partial_next_epoch=True,interrupted_process_id=pid,
        reason='EXPAND_HARD_REPLAY_TO_ALL_KNOWN_CONTRASTS_AND_SEEN_HUMAN_FALSE_EVENTS',
        all_known_constraints_met=False)
    (previous/'run_state.json').write_text(json.dumps(state,indent=2)+'\n')
print('RETAINED_COMPLETED_CACHED_EPOCHS_STARTING_FULL_CONTRAST_REPLAY',flush=True)
command=[sys.executable,'-u',str(root/'code/quality_fix/execute_notebook_cells_v06.py'),
    str(root/'notebooks/26c_Penguatan_Kontras_Lama_v0.8.3.ipynb')]
raise SystemExit(subprocess.call(command))
