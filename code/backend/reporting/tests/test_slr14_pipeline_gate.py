"""Verifier guard unit tests; OS doubles here are never evidence of native acceptance."""
import unittest
from unittest.mock import patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from django.test.runner import DiscoverRunner

from reporting.slr14_verification import (
    REQUIRED_TESTS, REQUIRED_PIPELINE_TESTS, SLR14PostgreSQLRunner, require_execution_identity,
)


def suite(names):
    class NamedCase(unittest.TestCase):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def id(self):
            return self.name

        def runTest(self):
            pass

    return unittest.TestSuite(NamedCase(name) for name in names)


class PipelineAcceptanceGuardTests(SimpleTestCase):
    def test_base_scope_does_not_silently_claim_pipeline_integration(self):
        runner = SLR14PostgreSQLRunner(verbosity=0)
        with patch.object(DiscoverRunner, 'build_suite', return_value=suite(REQUIRED_TESTS)):
            runner.build_suite([])
        self.assertFalse(runner.verification['pipeline_integration']['requested'])
        self.assertFalse(runner.verification['live_ai_inference_exercised'])

    def test_all_nine_pipeline_cases_are_required_in_combined_scope(self):
        runner = SLR14PostgreSQLRunner(verbosity=0, pipeline_integration=True)
        omitted = next(iter(REQUIRED_PIPELINE_TESTS))
        with patch.object(DiscoverRunner, 'build_suite', return_value=suite(
                (REQUIRED_TESTS | REQUIRED_PIPELINE_TESTS) - {omitted})):
            with self.assertRaises(CommandError):
                runner.build_suite([])
        with patch.object(DiscoverRunner, 'build_suite', return_value=suite(REQUIRED_TESTS | REQUIRED_PIPELINE_TESTS)):
            runner.build_suite([])
        self.assertEqual(runner.verification['pipeline_integration']['discovered_tests'], 9)
        self.assertEqual(runner.verification['pipeline_integration']['ai_clients'], 'test_doubles')
        self.assertFalse(runner.verification['live_ai_inference_exercised'])

    def test_unreadable_process_identity_blocks_instead_of_being_replaced(self):
        with patch('ai_pipeline.execution.process_context', side_effect=RuntimeError('OS identity unavailable')):
            with self.assertRaisesMessage(CommandError, 'Python/psutil'):
                require_execution_identity()

    def test_stopped_or_reused_identity_cannot_pass_a_live_environment_check(self):
        with patch('ai_pipeline.execution.process_context', return_value={'pid': 123, 'process_started_at': 4.0}), \
                patch('psutil.Process') as factory:
            process = factory.return_value
            process.is_running.return_value = False
            with self.assertRaises(CommandError):
                require_execution_identity()
            process.is_running.return_value = True
            process.create_time.return_value = 5.0
            with self.assertRaises(CommandError):
                require_execution_identity()
            process.create_time.return_value = 4.0
            self.assertTrue(require_execution_identity())

    @override_settings(MIGRATION_MODULES={})
    def test_identity_failure_stops_before_creating_any_test_database(self):
        runner = SLR14PostgreSQLRunner(verbosity=0, pipeline_integration=True)
        with patch('reporting.slr14_verification.require_postgresql16', return_value=16), \
                patch('reporting.slr14_verification.require_execution_identity', side_effect=CommandError('blocked')), \
                patch.object(DiscoverRunner, 'setup_databases') as create:
            with self.assertRaises(CommandError):
                runner.setup_databases()
        create.assert_not_called()
        self.assertNotIn('test_database', runner.verification)
