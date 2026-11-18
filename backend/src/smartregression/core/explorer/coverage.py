"""Explain coverage without treating docs/assets, parse failures and unknown calls alike."""

from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import PurePosixPath

from smartregression.contracts.explorer import CoverageDiagnostics, ExplorerGraph


def update_diagnostics(graph: ExplorerGraph, excluded: Iterable[str] = ()) -> None:
    groups = defaultdict(list)
    excluded = set(excluded)
    for path in graph.coverage.unsupported_files:
        suffix = PurePosixPath(path).suffix.lower()
        name = PurePosixPath(path).name.lower()
        if suffix in {
            ".md",
            ".rst",
            ".txt",
            ".png",
            ".svg",
            ".jpg",
            ".jpeg",
            ".gif",
            ".mmd",
        } or name in {"license", "licence", "readme"}:
            group = "documentation_asset"
        elif suffix in {".toml", ".ini", ".cfg", ".conf", ".yaml", ".yml", ".lock"} or (
            name.startswith(("requirements", ".gitignore", ".coveragerc"))
        ):
            group = "configuration"
        else:
            group = "other_unsupported"
        groups[group].append(path)
    graph.coverage.diagnostics = CoverageDiagnostics(
        file_groups={key: sorted(items) for key, items in sorted(groups.items())},
        unresolved_by_reason=dict(sorted(Counter(u.reason for u in graph.unresolved).items())),
        classified_by_kind=dict(
            sorted(Counter(f"{r.category}_{r.kind}" for r in graph.classified_references).items())
        ),
        excluded_files=sorted(excluded),
    )
