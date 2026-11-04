"""Tests for review_ordering.py — Task 2.07.

Oracle values are derived manually from fixture contents, never copied from code output.
All edges are (importer, importee) pairs — importer depends on importee.
No fault labels, no confidence scores, no test selection.
"""

from smartregression.contracts.models import ChangedComponent
from smartregression.core.impact.review_ordering import (
    RULE_VERSION,
    ReviewOrder,
    order_for_review,
)

# ---------------------------------------------------------------------------
# Shared fixture factories
# ---------------------------------------------------------------------------


def _comp(
    path: str,
    change: str = "modified",
    symbol: str | None = None,
    previous_path: str | None = None,
) -> ChangedComponent:
    return ChangedComponent(
        path=path,
        symbol=symbol,
        change=change,  # type: ignore[arg-type]
        previous_path=previous_path,
    )


# ---------------------------------------------------------------------------
# Group 1: Empty and trivial inputs
# ---------------------------------------------------------------------------


class TestEmptyInputs:
    """Empty or no-op inputs must not crash and return correct empty structures."""

    def test_no_changed_no_edges_returns_empty_candidates(self) -> None:
        result = order_for_review(changed=[], edges=[], limitations=[])
        assert result.candidates == ()

    def test_no_changed_no_edges_adds_partial_graph_limitation(self) -> None:
        # No edges → graph is partial; limitation must be recorded.
        result = order_for_review(changed=[], edges=[], limitations=[])
        assert "partial_graph" in result.limitations

    def test_no_changed_with_edges_returns_empty_candidates(self) -> None:
        # Edges exist but no changed component → nothing to order.
        result = order_for_review(
            changed=[],
            edges=[("b.py", "a.py")],
            limitations=[],
        )
        assert result.candidates == ()

    def test_rule_version_always_present(self) -> None:
        result = order_for_review(changed=[], edges=[], limitations=[])
        assert result.rule_version == RULE_VERSION

    def test_return_type_is_review_order(self) -> None:
        result = order_for_review(changed=[], edges=[], limitations=[])
        assert isinstance(result, ReviewOrder)


# ---------------------------------------------------------------------------
# Group 2: Tier 1 — changed components only (no graph)
# ---------------------------------------------------------------------------


class TestTierOne:
    """Changed components become Tier-1 candidates."""

    def test_single_changed_file_is_tier1(self) -> None:
        # Fixture: one modified file, no edges.
        # Oracle: one Tier-1 candidate for "auth.py", no Tier-2 or Tier-3.
        result = order_for_review(
            changed=[_comp("auth.py")],
            edges=[],
            limitations=[],
        )
        assert len(result.candidates) == 1
        c = result.candidates[0]
        assert c.path == "auth.py"
        assert c.tier == 1
        assert c.symbol is None

    def test_changed_with_symbol_preserved_in_tier1(self) -> None:
        # Fixture: file "storage.py" with symbol "Storage.save" modified.
        # Oracle: candidate has symbol = "Storage.save".
        result = order_for_review(
            changed=[_comp("storage.py", symbol="Storage.save")],
            edges=[],
            limitations=[],
        )
        assert result.candidates[0].symbol == "Storage.save"
        assert result.candidates[0].tier == 1

    def test_multiple_changed_files_all_tier1(self) -> None:
        # Fixture: two changed files.
        # Oracle: two Tier-1 candidates, no Tier-2.
        result = order_for_review(
            changed=[_comp("a.py"), _comp("b.py")],
            edges=[],
            limitations=[],
        )
        tiers = [c.tier for c in result.candidates]
        assert tiers == [1, 1]

    def test_tier1_sorted_alphabetically_by_path(self) -> None:
        # Fixture: changed files in reverse-alpha order supplied.
        # Oracle: candidates sorted by path ascending.
        result = order_for_review(
            changed=[_comp("z.py"), _comp("a.py"), _comp("m.py")],
            edges=[],
            limitations=[],
        )
        paths = [c.path for c in result.candidates]
        assert paths == ["a.py", "m.py", "z.py"]

    def test_tier1_with_add_change_type(self) -> None:
        result = order_for_review(
            changed=[_comp("new_module.py", change="added")],
            edges=[],
            limitations=[],
        )
        assert result.candidates[0].tier == 1
        assert "added" in result.candidates[0].reason

    def test_tier1_with_deleted_change_type(self) -> None:
        result = order_for_review(
            changed=[_comp("old_module.py", change="deleted")],
            edges=[],
            limitations=[],
        )
        assert result.candidates[0].tier == 1

    def test_tier1_with_renamed_change_type(self) -> None:
        result = order_for_review(
            changed=[_comp("new_name.py", change="renamed", previous_path="old_name.py")],
            edges=[],
            limitations=[],
        )
        assert result.candidates[0].tier == 1


