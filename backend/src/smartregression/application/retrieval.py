"""P5 workflow boundary: acquired snapshots -> verified committed index -> ranked context."""

from time import monotonic
from typing import Protocol

from smartregression.application.run_store import RunStorageError
from smartregression.contracts.stages import (
    ChangePayload,
    ImpactPayload,
    RetrievalPayload,
    StageIssue,
    StageResult,
)
from smartregression.core.git.snapshots import FrozenSnapshot, SnapshotPair
from smartregression.core.retrieval.lexical import (
    LexicalConfig,
    LexicalPlan,
    query_for_changes,
    search_lexical,
)


class RetrievalIndexStore(Protocol):
    """Trusted adapter verifies sources, artifacts and committed ready SQL state."""

    def ensure(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan: ...

    def load(self, snapshot: FrozenSnapshot, config: LexicalConfig) -> LexicalPlan | None: ...


_SAFE_ERRORS = frozenset(
    {
        "lexical_build_timeout",
        "lexical_query_timeout",
        "lexical_line_limit",
        "lexical_index_limit",
        "lexical_manifest_limit",
        "lexical_query_limit",
        "python_parse_failed",
        "source_limit",
        "snapshot_mismatch",
        "stale_index",
    }
)


def retrieve_context(
    store: RetrievalIndexStore,
    pair: SnapshotPair,
    *,
    changes: StageResult[ChangePayload],
    impact: StageResult[ImpactPayload],
    config: LexicalConfig,
) -> StageResult[RetrievalPayload]:
    if changes.data is None or impact.data is None:
        return StageResult(status="not_run", reason="dependency_failed")
    deleted = [c for c in changes.data.components if c.change == "deleted"]
    requests = [(pair.target, changes.data, impact.data)]
    if deleted and pair.base != pair.target:
        # This is only the internal relevance projection for deleted base context;
        # the canonical changed records remain deleted and retain base locations.
        base_changes = ChangePayload(
            components=[
                c.model_copy(update={"change": "modified", "target_location": c.base_location})
                for c in deleted
            ],
            files=[f for f in changes.data.files if f.path in {c.path for c in deleted}],
        )
        requests.append((pair.base, base_changes, None))
    sources, candidates, sizes, issues = [], [], {}, [*changes.limitations, *impact.limitations]
    try:
        for snapshot, projected, local_impact in requests:
            store.ensure(snapshot, config)
            query_started = monotonic()
            # Never trust a returned in-memory plan as evidence of committed ready.
            plan = store.load(snapshot, config)
            if plan is None:
                raise ValueError("stale_index")
            terms, limited = query_for_changes(projected, config)
            result = search_lexical(
                plan, snapshot, terms=terms, changes=projected, impact=local_impact
            )
            if monotonic() - query_started >= config.query_seconds:
                raise ValueError("lexical_query_timeout")
            issues.extend(result.limitations)
            if limited:
                issues.append(StageIssue(code="retrieval_query_limit"))
            sources.extend(result.data.sources)
            changed_paths = {c.path for c in projected.components}
            direct = (
                {c.path for c in local_impact.candidates if c.relationship == "direct"}
                if local_impact
                else set()
            )
            indirect = (
                {c.path for c in local_impact.candidates if c.relationship == "indirect"}
                if local_impact
                else set()
            )
            for item in result.data.items:
                tier = (
                    1
                    if item.path in changed_paths
                    else 2
                    if item.path in direct
                    else 3
                    if item.path in indirect
                    else 4
                )
                candidates.append(
                    (
                        tier,
                        -(item.score or 0),
                        len(sources),
                        item.path,
                        item.location.line_start,
                        item.location.line_end,
                        item.id,
                        item,
                    )
                )
                sizes[item.id] = len(
                    plan.chunks_by_range[
                        (item.path, item.location.line_start, item.location.line_end)
                    ].source.content
                )
        items, total = [], 0
        for *_, item in sorted(candidates, key=lambda value: value[:-1]):
            if len(items) >= config.context_chunks or total + sizes[item.id] > config.context_bytes:
                issues.append(StageIssue(code="retrieval_context_limit"))
                break
            items.append(item.model_copy(update={"rank": len(items) + 1}))
            total += sizes[item.id]
        unique_issues = {(i.code, i.path): i for i in issues}
        return StageResult(
            status="partial" if issues else "completed",
            data=RetrievalPayload(sources=sources, items=items),
            limitations=list(unique_issues.values()),
        )
    except RunStorageError as exc:
        return StageResult(
            status="failed",
            error_code=(exc.code if exc.code in _SAFE_ERRORS else "retrieval_storage_failed"),
        )
    except (ValueError, OSError, RecursionError) as exc:
        code = str(exc) if str(exc) in _SAFE_ERRORS else "retrieval_failed"
        return StageResult(status="failed", error_code=code)
