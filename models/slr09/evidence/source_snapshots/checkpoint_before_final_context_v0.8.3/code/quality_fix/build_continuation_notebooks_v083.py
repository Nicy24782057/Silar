"""Create reproducible verification and pending-acceptance notebook sources."""
from copy import deepcopy
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[2]


def cell(kind, source):
    result = dict(cell_type=kind, id=uuid.uuid4().hex[:8], metadata={}, source=source)
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


def save(name, cells):
    path = ROOT / 'notebooks' / name
    if path.exists():
        raise ValueError('Preserve previous notebook sources: ' + name)
    notebook = dict(cells=cells, metadata=dict(
        kernelspec=dict(display_name='Python 3', language='python', name='python3'),
        language_info=dict(name='python', version='3.12.14')),
        nbformat=4, nbformat_minor=5)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + '\n')


def build():
    save('27_Verifikasi_Kandidat_SLR09_v0.8.3.ipynb', [
        cell('markdown', '# Verifikasi kandidat SLR_09 v0.8.3\n\nInferensi neural aktual SENA dan NARA pada 150 acuan yang sudah dipakai untuk training/pengembangan. Ini regresi, bukan uji penerimaan baru. NARA dan cutoff 0,95 tetap. Keluaran aktual direkam pada salinan _executed.'),
        cell('code', """from pathlib import Path
import os, sys, json, subprocess
from datetime import datetime, timezone
ROOT = Path(os.environ['SLR09_PACKAGE_ROOT']).resolve()
WORK = Path(os.environ['SLR09_WORK_DIR']).resolve()
SENA = Path(os.environ['SLR09_SENA_DIR']).resolve()
NARA = Path(os.environ['SLR09_NARA_DIR']).resolve()
OUT = WORK / ('joint_regression_v083_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
cmd = [sys.executable, str(ROOT/'code/quality_fix/verify_last_layer_candidate_v083.py'), '--sena-dir', str(SENA), '--nara-dir', str(NARA), '--output', str(OUT)]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in process.stdout:
    print(line, end='', flush=True)
process.wait()
if process.returncode:
    raise RuntimeError('Verifikasi kandidat gagal; pertahankan run_state/error_trace.')
report = json.loads((OUT/'run_state.json').read_text())
assert report['status'] == 'SUCCEEDED' and report['all_seen_joint_regression_checks_met']
assert not report['new_independent_acceptance_executed']
print(json.dumps(report, ensure_ascii=False, indent=2))
""")])
    original = json.loads((ROOT / 'notebooks/25_Uji_Penerimaan_SLR09_v0.8.2.ipynb').read_text())
    cells = deepcopy(original['cells'])
    cells[0]['source'] = '# Uji penerimaan SLR_09 v0.8.3\n\nAcuan FINAL083 berisi 50 usulan narasi sintetis yang masih PENDING. Kategori, tujuh field dan token harus direview manusia sebelum model dijalankan. Persetujuan lama tidak mengesahkan acuan ini. Kandidat dibekukan, cutoff dan target tetap. Notebook menolak template yang belum direview. Belum dieksekusi.'
    for item in cells:
        item['id'] = uuid.uuid4().hex[:8]
        if item['cell_type'] == 'code':
            source = item['source']
            source = ''.join(source) if isinstance(source, list) else source
            item['source'] = source.replace('final_acceptance_v082_', 'final_acceptance_v083_')
            item['execution_count'] = None
            item['outputs'] = []
    cells[2]['source'] = """# Tolak kandidat/acuan lama sebelum impor atau pemuatan model.
template = json.loads((ROOT/'acceptance/review_bundle_draft.json').read_text())
if template['protocol']['binding']['candidate_version'] != '0.8.3':
    raise ValueError('Kandidat v0.8.3 belum siap; jangan menjalankan penerimaan dengan kandidat lama.')
if not all(row['id'].startswith('FINAL083-') for row in template['records']):
    raise ValueError('Notebook ini memerlukan acuan FINAL083 baru.')
""" + cells[2]['source']
    cells[2]['source'] += """
# Simpan byte sumber yang terikat sebelum proses pemuatan/inferensi neural.
import shutil, hashlib
snapshot = RUN / 'pre_inference_snapshot'
snapshot_manifest = {}
for relative, expected in bundle['protocol']['binding']['files_sha256'].items():
    source = ROOT / relative
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    observed = hashlib.sha256(target.read_bytes()).hexdigest()
    assert observed == expected
    snapshot_manifest[relative] = observed
write(RUN/'pre_inference_snapshot_manifest.json', dict(files_sha256=snapshot_manifest, created_before_model_load=True))
"""
    save('28_Uji_Penerimaan_SLR09_v0.8.3.ipynb', cells)
    print('Created notebook 27 and pending notebook 28.')


if __name__ == '__main__':
    build()