# ---------------------------------------------------------------------------
# Group 3: Tier 2 — direct dependents
# ---------------------------------------------------------------------------


class TestTierTwo:
    """Direct importers of Tier-1 paths become Tier-2 candidates."""

    def test_direct_importer_is_tier2(self) -> None:
        # Fixture: "core.py" is changed; "api.py" imports "core.py".
        # Edge: ("api.py", "core.py") means api.py depends on core.py.
        # Oracle: core.py → Tier 1; api.py → Tier 2.
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[("api.py", "core.py")],
            limitations=[],
        )
        paths_by_tier = {c.path: c.tier for c in result.candidates}
        assert paths_by_tier["core.py"] == 1
        assert paths_by_tier["api.py"] == 2

    def test_tier2_symbol_is_none_file_level(self) -> None:
        # Tier-2 candidates are file-level (no symbol info from edges alone).
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[("api.py", "core.py")],
            limitations=[],
        )
        tier2 = [c for c in result.candidates if c.tier == 2]
        assert all(c.symbol is None for c in tier2)

    def test_multiple_direct_importers_all_tier2(self) -> None:
        # Fixture: "lib.py" changed; "svc.py" and "cli.py" both import it.
        # Oracle: lib.py → Tier 1; svc.py, cli.py → Tier 2; sorted alpha.
        result = order_for_review(
            changed=[_comp("lib.py")],
            edges=[("svc.py", "lib.py"), ("cli.py", "lib.py")],
            limitations=[],
        )
        tier2_paths = sorted(c.path for c in result.candidates if c.tier == 2)
        assert tier2_paths == ["cli.py", "svc.py"]

    def test_tier2_sorted_alphabetically(self) -> None:
        result = order_for_review(
            changed=[_comp("lib.py")],
            edges=[("z_svc.py", "lib.py"), ("a_svc.py", "lib.py"), ("m_svc.py", "lib.py")],
            limitations=[],
        )
        tier2_paths = [c.path for c in result.candidates if c.tier == 2]
        assert tier2_paths == ["a_svc.py", "m_svc.py", "z_svc.py"]

    def test_edge_pointing_to_non_tier1_is_ignored_for_tier2(self) -> None:
        # "irrelevant.py" → "unrelated.py"; "unrelated.py" not in changed.
        # Only core.py → Tier 1; api.py (imports core) → Tier 2.
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[
                ("api.py", "core.py"),
                ("irrelevant.py", "unrelated.py"),
            ],
            limitations=[],
        )
        paths = {c.path for c in result.candidates}
        assert "irrelevant.py" not in paths
        assert "unrelated.py" not in paths


# ---------------------------------------------------------------------------
# Group 4: Tier 3 — indirect (transitive) dependents
# ---------------------------------------------------------------------------


class TestTierThree:
    """Transitive importers beyond direct deps become Tier-3 candidates."""

    def test_two_hop_importer_is_tier3(self) -> None:
        # Fixture: core.py changed; api.py → core.py (direct); web.py → api.py (indirect).
        # Oracle: core.py=1, api.py=2, web.py=3.
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[("api.py", "core.py"), ("web.py", "api.py")],
            limitations=[],
        )
        paths_by_tier = {c.path: c.tier for c in result.candidates}
        assert paths_by_tier["core.py"] == 1
        assert paths_by_tier["api.py"] == 2
        assert paths_by_tier["web.py"] == 3

    def test_three_hop_chain_is_tier3(self) -> None:
        # core.py → Tier 1; mid.py → Tier 2; far.py → Tier 3; distant.py → Tier 3.
        # Edges: mid imports core; far imports mid; distant imports far.
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[
                ("mid.py", "core.py"),
                ("far.py", "mid.py"),
                ("distant.py", "far.py"),
            ],
            limitations=[],
        )
        paths_by_tier = {c.path: c.tier for c in result.candidates}
        assert paths_by_tier["mid.py"] == 2
        assert paths_by_tier["far.py"] == 3
        assert paths_by_tier["distant.py"] == 3

    def test_tier3_sorted_alphabetically_within_tier(self) -> None:
        # api.py imports core.py; b_web.py, a_web.py, m_web.py all import api.py
        # Oracle Tier-3 order: a_web.py, b_web.py, m_web.py
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[
                ("api.py", "core.py"),
                ("b_web.py", "api.py"),
                ("a_web.py", "api.py"),
                ("m_web.py", "api.py"),
            ],
            limitations=[],
        )
        tier3_paths = [c.path for c in result.candidates if c.tier == 3]
        assert tier3_paths == ["a_web.py", "b_web.py", "m_web.py"]


# ---------------------------------------------------------------------------
# Group 5: Deduplication rules
# ---------------------------------------------------------------------------


