import hashlib
from pathlib import Path

import pytest
from test_run_store import inputs

from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.persistence import persist_report
from smartregression.application.run_store import RunConflict, RunStorageError


class Store:
    def __init__(self, fail=False):
        self.writes = []
        self.fail = fail

    def save(self, write):
        if self.fail:
            raise RunStorageError()
        self.writes.append(write)


def publish(tmp_path: Path, stage_artifacts, fail=False):
    source, root = tmp_path / "input", tmp_path / "artifacts"
    source.mkdir()
    root.mkdir()
    files = ReportFiles(root, source_repository=source)
    args = inputs(stage_artifacts)
    kwargs = {k: args[k] for k in ("report", "configuration", "snapshot_manifests")}
    return files, args, kwargs, Store(fail)


def test_publication_retry_and_read_validate_bytes_and_identity(tmp_path, stage_artifacts):
    native_ids = [" tests/test_a.py::test_f \t", "tests/test_a.py::test_f[" + "\u00e9" * 300 + "]"]
    stage_artifacts["stages"]["inventory"] = {
        "status": "completed",
        "data": {
            "snapshot": stage_artifacts["identity"]["target"],
            "framework": "pytest",
            "test_ids": native_ids,
            "completeness": "complete",
        },
    }
    files, args, kwargs, store = publish(tmp_path, stage_artifacts)
    for _ in range(2):
        write = persist_report(
            files, store, artifact_id="file-1", storage_key="reports/1.json", **kwargs
        )
    assert len(store.writes) == 2
    restored = files.read(
        write.artifact, expected_identity=write.identity, expected_report_id=write.report_id
    )
    assert restored == args["report"]
    assert restored.stages.inventory.data.test_ids == native_ids
    raw = (files.root / "reports/1.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == write.artifact.sha256


def test_db_failure_preserves_published_file_for_reconciliation(tmp_path, stage_artifacts):
    files, _, kwargs, store = publish(tmp_path, stage_artifacts, fail=True)
    with pytest.raises(RunStorageError):
        persist_report(files, store, artifact_id="file-1", storage_key="reports/1.json", **kwargs)
    assert (files.root / "reports/1.json").exists()


def test_publication_failure_does_not_call_db(tmp_path, stage_artifacts):
    files, _, kwargs, store = publish(tmp_path, stage_artifacts)
    (files.root / "reports").mkdir()
    (files.root / "reports/1.json").write_bytes(b"other bytes")
    with pytest.raises(RunConflict):
        persist_report(files, store, artifact_id="file-1", storage_key="reports/1.json", **kwargs)
    assert store.writes == []


def test_corrupt_missing_and_foreign_artifacts_never_become_report_success(
    tmp_path, stage_artifacts
):
    files, _, kwargs, store = publish(tmp_path, stage_artifacts)
    write = persist_report(
        files, store, artifact_id="file-1", storage_key="reports/1.json", **kwargs
    )
    with pytest.raises(RunStorageError):
        files.read(write.artifact, expected_identity=write.identity, expected_report_id="foreign")
    file = files.root / "reports/1.json"
    file.write_bytes(b"corrupt")
    with pytest.raises(RunStorageError):
        files.read(
            write.artifact, expected_identity=write.identity, expected_report_id=write.report_id
        )
    file.unlink()
    with pytest.raises(RunStorageError):
        files.read(
            write.artifact, expected_identity=write.identity, expected_report_id=write.report_id
        )
