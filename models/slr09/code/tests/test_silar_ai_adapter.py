"""Pemeriksaan kontrak adapter dengan fixture sintetis; bukan evaluasi AI."""

import copy
import unittest

from silar_ai_adapter import (
    AdapterValidationError, CalibrationRequiredError, EXTRACTION_FIELDS,
    NARA_LABELS, adapt_legacy_ai_output, fuse_for_silar,
)
from synthetic_fixture import demo_fixture, make_synthetic_legacy


class AdapterContractTests(unittest.TestCase):
    def adapt(self, raw=None):
        return adapt_legacy_ai_output(
            demo_fixture() if raw is None else raw,
            narrative_id="SYNTHETIC-NARRATIVE-001",
            sena_model_version="SILAR_SENA_v1", nara_model_version="SILAR_NARA_v1",
        )

    def fuse(self, adapted, threshold=0.8):
        return fuse_for_silar(adapted, confidence_threshold=threshold, calibration_reference="SYNTHETIC_TEST_ONLY")

    def test_all_15_configured_labels_are_accepted(self):
        for role in NARA_LABELS:
            with self.subTest(role=role):
                raw = make_synthetic_legacy("contoh", role_phrases={} if role == "O" else {role: ["contoh"]})
                self.adapt(raw)

    def test_projection_has_exactly_seven_extraction_fields(self):
        data = self.adapt()["nara_result"]["normalized_output"]
        self.assertEqual(set(data), set(EXTRACTION_FIELDS))
        self.assertNotIn("event_type", data)

    def test_spatial_information_is_not_projected_as_impact(self):
        raw = make_synthetic_legacy("Banjir di depan pom bensin", role_phrases={"INFORMATION-ARG": ["depan pom bensin"]})
        result = self.adapt(raw)
        self.assertEqual(result["nara_result"]["normalized_output"]["impacts"], [])
        self.assertNotIn({"code": "INFORMATION_AS_IMPACT_SUGGESTION", "field": "impacts"}, result["nara_result"]["normalization_warnings"])
        self.assertFalse(self.fuse(result)["incident_card_version_fields"]["uncertain"])

    def test_role_mapping_for_location_time_parties_objects_and_victims(self):
        data = self.adapt()["nara_result"]["normalized_output"]
        self.assertEqual(data, {
            "location_text": "Rajabasa; Jalan Mawar", "time_text": "pukul 14.30",
            "occurred_at": None, "involved_parties": ["BPBD", "satu warga"], "impacts": ["Dua rumah terendam"],
            "victims": ["satu warga terluka"], "affected_objects": ["Dua rumah"],
        })

    def test_reason_remains_in_raw_without_new_schema_field(self):
        nara = self.adapt()["nara_result"]
        self.assertEqual(nara["raw_output"]["srl_spans"]["REASON-ARG"][0]["text"], "hujan deras")
        self.assertNotIn("reason", nara["normalized_output"])

    def test_no_input_mutation(self):
        raw = demo_fixture()
        before = copy.deepcopy(raw)
        self.adapt(raw)
        self.assertEqual(raw, before)

    def test_raw_output_has_no_alias_to_input_or_normalized_values(self):
        raw = demo_fixture()
        result = self.adapt(raw)
        result["nara_result"]["normalized_output"]["impacts"].append("perubahan fixture")
        raw["srl_spans"]["INFORMATION-ARG"][0]["text"] = "diganti"
        self.assertEqual(result["nara_result"]["raw_output"]["srl_spans"]["INFORMATION-ARG"][0]["text"], "terendam")
        self.assertEqual(result["nara_result"]["raw_output"]["srl_token_predictions"], demo_fixture()["srl_token_predictions"])

    def test_empty_extraction_does_not_create_uncertainty_or_completeness(self):
        result = self.adapt(make_synthetic_legacy("Air naik", role_phrases={}))
        data = result["nara_result"]["normalized_output"]
        self.assertIsNone(data["location_text"])
        self.assertEqual(data["victims"], [])
        self.assertEqual(data["impacts"], [])
        card = self.fuse(result)["incident_card_version_fields"]
        self.assertFalse(card["uncertain"])
        self.assertEqual(card["uncertain_reasons"], [])
        self.assertNotIn("completeness", result)

    def test_non_event_blocks_even_when_confidence_is_low(self):
        raw = make_synthetic_legacy("Simulasi banjir", category="NON_EVENT", confidence=0.6)
        fused = self.fuse(self.adapt(raw))
        self.assertIsNone(fused["incident_card_version_fields"]["data"]["event_type"])
        self.assertTrue(fused["integration_signals"]["blocked_by_non_event"])
        self.assertTrue(fused["incident_card_version_fields"]["uncertain"])

    def test_category_stays_sena_when_nara_event_differs(self):
        raw = make_synthetic_legacy("Api terlihat", category="FIRE", role_phrases={"EARTHQUAKE-EVENT": ["Api"]})
        card = self.fuse(self.adapt(raw))["incident_card_version_fields"]
        self.assertEqual(card["data"]["event_type"], "FIRE")
        self.assertFalse(card["uncertain"])

    def test_false_event_role_does_not_override_sena(self):
        raw = make_synthetic_legacy("Banjir", category="FLOOD", role_phrases={"FALSE-EVENT": ["Banjir"]})
        self.assertEqual(self.fuse(self.adapt(raw))["incident_card_version_fields"]["data"]["event_type"], "FLOOD")

    def test_old_fusion_and_completeness_outputs_are_ignored(self):
        raw = demo_fixture()
        raw["fusion"] = {"Event_Type": "UNCERTAIN", "Event_Status": "FALSE_EVENT"}
        raw["completeness"] = {"missing_fields": ["location"], "adaptive_questions": ["pertanyaan lama"]}
        result = self.adapt(raw)
        fused = self.fuse(result)
        self.assertEqual(fused["incident_card_version_fields"]["data"]["event_type"], "FLOOD")
        self.assertNotIn("completeness", result)

    def test_confidence_below_and_at_threshold(self):
        result = self.adapt(make_synthetic_legacy("Air naik", confidence=0.7))
        below = self.fuse(result, threshold=0.8)["incident_card_version_fields"]
        equal = self.fuse(result, threshold=0.7)["incident_card_version_fields"]
        self.assertEqual(below["uncertain_reasons"], ["LOW_CLASSIFICATION_CONFIDENCE"])
        self.assertEqual(below["data"]["event_type"], "FLOOD")
        self.assertFalse(equal["uncertain"])

    def test_missing_calibration_is_rejected(self):
        for threshold, reference in [(None, "fixture"), (0.8, None), (0.8, "")]:
            with self.subTest(threshold=threshold, reference=reference):
                with self.assertRaises(CalibrationRequiredError):
                    fuse_for_silar(self.adapt(), confidence_threshold=threshold, calibration_reference=reference)

    def test_relative_time_does_not_become_timestamp(self):
        raw = make_synthetic_legacy("Kemarin banjir", role_phrases={"TIME-ARG": ["Kemarin"]})
        data = self.adapt(raw)["nara_result"]["normalized_output"]
        self.assertEqual(data["time_text"], "Kemarin")
        self.assertIsNone(data["occurred_at"])

    def test_existing_time_fallback_is_preserved_and_marked(self):
        raw = make_synthetic_legacy("Kemarin banjir")
        raw["incident_card"] = {"time": ["Kemarin"], "time_source": "DETERMINISTIC_FALLBACK"}
        result = self.adapt(raw)
        self.assertEqual(result["nara_result"]["normalized_output"]["time_text"], "Kemarin")
        self.assertIn({"code": "TIME_FROM_DETERMINISTIC_FALLBACK", "field": "time_text"}, result["nara_result"]["normalization_warnings"])

    def test_unsupported_time_fallback_or_ungrounded_value_is_rejected(self):
        for card in [
            {"time": ["Kemarin"], "time_source": "UNKNOWN_SOURCE"},
            {"time": ["besok"], "time_source": "DETERMINISTIC_FALLBACK"},
        ]:
            raw = make_synthetic_legacy("Kemarin banjir")
            raw["incident_card"] = card
            with self.subTest(card=card):
                with self.assertRaises(AdapterValidationError):
                    self.adapt(raw)

    def test_victim_suppressed_by_upstream_guard_is_not_reintroduced(self):
        raw = make_synthetic_legacy("Tidak ada korban meninggal", role_phrases={"DEATHVICTIM-ARG": ["korban meninggal"]})
        raw["srl_spans"]["DEATHVICTIM-ARG"] = []  # Simulasi hasil guard lama.
        result = self.adapt(raw)
        self.assertEqual(result["nara_result"]["normalized_output"]["victims"], [])
        self.assertTrue(any(t["label"] == "DEATHVICTIM-ARG" for t in result["nara_result"]["raw_output"]["srl_token_predictions"]))

    def test_partial_token_coverage_is_recorded(self):
        raw = make_synthetic_legacy("Air mulai naik")
        raw["srl_token_predictions"] = raw["srl_token_predictions"][:1]
        result = self.adapt(raw)
        self.assertFalse(result["adapter_metadata"]["nara_token_coverage_complete"])
        self.assertEqual(result["adapter_metadata"]["nara_source_tokens"], 3)

    def test_empty_tokens_unknown_label_and_bad_offsets_are_rejected(self):
        variants = []
        raw = demo_fixture(); raw["srl_token_predictions"] = []; variants.append(raw)
        raw = demo_fixture(); raw["srl_token_predictions"][0]["label"] = "NEW-LABEL"; variants.append(raw)
        raw = demo_fixture(); raw["srl_token_predictions"][0]["start"] = 1; variants.append(raw)
        for raw in variants:
            with self.subTest(variant=variants.index(raw)):
                with self.assertRaises(AdapterValidationError):
                    self.adapt(raw)

    def test_missing_span_role_and_ungrounded_span_are_rejected(self):
        raw = demo_fixture(); del raw["srl_spans"]["TIME-ARG"]
        with self.assertRaises(AdapterValidationError): self.adapt(raw)
        raw = demo_fixture(); raw["srl_spans"]["PLACE-ARG"][0]["text"] = "lokasi yang tidak disebut"
        with self.assertRaises(AdapterValidationError): self.adapt(raw)

    def test_legacy_punctuation_spacing_is_accepted(self):
        raw = make_synthetic_legacy("Api di Jl.A.Yani", role_phrases={"PLACE-ARG": ["Jl.A.Yani"]})
        raw["srl_spans"]["PLACE-ARG"][0]["text"] = "Jl . A . Yani"
        self.assertEqual(self.adapt(raw)["nara_result"]["normalized_output"]["location_text"], "Jl. A. Yani")

    def test_substring_inside_another_word_is_not_grounding(self):
        raw = make_synthetic_legacy("tetapi", role_phrases={"PLACE-ARG": ["tetapi"]})
        raw["srl_spans"]["PLACE-ARG"][0]["text"] = "api"
        with self.assertRaises(AdapterValidationError): self.adapt(raw)

    def test_nan_boolean_and_inconsistent_probabilities_are_rejected(self):
        for value in [float("nan"), float("inf"), True, -0.1, 1.1]:
            raw = demo_fixture(); raw["event_classifier"]["confidence"] = value
            with self.subTest(value=value):
                with self.assertRaises(AdapterValidationError): self.adapt(raw)
        raw = demo_fixture(); raw["event_classifier"]["probabilities"]["FLOOD"] = 0.1
        with self.assertRaises(AdapterValidationError): self.adapt(raw)

    def test_mixed_narratives_and_modified_sena_projection_are_rejected(self):
        result = self.adapt(); result["nara_result"]["narrative_id"] = "OTHER-SOURCE"
        with self.assertRaises(AdapterValidationError): self.fuse(result)
        result = self.adapt(); result["sena_result"]["category"] = "FIRE"
        with self.assertRaises(AdapterValidationError): self.fuse(result)

    def test_schema_injection_and_unverified_ambiguity_are_rejected(self):
        result = self.adapt(); result["nara_result"]["normalized_output"]["event_type"] = "FIRE"
        with self.assertRaises(AdapterValidationError): self.fuse(result)
        result = self.adapt(); result["nara_result"]["normalization_warnings"].append({"code": "EXTRACTION_AMBIGUITY", "field": "impacts"})
        with self.assertRaises(AdapterValidationError): self.fuse(result)

    def test_fusion_has_no_alias_to_adapted_record(self):
        result = self.adapt()
        fused = self.fuse(result)
        fused["incident_card_version_fields"]["data"]["impacts"].append("perubahan fixture")
        self.assertEqual(result["nara_result"]["normalized_output"]["impacts"], ["Dua rumah terendam"])

    def test_fused_data_has_exactly_eight_fields_without_auto_verification(self):
        fused = self.fuse(self.adapt())
        data = fused["incident_card_version_fields"]["data"]
        self.assertEqual(set(data), set(EXTRACTION_FIELDS) | {"event_type"})
        self.assertNotIn("human_verified", data)
        self.assertNotIn("workflow_status", data)
        self.assertNotIn("report_text", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
