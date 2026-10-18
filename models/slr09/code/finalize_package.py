"""Create and verify the deliverable ZIP after packaging QA has passed."""
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    qa = json.loads((ROOT / "evidence/package_qa.json").read_text())
    assert len(qa["notebooks"]) == 9
    assert all(r["schema_valid"] and r["syntax_valid"] for r in qa["notebooks"])
    assert qa["original_sources"]["all_original_code_cells_unchanged"]
    assert not qa["new_sena_training_notebook"]["gpu_training_executed"]
    assert not qa["completed_nara_tests_repeated"]
    assert qa["completed_external_sena_run_update"]["training_code_cells_unchanged"]
    assert qa["completed_external_sena_run_update"]["threshold_selected_for_integration_not_deployed"]
    assert qa["completed_external_sena_run_update"]["confidence_threshold"] == .95
    assert qa["completed_external_sena_run_update"]["synthetic_fusion_checks_passed"] == 9
    sena_qa = json.loads((ROOT / "results/sena_reviewed_620/independent_qa.json").read_text())
    assert all(r["passed"] for r in sena_qa["checks"])
    for directory in ROOT.rglob("__pycache__"):
        shutil.rmtree(directory)
    members = [p for p in sorted(ROOT.rglob("*")) if p.is_file() and p.name != "FILE_MANIFEST.json"]
    manifest = {"schema": "slr09-notebook-snapshot-0.1", "weights_included": False,
        "new_gpu_training_executed": False,
        "completed_external_sena_run": "20261018T044447_926664Z",
        "threshold_activated": False,
        "selected_threshold_for_integration": .95, "selected_option": "A",
        "production_deployed": False,
        "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                   "sha256": digest(p.read_bytes())} for p in members]}
    (ROOT / "FILE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    target = ROOT.parent / (ROOT.name + ".zip")
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for p in sorted(ROOT.rglob("*")):
            if p.is_file(): archive.write(p, ROOT.name + "/" + p.relative_to(ROOT).as_posix())
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        for entry in manifest["files"]:
            raw = archive.read(ROOT.name + "/" + entry["path"])
            assert len(raw) == entry["bytes"] and digest(raw) == entry["sha256"]
    print(json.dumps({"zip": str(target), "bytes": target.stat().st_size,
        "files_in_manifest": len(manifest["files"]), "manifest_and_crc_verified": True,
        "sha256": digest(target.read_bytes()), "new_gpu_training_executed": False}, indent=2))


if __name__ == "__main__":
    main()