class TestDeduplication:
    """A path must appear only once, at its lowest (best) tier."""

    def test_tier1_path_not_duplicated_as_tier2(self) -> None:
        # Fixture: a.py is changed; b.py imports a.py; a.py also imports itself
        # (self-edge). a.py must remain Tier 1 only.
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py"), ("a.py", "a.py")],  # self-edge
            limitations=[],
        )
        a_entries = [c for c in result.candidates if c.path == "a.py"]
        assert len(a_entries) == 1
        assert a_entries[0].tier == 1

    def test_tier2_path_not_promoted_to_tier3(self) -> None:
        # Fixture: core.py changed; api.py imports core.py (Tier 2).
        #          web.py imports api.py (normally Tier 3).
        #          web.py also imports core.py directly (would make it Tier 2 too).
        # Oracle: web.py is Tier 2 (lower tier wins).
        result = order_for_review(
            changed=[_comp("core.py")],
            edges=[
                ("api.py", "core.py"),
                ("web.py", "api.py"),
                ("web.py", "core.py"),  # web.py also directly imports core
            ],
            limitations=[],
        )
        web_entries = [c for c in result.candidates if c.path == "web.py"]
        assert len(web_entries) == 1
        assert web_entries[0].tier == 2

    def test_changed_component_with_same_path_different_symbol_both_appear(self) -> None:
        # Two ChangedComponents with same path but different symbols are distinct entries.
        # Oracle: two Tier-1 candidates for "storage.py" (different symbols).
        result = order_for_review(
            changed=[
                _comp("storage.py", symbol="Storage.save"),
                _comp("storage.py", symbol="Storage.load"),
            ],
            edges=[],
            limitations=[],
        )
        storage_entries = [c for c in result.candidates if c.path == "storage.py"]
        assert len(storage_entries) == 2
        symbols = {c.symbol for c in storage_entries}
        assert symbols == {"Storage.save", "Storage.load"}

    def test_same_path_same_symbol_not_duplicated(self) -> None:
        # Two identical ChangedComponents → single candidate.
        result = order_for_review(
            changed=[
                _comp("util.py", symbol="helper"),
                _comp("util.py", symbol="helper"),
            ],
            edges=[],
            limitations=[],
        )
        util_entries = [c for c in result.candidates if c.path == "util.py"]
        assert len(util_entries) == 1

    def test_tier3_path_already_at_tier2_stays_tier2(self) -> None:
        # b.py imports a.py (Tier 2 from a.py); c.py imports b.py (Tier 3);
        # b.py ALSO imports itself from another edge to a.py — b stays Tier 2.
        # This verifies BFS visited set works.
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[
                ("b.py", "a.py"),
                ("c.py", "b.py"),
                ("b.py", "a.py"),  # duplicate edge — same importer
            ],
            limitations=[],
        )
        b_entries = [c for c in result.candidates if c.path == "b.py"]
        assert len(b_entries) == 1
        assert b_entries[0].tier == 2


# ---------------------------------------------------------------------------
# Group 6: Cycle handling
# ---------------------------------------------------------------------------


class TestCycleHandling:
    """Cycles in the import graph must not cause infinite loops or duplicates."""

    def test_two_node_cycle_no_infinite_loop(self) -> None:
        # a.py ↔ b.py; a.py is changed.
        # Oracle: a.py=1, b.py=2; no infinite loop, no b.py appearing in Tier 3.
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py"), ("a.py", "b.py")],
            limitations=[],
        )
        paths_by_tier = {c.path: c.tier for c in result.candidates}
        assert paths_by_tier["a.py"] == 1
        assert paths_by_tier["b.py"] == 2
        assert len(result.candidates) == 2  # no phantom Tier-3 entries

    def test_three_node_cycle_no_duplicate(self) -> None:
        # a.py → b.py → c.py → a.py (cycle); a.py is changed.
        # Oracle: a.py=1, b.py=2, c.py=3; each appears exactly once.
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py"), ("c.py", "b.py"), ("a.py", "c.py")],
            limitations=[],
        )
        paths = [c.path for c in result.candidates]
        assert len(paths) == len(set(paths)), "No duplicates"
        assert {c.path for c in result.candidates} == {"a.py", "b.py", "c.py"}


# ---------------------------------------------------------------------------
# Group 7: Stable ordering / determinism
# ---------------------------------------------------------------------------


