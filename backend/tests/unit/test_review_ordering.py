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
