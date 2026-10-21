"""Kontrak kandidat dengan bytes/fixture sintetis; tidak memuat model neural."""
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

from slr09_candidate_runtime import (
    CANDIDATE_LOCK, INTEGRATION_CONFIG, PACKAGE_ROOT, RUNTIME_FILES, candidate_record, check_dependencies,
    extract_candidate_archive, run_smoke, selected_assets, verify_candidate_directory,
)
from silar_ai_adapter import EVENT_CATEGORIES, NARA_LABELS, adapt_legacy_ai_output
from slr09_runtime import build_adapter_input
from synthetic_fixture import demo_fixture, make_synthetic_legacy


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


class CandidateAssetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.files = {name: b'SYNTHETIC_NOT_NEURAL' for name in RUNTIME_FILES}
        self.files['config.json'] = json.dumps({'id2label': {'0': 'FLOOD'}}).encode()
        self.spec = {'model_id': 'SYNTHETIC-CANDIDATE', 'run_id': 'SYNTHETIC-RUN',
                     'labels': ['FLOOD'], 'archive_sha256': '0' * 64,
                     'files': {name: hash_bytes(data) for name, data in self.files.items()}}
        for name, value in self.files.items():
            (self.directory / name).write_bytes(value)

    def test_candidate_directory_has_explicit_identity_and_hashes(self):
        observed = verify_candidate_directory(self.directory, 'sena', self.spec)
        self.assertEqual(observed['model_id'], 'SYNTHETIC-CANDIDATE')
        self.assertEqual(observed['files'], self.spec['files'])
        self.assertTrue(observed['candidate_directory_verified'])

    def test_different_weights_cannot_be_accepted_as_candidate(self):
        (self.directory / 'model.safetensors').write_bytes(b'DIFFERENT_WEIGHT_BYTES')
        with self.assertRaisesRegex(ValueError, 'hash kandidat berbeda'):
            verify_candidate_directory(self.directory, 'sena', self.spec)

    def test_config_labels_must_match_even_if_hash_was_updated(self):
        data = json.dumps({'id2label': {'0': 'NON_EVENT'}}).encode()
        (self.directory / 'config.json').write_bytes(data)
        self.spec['files']['config.json'] = hash_bytes(data)
        with self.assertRaisesRegex(ValueError, 'label konfigurasi'):
            verify_candidate_directory(self.directory, 'sena', self.spec)

    def test_missing_tokenizer_is_rejected(self):
        (self.directory / 'tokenizer.json').unlink()
        with self.assertRaisesRegex(ValueError, 'berkas tidak tersedia'):
            verify_candidate_directory(self.directory, 'sena', self.spec)

    def test_symlink_weight_is_rejected(self):
        weight = self.directory / 'model.safetensors'
        weight.unlink()
        weight.symlink_to(self.directory / 'vocab.txt')
        with self.assertRaisesRegex(ValueError, 'berkas tidak tersedia'):
            verify_candidate_directory(self.directory, 'sena', self.spec)

    def archive(self, duplicate=False):
        path = self.directory / 'candidate.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in self.files.items():
                archive.writestr(name, data)
            archive.writestr('../outside.txt', b'IGNORED')
            archive.writestr('training_args.bin', b'NEVER_DESERIALIZED')
            if duplicate:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    archive.writestr('model.safetensors', b'DUPLICATE')
        self.spec['archive_sha256'] = hash_bytes(path.read_bytes())
        return path

    def test_extraction_uses_only_hashed_runtime_files(self):
        path = self.archive()
        output = self.directory / 'extracted'
        evidence = extract_candidate_archive(path, output, 'sena', self.spec)
        self.assertEqual(set(p.name for p in output.iterdir()), RUNTIME_FILES)
        self.assertEqual(evidence['archive_sha256_observed'], self.spec['archive_sha256'])
        self.assertFalse((self.directory / 'outside.txt').exists())

    def test_duplicate_archive_member_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'anggota runtime'):
            extract_candidate_archive(self.archive(duplicate=True), self.directory / 'out', 'sena', self.spec)

    def test_wrong_archive_hash_is_rejected_before_extracting(self):
        path = self.archive()
        self.spec['archive_sha256'] = '0' * 64
        output = self.directory / 'out'
        with self.assertRaisesRegex(ValueError, 'arsip berbeda'):
            extract_candidate_archive(path, output, 'sena', self.spec)
        self.assertFalse(output.exists())


