"""Fixture-only Docker/pytest spike. Not wired to API or the production runner port.

Only task-authored .py snapshots, never arbitrary external repositories. Docker
daemon is a privileged host service; subprocesses below run on the developer's
approved machine, never in the workload. Workload gets no Docker socket or secrets.
"""

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.bounded_process import bounded_command


@dataclass(frozen=True)
class Limits:
    timeout: float = 30
    memory_mib: int = 256
    cpus: float = 1
    pids: int = 64
    output_bytes: int = 65536

    def __post_init__(self) -> None:
        for value, cap in [
            (self.timeout, 120),
            (self.memory_mib, 512),
            (self.cpus, 2),
            (self.pids, 128),
            (self.output_bytes, 262144),
        ]:
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not math.isfinite(value)
                or not 0 < value <= cap
            ):
                raise ValueError("invalid_limits")
        if any(type(v) is not int for v in [self.memory_mib, self.pids, self.output_bytes]):
            raise ValueError("invalid_limits")


def classify_pytest(exit_code: int, *, collecting: bool, reports: list[dict] | None = None) -> str:
    if collecting:
        return {0: "complete", 5: "empty_inventory"}.get(exit_code, "discovery_failed")
    if any(r["phase"] != "call" and r["outcome"] == "failed" for r in reports or []):
        return "setup_error"
    if exit_code == 0 and reports and any(r["outcome"] == "skipped" for r in reports):
        return "skipped"
    return {0: "passed", 1: "test_failed", 5: "no_tests"}.get(exit_code, "infrastructure_error")


def validate_dispatch(expected: str, actual: str, inventory: tuple[str, ...], test_id: str) -> None:
    if expected != actual:
        raise ValueError("snapshot_mismatch")
    if not inventory or len(set(inventory)) != len(inventory) or test_id not in inventory:
        raise ValueError("unknown_test")


def snapshot_digest(root: Path) -> str:
    root = root.resolve(strict=True)
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("unsupported_snapshot")
        if path.is_dir():
            continue
        if not path.is_file() or path.suffix != ".py" or path.stat().st_size > 256_000:
            raise ValueError("unsupported_snapshot")
        count += 1
        if count > 100:
            raise ValueError("unsupported_snapshot")
        digest.update(
            path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0"
        )
    if not count:
        raise ValueError("unsupported_snapshot")
    return digest.hexdigest()


class FixtureWorker:
    def __init__(
        self, image: str, worker: Path, seccomp: Path, limits: Limits | None = None
    ) -> None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
            raise ValueError("pinned_image_required")
        self.image, self.worker, self.seccomp = image, worker, seccomp
        self.limits = limits or Limits()

    def run(
        self,
        root: Path,
        digest: str,
        *,
        test_id: str | None = None,
        inventory: tuple[str, ...] = (),
    ) -> dict:
        actual = snapshot_digest(root)
        if actual != digest:
            raise ValueError("snapshot_mismatch")
        if test_id is not None:
            validate_dispatch(digest, actual, inventory, test_id)
        name = "smartregression-g1-" + uuid4().hex
        limit = self.limits
        args = [
            "docker",
            "create",
            "--name",
            name,
            "--pull=never",
            "--network=none",
            "--read-only",
            "--user=65534:65534",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--security-opt=seccomp=" + str(self.seccomp.resolve()),
            "--memory=" + str(limit.memory_mib) + "m",
            "--memory-swap=" + str(limit.memory_mib) + "m",
            "--cpus=" + str(limit.cpus),
            "--pids-limit=" + str(limit.pids),
            "--ulimit=nofile=256:256",
            "--log-driver=none",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--workdir=/repo",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "--env=PYTHONPATH=/repo",
            "--mount=type=bind,src=" + str(root.resolve()) + ",dst=/repo,readonly",
            "--mount=type=bind,src=" + str(self.worker.resolve()) + ",dst=/worker.py,readonly",
            self.image,
            "python",
            "/worker.py",
            "run" if test_id is not None else "collect",
        ]
        if test_id is not None:
            args.append(test_id)
        try:
            bounded_command(args, 15, limit.output_bytes)
            # Confirm daemon accepted isolation settings before starting workload.
            config = json.loads(bounded_command(["docker", "inspect", name], 15, 32768))[0]
            host = config["HostConfig"]
            if (
                host["Privileged"]
                or host["NetworkMode"] != "none"
                or not host["ReadonlyRootfs"]
                or host["Memory"] != limit.memory_mib * 1024 * 1024
                or host["PidsLimit"] != limit.pids
                or host["NanoCpus"] != int(limit.cpus * 1_000_000_000)
                or any(m["RW"] for m in config["Mounts"])
            ):
                raise ValueError("isolation_not_enforced")
            started_at = datetime.now(UTC).isoformat()
            output = bounded_command(
                ["docker", "start", "-a", name], limit.timeout, limit.output_bytes
            )
            marker = b"SMARTREGRESSION_RESULT="
            lines = [line[len(marker) :] for line in output.splitlines() if line.startswith(marker)]
            if len(lines) != 1:
                raise ValueError("invalid_worker_result")
            result = json.loads(lines[0])
            if (
                type(result.get("exit_code")) is not int
                or not isinstance(result.get("ids"), list)
                or not all(isinstance(i, str) for i in result["ids"])
                or len(set(result["ids"])) != len(result["ids"])
                or not isinstance(result.get("reports"), list)
            ):
                raise ValueError("invalid_worker_result")
            if test_id is not None and result["ids"] != [test_id]:
                raise ValueError("invalid_worker_result")
            result["status"] = classify_pytest(
                result["exit_code"], collecting=test_id is None, reports=result["reports"]
            )
            result["snapshot_digest"] = digest
            result["started_at"] = started_at
            result["finished_at"] = datetime.now(UTC).isoformat()
            result["container_id"] = config["Id"]
            return result
        finally:
            # Even create/start/timeout/output-limit failures must remove the workload.
            bounded_command(["docker", "rm", "-f", name], 15, 4096)
