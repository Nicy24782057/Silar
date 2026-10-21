"""Reporting/absence precision boundaries; synthetic contracts, not neural tests."""
from copy import deepcopy
import unittest
from silar_postprocessing import filter_nonimpact_information
from silar_ai_adapter import adapt_legacy_ai_output
from synthetic_fixture import make_synthetic_legacy


class ReportingAndAbsenceTests(unittest.TestCase):
    def keep(self, text):
        return filter_nonimpact_information(text, [text])[0]

    def test_confirmation_without_effect_is_not_an_impact(self):
        self.assertEqual(self.keep('mengonfirmasi'), [])

    def test_reporting_subject_without_effect_is_not_an_impact(self):
        self.assertEqual(self.keep('Pemeriksaan regu desa'), [])

    def test_reporting_fragment_with_actual_damage_is_preserved(self):
        text='mengonfirmasi empat rumah rusak'
        self.assertEqual(self.keep(text), [text])

    def test_absence_of_incident_is_not_a_positive_impact(self):
        self.assertEqual(self.keep('belum ada kejadian'), [])

    def test_absence_of_victims_is_not_a_positive_impact(self):
        self.assertEqual(self.keep('tidak ada korban luka'), [])

    def test_absence_fragment_with_later_actual_effect_is_preserved(self):
        text='belum ada kejadian, tetapi empat rumah rusak'
        self.assertEqual(self.keep(text), [text])

    def test_conjoined_actual_effect_is_not_erased_by_negation_prefix(self):
        text='tidak ada korban dan empat rumah rusak'
        self.assertEqual(self.keep(text), [text])

    def test_unconscious_victim_condition_is_not_absence(self):
        text='dua warga tidak sadarkan diri'
        self.assertEqual(self.keep(text), [text])

    def test_standalone_connector_is_not_a_positive_effect(self):
        self.assertEqual(self.keep('sampai'), [])

    def test_connector_followed_by_actual_effect_is_preserved(self):
        text='sampai atap roboh'
        self.assertEqual(self.keep(text), [text])

    def test_adapter_preserves_damage_and_raw_roles_when_filtering_reporting(self):
        raw=make_synthetic_legacy('Petugas mengonfirmasi kebakaran; api merusak dua toko.',role_phrases={
            'OFFICER-ARG':['Petugas'],'FIRE-EVENT':['kebakaran','api'],
            'INFORMATION-ARG':['mengonfirmasi','merusak'],'AFFECTEDOBJECTS-ARG':['dua toko']})
        before=deepcopy(raw)
        result=adapt_legacy_ai_output(raw,narrative_id='UNIT-ONLY',sena_model_version='UNIT-SENA',nara_model_version='UNIT-NARA')
        self.assertEqual(result['nara_result']['normalized_output']['impacts'],['merusak dua toko'])
        self.assertEqual(raw,before)
        self.assertEqual(result['nara_result']['raw_output']['srl_token_predictions'],before['srl_token_predictions'])


if __name__=='__main__':
    unittest.main()
