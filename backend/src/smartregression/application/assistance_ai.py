"""Explicit scoped assistance; metadata by default, source only in approved ranges.

The immutable context hash and evidence metadata are retained; source-bearing
provider input stays in memory and is never persisted as a prompt.
"""

import hashlib
import json

from smartregression.application.auth import AuthFailure
from smartregression.contracts.repository import NarrativeResult
from smartregression.core.explorer.assistance import reading_guide, search_features
from smartregression.core.explorer.graph import digest
from smartregression.core.git.snapshots import validate_snapshot_paths
from smartregression.core.retrieval.exclusions import contains_recognized_secret


class AssistanceAiService:
    def __init__(self, store, explorer, scenarios, explain):
        self.store, self.explorer, self.scenarios, self.explain = (
            store,
            explorer,
            scenarios,
            explain,
        )

    def context(self, owner, project, body):
        snapshot, sources = self.explorer.read(owner, project, body.commit)
        graph = snapshot.graph
        if body.path:
            try:
                validate_snapshot_paths([body.path])
            except ValueError:
                raise AuthFailure("invalid_source_path", 422) from None
        paths = set()
        observations = []
        additional = {}
        omitted = 0
        seen = set()

        def observe(proof, kind, **facts):
            nonlocal omitted
            item = {
                "id": proof.id,
                "path": proof.path,
                "commit": proof.commit,
                "kind": kind,
                "line_start": proof.line_start,
                "line_end": proof.line_end,
                **facts,
            }
            if item["id"] in seen:
                return
            seen.add(item["id"])
            if len(observations) >= 24:
                omitted += 1
            else:
                observations.append(item)

        if body.action == "reading_guide":
            guide = reading_guide(graph, sources)
            for step in guide.steps:
                paths.add(step.path)
                observe(
                    step.evidence,
                    "reading_step",
                    category=step.category,
                    target_path=step.path,
                    reason=step.reason,
                )
            additional = {
                "entrypoint_status": guide.entrypoint_status,
                "limitations": guide.limitations,
            }
        elif body.action == "search":
            try:
                found = search_features(graph, sources, body.question, 10)
            except ValueError:
                raise AuthFailure("invalid_search_query", 422) from None
            for item in found.items:
                paths.add(item.path)
                observe(
                    item.evidence,
                    "lexical_match",
                    symbol=item.symbol,
                    matched_terms=item.matched_terms,
                )
            additional = {"search_status": found.status, "limitations": found.limitations}
        elif body.action in {"file", "folder", "hypothesis"}:
            if not body.path:
                raise AuthFailure("source_not_available", 404)
            if body.action == "folder":
                paths = {p for p in sources if p.startswith(body.path.rstrip("/") + "/")}
                if not paths:
                    raise AuthFailure("source_not_available", 404)
                all_paths = sorted(paths)
                paths = set(all_paths[:8])
                additional = {
                    "included_files": sorted(paths),
                    "omitted_file_count": len(all_paths) - len(paths),
                }
            else:
                if body.path not in sources:
                    raise AuthFailure("source_not_available", 404)
                paths = {body.path}
            if body.action == "hypothesis":
                if body.scenario_id is None:
                    raise AuthFailure("scenario_required", 422)
                scenario = self.scenarios.store.get(owner, project, str(body.scenario_id))
                if (
                    scenario.baseline != body.commit
                    or scenario.path != body.path
                    or scenario.mode != "description"
                ):
                    raise AuthFailure("scenario_context_mismatch", 409)
                if contains_recognized_secret(scenario.input):
                    raise AuthFailure("sensitive_question", 422)
                additional = {
                    "hypothesis": scenario.input,
                    "interpretation": (
                        "Unverified user intention, not static facts; no static percentage."
                    ),
                }
            for node in graph.nodes:
                if node.path not in paths:
                    continue
                if node.evidence:
                    observe(node.evidence, "symbol", symbol=node.symbol, node_kind=node.kind)
            for edge in graph.edges:
                if edge.source_path in paths and edge.kind != "contains":
                    observe(edge.evidence, edge.kind, target_path=edge.target_path)
            for path in sorted(paths):
                observations.append(
                    {
                        "id": digest(graph.repository_id, graph.commit, "assist-file/1", path),
                        "path": path,
                        "commit": graph.commit,
                        "kind": "file_metadata",
                        "line_start": None,
                        "line_end": None,
                    }
                )
        else:
            raise AuthFailure("invalid_ai_action", 422)
        observations.sort(key=lambda o: (o["kind"] != "file_metadata", o["path"], o["id"]))
        additional["coverage_status"] = graph.coverage.status
        additional["unparsed_file_count"] = len(graph.coverage.unparsed_files)
        additional["unresolved_relation_count"] = len(graph.unresolved)
        additional["omitted_observation_count"] = omitted
        if not observations:
            raise AuthFailure("no_evidence", 422)
        excerpts = []
        size = 0
        for selected in body.excerpts:
            if selected.path not in paths:
                raise AuthFailure("excerpt_scope_mismatch", 422)
            value = self.explorer.source(
                owner, project, body.commit, selected.path, selected.start, selected.end
            )
            size += len(value.content.encode())
            if size > 20480:
                raise AuthFailure("excerpt_limit", 422)
            excerpts.append(value.model_dump())
        context = {
            "repository": graph.repository_id,
            "commit": graph.commit,
            "config_digest": graph.config_digest,
            "action": body.action,
            "question": body.question,
            "files": sorted(paths),
            "observations": observations,
            "context": additional,
            "excerpts": excerpts,
            "interpretation": (
                "Potential static relationships, not executed tests or proven failures."
            ),
        }
        packed = json.dumps(context, sort_keys=True, ensure_ascii=True)
        while len(packed.encode()) > 28000 and len(observations) > 1:
            observations.pop()
            additional["omitted_observation_count"] += 1
            packed = json.dumps(context, sort_keys=True, ensure_ascii=True)
        if len(packed.encode()) > 28000:
            raise AuthFailure("ai_context_limit", 422)
        context_hash = hashlib.sha256(packed.encode()).hexdigest()
        scope_key = (
            body.commit + ":" + (str(body.scenario_id) if body.scenario_id else body.path or "")
        )
        provenance = {
            "repository_id": graph.repository_id,
            "commit": graph.commit,
            "config_digest": graph.config_digest,
            "action": body.action,
            "path": body.path,
            "scenario_id": str(body.scenario_id) if body.scenario_id else None,
            "observations": observations,
            "excerpt_ranges": [r.model_dump() for r in body.excerpts],
            "context_hash": context_hash,
        }
        return context, {
            "key": scope_key,
            "hash": context_hash,
            "provenance": provenance,
            "commit": graph.commit,
            "config": graph.config_digest,
        }

    def create(self, owner, project, body):
        if not body.allow_metadata_egress:
            raise AuthFailure("metadata_egress_consent_required", 422)
        if body.excerpts and not body.allow_excerpt_egress:
            raise AuthFailure("excerpt_egress_consent_required", 422)
        if contains_recognized_secret(body.question):
            raise AuthFailure("sensitive_question", 422)
        context, scope = self.context(owner, project, body)
        result = self.store.reserve(owner, project, None, body, scope["hash"], scope=scope)
        return (*result, context)

    def execute(self, owner, identity, batch, campaign, context):
        if not self.store.start(owner, identity):
            return
        try:
            result = self.explain(context, identity, batch, campaign)
        except Exception:
            result = NarrativeResult(status="failed", error_code="provider_configuration")
        self.store.finish(owner, identity, result)
