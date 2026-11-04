import hashlib

import pytest

from smartregression.contracts.stages import (
    ChangePayload,
    FileCoverage,
    GraphPayload,
    RunIdentity,
    SnapshotIdentity,
    StageComponent,
    StageEdge,
    validate_artifacts,
)
from smartregression.core.impact.potential_impact import build_potential_impact

BASE = "a" * 40
TARGET = "b" * 40


def identity() -> RunIdentity:
    return RunIdentity(
        repository_id="repo-1",
        run_id="run-1",
        base=SnapshotIdentity(
            repository_id="repo-1", commit=BASE, snapshot_id=hashlib.sha256(b"base").hexdigest()
        ),
        target=SnapshotIdentity(
            repository_id="repo-1",
            commit=TARGET,
            snapshot_id=hashlib.sha256(b"target").hexdigest(),
        ),
        comparison_mode="direct_two_tree",
    )


def changes(*items: tuple[str, str, str | None, str | None]) -> ChangePayload:
    components = []
    files = []
    for path, change, previous_path, symbol in items:
        component_id = hashlib.sha256(
            f"{path}:{change}:{previous_path}:{symbol}".encode()
        ).hexdigest()
        components.append(
            StageComponent(
                id=component_id,
                path=path,
                previous_path=previous_path,
                kind="module" if symbol is None else "function",
                symbol=symbol,
                change=change,
                base_location=None if change == "added" else {"line_start": 1, "line_end": 1},
                target_location=None if change == "deleted" else {"line_start": 1, "line_end": 1},
                reason="content_changed",
            )
        )
        files.append(FileCoverage(path=path, status="completed", limitations=[]))
    return ChangePayload(components=components, files=files)


