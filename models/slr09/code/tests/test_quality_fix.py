"""Synthetic regression cases; these tests do not measure neural accuracy."""
from copy import deepcopy
import unittest

from support.synthetic_fixture import make_synthetic_legacy
from slr09_runtime import build_adapter_input
from silar_ai_adapter import adapt_legacy_ai_output, fuse_for_silar


def adapt(text, roles, category='FIRE'):
    fixture = make_synthetic_legacy(text, category=category, role_phrases=roles)
    before = deepcopy(fixture)
    raw, trace = build_adapter_input(text, fixture['event_classifier'], fixture['srl_token_predictions'])
    result = adapt_legacy_ai_output(raw, narrative_id='REGRESSION', sena_model_version='synthetic', nara_model_version='synthetic')
    if fixture != before:
        raise AssertionError('Input predictions were modified')
    return result['nara_result']['normalized_output'], result, trace


class QualityFixRegressionTests(unittest.TestCase):
    def test_negated_victims_with_quantities_are_suppressed(self):
        for phrase in ('tiga penumpang terluka', '2 pengendara terluka', 'seorang pejalan kaki terluka'):
            with self.subTest(phrase=phrase):
                output, _, _ = adapt('Tidak ada ' + phrase + ' dalam insiden tersebut.', {'WOUNDVICTIM-ARG':[phrase]})
                self.assertEqual(output['victims'], [])
                self.assertEqual(output['involved_parties'], [])

    def test_denial_does_not_cross_clause_boundary(self):
        for separator in ('; ', ', tetapi ', '. '):
            with self.subTest(separator=separator):
                text = 'Tidak ada korban meninggal' + separator + 'tiga penumpang terluka.'
                output, _, _ = adapt(text, {'DEATHVICTIM-ARG':['korban meninggal'], 'WOUNDVICTIM-ARG':['tiga penumpang terluka']})
                self.assertEqual(output['victims'], ['tiga penumpang terluka'])
                self.assertEqual(output['involved_parties'], ['tiga penumpang'])

    def test_adjacent_human_quantity_restored_from_literal_source(self):
        output, result, _ = adapt('Tiga pengendara terluka di tikungan.', {'WOUNDVICTIM-ARG':['terluka']})
        self.assertEqual(output['victims'], ['Tiga pengendara terluka'])
        self.assertEqual(output['involved_parties'], ['Tiga pengendara'])
        self.assertEqual([x['label'] for x in result['nara_result']['raw_output']['srl_token_predictions']].count('WOUNDVICTIM-ARG'), 1)

    def test_ambulance_is_not_injury_evidence(self):
        output, _, _ = adapt('Dua ambulans tiba di lokasi.', {'WOUNDVICTIM-ARG':['Dua ambulans']})
        self.assertEqual(output['victims'], [])

    def test_real_injury_during_training_is_preserved(self):
        output, result, _ = adapt('Saat latihan, seorang pekerja terluka karena api sungguhan.', {'WOUNDVICTIM-ARG':['seorang pekerja terluka']})
        self.assertEqual(output['victims'], ['seorang pekerja terluka'])
        fused = fuse_for_silar(result, confidence_threshold=.95, calibration_reference='synthetic')
        self.assertEqual(fused['incident_card_version_fields']['data']['event_type'], 'FIRE')

    def test_actor_is_not_added_to_impact_but_damaged_object_is(self):
        output, _, _ = adapt('Relawan mengevakuasi tiga warga.', {'OFFICER-ARG':['Relawan'], 'INFORMATION-ARG':['mengevakuasi'], 'WOUNDVICTIM-ARG':['tiga warga']})
        self.assertEqual(output['impacts'], ['mengevakuasi'])
        self.assertEqual(output['victims'], [])
        output, _, _ = adapt('Dua kios rusak.', {'AFFECTEDOBJECTS-ARG':['Dua kios'], 'INFORMATION-ARG':['rusak']})
        self.assertEqual(output['impacts'], ['Dua kios rusak'])

    def test_local_nonimpact_and_real_effect_are_distinguished(self):
        output, _, _ = adapt('Petugas menggelar latihan; api menghanguskan gudang di tempat lain.',
                             {'INFORMATION-ARG':['menggelar latihan','menghanguskan'], 'AFFECTEDOBJECTS-ARG':['gudang']})
        self.assertEqual(output['impacts'], ['menghanguskan gudang'])

    def test_explicitly_unaffected_object_is_removed_locally(self):
        output, _, _ = adapt('Tanpa kerusakan pada gudang; kios terbakar.', {'AFFECTEDOBJECTS-ARG':['gudang','kios']})
        self.assertEqual(output['affected_objects'], ['kios'])

    def test_without_is_not_a_blanket_impact_suppression(self):
        output, _, _ = adapt('Truk tanpa kendali merusak pagar.', {'INFORMATION-ARG':['tanpa kendali merusak'], 'AFFECTEDOBJECTS-ARG':['pagar']})
        self.assertEqual(output['impacts'], ['tanpa kendali merusak pagar'])

    def test_time_fallback_keeps_literal_text_and_null_timestamp(self):
        output, _, _ = adapt('Api terlihat sekarang di gudang.', {})
        self.assertEqual(output['time_text'], 'sekarang')
        self.assertIsNone(output['occurred_at'])

    def test_time_modifier_does_not_consume_uppercase_place_name(self):
        output, _, _ = adapt('Api di Pasar Pagi ini cepat padam.', {'PLACE-ARG':['Pasar Pagi'], 'TIME-ARG':['ini']})
        self.assertEqual(output['time_text'], 'ini')
        self.assertEqual(output['location_text'], 'Pasar Pagi')
