"""New SENA pilot fine-tune; reuse the baseline predictions already evaluated.

This file prepares a NEW experiment. It is not evidence that training ran.
110 reviewed train narratives and 620 reviewed validation narratives retain
their existing roles. Three deferred references and all official test IDs are
excluded. Validation is used for model selection, not described as blind test.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from evaluate_sena_reviewed import LABELS, cutoff_analysis, score


CONFIG = {
    "seed": 42, "max_length": 256, "learning_rate": 2e-5,
    "train_batch_size": 16, "eval_batch_size": 32,
    "max_epochs": 10, "weight_decay": 0.01,
    "early_stopping_patience": 2, "metric_for_best_model": "macro_f1",
    "transformers_version": "4.57.1",
}
BASELINE_ARCHIVE_SHA256 = "e4af9d1e09023bcfb29670f2ff93d9aa477e8af6990d1ad21192d50486de57f6"
BASELINE_WEIGHTS_SHA256 = "ae7ceb9959b7f0f3c55a6babd2cf73759a1d9458daadb654ca2fb68ca25cc4dc"


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_reviewed_data(root: Path) -> dict:
    """Standard-library validation; may be run without loading a model."""
    manifest = json.loads((root / "data/input_manifest.json").read_text())
    for relative, expected in manifest["sha256"].items():
        if file_hash(root / relative) != expected:
            raise ValueError("Frozen input differs: " + relative)
    train = read_rows(root / "data/sena_train_reviewed.jsonl")
    val = read_rows(root / "data/sena_validation_reviewed.jsonl")
    if len(train) != 110 or len(val) != 620:
        raise ValueError("Expected the existing 110 train and 620 validation references")
    train_ids = [r["id"] for r in train]
    val_ids = [r["id"] for r in val]
    if len(set(train_ids)) != len(train_ids) or len(set(val_ids)) != len(val_ids):
        raise ValueError("Duplicate narrative ID")
    if set(train_ids) & set(val_ids):
        raise ValueError("Train/validation overlap")
    for r in train + val:
        if r["final"] not in LABELS or r["status"] not in {"REVIEW_TERCATAT", "FINAL_TERWARIS"}:
            raise ValueError("Reference is not final: " + r["id"])
        if int(r["id"].split("-")[-1]) <= 250:
            raise ValueError("Official held-out source ID must not enter fine-tune: " + r["id"])
    pending_ids = {"BAN-01028", "KEB-01113", "BAN-01529"}
    if pending_ids & (set(train_ids) | set(val_ids)):
        raise ValueError("Deferred reference entered fine-tune")
    if {r["text"].casefold().strip() for r in train} & {r["text"].casefold().strip() for r in val}:
        raise ValueError("Exact text duplicate across train/validation")
    baseline = json.loads((root / "data/baseline_reviewed_evaluation.json").read_text())
    if baseline["records_scored"] != 620 or baseline["production_threshold_selected"]:
        raise ValueError("Unexpected baseline scope or selected threshold")
    return {"train": train, "validation": val, "baseline": baseline,
            "train_narratives": len(train), "validation_narratives": len(val),
            "train_class_counts": {label: sum(r["final"] == label for r in train) for label in LABELS},
            "validation_class_counts": {label: sum(r["final"] == label for r in val) for label in LABELS},
            "test_used_for_training_or_selection": False,
            "historical_sena_train_membership_verified": False}


class SenaExperiment:
    def __init__(self, root: Path, drive_folder: Path, config: dict | None = None):
        self.root = Path(root)
        self.drive = Path(drive_folder)
        self.config = dict(CONFIG if config is None else config)
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        self.work = self.root / "runs" / self.run_id
        self.results = self.work / "results"
        self.results.mkdir(parents=True, exist_ok=True)
        self.state = {"schema": "silar-sena-finetune-run-0.1", "run_id": self.run_id,
            "status": "INITIALIZED", "completed_stages": [], "config": self.config,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "training_attempted": False, "training_executed": False, "training_completed": False,
            "new_neural_inference_started": False, "new_neural_inference_executed": False, "baseline_neural_inference_repeated": False,
            "model_exported": False, "production_model_selected": False,
            "production_threshold_selected": False,
            "validation_is_independent_blind_test": False}
        save_json(self.results / "run_state.json", self.state)

    def _save_results_zip(self) -> Path:
        self.drive.mkdir(parents=True, exist_ok=True)
        target = self.drive / f"SLR09_SENA_Hasil_FineTune_{self.run_id}.zip"
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            for path in sorted(self.results.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(self.results).as_posix())
        return target

    def _stage(self, name: str, function):
        self.state.update(status="RUNNING", current_stage=name)
        save_json(self.results / "run_state.json", self.state)
        try:
            result = function()
            self.state["completed_stages"].append(name)
            self.state["status"] = "SUCCEEDED" if name == "EXPORT" else "STAGE_SUCCEEDED"
            save_json(self.results / "run_state.json", self.state)
            self._save_results_zip()
            return result
        except Exception as error:
            if name == "FINE_TUNE" and hasattr(self, "trainer"):
                self.state["optimizer_steps"] = int(self.trainer.state.global_step)
                self.state["training_executed"] = self.trainer.state.global_step > 0
            self.state.update(status="FAILED", error_type=type(error).__name__, error=str(error))
            (self.results / "error_traceback.txt").write_text(traceback.format_exc())
            save_json(self.results / "run_state.json", self.state)
            try:
                print("ZIP hasil sementara:", self._save_results_zip())
            except Exception as saving_error:
                print("Hasil sementara lokal:", self.results, type(saving_error).__name__)
            raise

    def prepare(self) -> dict:
        return self._stage("PREPARE", self._prepare)

    def _prepare(self) -> dict:
        import torch
        import transformers
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed
        if transformers.__version__ != self.config["transformers_version"]:
            raise RuntimeError("Use the pinned Transformers version and restart a previously used session")
        if not torch.cuda.is_available():
            raise RuntimeError("Pilih Runtime > Change runtime type > GPU di Colab; tahap ini adalah training baru")
        set_seed(self.config["seed"])
        self.data = validate_reviewed_data(self.root)
        self.train_rows = self.data["train"]
        self.val_rows = self.data["validation"]
        self.baseline = self.data["baseline"]["metrics_reviewed"]
        self.state.update(train_narratives=len(self.train_rows), validation_narratives=len(self.val_rows))
        source = self.drive / "SILAR_SENA_v1.zip"
        if not source.is_file() or file_hash(source) != BASELINE_ARCHIVE_SHA256:
            raise ValueError("ZIP SENA v1 pada Drive tidak ditemukan atau hash berbeda; jangan memakai model NARA")
        model_dir = self.work / "source_model"
        with ZipFile(source) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP SENA v1 rusak")
            for info in archive.infolist():
                relative = Path(info.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Invalid archive path")
                if info.is_dir():
                    continue
                destination = model_dir / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(info.filename))
        candidates = [p.parent for p in model_dir.rglob("config.json") if (p.parent / "model.safetensors").is_file()]
        if len(candidates) != 1:
            raise ValueError("Expected one exported SENA model root")
        model_path = candidates[0]
        if file_hash(model_path / "model.safetensors") != BASELINE_WEIGHTS_SHA256:
            raise ValueError("SENA baseline weight identity differs")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
        if [self.model.config.id2label[i] for i in range(len(LABELS))] != LABELS:
            raise ValueError("SENA five-label mapping differs")
        self.label2id = {label: i for i, label in enumerate(LABELS)}
        max_length = self.config["max_length"]
        lengths = [len(self.tokenizer(r["text"], truncation=False)["input_ids"]) for r in self.train_rows + self.val_rows]
        if max(lengths) > max_length:
            raise ValueError("Input exceeds the pinned maximum; review truncation before training")
        environment = {"python": platform.python_version(), "torch": torch.__version__,
                       "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(0),
                       "cuda": torch.version.cuda, "source_archive_sha256": BASELINE_ARCHIVE_SHA256,
                       "source_weights_sha256": BASELINE_WEIGHTS_SHA256}
        save_json(self.results / "environment.json", environment)
        summary = {k: v for k, v in self.data.items() if k not in {"train", "validation", "baseline"}}
        summary.update(max_wordpieces=max(lengths), truncated_narratives=0)
        save_json(self.results / "dataset_manifest.json", summary)
        save_json(self.results / "baseline_reviewed_metrics.json", self.baseline)
        save_json(self.results / "input_manifest.json", json.loads((self.root / "data/input_manifest.json").read_text()))
        return summary

    def fit(self) -> dict:
        return self._stage("FINE_TUNE", self._fit)

    def _fit(self) -> dict:
        import numpy as np
        from torch.utils.data import Dataset
        from transformers import DataCollatorWithPadding, EarlyStoppingCallback, Trainer, TrainingArguments

        class TextDataset(Dataset):
            def __init__(self, rows, tokenizer, label2id):
                self.values = []
                for row in rows:
                    encoded = tokenizer(row["text"], truncation=False)
                    encoded["labels"] = label2id[row["final"]]
                    self.values.append(encoded)
            def __len__(self):
                return len(self.values)
            def __getitem__(self, item):
                return self.values[item]

        def compute_metrics(evaluation):
            logits, ids = evaluation
            if isinstance(logits, tuple):
                logits = logits[0]
            result = score([LABELS[int(i)] for i in ids], [LABELS[int(i)] for i in np.argmax(logits, axis=1)])
            return {"accuracy": result["accuracy"], "macro_f1": result["macro_f1_all_five_classes"],
                    "weighted_f1": result["weighted_f1"]}

        args = TrainingArguments(
            output_dir=str(self.work / "checkpoints"), learning_rate=self.config["learning_rate"],
            per_device_train_batch_size=self.config["train_batch_size"],
            per_device_eval_batch_size=self.config["eval_batch_size"],
            num_train_epochs=self.config["max_epochs"], weight_decay=self.config["weight_decay"],
            eval_strategy="epoch", save_strategy="epoch", logging_strategy="epoch",
            load_best_model_at_end=True, metric_for_best_model="macro_f1", greater_is_better=True,
            save_total_limit=2, seed=self.config["seed"], data_seed=self.config["seed"],
            report_to="none", fp16=False, dataloader_num_workers=0,
        )
        self.val_dataset = TextDataset(self.val_rows, self.tokenizer, self.label2id)
        self.trainer = Trainer(model=self.model, args=args,
            train_dataset=TextDataset(self.train_rows, self.tokenizer, self.label2id),
            eval_dataset=self.val_dataset, processing_class=self.tokenizer,
            data_collator=DataCollatorWithPadding(self.tokenizer), compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=self.config["early_stopping_patience"])])
        self.state["training_attempted"] = True
        save_json(self.results / "run_state.json", self.state)
        output = self.trainer.train()
        self.model = self.trainer.model
        self.state.update(training_executed=self.trainer.state.global_step > 0,
            training_completed=True, optimizer_steps=self.trainer.state.global_step,
            best_checkpoint=self.trainer.state.best_model_checkpoint,
            best_validation_macro_f1=self.trainer.state.best_metric,
            epochs_completed=self.trainer.state.epoch)
        save_json(self.results / "training_result.json", output.metrics)
        save_json(self.results / "training_log_history.json", self.trainer.state.log_history)
        self._plot_training()
        return {k: self.state[k] for k in ["optimizer_steps", "best_checkpoint", "best_validation_macro_f1", "epochs_completed"]}

    def _plot_training(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        history = self.trainer.state.log_history
        train = [r for r in history if "loss" in r]
        val = [r for r in history if "eval_loss" in r]
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
        axes[0].plot([r["epoch"] for r in train], [r["loss"] for r in train], label="Train")
        axes[0].plot([r["epoch"] for r in val], [r["eval_loss"] for r in val], label="Validation")
        axes[0].set(xlabel="Epoch", ylabel="Loss", title="SENA pilot: loss"); axes[0].legend()
        axes[1].plot([r["epoch"] for r in val], [r["eval_macro_f1"] for r in val])
        axes[1].set(xlabel="Epoch", ylabel="Macro F1 (5 classes)", title="Validation used for checkpoint selection", ylim=(0, 1))
        fig.savefig(self.results / "training_curves.png", dpi=160); plt.close(fig)

    def evaluate(self) -> dict:
        return self._stage("EVALUATE", self._evaluate)

    def _evaluate(self) -> dict:
        import numpy as np
        import torch
        from evaluate_sena_reviewed import write_csv
        self.state["new_neural_inference_started"] = True
        save_json(self.results / "run_state.json", self.state)
        output = self.trainer.predict(self.val_dataset)
        logits = output.predictions[0] if isinstance(output.predictions, tuple) else output.predictions
        probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
        preds = np.argmax(probs, axis=1)
        rows = [{"id": r["id"], "text": r["text"], "gold": r["final"],
                 "prediction": LABELS[int(p)], "confidence": float(prob[int(p)]),
                 "probabilities": {label: float(prob[j]) for j, label in enumerate(LABELS)}}
                for r, p, prob in zip(self.val_rows, preds, probs)]
        metrics = score([r["gold"] for r in rows], [r["prediction"] for r in rows])
        save_json(self.results / "finetuned_validation_metrics.json", metrics)
        (self.results / "finetuned_validation_predictions.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        save_json(self.results / "cutoff_analysis.json", {"rows": cutoff_analysis(rows),
            "production_threshold_selected": False, "independent_test": False})
        write_csv(self.results / "per_class.csv", [{"label": label, **v} for label, v in metrics["per_class"].items()])
        errors = [r for r in rows if r["gold"] != r["prediction"]]
        save_json(self.results / "classification_errors.json", errors)
        comparison = {"baseline_reused_without_neural_rerun": self.baseline, "finetuned_validation": metrics,
            "validation_used_for_checkpoint_selection": True, "independent_blind_test": False,
            "historical_training_split_identity_verified": False, "official_test_evaluated": False,
            "new_model_production_ready": False}
        save_json(self.results / "comparison.json", comparison)
        self._plot_matrix(metrics)
        self.state["new_neural_inference_executed"] = True
        return {"accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1_all_five_classes"],
                "false_non_event": metrics["false_non_event_count"], "evaluated_narratives": len(rows)}

    def _plot_matrix(self, metrics):
        import csv
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        matrix = metrics["confusion_matrix_rows_gold_columns_prediction"]
        with (self.results / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(["gold/prediction", *LABELS])
            for label, row in zip(LABELS, matrix): writer.writerow([label, *row])
        fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
        plot = ax.imshow(matrix, cmap="Blues"); fig.colorbar(plot, ax=ax, shrink=.8)
        ax.set(xticks=range(5), yticks=range(5), xticklabels=LABELS, yticklabels=LABELS,
               xlabel="Prediction", ylabel="Reviewed reference", title="SENA: 620 validation narratives")
        plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
        for i, row in enumerate(matrix):
            for j, number in enumerate(row): ax.text(j, i, str(number), ha="center", va="center")
        fig.savefig(self.results / "confusion_matrix.png", dpi=160); plt.close(fig)

    def export(self) -> dict:
        return self._stage("EXPORT", self._export)

    def _export(self) -> dict:
        import torch
        from transformers import AutoModelForSequenceClassification
        export = self.work / "export_model"
        self.trainer.save_model(export); self.tokenizer.save_pretrained(export)
        metadata = {"project": "SILAR", "model": "SENA reviewed pilot", "run_id": self.run_id,
            "classes": LABELS, "config": self.config,
            "source_weights_sha256": BASELINE_WEIGHTS_SHA256,
            "train_ids": [r["id"] for r in self.train_rows],
            "validation_ids": [r["id"] for r in self.val_rows],
            "official_test_used_for_training_or_selection": False,
            "historical_base_training_membership_verified": False,
            "production_model_selected": False, "production_threshold_selected": False}
        save_json(export / "experiment_metadata.json", metadata)
        samples = self.tokenizer([r["text"] for r in self.val_rows[:3]], padding=True, return_tensors="pt")
        device = next(self.model.parameters()).device
        samples = {key: value.to(device) for key, value in samples.items()}
        self.model.eval()
        with torch.no_grad(): before = self.model(**samples).logits.detach().cpu()
        reloaded = AutoModelForSequenceClassification.from_pretrained(export, local_files_only=True).to(device).eval()
        with torch.no_grad(): after = reloaded(**samples).logits.detach().cpu()
        if not torch.allclose(before, after, atol=1e-5, rtol=1e-5):
            raise ValueError("Model reload logits differ on the three verification samples")
        del reloaded
        target = self.drive / f"SILAR_SENA_reviewed_pilot_{self.run_id}.zip"
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            for p in sorted(export.rglob("*")):
                if p.is_file(): archive.write(p, p.relative_to(export).as_posix())
        manifest = {"archive_name": target.name, "archive_sha256": file_hash(target),
            "files_sha256": {p.relative_to(export).as_posix(): file_hash(p) for p in sorted(export.rglob("*")) if p.is_file()},
            "reload_sample_count": 3, "reload_logits_match": True,
            "production_model_selected": False, "production_threshold_selected": False}
        save_json(self.results / "model_export_manifest.json", manifest)
        self.state.update(model_exported=True, model_archive_path=str(target),
                          finished_utc=datetime.now(timezone.utc).isoformat())
        return {"model_zip": str(target),
                "results_zip": str(self.drive / f"SLR09_SENA_Hasil_FineTune_{self.run_id}.zip"),
                "reload_logits_match": True, "production_model_selected": False}
