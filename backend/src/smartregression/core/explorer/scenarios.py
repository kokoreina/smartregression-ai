"""Strict single-file immutable overlay and provenance-preserving graph deltas."""

import re
from collections.abc import Mapping

from smartregression.contracts.explorer import ExplorerGraph
from smartregression.contracts.scenarios import GraphDelta
from smartregression.core.git.snapshots import validate_snapshot_paths


def overlay(
    sources: Mapping[str, str], path: str, *, content: str | None = None, patch: str | None = None
) -> dict[str, str]:
    validate_snapshot_paths([path])
    if path not in sources or not path.endswith((".py", ".js")):
        raise ValueError("existing_supported_file_required")
    if (content is None) == (patch is None):
        raise ValueError("one_overlay_input_required")
    value = content if content is not None else patch
    if len(value.encode("utf-8")) > 262144 or "\0" in value:
        raise ValueError("overlay_limit")
    if patch is not None:
        content = apply_patch(sources[path], path, patch)
    result = dict(sources)
    result[path] = content
    return result


def apply_patch(source: str, path: str, patch: str) -> str:
    lines = patch.splitlines(keepends=True)
    index = 0
    if lines and lines[0].startswith("diff --git "):
        if lines[0].rstrip("\r\n") != f"diff --git a/{path} b/{path}":
            raise ValueError("patch_path_mismatch")
        index += 1
    if index < len(lines) and lines[index].startswith("index "):
        if not re.fullmatch(r"index [0-9a-f]+\.\.[0-9a-f]+(?: [0-9]{6})?\r?\n?", lines[index]):
            raise ValueError("unsupported_patch_metadata")
        index += 1
    expected = ["--- a/" + path, "+++ b/" + path]
    for header in expected:
        if index >= len(lines) or lines[index].rstrip("\r\n").split("\t")[0] != header:
            raise ValueError("patch_path_mismatch")
        index += 1
    original = source.splitlines(keepends=True)
    result = []
    cursor = 0
    hunks = 0
    while index < len(lines):
        match = re.fullmatch(
            r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\r\n]*\r?\n?", lines[index]
        )
        if not match:
            raise ValueError("unsupported_patch")
        old_start = int(match[1])
        old_count = int(match[2] or "1")
        new_start = int(match[3])
        new_count = int(match[4] or "1")
        position = old_start - 1 if old_count else old_start
        new_position = new_start - 1 if new_count else new_start
        if position < cursor or position > len(original):
            raise ValueError("patch_context_mismatch")
        result.extend(original[cursor:position])
        cursor = position
        if len(result) != new_position:
            raise ValueError("patch_position_mismatch")
        index += 1
        consumed = added = 0
        hunks += 1
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if not line or line[0] not in {" ", "-", "+"}:
                raise ValueError("unsupported_patch")
            marker = line[0]
            text = line[1:]
            index += 1
            if index < len(lines) and lines[index].startswith("\\ No newline at end of file"):
                text = text.removesuffix("\n").removesuffix("\r")
                index += 1
            if marker in {" ", "-"}:
                if cursor >= len(original) or original[cursor] != text:
                    raise ValueError("patch_context_mismatch")
                cursor += 1
                consumed += 1
            if marker in {" ", "+"}:
                result.append(text)
                added += 1
        if consumed != old_count or added != new_count:
            raise ValueError("patch_hunk_count_mismatch")
    if hunks == 0:
        raise ValueError("empty_patch")
    result.extend(original[cursor:])
    output = "".join(result)
    if len(output.encode()) > 262144:
        raise ValueError("overlay_limit")
    return output


def compare_graphs(left: ExplorerGraph, right: ExplorerGraph) -> GraphDelta:
    if left.repository_id != right.repository_id or left.config_digest != right.config_digest:
        raise ValueError("comparison_identity_mismatch")

    def node_key(node):
        return node.path, node.kind, node.symbol or ""

    a = {node_key(n): n for n in left.nodes}
    b = {node_key(n): n for n in right.nodes}
    left_nodes = {n.id: node_key(n) for n in left.nodes}
    right_nodes = {n.id: node_key(n) for n in right.nodes}

    def edge_key(edge, nodes):
        return nodes[edge.source], nodes[edge.target], edge.kind

    x = {edge_key(e, left_nodes): e for e in left.edges}
    y = {edge_key(e, right_nodes): e for e in right.edges}
    return GraphDelta(
        repository_id=left.repository_id,
        base_commit=left.commit,
        target_commit=right.commit,
        config_digest=left.config_digest,
        added_nodes=[b[k] for k in sorted(b.keys() - a.keys())],
        removed_nodes=[a[k] for k in sorted(a.keys() - b.keys())],
        retained_node_count=len(a.keys() & b.keys()),
        added_edges=[y[k] for k in sorted(y.keys() - x.keys())],
        removed_edges=[x[k] for k in sorted(x.keys() - y.keys())],
        retained_edge_count=len(x.keys() & y.keys()),
        total_added_nodes=len(b.keys() - a.keys()),
        total_removed_nodes=len(a.keys() - b.keys()),
        total_added_edges=len(y.keys() - x.keys()),
        total_removed_edges=len(x.keys() - y.keys()),
        limitations=[
            "Rename matching is unsupported; renamed paths appear as removed/added.",
            "Static observations are potential relationships, not behavioral proof.",
            *(
                ["At least one graph has partial coverage."]
                if left.coverage.status == "partial" or right.coverage.status == "partial"
                else []
            ),
        ],
    )
