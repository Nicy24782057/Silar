"""Prepare the existing local Windows project, without resetting its database."""
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'code/backend'
FRONTEND = ROOT / 'code/frontend'


def run(args, cwd=ROOT):
    print('Menjalankan:', Path(args[0]).name, ' '.join(str(x) for x in args[1:] if 'password' not in str(x).lower()), flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)


def refresh_windows_path():
    if os.name != 'nt':
        return
    import winreg
    parts = [os.environ.get('PATH', '')]
    for hive, key in [(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
                      (winreg.HKEY_CURRENT_USER, r'Environment')]:
        try:
            with winreg.OpenKey(hive, key) as handle:
                parts.append(os.path.expandvars(winreg.QueryValueEx(handle, 'Path')[0]))
        except OSError:
            pass
    os.environ['PATH'] = os.pathsep.join(parts)


def configure_env(env_path, decoder=None, probe=None):
    text = env_path.read_text(encoding='utf-8-sig')
    values = {}
    for line in text.splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    if values.get('SILAR_LOCAL_MODE', '').lower() not in ('1', 'true', 'yes'):
        raise ValueError('Setup SLR_10 hanya untuk .env SILAR_LOCAL_MODE=true. Konfigurasi nonlokal tidak diubah.')
    changes = {'FRONTEND_URL': 'http://localhost:5173', 'FRONTEND_VERIFY_PATH': '/verify-email',
               'FRONTEND_ACTIVATE_PATH': '/activate-operator', 'FRONTEND_RESET_PATH': '/reset-password'}
    for key in ('CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS'):
        current = [x.strip() for x in values.get(key, '').split(',') if x.strip()]
        if 'http://localhost:5173' not in current:
            current.append('http://localhost:5173')
        changes[key] = ','.join(current)
    if decoder and probe:
        changes.update(FFMPEG_BINARY=str(decoder), FFPROBE_BINARY=str(probe))
    lines = text.splitlines()
    seen = set()
    for i, line in enumerate(lines):
        if '=' in line and not line.lstrip().startswith('#'):
            key = line.split('=', 1)[0].strip()
            if key in changes:
                value = changes[key].replace('\\', '/')
                lines[i] = key + '="' + value + '"'
                seen.add(key)
    for key, value in changes.items():
        if key not in seen:
            lines.append(key + '="' + value.replace('\\', '/') + '"')
    new = '\n'.join(lines) + '\n'
    if new != text:
        backup = ROOT / '.slr10-backups' / ('env-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(env_path, backup / 'backend.env')
        env_path.write_text(new, encoding='utf-8')
    print('Origin frontend lokal diselaraskan; koneksi database dan rahasia akun dipertahankan.')


def main():
    try:
        ignore = ROOT / '.gitignore'
        text = ignore.read_text() if ignore.exists() else ''
        if '.slr10-backups/' not in text:
            ignore.write_text(text + '\n.slr10-backups/\n')
        env_path = BACKEND / '.env'
        if not env_path.exists():
            raise ValueError('Konfigurasi backend belum ada. Ikuti bagian instalasi baru pada PANDUAN_RUNNING.md; gunakan PostgreSQL 16 dan port lokal yang benar.')
        executable = BACKEND / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not executable.exists():
            venv.create(BACKEND / '.venv', with_pip=True)
        refresh_windows_path()
        decoder, probe = shutil.which('ffmpeg'), shutil.which('ffprobe')
        if (not decoder or not probe) and os.name == 'nt' and shutil.which('winget'):
            print('Menyiapkan decoder audio FFmpeg untuk rekaman browser dan upload audio.')
            subprocess.run(['winget', 'install', '--exact', '--id', 'Gyan.FFmpeg', '--source', 'winget',
                            '--accept-source-agreements', '--accept-package-agreements'], check=False)
            refresh_windows_path()
            decoder, probe = shutil.which('ffmpeg'), shutil.which('ffprobe')
        configure_env(env_path, decoder, probe)
        requirements = ['-r', 'requirements-slr10.txt']
        if (BACKEND / 'requirements-ai.txt').exists():
            requirements += ['-r', 'requirements-ai.txt']
            print('Memeriksa dependensi SLR_10 dan SLR_11 dalam satu resolver.')
        run([executable, '-m', 'pip', 'install', *requirements], BACKEND)
        run([executable, 'manage.py', 'check'], BACKEND)
        run([executable, 'manage.py', 'migrate', '--noinput'], BACKEND)
        run([executable, 'manage.py', 'bootstrap_silar'], BACKEND)
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if npm:
            run([npm, 'ci', '--ignore-scripts', '--no-fund', '--no-audit'], FRONTEND)
            run([npm, 'run', 'build'], FRONTEND)
        elif (FRONTEND / 'dist/index.html').exists():
            print('Memakai build Vue bawaan. Node.js/npm diperlukan saat mengubah atau membangun ulang frontend.')
        else:
            raise ValueError('Pasang Node.js LTS, lalu jalankan kembali setup untuk membangun frontend.')
        if not decoder or not probe:
            print('Catatan: FFmpeg belum terbaca. WAV PCM dapat dipakai; audio lain menunggu decoder. Pasang FFmpeg lalu jalankan ulang setup.')
        print('\nPersiapan selesai. Ikuti bagian menjalankan backend dan frontend pada PANDUAN_RUNNING.md; gunakan dua terminal.')
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('Persiapan belum selesai:', str(error))
        return 1


if __name__ == '__main__':
    sys.exit(main())
