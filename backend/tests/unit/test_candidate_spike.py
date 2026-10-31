import hashlib
import importlib.util
import io
import json
import subprocess
import tarfile
from pathlib import Path

import pytest

# scripts/ is intentionally not an installed product package. Load this one trusted
# harness by file so both `pytest` (CI) and `python -m pytest` use the same module.
spec = importlib.util.spec_from_file_location(
    "candidate_spike", Path(__file__).resolve().parents[3] / "scripts/candidates/run_candidates.py"
)
assert spec is not None and spec.loader is not None
candidate_spike = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_spike)
extract_snapshot = candidate_spike.extract_snapshot
freeze_selection = candidate_spike.freeze_selection
run_stage = candidate_spike.run_stage
validate_observation = candidate_spike.validate_observation


def archive(path, data=b"value = 1\n", *, symlink=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as bundle:
        member = tarfile.TarInfo("github-root/" + path)
        member.size = len(data)
        if symlink:
            member.type = tarfile.SYMTYPE
            member.linkname = "/outside"
        bundle.addfile(member, None if symlink else io.BytesIO(data))
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    return stream.getvalue(), {path: blob}


def test_materialization_is_bound_to_git_blob_and_rejects_traversal(tmp_path):
    payload, expected = archive("package.py")
    extract_snapshot(payload, expected, tmp_path / "valid")
    assert (tmp_path / "valid/package.py").read_bytes() == b"value = 1\n"
    for path in ["../outside", "a/../../outside", "a\\outside", ".env", "AUX.txt", "a. /x"]:
        payload, expected = archive(path)
        with pytest.raises(ValueError):
            extract_snapshot(payload, expected, tmp_path / "unsafe")
    payload, expected = archive("link", symlink=True)
    with pytest.raises(ValueError):
        extract_snapshot(payload, expected, tmp_path / "link")


def test_mismatched_or_incomplete_snapshot_is_rejected(tmp_path):
    payload, expected = archive("package.py")
    with pytest.raises(ValueError, match="snapshot_blob_mismatch"):
        extract_snapshot(payload, {"package.py": "a" * 40}, tmp_path / "wrong")
    with pytest.raises(ValueError, match="incomplete_snapshot"):
        extract_snapshot(payload, {**expected, "missing.py": "b" * 40}, tmp_path / "partial")


def test_selection_needs_two_matching_complete_inventories_and_real_id(tmp_path):
    first = {"exit_code": 0, "ids": ["tests/test_x.py::test_a"]}
    selected = freeze_selection(first, first, first["ids"][0])
    assert selected["selected"] == first["ids"]
    for second in [
        {"exit_code": 2, "ids": first["ids"]},
        {"exit_code": 0, "ids": ["other"]},
        {"exit_code": 0, "ids": first["ids"] * 2},
        {"exit_code": 5, "ids": []},
    ]:
        with pytest.raises(ValueError):
            freeze_selection(first, second, first["ids"][0])
    with pytest.raises(ValueError, match="unknown_test"):
        freeze_selection(first, first, "unknown")


def test_selected_execution_cannot_report_a_different_test():
    result = {"exit_code": 0, "ids": ["other"], "reports": []}
    with pytest.raises(ValueError, match="wrong_dispatch"):
        validate_observation(result, "single", "chosen")
    result = {"exit_code": True, "ids": [], "reports": []}
    with pytest.raises(ValueError, match="invalid_observation"):
        validate_observation(result, "collect")
    with pytest.raises(ValueError, match="invalid_observation"):
        validate_observation([], "collect")
    with pytest.raises(ValueError, match="selected_test_not_passed"):
        validate_observation(
            {
                "exit_code": 0,
                "ids": ["chosen"],
                "reports": [{"test_id": "chosen", "phase": "setup", "outcome": "skipped"}],
            },
            "single",
            "chosen",
        )


def test_timeout_still_removes_candidate_container(monkeypatch, tmp_path):
    commands = []

    def command(args, *unused):
        commands.append(args)
        if args[1] == "inspect":
            return json.dumps(
                [
                    {
                        "HostConfig": {
                            "Privileged": False,
                            "NetworkMode": "none",
                            "ReadonlyRootfs": True,
                            "Memory": 512 * 1024 * 1024,
                            "MemorySwap": 512 * 1024 * 1024,
                            "PidsLimit": 64,
                            "NanoCpus": 1_000_000_000,
                        },
                        "Config": {"User": "65534:65534"},
                        "Mounts": [{"RW": False}],
                        "Id": "fixture",
                    }
                ]
            ).encode()
        if args[1] == "start":
            raise subprocess.TimeoutExpired(args, 1)
        return b""

    monkeypatch.setattr(candidate_spike, "bounded_command", command)
    with pytest.raises(subprocess.TimeoutExpired):
        run_stage("sqlparse", "sha256:" + "a" * 64, tmp_path, "collect", None)
    assert commands[-1][:3] == ["docker", "rm", "-f"]
    assert commands[0][commands[0].index("--name") + 1] == commands[-1][-1]
