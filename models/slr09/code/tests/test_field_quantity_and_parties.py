"""Regression of literal composition; fixtures do not evaluate neural quality."""
from copy import deepcopy
import unittest
from synthetic_fixture import make_synthetic_legacy
from silar_ai_adapter import adapt_legacy_ai_output


def adapt(raw):
    return adapt_legacy_ai_output(raw,narrative_id='UNIT-ONLY',
        sena_model_version='UNIT-SENA',nara_model_version='UNIT-NARA')


class LiteralFieldTests(unittest.TestCase):
    def test_guarded_watchmen_become_parties_without_losing_victim_condition(self):
        raw=make_synthetic_legacy('Dua penjaga terluka di gudang.',role_phrases={
            'WOUNDVICTIM-ARG':['Dua penjaga terluka'],'PLACE-ARG':['gudang']})
        result=adapt(raw)['nara_result']['normalized_output']
        self.assertEqual(result['victims'],['Dua penjaga terluka'])
        self.assertEqual(result['involved_parties'],['Dua penjaga'])

    def test_victim_removed_by_guard_is_not_reintroduced_from_tokens(self):
        raw=make_synthetic_legacy('Tidak ada penjaga terluka.',role_phrases={
            'WOUNDVICTIM-ARG':['penjaga terluka']})
        raw['srl_spans']['WOUNDVICTIM-ARG']=[]
        result=adapt(raw)['nara_result']['normalized_output']
        self.assertEqual(result['victims'],[]);self.assertEqual(result['involved_parties'],[])

    def test_quantity_before_object_is_not_a_second_location(self):
        raw=make_synthetic_legacy('Api merusak empat toko di Kampung Cemara.',role_phrases={
            'PLACE-ARG':['empat','Kampung Cemara'],'AFFECTEDOBJECTS-ARG':['toko']})
        original=deepcopy(raw);result=adapt(raw)
        self.assertEqual(result['nara_result']['normalized_output']['location_text'],'Kampung Cemara')
        self.assertEqual(result['nara_result']['normalized_output']['affected_objects'],['empat toko'])
        self.assertEqual(raw,original)
        self.assertEqual(result['nara_result']['raw_output']['srl_token_predictions'],raw['srl_token_predictions'])

    def test_location_name_with_quantity_word_is_preserved(self):
        raw=make_synthetic_legacy('Dua kios rusak di Desa Empat.',role_phrases={
            'PLACE-ARG':['Desa Empat'],'AFFECTEDOBJECTS-ARG':['kios']})
        result=adapt(raw)['nara_result']['normalized_output']
        self.assertEqual(result['location_text'],'Desa Empat')
        self.assertEqual(result['affected_objects'],['Dua kios'])

    def test_ambiguous_repeated_object_is_not_expanded(self):
        raw=make_synthetic_legacy('Tiga kios rusak; dua kios aman.',role_phrases={
            'AFFECTEDOBJECTS-ARG':['kios']})
        self.assertEqual(adapt(raw)['nara_result']['normalized_output']['affected_objects'],['kios'])

    def test_event_span_containing_damage_predicate_recovers_literal_impact(self):
        raw=make_synthetic_legacy('Api menghanguskan empat kios.',role_phrases={
            'FIRE-EVENT':['Api menghanguskan'],'AFFECTEDOBJECTS-ARG':['empat kios']})
        original=deepcopy(raw);result=adapt(raw)
        self.assertEqual(result['nara_result']['normalized_output']['impacts'],['menghanguskan empat kios'])
        self.assertEqual(result['nara_result']['raw_output']['srl_token_predictions'],original['srl_token_predictions'])

    def test_denied_damage_is_not_recovered(self):
        raw=make_synthetic_legacy('Api tidak menghanguskan empat kios.',role_phrases={
            'FIRE-EVENT':['Api','menghanguskan'],'AFFECTEDOBJECTS-ARG':['empat kios']})
        self.assertEqual(adapt(raw)['nara_result']['normalized_output']['impacts'],[])

    def test_simulation_only_damage_is_not_recovered(self):
        raw=make_synthetic_legacy('Simulasi kebakaran menghanguskan mobil properti.',role_phrases={
            'FIRE-EVENT':['kebakaran menghanguskan'],'AFFECTEDOBJECTS-ARG':['mobil properti']})
        self.assertEqual(adapt(raw)['nara_result']['normalized_output']['impacts'],[])

    def test_real_damage_during_exercise_can_be_recovered(self):
        raw=make_synthetic_legacy('Ketika latihan, api sungguhan menghanguskan empat kios.',role_phrases={
            'FIRE-EVENT':['api','menghanguskan'],'AFFECTEDOBJECTS-ARG':['empat kios']})
        self.assertEqual(adapt(raw)['nara_result']['normalized_output']['impacts'],['menghanguskan empat kios'])


if __name__=='__main__':unittest.main()
