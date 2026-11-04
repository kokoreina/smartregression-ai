"""Owned Git fixture; input Python is inspected, never imported or executed."""

import json
import subprocess
import sys

import pytest

from smartregression.cli.main import main
from smartregression.contracts.stages import StageAnalysisReport


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def analysis_repo(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Workflow Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (repo / "deleted.py").write_text("def gone():\n    return 1\n", encoding="utf-8")
    (repo / "old.py").write_text("def renamed():\n    return 10\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    (repo / "b.py").write_text(
        "import a\nraise RuntimeError('input must never run')\n", encoding="utf-8"
    )
    (repo / "deleted.py").unlink()
    (repo / "old.py").rename(repo / "new.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "target")
    return repo, base, git(repo, "rev-parse", "HEAD")


def args(revisions, *extra):
    repo, base, target = revisions
    return [
        "analyze",
        "--repository",
        str(repo),
        "--repository-id",
        "fixture",
        "--authorized-root",
        str(repo),
        "--base",
        base,
        "--target",
        target,
        "--data-kind",
        "demo",
        *map(str, extra),
    ]


def test_actual_cli_frozen_git_flow_and_legacy_validation(analysis_repo, capsys):
    repo, _, _ = analysis_repo
    (repo / "a.py").write_text("raise RuntimeError('dirty-private')", encoding="utf-8")
    assert main(args(analysis_repo)) == 1
    out = capsys.readouterr()
    report = StageAnalysisReport.model_validate_json(out.out)
    assert report.data_kind == "demo"
    assert report.stages.snapshots.status == "completed"
    assert report.stages.graph.data.nodes == ["a.py", "b.py", "new.py"]
    assert any(
        c.change == "deleted" and c.base_location for c in report.stages.changes.data.components
    )
    assert any(
        c.previous_path == "old.py" and c.path == "new.py"
        for c in report.stages.changes.data.components
    )
    assert "dirty-private" not in out.out + out.err
    assert "partial" in out.err


def test_output_file_exclusive_and_validate_report_is_not_analysis_success(
    analysis_repo, tmp_path, capsys
):
    output = tmp_path / "report.json"
    assert main(args(analysis_repo, "--output", output)) == 1
    original = output.read_bytes()
    assert main(["validate-report", str(output)]) == 0
    capsys.readouterr()
    assert main(args(analysis_repo, "--output", output)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "output_exists" in captured.err
    assert output.read_bytes() == original
    assert not list(tmp_path.glob(".smartregression-*"))


def test_output_inside_input_rejected(analysis_repo, capsys):
    repo, _, _ = analysis_repo
    assert main(args(analysis_repo, "--output", repo / "report.json")) == 2
    assert not (repo / "report.json").exists()
    assert "output_inside_repository" in capsys.readouterr().err


def test_acquisition_error_no_json_or_file(analysis_repo, tmp_path, capsys):
    argv = args(analysis_repo, "--output", tmp_path / "bad.json")
    argv[argv.index("--base") + 1] = "main"
    assert main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert not (tmp_path / "bad.json").exists()
    assert "Traceback" not in captured.err


def test_cli_subprocess_help_and_machine_json(analysis_repo):
    help_result = subprocess.run(
        [sys.executable, "-m", "smartregression.cli.main", "analyze", "--help"],
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    assert "--authorized-root" in help_result.stdout
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from smartregression.cli.main import main
code = main()
assert 'sqlalchemy' not in sys.modules
assert 'psycopg' not in sys.modules
raise SystemExit(code)
""",
            *args(analysis_repo),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["schema_version"] == "2.0.0"


def test_cli_failure_report_is_valid_but_analysis_exit_nonzero(analysis_repo, capsys):
    repo, base, _ = analysis_repo
    (repo / "a.py").write_text("def broken(\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "parse failure")
    broken = git(repo, "rev-parse", "HEAD")
    assert main(args((repo, base, broken))) == 2
    captured = capsys.readouterr()
    report = StageAnalysisReport.model_validate_json(captured.out)
    assert report.analysis_status == "partial"
    assert report.stages.graph.status == "failed"
    assert report.stages.changes.status == "partial"


def test_same_revision_and_output_io_failure(analysis_repo, tmp_path, capsys):
    repo, base, _ = analysis_repo
    assert main(args((repo, base, base))) == 1
    report = StageAnalysisReport.model_validate_json(capsys.readouterr().out)
    assert report.identity.base == report.identity.target
    assert report.stages.changes.data.components == []
    assert main(args(analysis_repo, "--output", tmp_path / "missing/report.json")) == 2
    assert capsys.readouterr().out == ""


def test_default_analysis_and_health_ignore_invalid_database_settings(
    analysis_repo, capsys, monkeypatch
):
    from fastapi.testclient import TestClient

    from smartregression.api.main import create_app

    monkeypatch.setenv("SMARTREGRESSION_DATABASE_URL", "invalid-private-url")

    def forbidden(*args, **kwargs):
        pytest.fail("Default analysis/health must not initialize persistence")

    monkeypatch.setattr("smartregression.adapters.storage.config.load_database_settings", forbidden)
    monkeypatch.setattr("smartregression.adapters.storage.connection.database_engine", forbidden)
    assert main(args(analysis_repo)) == 1
    assert (
        StageAnalysisReport.model_validate_json(capsys.readouterr().out).analysis_status
        == "partial"
    )
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize("combination", ["missing_root", "root_without_persist", "output"])
def test_persistence_arguments_rejected_before_acquisition(
    analysis_repo, tmp_path, capsys, monkeypatch, combination
):
    import importlib

    module = importlib.import_module("smartregression.cli.main")

    def forbidden(**kwargs):
        pytest.fail("Invalid persistence arguments must not analyze or publish")

    monkeypatch.setattr(module, "analyze_local", forbidden)
    extra = {
        "missing_root": ["--persist"],
        "root_without_persist": ["--artifact-root", tmp_path],
        "output": ["--persist", "--artifact-root", tmp_path, "--output", tmp_path / "out.json"],
    }[combination]
    assert main(args(analysis_repo, *extra)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid_persistence_arguments" in captured.err
    assert not (tmp_path / "out.json").exists()


@pytest.mark.parametrize("configured", [False, True])
def test_persistence_configuration_failure_is_safe(
    analysis_repo, tmp_path, capsys, monkeypatch, configured
):
    monkeypatch.delenv("SMARTREGRESSION_DATABASE_URL", raising=False)
    # Runtime must never fall back to migration credentials.
    monkeypatch.setenv("SMARTREGRESSION_MIGRATION_DATABASE_URL", "private-migration-url")
    if configured:
        monkeypatch.setenv("SMARTREGRESSION_DATABASE_URL", "private-invalid-runtime-url")
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    assert main(args(analysis_repo, "--persist", "--artifact-root", artifact_root)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "database_configuration_invalid" in captured.err
    assert "private-" not in captured.err
    assert list(artifact_root.iterdir()) == []


@pytest.mark.parametrize(
    "code", ["run_storage_failed", "run_storage_conflict", "run_metadata_invalid"]
)
def test_persistence_failure_never_emits_success(
    analysis_repo, tmp_path, capsys, monkeypatch, code
):
    import importlib

    from smartregression.application.run_store import RunConflict, RunMetadataError, RunStorageError

    errors = {
        "run_storage_failed": RunStorageError,
        "run_storage_conflict": RunConflict,
        "run_metadata_invalid": RunMetadataError,
    }
    module = importlib.import_module("smartregression.cli.main")

    def fail(**kwargs):
        raise errors[code]()

    monkeypatch.setattr(module, "analyze_local", fail)
    assert main(args(analysis_repo, "--persist", "--artifact-root", tmp_path)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"Persistence failed: {code}" in captured.err
    assert "Persistence saved" not in captured.err


def test_unexpected_exception_and_bad_serialized_report_fail_safely(
    analysis_repo, capsys, monkeypatch
):
    import importlib

    module = importlib.import_module("smartregression.cli.main")

    def internal(**kwargs):
        raise RuntimeError("private exception source")

    monkeypatch.setattr(module, "analyze_local", internal)
    assert main(args(analysis_repo)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "analysis_internal_error" in captured.err
    assert "private exception" not in captured.err

    class BadReport:
        def model_dump_json(self):
            return '{"private_source":"never-echo"}'

    monkeypatch.setattr(module, "analyze_local", lambda **k: BadReport())
    assert main(args(analysis_repo)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "report_validation_failed" in captured.err
    assert "never-echo" not in captured.err
