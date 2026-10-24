"""Generate and run our own synthetic Git/pytest fixture; never a benchmark.

Run from repository root with existing dev environment. Requires prepared image ID.
Only generated snapshots are mounted; never the workspace or .env.
"""

import argparse
import json
import subprocess
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.runners.pytest_spike import (
    FixtureWorker,
    Limits,
    classify_pytest,
    snapshot_digest,
    validate_dispatch,
)
from smartregression.core.impact.python_snapshot import (
    changed_symbols,
    inspect_python,
    module_edges,
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def execute(image: str, output: Path) -> None:
    here = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=False)
    results = {
        "data_kind": "synthetic_fixture",
        "image_id": image,
        "started_at": datetime.now(UTC).isoformat(),
        "checks": {},
    }
    # Temp dir is created by this task; cleanup only touches this owned directory.
    with tempfile.TemporaryDirectory(prefix="smartregression-g1-") as temp:
        repo = Path(temp) / "git-fixture"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Synthetic Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
        (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "synthetic base")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n")
        (repo / "tests").mkdir()
        (repo / "tests/test_calc.py").write_text(
            "from calc import add\nimport pytest\nimport time\nimport os\n"
            "def test_add():\n    assert add(2, 3) == 5\n"
            'def test_failure():\n    assert False, "synthetic failure"\n'
            '@pytest.mark.skip(reason="synthetic skip")\n'
            "def test_skip():\n    pass\n"
            "def test_timeout():\n    time.sleep(60)\n"
            'def test_output():\n    os.write(1, b"x" * 100000)\n'
        )
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "synthetic target")
        target = git(repo, "rev-parse", "HEAD")
        reader = LocalGit(repo)
        results["base"], results["target"] = base, target
        results["changes"] = [x.model_dump() for x in reader.diff(base, target)]
        results["python_snapshot"] = asdict(inspect_python(reader.read_text(target, "calc.py")))
        results["test_imports"] = asdict(
            inspect_python(reader.read_text(target, "tests/test_calc.py"))
        )
        results["changed_symbols"] = changed_symbols(
            reader.read_text(base, "calc.py"), reader.read_text(target, "calc.py")
        )
        results["dependency_edges"] = module_edges(
            {path: reader.read_text(target, path) for path in ["calc.py", "tests/test_calc.py"]}
        )
        # Export exactly our reviewed fixture files from immutable objects. No git checkout hooks.
        snapshot = Path(temp) / "snapshot"
        (snapshot / "tests").mkdir(parents=True)
        for path in ["calc.py", "tests/test_calc.py"]:
            (snapshot / path).write_text(reader.read_text(target, path))
        digest = snapshot_digest(snapshot)
        worker = FixtureWorker(image, here / "worker.py", here / "seccomp.json")
        collected = worker.run(snapshot, digest)
        assert classify_pytest(collected["exit_code"], collecting=True) == "complete"
        ids = tuple(collected["ids"])
        chosen = "tests/test_calc.py::test_add"
        results["collection"] = collected
        isolation = collected["isolation"]
        assert isolation["memory_max"] == str(256 * 1024 * 1024)
        assert isolation["pids_max"] == "64"
        quota, period = map(int, isolation["cpu_max"].split())
        assert quota / period == 1
        # This is frozen BEFORE any selected-test outcome is observed.
        selection = {
            "target": target,
            "snapshot_digest": digest,
            "inventory": ids,
            "selected": [chosen],
            "frozen_at": datetime.now(UTC).isoformat(),
        }
        with (output / "selection.json").open("x", encoding="utf-8") as selection_file:
            json.dump(selection, selection_file, indent=2)
        for expected, supplied, test_id, error in [
            (digest, "wrong", chosen, "snapshot_mismatch"),
            (digest, digest, ("tests/test_calc.py::unknown"), "unknown_test"),
        ]:
            try:
                validate_dispatch(expected, supplied, ids, test_id)
            except ValueError as exc:
                assert str(exc) == error
                results["checks"][error] = "rejected_before_dispatch"
            else:
                raise AssertionError(error)
        for name, expected_exit in [("test_add", 0), ("test_failure", 1), ("test_skip", 0)]:
            outcome = worker.run(
                snapshot, digest, test_id="tests/test_calc.py::" + name, inventory=ids
            )
            assert outcome["exit_code"] == expected_exit
            assert outcome["started_at"] >= selection["frozen_at"]
            results[name] = outcome
        # Runtime limit tests use fixture IDs, not untrusted commands.
        for name, limits, expected_error in [
            ("test_timeout", Limits(timeout=2), "timeout"),
            ("test_output", Limits(output_bytes=8192), "output_limit"),
        ]:
            limited = FixtureWorker(image, here / "worker.py", here / "seccomp.json", limits)
            try:
                limited.run(snapshot, digest, test_id="tests/test_calc.py::" + name, inventory=ids)
            except subprocess.TimeoutExpired:
                assert expected_error == "timeout"
                results["checks"][name] = "timeout_and_cleanup"
            except ValueError as exc:
                assert str(exc) == expected_error
                results["checks"][name] = str(exc) + "_and_cleanup"
            else:
                raise AssertionError("limit_not_enforced")
        for name, source, expected in [
            ("empty", "value = 1\n", "empty_inventory"),
            ("broken", "import missing_g1_module\n", "discovery_failed"),
        ]:
            directory = Path(temp) / name
            directory.mkdir()
            (directory / "test_case.py").write_text(source)
            observation = worker.run(directory, snapshot_digest(directory))
            assert classify_pytest(observation["exit_code"], collecting=True) == expected
            results[name] = observation
        results["finished_at"] = datetime.now(UTC).isoformat()
    (output / "observations.json").write_text(json.dumps(results, indent=2))
    print("Synthetic G1 checks complete. Artifacts:", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="local immutable sha256 image ID")
    parser.add_argument("--output", type=Path, required=True, help="new artifact directory")
    args = parser.parse_args()
    execute(args.image, args.output)
