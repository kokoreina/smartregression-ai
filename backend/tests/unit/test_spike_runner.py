import subprocess
import sys
from pathlib import Path

import pytest

from smartregression.adapters.runners.pytest_spike import Limits, classify_pytest, validate_dispatch


@pytest.mark.parametrize("value", [0, -1, True, float("inf"), float("nan"), 121])
def test_invalid_limits_are_rejected(value):
    with pytest.raises(ValueError):
        Limits(timeout=value)


def test_discovery_failure_differs_from_empty_inventory():
    assert classify_pytest(5, collecting=True) == "empty_inventory"
    assert classify_pytest(2, collecting=True) == "discovery_failed"
    assert classify_pytest(1, collecting=False) == "test_failed"
    assert classify_pytest(3, collecting=False) == "infrastructure_error"
    assert (
        classify_pytest(1, collecting=False, reports=[{"phase": "setup", "outcome": "failed"}])
        == "setup_error"
    )
    assert (
        classify_pytest(0, collecting=False, reports=[{"phase": "setup", "outcome": "skipped"}])
        == "skipped"
    )


def test_controller_bounds_output_and_time():
    from smartregression.adapters.runners.pytest_spike import bounded_command

    with pytest.raises(ValueError, match="output_limit"):
        bounded_command([sys.executable, "-c", 'print("x" * 100000)'], 5, 4096)
    with pytest.raises(subprocess.TimeoutExpired):
        bounded_command([sys.executable, "-c", "import time; time.sleep(10)"], 0.1, 4096)


def test_git_binary_channel_is_not_corrupted_by_diagnostics():
    from smartregression.adapters.bounded_process import bounded_command

    output = bounded_command(
        [
            sys.executable,
            "-c",
            'import sys; sys.stderr.write("diagnostic"); sys.stdout.buffer.write(b"blob\\x00")',
        ],
        5,
        4096,
        merge_stderr=False,
    )
    assert output == b"blob\x00"


def test_wrong_snapshot_and_unknown_test_cannot_dispatch():
    inventory = ("tests/test_calc.py::test_add",)
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        validate_dispatch("base", "target", inventory, inventory[0])
    with pytest.raises(ValueError, match="unknown_test"):
        validate_dispatch("target", "target", inventory, "tests/test_calc.py::unknown")
    validate_dispatch("target", "target", inventory, inventory[0])


def test_snapshot_rejects_symlinks_and_non_python_files(tmp_path: Path):
    from smartregression.adapters.runners.pytest_spike import snapshot_digest

    (tmp_path / ".env").write_text("synthetic excluded fixture")
    with pytest.raises(ValueError, match="unsupported_snapshot"):
        snapshot_digest(tmp_path)
