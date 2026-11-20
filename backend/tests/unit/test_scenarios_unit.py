"""Immutable one-file overlay and source-aware graph comparisons."""

import difflib

import pytest

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.graph import build_graph
from smartregression.core.explorer.scenarios import compare_graphs, overlay


def test_full_source_overlay_never_changes_original_and_adds_payment_method():
    sources = {"payment.js": "export function pay(){}", "app.js": 'import {pay} from "./payment";'}
    original = dict(sources)
    result = overlay(
        sources, "payment.js", content="export function pay(){}\nexport function refund(){}"
    )
    assert sources == original and result["app.js"] == sources["app.js"]
    before = build_graph("repo", "a" * 40, sources, parse_javascript)
    after = build_graph("repo", "a" * 40, result, parse_javascript)
    delta = compare_graphs(before, after)
    assert any(node.path == "payment.js" and node.symbol == "refund" for node in delta.added_nodes)


def test_matching_single_file_diff_and_no_newline():
    source = "export function pay(){return 1;}"
    changed = "export function pay(){return 2;}"
    patch = (
        "--- a/payment.js\n+++ b/payment.js\n@@ -1 +1 @@\n-"
        + source
        + "\n\\ No newline at end of file\n+"
        + changed
        + "\n\\ No newline at end of file\n"
    )
    assert overlay({"payment.js": source}, "payment.js", patch=patch)["payment.js"] == changed


@pytest.mark.parametrize(
    "path,patch",
    [
        ("../secret.js", ""),
        ("new.js", ""),
        ("payment.js", "--- a/other.js\n+++ b/other.js\n@@ -1 +1 @@\n-x\n+y\n"),
        ("payment.js", "--- a/payment.js\n+++ b/payment.js\n@@ -1 +1 @@\n-wrong context\n+y\n"),
        ("payment.js", "--- /dev/null\n+++ b/payment.js\n@@ -0,0 +1 @@\n+new\n"),
    ],
)
def test_overlay_rejects_out_of_scope_paths_or_bad_context(path, patch):
    with pytest.raises(ValueError):
        overlay({"payment.js": "old\n"}, path, patch=patch)


def test_generated_unified_patch_round_trip_and_size_limit():
    source = "one\ntwo\nthree\n"
    target = "one\nchanged\nthree\n"
    patch = "".join(
        difflib.unified_diff(
            source.splitlines(True),
            target.splitlines(True),
            fromfile="a/file.py",
            tofile="b/file.py",
        )
    )
    assert overlay({"file.py": source}, "file.py", patch=patch)["file.py"] == target
    with pytest.raises(ValueError, match="overlay_limit"):
        overlay({"file.py": source}, "file.py", content="x" * 262145)


def test_version_comparison_rejects_wrong_repository_or_config():
    first = build_graph("one", "a" * 40, {"a.js": "export function a(){}"}, parse_javascript)
    second = build_graph("two", "b" * 40, {"a.js": "export function a(){}"}, parse_javascript)
    with pytest.raises(ValueError, match="comparison_identity_mismatch"):
        compare_graphs(first, second)
    with pytest.raises(ValueError, match="comparison_identity_mismatch"):
        compare_graphs(first, first.model_copy(update={"config_digest": "f" * 64}))


def test_equal_versions_have_no_delta_and_removed_evidence_keeps_base_sha():
    base = build_graph("one", "a" * 40, {"old.py": "def gone(): pass\n"}, parse_javascript)
    equal = compare_graphs(base, base)
    assert equal.total_added_nodes == equal.total_removed_nodes == 0
    target = build_graph("one", "b" * 40, {"new.py": "def added(): pass\n"}, parse_javascript)
    delta = compare_graphs(base, target)
    assert delta.removed_nodes and delta.added_nodes
    assert delta.base_commit == "a" * 40 and delta.target_commit == "b" * 40
    removed = [node.evidence for node in delta.removed_nodes if node.symbol]
    added = [node.evidence for node in delta.added_nodes if node.symbol]
    assert removed and all(proof.commit == "a" * 40 for proof in removed)
    assert added and all(proof.commit == "b" * 40 for proof in added)
