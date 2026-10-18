"""Interactive local setup. Creates a new database; never deletes an existing one."""
from pathlib import Path
import getpass,os,re,secrets,subprocess,sys,venv

BACKEND=Path(__file__).resolve().parents[1]
VENV=BACKEND/'.venv'
PYTHON=VENV/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def run(*args):subprocess.run([str(a) for a in args],cwd=BACKEND,check=True)
def prompt(label,default):
    value=input(f'{label} [{default}]: ').strip()
    return value or default
def valid_identifier(value):return re.fullmatch(r'[a-z][a-z0-9_]{0,47}',value) is not None

def create_environment():
    from dotenv import dotenv_values
    import psycopg
    from psycopg import sql
    target=BACKEND/'.env'
    if target.exists():
        print('.env sudah ada; konfigurasi dan database dipertahankan.')
        values=dotenv_values(target)
        if values.get('SILAR_LOCAL_MODE','').lower() not in ('1','true','yes'):
            raise RuntimeError('Setup ini hanya untuk mode lokal. Gunakan prosedur deployment terpisah.')
        return
    print('PostgreSQL 16 harus sudah terpasang dan servicenya berjalan.')
    host=prompt('Host PostgreSQL','127.0.0.1')
    if host not in ('localhost','127.0.0.1'):
        raise RuntimeError('Setup otomatis ini khusus database lokal localhost.')
    port=prompt('Port PostgreSQL','5432')
    if not port.isdigit() or not 1<=int(port)<=65535:raise RuntimeError('Port tidak sah.')
    admin=prompt('Username administrator PostgreSQL','postgres')
    password=getpass.getpass('Password administrator PostgreSQL (tidak disimpan): ')
    with psycopg.connect(host=host,port=port,user=admin,password=password,dbname='postgres',autocommit=True,connect_timeout=8) as connection:
        version=int(connection.execute('SHOW server_version_num').fetchone()[0])
        if version//10000!=16:raise RuntimeError('Acuan SILAR memerlukan PostgreSQL mayor 16.')
        while True:
            database=prompt('Nama database BARU','silar_local')
            role=prompt('Nama role database BARU',database+'_app')
            if not valid_identifier(database) or not valid_identifier(role):
                print('Gunakan huruf kecil, angka, underscore; diawali huruf; maksimal 48 karakter.');continue
            if connection.execute('SELECT 1 FROM pg_database WHERE datname=%s',[database]).fetchone() or connection.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',[role]).fetchone():
                print('Database/role sudah ada. Pilih nama baru; tidak ada yang ditimpa atau dihapus.');continue
            break
        app_password=secrets.token_urlsafe(36)
        # CREATEDB is local-only so Django can create an isolated test_<name> DB.
        connection.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} CREATEDB').format(sql.Identifier(role),sql.Literal(app_password)))
        try:
            connection.execute(sql.SQL('CREATE DATABASE {} OWNER {} ENCODING {} TEMPLATE template0').format(sql.Identifier(database),sql.Identifier(role),sql.Literal('UTF8')))
        except Exception:
            connection.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
            raise
    text=(BACKEND/'.env.example').read_text(encoding='utf-8')
    replacements={'SECRET_KEY':secrets.token_urlsafe(48),'JWT_SIGNING_KEY':secrets.token_urlsafe(48),
        'OTP_HMAC_KEY':secrets.token_urlsafe(48),'DB_NAME':database,'DB_USER':role,
        'DB_PASSWORD':app_password,'DB_HOST':host,'DB_PORT':port,'DEBUG':'false'}
    lines=[]
    for line in text.splitlines():
        key=line.split('=',1)[0]
        lines.append(key+'='+replacements[key] if key in replacements else line)
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:stream.write('\n'.join(lines)+'\n')
    for directory in ('private_media','private_outbox','model_assets'):
        path=BACKEND/directory;path.mkdir(mode=0o700,exist_ok=True);os.chmod(path,0o700)
    print('Database baru dan .env lokal tersedia; rahasia dibuat acak.')

def main():
    if sys.version_info[:2] not in ((3,12),(3,13)):
        raise RuntimeError('Gunakan Python 3.12 atau 3.13. Paket diuji pada Python 3.12.')
    if '--inside-venv' not in sys.argv:
        if not PYTHON.exists():
            print('Membuat virtual environment lokal...',flush=True);venv.EnvBuilder(with_pip=True).create(VENV)
        run(PYTHON,'-m','pip','install','-r',BACKEND/'requirements.txt')
        run(PYTHON,Path(__file__).resolve(),'--inside-venv')
        return
    create_environment()
    run(PYTHON,'manage.py','check')
    run(PYTHON,'manage.py','migrate','--noinput')
    run(PYTHON,'manage.py','bootstrap_silar')
    print('\nSetup selesai. Buat Admin pilihan sendiri:')
    print('.venv\\Scripts\\python.exe manage.py create_silar_admin' if os.name=='nt' else '.venv/bin/python manage.py create_silar_admin')
    print('Jalankan backend di http://localhost:8001; lihat MULAI_DI_SINI.txt dan docs/backend/README.md.')

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nSetup dibatalkan. Tidak ada database lama yang dihapus.');sys.exit(1)
    except subprocess.CalledProcessError as error:print(f'Langkah setup gagal (exit {error.returncode}). Periksa pesan di atas.');sys.exit(1)
    except Exception as error:
        # Never echo database connection strings, passwords, or environment values.
        if isinstance(error,RuntimeError):print(str(error))
        else:print(f'Setup belum selesai ({type(error).__name__}). Periksa PostgreSQL 16, kredensial, koneksi internet dan izin folder.')
        sys.exit(1)