class CandidateConfigurationTests(unittest.TestCase):
    def test_committed_lock_matches_selected_candidates_and_adapter(self):
        config, lock, _ = selected_assets()
        self.assertEqual(config['confidence_threshold'], .95)
        self.assertEqual(tuple(lock['models']['sena']['labels']), EVENT_CATEGORIES)
        self.assertEqual(tuple(lock['models']['nara']['labels']), NARA_LABELS)
        self.assertNotEqual(lock['models']['sena']['model_id'], 'SILAR_SENA_v1')
        self.assertNotEqual(lock['models']['nara']['model_id'], 'SILAR_NARA_v1')

    def test_inconsistent_lock_and_integration_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'config').mkdir()
            for name in [INTEGRATION_CONFIG, CANDIDATE_LOCK, 'inference_environment.json']:
                (root / 'config' / name).write_bytes((PACKAGE_ROOT / 'config' / name).read_bytes())
            path = root / 'config' / CANDIDATE_LOCK
            data = json.loads(path.read_text())
            data['models']['sena']['files']['model.safetensors'] = 'a' * 64
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'hash bobot kandidat'):
                selected_assets(root)

    def test_dependency_guard_accepts_matching_cuda_local_suffix(self):
        profile = {'guard_packages': ['torch'], 'pinned_packages': {'torch': '2.11.0'}}
        self.assertEqual(check_dependencies(profile, lambda name: '2.11.0+cu130')['torch'], '2.11.0+cu130')

    def test_dependency_guard_rejects_different_version(self):
        profile = {'guard_packages': ['transformers'], 'pinned_packages': {'transformers': '4.57.1'}}
        with self.assertRaisesRegex(RuntimeError, 'Profil inference belum sesuai'):
            check_dependencies(profile, lambda name: '5.13.1')

    def test_dependency_guard_reports_missing_package(self):
        def missing(name):
            raise importlib.metadata.PackageNotFoundError(name)
        profile = {'guard_packages': ['torch'], 'pinned_packages': {'torch': '2.11.0'}}
        with self.assertRaisesRegex(RuntimeError, 'belum terpasang'):
            check_dependencies(profile, missing)

    def test_record_identifies_candidate_versions_and_keeps_fusion_separate(self):
        config, lock, _ = selected_assets()
        raw = demo_fixture()
        result = candidate_record({'id': 'SYNTHETIC', 'text': raw['report_text']},
                                  raw['event_classifier'], raw['srl_token_predictions'], config, lock)
        self.assertIn(lock['models']['sena']['run_id'], result['adapted_result']['sena_result']['model_version'])
        self.assertIn(lock['models']['nara']['run_id'], result['adapted_result']['nara_result']['model_version'])
        before = deepcopy(result['adapted_result'])
        result['fusion_result']['incident_card_version_fields']['data']['impacts'].append('MUTATED')
        self.assertEqual(result['adapted_result'], before)

    def test_missing_weights_are_recorded_as_failed_without_inference_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = directory / 'input.jsonl'
            inputs.write_text(json.dumps({'id': 'SYNTHETIC', 'text': 'Banjir di jalan'}) + '\n')
            args = SimpleNamespace(root=PACKAGE_ROOT, sena_dir=directory / 'missing-sena',
                nara_dir=directory / 'missing-nara', input=inputs, output_dir=directory / 'evidence',
                device='cpu', cpu_threads=None, environment_label='SYNTHETIC-TEST', environment_scope='REPRESENTATIVE')
            with self.assertRaises(ValueError):
                run_smoke(args)
            summary = json.loads((args.output_dir / 'run_summary.json').read_text())
            self.assertEqual(summary['status'], 'FAILED')
            self.assertEqual(summary['records_completed'], 0)
            self.assertFalse(summary['model_inference_executed'])
            self.assertFalse(summary['fusion_executed'])


class ActiveNormalizationTests(unittest.TestCase):
    def adapt_victim(self, text, phrase):
        raw = make_synthetic_legacy(text, category='ACCIDENT', role_phrases={'WOUNDVICTIM-ARG': [phrase]})
        guarded, trace = build_adapter_input(text, raw['event_classifier'], raw['srl_token_predictions'])
        return adapt_legacy_ai_output(guarded, narrative_id='SYNTHETIC', sena_model_version='SENA-test', nara_model_version='NARA-test'), trace

    def test_explicit_breathing_condition_is_kept(self):
        result, _ = self.adapt_victim('Kecelakaan menyebabkan satu warga sesak napas.', 'satu warga sesak napas')
        self.assertEqual(result['nara_result']['normalized_output']['victims'], ['satu warga sesak napas'])

    def test_negated_breathing_condition_is_not_positive_victim(self):
        result, _ = self.adapt_victim('Kecelakaan: satu warga tidak sesak napas.', 'satu warga tidak sesak napas')
        self.assertEqual(result['nara_result']['normalized_output']['victims'], [])

    def test_unconscious_condition_is_not_misread_as_negation(self):
        result, _ = self.adapt_victim('Kecelakaan menyebabkan satu warga tidak sadarkan diri.', 'satu warga tidak sadarkan diri')
        self.assertEqual(result['nara_result']['normalized_output']['victims'], ['satu warga tidak sadarkan diri'])

    def test_literal_impact_still_maps_to_impact(self):
        raw = make_synthetic_legacy('Rumah terendam', role_phrases={'INFORMATION-ARG': ['terendam']})
        result = adapt_legacy_ai_output(raw, narrative_id='SYNTHETIC', sena_model_version='SENA-test', nara_model_version='NARA-test')
        self.assertEqual(result['nara_result']['normalized_output']['impacts'], ['terendam'])
        self.assertIn({'code': 'INFORMATION_AS_IMPACT_SUGGESTION', 'field': 'impacts'}, result['nara_result']['normalization_warnings'])
