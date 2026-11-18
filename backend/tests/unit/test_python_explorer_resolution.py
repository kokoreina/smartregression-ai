"""Expected Python edges and non-edges, checked without importing fixture code."""

import pytest

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.contracts.explorer import ExplorerGraph
from smartregression.core.explorer.graph import build_graph


def graph(sources):
    return build_graph("python-resolution-fixture", "a" * 40, sources, parse_javascript)


def call_targets(value, source="app.py"):
    nodes = {node.id: node for node in value.nodes}
    return {
        (edge.target_path, nodes[edge.target].symbol)
        for edge in value.edges
        if edge.kind == "calls" and edge.source_path == source
    }


def test_python_reexports_and_dotted_module_aliases_resolve_to_defining_file():
    value = graph(
        {
            "pkg/__init__.py": "from .worker import work as task\n",
            "pkg/worker.py": "def work():\n    return 1\n",
            "app.py": "from pkg import task as run\nimport pkg.worker\n"
            "import pkg.worker as worker\nrun()\npkg.worker.work()\nworker.work()\n",
        }
    )
    assert call_targets(value) == {("pkg/worker.py", "work")}
    assert len([e for e in value.edges if e.kind == "calls" and e.source_path == "app.py"]) == 3


def test_function_local_import_does_not_leak_to_other_functions():
    value = graph(
        {
            "worker.py": "def work():\n    return 1\n",
            "app.py": "def allowed():\n    from worker import work\n    return work()\n"
            "def unknown():\n    return work()\n",
        }
    )
    calls = [e for e in value.edges if e.kind == "calls" and e.source_path == "app.py"]
    assert len(calls) == 1
    assert calls[0].evidence.line_start == 3
    assert any(u.line == 5 for u in value.unresolved)


def test_nested_assignment_does_not_shadow_a_sibling_call():
    value = graph(
        {
            "worker.py": "def work():\n    return 1\n",
            "app.py": "from worker import work\ndef outer():\n"
            "    def inner():\n        work = lambda: 2\n        return work()\n"
            "    return work()\n",
        }
    )
    calls = [e for e in value.edges if e.kind == "calls" and e.source_path == "app.py"]
    assert len(calls) == 1
    assert calls[0].evidence.line_start == 6


def test_shadowed_import_and_rebound_module_function_never_invent_calls():
    value = graph(
        {
            "worker.py": "def work():\n    return 1\n",
            "app.py": "from worker import work\ndef masked(work):\n    return work()\n"
            "def local():\n    work = lambda: 2\n    return work()\n"
            "def original():\n    pass\noriginal = object()\noriginal()\n",
        }
    )
    assert not call_targets(value)


def test_builtin_and_stdlib_references_are_explained_separately_from_unknowns():
    value = graph({"app.py": "import json\nlen([])\njson.dumps({})\nmissing()\n"})
    assert [u.reference for u in value.unresolved] == ["missing"]
    classified = {(r.reference, r.category) for r in value.classified_references}
    assert ("len", "builtin") in classified
    assert ("json", "stdlib") in classified
    assert ("json.dumps", "stdlib") in classified
    assert value.coverage.diagnostics.unresolved_by_reason == {"unresolved_static_call": 1}


def test_builtin_shadow_is_not_classified_as_a_known_builtin():
    value = graph({"app.py": "def run(len):\n    return len([])\n"})
    assert not value.classified_references
    assert value.coverage.status == "partial"


def test_internal_missing_import_is_distinct_from_possible_external_dependency():
    value = graph(
        {
            "pkg/__init__.py": "",
            "pkg/app.py": "from .missing import work\nimport third_party_unknown\nwork()\n",
        }
    )
    reasons = {u.reason for u in value.unresolved}
    assert "unresolved_internal_import" in reasons
    assert "external_or_unresolved_import" in reasons


def test_reexport_cycle_and_missing_member_remain_unresolved_without_inventing_edges():
    value = graph(
        {
            "pkg/__init__.py": "from .other import task\n",
            "pkg/other.py": "from . import task\n",
            "app.py": "from pkg import task\ntask()\n",
        }
    )
    assert not call_targets(value)
    assert any(u.reason == "unresolved_static_call" for u in value.unresolved)


