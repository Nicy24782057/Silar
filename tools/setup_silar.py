"""One local setup entry point, including backend, AI packages and frontend."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/'code/backend'
sys.path.insert(0,str(ROOT))

def backend_python():
    import os
    return BACKEND/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def run(args):
    subprocess.run([str(value) for value in args],cwd=ROOT,check=True)

def main(argv=None):
    parser=argparse.ArgumentParser(description='Siapkan SILAR lokal secara lengkap, atau periksa lingkungan yang sudah ada.')
    parser.add_argument('--check',action='store_true',help='Hanya periksa lingkungan; tidak memasang paket atau mengubah database.')
    args=parser.parse_args(argv)
    try:
        executable=backend_python()
        if args.check:
            if not executable.exists():raise RuntimeError('Venv backend belum tersedia. Jalankan setup tanpa --check dengan Python 3.12.')
            run([executable,BACKEND/'check_environment.py','--database'])
            return 0
        if sys.version_info[:2]!=(3,12):raise RuntimeError('Setup lengkap memerlukan Python 3.12. Jalankan: py -3.12 tools/setup_silar.py')
        if executable.exists():
            version=subprocess.run([str(executable),'-c','import sys; print("%d.%d" % sys.version_info[:2])'],capture_output=True,text=True,check=True).stdout.strip()
            if version!='3.12':raise RuntimeError('Venv yang ada bukan Python 3.12. Pertahankan .env/database/model dan siapkan venv Python 3.12 sebelum melanjutkan.')
        if not (BACKEND/'.env').exists():
            print('Tahap 1/3: membuat konfigurasi dan database lokal baru. PostgreSQL 16 harus sudah berjalan.',flush=True)
            run([sys.executable,BACKEND/'scripts/setup_local.py'])
        else:print('Tahap 1/3: memakai konfigurasi lokal yang sudah ada.',flush=True)
        print('Tahap 2/3: memasang paket backend/AI, decoder dan frontend. Aset model disiapkan terpisah.',flush=True)
        from tools.setup_slr10 import prepare_project
        if prepare_project()!=0:return 1
        print('Tahap 3/3: memeriksa paket, decoder dan koneksi PostgreSQL.',flush=True)
        run([backend_python(),BACKEND/'check_environment.py','--database'])
        print('\nSetup paket dan aplikasi selesai. Lihat PANDUAN_RUNNING.md untuk menjalankan dua server dan menyiapkan model/email SMTP.')
        return 0
    except (RuntimeError,OSError,subprocess.CalledProcessError) as error:
        if isinstance(error,RuntimeError):print(str(error))
        else:print('Setup belum selesai. Periksa pesan langkah yang gagal di atas. Konfigurasi dan database tidak direset.')
        return 1

if __name__=='__main__':raise SystemExit(main())
