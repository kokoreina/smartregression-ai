"""Bounded G1 collection for exact task-authored fixtures, never arbitrary repositories."""

import hashlib
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.bounded_process import CommandFailure
from smartregression.adapters.runners.inventory_fixtures import FIXTURE_CASES, fixture_sources
from smartregression.adapters.runners.pytest_spike import FixtureWorker, snapshot_digest
from smartregression.core.execution.inventory import (
    DiscoveryResult,
    InventoryIdentity,
    finalize_discovery,
)
from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    canonical_json,
    validate_frozen_snapshot,
)


class FixtureInventoryCollector:
    def __init__(self, worker: FixtureWorker, workspace: Path) -> None:
        self.worker = worker
        self.workspace = workspace.resolve(strict=True)
        self._configuration_digest = self._digest()
        self.last_observation: dict = {}

    @property
    def configuration_digest(self) -> str:
        return self._configuration_digest

    def _digest(self) -> str:
        for path in (self.worker.worker, self.worker.seccomp, self.workspace):
            if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
                raise ValueError("collector_configuration_changed")
        return hashlib.sha256(
            canonical_json(
                {
                    "adapter": "owned-fixture-discovery/1",
                    "framework": "pytest",
                    "image": self.worker.image,
                    "limits": vars(self.worker.limits),
                    "worker": hashlib.sha256(self.worker.worker.read_bytes()).hexdigest(),
                    "seccomp": hashlib.sha256(self.worker.seccomp.read_bytes()).hexdigest(),
                    "network": "none",
                    "plugin_autoload": False,
                    "mode": "collect-only",
                }
            )
        ).hexdigest()

    def collect(self, snapshot: FrozenSnapshot, *, identity: InventoryIdentity) -> DiscoveryResult:
        self.last_observation = {
            "image_id": self.worker.image,
            "configuration_digest": self.configuration_digest,
            "runtime_observation": None,
        }
        validate_frozen_snapshot(snapshot)
        manifest = snapshot.manifest
        if (identity.repository_id, identity.target_commit, identity.snapshot_digest) != (
            manifest.repository_id,
            manifest.commit,
            manifest.snapshot_id,
        ):
            raise ValueError("inventory_identity_mismatch")
        if (
            self._digest() != self.configuration_digest
            or identity.configuration_digest != self.configuration_digest
        ):
            raise ValueError("collector_configuration_changed")
        sources = {
            item.path: raw for item, raw in zip(manifest.files, snapshot.contents, strict=True)
        }
        if sources not in [fixture_sources(case) for case in FIXTURE_CASES]:
            raise ValueError("fixture_not_authorized")
        root = self.workspace / ("inventory-" + uuid4().hex)
        root.mkdir()
        try:
            for path, raw in sources.items():
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(raw)
            try:
                result = self.worker.run(root, snapshot_digest(root))
            except subprocess.TimeoutExpired:
                return finalize_discovery(
                    expected=identity, observed=identity, payload=None, termination="timeout"
                )
            except CommandFailure as exc:
                raise ValueError("discovery_infrastructure_error") from exc
            except ValueError as exc:
                if str(exc) != "output_limit":
                    raise
                return finalize_discovery(
                    expected=identity, observed=identity, payload=None, termination="output_limit"
                )
            payload = {
                key: result.get(key)
                for key in ("ids", "exit_code", "collection_finished", "collection_errors")
            }
            if result.get("reports") != []:
                raise ValueError("invalid_worker_result")
            limits = self.worker.limits
            isolation = result.get("isolation", {})
            if not isinstance(isolation, dict) or not isinstance(isolation.get("cpu_max"), str):
                raise ValueError("invalid_worker_result")
            cpu = isolation["cpu_max"].split()
            if (
                isolation.get("uid") != 65534
                or isolation.get("seccomp") != 2
                or isolation.get("no_new_privileges") is not True
                or isolation.get("network") != ["lo"]
                or isolation.get("memory_max") != str(limits.memory_mib * 1024 * 1024)
                or isolation.get("pids_max") != str(limits.pids)
                or len(cpu) != 2
                or not all(x.isdecimal() for x in cpu)
                or int(cpu[1]) <= 0
                or int(cpu[0]) / int(cpu[1]) != limits.cpus
            ):
                raise ValueError("isolation_not_enforced")
            self.last_observation["runtime_observation"] = {
                key: result.get(key)
                for key in (
                    "isolation",
                    "python",
                    "pytest",
                    "packages",
                    "started_at",
                    "finished_at",
                    "container_id",
                    "snapshot_digest",
                )
            }
            return finalize_discovery(expected=identity, observed=identity, payload=payload)
        finally:
            # This invocation exclusively owns this fresh directory. Workloads
            # receive a read-only bind; concurrent privileged host mutation is out of scope.
            if root.is_symlink() or root.is_junction() or root.resolve().parent != self.workspace:
                raise ValueError("unsafe_inventory_cleanup")
            shutil.rmtree(root)