class TestStableOrdering:
    """Output order must be stable for same inputs regardless of iteration order."""

    def test_overall_order_is_tier_then_alpha_path(self) -> None:
        # Fixture:
        #   Changed: z_changed.py, a_changed.py (Tier 1)
        #   Edges: x_dep.py → a_changed.py; b_dep.py → z_changed.py
        #   Oracle: Tier 1 sorted alpha, then Tier 2 sorted alpha.
        #   Expected order: a_changed.py(1), z_changed.py(1), b_dep.py(2), x_dep.py(2)
        result = order_for_review(
            changed=[_comp("z_changed.py"), _comp("a_changed.py")],
            edges=[("x_dep.py", "a_changed.py"), ("b_dep.py", "z_changed.py")],
            limitations=[],
        )
        paths = [c.path for c in result.candidates]
        assert paths == ["a_changed.py", "z_changed.py", "b_dep.py", "x_dep.py"]

    def test_symbol_sorts_within_same_path_and_tier(self) -> None:
        # Two Tier-1 entries for same path, different symbols.
        # Oracle: sort by symbol ascending → "A.method" before "B.method".
        result = order_for_review(
            changed=[
                _comp("mod.py", symbol="B.method"),
                _comp("mod.py", symbol="A.method"),
            ],
            edges=[],
            limitations=[],
        )
        symbols = [c.symbol for c in result.candidates if c.path == "mod.py"]
        assert symbols == ["A.method", "B.method"]

    def test_repeated_calls_same_input_same_output(self) -> None:
        changed = [_comp("a.py"), _comp("c.py"), _comp("b.py")]
        edges = [("d.py", "a.py"), ("e.py", "b.py")]
        result1 = order_for_review(changed=changed, edges=edges, limitations=[])
        result2 = order_for_review(changed=changed, edges=edges, limitations=[])
        assert result1 == result2


# ---------------------------------------------------------------------------
# Group 8: Limitations
# ---------------------------------------------------------------------------


class TestLimitations:
    """Limitations must be preserved and merged correctly."""

    def test_caller_limitations_preserved(self) -> None:
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py")],
            limitations=["relative_import_unresolved"],
        )
        assert "relative_import_unresolved" in result.limitations

    def test_partial_graph_added_when_no_edges(self) -> None:
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[],
            limitations=[],
        )
        assert "partial_graph" in result.limitations

    def test_partial_graph_not_added_when_edges_present(self) -> None:
        # At least one edge → graph is not empty → no auto partial_graph.
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py")],
            limitations=[],
        )
        assert "partial_graph" not in result.limitations

    def test_multiple_caller_limitations_all_kept(self) -> None:
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[("b.py", "a.py")],
            limitations=["star_import", "dynamic_import"],
        )
        assert "star_import" in result.limitations
        assert "dynamic_import" in result.limitations

    def test_limitations_merged_with_partial_graph(self) -> None:
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[],
            limitations=["relative_import_unresolved"],
        )
        assert "partial_graph" in result.limitations
        assert "relative_import_unresolved" in result.limitations

    def test_limitations_sorted_for_stability(self) -> None:
        result = order_for_review(
            changed=[_comp("a.py")],
            edges=[],
            limitations=["z_limit", "a_limit"],
        )
        assert list(result.limitations) == sorted(result.limitations)


# ---------------------------------------------------------------------------
# Group 9: No fault labels, no test selection
# ---------------------------------------------------------------------------


class TestNoFaultOrTestSelection:
    """Output must not contain confidence scores, fault labels, or test IDs."""

    def test_review_candidate_has_no_confidence_score(self) -> None:
        result = order_for_review(changed=[_comp("a.py")], edges=[], limitations=[])
        for cand in result.candidates:
            assert not hasattr(cand, "confidence")
            assert not hasattr(cand, "fault_probability")
            assert not hasattr(cand, "test_id")

    def test_review_order_has_no_test_selection(self) -> None:
        result = order_for_review(changed=[_comp("a.py")], edges=[], limitations=[])
        assert not hasattr(result, "selected_tests")
        assert not hasattr(result, "skipped_tests")
        assert not hasattr(result, "fault_label")

    def test_reason_field_is_string_description_only(self) -> None:
        result = order_for_review(changed=[_comp("a.py")], edges=[], limitations=[])
        for cand in result.candidates:
            assert isinstance(cand.reason, str)
            assert len(cand.reason) > 0


# ---------------------------------------------------------------------------
# Group 10: Partial graph — real-world scenario
# ---------------------------------------------------------------------------


