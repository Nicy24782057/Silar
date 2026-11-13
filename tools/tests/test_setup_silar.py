import contextlib
from importlib.util import spec_from_file_location,module_from_spec
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import tools.setup_silar as setup

ROOT=Path(__file__).resolve().parents[2]
spec=spec_from_file_location('silar_environment_check',ROOT/'code/backend/check_environment.py')
check=module_from_spec(spec);spec.loader.exec_module(check)

class UnifiedSetupTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name);self.backend=self.root/'code/backend';self.backend.mkdir(parents=True)
        self.exe=self.backend/'.venv/bin/python';self.exe.parent.mkdir(parents=True);self.exe.touch()
        for name,value in [('ROOT',self.root),('BACKEND',self.backend)]:
            p=patch.object(setup,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(setup,'backend_python',return_value=self.exe);p.start();self.addCleanup(p.stop)
    def test_check_never_installs_or_initializes_database(self):
        with patch.object(setup,'run') as run,patch('tools.setup_slr10.prepare_project') as install:
            self.assertEqual(setup.main(['--check']),0)
            install.assert_not_called();run.assert_called_once_with([self.exe,self.backend/'check_environment.py','--database'])
            self.assertFalse((self.backend/'.env').exists())
    def test_existing_configuration_is_preserved_and_full_install_is_checked(self):
        config=self.backend/'.env';config.write_text('PRIVATE_MARKER=unchanged\n')
        with patch.object(setup,'run') as run,patch.object(setup.subprocess,'run',return_value=SimpleNamespace(stdout='3.12\n')),patch('tools.setup_slr10.prepare_project',return_value=0) as install:
            self.assertEqual(setup.main([]),0)
            install.assert_called_once();self.assertEqual(run.call_count,1)
        self.assertEqual(config.read_text(),'PRIVATE_MARKER=unchanged\n')
    def test_fresh_install_initializes_foundation_then_installs_and_checks(self):
        calls=[]
        with patch.object(setup,'run',side_effect=lambda args:calls.append(args)),patch.object(setup.subprocess,'run',return_value=SimpleNamespace(stdout='3.12')),patch('tools.setup_slr10.prepare_project',return_value=0):
            self.assertEqual(setup.main([]),0)
        self.assertEqual(calls[0][-1],self.backend/'scripts/setup_local.py')
        self.assertEqual(calls[-1][-2:], [self.backend/'check_environment.py','--database'])
    def test_failed_install_does_not_claim_success_or_run_final_check(self):
        (self.backend/'.env').touch()
        with patch.object(setup,'run') as run,patch.object(setup.subprocess,'run',return_value=SimpleNamespace(stdout='3.12')),patch('tools.setup_slr10.prepare_project',return_value=1):
            self.assertEqual(setup.main([]),1);run.assert_not_called()
    def test_incompatible_existing_venv_is_not_replaced(self):
        with patch.object(setup,'run') as run,patch.object(setup.subprocess,'run',return_value=SimpleNamespace(stdout='3.13')):
            self.assertEqual(setup.main([]),1);run.assert_not_called();self.assertTrue(self.exe.exists())
    def test_missing_venv_check_fails_without_creating_one(self):
        self.exe.unlink()
        with patch.object(setup,'run') as run:
            self.assertEqual(setup.main(['--check']),1);run.assert_not_called();self.assertFalse(self.exe.exists())

class ReadinessCheckTests(unittest.TestCase):
    def test_missing_or_wrong_package_versions_are_reported(self):
        with patch.object(check.metadata,'version',side_effect=check.metadata.PackageNotFoundError),patch.object(check,'import_module'):
            self.assertIn('av: belum terpasang',check.check_packages({'av':'19.0.2'}))
        with patch.object(check.metadata,'version',return_value='1.0'),patch.object(check,'import_module'):
            self.assertIn('numpy: versi 1.0; diperlukan 2.1.3',check.check_packages({'numpy':'2.1.3'}))
    def test_broken_audio_import_is_reported_without_echoing_exception_contents(self):
        with patch.object(check.metadata,'version',return_value='19.0.2'),patch.object(check,'import_module',side_effect=ImportError('secret diagnostic content')):
            problems=check.check_packages({'av':'19.0.2'})
        self.assertIn('av: gagal dimuat (ImportError)',problems)
        self.assertNotIn('secret diagnostic content',' '.join(problems))
    def test_decoder_missing_or_unlaunchable_is_not_a_success(self):
        with patch.object(check.shutil,'which',return_value=None):self.assertEqual(len(check.check_decoders()),2)
        with patch.object(check.shutil,'which',return_value='/fake/ffmpeg'),patch.object(check.subprocess,'run',side_effect=OSError):self.assertEqual(len(check.check_decoders()),2)
    def test_no_success_message_after_failed_readiness(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output),patch.object(check,'check_packages',return_value=['av: belum terpasang']),patch.object(check,'check_decoders',return_value=[]):
            self.assertEqual(check.main([]),1)
        self.assertNotIn('LULUS',output.getvalue())
    def test_success_distinguishes_file_email_and_unverified_inference(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output),patch.object(check,'check_packages',return_value=[]),patch.object(check,'check_decoders',return_value=[]),patch.dict(check.os.environ,{'EMAIL_MODE':'file'}):
            self.assertEqual(check.main([]),0)
        self.assertIn('belum dikirim ke Gmail',output.getvalue());self.assertIn('Inferensi belum diuji',output.getvalue())

if __name__=='__main__':unittest.main()