def graph(
    snapshot: SnapshotIdentity,
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> GraphPayload:
    return GraphPayload(
        snapshot=snapshot,
        nodes=nodes,
        edges=[
            StageEdge(source=source, target=target, kind="absolute_import")
            for source, target in edges
        ],
        unresolved=[],
    )


def test_reverse_reachability_preserves_all_paths_and_classifies_candidates() -> None:
    run = identity()
    changed = changes(("c.py", "modified", None, None))
    dependency_graph = graph(
        run.target,
        ["a.py", "b.py", "c.py", "d.py"],
        [("a.py", "b.py"), ("b.py", "c.py"), ("a.py", "d.py"), ("d.py", "c.py")],
    )

    impact = build_potential_impact(run, changed, dependency_graph)

    assert [(candidate.path, candidate.relationship) for candidate in impact.candidates] == [
        ("a.py", "indirect"),
        ("b.py", "direct"),
        ("c.py", "changed"),
        ("d.py", "direct"),
    ]
    a_candidate = next(candidate for candidate in impact.candidates if candidate.path == "a.py")
    paths = {tuple(path.nodes) for path in impact.paths if path.id in a_candidate.path_ids}
    assert paths == {("a.py", "b.py", "c.py"), ("a.py", "d.py", "c.py")}
    assert all(path.nodes[-1] == "c.py" for path in impact.paths)

    validate_artifacts(run, changed, dependency_graph, impact, None)


def test_cycles_self_loops_and_duplicate_edges_are_safe_and_deterministic() -> None:
    run = identity()
    changed = changes(("c.py", "modified", None, None))
    dependency_graph = graph(
        run.target,
        ["a.py", "b.py", "c.py"],
        [
            ("b.py", "c.py"),
            ("a.py", "b.py"),
            ("b.py", "a.py"),
            ("c.py", "c.py"),
        ],
    )

    first = build_potential_impact(run, changed, dependency_graph)
    second = build_potential_impact(run, changed, dependency_graph)

    assert first == second
    assert {tuple(path.nodes) for path in first.paths} == {
        ("a.py", "b.py", "c.py"),
        ("b.py", "c.py"),
    }
    assert all(len(path.nodes) == len(set(path.nodes)) for path in first.paths)


def test_base_deleted_component_uses_previous_path_and_target_added_is_seeded() -> None:
    run = identity()
    deleted = changes(("new.py", "deleted", "old.py", None))
    base_graph = graph(run.base, ["consumer.py", "old.py"], [("consumer.py", "old.py")])
    base_impact = build_potential_impact(run, deleted, base_graph)
    validate_artifacts(run, deleted, base_graph, base_impact, None)
    assert {candidate.path for candidate in base_impact.candidates} == {"consumer.py", "old.py"}

    added = changes(("new.py", "added", None, None))
    target_graph = graph(run.target, ["consumer.py", "new.py"], [("consumer.py", "new.py")])
    target_impact = build_potential_impact(run, added, target_graph)
    validate_artifacts(run, added, target_graph, target_impact, None)
    assert {candidate.path for candidate in target_impact.candidates} == {"consumer.py", "new.py"}


def test_base_rename_uses_previous_path_without_merging_target_name() -> None:
    run = identity()
    renamed = changes(("new.py", "renamed", "old.py", None))
    dependency_graph = graph(
        run.base,
        ["consumer.py", "old.py", "new.py"],
        [("consumer.py", "old.py"), ("new.py", "new.py")],
    )

    impact = build_potential_impact(run, renamed, dependency_graph)

    assert {candidate.path for candidate in impact.candidates} == {"consumer.py", "old.py"}
    assert all("new.py" not in path.nodes for path in impact.paths)
    validate_artifacts(run, renamed, dependency_graph, impact, None)


@pytest.mark.parametrize(
    ("change", "snapshot", "nodes"),
    [
        ("added", "base", ["old.py"]),
        ("deleted", "target", ["new.py"]),
    ],
)
def test_components_absent_from_selected_snapshot_are_not_seeded(
    change: str, snapshot: str, nodes: list[str]
) -> None:
    run = identity()
    changed = changes(("new.py", change, None, None))
    selected = run.base if snapshot == "base" else run.target
    dependency_graph = graph(selected, nodes, [])

    impact = build_potential_impact(run, changed, dependency_graph)

    assert impact.candidates == []
    assert impact.paths == []
    validate_artifacts(run, changed, dependency_graph, impact, None)


def test_foreign_snapshot_and_present_component_missing_from_graph_are_rejected() -> None:
    run = identity()
    changed = changes(("c.py", "modified", None, None))
    foreign = SnapshotIdentity(
        repository_id="repo-1", commit="c" * 40, snapshot_id=hashlib.sha256(b"foreign").hexdigest()
    )
    with pytest.raises(ValueError, match="graph_snapshot_mismatch"):
        build_potential_impact(run, changed, graph(foreign, ["c.py"], []))

    with pytest.raises(ValueError, match="changed_component_not_in_graph"):
        build_potential_impact(run, changed, graph(run.target, ["other.py"], []))


def test_disconnected_nodes_and_multiple_changed_components_are_deduplicated() -> None:
    run = identity()
    changed = changes(("c.py", "modified", None, None), ("x.py", "modified", None, "f"))
    dependency_graph = graph(
        run.target,
        ["a.py", "c.py", "x.py", "isolated.py"],
        [("a.py", "c.py")],
    )

    impact = build_potential_impact(run, changed, dependency_graph)

    assert [
        (candidate.path, candidate.changed_component_id) for candidate in impact.candidates
    ] == [
        ("a.py", changed.components[0].id),
        ("c.py", changed.components[0].id),
        ("x.py", changed.components[1].id),
    ]
    assert all(candidate.path != "isolated.py" for candidate in impact.candidates)
    assert len({path.id for path in impact.paths}) == len(impact.paths)
    validate_artifacts(run, changed, dependency_graph, impact, None)


def test_empty_graph_and_no_changes_produce_empty_valid_impact() -> None:
    run = identity()
    changed = changes()
    dependency_graph = graph(run.target, [], [])

    impact = build_potential_impact(run, changed, dependency_graph)

    assert impact.candidates == []
    assert impact.paths == []
    validate_artifacts(run, changed, dependency_graph, impact, None)
