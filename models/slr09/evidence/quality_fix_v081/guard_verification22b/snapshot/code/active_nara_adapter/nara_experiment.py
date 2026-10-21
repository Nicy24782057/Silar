"""Eksperimen NARA: baseline aktual, fine-tune, evaluasi, dan ekspor lokal.

Library neural diimpor saat prepare(). File ini tidak melatih saat diimpor.
Tidak menjalankan training SENA, memilih threshold produksi, atau deployment.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import shutil
import time
import traceback
import zipfile

import numpy as np

from nara_data import (LABELS, FeatureDataset, dump, dump_jsonl, extract_baseline_model,
                       load_historical_test, load_locked_data, make_features, read_jsonl, sha256)
from nara_metrics import compute_metrics, save_evaluation
from silar_ai_adapter import EXTRACTION_FIELDS, adapt_legacy_ai_output
from silar_victim_guard import VICTIM_GUARD_VERSION
from slr09_runtime import build_adapter_input, encode_nara_words, text_digest
import legacy_postprocessing as legacy

DEFAULT_CONFIG = {"seed": 42, "max_length": 256, "learning_rate": 2e-5,
                  "train_batch_size": 16, "eval_batch_size": 32, "max_epochs": 10,
                  "weight_decay": .01, "early_stopping_patience": 2,
                  "metric_for_best_model": "macro_f1_no_o", "logging_strategy": "epoch",
                  "transformers_version": "4.57.1"}


def protected_step(stage):
    def decorate(function):
        def wrapped(self, *args, **kwargs):
            self.state.update(status="RUNNING", current_stage=stage)
            self._save_state()
            try:
                result = function(self, *args, **kwargs)
                self.state["completed_stages"].append(stage)
                self._save_state()
                self.save_small_results()
                return result
            except Exception as error:
                if hasattr(self, "trainer"):
                    self.state["training_executed"] = bool(self.trainer.state.global_step > 0)
                self.state.update(status="FAILED", failed_stage=stage,
                                  error={"type": type(error).__name__, "message": str(error)})
                dump(self.results / "failure_trace.json", {"traceback": traceback.format_exc()})
                self._save_state()
                self.save_small_results()
                raise
        return wrapped
    return decorate


class NaraExperiment:
    def __init__(self, root, assets_directory, work_directory, *, config=None):
        self.root = Path(root).resolve()
        self.assets = Path(assets_directory).resolve()
        self.work = Path(work_directory).resolve()
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        self.run_dir = self.work / "runs" / self.run_id
        self.results = self.run_dir / "results"
        self.results.mkdir(parents=True, exist_ok=False)
        self.state = {"schema_version": "silar-nara-finetune-run-0.1", "run_id": self.run_id,
                      "status": "PREPARING", "current_stage": "INITIALIZED", "completed_stages": [],
                      "training_executed": False, "training_completed": False,
                      "neural_inference_executed": False, "model_exported": False,
                      "production_model_selected": False, "production_threshold_selected": False,
                      "effective_annotation_policy": "nara-role-guideline-0.2",
                      "victim_guard_version": VICTIM_GUARD_VERSION,
                      "source_model": "SILAR_NARA_v1", "config": self.config,
                      "started_utc": datetime.now(timezone.utc).isoformat()}
        self._save_state()

    def _save_state(self):
        dump(self.results / "run_state.json", self.state)

    @protected_step("PREPARE")
    def prepare(self):
        import torch
        import transformers
        from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                                  DataCollatorForTokenClassification, EarlyStoppingCallback,
                                  Trainer, TrainingArguments, set_seed)
        self.torch = torch
        if transformers.__version__ != self.config["transformers_version"]:
            raise RuntimeError("Versi transformers berbeda. Jalankan sel instalasi pada notebook, lalu restart sesi bila library sudah terimpor.")
        if not torch.cuda.is_available():
            raise RuntimeError("GPU belum aktif. Pilih Runtime > Change runtime type > GPU (misalnya T4), lalu jalankan kembali notebook.")
        self.assets.mkdir(parents=True, exist_ok=True)
        self.records, self.manifest = load_locked_data(self.root)
        dump(self.results / "dataset_manifest.json", self.manifest)
        dump(self.results / "environment.json", {"python": platform.python_version(),
             "gpu": torch.cuda.get_device_name(0), "cuda_runtime": torch.version.cuda,
             "packages": {name: importlib.metadata.version(name) for name in
                          ("torch", "transformers", "accelerate", "tokenizers", "safetensors", "numpy", "scikit-learn", "matplotlib")},
             "seed_is_not_a_guarantee_of_bitwise_identity_across_hardware": True})
        model_zip = self.assets / "SILAR_NARA_v1.zip"
        dataset_zip = self.assets / "Semantic Role Labeling Datasets for Crisis Event.zip"
        for path in (model_zip, dataset_zip):
            if not path.is_file():
                raise FileNotFoundError("Aset yang sudah digunakan sebelumnya belum ditemukan: " + str(path))
        cache = self.work / "zip_cache"
        cache.mkdir(parents=True, exist_ok=True)
        lock = json.loads((self.root / "data/asset_lock.json").read_text())
        cached = []
        for source, expected in ((model_zip, lock["models"]["nara"]["archive_sha256"]),
                                 (dataset_zip, lock["dataset"]["archive_sha256"])):
            target = cache / source.name
            if not target.is_file() or sha256(target) != expected:
                print("Menyalin aset ke cache runtime:", source.name, flush=True)
                shutil.copyfile(source, target)
            if sha256(target) != expected:
                raise ValueError("Hash arsip berbeda: " + source.name)
            cached.append(target)
        self.baseline_dir = extract_baseline_model(self.root, cached[0], self.work / "baseline_nara_v1")
        self.historical_test = load_historical_test(self.root, cached[1])
        set_seed(self.config["seed"])
        self.tokenizer = AutoTokenizer.from_pretrained(self.baseline_dir, use_fast=True,
                                                       local_files_only=True, trust_remote_code=False)
        model = AutoModelForTokenClassification.from_pretrained(
            self.baseline_dir, local_files_only=True, trust_remote_code=False, use_safetensors=True)
        if tuple(model.config.id2label[i] for i in range(15)) != LABELS:
            raise ValueError("Head model bukan 15 label yang disetujui")
        self.datasets, self.metadata = {}, {}
        for part, items in {**self.records, "historical_test": self.historical_test}.items():
            features, meta = make_features(items, self.tokenizer, self.config["max_length"])
            self.datasets[part], self.metadata[part] = FeatureDataset(features), meta
        dump(self.results / "alignment_audit.json", {
            "method": "Token sumber korpus → WordPiece → label pada piece pertama; piece lanjutan dan special token -100.",
            "inference_encoder_shared_with_training": True,
            "deployment_regex_units_are_a_separate_projection_from_source_corpus_units": True,
            "span_metrics_exclude_truncated_records": True,
            "by_partition": {part: {"narratives": len(meta),
                "truncated_narratives": sum(r["truncated"] for r in meta),
                "partial_last_word_narratives": sum(r["partial_last_word"] for r in meta),
                "source_words": sum(r["source_words"] for r in meta),
                "processed_words": sum(r["processed_words"] for r in meta),
                "different_source_vs_serving_segmentation_narratives": sum(not r["source_units_equal_runtime_regex_units"] for r in meta),
                "records": meta} for part, meta in self.metadata.items()}})
        self.collator = DataCollatorForTokenClassification(tokenizer=self.tokenizer, label_pad_token_id=-100)
        arguments = TrainingArguments(
            output_dir=str(self.run_dir / "checkpoints"), learning_rate=self.config["learning_rate"],
            per_device_train_batch_size=self.config["train_batch_size"],
            per_device_eval_batch_size=self.config["eval_batch_size"],
            num_train_epochs=self.config["max_epochs"], weight_decay=self.config["weight_decay"],
            eval_strategy="epoch", save_strategy="epoch", logging_strategy="epoch",
            load_best_model_at_end=True, metric_for_best_model=self.config["metric_for_best_model"],
            greater_is_better=True, save_total_limit=2, report_to="none", push_to_hub=False,
            seed=self.config["seed"], data_seed=self.config["seed"], fp16=True,
            optim="adamw_torch", dataloader_num_workers=0, save_safetensors=True)
        self.trainer = Trainer(model=model, args=arguments,
            train_dataset=self.datasets["train"], eval_dataset=self.datasets["validation"],
            processing_class=self.tokenizer, data_collator=self.collator,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=self.config["early_stopping_patience"])])
        self.state.update(train_narratives=len(self.records["train"]), validation_narratives=len(self.records["validation"]),
                          historical_test_narratives=len(self.historical_test),
                          baseline_weights_sha256=sha256(self.baseline_dir / "model.safetensors"))
        print("Data siap:", self.state["train_narratives"], "train /", self.state["validation_narratives"], "validation", flush=True)
        return self.state

    def _evaluate_dataset(self, trainer, dataset_key, directory, title):
        result = trainer.predict(self.datasets[dataset_key], metric_key_prefix="evaluation")
        self.state["neural_inference_executed"] = True
        records = self.historical_test if dataset_key == "historical_test" else self.records[dataset_key]
        return save_evaluation(result, records, self.metadata[dataset_key], self.results / directory, title)

    def _predict_runtime_tokens(self, model, text):
        tokens = legacy.tokenize_with_offsets(text)
        encoded = encode_nara_words([row["token"] for row in tokens], self.tokenizer, self.config["max_length"])
        model.eval()
        device = next(model.parameters()).device
        with self.torch.inference_mode():
            inputs = {name: self.torch.tensor([encoded[name]], dtype=self.torch.long, device=device)
                      for name in ("input_ids", "attention_mask")}
            probabilities = self.torch.softmax(model(**inputs).logits[0], dim=-1)
        output = []
        for token, position in zip(tokens, encoded["positions"]):
            index = int(probabilities[position].argmax().item())
            output.append({**token, "label": LABELS[index], "confidence": float(probabilities[position, index].item())})
        self.state["neural_inference_executed"] = True
        return output

    def _diagnostic_fields(self, model, name):
        references = json.loads((self.root / "data/nara_reviewed_84_fields.json").read_text())["records"]
        cached = {row["id"]: row for row in read_jsonl(self.root / "data/cached_neural_predictions.jsonl")}
        details, outputs, correct, nonempty_correct, nonempty_total = [], [], 0, 0, 0
        if set(cached) != {r["id"] for r in references}:
            raise ValueError("ID diagnostik/SENA cache berbeda")
        for reference in references:
            key, text = reference["id"], reference["text"]
            sena = cached[key]
            if sena["input_sha256"] != text_digest(text):
                raise ValueError("Teks diagnostik berbeda dari SENA cache")
            tokens = self._predict_runtime_tokens(model, text)
            raw, trace = build_adapter_input(text, sena["event_classifier"], tokens)
            adapted = adapt_legacy_ai_output(raw, narrative_id=key,
                sena_model_version="SILAR_SENA_v1_CACHED_ACTUAL_PREVIOUS_RUN",
                nara_model_version=name)
            for field in EXTRACTION_FIELDS:
                expected = reference["fields"][field]
                actual = adapted["nara_result"]["normalized_output"][field]
                matched = expected == actual
                correct += int(matched)
                populated = expected is not None and expected != [] and expected != ""
                nonempty_total += int(populated)
                nonempty_correct += int(populated and matched)
                details.append({"id": key, "field": field, "reference": expected, "prediction": actual, "exact": matched})
            outputs.append({"id": key, "nara_neural_inference_is_fresh": True,
                            "sena_neural_inference_is_fresh": False, "cached_sena_source_sha256": sha256(self.root / "data/cached_neural_predictions.jsonl"),
                            "adapted_result": adapted, "postprocessing_trace": trace})
        result = {"scope": "12 diagnostik dikenal/review setelah melihat prediksi; bukan blind test atau skor produksi.",
                  "nara_neural_inference_is_fresh": True, "sena_source": "ACTUAL_CACHED_PREVIOUS_RUN_NO_FRESH_SENA_INFERENCE",
                  "correct_fields_including_empty": correct, "total_fields": len(details),
                  "correct_nonempty_reference_fields": nonempty_correct, "nonempty_reference_fields": nonempty_total,
                  "production_fusion_executed": False, "details": details}
        dump(self.results / f"{name}_field_diagnostics.json", result)
        dump_jsonl(self.results / f"{name}_field_predictions.jsonl", outputs)
        return result

    @protected_step("BASELINE_VALIDATION")
    def baseline(self):
        self.baseline_validation = self._evaluate_dataset(self.trainer, "validation", "baseline_validation", "NARA v1 — reviewed validation (41 narratives)")
        self.baseline_fields = self._diagnostic_fields(self.trainer.model, "baseline_nara_v1")
        print("Baseline validation macro F1 non-O:", self.baseline_validation["token_metrics"]["macro_f1_no_o"], flush=True)
        return self.baseline_validation["token_metrics"]

    @protected_step("FINE_TUNE")
    def fit(self):
        if not hasattr(self, "baseline_validation"):
            raise RuntimeError("Jalankan baseline() sebelum fine-tune")
        result = self.trainer.train()
        self.state["training_executed"] = bool(self.trainer.state.global_step > 0)
        if not self.state["training_executed"]:
            raise RuntimeError("Tidak ada optimizer step yang selesai")
        self.state.update(training_completed=True, optimizer_steps=self.trainer.state.global_step,
                          best_checkpoint=self.trainer.state.best_model_checkpoint,
                          best_validation_macro_f1_no_o=self.trainer.state.best_metric,
                          epochs_completed=self.trainer.state.epoch)
        dump(self.results / "training_result.json", {"metrics": result.metrics,
             "optimizer_steps": self.trainer.state.global_step, "best_metric": self.trainer.state.best_metric,
             "best_checkpoint": self.trainer.state.best_model_checkpoint,
             "test_used_for_early_stopping_or_checkpoint_selection": False})
        dump(self.results / "training_log_history.json", self.trainer.state.log_history)
        self._plot_training()
        print("Fine-tune selesai; best checkpoint dimuat kembali.", flush=True)
        return self.state

    def _plot_training(self, title_prefix=""):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        history = self.trainer.state.log_history
        train = [r for r in history if "loss" in r and "epoch" in r]
        validation = [r for r in history if "eval_loss" in r and "epoch" in r]
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
        axes[0].plot([r["epoch"] for r in train], [r["loss"] for r in train], marker="o", label="Train loss")
        axes[0].plot([r["epoch"] for r in validation], [r["eval_loss"] for r in validation], marker="o", label="Validation loss")
        axes[0].set(xlabel="Epoch", ylabel="Loss", title=title_prefix + "NARA fine-tune loss")
        axes[1].plot([r["epoch"] for r in validation], [r["eval_macro_f1_no_o"] for r in validation], marker="o", label="Validation macro F1 (14 roles)")
        axes[1].axhline(self.baseline_validation["token_metrics"]["macro_f1_no_o"], color="gray", linestyle="--", label="Baseline v1")
        axes[1].set(xlabel="Epoch", ylabel="Macro F1 non-O", title=title_prefix + "Reviewed validation — checkpoint selection", ylim=(0, 1))
        for axis in axes:
            axis.grid(alpha=.2)
            axis.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(self.results / "training_curves.png", dpi=250)
        plt.close(fig)

    @protected_step("EVALUATE")
    def evaluate(self):
        if not self.state["training_completed"]:
            raise RuntimeError("Training belum selesai")
        self.fine_validation = self._evaluate_dataset(self.trainer, "validation", "finetuned_validation", "NARA fine-tuned — reviewed validation (41 narratives)")
        self.fine_fields = self._diagnostic_fields(self.trainer.model, "finetuned_nara")
        clinical = []
        for part, rows in self.records.items():
            for row in rows:
                if row["id"] not in {"KEC-01099", "KEC-01462", "KEB-00290", "KEC-01399"}:
                    continue
                predicted = self._predict_runtime_tokens(self.trainer.model, row["text"])
                before = legacy.all_srl_spans(predicted)
                from silar_victim_guard import apply_reviewed_victim_safety
                after, flags = apply_reviewed_victim_safety(row["text"], before)
                clinical.append({"id": row["id"], "split": part, "seen_in_finetune_training": part == "train",
                                 "text": row["text"], "token_predictions": predicted,
                                 "wound_after_guard": after["WOUNDVICTIM-ARG"], "guard_flags": flags,
                                 "scope": "Contoh inspeksi; dua kasus train tidak dihitung sebagai heldout."})
        dump_jsonl(self.results / "physical_condition_case_predictions.jsonl", clinical)
        # Test historis dibuka untuk prediksi SETELAH checkpoint terbaik dipilih.
        fine_test = self._evaluate_dataset(self.trainer, "historical_test", "finetuned_historical_test", "NARA fine-tuned — historical test labels (different policy)")
        from transformers import AutoModelForTokenClassification, Trainer, TrainingArguments
        baseline_model = AutoModelForTokenClassification.from_pretrained(self.baseline_dir,
            use_safetensors=True, trust_remote_code=False, local_files_only=True)
        baseline_trainer = Trainer(model=baseline_model,
            args=TrainingArguments(output_dir=str(self.run_dir / "baseline_test_eval"),
                per_device_eval_batch_size=self.config["eval_batch_size"], report_to="none", fp16=True),
            processing_class=self.tokenizer, data_collator=self.collator, compute_metrics=compute_metrics)
        baseline_test = self._evaluate_dataset(baseline_trainer, "historical_test", "baseline_historical_test", "NARA v1 — historical test labels")
        del baseline_trainer, baseline_model
        self.torch.cuda.empty_cache()
        baseline_f1 = self.baseline_validation["token_metrics"]["macro_f1_no_o"]
        fine_f1 = self.fine_validation["token_metrics"]["macro_f1_no_o"]
        comparison = {"reviewed_validation": {"narratives": len(self.records["validation"]),
            "baseline": self.baseline_validation["token_metrics"], "finetuned": self.fine_validation["token_metrics"],
            "macro_f1_no_o_delta": fine_f1 - baseline_f1,
            "interpretation": "Validation pilot dipakai memilih checkpoint, bukan estimasi generalisasi independen."},
            "historical_test": {"narratives": len(self.historical_test), "baseline": baseline_test["token_metrics"],
                "finetuned": fine_test["token_metrics"],
                "interpretation": "Gold asli belum diselaraskan ke pedoman 0.2; bukan skor test baru sesuai definisi revisi."},
            "diagnostic_12_fields": {"baseline_exact_including_empty": self.baseline_fields["correct_fields_including_empty"],
                "finetuned_exact_including_empty": self.fine_fields["correct_fields_including_empty"], "denominator": 84,
                "interpretation": "Diagnostik dikenal; SENA memakai prediksi aktual tersimpan, NARA inferensi baru; bukan akurasi produksi."},
            "automatic_production_promotion": False, "production_threshold_selected": False}
        dump(self.results / "comparison.json", comparison)
        print("Delta validation macro F1 non-O:", fine_f1 - baseline_f1, flush=True)
        return comparison

    @protected_step("EXPORT")
    def export(self):
        if not self.state["training_completed"]:
            raise RuntimeError("Training belum selesai; checkpoint lama tidak boleh diberi nama fine-tuned")
        target = self.run_dir / "SILAR_NARA_reviewed_pilot_v0.1"
        self.trainer.save_model(str(target))
        self.tokenizer.save_pretrained(target)
        if not (target / "model.safetensors").is_file():
            raise RuntimeError("Ekspor safetensors belum tersedia")
        weights_hash = sha256(target / "model.safetensors")
        if weights_hash == self.state["baseline_weights_sha256"]:
            raise RuntimeError("Bobot ekspor masih identik dengan baseline")
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        reloaded = AutoModelForTokenClassification.from_pretrained(target, local_files_only=True,
                    trust_remote_code=False, use_safetensors=True).to("cuda")
        reloaded_tokenizer = AutoTokenizer.from_pretrained(target, use_fast=True, local_files_only=True, trust_remote_code=False)
        if tuple(reloaded.config.id2label[i] for i in range(15)) != LABELS:
            raise ValueError("Head ekspor berubah")
        sample = self.records["validation"][0]["text"]
        before = self._predict_runtime_tokens(self.trainer.model, sample)
        after = self._predict_runtime_tokens(reloaded, sample)
        if [r["label"] for r in before] != [r["label"] for r in after]:
            raise RuntimeError("Reload ekspor mengubah label prediksi contoh")
        if self.tokenizer.get_vocab() != reloaded_tokenizer.get_vocab():
            raise RuntimeError("Vocab tokenizer ekspor berubah")
        del reloaded
        self.torch.cuda.empty_cache()
        metadata = {"model_id": "SILAR_NARA_reviewed_pilot_v0.1", "run_id": self.run_id,
                    "source_checkpoint": "SILAR_NARA_v1", "source_weights_sha256": self.state["baseline_weights_sha256"],
                    "new_weights_sha256": weights_hash, "labels": list(LABELS),
                    "effective_annotation_policy": "nara-role-guideline-0.2", "victim_guard_version": VICTIM_GUARD_VERSION,
                    "dataset_manifest_sha256": sha256(self.root / "data/dataset_manifest.json"),
                    "train_ids": [r["id"] for r in self.records["train"]],
                    "validation_ids": [r["id"] for r in self.records["validation"]],
                    "historical_test_not_used_for_training_or_model_selection": True,
                    "reload_inference_check_passed": True, "production_approved": False, "config": self.config}
        dump(target / "experiment_metadata.json", metadata)
        dump(self.results / "model_export_manifest.json", {**metadata,
             "files_sha256": {p.name: sha256(p) for p in sorted(target.iterdir()) if p.is_file()}})
        archive_path = self.run_dir / f"SILAR_NARA_reviewed_pilot_{self.run_id}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(target.iterdir()):
                # training_args.bin bukan bagian aset inferensi dan tidak diperlukan.
                if path.is_file() and path.suffix != ".bin":
                    archive.write(path, path.name)
        drive_model = self.assets / archive_path.name
        shutil.copyfile(archive_path, drive_model)
        self.state.update(model_exported=True, model_archive_path=str(drive_model),
                          model_archive_sha256=sha256(drive_model))
        self.state["status"] = "SUCCEEDED"
        self.state["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        results = self.assets / f"SLR09_NARA_Hasil_FineTune_{self.run_id}.zip"
        print("Model tersimpan di Drive:", drive_model, flush=True)
        print("Kirim ZIP hasil kecil ini:", results, flush=True)
        return {"model_zip": str(drive_model), "results_zip_to_return": str(results)}

    def save_small_results(self):
        self._save_state()
        archive_path = self.run_dir / f"SLR09_NARA_Hasil_FineTune_{self.run_id}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.results.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(self.results).as_posix())
        if self.assets.is_dir():
            target = self.assets / archive_path.name
            shutil.copyfile(archive_path, target)
            return target
        return archive_path
