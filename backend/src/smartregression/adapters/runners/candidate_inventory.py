"""Collection for two accepted, complete Git trees only; never arbitrary source."""

import hashlib
import json
import math
import re
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.bounded_process import CommandFailure, bounded_command
from smartregression.application.inventory_store import InventoryConfiguration
from smartregression.core.execution.inventory import InventoryIdentity, finalize_discovery
from smartregression.core.git.snapshots import validate_frozen_snapshot, validate_snapshot_paths

CANDIDATES = {
    "sqlparse": (
        "andialbrecht/sqlparse",
        "60cdc649726bf1bc4f1b336050560b336da715ec",
        "0652386b2d4a79d8f37b9c4ab2e8cfcc41ab32d1",
    ),
    "tinydb": (
        "msiemens/tinydb",
        "edff96aeb2616402e9489d46e90a592c05565621",
        "52a3d82ceab13b0da98cc3b2808218ac02fde924",
    ),
}
OUTPUT_CAP = 524288


def git_tree_digest(snapshot):
    tree = {}
    for entry in snapshot.manifest.files:
        parts = entry.path.split("/")
        parent = tree
        for part in parts[:-1]:
            parent = parent.setdefault(part, {})
        parent[parts[-1]] = entry

    def freeze(node):
        raw = bytearray()
        for name, entry in sorted(
            node.items(), key=lambda kv: (kv[0] + ("/" if isinstance(kv[1], dict) else "")).encode()
        ):
            mode, digest = (
                ("40000", freeze(entry)) if isinstance(entry, dict) else (entry.mode, entry.blob_id)
            )
            raw.extend(mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(digest))
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

    return freeze(tree)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("invalid_worker_result")
        result[key] = value
    return result


def decode_result(raw, identity, mode):
    marker = b"SMARTREGRESSION_INVENTORY="
    records = [line[len(marker) :] for line in raw.splitlines() if line.startswith(marker)]
    if len(raw) > OUTPUT_CAP or len(records) != 1:
        raise ValueError("invalid_worker_result")
    try:
        result = json.loads(records[0], object_pairs_hook=_unique_pairs)
        if (
            set(result)
            != {
                "protocol",
                "identity",
                "mode",
                "test_sources",
                "collection",
                "isolation",
                "environment",
                "exclusions",
                "duration_seconds",
            }
            or result["protocol"] != "inventory/2"
            or result["mode"] != mode
        ):
            raise ValueError("invalid_worker_result")
        if result["identity"] != asdict(identity):
            raise ValueError("inventory_identity_mismatch")
        metadata = result["test_sources"]
        if (
            type(metadata) is not dict
            or set(metadata) != {"version", "items"}
            or metadata["version"] != "pytest-item-path/1"
            or type(metadata["items"]) is not list
        ):
            raise ValueError("invalid_worker_result")
        source_ids = []
        for item in metadata["items"]:
            if (
                type(item) is not dict
                or set(item) != {"test_id", "path"}
                or type(item["test_id"]) is not str
                or item["path"] is not None
                and type(item["path"]) is not str
            ):
                raise ValueError("invalid_worker_result")
            if item["path"] is not None:
                validate_snapshot_paths([item["path"]])
            source_ids.append(item["test_id"])
        if source_ids != result["collection"]["ids"]:
            raise ValueError("invalid_worker_result")
        iso = result["isolation"]
        cpu = iso["cpu_max"].split()
        if (
            iso["uid"] != 65534
            or iso["seccomp"] != 2
            or iso["no_new_privileges"] is not True
            or iso["network"] != ["lo"]
            or iso["memory_max"] != "536870912"
            or iso["pids_max"] != "64"
            or len(cpu) != 2
            or not all(x.isdecimal() for x in cpu)
            or int(cpu[1]) <= 0
            or int(cpu[0]) != int(cpu[1])
        ):
            raise ValueError("isolation_not_enforced")
        duration = result["duration_seconds"]
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
            raise ValueError("invalid_worker_result")
        if type(result["exclusions"]) is not dict or set(result["exclusions"]) != {
            "configuration",
            "collection_skips",
        }:
            raise ValueError("invalid_worker_result")
        return result
    except KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError:
        raise ValueError("invalid_worker_result") from None


