"""Validate new packaging/bootstrap without rerunning completed experiments."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def source_hash(nb):
    text = "\n\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    return hashlib.sha256(text.encode()).hexdigest()


def validate_notebooks():
    sys.path.insert(0, str(WORKSPACE / "tmp/slr09_nara03/qa_deps"))
    import nbformat
    from IPython.core.inputtransformer2 import TransformerManager
    transformer = TransformerManager()
    rows = []
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        nb = json.loads(path.read_text())
        nbformat.validate(nb)
        count = 0
        for i, cell in enumerate(nb["cells"]):
            if cell["cell_type"] == "code":
                compile(transformer.transform_cell("".join(cell["source"])), f"{path.name}:{i}", "exec")
                count += 1
        rows.append({"notebook": path.name, "schema_valid": True, "syntax_valid": True, "code_cells": count})
    return rows


def verify_sources():
    rows = json.loads((ROOT / "evidence/notebook_source_provenance.json").read_text())
    for row in rows:
        original = ROOT / row["source"]
        assert hashlib.sha256(original.read_bytes()).hexdigest() == row["source_sha256"]
        assert source_hash(json.loads(original.read_text())) == row["code_cells_sha256"]
        assert source_hash(json.loads((ROOT / row["notebook"]).read_text())) == row["code_cells_sha256"]
    return {"wrapped_notebooks_verified": len(rows), "all_original_code_cells_unchanged": True}


def run_summary():
    path = ROOT / "notebooks/00_SLR09_Hasil_Terverifikasi.ipynb"
    nb = json.loads(path.read_text())
    env_before = os.environ.get("SLR09_NOTEBOOK_ROOT")
    destination = WORKSPACE / "tmp/slr09_final_package_20261018/summary_notebook_qa"
    os.environ["SLR09_NOTEBOOK_ROOT"] = str(destination)
    namespace = {"__name__": "__main__"}
    executed = []
    try:
        for i, cell in enumerate(nb["cells"]):
            if cell["cell_type"] != "code":
                continue
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compile("".join(cell["source"]), f"summary:{i}", "exec"), namespace)
            text = output.getvalue()
            cell["execution_count"] = len(executed) + 1
            cell["outputs"] = [{"name": "stdout", "output_type": "stream", "text": text.splitlines(keepends=True)}]
            executed.append({"cell": i, "characters": len(text), "executed": True})
        nb.setdefault("metadata", {})["execution_provenance"] = {
            "mode": "local Python sequential execution", "reads_saved_results_only": True,
            "training_or_neural_inference_executed": False,
            "outputs_are_actual_stdout": True}
        path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n")
    finally:
        if env_before is None: os.environ.pop("SLR09_NOTEBOOK_ROOT", None)
        else: os.environ["SLR09_NOTEBOOK_ROOT"] = env_before
    return {"code_cells_executed": len(executed), "cells": executed, "neural_inference": False, "training": False}


def validate_new_training_bootstrap():
    path = ROOT / "notebooks/07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb"
    nb = json.loads(path.read_text())
    os.environ["SLR09_NOTEBOOK_ROOT"] = str(WORKSPACE / "tmp/slr09_final_package_20261018/sena_bootstrap_qa")
    namespace = {"__name__": "__main__"}
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            for i in [4, 5]:
                exec(compile("".join(nb["cells"][i]["source"]), f"SENA-bootstrap:{i}", "exec"), namespace)
        assert namespace["checked"]["train_narratives"] == 110
        assert namespace["checked"]["validation_narratives"] == 620
        assert not any(c.get("outputs") for c in nb["cells"] if c["cell_type"] == "code")
        files_equal = []
        for name in ["code/sena_experiment.py", "code/evaluate_sena_reviewed.py", "data/input_manifest.json",
                     "data/sena_train_reviewed.jsonl", "data/sena_validation_reviewed.jsonl", "data/baseline_reviewed_evaluation.json"]:
            assert (namespace["WORK_ROOT"] / name).read_bytes() == (ROOT / name).read_bytes()
            files_equal.append(name)
        assert not namespace["checked"]["test_used_for_training_or_selection"]
    finally:
        os.environ.pop("SLR09_NOTEBOOK_ROOT", None)
    return {"snapshot_restore_and_input_validation_executed": True, "byte_identical_files": files_equal,
        "train_narratives": 110, "validation_narratives": 620,
        "gpu_training_executed": False, "model_loading_or_reload_executed": False,
        "colab_drive_mount_executed": False, "no_fabricated_training_outputs": True,
        "stdout": output.getvalue()}


def validate_completed_run_update():
    evidence = json.loads((ROOT / "evidence/sena_training_source_unchanged.json").read_text())
    original = ROOT / evidence["source"]
    assert hashlib.sha256(original.read_bytes()).hexdigest() == evidence["source_sha256"]
    assert source_hash(json.loads(original.read_text())) == evidence["code_cells_sha256"]
    assert source_hash(json.loads((ROOT / "notebooks/07_SENA_FineTune_dan_Evaluasi_v0.1.ipynb").read_text())) == evidence["code_cells_sha256"]
    config = json.loads((ROOT / "config/threshold_options.json").read_text())
    models = json.loads((ROOT / "config/model_candidates.json").read_text())
    integration = json.loads((ROOT / "config/SLR09_Konfigurasi_Integrasi_v0.1.json").read_text())
    contracts = json.loads((ROOT / "evidence/selected_threshold_contract_checks.json").read_text())
    assert config["selected_option"] == "A" and not config["activated"]
    assert models["threshold_selected"] == .95 and not models["production_model_selected"]
    assert integration["confidence_threshold"] == .95 and not integration["production_deployed"]
    assert integration["calibration_reference"] == config["calibration_reference"]
    assert contracts["all_passed"] and len(contracts["checks"]) == 9
    assert contracts["configuration_sha256"] == hashlib.sha256((ROOT / "config/SLR09_Konfigurasi_Integrasi_v0.1.json").read_bytes()).hexdigest()
    assert all(row["passed"] for row in contracts["checks"])
    assert [(o["option"], o["confidence_threshold"]) for o in config["options"]] == [("A", .95), ("B", .9)]
    nb_path = ROOT / "notebooks/08_SENA_Analisis_Hasil_dan_Threshold.ipynb"
    nb = json.loads(nb_path.read_text())
    os.environ["SLR09_NOTEBOOK_ROOT"] = str(WORKSPACE / "tmp/slr09_sena_completed_20261018/analysis_reader_qa")
    namespace = {"__name__": "__main__"}
    executed = 0
    try:
        for i, cell in enumerate(nb["cells"]):
            if cell["cell_type"] != "code": continue
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compile("".join(cell["source"]), f"completed-analysis:{i}", "exec"), namespace)
            executed += 1
            cell["execution_count"] = executed
            cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": output.getvalue().splitlines(keepends=True)}]
        assert namespace["analysis"]["run_id"] == "20261018T044447_926664Z"
        assert namespace["analysis"]["confidence_threshold_selected"] is None
        assert namespace["integration"] == integration
        assert namespace["contract_checks"] == contracts
        nb.setdefault("metadata", {})["execution_provenance"] = {"mode": "actual sequential local Python execution",
            "reads_saved_results_only": True, "training_or_neural_inference_executed": False}
        nb_path.write_text(json.dumps(nb, indent=2, ensure_ascii=False) + "\n")
    finally:
        os.environ.pop("SLR09_NOTEBOOK_ROOT", None)
    return {"training_code_cells_unchanged": True, "threshold_selected_for_integration_not_deployed": True,
        "selected_option": "A", "confidence_threshold": .95, "synthetic_fusion_checks_passed": 9,
        "completed_run_analysis_reader_code_cells_executed": executed,
        "external_training_record_available": True, "external_training_locally_repeated": False}


def main():
    syntax = validate_notebooks()
    sources = verify_sources()
    reader = run_summary()
    bootstrap = validate_new_training_bootstrap()
    completed = validate_completed_run_update() if (ROOT / "evidence/sena_training_source_unchanged.json").exists() else None
    result = {"notebooks": syntax, "original_sources": sources, "summary_reader_execution": reader,
        "new_sena_training_notebook": bootstrap,
        "completed_external_sena_run_update": completed,
        "old_training_or_evaluation_repeated": False,
        "completed_nara_tests_repeated": False,
        "no_local_gpu_training_claimed": True}
    (ROOT / "evidence/package_qa.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
