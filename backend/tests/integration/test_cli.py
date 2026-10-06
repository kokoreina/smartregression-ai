import subprocess
import sys
from pathlib import Path


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
