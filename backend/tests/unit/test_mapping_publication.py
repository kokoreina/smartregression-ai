"""Real guarded file publication, with Git/collection doubles and no database."""

import hashlib
import json

import pytest
from test_analysis_workflow import BASE, TARGET, Source
from test_mapping_workflow import Collector

import smartregression.composition as composition


def test_mapping_sidecar_is_published_without_enabling_database(tmp_path, monkeypatch):
    repo, root = tmp_path / "input", tmp_path / "artifacts"
    repo.mkdir()
    root.mkdir()
    source = Source(repo)
    collector = Collector()
    monkeypatch.setattr(composition, "LocalGit", lambda _: source)
    monkeypatch.setattr(
        "smartregression.adapters.storage.config.load_database_settings",
        lambda: pytest.fail("sidecar-only mode must not access DB settings"),
    )
    report = composition.analyze_local(
        repository=repo,
        repository_id="fixture",
        authorized_root=repo,
        base=BASE,
        target=TARGET,
        data_kind="demo",
        mapping_collector=collector,
        mapping_artifact_root=root,
    )
    path = root / report.identity.run_id / (report.report_id + ".mapping.json")
    raw = path.read_bytes()
    doc = json.loads(raw)
    assert doc["report_id"] == report.report_id
    assert (
        doc["report_sha256"]
        == hashlib.sha256(report.model_dump_json(indent=2).encode() + b"\n").hexdigest()
    )
    assert collector.calls == 1


def test_invalid_receipt_never_publishes_sidecar(tmp_path, monkeypatch):
    repo, root = tmp_path / "input", tmp_path / "artifacts"
    repo.mkdir()
    root.mkdir()
    monkeypatch.setattr(composition, "LocalGit", lambda _: Source(repo))
    with pytest.raises(ValueError, match="mapping_validation_failed"):
        composition.analyze_local(
            repository=repo,
            repository_id="fixture",
            authorized_root=repo,
            base=BASE,
            target=TARGET,
            data_kind="demo",
            mapping_collector=Collector(corrupt="identity"),
            mapping_artifact_root=root,
        )
    assert list(root.iterdir()) == []


def test_mapping_root_inside_input_is_rejected_before_collection(tmp_path, monkeypatch):
    repo = tmp_path / "input"
    repo.mkdir()
    collector = Collector()
    monkeypatch.setattr(composition, "LocalGit", lambda _: Source(repo))
    with pytest.raises(RuntimeError):
        composition.analyze_local(
            repository=repo,
            repository_id="fixture",
            authorized_root=repo,
            base=BASE,
            target=TARGET,
            data_kind="demo",
            mapping_collector=collector,
            mapping_artifact_root=repo,
        )
    assert collector.calls == 0
