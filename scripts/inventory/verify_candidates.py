"""Reproduce both accepted inventories twice; download source as data, never import it."""

import hashlib
import importlib.util
import json
import sys
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.runners.candidate_inventory import (
    CANDIDATES,
    CandidateInventoryCollector,
)
from smartregression.application.inventory import inventory_identity, inventory_stage
from smartregression.application.inventory_store import prepare_inventory
from smartregression.application.stage_conversion import identity_from_snapshots
from smartregression.core.git.snapshots import (
    SnapshotPair,
    TreeEntry,
    canonical_json,
    freeze_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]


class FixedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("unexpected_candidate_download_redirect")


def download(url, cap):
    request = urllib.request.Request(url, headers={"User-Agent": "SmartRegression-inventory/1"})
    with urllib.request.build_opener(FixedRedirect()).open(request, timeout=60) as response:
        if response.status != 200:
            raise ValueError("candidate_download_failed")
        data = response.read(cap + 1)
        if len(data) > cap:
            raise ValueError("candidate_download_limit")
        return data


def source(name, destination):
    repo, sha, tree_sha = CANDIDATES[name]
    tree_raw = download(
        f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1", 2_000_000
    )
    tree = json.loads(tree_raw)
    if (
        tree.get("truncated")
        or tree.get("sha") != tree_sha
        or any(
            e["type"] not in {"blob", "tree"} or e["mode"] not in {"040000", "100644", "100755"}
            for e in tree["tree"]
        )
    ):
        raise ValueError("unsupported_candidate_tree")
    files = sorted((e for e in tree["tree"] if e["type"] == "blob"), key=lambda e: e["path"])
    archive = download(f"https://codeload.github.com/{repo}/tar.gz/{sha}", 8_000_000)
    # Reuse the existing bounded archive/blob verifier, without invoking its runner.
    spec = importlib.util.spec_from_file_location(
        "candidate_archive", ROOT / "scripts/candidates/run_candidates.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.extract_snapshot(archive, {e["path"]: e["sha"] for e in files}, destination / "snapshot")
    (destination / "archive.tar.gz").write_bytes(archive)
    (destination / "tree.json").write_bytes(tree_raw)
    entries, contents = [], []
    for item in files:
        raw = (destination / "snapshot" / item["path"]).read_bytes()
        entries.append(TreeEntry(item["path"], item["mode"], item["sha"], len(raw)))
        contents.append(raw)
    snapshot = freeze_snapshot(name, sha, tuple(entries), tuple(contents))
    (destination / "snapshot-manifest.json").write_bytes(canonical_json(asdict(snapshot.manifest)))
    return snapshot, hashlib.sha256(archive).hexdigest()


def execute(image):
    output = ROOT / "var" / ("candidate-inventory-verification-" + uuid4().hex)
    if any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
        raise ValueError("unsafe_inventory_output")
    output.mkdir(parents=True, exist_ok=False)
    ledger = {
        "passed": False,
        "image_id": image,
        "started_at": datetime.now(UTC).isoformat(),
        "candidates": {},
    }
    try:
        for name in CANDIDATES:
            folder = output / name
            folder.mkdir()
            snapshot, archive_hash = source(name, folder)
            identity = identity_from_snapshots(
                SnapshotPair(snapshot, snapshot, "fixed-public-candidate"),
                run_id="candidate-" + uuid4().hex,
            )
            collector = CandidateInventoryCollector(name, image, ROOT, folder)
            expected = inventory_identity(identity, collector.configuration_digest)
            record = {
                "archive_sha256": archive_hash,
                "identity": identity.model_dump(mode="json"),
                "attempts": [],
            }
            ledger["candidates"][name] = record
            collector.verify_build(snapshot, identity=expected)
            record["build"] = dict(collector.last_observation)
            stages = []
            for _attempt in range(2):
                result = collector.collect(snapshot, identity=expected)
                stage = inventory_stage(result, identity)
                record["attempts"].append(dict(collector.last_observation))
                record["attempts"][-1]["stage"] = stage.model_dump(mode="json")
                if stage.status != "completed":
                    raise ValueError("candidate_collection_failed")
                stages.append(stage)
            first, second = [s.data.test_ids for s in stages]
            if first != second:
                raise ValueError("unstable_candidate_inventory")
            record["ordered_ids_sha256"] = hashlib.sha256(canonical_json(first)).hexdigest()
            record["test_count"] = len(first)
            record["historical_count"] = {"sqlparse": 509, "tinydb": 228}[name]
            record["historical_count_matches"] = len(first) == record["historical_count"]
            record["historical_exact_ids"] = "not_available_in_committed_sprint1_evidence"
            if not record["historical_count_matches"]:
                raise ValueError("historical_inventory_count_changed_review_required")
            write = prepare_inventory(
                identity=identity,
                inventory_id="inventory-1",
                stage=stages[0],
                configuration=collector.configuration,
                exit_code=result.exit_code,
                duration_seconds=collector.last_observation["result"]["duration_seconds"],
            )
            # The DB harness consumes this frozen value in a dedicated test DB.
            (folder / "inventory-write.json").write_bytes(canonical_json(asdict(write)))
        ledger["passed"] = True
    except Exception as exc:
        ledger["error_type"] = type(exc).__name__
        allowed = {
            "candidate_collection_failed",
            "unstable_candidate_inventory",
            "historical_inventory_count_changed_review_required",
            "candidate_environment_mismatch",
            "candidate_setup_failed",
            "candidate_not_authorized",
        }
        ledger["error_code"] = (
            str(exc) if str(exc) in allowed else "candidate_inventory_verification_failed"
        )
    finally:
        ledger["finished_at"] = datetime.now(UTC).isoformat()
        (output / "evidence.json").write_bytes(canonical_json(ledger))
        print(json.dumps({"passed": ledger["passed"], "evidence": str(output / "evidence.json")}))
    return 0 if ledger["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(execute(sys.argv[1]))
