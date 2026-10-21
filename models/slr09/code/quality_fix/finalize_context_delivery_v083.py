"""Build a verifiable continuation package without extracted weights or caches."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from train_sena_cpu import LABELS, sha, write

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def included(path):
    rel = path.relative_to(ROOT)
    return (path.is_file() and '__pycache__' not in rel.parts
        and path.suffix not in {'.pyc', '.safetensors', '.bin'}
        and not ('quality_fix_v083' in rel.parts and any(p in rel.parts for p in ('runtime', 'best_model'))))


def build(training, verification, source, output):
    state = load(training / 'run_state.json')
    chosen = load(training / 'best_selection.json')
    base = load(training / 'baseline_evaluation.json')
    checks = load(verification / 'run_state.json')
    contract = load(ROOT / 'evidence/quality_fix_v083/active_tests27/active_tests.json')
    evaluator = load(ROOT / 'evidence/quality_fix_v083/evaluator_tests.json')
    kit = load(ROOT / 'evidence/quality_fix_v083/new_kit_binding.json')
    workbook = load(ROOT / 'results/quality_fix_v083/acceptance_workbook_verification.json')
    assert state['status'] == 'SUCCEEDED' and chosen['feasible']
    assert checks['status'] == 'SUCCEEDED' and checks['all_known_joint_regressions_met']
    assert contract['all_passed'] and evaluator['all_passed']
    assert workbook['all_pending'] and workbook['reviewer_blank'] and not workbook['model_inference_executed']
    assert kit['normalized_exact_overlap'] == 0
    lock = load(ROOT / 'config/quality_candidate_asset_lock_v0.8.3.json')
    training_config = load(training / 'training_config.json')
    continued = training_config.get('gradient_method') == 'DETERMINISTIC_FROZEN_PREFIX_CACHE_LAST_BLOCK_BACKPROP'
    training_history_note = ''
    notebook_note = 'Notebook 26 dan 27 beserta salinan `_executed` mencatat eksekusi nyata lewat CPython cell executor.'
    if continued:
        training_history_note = f'''Pelatihan awal notebook 26 menyelesaikan tiga epoch tetapi belum memenuhi
seluruh syarat. Hasil gagal tetap ada. Notebook 26b melanjutkan dari checkpoint
pengembangan tersebut menggunakan cache prefix yang telah dibandingkan dengan
forward penuh. Kandidat terpilih pada epoch {chosen['epoch']} tahap lanjutan.
Pengulangan contoh sulit menghasilkan {training_config['draws_per_epoch']} draw
per epoch dari {state['training_unique']} narasi unik, bukan tambahan data manusia.
Target, cutoff dan cakupan acuan tetap. Tidak ada data FINAL083 yang dibaca
atau digunakan untuk pelatihan maupun seleksi.\n'''
        notebook_note = 'Notebook 26 menyimpan hasil awal yang gagal syarat. Notebook 26b dan 27 beserta salinan `_executed` mencatat pelatihan lanjutan dan verifikasi aktual lewat CPython cell executor.'
        if training_config.get('replay_policy'):
            hard_replay = load(training / 'hard_replay_records.json')
            training_history_note = f'''Notebook 26 menyelesaikan tiga epoch tanpa kandidat yang memenuhi syarat.
Tahap 26b menyelesaikan dua epoch: 40 contoh tambahan sudah benar, tetapi
kontras lama dan sebagian gate NON_EVENT belum lulus. Tahap tersebut dihentikan
saat epoch ketiga untuk memperluas pengulangan. Checkpoint terpilih dan stdout
tetap ada. Berkas `_executed` 26b tidak tersedia setelah interupsi dan tidak
direka ulang sebagai bukti asli.

Notebook 26c melanjutkan dengan {hard_replay['unique_hard_records']} contoh sulit:
kontras yang sudah diketahui, kesalahan NON_EVENT beracuan manusia yang sudah
dilihat, dan 40 contoh tambahan. {training_config['draws_per_epoch']} draw per
epoch berasal dari {state['training_unique']} narasi unik, bukan data manusia
baru. Kandidat terpilih pada epoch {chosen['epoch']} tahap 26c. Cache prefix
dibandingkan dengan forward penuh sebelum gradien. Target dan cutoff tetap.
FINAL083 tidak dibaca untuk pelatihan atau seleksi.\n'''
            notebook_note = 'Notebook 26, 26c dan 27 beserta keluaran `_executed` yang benar-benar tersedia mencatat eksekusi lewat CPython cell executor. Untuk 26b, stdout, skor dua epoch dan catatan interupsi tersedia; keluaran notebook aslinya tidak tersedia.'
    rows = ['| Data yang sudah dilihat | Jumlah | F1 awal | F1 sesudah | Recall NON_EVENT | Recall kejadian minimum |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
    sets = load(training / 'scoring_sets_frozen.json')
    for name, metrics in chosen['metrics'].items():
        rows.append(f"| {name} | {len(sets[name])} | {base['metrics'][name]['macro_f1']:.2%} | {metrics['macro_f1']:.2%} | {metrics['per_class']['NON_EVENT']['recall']:.2%} | {min(metrics['per_class'][c]['recall'] for c in LABELS[:-1]):.2%} |")
    pred = next(r for r in load(training / 'predictions_FINAL082.json') if r['id'] == 'FINAL082-NON_EVENT-02')
    predicted = max(pred['probabilities'], key=pred['probabilities'].get)
    joint_rows = ['| Regresi gabungan | SENA macro F1 | NARA 14-role macro F1 | Exact span F1 | Field nonkosong tepat | Field kosong berlebih | Semua pemeriksaan |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for name in ('human_regression50', 'FINAL081_seen', 'FINAL082_seen'):
        r = load(verification / f'evaluation_{name}.json')
        joint_rows.append(f"| {name} | {r['sena']['macro_f1']:.2%} | {r['nara']['macro_f1_all_14_non_o']:.2%} | {r['nara']['exact_span_f1']:.2%} | {r['fields']['nonempty_exact']:.2%} | {r['fields']['empty_spurious_rate']:.2%} | {'Lulus' if r['metric_targets_met'] else 'Belum'} |")
    date = datetime.now(timezone.utc).astimezone().strftime('%d %B %Y')
    report = f'''# SLR_09 v0.8.3 — hasil kelanjutan 20 Oktober 2026

**Status: In Review.** Pelatihan dan verifikasi ekspor benar-benar selesai di CPU.
Kandidat dipilih pada epoch {chosen['epoch']} dengan {state['training_unique']} narasi unik.
Satu blok encoder terakhir, pooler dan classifier SENA dilatih. NARA dan cutoff
0,95 tetap. Target tidak diturunkan dan tidak ada fitting bias manual baru.

{training_history_note}

Kasus `FINAL082-NON_EVENT-02` yang sebelumnya salah diprediksi ACCIDENT sekarang
diprediksi **{predicted}**, confidence {pred['probabilities'][predicted]:.4%}.
Confidence masih di bawah cutoff 0,95. Flag `LOW_CLASSIFICATION_CONFIDENCE`
tetap aktif dan NON_EVENT tetap memblokir pengiriman; confidence tidak dinaikkan.
Seluruh kontras yang sudah diketahui serta 40 contoh tambahan yang dipakai
melatih kandidat terpenuhi. Ini perbaikan pada data yang telah dilihat.

## Regresi SENA

{chr(10).join(rows)}

Set-set di atas beririsan dan dipakai untuk training atau seleksi. Jumlahnya
tidak boleh dijumlahkan sebagai sampel independen. FINAL081, FINAL082 dan
human130 kini development/training; hasilnya bukan uji penerimaan baru.
Sumber manusia, acuan yang dikembalikan dan hasil uji lama tetap utuh.

## Verifikasi melalui arsip hasil ekspor

Kedua arsip dimuat melalui pemeriksaan hash. Prediksi SENA pada seluruh set
seleksi direproduksi dengan label identik dan selisih probabilitas paling
besar 1e-5. Inferensi gabungan SENA/NARA dijalankan pada 150 narasi regresi.

{chr(10).join(joint_rows)}

{contract['tests_run']}/{contract['tests_run']} tes kontrak dan
{evaluator['tests_run']}/{evaluator['tests_run']} tes evaluator lulus.
{notebook_note} Ini bukan klaim eksekusi kernel Jupyter asli.

## Langkah penerimaan berikutnya

`acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx` memuat 50 narasi baru,
{kit['tokens']} usulan label token, 10 narasi tiap kelas dan seluruh 14 role non-O.
Semuanya **PENDING**, reviewer kosong. Belum ada prediksi pada FINAL083.
Narasi disusun tanpa melihat prediksi model. Nol exact overlap setelah
normalisasi terhadap {kit['known_texts']} teks/fragmen tersedia tidak membuktikan
independensi semantik ataupun keterwakilan laporan lapangan.

Isi reviewer pada Mulai!B5. Periksa kategori, seluruh field dan label token,
lalu tetapkan APPROVED pada tiap ID yang sudah diperiksa atau DEFERRED beserta
alasan. Persetujuan putaran lama tidak mengesahkan acuan baru. Notebook 28
akan memvalidasi review, menyimpan snapshot sumber sebelum pemuatan model,
dan menjalankan uji. Pengguna tidak perlu menjalankan ulang di laptop.

Penerimaan mutu serta Done tetap false. Belum ada push atau deployment.
VM tujuan dan backend submission belum diuji pada run ini.

## Aset dan penyerahan

- SENA baru: `{lock['models']['sena']['archive_name']}`.
- SHA256 arsip SENA: `{lock['models']['sena']['archive_sha256']}`.
- NARA tetap: `{lock['models']['nara']['archive_name']}`; tidak perlu unggah ulang.
- Konfigurasi integrasi v0.8, lock v0.8.3, runtime 0.6.4. Logika adapter/Fusion tetap.
- Checkpoint mencakup sumber dan bukti lengkap, tanpa bobot hasil ekstraksi,
  environment, cache atau bytecode. Arsip SENA disimpan terpisah.
- Overlay dibandingkan dengan checkpoint v0.8.3 yang dipulihkan, bukan ZIP
  GitHub pengguna. Cocokkan basis sebelum penggabungan. Tidak ada penghapusan.
- Dua commit tracking SLR_08 dan suffix nama lokal (3) tetap dikecualikan dari audit.

Bukti utama: `evidence/quality_fix_v083/`. Protokol dan binding kandidat baru
berada di `acceptance/review_bundle_draft.json`. Bukti lama tidak ditulis ulang.
'''
    write(ROOT / 'evidence/quality_fix_v083/completion_summary.json', dict(
        status='SUCCEEDED_ON_KNOWN_REGRESSION', selected_epoch=chosen['epoch'],
        training_unique=state['training_unique'], corrected_FINAL082_NON_EVENT_02=predicted,
        all_known_class_gates_met=True, all_known_contrasts_met=True,
        context40_correct=chosen['metrics']['context40_now_training']['accuracy'] == 1,
        seen_joint_regression_records=150, contract_tests=contract['tests_run'],
        evaluator_tests=evaluator['tests_run'], new_acceptance_records=0,
        next_reference_pending=50, quality_acceptance_approved=False, card_done=False,
        remote_push_executed=False, production_deployed=False))
    (ROOT / 'SLR09_STATUS_v0.8.3.md').write_text(report)
    notes = ROOT / 'Catatan_Kelanjutan_SLR09_2026-10-19.md'
    historical = ROOT / 'historical/Catatan_Kelanjutan_before_v0.8.3.md'
    if not historical.exists():
        shutil.copy2(notes, historical)
    latest_history = ROOT / 'historical/Catatan_Kelanjutan_before_final_v0.8.3.md'
    notes.write_text(report + '\n\n---\n\n# Riwayat sebelum kelanjutan v0.8.3\n\n' + (latest_history if latest_history.exists() else historical).read_text())
    (ROOT / 'README.md').write_text('# SLR_09 v0.8.3\n\nPelatihan konteks dan verifikasi ekspor selesai; seluruh regresi yang diketahui lulus.\nStatus In Review. Acuan FINAL083 50 narasi/685 token menunggu review manusia.\nBaca [hasil dan langkah berikutnya](SLR09_STATUS_v0.8.3.md).\n')
    (ROOT / 'CHECKPOINT_v0.8.3.md').write_text(report)
    old_manifest = ROOT / 'historical/FILE_MANIFEST_before_v0.8.3.json'
    if not old_manifest.exists():
        shutil.copy2(ROOT / 'FILE_MANIFEST.json', old_manifest)
    files = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(ROOT.rglob('*')) if included(p) and p != ROOT / 'FILE_MANIFEST.json']
    write(ROOT / 'FILE_MANIFEST.json', dict(schema='slr09-source-evidence-files-0.8.3',
        revision='0.8.3', manifest_itself_excluded=True, status='IN_REVIEW', weights_included=False,
        new_gradient_training_executed=True, all_known_regressions_met=True,
        new_reference_status='50_PENDING_685_TOKENS_NOT_INFERRED',
        quality_acceptance_approved=False, card_done=False, remote_push_executed=False, files=files))
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / 'SLR09_Checkpoint_Pengerjaan_v0.8.3.zip'
    overlay = output / 'SLR09_Perubahan_dan_Bukti_v0.8.3_20261020.zip'
    with zipfile.ZipFile(source) as original:
        before = {n: hashlib.sha256(original.read(n)).hexdigest()
                  for n in original.namelist() if not n.endswith('/')}
    changed = []
    for p in sorted(ROOT.rglob('*')):
        if not included(p):
            continue
        relative = 'models/slr09/' + p.relative_to(ROOT).as_posix()
        h = sha(p)
        if before.get(relative) == h:
            continue
        changed.append(dict(path=relative, status='MODIFIED' if relative in before else 'NEW',
            expected_previous_sha256=before.get(relative), sha256=h, bytes=p.stat().st_size))
    overlay_manifest = dict(schema='slr09-source-evidence-overlay-0.8.3',
        basis='RECOVERED_V083_WORKING_CHECKPOINT_NOT_USER_GITHUB_ZIP',
        basis_checkpoint_sha256=sha(source), deletions=[], files=changed,
        quality_acceptance_approved=False, production_deployed=False, remote_push_executed=False)
    write(output / 'manifest_overlay_v0.8.3.json', overlay_manifest)
    with zipfile.ZipFile(checkpoint, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('README_RECOVERY.md', report)
        for p in sorted(ROOT.rglob('*')):
            if included(p):
                z.write(p, 'models/slr09/' + p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(overlay, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('README_OVERLAY.md', report)
        z.writestr('manifest_overlay_v0.8.3.json', json.dumps(overlay_manifest, indent=2) + '\n')
        for row in changed:
            z.write(ROOT / Path(row['path']).relative_to('models/slr09'), row['path'])
    for archive in [checkpoint, overlay]:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert not any(n.endswith(('.safetensors', '.bin', '.pyc')) or '/__pycache__/' in n for n in z.namelist())
    for name in ('SLR09_STATUS_v0.8.3.md', 'Catatan_Kelanjutan_SLR09_2026-10-19.md'):
        shutil.copy2(ROOT / name, output / name)
    shutil.copy2(ROOT / 'acceptance/Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx', output / 'Review_Penerimaan_Akhir_SLR09_v0.8.3.xlsx')
    summary = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
               for p in output.iterdir() if p.is_file() and not p.name.startswith('.')
               and p.name != 'delivery_verification_v0.8.3.json'}
    write(output / 'delivery_verification_v0.8.3.json', dict(status='SUCCEEDED', artifacts=summary))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('training', 'verification', 'source', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.training.resolve(), args.verification.resolve(), args.source.resolve(), args.output.resolve())
