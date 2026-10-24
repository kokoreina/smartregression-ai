import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from smartregression.adapters.runners.docker_fixture import (
    DockerFixtureWorker,
    ProcessObservation,
    WorkerError,
    _bounded_process,
    _events,
)
from smartregression.adapters.runners.fixture_entrypoint import Events
from smartregression.core.execution.config import ExecutionConfig

IMAGE = "sha256:" + "a" * 64
SHA = "b" * 40


def event(kind, **values):
    return "SMARTREGRESSION_EVENT " + json.dumps({"kind": kind, **values}) + "\n"


def test_discovery_is_bound_to_sha_and_uses_hardened_container_boundary():
    commands = []

    def transport(command, timeout, limit):
        commands.append(command)
        if command[1] == "rm":
            return ProcessObservation(0, "")
        return ProcessObservation(0, event("inventory", ids=["tests/test_demo.py::test_ok"]))

    worker = DockerFixtureWorker(IMAGE, execute=transport)
    inventory = worker.discover(Path("backend/tests/fixtures/g1"), SHA, ExecutionConfig())
    assert inventory.target_sha == SHA
    assert inventory.status == "complete"
    assert inventory.ids == ("tests/test_demo.py::test_ok",)
    command = commands[0]
    for required in [
        "--read-only",
        "--cap-drop=ALL",
        "--network=none",
        "--security-opt=no-new-privileges",
        "--pull=never",
        "--pids-limit=64",
    ]:
        assert required in command
    assert "--user=65534:65534" in command
    assert not any("docker.sock" in arg for arg in command)
    assert "--privileged" not in command
    assert commands[-1][1:3] == ["rm", "--force"]


@pytest.mark.parametrize(
    ("code", "text", "reason", "status"),
    [
        (5, event("inventory", ids=[]), None, "empty"),
        (2, event("inventory", ids=[]), None, "failed"),
        (0, "", None, "failed"),
        (0, event("inventory", ids=["../outside.py::test_bad"]), None, "failed"),
        (0, event("inventory", ids=["tests/t.py::test_x", "tests/t.py::test_x"]), None, "failed"),
        (124, "", "timeout", "timeout"),
        (125, "", "output_limit", "output_limit"),
        (125, "docker engine failed", None, "failed"),
    ],
)
def test_empty_inventory_never_masks_discovery_failure(code, text, reason, status):
    def transport(command, timeout, limit):
        return (
            ProcessObservation(0, "")
            if command[1] == "rm"
            else ProcessObservation(code, text, reason)
        )

    result = DockerFixtureWorker(IMAGE, execute=transport).discover(
        Path("backend/tests/fixtures/g1"),
        SHA,
        ExecutionConfig(),
    )
    assert result.status == status
    if status != "complete":
        assert result.ids == ()


def test_wrong_sha_or_unknown_id_never_starts_execution():
    commands = []

    def transport(command, timeout, limit):
        commands.append(command)
        return (
            ProcessObservation(0, "")
            if command[1] == "rm"
            else ProcessObservation(
                0,
                event("inventory", ids=["tests/test_demo.py::test_ok"]),
            )
        )

    worker = DockerFixtureWorker(IMAGE, execute=transport)
    inventory = worker.discover(Path("backend/tests/fixtures/g1"), SHA, ExecutionConfig())
    count = len(commands)
    for sha, nodeid in [(SHA, "tests/test_demo.py::unknown"), ("c" * 40, inventory.ids[0])]:
        with pytest.raises(WorkerError):
            worker.run_one(
                Path("backend/tests/fixtures/g1"), sha, inventory, nodeid, ExecutionConfig()
            )
    assert len(commands) == count


def test_execution_result_and_cleanup_failure_are_not_passing():
    mode = "discover"

    def transport(command, timeout, limit):
        if command[1] == "rm":
            return ProcessObservation(0 if mode == "discover" else 1, "")
        return ProcessObservation(0, event("inventory", ids=["tests/test_demo.py::test_ok"]))

    worker = DockerFixtureWorker(IMAGE, execute=transport)
    inventory = worker.discover(Path("backend/tests/fixtures/g1"), SHA, ExecutionConfig())
    mode = "run"
    with pytest.raises(WorkerError, match="cleanup_failed"):
        worker.run_one(
            Path("backend/tests/fixtures/g1"), SHA, inventory, inventory.ids[0], ExecutionConfig()
        )


def test_worker_requires_immutable_image_and_valid_snapshot():
    for image in ["python:latest", "user/image", "", IMAGE + " --privileged"]:
        with pytest.raises(WorkerError):
            DockerFixtureWorker(image)


def test_real_process_output_limit_terminates_streaming_process():
    observed = _bounded_process(
        [sys.executable, "-u", "-c", 'import time; print("x" * 8192, flush=True); time.sleep(20)'],
        5,
        1024,
    )
    assert observed.returncode == 125
    assert len(observed.output) <= 1024


def test_real_process_timeout_is_distinct_from_test_failure():
    observed = _bounded_process(
        [sys.executable, "-c", "import time; time.sleep(20)"],
        0.2,
        1024,
    )
    assert observed.returncode == 124


def test_real_process_small_output_and_exit_code_are_preserved():
    observed = _bounded_process(
        [sys.executable, "-c", 'import sys; print("observation"); sys.exit(1)'],
        5,
        1024,
    )
    assert observed.returncode == 1
    assert observed.output.strip() == "observation"


@pytest.mark.parametrize(
    "text",
    [
        "SMARTREGRESSION_EVENT invalid-json",
        "SMARTREGRESSION_EVENT []",
        event("inventory", ids=["tests/t.py::test_x"]) + event("inventory", ids=[]),
    ],
)
def test_malformed_or_duplicate_inventory_event_is_not_success(text):
    def transport(command, timeout, limit):
        return ProcessObservation(0, "") if command[1] == "rm" else ProcessObservation(0, text)

    observed = DockerFixtureWorker(IMAGE, execute=transport).discover(
        Path("backend/tests/fixtures/g1"),
        SHA,
        ExecutionConfig(),
    )
    assert observed.status == "failed"


def test_result_event_starts_new_line_after_pytest_progress(capsys):
    print(".", end="")
    Events().pytest_runtest_logreport(
        SimpleNamespace(
            when="call",
            failed=False,
            skipped=False,
            nodeid="tests/t.py::test_ok",
            outcome="passed",
            duration=0.01,
        )
    )
    rows = _events(capsys.readouterr().out)
    assert len(rows) == 1
    assert rows[0]["kind"] == "result"
    assert rows[0]["outcome"] == "passed"
