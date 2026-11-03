"""Task 2.01 application boundary, independent of the concrete Git adapter."""

from dataclasses import dataclass
from typing import Literal, Protocol

from smartregression.contracts.models import ChangedComponent
from smartregression.core.impact.changed_components import ComponentChange, compare_python


class SnapshotReader(Protocol):
    def diff(self, base: str, target: str) -> list[ChangedComponent]: ...

    def read_text(self, sha: str, path: str) -> str: ...


@dataclass(frozen=True)
class FileAnalysis:
    path: str
    status: Literal["completed", "partial", "file_only"]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ChangeAnalysis:
    repository: str
    base_sha: str
    target_sha: str
    status: Literal["completed", "partial"]
    components: tuple[ComponentChange, ...]
    files: tuple[FileAnalysis, ...]
    schema_version: str = "changed-components/1"
    comparison_mode: str = "direct_two_tree"


def identify_changes(
    reader: SnapshotReader, *, repository: str, base: str, target: str
) -> ChangeAnalysis:
    """Caller authorizes reader/repository. The reader validates immutable commits.

    This stage document is not the canonical AnalysisReport. Non-Python files
    retain file metadata; a Python read/parse limitation leaves a partial record.
    Invalid commits and unsupported Git diff entries propagate as fatal errors.
    """
    if not repository.strip():
        raise ValueError("repository_required")
    changes = reader.diff(base, target)
    records = []
    files = []
    for item in sorted(changes, key=lambda c: c.path):
        records.append(
            ComponentChange(
                item.path, item.previous_path, "file", None, item.change, None, None, "git_diff"
            )
        )
        old_path = item.previous_path or item.path
        old_python = item.change != "added" and old_path.endswith(".py")
        new_python = item.change != "deleted" and item.path.endswith(".py")
        if not old_python and not new_python:
            files.append(FileAnalysis(item.path, "file_only", ("non_python_file_level_only",)))
            continue
        try:
            old = reader.read_text(base, old_path) if old_python else None
            new = reader.read_text(target, item.path) if new_python else None
            records.extend(
                compare_python(old, new, path=item.path, previous_path=item.previous_path)
            )
        except UnicodeError:
            files.append(FileAnalysis(item.path, "partial", ("source_not_utf8",)))
        except ValueError as exc:
            # Stable codes only: never expose input source/path in diagnostics.
            known = {
                "ambiguous_symbol",
                "python_parse_failed",
                "source_limit",
                "binary_source",
                "missing_snapshot_path",
                "unsupported_file_mode",
                "unsupported_path",
                "git_unavailable_or_timeout",
            }
            if str(exc) not in known:
                raise
            files.append(FileAnalysis(item.path, "partial", (str(exc),)))
        else:
            files.append(FileAnalysis(item.path, "completed", ()))
    return ChangeAnalysis(
        repository,
        base,
        target,
        "partial" if any(f.status == "partial" for f in files) else "completed",
        tuple(records),
        tuple(files),
    )
