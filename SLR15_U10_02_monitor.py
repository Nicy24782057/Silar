#!/usr/bin/env python3
"""Read-only SILAR U10-02 recorder. It never sends an analysis or changes DB rows.

Place next to code/, run with the backend venv. A new saved draft is required for
each measurement. Resource sampling starts BEFORE the user clicks Analisis.
Backend TOTAL excludes some preflight work; HTTP duration is entered separately.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

VERSION = '1.0.0'
TERMINAL = {'SUCCEEDED', 'FAILED'}
RESOURCE_FIELDS = ['time_utc', 'elapsed_s', 'sample_gap_s', 'backend_cpu_pct_machine',
                   'backend_cpu_pct_one_core', 'backend_rss_mib', 'backend_pids',
                   'host_cpu_pct', 'host_ram_used_mib', 'access_errors']


def stamp():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def parse_duration(value):
    s = value.strip().lower().replace(',', '.')
    if not s:
        return None
    multiplier = 1.0
    if s.endswith('ms'):
        s = s[:-2].strip()
    elif s.endswith('s'):
        s = s[:-1].strip()
        multiplier = 1000.0
    number = float(s) * multiplier
    if not math.isfinite(number) or number < 0:
        raise ValueError('Durasi harus angka berhingga dan tidak negatif.')
    return round(number, 3)


def parse_report_id(value):
    matches = re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', value)
    if len(matches) != 1:
        raise ValueError('Tempel satu URL laporan atau UUID lengkap.')
    return str(uuid.UUID(matches[0]))


def signature(evidence):
    # IDs and upload filenames may differ between drafts; content must not.
    payload = sorted((e['type'], e['sha256'], int(e['byte_size'])) for e in evidence)
    return hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()


def process_key(process):
    return process.pid, round(process.create_time(), 3)


def same_process(context, key):
    try:
        return (context.get('pid') == key[0]
                and abs(float(context.get('process_started_at', -10)) - key[1]) < 0.05)
    except (TypeError, ValueError, AttributeError):
        return False


def detect_backend(root, psutil):
    found = {}
    root = os.path.normcase(str(root.resolve()))
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            args = p.info.get('cmdline') or []
            normalized = [a.replace('\\', '/').lower() for a in args]
            if 'runserver' not in normalized or not any(a.rsplit('/', 1)[-1] == 'manage.py' for a in normalized):
                continue
            cwd = os.path.normcase(os.path.realpath(p.cwd()))
            if os.path.commonpath([root, cwd]) != root:
                continue
            found[process_key(p)] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, OSError):
            continue
    return found


class Collector:
    """Samples backend Python processes and descendants, with PID reuse checks.

    RSS is a sum of resident working sets, not private/unique physical memory.
    Peaks are observed at the sampling interval, not guaranteed instantaneous maxima.
    """
    def __init__(self, roots, path, interval, psutil):
        self.roots = dict(roots)
        self.path, self.interval, self.psutil = path, interval, psutil
        self.logical = psutil.cpu_count() or 1
        self.rows, self.errors, self.seen_keys = [], [], set()
        self.stop_event, self.ready = threading.Event(), threading.Event()
        self.thread = None
        self.previous_cpu, self.previous_clock, self.previous_wall = {}, None, None
        self.started = time.perf_counter()
        self.missing_root = False

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(10):
            self.stop()
            raise RuntimeError('Sampler belum siap; jangan jalankan analisis.')
        if self.errors:
            raise RuntimeError('Sampler gagal sebelum analisis: ' + ','.join(self.errors))

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(10)
            if self.thread.is_alive():
                raise RuntimeError('Sampler belum berhenti; periksa file sumber daya.')

    def _sample(self):
        ps = self.psutil
        now, wall = time.perf_counter(), time.time()
        gap = None if self.previous_clock is None else now - self.previous_clock
        processes, current_cpu, rss, delta, denied = {}, {}, 0, 0.0, 0
        alive_roots = 0
        for key, root_process in self.roots.items():
            try:
                if process_key(root_process) != key or not root_process.is_running():
                    continue
                alive_roots += 1
                processes[key] = root_process
                for child in root_process.children(recursive=True):
                    try:
                        processes[process_key(child)] = child
                    except ps.NoSuchProcess:
                        pass
            except ps.NoSuchProcess:
                pass
            except ps.AccessDenied:
                denied += 1
        if alive_roots != len(self.roots):
            self.missing_root = True
        pids = []
        for key, p in processes.items():
            try:
                with p.oneshot():
                    ct = p.cpu_times()
                    cpu = float(ct.user + ct.system)
                    memory = int(p.memory_info().rss)
                current_cpu[key] = cpu
                rss += memory
                pids.append(p.pid)
                self.seen_keys.add(key)
                if key in self.previous_cpu:
                    delta += max(0.0, cpu - self.previous_cpu[key])
                elif self.previous_wall is not None and key[1] >= self.previous_wall - 0.005:
                    delta += cpu
            except ps.NoSuchProcess:
                pass
            except ps.AccessDenied:
                denied += 1
        one_core = None if gap is None or gap <= 0 else 100.0 * delta / gap
        self.previous_cpu, self.previous_clock, self.previous_wall = current_cpu, now, wall
        return {
            'time_utc': stamp(), 'elapsed_s': round(now - self.started, 6),
            'sample_gap_s': None if gap is None else round(gap, 6),
            'backend_cpu_pct_machine': None if one_core is None else round(one_core / self.logical, 4),
            'backend_cpu_pct_one_core': None if one_core is None else round(one_core, 4),
            'backend_rss_mib': round(rss / 1048576, 4),
            'backend_pids': ';'.join(map(str, sorted(pids))),
            'host_cpu_pct': ps.cpu_percent(interval=None),
            'host_ram_used_mib': round(ps.virtual_memory().used / 1048576, 3),
            'access_errors': denied,
        }

    def _run(self):
        try:
            self.psutil.cpu_percent(interval=None)
            with self.path.open('w', newline='', encoding='utf-8-sig') as stream:
                writer = csv.DictWriter(stream, fieldnames=RESOURCE_FIELDS)
                writer.writeheader()
                while not self.stop_event.is_set():
                    row = self._sample()
                    self.rows.append(row)
                    writer.writerow(row)
                    stream.flush()
                    self.ready.set()
                    self.stop_event.wait(self.interval)
        except Exception as exc:
            self.errors.append(type(exc).__name__)
            self.ready.set()

    def summary(self):
        def peak(name):
            vals = [r[name] for r in self.rows if r[name] is not None]
            return max(vals) if vals else None
        return {
            'samples': len(self.rows),
            'cpu_peak_pct_machine_observed': peak('backend_cpu_pct_machine'),
            'rss_peak_mib_observed': peak('backend_rss_mib'),
            'rss_baseline_mib': self.rows[0]['backend_rss_mib'] if self.rows else None,
            'max_sample_gap_s': peak('sample_gap_s'),
            'window_s': self.rows[-1]['elapsed_s'] if self.rows else 0,
            'logical_cpus': self.logical,
            'monitored_pids': sorted({k[0] for k in self.seen_keys}),
            'access_errors': sum(r['access_errors'] for r in self.rows),
            'root_process_changed_or_disappeared': self.missing_root,
            'sampler_errors': self.errors,
        }


class Reader:
    def __init__(self, root):
        sys.path.insert(0, str(root / 'code' / 'backend'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        from django.conf import settings
        from django.db import connection
        from django.utils import timezone as django_timezone
        from core.models import AnalysisRun, EvidenceBundleItem, Report, Transcript
        self.runs, self.items, self.reports, self.transcripts = AnalysisRun, EvidenceBundleItem, Report, Transcript
        self.settings, self.connection, self.now = settings, connection, django_timezone.now
        if connection.vendor != 'postgresql':
            raise RuntimeError('Pencatat ini memerlukan PostgreSQL SILAR.')
        with connection.cursor() as cur:
            cur.execute('SHOW server_version')
            self.postgres = cur.fetchone()[0]

    def active(self):
        return self.runs.objects.filter(status__in=['RUNNING', 'UNKNOWN']).exists()

    def check_draft(self, report_id, route):
        report = self.reports.objects.filter(pk=report_id, deleted_at__isnull=True).first()
        if report is None or report.submitted_at is not None:
            raise ValueError('Gunakan draft baru yang belum dikirim.')
        if self.runs.objects.filter(report_id=report_id).exists():
            raise ValueError('Draft ini sudah punya run. Buat draft baru agar tidak membaca hasil lama.')
        channels = list(report.evidence.values_list('type', flat=True))
        allowed = {'T': 'TEXT', 'A': 'AUDIO', 'I': 'IMAGE'}[route]
        if channels != [allowed]:
            raise ValueError('Draft harus berisi tepat satu bukti pada kanal yang dipilih.')

    def used_process(self, keys, route=None, successful=False):
        for key in keys:
            qs = self.runs.objects.filter(execution_context__pid=key[0])
            if route:
                qs = qs.filter(route=route, mode='EVIDENCE')
            if successful:
                qs = qs.filter(status='SUCCEEDED')
            for context in qs.order_by('-started_at').values_list('execution_context', flat=True)[:100]:
                if same_process(context, key):
                    return True
        return False

    def run(self, report_id):
        fields = ['id', 'report_id', 'bundle_id', 'route', 'mode', 'status', 'stage',
                  'started_at', 'finished_at', 'timings_ms', 'model_versions', 'error_code',
                  'execution_context']
        value = self.runs.objects.filter(report_id=report_id).order_by('-started_at').values(*fields).first()
        if value:
            context = value.pop('execution_context') or {}
            value['backend_pid'] = context.get('pid')
            value['backend_process_started_at'] = context.get('process_started_at')
        return value

    def evidence(self, run):
        result = []
        for item in self.items.objects.filter(bundle_id=run['bundle_id']).select_related('evidence').order_by('position'):
            e = item.evidence
            result.append({'id': str(e.id), 'type': e.type, 'original_name': e.original_name,
                           'byte_size': e.byte_size, 'sha256': e.sha256})
        audio = self.transcripts.objects.filter(analysis_run_id=run['id']).values('duration_ms', 'model_version').first()
        return result, audio


def fmt(value, decimals=2):
    if value is None:
        return '-'
    if isinstance(value, (float, int)):
        return f'{value:.{decimals}f}'
    return str(value)


def report_html(title, headers, rows, notes, detail_headers=None, detail_rows=None):
    esc = lambda value: html.escape(str(value))
    table = '<table><thead><tr>' + ''.join('<th>' + esc(x) + '</th>' for x in headers) + '</tr></thead><tbody>'
    table += ''.join('<tr>' + ''.join('<td>' + esc(x) + '</td>' for x in row) + '</tr>' for row in rows)
    table += '</tbody></table>'
    details = ''
    if detail_headers:
        details = '<details><summary>Lihat seluruh run; data mentah tersedia dalam CSV/JSON</summary><table><thead><tr>'
        details += ''.join('<th>' + esc(x) + '</th>' for x in detail_headers) + '</tr></thead><tbody>'
        details += ''.join('<tr>' + ''.join('<td>' + esc(x) + '</td>' for x in row) + '</tr>' for row in (detail_rows or []))
        details += '</tbody></table></details>'
    return ('<!doctype html><html lang="id"><meta charset="utf-8"><title>' + esc(title) + '</title>'
            '<style>body{font:15px Arial,sans-serif;color:#17212b;margin:24px auto;max-width:1600px;padding:0 20px}'
            'h1{font-size:25px}table{border-collapse:collapse;width:100%;margin:18px 0}th,td{border:1px solid #ccd3da;padding:9px;text-align:left}'
            'th{background:#e8edf2}p{line-height:1.45}code{font-size:13px}</style><h1>' + esc(title) + '</h1>'
            '<p>SLR 15 | U10-02 | Pengukuran lokal Windows | Diperbarui ' + esc(datetime.now().astimezone().isoformat(timespec='seconds')) + '</p>'
            + table + ''.join('<p>' + esc(n) + '</p>' for n in notes) + details + '</html>')


def aggregate(summaries):
    groups = {}
    for s in summaries:
        groups.setdefault((s['session'], s['route'], s['condition']), []).append(s)
    durations, resources = [], []
    for (session, route, condition), values in sorted(groups.items()):
        valid = [s for s in values if s.get('comparable')]
        successful = [s for s in valid if s['status'] == 'SUCCEEDED']
        def numbers(rows, name):
            return [float(s[name]) for s in rows if type(s.get(name)) in (int, float)
                    and math.isfinite(s[name]) and s[name] >= 0]
        total = numbers(successful, 'backend_total_ms')
        http = numbers(successful, 'http_ms')
        cpu = numbers(valid, 'cpu_peak_pct_machine_observed')
        rss = numbers(valid, 'rss_peak_mib_observed')
        gaps = numbers(valid, 'max_sample_gap_s')
        n_success = sum(s['status'] == 'SUCCEEDED' for s in values)
        n_fail = sum(s['status'] == 'FAILED' for s in values)
        n_pending = len(values) - n_success - n_fail
        quality = f"invalid={len(values)-len(valid)}; tanpa hasil terminal={n_pending}; sesi={session.removeprefix('session_')}"
        triplet = ' / '.join(fmt(x) for x in [min(total), statistics.median(total), max(total)]) if total else '-'
        durations.append([route, condition, len(values), n_success, n_fail, len(successful), triplet,
                          fmt(statistics.median(http) if http else None), len(http), quality])
        resources.append([route, condition, len(values), len(valid), fmt(max(cpu) if cpu else None),
                          fmt(max(rss) if rss else None), fmt(max(gaps) if gaps else None, 3), quality])
    return durations, resources


def render_reports(output):
    summaries = []
    for path in sorted(output.glob('session_*/*/summary.json')):
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            if value.get('collector_version') == VERSION:
                summaries.append(value)
        except (OSError, ValueError):
            continue
    fields = ['session', 'route', 'condition', 'trial', 'status', 'run_id', 'report_id',
              'backend_total_ms', 'http_ms', 'cpu_peak_pct_machine_observed', 'rss_peak_mib_observed',
              'samples', 'max_sample_gap_s', 'comparable', 'notes']
    with (output / 'rekap_per_run.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summaries)
    durations, resources = [], []
    for s in summaries:
        label = s['session'].removeprefix('session_')
        common = [s['route'], s['condition'], s['trial'], s['status']]
        durations.append(common + [fmt(s['backend_total_ms']), fmt(s['http_ms']), s['run_id'][:8], label, s['notes'] or '-'])
        resources.append(common + [fmt(s['cpu_peak_pct_machine_observed']), fmt(s['rss_peak_mib_observed']),
                                  s['samples'], fmt(s['max_sample_gap_s'], 3), s['run_id'][:8], s['notes'] or '-'])
    aggregate_duration, aggregate_resources = aggregate(summaries)
    notes = [
        'Run/berhasil/gagal adalah jumlah aktual yang tercatat. Statistik TOTAL dan HTTP hanya memakai run SUCCEEDED yang comparable; nilai kosong dan run gagal tidak dianggap nol.',
        'Awal berarti percobaan pertama yang tercatat setelah restart proses backend. Cache OS dan cache provider eksternal tidak dikendalikan.',
        'TOTAL adalah timer internal pipeline tersimpan; beberapa pekerjaan preflight/pemuatan awal dapat berada di luar timer tersebut. HTTP diisi dari POST analyses pada Network, di luar upload bukti.',
        'Tanda - berarti nilai belum tersedia. Jendela pemantauan sumber daya bukan durasi request. Gunakan metadata dan CSV mentah untuk audit.',
        'Bandingkan input, versi, kondisi, jumlah percobaan, dan catatan validitas sebelum menyimpulkan hasil. Belum ada target penerimaan performa yang ditetapkan oleh pencatat ini.'
    ]
    (output / 'rekap_durasi.html').write_text(report_html('U10-02 Rekap durasi analisis',
        ['Rute', 'Kondisi', 'Run', 'Berhasil', 'Gagal', 'Valid berhasil', 'TOTAL min / median / maks. (ms)', 'HTTP median (ms)', 'n HTTP', 'Catatan'],
        aggregate_duration, notes,
        ['Rute', 'Kondisi', 'Ulangan', 'Status', 'TOTAL backend (ms)', 'HTTP (ms)', 'Run', 'Sesi', 'Catatan'], durations), encoding='utf-8')
    resource_notes = [
        'CPU backend dinormalisasi terhadap jumlah prosesor logis: 100% berarti setara seluruh CPU mesin. Cakupan: proses runserver proyek ini beserta proses turunannya; Chrome, frontend, dan PostgreSQL tidak termasuk metrik backend.',
        'RAM = jumlah RSS/working set proses yang dipantau dalam MiB, bukan unique/private memory. Halaman bersama dapat terhitung lebih dari sekali.',
        'Puncak merupakan nilai maksimum TERAMATI pada interval sampling; lonjakan singkat di antara sampel dapat terlewat. CSV juga menyimpan CPU/RAM host sebagai konteks.',
        'Ringkasan sumber daya mencakup run comparable yang berhasil maupun gagal. Run tidak comparable tetap tersedia di rincian dan data mentah.',
        'Sampel dimulai sebelum klik Analisis untuk mencakup pemuatan awal. Catat proses berubah, akses gagal, jarak antar-sampel, dan keterbatasan lingkungan lokal.'
    ]
    (output / 'rekap_cpu_ram.html').write_text(report_html('U10-02 Rekap CPU dan RAM backend',
        ['Rute', 'Kondisi', 'Run', 'Valid sumber daya', 'CPU puncak teramati (%)', 'RSS puncak teramati (MiB)', 'Gap maks. (s)', 'Catatan'],
        aggregate_resources, resource_notes,
        ['Rute', 'Kondisi', 'Ulangan', 'Status', 'CPU puncak (%)', 'RSS puncak (MiB)', 'Sampel', 'Gap maks. (s)', 'Run', 'Catatan'], resources), encoding='utf-8')
    return summaries


def ask_http():
    while True:
        try:
            return parse_duration(input('Durasi POST analyses dari Network (contoh 1250 ms / 1.25 s; Enter bila belum ada): '))
        except ValueError:
            print('Gunakan angka durasi yang terlihat, dengan ms atau s. Nilai kosong disimpan sebagai belum tersedia.')


def measure(reader, roots, report_id, route, condition, trial, directory, args, psutil):
    directory.mkdir()
    input('Tekan Enter untuk MULAI PENCATATAN, lalu klik Analisis laporan SEKALI di browser. ')
    reader.check_draft(report_id, route)
    start_wall = reader.now()
    collector = Collector(roots, directory / 'resources.csv', args.sample_interval, psutil)
    collector.start()
    run, observation, previous = None, 'WAITING', None
    print('PENCATAT AKTIF. Sekarang klik Analisis laporan. Ctrl+C jika UI gagal dan tidak ada run yang tercatat.')
    try:
        deadline = time.monotonic() + args.wait_seconds
        while time.monotonic() < deadline:
            if collector.errors:
                raise RuntimeError('Sampler gagal: ' + ','.join(collector.errors))
            run = reader.run(report_id)
            if run:
                current = (run['status'], run['stage'])
                if current != previous:
                    print('Run', str(run['id'])[:8], '|', *current)
                    previous = current
                if run['status'] in TERMINAL:
                    observation = run['status']
                    break
                if run['status'] == 'UNKNOWN':
                    observation = 'OBSERVED_UNKNOWN'
                    break
            time.sleep(args.poll_interval)
        else:
            observation = 'OBSERVER_TIMEOUT'
    except KeyboardInterrupt:
        observation = 'USER_STOPPED_OBSERVATION'
        run = reader.run(report_id)
        if run and run['status'] in TERMINAL:
            observation = run['status']
    finally:
        collector.stop()
    stats = collector.summary()
    evidence, audio = reader.evidence(run) if run else ([], None)
    sig = signature(evidence) if evidence else None
    issues = []
    if observation not in TERMINAL:
        issues.append('Pengamatan berakhir: ' + observation)
    if not run:
        issues.append('Tidak ada run teramati; periksa kegagalan preflight/HTTP')
    else:
        if run['started_at'] < start_wall:
            issues.append('Run dimulai sebelum pencatatan')
        if run['route'] != route or run['mode'] != 'EVIDENCE':
            issues.append('Rute atau mode berbeda dari rencana')
        key = (run['backend_pid'], round(float(run['backend_process_started_at'] or -1), 3))
        if key not in collector.seen_keys:
            issues.append('Identitas proses run tidak terpantau')
    if stats['samples'] < 2:
        issues.append('Sampel sumber daya kurang dari dua')
    if stats['access_errors'] or stats['sampler_errors']:
        issues.append('Pembacaan sumber daya tidak lengkap')
    if stats['root_process_changed_or_disappeared']:
        issues.append('Proses backend berubah/hilang saat pencatatan')
    comparable = not issues
    result = {
        'collector_version': VERSION, 'session': directory.parent.name,
        'route': route, 'condition': condition, 'trial': trial,
        'report_id': report_id, 'run_id': str(run['id']) if run else '',
        'status': run['status'] if run else 'NO_RUN_OBSERVED', 'observation': observation,
        'backend_total_ms': (run['timings_ms'] or {}).get('TOTAL') if run else None,
        'http_ms': None, 'input_signature': sig,
        'cpu_peak_pct_machine_observed': stats['cpu_peak_pct_machine_observed'],
        'rss_peak_mib_observed': stats['rss_peak_mib_observed'],
        'samples': stats['samples'], 'max_sample_gap_s': stats['max_sample_gap_s'],
        'comparable': comparable, 'notes': '; '.join(issues),
    }
    dump(directory / 'metadata.json', {'measurement_start_utc': start_wall, 'observation': observation,
         'run': run, 'input_evidence': evidence, 'audio_metadata': audio, 'resource_summary': stats,
         'definitions': {'sample_interval_s': args.sample_interval,
         'cpu_machine_percent': 'one-core equivalent divided by logical CPU count',
         'rss_mib': 'sum of sampled backend process working sets / 1048576',
         'observation_window': 'before user clicks analysis until terminal state observed; not request latency'}})
    dump(directory / 'summary.json', result)
    render_reports(directory.parent.parent)
    # Save first: an interruption while the user reads Network must not lose the run.
    result['http_ms'] = ask_http()
    extra = input('Catatan tambahan atau kode error (Enter jika tidak ada): ').strip()
    if extra:
        result['notes'] = '; '.join(filter(None, [result['notes'], extra]))
    dump(directory / 'summary.json', result)
    print('TERSIMPAN:', directory)
    print('TOTAL backend:', fmt(result['backend_total_ms']), 'ms | CPU teramati:', fmt(result['cpu_peak_pct_machine_observed']),
          '% | RSS teramati:', fmt(result['rss_peak_mib_observed']), 'MiB')
    return result, run


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--route', choices=['T', 'A', 'I'])
    parser.add_argument('--render-only', action='store_true', help='Perbarui HTML/CSV dari data yang sudah tersimpan; tanpa akses DB.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--warm-repeats', type=int, default=3)
    parser.add_argument('--sample-interval', type=float, default=0.2)
    parser.add_argument('--poll-interval', type=float, default=0.5)
    parser.add_argument('--wait-seconds', type=float, default=600)
    args = parser.parse_args()
    if not (1 <= args.warm_repeats <= 30 and 0.05 <= args.sample_interval <= 5
            and 0.1 <= args.poll_interval <= 5 and args.wait_seconds > 0):
        parser.error('Parameter pengulangan/interval tidak sesuai.')
    root = args.root.resolve()
    if not (root / 'code' / 'backend' / 'manage.py').is_file():
        parser.error('Letakkan skrip di folder utama Silar yang berisi code/, atau berikan --root.')
    if args.render_only:
        output = root / 'bukti_uji' / 'SLR15' / 'U10-02'
        if not output.is_dir():
            parser.error('Folder hasil U10-02 belum ada.')
        render_reports(output)
        print('Rekap diperbarui:', output)
        return
    if not args.route:
        parser.error('--route T, A, atau I diperlukan untuk pengukuran baru.')
    import psutil
    reader = Reader(root)
    if reader.active():
        raise RuntimeError('Ada run RUNNING/UNKNOWN. Pastikan keadaan tersimpan sebelum benchmark baru.')
    roots = detect_backend(root, psutil)
    if not roots:
        raise RuntimeError('Backend runserver proyek ini belum terdeteksi. Jalankan backend --noreload dahulu.')
    if reader.used_process(roots):
        raise RuntimeError('Proses backend sudah pernah menganalisis. Restart backend --noreload untuk percobaan awal rute ini.')
    output = root / 'bukti_uji' / 'SLR15' / 'U10-02'
    output.mkdir(parents=True, exist_ok=True)
    session = output / ('session_' + args.route + '_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6])
    session.mkdir()
    git = subprocess.run(['git', '-C', str(root), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, check=False)
    dump(session / 'environment.json', {
        'collector_version': VERSION, 'started_utc': stamp(), 'platform': platform.platform(),
        'logical_cpus': psutil.cpu_count(), 'ram_total_bytes': psutil.virtual_memory().total,
        'postgresql': reader.postgres, 'commit': git.stdout.strip() if git.returncode == 0 else None,
        'backend_processes_initial': [{'pid': k[0], 'process_started_at': k[1]} for k in roots],
        'route': args.route, 'warm_repeats_planned': args.warm_repeats,
        'sample_interval_s': args.sample_interval, 'db_poll_interval_s': args.poll_interval,
        'analysis_capacity': reader.settings.ANALYSIS_CAPACITY,
        'ai_cpu_threads': reader.settings.AI_CPU_THREADS,
        'gemini_timeout_ms': reader.settings.GEMINI_TIMEOUT_MS,
        'analysis_deadline_seconds': reader.settings.ANALYSIS_DEADLINE_SECONDS,
        'scope': 'LOCAL_BACKEND_PROCESS_TREE; NOT_TARGET_VM_BENCHMARK'})
    print('\nU10-02 | Rute', args.route, '| 1 awal +', args.warm_repeats, 'hangat')
    print('Hanya membaca DB dan proses; analisis dijalankan MANUAL di browser.')
    print('Gunakan draft BARU per percobaan dan bukti dengan isi/berkas yang SAMA.')
    print('Sesi:', session)
    first_signature, first_models, anchor = None, None, None
    for index in range(args.warm_repeats + 1):
        condition, trial = ('awal', 1) if index == 0 else ('hangat', index)
        current_roots = detect_backend(root, psutil)
        if set(current_roots) != set(roots):
            print('Backend berubah. Sesi dihentikan; hasil yang ada tetap tersimpan.')
            break
        if index > 0 and (not anchor or not reader.used_process([anchor], route=args.route, successful=True)):
            print('Belum ada keberhasilan pada proses/rute yang sama untuk dasar kondisi hangat.')
            break
        print('\nPERCOBAAN:', args.route, condition, trial)
        while True:
            try:
                report_id = parse_report_id(input('Siapkan draft baru, simpan satu bukti, lalu tempel URL laporan: '))
                reader.check_draft(report_id, args.route)
                if reader.active():
                    raise ValueError('Masih ada run RUNNING/UNKNOWN. Periksa keadaan tersimpan dahulu.')
                break
            except ValueError as exc:
                print(exc)
        directory = session / f'{condition}_{trial:02d}'
        result, run = measure(reader, roots, report_id, args.route, condition, trial, directory, args, psutil)
        models = run['model_versions'] if run else None
        if index == 0:
            first_signature, first_models = result['input_signature'], models
            if run:
                anchor = (run['backend_pid'], round(float(run['backend_process_started_at'] or -1), 3))
        else:
            extra = []
            if result['input_signature'] != first_signature:
                extra.append('Input berbeda dari percobaan awal')
            # Provider metadata may include per-call token counts; compare model identity instead.
            def identity(value):
                value = dict(value or {})
                gemini = value.get('gemini')
                if isinstance(gemini, dict):
                    value['gemini'] = {k: gemini.get(k) for k in ['requested_model', 'resolved_model', 'sdk_version']}
                return value
            if identity(models) != identity(first_models):
                extra.append('Identitas model berbeda dari percobaan awal')
            if extra:
                result['comparable'] = False
                result['notes'] = '; '.join(filter(None, [result['notes'], *extra]))
                dump(directory / 'summary.json', result)
        render_reports(output)
        if not run or run['status'] not in TERMINAL or (index == 0 and run['status'] != 'SUCCEEDED'):
            print('Sesi dihentikan untuk pemeriksaan hasil awal/keadaan proses. Tidak ada retry otomatis.')
            break
    print('\nBuka untuk screenshot:')
    print(output / 'rekap_durasi.html')
    print(output / 'rekap_cpu_ram.html')
    print('Kirim rekap_per_run.csv dan folder sesi berisi metadata/CSV mentah untuk penilaian.')
    reader.connection.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nPencatat dihentikan pengguna. Hasil yang selesai tetap tersimpan.')
    except Exception as exc:
        print(f'PENCATAT BERHENTI ({type(exc).__name__}): {exc}', file=sys.stderr)
        sys.exit(1)
