"""Bridge the existing change producer to verified bytes, never the working tree."""

from typing import Protocol

from smartregression.contracts.models import ChangedComponent
from smartregression.core.git.snapshots import SnapshotPair


class DiffSource(Protocol):
    def diff(self, base: str, target: str) -> list[ChangedComponent]: ...


class FrozenReader:
    """A run-local reader. Caller validates/authorizes the pair before construction."""

    def __init__(self, pair: SnapshotPair, source: DiffSource) -> None:
        self.pair = pair
        self.source = source
        self.files = {
            snapshot.manifest.commit: {
                item.path: (item, content)
                for item, content in zip(snapshot.manifest.files, snapshot.contents, strict=True)
            }
            for snapshot in (pair.base, pair.target)
        }

    def diff(self, base: str, target: str) -> list[ChangedComponent]:
        if (base, target) != (self.pair.base.manifest.commit, self.pair.target.manifest.commit):
            raise ValueError("snapshot_diff_mismatch")
        changes = self.source.diff(base, target)
        old, new = self.files[base], self.files[target]
        expected = {
            path
            for path in old.keys() | new.keys()
            if path not in old
            or path not in new
            or (old[path][0].blob_id, old[path][0].mode)
            != (new[path][0].blob_id, new[path][0].mode)
        }
        expected_old, expected_new = expected & old.keys(), expected & new.keys()
        covered_old: set[str] = set()
        covered_new: set[str] = set()
        for change in changes:
            path = change.path
            previous = change.previous_path
            before: set[str] = set()
            after: set[str] = set()
            if change.change == "renamed":
                if previous is None or previous == path:
                    raise ValueError("snapshot_diff_mismatch")
                before, after = {previous}, {path}
            elif previous is None:
                if change.change == "added":
                    after = {path}
                elif change.change == "deleted":
                    before = {path}
                elif change.change == "modified":
                    before, after = {path}, {path}
            if (
                not (before or after)
                or before & covered_old
                or after & covered_new
                or not before <= expected_old
                or not after <= expected_new
            ):
                raise ValueError("snapshot_diff_mismatch")
            covered_old.update(before)
            covered_new.update(after)
        if covered_old != expected_old or covered_new != expected_new:
            raise ValueError("snapshot_diff_mismatch")
        return changes

    def read_text(self, sha: str, path: str) -> str:
        entry = self.files.get(sha, {}).get(path)
        if entry is None:
            raise ValueError("missing_snapshot_path")
        _, content = entry
        if len(content) > 256_000:
            raise ValueError("source_limit")
        if b"\0" in content:
            raise ValueError("binary_source")
        return content.decode("utf-8", errors="strict")
