"""Reproducibility spike for exactly two fixed public snapshots; not a product runner."""

import argparse
import hashlib
import io
import json
import re
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.bounded_process import bounded_command

CANDIDATES = {
    "sqlparse": (
        "andialbrecht/sqlparse",
        "60cdc649726bf1bc4f1b336050560b336da715ec",
        "tests/test_parse.py::test_parse_tokenize",
    ),
    "tinydb": (
        "msiemens/tinydb",
        "edff96aeb2616402e9489d46e90a592c05565621",
        "tests/test_tinydb.py::test_drop_tables[memory]",
    ),
}
HERE = Path(__file__).resolve().parent


def now() -> str:
    return datetime.now(UTC).isoformat()


def extract_snapshot(payload: bytes, expected: dict[str, str], destination: Path) -> None:
    """Validate all archive entries against Git blobs before materializing regular files."""
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as bundle:
        prefix = None
        for member in bundle:
            parts = member.name.rstrip("/").split("/")
            if prefix is None:
                prefix = parts[0]
            if parts[0] != prefix or any(p in {"", ".", ".."} for p in parts):
                raise ValueError("unsafe_archive_path")
            if any(
                p != p.rstrip(" .")
                or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
                for p in parts
            ):
                raise ValueError("unsafe_archive_path")
            if any(c in member.name for c in "\\:\x00\n\r\t"):
                raise ValueError("unsafe_archive_path")
            if member.isdir():
                continue
            path = "/".join(parts[1:])
            if (
                not member.isfile()
                or not path
                or path in files
                or any(
                    p == ".env" or p.startswith(".env.") or p.endswith((".pem", ".key"))
                    for p in parts
                )
            ):
                raise ValueError("unsupported_archive_entry")
            total += member.size
            if not 0 <= member.size <= 2_000_000 or total > 32_000_000 or len(files) >= 2000:
                raise ValueError("snapshot_limit")
            source = bundle.extractfile(member)
            assert source is not None
            content = source.read()
            blob = b"blob " + str(len(content)).encode() + b"\0" + content
            if hashlib.sha1(blob).hexdigest() != expected.get(path):
                raise ValueError("snapshot_blob_mismatch")
            files[path] = content
    if not files or set(files) != set(expected):
        raise ValueError("incomplete_snapshot")
    destination.mkdir(parents=True, exist_ok=False)
    for path, content in files.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def validate_observation(result: dict, stage: str, selected: str | None = None) -> None:
    if not isinstance(result, dict):
        raise ValueError("invalid_observation")
    if (
        type(result.get("exit_code")) is not int
        or not isinstance(result.get("ids"), list)
        or not all(isinstance(i, str) and i for i in result["ids"])
        or len(set(result["ids"])) != len(result["ids"])
        or not isinstance(result.get("reports"), list)
    ):
        raise ValueError("invalid_observation")
    for report in result["reports"]:
        if (
            not isinstance(report, dict)
            or report.get("test_id") not in result["ids"]
            or report.get("phase") not in {"setup", "call", "teardown"}
            or report.get("outcome") not in {"passed", "failed", "skipped"}
        ):
            raise ValueError("invalid_observation")
    if stage == "single" and result["ids"] != [selected]:
        raise ValueError("wrong_dispatch")
    if (
        stage == "single"
        and result["exit_code"] == 0
        and (
            {r["phase"] for r in result["reports"]} != {"setup", "call", "teardown"}
            or len(result["reports"]) != 3
            or any(r["outcome"] != "passed" or r.get("was_xfail") for r in result["reports"])
        )
    ):
        raise ValueError("selected_test_not_passed")
    if stage in {"single", "full"} and result["exit_code"] == 0 and not result["reports"]:
        raise ValueError("missing_test_verdict")


def freeze_selection(first: dict, second: dict, selected: str) -> dict:
    for result in (first, second):
        if (
            result["exit_code"] != 0
            or not result["ids"]
            or len(set(result["ids"])) != len(result["ids"])
        ):
            raise ValueError("incomplete_inventory")
    if first["ids"] != second["ids"]:
        raise ValueError("unstable_inventory")
    if selected not in first["ids"]:
        raise ValueError("unknown_test")
    return {"inventory": first["ids"], "selected": [selected], "frozen_at": now()}


