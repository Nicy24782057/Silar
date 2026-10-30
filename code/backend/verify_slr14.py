#!/usr/bin/env python
"""Run native PostgreSQL 16 acceptance and save a shareable, credential-free report."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4


BACKEND = Path(__file__).resolve().parent
PROJECT = BACKEND.parent.parent


def main():
    parser = argparse.ArgumentParser(description='Verifikasi SLR14 pada PostgreSQL 16 dengan database uji terpisah.')
    parser.add_argument('--report', type=Path, help='Lokasi laporan JSON; bawaan docs/slr14/hasil-postgresql/.')
    args = parser.parse_args()
    now = datetime.now(timezone(timedelta(hours=7)))
    destination = args.report or PROJECT / 'docs/slr14/hasil-postgresql' / (
        now.strftime('verifikasi-%Y%m%d-%H%M%S-') + uuid4().hex[:8] + '.json')
    destination = destination.resolve()
    report = {'status': 'BLOCKED', 'generated_at': now.isoformat(), 'tests_run': 0,
              'database_vendor': None, 'postgresql_major': None}
    exit_code = 2
    try:
        # These secrets exist only in this test process. The project's .env,
        # account credentials and application settings files are never edited.
        for name in ('SECRET_KEY', 'JWT_SIGNING_KEY', 'OTP_HMAC_KEY'):
            os.environ[name] = secrets.token_urlsafe(48)
        os.environ.update(DJANGO_SETTINGS_MODULE='config.test_settings', SILAR_LOCAL_MODE='1',
                          FRONTEND_URL='http://localhost:5173', EMAIL_MODE='file',
                          ALLOWED_HOSTS='localhost,127.0.0.1,testserver')
        sys.path.insert(0, str(BACKEND))
        os.chdir(BACKEND)
        import django
        django.setup()
        from django.core.management.base import CommandError
        from django.db import DatabaseError, connections
        from django.test import override_settings
        from reporting.slr14_verification import SLR14PostgreSQLRunner, TEST_LABELS

        report['django_version'] = django.get_version()
        try:
            with TemporaryDirectory(prefix='silar-slr14-verification-') as temporary:
                with override_settings(PRIVATE_MEDIA_ROOT=Path(temporary) / 'media',
                                       EMAIL_FILE_PATH=Path(temporary) / 'outbox'):
                    runner = SLR14PostgreSQLRunner(verification=report, verbosity=2,
                        interactive=False, keepdb=False, parallel=1)
                    failures = runner.run_tests(TEST_LABELS)
                    exit_code = 1 if failures else 0
        except CommandError as error:
            exit_code = 2
            report.update(status='BLOCKED', reason=str(error))
        except DatabaseError:
            # Do not copy DSNs, hosts, usernames or driver diagnostics into
            # a report intended to be shared for troubleshooting.
            exit_code = 2
            report.update(status='BLOCKED', reason='PostgreSQL 16 belum dapat digunakan. Periksa koneksi dan hak membuat database uji pada konfigurasi lokal.')
        finally:
            connections.close_all()
    except KeyboardInterrupt:
        exit_code = 2
        report.update(status='BLOCKED', reason='Pengujian dihentikan sebelum selesai.')
    except Exception as error:
        exit_code = 2
        report.update(status='BLOCKED', reason='Verifikasi tidak selesai; periksa dependensi dan konfigurasi pengujian.',
                      error_type=type(error).__name__)
    finally:
        try:
            destination = destination.resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary_report = destination.with_name(destination.name + '.' + uuid4().hex + '.tmp')
            temporary_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            temporary_report.replace(destination)
            print(f'\nStatus SLR14: {report["status"]}')
            if report.get('reason'):
                print(report['reason'])
            print(f'Laporan: {destination}')
        except OSError:
            print('Laporan verifikasi tidak dapat disimpan.', file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