class TestPartialGraphScenario:
    """Simulate a realistic partial graph and verify correct behaviour."""

    def test_partial_graph_tier1_still_present(self) -> None:
        # Even with no graph info, changed components must be Tier 1.
        result = order_for_review(
            changed=[_comp("payments/charge.py"), _comp("payments/refund.py")],
            edges=[],
            limitations=["relative_import_unresolved"],
        )
        tier1_paths = {c.path for c in result.candidates if c.tier == 1}
        assert "payments/charge.py" in tier1_paths
        assert "payments/refund.py" in tier1_paths

    def test_partial_graph_no_tier2_or_tier3(self) -> None:
        result = order_for_review(
            changed=[_comp("payments/charge.py")],
            edges=[],
            limitations=[],
        )
        assert all(c.tier == 1 for c in result.candidates)

    def test_partial_graph_with_known_edges_still_builds_tier2(self) -> None:
        # Some edges known, some unknown. Known edges must still produce Tier 2/3.
        # "payments/charge.py" changed; "api/checkout.py" imports it (known edge).
        # No further edges known.
        result = order_for_review(
            changed=[_comp("payments/charge.py")],
            edges=[("api/checkout.py", "payments/charge.py")],
            limitations=["relative_import_unresolved"],  # partial: some imports unknown
        )
        paths_by_tier = {c.path: c.tier for c in result.candidates}
        assert paths_by_tier["payments/charge.py"] == 1
        assert paths_by_tier["api/checkout.py"] == 2
        # partial_graph NOT auto-added because edges non-empty
        assert "partial_graph" not in result.limitations
        assert "relative_import_unresolved" in result.limitations


# ---------------------------------------------------------------------------
# Group 11: Combined scenario — ties, repeats, full pipeline
# ---------------------------------------------------------------------------


class TestFullPipelineScenario:
    """End-to-end fixture verifying ordering rule 2.07-v1 behaviour."""

    def test_full_ordering_example(self) -> None:
        """Fixture (hand-computed oracle):

        Changed:
          - "core/auth.py" (modified, no symbol)
          - "core/storage.py" (modified, symbol "Storage.save")
          - "core/storage.py" (modified, symbol "Storage.load")

        Edges (importer, importee):
          - "api/login.py"   → "core/auth.py"    (direct dep of auth)
          - "api/profile.py" → "core/auth.py"    (direct dep of auth)
          - "api/upload.py"  → "core/storage.py" (direct dep of storage)
          - "web/app.py"     → "api/login.py"    (indirect via login)
          - "web/app.py"     → "api/profile.py"  (indirect via profile, same node)

        Oracle:
          Tier 1 (alpha by path, then symbol):
            ("core/auth.py", None)
            ("core/storage.py", "Storage.load")
            ("core/storage.py", "Storage.save")
          Tier 2 (alpha):
            ("api/login.py", None)
            ("api/profile.py", None)
            ("api/upload.py", None)
          Tier 3:
            ("web/app.py", None)       — imports both login and profile (Tier-2), deduped
        """
        result = order_for_review(
            changed=[
                _comp("core/auth.py"),
                _comp("core/storage.py", symbol="Storage.save"),
                _comp("core/storage.py", symbol="Storage.load"),
            ],
            edges=[
                ("api/login.py", "core/auth.py"),
                ("api/profile.py", "core/auth.py"),
                ("api/upload.py", "core/storage.py"),
                ("web/app.py", "api/login.py"),
                ("web/app.py", "api/profile.py"),
            ],
            limitations=[],
        )

        # Tier-1: 3 entries (core/auth + two storage symbols)
        tier1 = [c for c in result.candidates if c.tier == 1]
        assert len(tier1) == 3
        tier1_keys = [(c.path, c.symbol) for c in tier1]
        assert tier1_keys == [
            ("core/auth.py", None),
            ("core/storage.py", "Storage.load"),
            ("core/storage.py", "Storage.save"),
        ]

        # Tier-2: 3 entries (login, profile, upload)
        tier2 = [c for c in result.candidates if c.tier == 2]
        assert len(tier2) == 3
        tier2_paths = [c.path for c in tier2]
        assert tier2_paths == ["api/login.py", "api/profile.py", "api/upload.py"]

        # Tier-3: 1 entry (web/app.py deduped — only appears once)
        tier3 = [c for c in result.candidates if c.tier == 3]
        assert len(tier3) == 1
        assert tier3[0].path == "web/app.py"

        # No fault fields
        for cand in result.candidates:
            assert not hasattr(cand, "confidence")

        # Limitations: none expected (edges non-empty, none passed)
        assert result.limitations == ()

        # Rule version
        assert result.rule_version == RULE_VERSION


# ---------------------------------------------------------------------------
# Group 12: Real data thin adapter (Task 2.01 & 2.04 integration)
# ---------------------------------------------------------------------------


