import hashlib
from dataclasses import replace

import pytest

from smartregression.application.evidence import explain_impact, inspect_bundle
from smartregression.application.evidence_store import prepare_evidence
from smartregression.application.stage_conversion import graph_result, identity_from_snapshots
from smartregression.contracts.stages import (
    ChangePayload,
    EvidenceBundle,
    FileCoverage,
    SourceLocation,
    StageComponent,
)
from smartregression.core.evidence.resolution import resolve_source
from smartregression.core.git.snapshots import SnapshotPair, TreeEntry, freeze_snapshot
from smartregression.core.impact.dependency_graph import build_dependency_graph
from smartregression.core.impact.potential_impact import build_potential_impact


def frozen(commit, sources):
    entries, contents = [], []
    for path, raw in sorted(sources.items()):
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        entries.append(TreeEntry(path, "100644", oid, len(raw)))
        contents.append(raw)
    return freeze_snapshot("fixture", commit * 40, tuple(entries), tuple(contents))


def case(*, newline="\n", renamed=False, deleted=False):
    old = {"a.py": ("def f():" + newline + "    return 'é'" + newline).encode()}
    new_path = "renamed.py" if renamed else "a.py"
    after = (
        {}
        if deleted
        else {
            new_path: ("def f():" + newline + "    return 'changed'" + newline).encode(),
            "b.py": ("import " + new_path[:-3] + newline).encode(),
        }
    )
    pair = SnapshotPair(frozen("a", old), frozen("b", after), "owned-fixture")
    identity = identity_from_snapshots(pair, run_id="evidence-run")
    location = SourceLocation(line_start=1, line_end=2)
    component = StageComponent(
        id="f-change",
        path="a.py" if deleted else new_path,
        previous_path="a.py" if renamed else None,
        kind="function",
        symbol="f",
        change="deleted" if deleted else "renamed" if renamed else "modified",
        base_location=location,
        target_location=None if deleted else location,
        reason="content_changed",
    )
    changes = ChangePayload(
        components=[component],
        files=[FileCoverage(path=component.path, status="completed", limitations=[])],
    )
    side = identity.base if deleted else identity.target
    sources = old if deleted else after
    graph = graph_result(
        build_dependency_graph(
            repository="fixture",
            revision=side.commit,
            sources={path: raw.decode() for path, raw in sources.items()},
        ),
        side,
    ).data
    impact = build_potential_impact(identity, changes, graph)
    explained, evidence = explain_impact(identity, changes, graph, impact, pair)
    return (
        EvidenceBundle(
            identity=identity,
            changes=changes,
            graph=graph,
            impact=explained,
            evidence=evidence.data,
        ),
        pair,
        evidence,
    )


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_actual_changed_and_direct_evidence_is_verified_and_deterministic(newline):
    bundle, pair, stage = case(newline=newline)
    assert stage.status == "completed"
    assert bundle.evidence.items
    assert all(
        e.resolution == "resolved" and e.support == "supported" for e in bundle.evidence.items
    )
    assert any("Static import" in c.explanation for c in bundle.impact.candidates)
    before = prepare_evidence(bundle)
    assert inspect_bundle(bundle, pair) == stage
    assert prepare_evidence(bundle) == before
    assert case(newline=newline)[0] == bundle


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("path", "missing.py", "missing"),
        ("excerpt", "wrong text", "mismatched"),
        ("symbol", "other", "mismatched"),
        ("location", SourceLocation(line_start=999, line_end=1000), "missing"),
    ],
)
def test_untrusted_saved_claims_are_rechecked_without_mutation(field, value, expected):
    bundle, pair, _ = case()
    original = bundle.evidence.items[0]
    bundle.evidence.items[0] = original.model_copy(update={field: value})
    before = prepare_evidence(bundle)
    result = inspect_bundle(bundle, pair)
    assert result.status == "partial"
    checked = next(item for item in result.data.items if item.id == original.id)
    assert checked.resolution == expected and checked.support == "unverified"
    assert prepare_evidence(bundle) == before


def test_arbitrary_explanation_does_not_become_supported_from_a_valid_source():
    bundle, pair, _ = case()
    bundle.impact.candidates[0] = bundle.impact.candidates[0].model_copy(
        update={"explanation": "This proves a security vulnerability and a certain fault."}
    )
    result = inspect_bundle(bundle, pair)
    assert result.status == "partial"
    assert any(e.resolution == "resolved" and e.support == "unverified" for e in result.data.items)


@pytest.mark.parametrize("renamed,deleted", [(True, False), (False, True)])
def test_base_evidence_for_renamed_or_deleted_symbol(renamed, deleted):
    bundle, _, result = case(renamed=renamed, deleted=deleted)
    assert result.status == "completed"
    assert any(
        item.snapshot == bundle.identity.base and item.path == "a.py"
        for item in bundle.evidence.items
    )


def test_tampered_or_foreign_snapshot_is_not_used():
    bundle, pair, _ = case()
    tampered = replace(pair.target, contents=(b"tampered", *pair.target.contents[1:]))
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        inspect_bundle(bundle, replace(pair, target=tampered))
    with pytest.raises(ValueError, match="evidence_snapshot_identity_mismatch"):
        inspect_bundle(bundle, replace(pair, target=frozen("c", {})))


def test_resolved_but_unchanged_origin_does_not_support_changed_claim():
    bundle, pair, _ = case()
    # Rebind a valid pair whose base and target contents are identical; no hash forgery.
    identical = frozen(
        "a",
        {
            f.path: raw
            for f, raw in zip(pair.target.manifest.files, pair.target.contents, strict=True)
        },
    )
    same_pair = replace(pair, base=identical)
    identity = identity_from_snapshots(same_pair, run_id=bundle.identity.run_id)
    for i, item in enumerate(bundle.evidence.items):
        if item.snapshot == bundle.identity.base:
            bundle.evidence.items[i] = item.model_copy(
                update={"snapshot": identity.base, "excerpt": None}
            )
    changed = bundle.model_copy(update={"identity": identity})
    _, result = explain_impact(identity, changed.changes, changed.graph, changed.impact, same_pair)
    assert result.status == "partial"
    assert any(
        item.resolution == "resolved" and item.support == "unsupported"
        for item in result.data.items
    )


def test_missing_witnesses_cannot_report_completed_inspection():
    bundle, pair, _ = case()
    bundle.evidence.items.clear()
    for i, candidate in enumerate(bundle.impact.candidates):
        bundle.impact.candidates[i] = candidate.model_copy(update={"evidence_ids": []})
    result = inspect_bundle(bundle, pair)
    assert result.status == "partial"
    assert any(issue.code == "evidence_witness_missing" for issue in result.limitations)


@pytest.mark.parametrize(
    "raw", [b"\xff", b"x\0y", b"x" * 256001], ids=["encoding", "binary", "limit"]
)
def test_unsupported_source_is_explicit(raw):
    bundle, _, _ = case()
    result = resolve_source(bundle.evidence.items[0], raw)
    assert result.resolution == "unverified" and result.support == "unverified"
    assert result.verification_reason == "evidence_source_unsupported"


def test_graph_edge_kind_is_rederived_from_source_not_trusted():
    bundle, pair, _ = case()
    graph = bundle.graph.model_copy(
        update={
            "edges": [
                edge.model_copy(update={"kind": "invented_dependency"})
                for edge in bundle.graph.edges
            ]
        }
    )
    _, result = explain_impact(bundle.identity, bundle.changes, graph, bundle.impact, pair)
    assert result.status == "partial"
    assert any(item.support == "unsupported" for item in result.data.items)
