import pytest

from tests.fixtures.dependency_graph_cases import (
    EXPECTED_SUPPORTED_EDGES,
    EXPECTED_UNRESOLVED,
    REPOSITORY,
    REVISION,
    SOURCES,
)

from smartregression.core.impact.dependency_graph import (
    DependencyGraph,
    GraphEdge,
    GraphNode,
    build_dependency_graph,
)


def test_graph_records_supported_edges_and_unresolved_imports():
    graph = build_dependency_graph(
        repository=REPOSITORY,
        revision=REVISION,
        sources=SOURCES,
    )

    assert tuple(
        (edge.source.path, edge.target.path, edge.kind) for edge in graph.edges
    ) == EXPECTED_SUPPORTED_EDGES
    assert {
        (item.source_path, item.reference, item.kind) for item in graph.unresolved
    } == EXPECTED_UNRESOLVED
    assert all(node.repository == REPOSITORY for node in graph.nodes)
    assert all(node.revision == REVISION for node in graph.nodes)
    assert all(edge.source.revision == edge.target.revision == REVISION for edge in graph.edges)


def test_graph_rejects_non_snapshot_edge_inputs():
    sources = {"consumer.py": "import provider\n"}

    graph = build_dependency_graph(
        repository=REPOSITORY,
        revision=REVISION,
        sources=sources,
    )

    assert graph.edges == ()
    assert graph.unresolved[0].reason == "target_not_in_snapshot"


def test_graph_rejects_invalid_snapshot_identity():
    with pytest.raises(ValueError, match="invalid_snapshot_identity"):
        build_dependency_graph(repository=REPOSITORY, revision="not-a-sha", sources={})


def test_graph_objects_reject_cross_snapshot_edges():
    with pytest.raises(ValueError, match="invalid_snapshot_identity"):
        GraphNode("a.py", REPOSITORY, "not-a-sha")

    first = GraphNode("a.py", "repo-a", "a" * 40)
    other_repository = GraphNode("b.py", "repo-b", "a" * 40)
    other_revision = GraphNode("c.py", "repo-a", "b" * 40)

    with pytest.raises(ValueError, match="cross_snapshot_edge"):
        GraphEdge(first, other_repository, "absolute_import")
    with pytest.raises(ValueError, match="cross_snapshot_edge"):
        GraphEdge(first, other_revision, "absolute_import")


def test_graph_rejects_mixed_nodes_and_missing_edge_endpoints():
    first = GraphNode("a.py", REPOSITORY, REVISION)
    second = GraphNode("b.py", REPOSITORY, "b" * 40)
    with pytest.raises(ValueError, match="mixed_snapshot_nodes"):
        DependencyGraph((first, second), (), ())

    missing = GraphNode("missing.py", REPOSITORY, REVISION)
    edge = GraphEdge(first, missing, "absolute_import")
    with pytest.raises(ValueError, match="edge_endpoint_not_in_graph"):
        DependencyGraph((first,), (edge,), ())


@pytest.mark.parametrize(
    ("sources", "expected_target"),
    [
        (
            {"pkg/__init__.py": "from .models import User\n", "pkg/models.py": ""},
            "pkg/models.py",
        ),
        (
            {
                "pkg/__init__.py": "",
                "pkg/service.py": "from .models import User\n",
                "pkg/models.py": "",
            },
            "pkg/models.py",
        ),
        (
            {
                "pkg/__init__.py": "",
                "pkg/sub/__init__.py": "",
                "pkg/base.py": "",
                "pkg/sub/service.py": "from ..base import User\n",
            },
            "pkg/base.py",
        ),
        (
            {
                "pkg/__init__.py": "",
                "pkg/sub/__init__.py": "",
                "pkg/sub/models.py": "",
                "pkg/service.py": "from .sub import models\n",
            },
            "pkg/sub/__init__.py",
        ),
        (
            {
                "pkg/__init__.py": "",
                "pkg/sub/__init__.py": "",
                "pkg/sub/deep/__init__.py": "",
                "pkg/base.py": "",
                "pkg/sub/deep/service.py": "from ...base import User\n",
            },
            "pkg/base.py",
        ),
    ],
)
def test_relative_imports_resolve_with_package_context(sources, expected_target):
    graph = build_dependency_graph(repository=REPOSITORY, revision=REVISION, sources=sources)
    assert len(graph.edges) == 1
    assert graph.edges[0].target.path == expected_target


@pytest.mark.parametrize(
    "sources",
    [
        {"service.py": "from .models import User\n"},
        {
            "pkg/__init__.py": "",
            "pkg/sub/__init__.py": "",
            "pkg/sub/service.py": "from ...models import User\n",
        },
    ],
)
def test_relative_import_beyond_root_is_explicitly_unresolved(sources):
    graph = build_dependency_graph(repository=REPOSITORY, revision=REVISION, sources=sources)
    assert graph.edges == ()
    assert graph.unresolved[0].reason == "relative_import_beyond_root"


def test_valid_relative_import_with_missing_target_has_distinct_reason():
    graph = build_dependency_graph(
        repository=REPOSITORY,
        revision=REVISION,
        sources={"pkg/__init__.py": "", "pkg/service.py": "from .missing import User\n"},
    )
    assert graph.edges == ()
    assert graph.unresolved[0].reason == "target_not_in_snapshot"


def test_graph_order_is_deterministic():
    sources = {
        "pkg/__init__.py": "",
        "pkg/z.py": "import pkg.a\n",
        "pkg/a.py": "import missing\n",
    }
    results = [
        build_dependency_graph(repository=REPOSITORY, revision=REVISION, sources=sources)
        for _ in range(10)
    ]
    assert all(result == results[0] for result in results)


def test_dynamic_import_alias_is_unresolved_without_execution():
    sources = {
        "pkg/__init__.py": "",
        "pkg/service.py": (
            "from importlib import import_module\n"
            "import_module('pkg.models')\n"
        ),
        "pkg/models.py": "",
    }
    graph = build_dependency_graph(repository=REPOSITORY, revision=REVISION, sources=sources)
    assert ("dynamic_import", "pkg.models") in {
        (item.kind, item.reference) for item in graph.unresolved
    }
