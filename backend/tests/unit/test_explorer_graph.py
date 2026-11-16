"""Hand-authored Python/JavaScript graph expectations, without executing input code."""

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.graph import build_graph, hotspots, impact, neighborhood

REPO = "github-fixture"
SHA = "a" * 40


def graph(sources):
    return build_graph(REPO, SHA, sources, parse_javascript)


def test_independent_40_file_fixture_has_10_file_potential_scope():
    sources = {"changed.js": "export function pay(){}"}
    sources.update({f"direct{i}.js": 'import "./changed.js";' for i in range(3)})
    sources.update({f"indirect{i}.js": f'import "./direct{i % 3}.js";' for i in range(6)})
    sources.update({f"unrelated{i}.js": "export const value=1;" for i in range(30)})
    result = impact(graph(sources), {"changed.js"})
    assert result.denominator == 40
    assert result.counts == {"changed": 1, "direct": 3, "indirect": 6, "potential": 10}
    assert result.percentages == {
        "changed": 2.5,
        "direct": 7.5,
        "indirect": 15.0,
        "potential": 25.0,
    }


def test_js_literal_imports_require_and_index_resolution():
    value = graph(
        {
            "payment.js": "export function pay() { return 1; }",
            "lib/index.js": 'export {pay} from "../payment.js";',
            "app.js": 'import {pay as payment} from "./payment"; '
            "export function run(){ return payment(); }",
            "server.js": 'const payment = require("./payment"); payment.pay();',
        }
    )
    imports = {(e.source_path, e.target_path) for e in value.edges if e.kind == "imports"}
    assert imports == {
        ("lib/index.js", "payment.js"),
        ("app.js", "payment.js"),
        ("server.js", "payment.js"),
    }
    calls = [e for e in value.edges if e.kind == "calls"]
    assert any(e.source_path == "app.js" and e.target_path == "payment.js" for e in calls)
    assert all(e.evidence.commit == SHA for e in value.edges)
    assert all(e.evidence.line_start >= 1 for e in value.edges if e.evidence.kind == "source_range")
    nodes = {node.id: node for node in value.nodes}
    # Folder containment is metadata; file-to-symbol containment has real source ranges.
    assert all(
        e.evidence.line_start is None
        for e in value.edges
        if e.kind == "contains" and nodes[e.source].kind == "directory"
    )


def test_python_reuse_and_import_is_not_call():
    value = graph(
        {
            "payment.py": "def pay():\n    return 1\n",
            "app.py": "from payment import pay\ndef run():\n    return pay()\n",
            "unused.py": "import payment\n",
        }
    )
    assert any(e.kind == "imports" and e.source_path == "unused.py" for e in value.edges)
    assert not any(e.kind == "calls" and e.source_path == "unused.py" for e in value.edges)
    assert any(e.kind == "calls" and e.source_path == "app.py" for e in value.edges)


def test_dynamic_external_and_syntax_errors_remain_unresolved():
    value = graph(
        {
            "app.js": 'import fs from "fs"; const x=require(name); function broken( {',
            "types.ts": "export const a=1;",
        }
    )
    assert value.coverage.status == "partial"
    assert "app.js" in value.coverage.unparsed_files
    assert "types.ts" in value.coverage.unsupported_files


def test_diamond_impact_has_disjoint_sets_and_explicit_denominator():
    value = graph(
        {
            "a.js": "export function a(){}",
            "b.js": 'import "./a.js";',
            "c.js": 'import "./a.js";',
            "d.js": 'import "./b.js"; import "./c.js";',
        }
    )
    result = impact(value, {"a.js"})
    assert set(result.changed) == {"a.js"} and set(result.direct) == {"b.js", "c.js"}
    assert set(result.indirect) == {"d.js"} and result.denominator == 4
    assert result.percentages["direct"] == 50.0 and result.percentages["potential"] == 100.0


def test_cycle_bounded_view_and_structural_hotspots():
    value = graph(
        {"a.js": 'import "./b.js";', "b.js": 'import "./a.js";', "c.js": 'import "./a.js";'}
    )
    stats = hotspots(value)
    assert ["a.js", "b.js"] in stats.cycles
    assert stats.fan_in["a.js"] == 2
    result = impact(value, {"a.js"})
    assert set(result.direct) == {"b.js", "c.js"} and result.indirect == []
    view = neighborhood(value, focus_path="a.js", limit=2)
    assert len(view.nodes) <= 2 and view.truncated and view.total_nodes == len(value.nodes)


def test_graph_identity_is_deterministic_and_snapshot_bound():
    sources = {"a.js": "export function pay(){}"}
    first = graph(sources)
    assert graph(sources) == first
    second = build_graph(REPO, "b" * 40, sources, parse_javascript)
    assert first.nodes[0].id != second.nodes[0].id


def test_js_parameters_do_not_invent_imported_calls():
    value = graph(
        {
            "payment.js": "export function pay(){}",
            "app.js": 'import {pay} from "./payment"; function run(pay){return pay();}',
        }
    )
    assert not any(edge.kind == "calls" for edge in value.edges)
    assert any(item.reason == "shadowed_call" for item in value.unresolved)


def test_arrow_parameters_do_not_invent_imported_calls():
    value = graph(
        {
            "payment.js": "export function pay(){}",
            "app.js": 'import {pay} from "./payment"; const run=(pay)=>pay();',
        }
    )
    assert not any(edge.kind == "calls" for edge in value.edges)


def test_commonjs_object_exports_support_literal_static_calls():
    value = graph(
        {
            "payment.js": "function pay(){}; module.exports={pay};",
            "app.js": 'const payment=require("./payment"); function run(){return payment.pay();}',
        }
    )
    assert any(edge.kind == "calls" and edge.target_path == "payment.js" for edge in value.edges)
