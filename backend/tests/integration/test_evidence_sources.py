"""Resolve actual acquired Git sources, never import the fixture's Python."""

import subprocess
from dataclasses import replace

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze_execution
from smartregression.application.evidence import explain_impact, inspect_bundle
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.contracts.stages import EvidenceBundle
from smartregression.core.git.snapshots import canonical_json
from smartregression.core.impact.potential_impact import build_potential_impact


def test_actual_git_sources_support_static_paths_and_remain_frozen(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    git("init", "-q", "--object-format=sha1")
    git("config", "user.name", "Evidence Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "core.autocrlf", "false")
    (repo / "calc.py").write_bytes(b"def value():\r\n    return 1\r\n")
    (repo / "consumer.py").write_bytes(b"import calc\nraise RuntimeError('must not execute')\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (repo / "calc.py").write_bytes(b"def value():\r\n    return 2\r\n")
    git("add", ".")
    git("commit", "-qm", "target")
    target = git("rev-parse", "HEAD")
    source = LocalGit(repo)
    args = dict(
        authorization=RepositoryAuthorization("fixture", repo),
        repository_id="fixture",
        base=base,
        target=target,
    )
    execution = analyze_execution(source, **args, data_kind="demo")
    pair = prepare_snapshots(source, **args)
    report = execution.report
    changes, graph = report.stages.changes.data, report.stages.graph.data
    impact = build_potential_impact(report.identity, changes, graph)
    explained, stage = explain_impact(report.identity, changes, graph, impact, pair)
    bundle = EvidenceBundle(
        identity=report.identity,
        changes=changes,
        graph=graph,
        impact=explained,
        evidence=stage.data,
    )
    assert stage.status == "completed"
    assert all(
        item.resolution == "resolved" and item.support == "supported" for item in stage.data.items
    )
    before = canonical_json(bundle.model_dump(mode="json"))
    (repo / "calc.py").write_bytes(b"dirty unrelated content")
    assert inspect_bundle(bundle, prepare_snapshots(source, **args)) == stage
    assert canonical_json(bundle.model_dump(mode="json")) == before
    forged = replace(pair.target, contents=(b"tampered", *pair.target.contents[1:]))
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        inspect_bundle(bundle, replace(pair, target=forged))