@pytest.mark.parametrize(
    "source",
    [
        "from unknown import *\nlen([])\n",
        "len = lambda x: 0\nlen([])\n",
        "import json\njson.dumps = replacement\njson.dumps({})\n",
        "exec(code)\nlen([])\n",
        "[(len := callback) for x in []]\nlen([])\n",
        "match item:\n    case {'handler': len}:\n        len([])\n",
    ],
)
def test_dynamic_or_rebound_names_are_never_classified_as_known_builtin_or_stdlib_calls(source):
    value = graph({"app.py": source})
    assert not [r for r in value.classified_references if r.kind == "call"]
    assert not call_targets(value)


def test_missing_module_member_does_not_fall_back_to_python_builtins():
    value = graph({"local.py": "", "app.py": "import local\nlocal.len([])\n"})
    assert not value.classified_references
    assert any(u.reference == "local.len" for u in value.unresolved)


def test_method_body_does_not_treat_class_namespace_as_a_lexical_function_scope():
    value = graph(
        {
            "app.py": "class A:\n    def helper(self):\n        pass\n"
            "    def run(self):\n        helper()\n"
        }
    )
    assert not call_targets(value)


def test_external_classification_does_not_hide_a_same_named_local_module():
    value = graph(
        {
            "json.py": "def dumps(value):\n    return value\n",
            "app.py": "import json\njson.dumps({})\n",
        }
    )
    assert call_targets(value) == {("json.py", "dumps")}
    assert not value.classified_references


def test_rebound_class_member_never_invents_a_method_call():
    value = graph(
        {"app.py": "class A:\n    def work():\n        pass\n    work = callback\nA.work()\n"}
    )
    assert not call_targets(value)


def test_coverage_diagnostics_separate_file_kinds_and_keep_legacy_status_conservative():
    value = graph(
        {
            "app.py": "def work():\n    return len([])\n",
            "README.md": "Docs",
            "pytest.ini": "[pytest]",
            "page.ts": "const x=1;",
        }
    )
    assert value.coverage.status == "partial"
    assert value.coverage.unparsed_files == []
    assert value.coverage.diagnostics.file_groups == {
        "configuration": ["pytest.ini"],
        "documentation_asset": ["README.md"],
        "other_unsupported": ["page.ts"],
    }
    assert not value.unresolved


def test_legacy_cached_graph_without_diagnostic_fields_remains_readable():
    payload = graph({"app.py": "pass\n"}).model_dump(mode="json")
    payload.pop("classified_references")
    payload["coverage"].pop("diagnostics")
    value = ExplorerGraph.model_validate(payload)
    assert value.classified_references == []
    assert value.coverage.diagnostics is None


def test_relative_package_attribute_reexport_resolves_to_defining_class():
    value = graph(
        {
            "pkg/__init__.py": "from .engine import Engine\n",
            "pkg/engine.py": "class Engine:\n    pass\n",
            "app.py": "from pkg import Engine\nEngine()\n",
            "pkg/use.py": "from . import Engine\nEngine()\n",
        }
    )
    assert call_targets(value, "pkg/use.py") == {("pkg/engine.py", "Engine")}
    assert not [u for u in value.unresolved if u.reason == "unresolved_internal_import"]


def test_from_namespace_package_import_submodule_without_init():
    value = graph(
        {
            "pkg/worker.py": "def work():\n    pass\n",
            "app.py": "from pkg import worker\nworker.work()\n",
        }
    )
    assert call_targets(value) == {("pkg/worker.py", "work")}
    assert any(
        e.kind == "imports" and e.source_path == "app.py" and e.target_path == "pkg/worker.py"
        for e in value.edges
    )


def test_package_export_wins_over_a_same_named_child_module():
    value = graph(
        {
            "pkg/__init__.py": "def task():\n    return 1\n",
            "pkg/task.py": "def work():\n    return 2\n",
            "app.py": "from pkg import task\ntask()\n",
        }
    )
    assert call_targets(value) == {("pkg/__init__.py", "task")}


def test_nested_function_definition_is_not_an_attribute_of_the_outer_function():
    value = graph({"app.py": "def outer():\n    def inner():\n        pass\nouter.inner()\n"})
    assert not call_targets(value)


def test_excluded_local_module_name_blocks_stdlib_classification():
    value = build_graph(
        "python-fixture",
        "a" * 40,
        {"app.py": "import json\njson.dumps({})\n"},
        parse_javascript,
        known_paths=["json.py"],
    )
    assert not value.classified_references
    assert value.unresolved
