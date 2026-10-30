"""Native SLR14 acceptance gate. Never substitute the component database."""
import unittest
from uuid import uuid4

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection
from django.test.runner import DiscoverRunner


TEST_LABELS = (
    'core',
    'reporting.tests.test_publication',
    'reporting.tests.test_workspace',
    'reporting.tests.test_workspace_update03',
    'reporting.tests.test_review',
    'reporting.tests.test_report_list_filters',
    'reporting.tests.test_review_postgresql',
    'reporting.tests.test_slr14_verification',
    'reporting.tests.test_deletion',
    'reporting.tests.test_deletion_postgresql',
)
REQUIRED_TESTS = frozenset({
    'core.tests.FoundationTests.test_postgresql_16_is_actual_test_engine',
    'core.tests.FoundationTests.test_json_type_constraint_blocks_raw_sql_bypass',
    'reporting.tests.test_publication.PublicationConcurrencyTests.test_concurrent_candidate_creation_commits_only_one_active_version',
    'reporting.tests.test_publication.PublicationConcurrencyTests.test_concurrent_publish_replay_has_one_notification_and_one_audit',
    'reporting.tests.test_workspace.ClaimConcurrencyTests.test_two_simultaneous_claims_produce_one_current_handler',
    'reporting.tests.test_review_postgresql.ReporterLockTests.test_official_source_is_locked_by_database',
    'reporting.tests.test_deletion_postgresql.DraftDeletionLockTests.test_delete_and_submit_cannot_both_commit',
    'reporting.tests.test_deletion_postgresql.DraftDeletionLockTests.test_same_key_concurrent_delete_has_one_audit',
    'reporting.tests.test_deletion_postgresql.DraftDeletionLockTests.test_raw_sql_cannot_restore_or_change_a_deleted_report',
})
REQUIRED_TRIGGERS = frozenset({
    ('core_report', 'silar_report_guard'),
    ('core_report', 'silar_deleted_report_guard'),
    ('core_publicationversion', 'silar_publication_guard'),
    ('core_publicationversion', 'silar_no_delete'),
    ('core_operatorassignment', 'silar_assignment_guard'),
    ('core_evidencebundle', 'silar_bundle_nonempty'),
    ('core_evidencebundleitem', 'silar_bundle_membership'),
    ('core_auditevent', 'silar_immutable'),
    ('core_idempotencyrecord', 'silar_no_delete'),
})
REQUIRED_CONSTRAINTS = frozenset({('core_report','deleted_draft_owner_and_state')} | {
    ('core_publicationversion', name) for name in (
        'publication_version_unique', 'publication_state_allowed',
        'publication_approval_metadata', 'publication_publish_metadata',
        'publication_cancel_metadata', 'publicationversion_data_jsonkind',
    )
})


def require_postgresql16(database, migration_modules):
    if database.vendor != 'postgresql':
        raise CommandError('Verifikasi SLR14 memerlukan PostgreSQL 16, bukan database komponen.')
    if any(name in migration_modules and migration_modules[name] is None for name in ('core', 'accounts')):
        raise CommandError('Migration core/accounts tidak boleh dinonaktifkan pada verifikasi PostgreSQL.')
    with database.cursor() as cursor:
        cursor.execute('SHOW server_version_num')
        major = int(cursor.fetchone()[0]) // 10000
    if major != 16:
        raise CommandError(f'PostgreSQL mayor {major} terdeteksi; verifikasi SLR14 memerlukan mayor 16.')
    return major


def require_schema_guards(database):
    with database.cursor() as cursor:
        cursor.execute('''
            SELECT relation.relname, guard.tgname
            FROM pg_trigger guard
            JOIN pg_class relation ON relation.oid = guard.tgrelid
            JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = current_schema()
              AND NOT guard.tgisinternal AND guard.tgenabled IN ('O', 'A')
        ''')
        triggers = set(cursor.fetchall())
        cursor.execute('''
            SELECT relation.relname, rule.conname
            FROM pg_constraint rule
            JOIN pg_class relation ON relation.oid = rule.conrelid
            JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = current_schema() AND rule.convalidated
        ''')
        constraints = set(cursor.fetchall())
    missing = (REQUIRED_TRIGGERS - triggers) | (REQUIRED_CONSTRAINTS - constraints)
    if missing:
        names = ', '.join(f'{table}.{name}' for table, name in sorted(missing))
        raise CommandError('Guard database uji belum lengkap: ' + names)
    return {'triggers': sorted(REQUIRED_TRIGGERS), 'constraints': sorted(REQUIRED_CONSTRAINTS)}


def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


class SLR14PostgreSQLRunner(DiscoverRunner):
    """Separate database, real migrations/guards, required races, no skipped pass."""

    def __init__(self, *args, verification=None, **kwargs):
        self.verification = verification if verification is not None else {}
        super().__init__(*args, **kwargs)

    def build_suite(self, *args, **kwargs):
        suite = super().build_suite(*args, **kwargs)
        discovered = set(test_ids(suite))
        missing = REQUIRED_TESTS - discovered
        if missing:
            raise CommandError('Tes wajib SLR14 tidak ditemukan: ' + ', '.join(sorted(missing)))
        self.verification['discovered_tests'] = suite.countTestCases()
        return suite

    def setup_databases(self, **kwargs):
        major = require_postgresql16(connection, settings.MIGRATION_MODULES)
        self.verification.update(database_vendor='postgresql', postgresql_major=major)
        # Never reuse/drop a configured application database or an existing
        # test database. Django creates and tears down this unique test name.
        test_name = 'test_silar_slr14_' + uuid4().hex
        connection.settings_dict.setdefault('TEST', {}).update(NAME=test_name, MIRROR=None)
        self.verification['test_database'] = test_name
        return super().setup_databases(**kwargs)

    def run_checks(self, databases):
        super().run_checks(databases)
        self.verification['schema_guards'] = require_schema_guards(connection)

    def suite_result(self, suite, result, **kwargs):
        failures = super().suite_result(suite, result, **kwargs)
        skipped = [{'test': test.id(), 'reason': str(reason)} for test, reason in result.skipped]
        empty = result.testsRun == 0
        expected_failures = [test.id() for test, _ in result.expectedFailures]
        count = failures + len(skipped) + len(expected_failures) + int(empty)
        self.verification.update(
            status='FAILED' if count else 'PASSED', tests_run=result.testsRun,
            failures=len(result.failures), errors=len(result.errors), skipped=skipped,
            unexpected_successes=len(result.unexpectedSuccesses),
            expected_failures=expected_failures,
            failed_tests=[test.id() for test, _ in result.failures + result.errors],
        )
        if skipped or empty or expected_failures:
            self.log('SLR14 belum lulus: tes wajib dilewati atau tidak ada tes yang dijalankan.')
        return count