class TestRealDataThinAdapter:
    """Kiểm chứng lớp chuyển đổi mỏng kết nối output thực tế từ

    Task 2.01 (ChangePayload) và Task 2.04 (ImpactPayload) sang ReviewOrder.
    """

    def test_order_from_impact_payload_mapping_and_distances(self) -> None:
        """Kiểm chứng:

        1. relationship 'changed' -> Tier 1, 'direct' -> Tier 2, 'indirect' -> Tier 3
        2. Khoảng cách (distance) được trích xuất từ chuỗi nodes của ImpactPath:
           - direct: distance 1
           - indirect: min distance theo số cạnh (len(nodes) - 1)
        """
        import hashlib

        from smartregression.contracts.stages import (
            ImpactCandidate,
            ImpactPath,
            ImpactPayload,
            SnapshotIdentity,
        )
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        p1 = ImpactPath(id="p1", changed_component_id="c1", nodes=["api.py", "core.py"])
        p2 = ImpactPath(id="p2", changed_component_id="c1", nodes=["web.py", "api.py", "core.py"])

        cand_core = ImpactCandidate(
            id="cand-1",
            path="core.py",
            symbol=None,
            relationship="changed",
            changed_component_id="c1",
            path_ids=[],
        )
        cand_api = ImpactCandidate(
            id="cand-2",
            path="api.py",
            symbol=None,
            relationship="direct",
            changed_component_id="c1",
            path_ids=["p1"],
        )
        cand_web = ImpactCandidate(
            id="cand-3",
            path="web.py",
            symbol=None,
            relationship="indirect",
            changed_component_id="c1",
            path_ids=["p2"],
        )

        impact = ImpactPayload(
            snapshot=snap,
            candidates=[cand_web, cand_core, cand_api],
            paths=[p1, p2],
        )

        review_order = order_from_impact_payload(impact)

        assert len(review_order.candidates) == 3
        # Tier 1: core.py (distance 0)
        assert review_order.candidates[0].path == "core.py"
        assert review_order.candidates[0].tier == 1
        assert review_order.candidates[0].distance == 0
        assert "directly changed" in review_order.candidates[0].reason

        # Tier 2: api.py (distance 1)
        assert review_order.candidates[1].path == "api.py"
        assert review_order.candidates[1].tier == 2
        assert review_order.candidates[1].distance == 1
        assert "distance 1" in review_order.candidates[1].reason

        # Tier 3: web.py (distance 2 hops: web -> api -> core)
        assert review_order.candidates[2].path == "web.py"
        assert review_order.candidates[2].tier == 3
        assert review_order.candidates[2].distance == 2
        assert "distance 2" in review_order.candidates[2].reason

    def test_order_from_impact_missing_and_broken_paths_handled(self) -> None:
        """Kiểm chứng xử lý thiếu path và tham chiếu hỏng:

        1. Khi candidate tier 3 không có path: distance là None, ghi 'distance unknown'
           và thêm limitation 'missing_impact_path'. Không bịa khoảng cách.
        2. Khi path_ids tham chiếu ID không tồn tại: thêm limitation
           'broken_impact_path_reference', không bỏ qua im lặng.
        """
        import hashlib

        from smartregression.contracts.stages import (
            ImpactCandidate,
            ImpactPayload,
            SnapshotIdentity,
        )
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        cand_broken = ImpactCandidate(
            id="c_broken",
            path="broken.py",
            symbol=None,
            relationship="indirect",
            changed_component_id="c1",
            path_ids=["non_existent_pid"],  # broken reference
        )
        cand_empty = ImpactCandidate(
            id="c_empty",
            path="empty.py",
            symbol=None,
            relationship="indirect",
            changed_component_id="c1",
            path_ids=[],  # missing path
        )

        impact = ImpactPayload(
            snapshot=snap,
            candidates=[cand_broken, cand_empty],
            paths=[],
        )

        order = order_from_impact_payload(impact)

        # Cả 2 đều có distance là None, reason ghi 'distance unknown'
        for cand in order.candidates:
            assert cand.distance is None
            assert "distance unknown" in cand.reason

        # Limitations ghi nhận rõ ràng, không bịa số và không bỏ qua im lặng
        assert "broken_impact_path_reference" in order.limitations
        assert "missing_impact_path" in order.limitations
        assert "inconsistent_impact_payload" in order.limitations

    def test_order_from_impact_structural_inference_labels(self) -> None:
        """Kiểm chứng: partial_graph chỉ đến từ unresolved; các suy luận cấu trúc

        dùng nhãn riêng 'no_dependency_edges_observed' và 'inconsistent_impact_payload'.
        """
        import hashlib

        from smartregression.contracts.stages import (
            GraphPayload,
            ImpactCandidate,
            ImpactPayload,
            SnapshotIdentity,
        )
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        impact = ImpactPayload(
            snapshot=snap,
            candidates=[
                ImpactCandidate(
                    id="c1",
                    path="core.py",
                    symbol=None,
                    relationship="changed",
                    changed_component_id="comp1",
                    path_ids=[],
                )
            ],
            paths=[],
        )

        # Graph có nodes nhưng 0 edges: suy luận cấu trúc
        empty_edge_graph = GraphPayload(
            snapshot=snap,
            nodes=["core.py", "standalone.py"],
            edges=[],
            unresolved=[],
        )

        order = order_from_impact_payload(impact, graph=empty_edge_graph)

        # Không gắn 'partial_graph' mà dùng nhãn riêng
        assert "partial_graph" not in order.limitations
        assert "no_dependency_edges_observed" in order.limitations

    def test_order_from_impact_deduplication_best_tier_wins(self) -> None:
        """Kiểm chứng deduplication khi một component xuất hiện qua nhiều relationship

        (ví dụ: vừa direct từ change 1 vừa indirect từ change 2).
        Tier thấp hơn (1 < 2 < 3) và khoảng cách ngắn nhất phải thắng.
        """
        import hashlib

        from smartregression.contracts.stages import (
            ImpactCandidate,
            ImpactPath,
            ImpactPayload,
            SnapshotIdentity,
        )
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        p_direct = ImpactPath(
            id="p_d", changed_component_id="c1", nodes=["shared.py", "origin1.py"]
        )
        p_indirect = ImpactPath(
            id="p_i", changed_component_id="c2", nodes=["shared.py", "mid.py", "origin2.py"]
        )

        # shared.py xuất hiện 2 lần: direct từ c1, indirect từ c2
        cand_direct = ImpactCandidate(
            id="c_d",
            path="shared.py",
            symbol=None,
            relationship="direct",
            changed_component_id="c1",
            path_ids=["p_d"],
        )
        cand_indirect = ImpactCandidate(
            id="c_i",
            path="shared.py",
            symbol=None,
            relationship="indirect",
            changed_component_id="c2",
            path_ids=["p_i"],
        )

        impact = ImpactPayload(
            snapshot=snap,
            candidates=[cand_indirect, cand_direct],
            paths=[p_direct, p_indirect],
        )

        review_order = order_from_impact_payload(impact)

        # shared.py chỉ xuất hiện duy nhất 1 lần ở Tier 2 (best tier)
        assert len(review_order.candidates) == 1
        cand = review_order.candidates[0]
        assert cand.path == "shared.py"
        assert cand.tier == 2
        assert "distance 1" in cand.reason

    def test_order_from_impact_limitations_reconciliation_from_graph(self) -> None:
        """Kiểm chứng tính tương thích của định nghĩa 'partial':

        Khi GraphPayload có unresolved imports (star_import, dynamic_import, v.v.),
        lớp chuyển đổi mỏng phải ghi nhận 'partial_graph' và các unresolved reasons cụ thể.
        """
        import hashlib

        from smartregression.contracts.stages import (
            GraphPayload,
            ImpactCandidate,
            ImpactPayload,
            ImportLimitation,
            SnapshotIdentity,
            StageEdge,
        )
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        impact = ImpactPayload(
            snapshot=snap,
            candidates=[
                ImpactCandidate(
                    id="c1",
                    path="core.py",
                    symbol=None,
                    relationship="changed",
                    changed_component_id="comp1",
                    path_ids=[],
                )
            ],
            paths=[],
        )

        graph = GraphPayload(
            snapshot=snap,
            nodes=["core.py", "importer.py"],
            edges=[StageEdge(source="importer.py", target="core.py", kind="absolute_import")],
            unresolved=[
                ImportLimitation(
                    source_path="importer.py",
                    reference="*",
                    kind="star_import",
                    reason="unsupported_import",
                ),
                ImportLimitation(
                    source_path="importer.py",
                    reference="missing_pkg",
                    kind="absolute_import",
                    reason="target_not_in_snapshot",
                ),
            ],
        )

        review_order = order_from_impact_payload(impact, graph=graph)

        assert "partial_graph" in review_order.limitations
        assert "unsupported_import" in review_order.limitations
        assert "target_not_in_snapshot" in review_order.limitations

    def test_order_from_stage_changes_end_to_end(self) -> None:
        """Kiểm chứng hàm order_from_stage_changes chuyển đổi ChangePayload + GraphPayload."""
        import hashlib

        from smartregression.contracts.stages import (
            ChangePayload,
            FileCoverage,
            GraphPayload,
            SnapshotIdentity,
            StageComponent,
            StageEdge,
        )
        from smartregression.core.impact.review_ordering import order_from_stage_changes

        snap = SnapshotIdentity(
            repository_id="repo-1",
            commit="a" * 40,
            snapshot_id=hashlib.sha256(b"snap").hexdigest(),
        )

        changes = ChangePayload(
            components=[
                StageComponent(
                    id="comp-1",
                    path="core/storage.py",
                    kind="method",
                    symbol="Storage.validate",
                    change="modified",
                    base_location={"line_start": 5, "line_end": 8},
                    target_location={"line_start": 5, "line_end": 10},
                    reason="content_changed",
                )
            ],
            files=[FileCoverage(path="core/storage.py", status="completed", limitations=[])],
        )

        graph = GraphPayload(
            snapshot=snap,
            nodes=["core/storage.py", "api/routes.py"],
            edges=[
                StageEdge(
                    source="api/routes.py",
                    target="core/storage.py",
                    kind="absolute_import",
                )
            ],
            unresolved=[],
        )

        review_order = order_from_stage_changes(changes, graph)

        assert len(review_order.candidates) == 2
        # Tier 1: core/storage.py with symbol Storage.validate
        assert review_order.candidates[0].path == "core/storage.py"
        assert review_order.candidates[0].symbol == "Storage.validate"
        assert review_order.candidates[0].tier == 1

        # Tier 2: api/routes.py
        assert review_order.candidates[1].path == "api/routes.py"
        assert review_order.candidates[1].tier == 2

    def test_real_integration_through_task_203_and_204_code(self) -> None:
        """Test tích hợp chạy qua code THẬT của Task 2.03 (build_dependency_graph)

        và Task 2.04 (build_potential_impact) trên fixture nhỏ: web -> api -> core.
        Thứ tự mong đợi (oracle viết tay trước):
          1. core.py: tier 1 (directly changed), distance 0
          2. api.py:  tier 2 (direct dependent), distance 1
          3. web.py:  tier 3 (indirect dependent), distance 2
        """
        import hashlib

        from smartregression.contracts.stages import (
            ChangePayload,
            FileCoverage,
            GraphPayload,
            ImportLimitation,
            RunIdentity,
            SnapshotIdentity,
            StageComponent,
            StageEdge,
        )
        from smartregression.core.impact.dependency_graph import build_dependency_graph
        from smartregression.core.impact.potential_impact import build_potential_impact
        from smartregression.core.impact.review_ordering import order_from_impact_payload

        base_sha = "1" * 40
        target_sha = "2" * 40
        run = RunIdentity(
            repository_id="repo-test",
            run_id="run-test",
            base=SnapshotIdentity(
                repository_id="repo-test",
                commit=base_sha,
                snapshot_id=hashlib.sha256(b"base").hexdigest(),
            ),
            target=SnapshotIdentity(
                repository_id="repo-test",
                commit=target_sha,
                snapshot_id=hashlib.sha256(b"target").hexdigest(),
            ),
            comparison_mode="direct_two_tree",
        )

        sources = {
            "core.py": "def add(x, y):\n    return x + y\n",
            "api.py": "import core\n\ndef handle(x, y):\n    return core.add(x, y)\n",
            "web.py": "import api\n\ndef app():\n    return api.handle(1, 2)\n",
        }

        # 1. Chạy code THẬT của Task 2.03: build_dependency_graph
        dep_graph = build_dependency_graph(
            repository="repo-test",
            revision=target_sha,
            sources=sources,
        )
        graph_payload = GraphPayload(
            snapshot=run.target,
            nodes=[n.path for n in dep_graph.nodes],
            edges=[
                StageEdge(source=e.source.path, target=e.target.path, kind=e.kind)
                for e in dep_graph.edges
            ],
            unresolved=[
                ImportLimitation(
                    source_path=u.source_path,
                    reference=u.reference,
                    kind=u.kind,
                    reason=u.reason,
                )
                for u in dep_graph.unresolved
            ],
        )

        # 2. Dựng ChangePayload: core.py bị sửa
        changes = ChangePayload(
            components=[
                StageComponent(
                    id=hashlib.sha256(b"core.py:modified").hexdigest(),
                    path="core.py",
                    kind="module",
                    change="modified",
                    base_location={"line_start": 1, "line_end": 2},
                    target_location={"line_start": 1, "line_end": 2},
                    reason="content_changed",
                )
            ],
            files=[FileCoverage(path="core.py", status="completed", limitations=[])],
        )

        # 3. Chạy code THẬT của Task 2.04: build_potential_impact
        impact_payload = build_potential_impact(run, changes, graph_payload)

        # 4. Nối qua Adapter mỏng của Task 2.07
        review_order = order_from_impact_payload(impact_payload, graph=graph_payload)

        # 5. Kiểm chứng thứ tự mong đợi (oracle định nghĩa trước):
        assert len(review_order.candidates) == 3

        # Candidate 1: core.py (tier 1, distance 0)
        c1 = review_order.candidates[0]
        assert c1.path == "core.py"
        assert c1.tier == 1
        assert c1.distance == 0
        assert "directly changed" in c1.reason

        # Candidate 2: api.py (tier 2, distance 1)
        c2 = review_order.candidates[1]
        assert c2.path == "api.py"
        assert c2.tier == 2
        assert c2.distance == 1
        assert "distance 1" in c2.reason

        # Candidate 3: web.py (tier 3, distance 2 hops)
        c3 = review_order.candidates[2]
        assert c3.path == "web.py"
        assert c3.tier == 3
        assert c3.distance == 2
        assert "distance 2" in c3.reason

        # Limitations: đồ thị đầy đủ, không có unresolved -> limitations rỗng
        assert review_order.limitations == ()
