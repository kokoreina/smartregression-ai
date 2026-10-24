"""G1-only container adapter. No host-execution fallback and no API wiring."""

import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from smartregression.core.execution.config import ExecutionConfig
from smartregression.core.git.changes import validate_path


class WorkerError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessObservation:
    returncode: int
    output: str
    termination_reason: str | None = None


@dataclass(frozen=True)
class Inventory:
    target_sha: str
    snapshot_path: str
    config_hash: str
    snapshot_hash: str
    ids: tuple[str, ...]
    status: str

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(self.ids).encode()).hexdigest()


def _bounded_process(command: list[str], timeout: float, limit: int) -> ProcessObservation:
    env = {
        k: os.environ[k]
        for k in (
            "PATH",
            "SystemRoot",
            "COMSPEC",
            "TEMP",
            "TMP",
            "HOME",
            "USERPROFILE",
            "DOCKER_CONFIG",
        )
        if k in os.environ
    }
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
        )
    except OSError as exc:
        raise WorkerError("docker_unavailable") from exc
    chunks: queue.Queue[bytes | None] = queue.Queue(maxsize=16)
    stopped = threading.Event()

    def read() -> None:
        assert proc.stdout is not None
        while not stopped.is_set():
            block = proc.stdout.read1(4096)
            while not stopped.is_set():
                try:
                    chunks.put(block or None, timeout=0.1)
                    break
                except queue.Full:
                    continue
            if not block:
                break

    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    output = bytearray()
    deadline = time.monotonic() + timeout
    code = None
    termination_reason = None
    try:
        while True:
            if time.monotonic() >= deadline:
                code = 124
                termination_reason = "timeout"
                break
            try:
                block = chunks.get(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if block is None:
                code = proc.wait(timeout=max(0.001, deadline - time.monotonic()))
                break
            if len(output) + len(block) > limit:
                code = 125
                termination_reason = "output_limit"
                break
            output.extend(block)
    except subprocess.TimeoutExpired:
        code = 124
        termination_reason = "timeout"
    finally:
        stopped.set()
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        thread.join(timeout=2)
        if proc.stdout:
            proc.stdout.close()
    return ProcessObservation(code, output.decode("utf-8", errors="replace"), termination_reason)


def _events(output: str) -> list[dict]:
    try:
        events = [
            json.loads(line.removeprefix("SMARTREGRESSION_EVENT "))
            for line in output.splitlines()
            if line.startswith("SMARTREGRESSION_EVENT ")
        ]
        if any(not isinstance(item, dict) for item in events):
            raise ValueError
        return events
    except (ValueError, TypeError) as exc:
        raise WorkerError("invalid_worker_output") from exc


def _valid_id(value: str) -> bool:
    try:
        if not isinstance(value, str) or len(value) > 2048 or "::" not in value:
            return False
        if any(ord(char) < 32 for char in value):
            return False
        validate_path(value.split("::")[0])
        return True
    except ValueError:
        return False


def snapshot_digest(snapshot: Path) -> str:
    root = snapshot.resolve(strict=True)
    digest = hashlib.sha256()
    files = 0
    total = 0
    for item in sorted(root.rglob("*")):
        if item.is_symlink() or item.is_junction():
            raise WorkerError("snapshot_link_rejected")
        if not item.is_file():
            continue
        files += 1
        total += item.stat().st_size
        if files > 100 or total > 1024 * 1024:
            raise WorkerError("fixture_size_exceeded")
        data = item.read_bytes()
        digest.update(item.relative_to(root).as_posix().encode() + b"\0")
        digest.update(len(data).to_bytes(8) + data)
    return digest.hexdigest()


class DockerFixtureWorker:
    def __init__(self, image: str, *, execute: Callable = _bounded_process):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
            raise WorkerError("immutable_local_image_required")
        self.image = image
        self.execute = execute

    def _run(
        self,
        snapshot: Path,
        sha: str,
        config: ExecutionConfig,
        mode: str,
        test_id: str | None = None,
    ) -> ProcessObservation:
        root = snapshot.resolve(strict=True)
        if not root.is_dir() or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            raise WorkerError("invalid_snapshot")
        if "," in str(root) or any(ord(c) < 32 for c in str(root)):
            raise WorkerError("unsupported_mount_path")
        # Caller authorization is separate; a LICENSE marker alone does not establish trust.
        if not (root / "LICENSE").is_file():
            raise WorkerError("fixture_provenance_required")
        if any(item.is_symlink() or item.is_junction() for item in root.rglob("*")):
            raise WorkerError("snapshot_link_rejected")
        name = "smartregression-g1-" + uuid4().hex
        entrypoint = Path(__file__).with_name("fixture_entrypoint.py").resolve()
        request = {"paths": config.test_paths, "args": config.approved_args, "test_id": test_id}
        command = [
            "docker",
            "run",
            "--name",
            name,
            "--pull=never",
            "--read-only",
            "--network=none",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=65534:65534",
            "--pids-limit=64",
            f"--cpus={config.cpu_count}",
            f"--memory={config.memory_mib}m",
            f"--memory-swap={config.memory_mib}m",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "--workdir=/input",
            "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=PYTEST_ADDOPTS=",
            "--env=PYTHONPATH=/input",
            "--mount",
            f"type=bind,source={root},target=/input,readonly",
            "--mount",
            f"type=bind,source={entrypoint},target=/worker.py,readonly",
            "--entrypoint=python",
            self.image,
            "/worker.py",
            mode,
            json.dumps(request),
        ]
        try:
            return self.execute(command, config.timeout_seconds, config.output_bytes)
        finally:
            cleaned = self.execute(["docker", "rm", "--force", name], 10, 4096)
            if cleaned.returncode != 0:
                raise WorkerError("cleanup_failed:" + name)

    def discover(self, snapshot: Path, sha: str, config: ExecutionConfig) -> Inventory:
        frozen_digest = snapshot_digest(snapshot)
        observed = self._run(snapshot, sha, config, "discover")
        status = observed.termination_reason or "failed"
        ids: tuple[str, ...] = ()
        if observed.returncode in {0, 5}:
            try:
                rows = [row for row in _events(observed.output) if row.get("kind") == "inventory"]
                if len(rows) != 1 or not isinstance(rows[0].get("ids"), list):
                    raise WorkerError("invalid_inventory")
                values = rows[0]["ids"]
                if any(not _valid_id(value) for value in values) or len(set(values)) != len(values):
                    raise WorkerError("invalid_inventory")
                if observed.returncode == 0 and values:
                    ids, status = tuple(values), "complete"
                elif observed.returncode == 5 and not values:
                    status = "empty"
            except WorkerError:
                status = "failed"
        if snapshot_digest(snapshot) != frozen_digest:
            raise WorkerError("snapshot_changed")
        return Inventory(
            sha, str(snapshot.resolve()), config.fingerprint, frozen_digest, ids, status
        )

    def run_one(
        self, snapshot: Path, sha: str, inventory: Inventory, nodeid: str, config: ExecutionConfig
    ) -> ProcessObservation:
        if (
            inventory.target_sha != sha
            or inventory.snapshot_path != str(snapshot.resolve())
            or inventory.config_hash != config.fingerprint
            or inventory.status != "complete"
            or inventory.snapshot_hash != snapshot_digest(snapshot)
            or nodeid not in inventory.ids
            or not _valid_id(nodeid)
        ):
            raise WorkerError("invalid_dispatch")
        return self._run(snapshot, sha, config, "run", nodeid)
