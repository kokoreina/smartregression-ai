"""Publication must never expose incomplete JSON or clobber an existing report."""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from smartregression.adapters import report_output


@pytest.fixture
def paths(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()
    return repo, tmp_path / "report.json"


def test_failed_publish_leaves_no_destination_or_temp(paths, monkeypatch):
    repo, output = paths

    def fail(*args):
        raise OSError("disk failure")

    monkeypatch.setattr(report_output.os, "link", fail)
    with pytest.raises(OSError):
        report_output.write_report(output, '{"complete":true}', repository=repo)
    assert not output.exists()
    assert not list(output.parent.glob(".smartregression-*"))


def test_concurrent_writers_publish_one_whole_document(paths):
    repo, output = paths

    def publish(text):
        try:
            report_output.write_report(output, text, repository=repo)
        except ValueError as exc:
            assert str(exc) == "output_exists"
            return False
        return True

    values = ['{"writer":1}', '{"writer":2}']
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(publish, values))
    assert sum(result) == 1
    assert output.read_text("utf-8").strip() == values[result.index(True)]
    assert not list(output.parent.glob(".smartregression-*"))


def test_missing_parent_and_input_subdirectory_do_not_create_files(paths):
    repo, output = paths
    with pytest.raises(OSError):
        report_output.write_report(output.parent / "missing/report.json", "{}", repository=repo)
    inside = repo / "reports"
    inside.mkdir()
    with pytest.raises(ValueError, match="output_inside_repository"):
        report_output.write_report(inside / "report.json", "{}", repository=repo)
    assert not list(inside.iterdir())


def test_redirected_output_parent_rejected(paths):
    repo, output = paths
    actual = output.parent / "actual"
    actual.mkdir()
    redirect = output.parent / "redirect"
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(redirect), str(actual)], capture_output=True
        )
        assert result.returncode == 0
    else:
        redirect.symlink_to(actual, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="unsafe_output_path"):
            report_output.write_report(redirect / "report.json", "{}", repository=repo)
        assert not (actual / "report.json").exists()
    finally:
        if os.name == "nt":
            redirect.rmdir()  # Remove this junction itself, never its target.
        else:
            redirect.unlink()