def run_stage(name: str, image: str, snapshot: Path, stage: str, selected: str | None) -> dict:
    container = "smartregression-candidate-" + uuid4().hex
    timeout = {"build": 60, "collect": 60, "single": 30, "full": 120}[stage]
    args = [
        "docker",
        "create",
        "--name",
        container,
        "--pull=never",
        "--network=none",
        "--read-only",
        "--user=65534:65534",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges=true",
        "--security-opt=seccomp=" + str(HERE / "seccomp.json"),
        "--memory=512m",
        "--memory-swap=512m",
        "--cpus=1",
        "--pids-limit=64",
        "--ulimit=nofile=256:256",
        "--log-driver=none",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--workdir=/repo",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "--env=PYTHONPATH=/repo:/observer",
        "--env=COVERAGE_FILE=/tmp/.coverage",
        "--mount=type=bind,src=" + str(snapshot.resolve()) + ",dst=/repo,readonly",
        "--mount=type=bind,src=" + str(HERE / "worker.py") + ",dst=/observer/worker.py,readonly",
        "--mount=type=bind,src="
        + str(HERE.parent / "g1/worker.py")
        + ",dst=/observer/isolation.py,readonly",
        image,
        "python",
        "/observer/worker.py",
        stage,
        name,
    ]
    if selected is not None:
        args.append(selected)
    try:
        bounded_command(args, 20, 524288)
        inspection = json.loads(bounded_command(["docker", "inspect", container], 15, 32768))[0]
        host = inspection["HostConfig"]
        if (
            host["Privileged"]
            or host["NetworkMode"] != "none"
            or not host["ReadonlyRootfs"]
            or host["Memory"] != 512 * 1024 * 1024
            or host["MemorySwap"] != 512 * 1024 * 1024
            or host["PidsLimit"] != 64
            or host["NanoCpus"] != 1_000_000_000
            or inspection["Config"]["User"] != "65534:65534"
            or any(m["RW"] for m in inspection["Mounts"])
        ):
            raise ValueError("isolation_not_enforced")
        started = now()
        output = bounded_command(["docker", "start", "-a", container], timeout, 524288)
        log_path = snapshot.parent / (stage + "-" + container + ".log")
        log_path.write_bytes(output)
        marker = b"SMARTREGRESSION_CANDIDATE="
        records = [line[len(marker) :] for line in output.splitlines() if line.startswith(marker)]
        if len(records) != 1:
            raise ValueError("invalid_observation")
        result = json.loads(records[0])
        validate_observation(result, stage, selected)
        isolation = result["isolation"]
        quota, period = map(int, isolation["cpu_max"].split())
        if (
            isolation["memory_max"] != str(512 * 1024 * 1024)
            or isolation["pids_max"] != "64"
            or quota / period != 1
        ):
            raise ValueError("runtime_limits_not_enforced")
        result.update(
            started_at=started,
            finished_at=now(),
            container_id=inspection["Id"],
            output_log=log_path.name,
        )
        return result
    finally:
        bounded_command(["docker", "rm", "-f", container], 20, 4096)


def execute(name: str, image: str, output: Path, full: bool) -> None:
    if name not in CANDIDATES:
        raise ValueError("unsupported_candidate")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("pinned_image_required")
    output = output.resolve()
    allowed = HERE.parents[1] / "var"
    if not output.is_relative_to(allowed.resolve()) or output == allowed.resolve():
        raise ValueError("output_must_be_new_under_var")
    # Stop before downloading source or allocating output when the engine is unavailable.
    bounded_command(["docker", "version", "--format", "{{.Server.Version}}"], 15, 4096)
    output.mkdir(parents=True, exist_ok=False)
    repository, revision, selected = CANDIDATES[name]
    ledger = {
        "data_kind": "candidate_reproducibility",
        "repository": repository,
        "target": revision,
        "image": image,
        "started_at": now(),
        "stages": {},
        "harness_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__), HERE / "worker.py", HERE / "seccomp.json"]
        },
    }
    try:
        commit = json.loads(
            bounded_command(
                ["gh", "api", f"repos/{repository}/commits/{revision}"],
                30,
                2_000_000,
            )
        )
        if commit["sha"] != revision:
            raise ValueError("commit_mismatch")
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = json.loads(
            bounded_command(
                ["gh", "api", f"repos/{repository}/git/trees/{tree_sha}?recursive=1"], 30, 2_000_000
            )
        )
        if tree.get("truncated") or any(
            e["type"] not in {"tree", "blob"} or e["mode"] not in {"040000", "100644", "100755"}
            for e in tree["tree"]
        ):
            raise ValueError("unsupported_git_tree")
        expected = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}
        payload = bounded_command(
            ["gh", "api", f"repos/{repository}/tarball/{revision}"],
            60,
            8_000_000,
            merge_stderr=False,
        )
        ledger["archive_sha256"] = hashlib.sha256(payload).hexdigest()
        snapshot = output / "snapshot"
        extract_snapshot(payload, expected, snapshot)
        ledger["git_tree"] = tree["sha"]
        ledger["snapshot_files"] = len(expected)
        for label, stage in [
            ("build", "build"),
            ("collect_1", "collect"),
            ("collect_2", "collect"),
        ]:
            ledger["active_stage"] = label
            result = run_stage(name, image, snapshot, stage, None)
            ledger["stages"][label] = result
            if result["exit_code"] != 0:
                raise ValueError(label + "_failed")
        selection = freeze_selection(
            ledger["stages"]["collect_1"], ledger["stages"]["collect_2"], selected
        )
        selection.update(repository=repository, target=revision, git_tree=tree["sha"], image=image)
        (output / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
        for stage in ["single", "full"] if full else ["single"]:
            ledger["active_stage"] = stage
            result = run_stage(
                name, image, snapshot, stage, selected if stage == "single" else None
            )
            ledger["stages"][stage] = result
            expected_ids = [selected] if stage == "single" else selection["inventory"]
            if result["ids"] != expected_ids or result["exit_code"] != 0:
                raise ValueError(stage + "_failed_or_inventory_changed")
        ledger["status"] = "reproducibility_checks_passed"
    except BaseException as exc:
        # Preserve completed/failed stages; raw exception/output may contain candidate data.
        # Orchestrator boundary also records interruption; re-raise, never convert to success.
        ledger["status"] = "incomplete_or_failed"
        ledger["failure_type"] = type(exc).__name__
        raise
    finally:
        ledger["finished_at"] = now()
        (output / "observations.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--full-suite", action="store_true")
    args = parser.parse_args()
    execute(args.candidate, args.image, args.output, args.full_suite)
