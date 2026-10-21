"""Pemeriksaan sintetis runtime/analisis; tidak mengeksekusi model neural."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from slr09_runtime import (
    asset_lock, build_adapter_input, encode_nara_words, read_records,
    sha256_file, text_digest, validate_prediction, write_json,
)
from slr09_calibration import SPLIT_STATUS, summarize_predictions, threshold_table
from silar_ai_adapter import EVENT_CATEGORIES, EXTRACTION_FIELDS, adapt_legacy_ai_output


def prediction(label, confidence):
    return {"label": label, "confidence": confidence,
            "probabilities": {name: confidence if name == label else (1 - confidence) / 4 for name in EVENT_CATEGORIES}}


class FakeTokenizer:
    cls_token_id, sep_token_id, unk_token = 3, 4, "[UNK]"

    def tokenize(self, token):
        return {"empty": [], "long": ["a", "b", "c", "d"]}.get(token, [token])

    def convert_tokens_to_ids(self, tokens):
        return [{"[UNK]": 1, "a": 10, "b": 11, "c": 12, "d": 13}.get(token, 20) for token in tokens]


class RuntimeContractTests(unittest.TestCase):
    def test_first_wordpiece_positions_and_unknown_token(self):
        encoded = encode_nara_words(["x", "long", "empty"], FakeTokenizer())
        self.assertEqual(encoded["input_ids"], [3, 20, 10, 11, 12, 13, 1, 4])
        self.assertEqual(encoded["positions"], [1, 2, 6])
        self.assertEqual(encoded["attention_mask"], [1] * 8)
        self.assertFalse(encoded["partial_last_word"])

    def test_wordpiece_limit_preserves_sep_and_reports_partial_word(self):
        encoded = encode_nara_words(["long", "x"], FakeTokenizer(), max_length=5)
        self.assertEqual(encoded["input_ids"], [3, 10, 11, 12, 4])
        self.assertEqual(encoded["positions"], [1])
        self.assertTrue(encoded["partial_last_word"])

    def test_exact_256_limit_omits_later_words(self):
        encoded = encode_nara_words(["x"] * 300, FakeTokenizer())
        self.assertEqual(len(encoded["input_ids"]), 256)
        self.assertEqual(len(encoded["positions"]), 254)
        self.assertFalse(encoded["partial_last_word"])

    def test_victim_guard_does_not_overwrite_raw_tokens_or_before_guard_trace(self):
        import legacy_postprocessing as legacy
        text = "Kecelakaan tanpa korban meninggal tadi pagi."
        tokens = legacy.tokenize_with_offsets(text)
        for item in tokens:
            item.update(label="DEATHVICTIM-ARG" if item["token"] == "meninggal" else "O", confidence=0.9)
        original = deepcopy(tokens)
        raw, trace = build_adapter_input(text, prediction("ACCIDENT", 0.9), tokens)
        adapted = adapt_legacy_ai_output(raw, narrative_id="SYNTHETIC", sena_model_version="SILAR_SENA_v1", nara_model_version="SILAR_NARA_v1")
        self.assertEqual(tokens, original)
        self.assertTrue(trace["spans_before_guard"]["DEATHVICTIM-ARG"])
        self.assertEqual(raw["srl_spans"]["DEATHVICTIM-ARG"], [])
        self.assertEqual(adapted["nara_result"]["normalized_output"]["victims"], [])
        self.assertEqual(adapted["nara_result"]["normalized_output"]["time_text"], "tadi pagi")
        self.assertEqual(set(adapted["nara_result"]["normalized_output"]), set(EXTRACTION_FIELDS))
        self.assertNotIn("fusion", raw)
        self.assertNotIn("completeness", raw)

    def test_invalid_probability_map_cannot_be_calibrated(self):
        valid = prediction("FLOOD", 0.8)
        for change in ({"confidence": True}, {"confidence": float("nan")}, {"label": "OTHER"},
                       {"probabilities": {"FLOOD": 1.0}}, {"confidence": 0.7}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_prediction({**valid, **change})

    def test_records_reject_duplicate_ids_and_empty_narrative(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.jsonl"
            for rows in ([{"id": "A", "text": "banjir"}] * 2,
                         [{"id": "A", "text": "  "}], [{"id": True, "text": "banjir"}]):
                path.write_text("\n".join(json.dumps(row) for row in rows))
                with self.assertRaises(ValueError):
                    read_records(path)

    def test_threshold_equality_and_non_event_errors_are_counted(self):
        pairs = [("FLOOD", prediction("FLOOD", 0.8)), ("FIRE", prediction("NON_EVENT", 0.7)),
                 ("NON_EVENT", prediction("FIRE", 0.6)), ("ACCIDENT", prediction("ACCIDENT", 0.6))]
        table = {row["threshold"]: row for row in threshold_table(pairs)}
        self.assertEqual(table[0.6]["n_above_or_equal"], 4)
        self.assertEqual(table[0.8]["n_above_or_equal"], 1)
        self.assertEqual(table[0.8]["accuracy_above_or_equal"], 1)
        self.assertEqual(table[0.8]["false_non_event_below"], 1)
        self.assertEqual(table[1.0]["n_above_or_equal"], 0)
        self.assertIsNone(table[1.0]["accuracy_above_or_equal"])


class ThresholdEvidenceTests(unittest.TestCase):
    """Seluruh bukti di fixture ini buatan khusus tes, bukan hasil inferensi."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inputs = [{"id": "S1", "text": "banjir", "gold_label": "FLOOD"},
                       {"id": "S2", "text": "kebakaran", "gold_label": "FIRE"},
                       {"id": "S3", "text": "simulasi", "gold_label": "NON_EVENT"},
                       {"id": "S4", "text": "tabrakan", "gold_label": "ACCIDENT"}]
        self.input = self.root / "candidate_validation.jsonl"
        self.input.write_text("".join(json.dumps(row) + "\n" for row in self.inputs))
        self.rows = [{"id": row["id"], "input_sha256": text_digest(row["text"]), "event_classifier": pred}
                     for row, pred in zip(self.inputs, [prediction("FLOOD", 0.8), prediction("NON_EVENT", 0.7),
                                                        prediction("FIRE", 0.6), prediction("ACCIDENT", 0.6)])]
        self.predictions = self.root / "predictions.jsonl"
        self.run_path = self.root / "run_summary.json"
        self.split_path = self.root / "split_manifest.json"
        for name, values in (("validation", [row["id"] for row in self.inputs]), ("train", ["TRAIN"]), ("test", ["TEST"])):
            write_json(self.root / f"{name}_ids.json", values)
        self.split = {"split_status": SPLIT_STATUS, "historical_split_identity_verified": False,
                      "files_sha256": {name: sha256_file(self.root / name) for name in
                                       ("candidate_validation.jsonl", "validation_ids.json", "train_ids.json", "test_ids.json")}}
        self.run = {"status": "SUCCEEDED", "mode": "sena", "model_inference_executed": True,
                    "SYNTHETIC_TEST_EVIDENCE_ONLY": True,
                    "input_sha256": sha256_file(self.input), "records_completed": 4,
                    "models": {"sena": {"files": asset_lock()["models"]["sena"]["files"]}}}
        self.flush()

    def flush(self):
        self.predictions.write_text("".join(json.dumps(row) + "\n" for row in self.rows))
        self.run["predictions_sha256"] = sha256_file(self.predictions)
        write_json(self.run_path, self.run)
        write_json(self.split_path, self.split)

    def summarize(self):
        return summarize_predictions(self.input, self.predictions, self.run_path, self.split_path, self.root / "analysis")

    def test_metrics_calculate_from_all_five_classes_without_selecting_threshold(self):
        result = self.summarize()
        self.assertEqual(result["records"], 4)
        self.assertEqual(result["accuracy"], 0.5)
        self.assertAlmostEqual(result["macro_f1_all_five_classes"], 0.4)
        self.assertEqual(result["false_non_event_rate_among_gold_events"], 1 / 3)
        self.assertIsNone(result["production_confidence_threshold"])
        self.assertFalse(result["production_threshold_selected"])
        self.assertFalse(result["historical_split_identity_verified"])

    def test_changed_prediction_bytes_rejected(self):
        self.predictions.write_text(self.predictions.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "Hash input/prediksi"):
            self.summarize()

    def test_foreign_duplicate_missing_or_mismatched_text_prediction_rejected(self):
        original = deepcopy(self.rows)
        for mutation in ("foreign", "duplicate", "missing", "text"):
            self.rows = deepcopy(original)
            if mutation == "foreign":
                self.rows[0]["id"] = "OTHER"
            elif mutation == "duplicate":
                self.rows.append(deepcopy(self.rows[0]))
            elif mutation == "missing":
                self.rows.pop()
            else:
                self.rows[0]["input_sha256"] = text_digest("narasi berbeda")
            self.flush()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.summarize()

    def test_incomplete_or_unexecuted_model_run_rejected(self):
        for changes in ({"status": "FAILED"}, {"model_inference_executed": False}, {"records_completed": 3}):
            original = deepcopy(self.run)
            self.run.update(changes)
            self.flush()
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.summarize()
            self.run = original

    def test_train_overlap_rejected_even_if_manifest_hash_updated(self):
        write_json(self.root / "train_ids.json", ["S1"])
        self.split["files_sha256"]["train_ids.json"] = sha256_file(self.root / "train_ids.json")
        self.flush()
        with self.assertRaisesRegex(ValueError, "tumpang tindih"):
            self.summarize()

    def test_wrong_model_weights_rejected(self):
        self.run["models"]["sena"]["files"]["model.safetensors"] = "0" * 64
        self.flush()
        with self.assertRaisesRegex(ValueError, "bukan aset SENA"):
            self.summarize()


if __name__ == "__main__":
    unittest.main()