class CandidateInventoryCollector:
    def __init__(self, name: str, image: str, project: Path, workspace: Path):
        if name not in CANDIDATES or not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
            raise ValueError("candidate_not_authorized")
        self.name, self.image = name, image
        self.project, self.workspace = project.resolve(strict=True), workspace.resolve(strict=True)
        self.configuration = self._configuration()
        self.last_observation = {}

    def _configuration(self):
        paths = [
            self.project / p
            for p in (
                "scripts/inventory/collect.py",
                "scripts/candidates/seccomp.json",
                "scripts/inventory/requirements.lock",
            )
        ]
        for path in (*paths, self.project, self.workspace):
            if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
                raise ValueError("collector_configuration_changed")
        # Probe code is mounted separately; include it in the observer identity.
        observer = (
            paths[0].read_bytes()
            + b"\0"
            + (self.project / "scripts/g1/worker.py").read_bytes()
            + b"\0"
            + Path(__file__).read_bytes()
        )
        return InventoryConfiguration(
            "candidate-inventory/2",
            self.name,
            self.image,
            hashlib.sha256(observer).hexdigest(),
            hashlib.sha256(paths[1].read_bytes()).hexdigest(),
            hashlib.sha256(paths[2].read_bytes()).hexdigest(),
            plugins=("pytest_cov.plugin",) if self.name == "tinydb" else (),
        )

    @property
    def configuration_digest(self):
        return self.configuration.digest

    def _authorize(self, snapshot, identity):
        validate_frozen_snapshot(snapshot)
        manifest = snapshot.manifest
        if (identity.repository_id, identity.target_commit, identity.snapshot_digest) != (
            manifest.repository_id,
            manifest.commit,
            manifest.snapshot_id,
        ):
            raise ValueError("inventory_identity_mismatch")
        if (manifest.repository_id, manifest.commit, git_tree_digest(snapshot)) != (
            self.name,
            CANDIDATES[self.name][1],
            CANDIDATES[self.name][2],
        ):
            raise ValueError("candidate_not_authorized")
        if (
            identity.configuration_digest != self.configuration_digest
            or self._configuration() != self.configuration
        ):
            raise ValueError("collector_configuration_changed")

    def collect(self, snapshot, *, identity: InventoryIdentity):
        self._authorize(snapshot, identity)
        try:
            result = self._run(snapshot, identity, "collect")
        except subprocess.TimeoutExpired:
            return finalize_discovery(
                expected=identity, observed=identity, payload=None, termination="timeout"
            )
        except CommandFailure:
            raise ValueError("discovery_infrastructure_error") from None
        except ValueError as exc:
            if str(exc) == "output_limit":
                return finalize_discovery(
                    expected=identity, observed=identity, payload=None, termination="output_limit"
                )
            raise
        return finalize_discovery(
            expected=identity, observed=identity, payload=result["collection"]
        )

    def verify_build(self, snapshot, *, identity):
        self._authorize(snapshot, identity)
        result = self._run(snapshot, identity, "build")
        if result["collection"]["exit_code"] != 0:
            raise ValueError("candidate_setup_failed")
        return result

    def _run(self, snapshot, identity, mode):
        self.last_observation = {"configuration_sha256": self.configuration_digest, "mode": mode}
        root = self.workspace / ("candidate-inventory-" + uuid4().hex)
        root.mkdir()
        name = "smartregression-inventory-" + uuid4().hex
        created = False
        try:
            for item, raw in zip(snapshot.manifest.files, snapshot.contents, strict=True):
                target = root / item.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            mounts = [
                (root, "/repo"),
                (self.project / "scripts/inventory/collect.py", "/observer/collect.py"),
                (self.project / "scripts/g1/worker.py", "/observer/isolation.py"),
            ]
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
                "--security-opt=seccomp=" + str(self.project / "scripts/candidates/seccomp.json"),
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
            ]
            for source, destination in mounts:
                args += [
                    "--mount=type=bind,src=" + str(source) + ",dst=" + destination + ",readonly"
                ]
            args += [
                self.image,
                "python",
                "/observer/collect.py",
                mode,
                self.name,
                json.dumps(asdict(identity), separators=(",", ":")),
            ]
            # Cleanup also covers a daemon create that succeeds after the client loses its reply.
            created = True
            bounded_command(args, 20, 4096)
            inspect = json.loads(bounded_command(["docker", "inspect", name], 15, 32768))[0]
            host = inspect["HostConfig"]
            if (
                host["Privileged"]
                or host["NetworkMode"] != "none"
                or not host["ReadonlyRootfs"]
                or host["Memory"] != 536870912
                or host["MemorySwap"] != 536870912
                or host["PidsLimit"] != 64
                or host["NanoCpus"] != 1000000000
                or inspect["Config"]["User"] != "65534:65534"
                or inspect["Image"] != self.image
                or any(m["RW"] for m in inspect["Mounts"])
                or {m["Destination"] for m in inspect["Mounts"]}
                != {"/repo", "/observer/collect.py", "/observer/isolation.py"}
                or len(inspect["Mounts"]) != 3
                or any(m["Type"] != "bind" for m in inspect["Mounts"])
                or host["CapDrop"] != ["ALL"]
                or host["LogConfig"]["Type"] != "none"
                or not any(s.startswith("no-new-privileges") for s in host["SecurityOpt"])
                or not any(s.startswith("seccomp=") for s in host["SecurityOpt"])
                or set(host["Tmpfs"]) != {"/tmp"}
                or not {"noexec", "nosuid", "nodev", "size=64m"}.issubset(
                    set(host["Tmpfs"]["/tmp"].split(","))
                )
            ):
                raise ValueError("isolation_not_enforced")
            raw = bounded_command(["docker", "start", "-a", name], 60, OUTPUT_CAP)
            self.last_observation["output_sha256"] = hashlib.sha256(raw).hexdigest()
            # Logs are bounded diagnostics; inventory comes only from the structured frame.
            (self.workspace / (name + ".log")).write_bytes(raw)
            result = decode_result(raw, identity, mode)
            packages = result["environment"]["packages"]
            locked = dict(
                re.findall(
                    r"^([A-Za-z0-9-]+)==([^\s]+)",
                    (self.project / "scripts/inventory/requirements.lock").read_text(),
                    re.M,
                )
            )
            if result["environment"]["python"] != "3.14.3" or any(
                packages.get(k) != v for k, v in locked.items()
            ):
                raise ValueError("candidate_environment_mismatch")
            self.last_observation.update(
                result=result,
                container_id=inspect["Id"],
                configuration=json.loads(self.configuration.canonical_bytes()),
            )
            return result
        finally:
            try:
                if created:
                    bounded_command(["docker", "rm", "-f", name], 20, 4096)
                    self.last_observation["container_removed"] = True
            finally:
                if (
                    root.is_symlink()
                    or root.is_junction()
                    or root.resolve().parent != self.workspace
                ):
                    raise ValueError("unsafe_inventory_cleanup")
                shutil.rmtree(root)
