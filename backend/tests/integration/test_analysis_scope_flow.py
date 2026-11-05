"""Scope through real Git, workflow and report files; input Python never executes.

Inventory results are explicit collector doubles: these tests verify propagation,
not Docker isolation, real pytest collection or PostgreSQL acceptance.
"""

import subprocess

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analysis_exit_code, analyze
from smartregression.application.reports import validate_report_json
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.cli.main import main
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.execution.inventory import finalize_discovery


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def scope_repo(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Scope Fixture")
    git(repo, "config", "user.email", "scope@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    for path, text in {
        "changed.py": "def f():\n    return 1\n",
        "deleted.py": "def gone():\n    return 1\n",
        "old.py": "def moved():\n    return 3\n",
        "unchanged.py": "x = 1\n",
    }.items():
        (repo / path).write_text(text, encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "scope base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "changed.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    (repo / "deleted.py").unlink()
    (repo / "old.py").rename(repo / "new.py")
    (repo / "README.md").write_text("file-only observation\n", encoding="utf-8")
    (repo / "use.py").write_text(
        "import missing_module\nraise RuntimeError('input-must-never-execute')\n",
        encoding="utf-8",
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "scope target")
    return repo, base, git(repo, "rev-parse", "HEAD")


def cli_args(revisions, output):
    repo, base, target = revisions
    return [
        "analyze",
        "--repository",
        str(repo),
        "--repository-id",
        "scope-fixture",
        "--authorized-root",
        str(repo),
        "--base",
        base,
        "--target",
        target,
        "--data-kind",
        "demo",
        "--output",
        str(output),
    ]


def read_report(path):
    report = validate_report_json(path.read_text("utf-8"))
    assert isinstance(report, StageAnalysisReport)
    return report


def test_actual_cli_preserves_stage_specific_scope_and_revision_sides(scope_repo, tmp_path, capsys):
    output = tmp_path / "scope.json"
    assert main(cli_args(scope_repo, output)) == 1
    report = read_report(output)
    changes, graph = report.stages.changes, report.stages.graph
    assert {f.path for f in changes.data.files} == {
        "changed.py",
        "deleted.py",
        "new.py",
        "README.md",
        "use.py",
    }
    assert graph.data.nodes == ["changed.py", "new.py", "unchanged.py", "use.py"]
    assert graph.data.snapshot == report.identity.target
    assert [(f.status, f.limitations) for f in changes.data.files if f.path == "README.md"] == [
        ("file_only", ["non_python_file_level_only"]),
    ]
    assert [(issue.code, issue.path) for issue in graph.limitations] == [
        ("target_not_in_snapshot", "use.py"),
    ]
    assert graph.data.unresolved[0].reference == "missing_module"
    assert graph.status == changes.status == "partial"
    deleted = next(c for c in changes.data.components if c.path == "deleted.py" and c.symbol)
    assert deleted.base_location is not None and deleted.target_location is None
    renamed = next(c for c in changes.data.components if c.path == "new.py")
    assert renamed.previous_path == "old.py"
    assert report.stages.inventory.status == "not_run"
    assert report.stages.inventory.reason == "inventory_collector_not_configured"
    assert "input-must-never-execute" not in output.read_text("utf-8")
    assert main(["validate-report", str(output)]) == 0
    capsys.readouterr()


def test_no_diff_is_not_no_impact_when_unchanged_target_source_fails(scope_repo, tmp_path, capsys):
    repo, _, _ = scope_repo
    (repo / "unchanged.py").write_text("def private_broken(\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "owned invalid source")
    revision = git(repo, "rev-parse", "HEAD")
    output = tmp_path / "failed-scope.json"
    assert main(cli_args((repo, revision, revision), output)) == 2
    report = read_report(output)
    assert report.identity.base == report.identity.target
    assert report.stages.changes.status == "completed"
    assert report.stages.changes.data.files == []
    assert report.stages.changes.data.components == []
    assert report.stages.graph.status == "failed"
    assert report.stages.graph.data is None
    assert [(i.code, i.path) for i in report.stages.graph.limitations] == [
        ("python_parse_failed", "unchanged.py"),
    ]
    assert report.stages.review_ordering.reason == "dependency_failed"
    assert report.stages.impact.status == "not_run"
    assert report.stages.impact.reason == "dependency_failed"
    assert report.stages.impact.data is None
    assert report.analysis_status == "partial"
    assert "private_broken" not in output.read_text("utf-8")
    assert main(["validate-report", str(output)]) == 0  # Valid report, failed analysis.
    capsys.readouterr()


class Collector:
    configuration_digest = "c" * 64

    def __init__(self, ids, code, errors, termination):
        self.ids, self.code, self.errors, self.termination = ids, code, errors, termination

    def collect(self, snapshot, *, identity):
        return finalize_discovery(
            expected=identity,
            observed=identity,
            payload={
                "ids": self.ids,
                "exit_code": self.code,
                "collection_finished": True,
                "collection_errors": self.errors,
            },
            termination=self.termination,
        )


@pytest.mark.parametrize(
    ("ids", "code", "errors", "termination", "status", "completeness", "reason", "exit_code"),
    [
        (["tests/test_a.py::test_f"], 0, 0, "exited", "completed", "complete", None, 1),
        ([], 5, 0, "exited", "completed", "complete", None, 1),
        (["tests/test_a.py::test_f"], 2, 1, "exited", "partial", "partial", "collection_failed", 1),
        ([], 2, 1, "exited", "failed", None, "collection_failed", 2),
        ([], 0, 0, "timeout", "failed", None, "discovery_timeout", 2),
    ],
    ids=["complete", "empty", "partial", "failed", "timeout"],
)
def test_inventory_matrix_survives_workflow_and_json_file(
    scope_repo,
    tmp_path,
    ids,
    code,
    errors,
    termination,
    status,
    completeness,
    reason,
    exit_code,
):
    repo, base, target = scope_repo
    report = analyze(
        LocalGit(repo),
        authorization=RepositoryAuthorization("scope-fixture", repo),
        repository_id="scope-fixture",
        base=base,
        target=target,
        data_kind="demo",
        inventory_collector=Collector(ids, code, errors, termination),
    )
    output = tmp_path / "inventory.json"
    output.write_text(report.model_dump_json(), encoding="utf-8")
    restored = read_report(output)
    inventory = restored.stages.inventory
    assert inventory.status == status
    if completeness is None:
        assert inventory.data is None
        assert inventory.error_code == reason
    else:
        assert inventory.data.snapshot == restored.identity.target
        assert inventory.data.completeness == completeness
        assert inventory.data.test_ids == ids
        assert [i.code for i in inventory.limitations] == ([] if reason is None else [reason])
    assert restored.analysis_status == "partial"
    assert analysis_exit_code(restored) == exit_code
