"""Write current status from completed actual evidence, keeping prior history."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from train_sena_cpu import write

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def percentage(value):
    return f'{100 * value:.2f}%'.replace('.', ',')


def build(run):
    state = load(run / 'run_state.json')
    baseline = load(run / 'baseline_evaluation.json')
    history = load(run / 'training_history.json')
    selected = load(run / 'best_selection.json')
    tests = load(ROOT / 'evidence/quality_fix_v083/unit_test_results.json')
    if state['status'] not in {'SUCCEEDED', 'FAILED', 'NO_FEASIBLE_CANDIDATE'}:
        raise ValueError('The training run has not finished')
    feasible = selected['feasible'] and state.get('all_known_constraints_met', False)
    moment = datetime.now(timezone.utc).isoformat()
    heading = ('Pelatihan selesai dan seluruh gerbang regresi SENA terpenuhi; penerimaan baru masih diperlukan.'
               if feasible else
               'Pelatihan selesai, tetapi tidak ada kandidat yang memenuhi seluruh gerbang regresi. Kandidat aktif tidak diganti.')
    names = dict(human130='Manusia 130', original146='Label sumber 146',
                 adjudicated145='Adjudikasi 145', scope50='Usulan v0.6: 50',
                 seen_v07_50='Usulan v0.7: 50', human_regression50='Regresi manusia: 50',
                 FINAL081='FINAL081', FINAL082='FINAL082', context40_now_training='Konteks tambahan: 40')
    lines = [
        '# SILAR SLR_09: kelanjutan v0.8.3, 20 Oktober 2026', '',
        '**Status: In Review.** ' + heading, '',
        f'Notebook 26 benar-benar menjalankan {len(history)} putaran dengan {state["training_unique"]} narasi unik. '
        'Satu blok encoder terakhir, pooler dan classifier SENA dilatih. '
        'NARA tidak dilatih ulang. Cutoff tetap **0,95**, target mutu tidak diturunkan, dan acuan lama tidak diganti.', '',
        '## Hasil diagnostik terpilih', '',
        f'Putaran terpilih menurut kriteria sebelum training: **{selected["epoch"]}**. '
        + ('Ini kandidat pengembangan, belum model yang diterima.' if feasible else
           'Checkpoint ini disimpan hanya untuk diagnosis dan pemulihan eksperimen, bukan sebagai kandidat yang telah lulus.'), '',
        '| Data yang sudah dilihat | Macro F1 awal | Macro F1 terpilih | Recall NON_EVENT terpilih | Recall kejadian minimum | Kontras salah |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for name, metrics in selected['metrics'].items():
        minimum = min(v['recall'] for key, v in metrics['per_class'].items() if key != 'NON_EVENT')
        lines.append(f'| {names[name]} | {percentage(baseline["metrics"][name]["macro_f1"])} | '
                     f'{percentage(metrics["macro_f1"])} | {percentage(metrics["per_class"]["NON_EVENT"]["recall"])} | '
                     f'{percentage(minimum)} | {len(selected["contrast_errors"][name])} |')
    correct_before = round(baseline['metrics']['context40_now_training']['accuracy'] * 40)
    correct_after = round(selected['metrics']['context40_now_training']['accuracy'] * 40)
    lines += ['', f'Konteks tambahan: **{correct_before}/40** benar pada bobot awal, '
              f'**{correct_after}/40** pada checkpoint diagnostik terpilih. '
              'Syarat eksperimen adalah 40/40, selain macro F1 >=85%, recall NON_EVENT >=90%, '
              'recall setiap kelas kejadian >=80%, dan seluruh kontras pada setiap kelompok data benar.', '',
              '| Putaran aktual | Durasi training dan evaluasi | Regresi terhadap prediksi awal pada kelompok beririsan | Konteks 40 benar | Semua syarat |',
              '| --- | ---: | ---: | ---: | --- |']
    for item in history:
        lines.append(f'| {item["epoch"]} | {item["seconds"]:.1f} detik | '
                     f'{item["regressions_with_overlapping_sets"]} | '
                     f'{round(item["metrics"]["context40_now_training"]["accuracy"]*40)}/40 | '
                     + ('Terpenuhi |' if item['feasible'] else 'Belum |'))
    failures = []
    for name in selected['metrics']:
        for row in load(run / f'predictions_{name}.json'):
            guess, confidence = max(row['probabilities'].items(), key=lambda item: item[1])
            if guess != row['gold']:
                failures.append(dict(group=name, id=row['id'], text=row['text'], gold=row['gold'],
                                     prediction=guess, confidence=confidence,
                                     low_confidence=confidence < 0.95))
    critical = [row for row in failures if row['id'] == 'FINAL082-NON_EVENT-02']
    if critical:
        row = critical[0]
        lines += ['', 'Kasus yang menghambat penerimaan sebelumnya masih salah:', '',
                  f'- ID `{row["id"]}`: acuan `{row["gold"]}`, prediksi `{row["prediction"]}`, '
                  f'confidence {percentage(row["confidence"])}.',
                  f'- Narasi: “{row["text"]}”',
                  '- Flag confidence rendah (<0,95): ' + ('Ya.' if row['low_confidence'] else 'Tidak.') +
                  ' Kelas yang salah tetap gagal pada syarat kontras.']
    lines += ['', '## Bukti dan batas hasil', '',
              '- Seluruh kelompok ini adalah training/development atau regresi yang sudah dilihat. '
              'Human130, FINAL081 dan FINAL082 kini dipakai untuk gradient; jangan disebut held-out atau penerimaan baru.',
              '- Sumber manusia asli, acuan yang sudah direview, keluaran historis dan label sebelumnya dipertahankan. '
              'Berkas retirement mencatat perubahan peran data sebelum gradient.',
              '- Kelompok data saling beririsan. Hitungan regresi dan kesalahan antarkelompok bukan jumlah narasi unik.',
              '- Label 104 contoh konteks tambahan berasal dari asisten. '
              'Angka pada contoh tersebut bukan persetujuan anotasi manusia atau estimasi populasi laporan lapangan.',
              '- Notebook memakai CPython cell executor. Salinan `_executed.ipynb` memuat stdout dan '
              'exception aktual; bukan klaim eksekusi kernel Jupyter asli.',
              '- Ketika tak ada checkpoint feasible, CLI menolak ekspor kandidat dan workflow berakhir FAILED '
              'karena gerbang mutu. Ini tidak berarti gradient tidak berjalan.', '',
              '## Pemeriksaan kode', '',
              '| Suite | Tes | Hasil |', '| --- | ---: | --- |']
    for suite in tests['suites']:
        lines.append(f'| {suite["suite"]} | {suite["tests"]} | '
                     + ('Lulus |' if suite['returncode'] == 0 else 'Gagal |'))
    lines += ['', 'Tes tersebut memeriksa kontrak/runtime/evaluator dengan fixture. '
              'Tes tidak membuktikan ketepatan model neural. Nama berkas pada fixture pengujian kini '
              'mengikuti konstanta selector, sementara penolakan hash yang tidak cocok tetap diuji.', '',
              '## Kelanjutan yang diperlukan', '']
    if feasible:
        lines += ['Bekukan kandidat yang telah diverifikasi, lalu gunakan acuan penerimaan baru '
                  'yang direview sebelum inferensi. Review dan persetujuan lama tidak mengesahkan narasi baru. '
                  'Notebook 28 menolak kandidat/acuan yang tidak sesuai; tidak boleh dijalankan pada template PENDING.']
    else:
        lines += ['Jangan mempromosikan checkpoint diagnostik ini. Putaran satu sampai tiga belum '
                  'memenuhi batas yang ditetapkan. Perbaikan selanjutnya perlu mengatasi pertukaran '
                  'antara kejadian nyata yang diblokir dan simulasi yang dianggap kejadian, dengan '
                  'mempertahankan target dan kasus lama. Data yang sudah terlihat tetap development.',
                  '', 'Tidak dibuat workbook penerimaan baru dan tidak dijalankan notebook 27/28 pada tahap ini. '
                  'Sumber helper untuk verifikasi dan kit lanjutan disimpan, tetapi belum diaktifkan. '
                  'Notebook 28 menolak selector kandidat lama. Acuan penerimaan baru digunakan '
                  'setelah kandidat pengembangan memenuhi pemeriksaan.']
    lines += ['', '## Berkas dan penyerahan', '',
              '- `notebooks/26_Perbaikan_Konteks_SENA_v0.8.3_executed.ipynb`: eksekusi dan hasil nyata.',
              f'- `{run.relative_to(ROOT).as_posix()}/`: konfigurasi, data beku, retirement, '
              'probabilitas awal, riwayat, pemilihan dan prediksi terpilih.',
              '- `results/continuation_v083/`: Excel hasil dan pemeriksaan workbook.',
              '- `FILE_MANIFEST.json`: ukuran/hash sumber dan bukti versi ini; bobot terpisah.',
              '- Paket perubahan hanya dibandingkan dengan checkpoint v0.8.3 sebelum eksekusi, '
              'belum dengan ZIP repository GitHub pengguna.',
              '- Tidak ada push, deployment, penghapusan, perubahan Kanban atau penetapan model produksi. '
              'Dua commit tracking SLR_08 dan akhiran nama lokal `(3)` tetap dikecualikan dari audit.', '',
              f'Disusun dari bukti aktual pada {moment}.', '']
    document = '\n'.join(lines)
    (ROOT / 'SLR09_STATUS_v0.8.3.md').write_text(document)
    (ROOT / 'CHECKPOINT_v0.8.3.md').write_text(document)
    history_path = ROOT / 'historical/README_before_v0.8.3_execution.md'
    if not history_path.exists():
        shutil.copy2(ROOT / 'README.md', history_path)
    (ROOT / 'README.md').write_text(document)
    note_path = ROOT / 'Catatan_Kelanjutan_SLR09_2026-10-19.md'
    previous = note_path.read_text()
    if previous.startswith('# SILAR SLR_09: kelanjutan v0.8.3'):
        raise ValueError('Do not duplicate a status prefix')
    note_path.write_text(document + '\n---\n\n# Riwayat sebelum eksekusi v0.8.3\n\n' + previous)
    write(ROOT / 'RECOVERY_v0.8.3.json', dict(
        schema='slr09-continuation-recovery-0.8.3', status='IN_REVIEW',
        actual_training_status=state['status'], training_executed=state['training_executed'],
        epochs_completed=len(history), selected_diagnostic_epoch=selected['epoch'],
        known_constraints_met=feasible,
        run_directory=run.relative_to(ROOT).as_posix(),
        executed_notebook='notebooks/26_Perbaikan_Konteks_SENA_v0.8.3_executed.ipynb',
        independent_acceptance_executed=False, quality_acceptance_approved=False,
        card_done=False, confidence_threshold=0.95, nara_weights_changed=False,
        remote_push_executed=False, production_deployed=False,
        next_action='NEW_REVIEWED_ACCEPTANCE_AFTER_CANDIDATE_FREEZE' if feasible
                    else 'QUALITY_IMPROVEMENT_REQUIRED_DO_NOT_PROMOTE_DIAGNOSTIC_WEIGHTS'))
    write(ROOT / 'evidence/quality_fix_v083/selected_errors.json', dict(
        selected_diagnostic_epoch=selected['epoch'],
        group_errors_may_overlap=True, records=failures,
        independent_acceptance_executed=False))
    print(json.dumps(dict(status='WRITTEN', training_status=state['status'],
                         known_constraints_met=feasible, error_rows=len(failures)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    arguments = parser.parse_args()
    build(arguments.run.resolve())
