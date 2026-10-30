"""Acceptance-runner safeguards, without connecting to an application database."""
import unittest
from unittest.mock import MagicMock, patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from django.test.runner import DiscoverRunner

from reporting.slr14_verification import (
    REQUIRED_CONSTRAINTS, REQUIRED_TRIGGERS, SLR14PostgreSQLRunner,
    require_postgresql16, require_schema_guards,
)


def database(major=16):
    fake = MagicMock()
    fake.vendor = 'postgresql'
    cursor = fake.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (str(major * 10000 + 14),)
    return fake


class AcceptanceRunnerTests(SimpleTestCase):
    def test_component_database_is_rejected_before_any_sql(self):
        fake = database()
        fake.vendor = 'sqlite'
        with self.assertRaisesMessage(CommandError, 'PostgreSQL 16'):
            require_postgresql16(fake, {})
        fake.cursor.assert_not_called()

    def test_postgresql_other_major_cannot_receive_native_acceptance(self):
        with self.assertRaisesMessage(CommandError, 'mayor 17'):
            require_postgresql16(database(17), {})

    def test_disabled_migrations_are_rejected_before_database_creation(self):
        fake = database()
        with self.assertRaisesMessage(CommandError, 'Migration core/accounts'):
            require_postgresql16(fake, {'core': None})
        fake.cursor.assert_not_called()

    def test_supported_major_is_read_from_the_server(self):
        fake = database()
        self.assertEqual(require_postgresql16(fake, {}), 16)
        fake.cursor.return_value.__enter__.return_value.execute.assert_called_once_with('SHOW server_version_num')

    @override_settings(MIGRATION_MODULES={})
    def test_runner_ignores_a_test_name_or_mirror_pointing_at_application_data(self):
        fake = database()
        fake.settings_dict = {'NAME': 'application_database', 'TEST': {
            'NAME': 'application_database', 'MIRROR': 'default'}}
        with patch('reporting.slr14_verification.connection', fake), \
                patch.object(DiscoverRunner, 'setup_databases', return_value='isolated'):
            runner = SLR14PostgreSQLRunner(verbosity=0)
            self.assertEqual(runner.setup_databases(), 'isolated')
        self.assertEqual(fake.settings_dict['NAME'], 'application_database')
        self.assertTrue(fake.settings_dict['TEST']['NAME'].startswith('test_silar_slr14_'))
        self.assertNotEqual(fake.settings_dict['TEST']['NAME'], 'application_database')
        self.assertIsNone(fake.settings_dict['TEST']['MIRROR'])

    def test_missing_concurrency_tests_block_acceptance_before_setup(self):
        with patch.object(DiscoverRunner, 'build_suite', return_value=unittest.TestSuite()):
            with self.assertRaisesMessage(CommandError, 'Tes wajib SLR14'):
                SLR14PostgreSQLRunner(verbosity=0).build_suite([])

    def test_skipped_test_is_a_failure_even_when_unittest_calls_it_successful(self):
        result = unittest.TestResult()
        result.testsRun = 1
        result.skipped.append((self, 'Requires PostgreSQL'))
        self.assertTrue(result.wasSuccessful())
        runner = SLR14PostgreSQLRunner(verbosity=0)
        self.assertGreater(runner.suite_result(None, result), 0)
        self.assertEqual(runner.verification['status'], 'FAILED')

    def test_expected_failure_cannot_hide_a_missing_acceptance_guarantee(self):
        result = unittest.TestResult()
        result.testsRun = 1
        result.expectedFailures.append((self, 'Expected failure'))
        self.assertTrue(result.wasSuccessful())
        runner = SLR14PostgreSQLRunner(verbosity=0)
        self.assertGreater(runner.suite_result(None, result), 0)
        self.assertEqual(runner.verification['status'], 'FAILED')

    def test_zero_executed_tests_cannot_be_reported_as_passed(self):
        runner = SLR14PostgreSQLRunner(verbosity=0)
        self.assertGreater(runner.suite_result(None, unittest.TestResult()), 0)
        self.assertEqual(runner.verification['status'], 'FAILED')

    def test_complete_success_is_recorded_without_failure_or_skip(self):
        result = unittest.TestResult()
        result.testsRun = 3
        runner = SLR14PostgreSQLRunner(verbosity=0)
        self.assertEqual(runner.suite_result(None, result), 0)
        self.assertEqual(runner.verification['status'], 'PASSED')
        self.assertEqual(runner.verification['tests_run'], 3)
        self.assertEqual(runner.verification['skipped'], [])

    def test_missing_database_trigger_is_rejected(self):
        fake = database()
        cursor = fake.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [list(REQUIRED_TRIGGERS - {
            ('core_publicationversion', 'silar_publication_guard')}), list(REQUIRED_CONSTRAINTS)]
        with self.assertRaisesMessage(CommandError, 'core_publicationversion.silar_publication_guard'):
            require_schema_guards(fake)

    def test_native_guard_inventory_is_recorded_only_when_complete(self):
        fake = database()
        cursor = fake.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [list(REQUIRED_TRIGGERS), list(REQUIRED_CONSTRAINTS)]
        result = require_schema_guards(fake)
        self.assertEqual(set(result['triggers']), REQUIRED_TRIGGERS)
        self.assertEqual(set(result['constraints']), REQUIRED_CONSTRAINTS)
