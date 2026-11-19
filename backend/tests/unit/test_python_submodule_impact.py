"""Named package imports must preserve the submodule dependency and its evidence."""

import pytest

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.graph import build_graph, impact


@pytest.mark.parametrize("reference", ["sqlparse.engine", "."])
def test_package_reexport_records_submodule_and_reverse_impact(reference):
    sources = {
        "sqlparse/__init__.py": "from sqlparse.engine.filter_stack import run\n",
        "sqlparse/engine/__init__.py": f"from {reference} import grouping\n",
        "sqlparse/engine/grouping.py": "def group(stmt):\n    return stmt\n",
        "sqlparse/engine/filter_stack.py": (
            "from sqlparse.engine import grouping as selected\n"
            "def run(stmt):\n    return selected.group(stmt)\n"
        ),
        "app.py": "import sqlparse\n",
        "unrelated.py": "value = 1\n",
    }
    graph = build_graph("fixture", "a" * 40, sources, parse_javascript)
    target = "sqlparse/engine/grouping.py"
    incoming = {
        e.source_path for e in graph.edges if e.kind == "imports" and e.target_path == target
    }
    assert incoming == {"sqlparse/engine/__init__.py", "sqlparse/engine/filter_stack.py"}
    result = impact(graph, {target})
    assert result.direct == sorted(incoming)
    assert result.indirect == ["app.py", "sqlparse/__init__.py"]
    assert result.counts == {"changed": 1, "direct": 2, "indirect": 2, "potential": 5}
    assert any(
        e.kind == "calls"
        and e.source_path == "sqlparse/engine/filter_stack.py"
        and e.target_path == target
        and e.evidence.line_start == 3
        for e in graph.edges
    )
    assert all(
        e.evidence.line_start == 1
        for e in graph.edges
        if e.kind == "imports" and e.target_path == target
    )


def test_explicit_package_attribute_takes_precedence_over_same_named_submodule():
    graph = build_graph(
        "fixture",
        "a" * 40,
        {
            "pkg/__init__.py": "def child():\n    return 1\n",
            "pkg/child.py": "def work():\n    return 2\n",
            "app.py": "from pkg import child\nchild()\n",
        },
        parse_javascript,
    )
    assert not any(e.kind == "imports" and e.target_path == "pkg/child.py" for e in graph.edges)
    assert any(e.kind == "calls" and e.target_path == "pkg/__init__.py" for e in graph.edges)


def test_cyclic_reexports_do_not_invent_submodule_dependencies():
    graph = build_graph(
        "fixture",
        "a" * 40,
        {
            "a/__init__.py": "from b import missing\n",
            "b/__init__.py": "from a import missing\n",
            "app.py": "from a import missing\nmissing()\n",
        },
        parse_javascript,
    )
    assert not any(e.kind == "calls" for e in graph.edges)
    assert any(item.path == "app.py" for item in graph.unresolved)


@pytest.mark.parametrize(
    "source",
    [
        "from pkg import child\nchild = 1\n",
        "from pkg import child\nfrom pkg import child\n",
        "def f(child):\n    from pkg import child\n    return child\n",
    ],
)
def test_import_dependency_survives_rebinding_in_importing_scope(source):
    value = build_graph(
        "fixture",
        "a" * 40,
        {
            "pkg/__init__.py": "",
            "pkg/child.py": "value = 1\n",
            "app.py": source,
        },
        parse_javascript,
    )
    assert impact(value, {"pkg/child.py"}).direct == ["app.py"]


def test_reexported_dotted_import_preserves_the_module_suffix():
    value = build_graph(
        "fixture",
        "a" * 40,
        {
            "pkg/__init__.py": "import dep.child\n",
            "dep/__init__.py": "",
            "dep/child.py": "def work():\n    pass\n",
            "app.py": "from pkg import dep\ndep.child.work()\ndep.work()\n",
        },
        parse_javascript,
    )
    assert {e.evidence.line_start for e in value.edges if e.kind == "calls"} == {2}
