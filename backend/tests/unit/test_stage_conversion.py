"""Conversions consume real pure producers; no repository code is executed."""

import hashlib
from dataclasses import replace

import pytest

from smartregression.application.changed_components import identify_changes
from smartregression.application.stage_conversion import (
    changes_result,
    graph_result,
    identity_from_snapshots,
    ordering_inputs,
    review_result,
)
from smartregression.contracts.models import ChangedComponent
from smartregression.core.git.snapshots import SnapshotPair, TreeEntry, freeze_snapshot
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.review_ordering import order_for_review

BASE = "a" * 40
TARGET = "b" * 40


def snapshot(commit: str, sources: dict[str, str]):
    entries, contents = [], []
    for path, source in sorted(sources.items()):
        raw = source.encode()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        entries.append(TreeEntry(path, "100644", blob, len(raw)))
        contents.append(raw)
    return freeze_snapshot("repo-1", commit, tuple(entries), tuple(contents))


def pair():
    return SnapshotPair(
        snapshot(BASE, {"a.py": "def f():\n    return 1\n", "b.py": "import a\n"}),
        snapshot(TARGET, {"a.py": "def f():\n    return 2\n", "b.py": "import a\n"}),
        "private-local-path",
    )


class Reader:
    def diff(self, base: str, target: str):
        assert (base, target) == (BASE, TARGET)
        return [ChangedComponent(path="a.py", change="modified")]

    def read_text(self, sha: str, path: str):
        assert path == "a.py"
        return "def f():\n    return 1\n" if sha == BASE else "def f():\n    return 2\n"


def test_real_changes_graph_ordering_keep_identity_and_spans() -> None:
    identity = identity_from_snapshots(pair(), run_id="run-1")
    result = identify_changes(Reader(), repository="repo-1", base=BASE, target=TARGET)
    changed = changes_result(result, identity)
    assert changed.data.components[-1].symbol == "f"
    assert changed.data.components[-1].base_location.line_start == 1
    assert changed.data.components[-1].target_location.line_end == 2
    assert changes_result(result, identity) == changed
    graph = graph_result(
        build_dependency_graph(
            repository="repo-1", revision=TARGET, sources={"a.py": "", "b.py": "import a\n"}
        ),
        identity.target,
    )
    legacy, edges, limitations = ordering_inputs(changed, graph, identity)
    assert edges == [("b.py", "a.py")]
    ordered = review_result(order_for_review(legacy, edges, limitations), identity.target)
    assert [(c.path, c.tier) for c in ordered.data.candidates] == [
        ("a.py", 1),
        ("a.py", 1),
        ("b.py", 2),
    ]
    assert "private-local-path" not in identity.model_dump_json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository", "wrong"),
        ("base_sha", TARGET),
        ("target_sha", BASE),
        ("schema_version", "changed-components/999"),
        ("comparison_mode", "guess"),
    ],
)
def test_changes_conversion_rejects_foreign_or_unknown_producer(field, value) -> None:
    identity = identity_from_snapshots(pair(), run_id="run-1")
    result = identify_changes(Reader(), repository="repo-1", base=BASE, target=TARGET)
    with pytest.raises(ValueError):
        changes_result(replace(result, **{field: value}), identity)


def test_tampered_snapshot_is_not_an_identity_source() -> None:
    source = pair()
    bad = replace(source, base=replace(source.base, contents=(b"tampered", b"import a\n")))
    with pytest.raises(ValueError):
        identity_from_snapshots(bad, run_id="run-1")


def test_unresolved_graph_remains_partial() -> None:
    identity = identity_from_snapshots(pair(), run_id="run-1")
    result = graph_result(
        build_dependency_graph(
            repository="repo-1", revision=TARGET, sources={"a.py": "import unavailable\n"}
        ),
        identity.target,
    )
    assert result.status == "partial"
    assert result.data.unresolved[0].reference == "unavailable"
    assert result.limitations[0].code == "target_not_in_snapshot"


def test_graph_conversion_cannot_relabel_repository_or_commit() -> None:
    identity = identity_from_snapshots(pair(), run_id="run-1")
    graph = build_dependency_graph(repository="other-repo", revision=TARGET, sources={"a.py": ""})
    with pytest.raises(ValueError):
        graph_result(graph, identity.target)


def test_ordering_projection_does_not_mark_non_python_as_executable() -> None:
    identity = identity_from_snapshots(pair(), run_id="run-1")

    class Files(Reader):
        def diff(self, base, target):
            return [ChangedComponent(path="README.md", change="modified")]

    changed = changes_result(
        identify_changes(Files(), repository="repo-1", base=BASE, target=TARGET), identity
    )
    graph = graph_result(
        build_dependency_graph(repository="repo-1", revision=TARGET, sources={}), identity.target
    )
    legacy, edges, limitations = ordering_inputs(changed, graph, identity)
    assert legacy == []
    assert "non_executable_changes_omitted" in limitations
    assert "non_python_file_level_only" in limitations


def test_container_semantics_and_decorator_spans_survive_conversion() -> None:
    class ClassReader(Reader):
        def read_text(self, sha, path):
            value = 1 if sha == BASE else 2
            return f"class C:\n    @staticmethod\n    def f():\n        return {value}\n"

    identity = identity_from_snapshots(pair(), run_id="run-1")
    stage = changes_result(
        identify_changes(ClassReader(), repository="repo-1", base=BASE, target=TARGET), identity
    )
    by_symbol = {c.symbol: c for c in stage.data.components if c.symbol}
    assert by_symbol["C"].reason == "contains_changed_symbol"
    assert by_symbol["C.f"].reason == "content_changed"
    assert by_symbol["C.f"].base_location.line_start == 2
    assert by_symbol["C.f"].target_location.line_start == 2


@pytest.mark.parametrize("change", ["added", "deleted", "renamed"])
def test_actual_change_producer_preserves_absence_and_previous_path(change: str) -> None:
    class ChangedReader(Reader):
        def diff(self, base, target):
            return [
                ChangedComponent(
                    path="a.py",
                    change=change,
                    previous_path="old.py" if change == "renamed" else None,
                )
            ]

        def read_text(self, sha, path):
            return "def f():\n    return 1\n"

    identity = identity_from_snapshots(pair(), run_id="run-1")
    result = changes_result(
        identify_changes(ChangedReader(), repository="repo-1", base=BASE, target=TARGET), identity
    )
    for item in result.data.components:
        if change == "added":
            assert item.base_location is None
        elif change == "deleted":
            assert item.target_location is None
        else:
            assert item.previous_path == "old.py"


def test_parse_failure_preserves_file_and_partial_reason() -> None:
    class BrokenReader(Reader):
        def read_text(self, sha, path):
            return "def invalid("

    identity = identity_from_snapshots(pair(), run_id="run-1")
    result = changes_result(
        identify_changes(BrokenReader(), repository="repo-1", base=BASE, target=TARGET), identity
    )
    assert result.status == "partial"
    assert result.data.components[0].kind == "file"
    assert result.data.files[0].status == "partial"
    assert result.limitations[0].code == "python_parse_failed"
