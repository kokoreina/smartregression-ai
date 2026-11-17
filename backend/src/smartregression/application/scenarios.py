"""Immutable hypothetical changes over an authorized cached baseline."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from smartregression.application.auth import AuthFailure
from smartregression.application.explorer import ExplorerService, source_allowed
from smartregression.contracts.repository import NarrativeResult
from smartregression.contracts.scenarios import (
    Scenario,
    ScenarioComparison,
    ScenarioCreate,
    ScenarioView,
    ScenarioViewPage,
)
from smartregression.core.explorer.graph import build_graph, impact
from smartregression.core.explorer.scenarios import compare_graphs, overlay
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class ScenarioStore(Protocol):
    def save(self, owner: str, project: str, key: str, value: Scenario) -> Scenario: ...
    def get(self, owner: str, project: str, identity: str) -> Scenario: ...
    def list(self, owner: str, project: str, cursor: str | None, limit: int): ...


def scenario_view(value: Scenario) -> ScenarioView:
    delta = value.delta
    data = value.model_dump(exclude={"graph", "delta", "input", "narrative", "schema_version"})
    return ScenarioView(
        **data,
        added_symbols=sorted({n.symbol for n in delta.added_nodes if n.symbol}) if delta else [],
        removed_symbols=sorted({n.symbol for n in delta.removed_nodes if n.symbol})
        if delta
        else [],
        added_node_count=delta.total_added_nodes if delta else None,
        removed_node_count=delta.total_removed_nodes if delta else None,
        added_edge_count=delta.total_added_edges if delta else None,
        removed_edge_count=delta.total_removed_edges if delta else None,
    )


class ScenarioService:
    def __init__(self, store: ScenarioStore, explorer: ExplorerService):
        self.store, self.explorer = store, explorer

    def create(self, owner: str, project: str, body: ScenarioCreate) -> Scenario:
        current = self.explorer.store.project(owner, project)
        if current.archived:
            raise AuthFailure("project_archived", 409)
        snapshot, sources = self.explorer.read(owner, project, body.baseline)
        if body.path not in sources or not body.path.endswith((".py", ".js")):
            raise AuthFailure("existing_supported_file_required", 422)
        if contains_recognized_secret(body.input):
            raise AuthFailure("sensitive_input", 422)
        digest = hashlib.sha256(
            json.dumps(
                body.model_dump(exclude={"idempotency_key"})
                | {"config": snapshot.graph.config_digest},
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        hypothetical = body.mode == "description"
        graph = delta = summary = None
        limitations = ["Proposed change only; the repository has not been modified or executed."]
        if not hypothetical:
            try:
                changed = overlay(
                    sources,
                    body.path,
                    **({"content": body.input} if body.mode == "code" else {"patch": body.input}),
                )
                if not source_allowed(body.path, changed[body.path].encode()):
                    raise ValueError("source_policy_rejected")
                graph = build_graph(
                    snapshot.graph.repository_id,
                    body.baseline,
                    changed,
                    self.explorer.parse_javascript,
                    overlay_identity=(body.path, digest),
                )
                delta = compare_graphs(snapshot.graph, graph)
                summary = impact(graph, {body.path})
            except ValueError:
                raise AuthFailure("invalid_overlay", 422) from None
        else:
            limitations.extend(
                [
                    "Natural-language input is a hypothesis, not observed code.",
                    "No static impact percentage can be inferred from this description.",
                    "Use an explicit AI request for interpretation; saving does not call Gemini.",
                ]
            )
        value = Scenario(
            id=uuid4(),
            project_id=project,
            baseline=body.baseline,
            config_digest=snapshot.graph.config_digest,
            input_digest=digest,
            title=body.title,
            path=body.path,
            mode=body.mode,
            input=body.input,
            created_at=datetime.now(UTC),
            analysis_kind="hypothesis" if hypothetical else "static_overlay",
            graph=graph,
            delta=delta,
            impact=summary,
            narrative=NarrativeResult(status="not_run", reason="user_disabled_llm"),
            limitations=limitations,
        )
        return self.store.save(owner, project, body.idempotency_key, value)

    def list(
        self, owner: str, project: str, cursor: str | None = None, limit: int = 25
    ) -> ScenarioViewPage:
        items, next_cursor = self.store.list(owner, project, cursor, limit)
        return ScenarioViewPage(
            items=[scenario_view(item) for item in items], next_cursor=next_cursor
        )

    def compare(self, owner: str, project: str, left: str, right: str) -> ScenarioComparison:
        a = self.store.get(owner, project, left)
        b = self.store.get(owner, project, right)
        if (a.baseline, a.config_digest, a.analysis_kind) != (
            b.baseline,
            b.config_digest,
            b.analysis_kind,
        ):
            raise AuthFailure("scenario_baseline_mismatch", 409)
        if a.analysis_kind == "hypothesis":
            return ScenarioComparison(
                left=a.id,
                right=b.id,
                baseline=a.baseline,
                config_digest=a.config_digest,
                added_affected=[],
                removed_affected=[],
                retained_affected=[],
                graph_delta=None,
                comparison_kind="hypotheses",
                unresolved_left=None,
                unresolved_right=None,
            )
        if not a.graph or not b.graph or not a.impact or not b.impact:
            raise AuthFailure("scenario_not_ready", 409)
        x = set(a.impact.direct + a.impact.indirect)
        y = set(b.impact.direct + b.impact.indirect)
        return ScenarioComparison(
            left=a.id,
            right=b.id,
            baseline=a.baseline,
            config_digest=a.config_digest,
            added_affected=sorted(y - x),
            removed_affected=sorted(x - y),
            retained_affected=sorted(x & y),
            graph_delta=compare_graphs(a.graph, b.graph),
            unresolved_left=len(a.graph.unresolved),
            unresolved_right=len(b.graph.unresolved),
        )

    def versions(self, owner: str, project: str, base: str, target: str):
        a = self.explorer.read(owner, project, base)[0].graph
        b = self.explorer.read(owner, project, target)[0].graph
        return compare_graphs(a, b)
