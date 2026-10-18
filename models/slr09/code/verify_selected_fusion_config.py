"""Check the selected configuration with synthetic Fusion fixtures, without models.

These checks establish configuration and boundary behavior only. They neither
re-evaluate model accuracy nor verify enforcement by a deployed backend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(root):
    root = Path(root)
    config_path = root / "config/SLR09_Konfigurasi_Integrasi_v0.1.json"
    config = load(config_path)
    decision = load(root / "config/threshold_decision.json")
    options = load(root / "config/threshold_options.json")
    models = load(root / "config/model_candidates.json")
    analysis = load(root / "results" / ("sena_finetune_" + config["reference_run_id"])
                    / "completed_run_analysis.json")
    selected = next(o for o in options["options"] if o["option"] == config["selected_option"])
    assert decision["decision_source"] == "EXPLICIT_USER_INSTRUCTION"
    assert decision["scope"] == "CANDIDATE_INTEGRATION_CONFIGURATION"
    assert config["selected_option"] == options["selected_option"] == decision["selected_option"] == "A"
    assert (config["confidence_threshold"] == options["confidence_threshold"]
            == decision["confidence_threshold"] == models["threshold_selected"] == .95)
    assert config["calibration_reference"] == options["calibration_reference"] == selected["calibration_reference"]
    assert config["sena"] == models["sena"] and config["nara"] == models["nara"]
    assert config["sena"]["weights_sha256"] == decision["sena_weights_sha256"] == options["sena_weights_sha256"]
    assert config["sena"]["weights_sha256"] == analysis["model_export_manifest"]["files_sha256"]["model.safetensors"]
    source_report = root / "sources" / ("SLR09_SENA_Hasil_FineTune_" + config["reference_run_id"] + ".zip")
    assert (hashlib.sha256(source_report.read_bytes()).hexdigest()
            == config["reference_report_sha256"] == decision["reference_report_sha256"])
    assert not options["activated"] and not config["production_deployed"]
    assert not config["production_model_selected"] and not models["production_model_selected"]
    assert not config["quality_acceptance_approved"] and not config["probability_calibration_fitted"]
    assert not config["target_vm_loading_and_joint_new_model_inference_verified"]
    assert all(config["rules"].values())
    assert config["rules"]["human_verification_always_required"]

    adapter_directory = str(root / "code/active_nara_adapter")
    sys.path.insert(0, adapter_directory)
    try:
        from silar_ai_adapter import (
            ADAPTER_VERSION, FUSION_VERSION, EVENT_CATEGORIES, NARA_LABELS,
            CalibrationRequiredError, adapt_legacy_ai_output, fuse_for_silar,
        )
        assert config["adapter_version"] == ADAPTER_VERSION
        assert config["fusion_version"] == FUSION_VERSION

        def adapted_fixture(category, confidence, conflicting_nara_category=False):
            # Deliberately synthetic: these values are not model predictions.
            text = "Banjir" if conflicting_nara_category else "Laporan"
            spans = {role: [] for role in NARA_LABELS if role != "O"}
            role = "FLOOD-EVENT" if conflicting_nara_category else "O"
            if conflicting_nara_category:
                spans[role] = [{"role": role, "text": text, "mean_confidence": .99}]
            raw = {"report_text": text,
                "event_classifier": {"label": category, "confidence": confidence,
                    "probabilities": {label: confidence if label == category else (1-confidence)/4
                                      for label in EVENT_CATEGORIES}},
                "srl_token_predictions": [{"original": text, "token": text.lower(),
                    "start": 0, "end": len(text), "label": role, "confidence": .99}],
                "srl_spans": spans}
            return adapt_legacy_ai_output(raw, narrative_id="SYNTHETIC-CONTRACT-ONLY",
                sena_model_version="SENA-" + config["sena"]["run_id"],
                nara_model_version="NARA-" + config["nara"]["run_id"])

        checks = []
        for category in ("FIRE", "NON_EVENT"):
            for confidence in (.949, .950, .951):
                fixture = adapted_fixture(category, confidence)
                result = fuse_for_silar(fixture,
                    confidence_threshold=config["confidence_threshold"],
                    calibration_reference=config["calibration_reference"])
                fields = result["incident_card_version_fields"]
                expected_reasons = ["LOW_CLASSIFICATION_CONFIDENCE"] if confidence < .95 else []
                assert fields["uncertain_reasons"] == expected_reasons
                assert fields["uncertain"] is bool(expected_reasons)
                assert result["integration_signals"]["blocked_by_non_event"] is (category == "NON_EVENT")
                assert fields["data"]["event_type"] == (None if category == "NON_EVENT" else category)
                assert fields["data"]["location_text"] is None and fields["data"]["time_text"] is None
                assert fields["data"]["occurred_at"] is None
                assert all(fields["data"][name] == [] for name in
                           ("involved_parties", "impacts", "victims", "affected_objects"))
                assert result["fusion_metadata"]["calibration_reference"] == config["calibration_reference"]
                checks.append({"case": f"{category}_{confidence:.3f}", "confidence": confidence,
                    "uncertain": fields["uncertain"], "uncertain_reasons": fields["uncertain_reasons"],
                    "blocked_by_non_event": result["integration_signals"]["blocked_by_non_event"],
                    "empty_extraction_alone_adds_no_uncertain_reason": True, "passed": True})

        conflict_fixture = adapted_fixture("FIRE", .95, conflicting_nara_category=True)
        conflict_result = fuse_for_silar(conflict_fixture,
            confidence_threshold=config["confidence_threshold"],
            calibration_reference=config["calibration_reference"])
        assert conflict_result["incident_card_version_fields"]["data"]["event_type"] == "FIRE"
        checks.append({"case": "CATEGORY_FROM_SENA_WHEN_NARA_EVENT_LABEL_DIFFERS", "passed": True,
            "scope": "CATEGORY_PRECEDENCE_ONLY_NOT_GENERAL_SEMANTIC_CONFLICT_DETECTION"})

        for threshold, reference, name in [
            (None, config["calibration_reference"], "MISSING_THRESHOLD_REJECTED"),
            (config["confidence_threshold"], None, "MISSING_REFERENCE_REJECTED"),
        ]:
            try:
                fuse_for_silar(conflict_fixture, confidence_threshold=threshold, calibration_reference=reference)
            except CalibrationRequiredError:
                checks.append({"case": name, "passed": True})
            else:
                raise AssertionError(name)
    finally:
        sys.path.remove(adapter_directory)

    result = {"schema": "slr09-selected-threshold-contract-checks-0.1",
        "selected_option": config["selected_option"], "confidence_threshold": config["confidence_threshold"],
        "calibration_reference": config["calibration_reference"],
        "configuration_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "configuration_identity_consistent": True, "checks": checks, "all_passed": True,
        "fixture_source": "SYNTHETIC_CONTROLLED_VALUES_NOT_NEURAL_PREDICTIONS",
        "training_executed": False, "neural_inference_executed": False,
        "prior_nara_evaluation_or_adapter_diagnostic_repeated": False,
        "human_verification_required_in_configuration": True,
        "human_verification_backend_enforcement_verified": False,
        "production_deployed": False, "quality_acceptance_approved": False}
    evidence_path = root / "evidence/selected_threshold_contract_checks.json"
    evidence_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    result = verify(arguments.root)
    print(json.dumps({"selected_option": result["selected_option"],
        "confidence_threshold": result["confidence_threshold"], "checks_passed": len(result["checks"]),
        "all_passed": result["all_passed"], "neural_inference_executed": False}, indent=2))
