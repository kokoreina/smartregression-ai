import json
import subprocess
import sys
from pathlib import Path

import pytest


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "smartregression.cli.main", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_help() -> None:
    result = invoke("--help")
    assert result.returncode == 0
    assert "validate-report" in result.stdout


def test_cli_accepts_demo(demo_path: Path) -> None:
    result = invoke("validate-report", str(demo_path))
    assert result.returncode == 0
    assert "[DEMO]" in result.stdout


def test_cli_rejects_invalid_report(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text('{"private_source": "do-not-echo"}', encoding="utf-8")
    result = invoke("validate-report", str(path))
    assert result.returncode == 1
    assert "Invalid report" in result.stderr
    assert "do-not-echo" not in result.stderr


def test_cli_reports_unreadable_file(tmp_path: Path) -> None:
    result = invoke("validate-report", str(tmp_path / "missing.json"))
    assert result.returncode == 2


@pytest.mark.parametrize("example", ["partial", "failed", "not-implemented", "empty"])
def test_cli_validates_stage_examples_without_running_analysis(example: str) -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / f"examples/reports/stage-report.{example}.json"
    result = invoke("validate-report", str(path))
    assert result.returncode == 0  # Valid document, not a successful analysis.
    assert "[DEMO]" in result.stdout


def test_cli_rejects_nested_stage_mismatch_without_echoing_input(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    data = json.loads((root / "examples/reports/stage-report.partial.json").read_text("utf-8"))
    data["stages"]["graph"]["data"]["snapshot"]["repository_id"] = "foreign-repo"
    data["private_source"] = "do-not-echo-stage-content"
    path = tmp_path / "stage-invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = invoke("validate-report", str(path))
    assert result.returncode == 1
    assert "do-not-echo-stage-content" not in result.stderr + result.stdout
