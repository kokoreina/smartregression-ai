"""Read two pinned, previously acquired candidates as data; never import/build them."""

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from uuid import uuid4

from smartregression.adapters.runners.candidate_inventory import CANDIDATES, git_tree_digest
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot
from smartregression.core.retrieval.exclusions import EXCLUSIONS_VERSION, exclusion_reason


def execute(candidate_root: Path) -> Path:
    project = Path(__file__).resolve().parents[2]
    root = candidate_root.absolute()
    if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
        raise ValueError("unsafe_candidate_path")
    output = project / "var" / ("index-exclusions-candidates-" + uuid4().hex)
    if any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
        raise ValueError("unsafe_output_directory")
    result = {
        "scope": "pinned candidate static exclusions; no chunker/search/benchmark",
        "policy": EXCLUSIONS_VERSION,
        "candidates": {},
    }
    for name, (_, sha, tree) in CANDIDATES.items():
        base = root / name
        manifest_path = base / "snapshot-manifest.json"
        if any(p.is_symlink() or p.is_junction() for p in (manifest_path, *manifest_path.parents)):
            raise ValueError("unsafe_candidate_path")
        original = json.loads(manifest_path.read_text("utf-8"))
        entries, contents = [], []
        # Validate paths before joining them to the caller-authorized data root.
        from smartregression.core.git.snapshots import validate_snapshot_paths

        validate_snapshot_paths([item["path"] for item in original["files"]])
        for item in original["files"]:
            path = base / "snapshot" / item["path"]
            if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
                raise ValueError("unsafe_candidate_path")
            if path.stat().st_size > 1_000_000:
                raise ValueError("candidate_file_limit")
            raw = path.read_bytes()
            entries.append(TreeEntry(item["path"], item["mode"], item["blob_id"], len(raw)))
            contents.append(raw)
        snapshot = freeze_snapshot(name, sha, tuple(entries), tuple(contents))
        if (
            snapshot.manifest.snapshot_id != original["snapshot_id"]
            or git_tree_digest(snapshot) != tree
        ):
            raise ValueError("candidate_snapshot_mismatch")
        started = time.perf_counter()
        decisions = [
            exclusion_reason(e.path, raw)
            for e, raw in zip(
                snapshot.manifest.files,
                snapshot.contents,
                strict=True,
            )
        ]
        seconds = time.perf_counter() - started
        eligible = [raw for raw, reason in zip(contents, decisions, strict=True) if reason is None]
        result["candidates"][name] = {
            "commit": sha,
            "tree": tree,
            "snapshot_id": snapshot.manifest.snapshot_id,
            "files": len(entries),
            "eligible_files": decisions.count(None),
            "eligible_bytes": sum(map(len, eligible)),
            "excluded_reasons": dict(Counter(r for r in decisions if r is not None)),
            "policy_seconds_single_run": seconds,
            "max_physical_line_content_bytes": max(
                (len(line) for raw in eligible for line in re.split(rb"\r\n|\r|\n", raw)),
                default=0,
            ),
        }
    output.mkdir(parents=True, exist_ok=False)
    evidence = output / "evidence.json"
    evidence.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"evidence": str(evidence), "result": result}))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    execute(parser.parse_args().candidate_root)
