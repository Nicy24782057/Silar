"""Installer contract tests using isolated repositories and synthetic secrets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'install_slr10.py'
spec = importlib.util.spec_from_file_location('slr10_installer_tested', MODULE_PATH)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class InstallerTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pack = Path(folder.name) / 'package'
        self.target = Path(folder.name) / 'Silar'
        for root in (self.pack, self.target):
            (root / 'tools').mkdir(parents=True)
        previous_source = installer.SOURCE
        installer.SOURCE = self.pack
        self.addCleanup(setattr, installer, 'SOURCE', previous_source)
        self.name = 'code/frontend/src/feature.js'
        self.old = b'// version 1.0.0\n'
        self.new = b'// version 1.1.0\n'
        self.write(self.pack, self.name, self.new)
        self.write(self.target, 'code/backend/manage.py', b'# fixture\n')
        self.write(self.target, 'code/backend/config/settings.py', b"INSTALLED_APPS = ['core', 'ai_pipeline']\n")
        self.write(self.target, 'code/backend/config/urls.py', b"urlpatterns = []\n# existing ai_pipeline routes\n")
        self.write(self.target, 'code/backend/requirements.txt', b'Django==5.2.18\n')
        self.write(self.target, '.gitignore', b'local_files/\n')
        for name in ('code/backend/.env', 'code/backend/ai_pipeline/work.py',
                     'code/backend/private_media/evidence.bin', 'models/model.bin',
                     'code/backend/.venv/keep.txt', 'code/backend/core/migrations/0001_initial.py'):
            self.write(self.target, name, ('preserve fixture: ' + name).encode())
        self.manifest = {'version':'1.1.0','files':{self.name:{'sha256':digest(self.new),
            'equivalent_sha256':[digest(self.new),digest(self.new.replace(b'\n', b'\r\n'))],
            'accepted_previous_sha256':[digest(self.old),digest(self.old.replace(b'\n', b'\r\n'))]}}}
        self.save_manifest()

    def write(self, root, name, data):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def save_manifest(self):
        (self.pack / 'tools/release-manifest.json').write_text(json.dumps(self.manifest,indent=2)+'\n')

    def snapshot(self):
        return {str(p.relative_to(self.target)):p.read_bytes() for p in self.target.rglob('*') if p.is_file()}

    def test_fresh_install_preserves_database_configuration_ai_media_and_models(self):
        before = self.snapshot()
        installer.install(self.target)
        for name, raw in before.items():
            if name not in ('.gitignore','code/backend/config/settings.py','code/backend/config/urls.py','code/backend/requirements.txt'):
                self.assertEqual((self.target / name).read_bytes(), raw)
        self.assertIn('ai_pipeline', (self.target/'code/backend/config/settings.py').read_text())
        self.assertIn('ai_pipeline', (self.target/'code/backend/config/urls.py').read_text())
        self.assertIn('Pillow==13.0.0', (self.target/'code/backend/requirements.txt').read_text())

    def test_upgrade_known_100_and_pillow_without_changing_ai_requirements(self):
        self.write(self.target, self.name, self.old)
        self.write(self.target, 'code/backend/requirements.txt', b'Django==5.2.18\nPillow==12.3.0\n# team dependency\n')
        ai = b'-r requirements.txt\nPillow==13.0.0\n# existing AI dependencies\n'
        self.write(self.target, 'code/backend/requirements-ai.txt', ai)
        installer.install(self.target)
        self.assertEqual((self.target/self.name).read_bytes(), self.new)
        self.assertEqual((self.target/'code/backend/requirements-ai.txt').read_bytes(), ai)
        requirements = (self.target/'code/backend/requirements.txt').read_text()
        self.assertNotIn('12.3.0', requirements)
        self.assertIn('# team dependency', requirements)

    def test_known_windows_crlf_previous_file_is_upgraded(self):
        self.write(self.target, self.name, self.old.replace(b'\n', b'\r\n'))
        installer.install(self.target)
        self.assertEqual((self.target/self.name).read_bytes(), self.new)

    def test_reinstall_is_idempotent(self):
        installer.install(self.target)
        self.assertEqual(installer.install(self.target, dry_run=True), 0)

    def test_current_windows_crlf_does_not_create_false_conflict(self):
        installer.install(self.target)
        self.write(self.target, self.name, self.new.replace(b'\n', b'\r\n'))
        path = self.target/'tools/release-manifest.json'
        path.write_bytes(path.read_bytes().replace(b'\n',b'\r\n'))
        self.assertEqual(installer.install(self.target,dry_run=True), 0)

    def test_local_source_edits_stop_all_writes(self):
        self.write(self.target, self.name, b'// local work\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): installer.install(self.target)
        self.assertEqual(before, self.snapshot())

    def test_unknown_pillow_pin_stops_all_writes(self):
        self.write(self.target, 'code/backend/requirements.txt', b'Pillow==99.0.0\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): installer.install(self.target)
        self.assertEqual(before, self.snapshot())

    def test_conflicting_ai_pin_stops_all_writes(self):
        self.write(self.target, 'code/backend/requirements-ai.txt', b'Pillow==12.3.0\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): installer.install(self.target)
        self.assertEqual(before, self.snapshot())

    def test_previous_file_and_requirements_are_backed_up(self):
        self.write(self.target, self.name, self.old)
        installer.install(self.target)
        backups = list((self.target/'.slr10-backups').glob('*/'+self.name))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.old)

    def test_modified_distribution_is_rejected_without_target_changes(self):
        self.write(self.pack, self.name, b'changed distribution')
        before = self.snapshot()
        with self.assertRaises(ValueError): installer.install(self.target)
        self.assertEqual(before, self.snapshot())

    def test_known_previous_manifest_is_replaced_safely(self):
        old = b'{"version":"1.0.0","files":{}}'
        self.write(self.target, 'tools/release-manifest.json', old)
        self.manifest['previous_manifest_sha256'] = [digest(old)]
        self.save_manifest()
        installer.install(self.target)
        self.assertEqual((self.target/'tools/release-manifest.json').read_bytes(), (self.pack/'tools/release-manifest.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
