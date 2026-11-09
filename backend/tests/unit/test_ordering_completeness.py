"""ADR 0004: empty observations are not proof of an incomplete graph."""

import pytest
from test_analysis_workflow import Source, run

from smartregression.contracts.models import ChangedComponent
from smartregression.core.impact.review_ordering import (
    order_for_review,
    order_from_impact_payload,
    order_from_stage_changes,
)


@pytest.mark.parametrize("empty", [False, True])
def test_ordering_entrypoints_do_not_infer_partial_from_empty_edges(tmp_path, empty):
    before, after = ({}, {}) if empty else ({"a.py": b"x=1\n"}, {"a.py": b"x=2\n"})
    report = run(Source(tmp_path, before, after))
    stages = report.stages
    orders = (
        order_for_review(
            [] if empty else [ChangedComponent(path="a.py", change="modified")], [], []
        ),
        order_from_stage_changes(stages.changes.data, stages.graph.data),
        order_from_impact_payload(stages.impact.data, graph=stages.graph.data),
    )
    for order in orders:
        assert "partial_graph" not in order.limitations
    assert stages.graph.status == stages.review_ordering.status == "completed"


def test_explicit_partial_graph_remains_even_without_edges():
    order = order_for_review([], [], ["partial_graph", "source_limit"])
    assert {"partial_graph", "source_limit"} <= set(order.limitations)
