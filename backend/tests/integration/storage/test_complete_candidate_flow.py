"""Opt-in approved candidate Git/runner/index/PostgreSQL flow, not a benchmark."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.dialects.postgresql import insert

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.runners.candidate_inventory import (
    CANDIDATES,
    CandidateInventoryCollector,
)
from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.evidence_store import PostgresEvidenceStore
from smartregression.adapters.storage.schema import repositories
from smartregression.application.persistence import bundle_from_report
from smartregression.composition import analyze_local
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import canonical_json

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("name", ["sqlparse", "tinydb"])
def test_actual_candidate_collection_index_mapping_and_persistence(migrated, monkeypatch, name):
    image = os.environ.get("SMARTREGRESSION_P5_CANDIDATE_IMAGE")
    source_root = os.environ.get("SMARTREGRESSION_P5_CANDIDATE_ROOT")
    if not image or not source_root:
        pytest.skip("Set P5 candidate image/root for real Git+Docker+PostgreSQL acceptance")
    owner, runtime, _ = migrated
    repo = Path(source_root) / name / "source"
    if any(p.is_symlink() or p.is_junction() for p in (repo, *repo.parents)):
        pytest.fail("unsafe_candidate_source")
    repo = repo.resolve(strict=True)
    reader = LocalGit(repo)
    target = CANDIDATES[name][1]
    # LocalGit's hardened argument-vector read never checks out or executes source.
    base = reader._git("rev-parse", target + "^1").decode().strip()
    output = ROOT / "var" / ("p5-candidate-flow-" + name + "-" + uuid4().hex)
    artifacts, workspace = output / "artifacts", output / "worker"
    artifacts.mkdir(parents=True)
    workspace.mkdir()
    collector = CandidateInventoryCollector(name, image, ROOT, workspace)
    with owner.begin() as connection:
        connection.execute(
            insert(repositories)
            .values(repository_id=name, source_kind="local")
            .on_conflict_do_nothing()
        )
    settings = DatabaseSettings(runtime.url, allow_loopback_test=True)
    monkeypatch.setattr(
        "smartregression.adapters.storage.config.load_database_settings", lambda: settings
    )
    report = analyze_local(
        repository=repo,
        repository_id=name,
        authorized_root=repo,
        base=base,
        target=target,
        data_kind="real",
        artifact_root=artifacts,
        mapping_collector=collector,
        index_root=artifacts,
    )
    for field in type(report.stages).model_fields:
        assert getattr(report.stages, field).status in {"completed", "partial"}, field
    assert report.stages.inventory.status == "completed"
    assert len(report.stages.inventory.data.test_ids) == {"sqlparse": 509, "tinydb": 228}[name]
    assert report.stages.retrieval.data.sources
    assert report.stages.retrieval.data.items
    assert PostgresEvidenceStore(runtime).load(report.identity) == bundle_from_report(report)
    raw = (artifacts / report.identity.run_id / (report.report_id + ".json")).read_bytes()
    assert StageAnalysisReport.model_validate_json(raw) == report
    mapping = json.loads(
        (artifacts / report.identity.run_id / (report.report_id + ".mapping.json")).read_bytes()
    )
    assert mapping["report_sha256"] == hashlib.sha256(raw).hexdigest()
    assert mapping["identity"] == report.identity.model_dump(mode="json")
    assert mapping["mapping"]["safe_to_exclude"] is False
    assert collector.last_observation["container_removed"] is True
    (output / "evidence.json").write_bytes(
        canonical_json(
            dict(
                passed=True,
                data_kind="approved_candidate_integration",
                candidate=name,
                base=base,
                target=target,
                report_id=report.report_id,
                run_id=report.identity.run_id,
                stage_statuses={
                    f: getattr(report.stages, f).status for f in type(report.stages).model_fields
                },
                native_ids=len(report.stages.inventory.data.test_ids),
                context_chunks=len(report.stages.retrieval.data.items),
                report_sha256=hashlib.sha256(raw).hexdigest(),
                mapping_sha256=hashlib.sha256(canonical_json(mapping)).hexdigest(),
                container_removed=True,
            )
        )
    )
