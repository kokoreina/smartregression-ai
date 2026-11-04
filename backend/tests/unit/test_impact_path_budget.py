import pytest
from test_analysis_workflow import Source, run
from test_evidence_resolution import case

from smartregression.contracts.stages import GraphPayload, StageEdge
from smartregression.core.impact.potential_impact import build_potential_impact


def test_path_budget_is_global_across_component_origins_and_never_returns_truncated_success():
    bundle, _, _ = case()
    impact = build_potential_impact(bundle.identity, bundle.changes, bundle.graph, max_paths=1)
    assert len(impact.paths) == 1
    with pytest.raises(ValueError, match="^impact_path_limit$"):
        build_potential_impact(bundle.identity, bundle.changes, bundle.graph, max_paths=0)


def test_workflow_surfaces_budget_exhaustion_and_blocks_dependents(tmp_path, monkeypatch):
    import smartregression.application.analysis as workflow

    monkeypatch.setattr(workflow, "MAX_IMPACT_PATHS", 1)
    report = run(Source(tmp_path))  # Several origins each have b.py -> a.py.
    assert report.stages.impact.status == "failed"
    assert report.stages.impact.error_code == "impact_path_limit"
    assert report.stages.impact.data is None
    assert report.stages.evidence.reason == "dependency_failed"


def test_dense_graph_and_candidate_expansion_fail_explicitly_at_budget():
    bundle, _, _ = case()
    nodes = [*(f"n{i}.py" for i in range(13)), "a.py"]
    graph = GraphPayload(
        snapshot=bundle.identity.target,
        nodes=nodes,
        unresolved=[],
        edges=[
            StageEdge(source=a, target=b, kind="absolute_import")
            for i, a in enumerate(nodes)
            for b in nodes[i + 1 :]
        ],
    )
    with pytest.raises(ValueError, match="^impact_path_limit$"):
        build_potential_impact(bundle.identity, bundle.changes, graph)
    with pytest.raises(ValueError, match="^impact_candidate_limit$"):
        build_potential_impact(bundle.identity, bundle.changes, bundle.graph, max_candidates=1)
