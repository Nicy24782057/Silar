"""Read-only local readiness checks; never display credentials or send email."""
import argparse
from importlib import import_module, metadata
from pathlib import Path
import re
import shutil
import subprocess
import sys
import os

BACKEND=Path(__file__).resolve().parent

def package_requirements():
    required={}
    for filename in ('requirements.txt','requirements-ai.txt'):
        for line in (BACKEND/filename).read_text().splitlines():
            match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s#]+)',line.strip())
            if match:required[match[1]]=match[2]
    return required

def check_packages(required=None):
    problems=[]
    for name,expected in (required or package_requirements()).items():
        try:actual=metadata.version(name)
        except metadata.PackageNotFoundError:actual=None
        if actual!=expected:problems.append(f'{name}: '+('belum terpasang' if actual is None else f'versi {actual}; diperlukan {expected}'))
    for module in ('av','numpy','psutil'):
        try:import_module(module)
        except Exception as error:problems.append(f'{module}: gagal dimuat ({type(error).__name__})')
    return problems

def check_decoders():
    problems=[]
    for variable,default in [('FFMPEG_BINARY','ffmpeg'),('FFPROBE_BINARY','ffprobe')]:
        executable=shutil.which(os.getenv(variable,default))
        if not executable:problems.append(f'{default}: belum terbaca; pasang FFmpeg/FFprobe lalu ulangi setup')
        else:
            try:subprocess.run([executable,'-version'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=True)
            except (OSError,subprocess.SubprocessError):problems.append(f'{default}: ditemukan tetapi belum dapat dijalankan')
    return problems

def main(argv=None):
    parser=argparse.ArgumentParser(description='Periksa lingkungan SILAR tanpa menulis konfigurasi atau data.')
    parser.add_argument('--database',action='store_true')
    args=parser.parse_args(argv)
    problems=[]
    if sys.version_info[:2]!=(3,12):problems.append('Python: gunakan versi 3.12 untuk paket aplikasi ini')
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND/'.env',override=False)
    except ImportError:problems.append('python-dotenv: belum tersedia')
    problems.extend(check_packages())
    problems.extend(check_decoders())
    if args.database:
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
            import django
            django.setup()
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            with connection.cursor() as cursor:
                cursor.execute('SHOW server_version_num')
                if int(cursor.fetchone()[0])//10000!=16:problems.append('Database: PostgreSQL mayor 16 diperlukan')
            executor=MigrationExecutor(connection)
            if executor.migration_plan(executor.loader.graph.leaf_nodes()):problems.append('Database: masih ada migration yang belum diterapkan')
        except Exception as error:problems.append(f'Database/konfigurasi belum dapat diperiksa ({type(error).__name__}); periksa .env dan server PostgreSQL 16')
        finally:
            try:
                from django.db import connections
                connections.close_all()
            except Exception:pass
    for problem in problems:print('BELUM SIAP — '+problem)
    if problems:
        print('Pemeriksaan gagal. Jalankan setup lengkap atau perbaiki komponen yang disebut di atas.')
        return 1
    print('LULUS — versi Python, paket backend/AI, impor pembaca audio dan decoder'+(', PostgreSQL 16 serta migration' if args.database else ''))
    if os.getenv('EMAIL_MODE','smtp')=='file':print('EMAIL — mode berkas lokal; pesan tersedia di private_outbox, belum dikirim ke Gmail.')
    elif not all(os.getenv(key,'').strip() for key in ('EMAIL_HOST','EMAIL_HOST_USER','EMAIL_HOST_PASSWORD')):print('EMAIL — SMTP belum lengkap. Ikuti panduan pengiriman ke Gmail; tidak ada email uji yang dikirim oleh pemeriksaan ini.')
    else:print('EMAIL — konfigurasi SMTP tersedia; pengiriman belum diuji oleh pemeriksaan ini.')
    print('AI — paket tersedia. Inferensi belum diuji di sini; siapkan aset SENA/NARA/Whisper dan konfigurasi Gemini mengikuti panduan.')
    return 0

if __name__=='__main__':raise SystemExit(main())
