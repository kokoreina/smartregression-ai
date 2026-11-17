"""Deterministic reading paths and bounded lexical search over eligible cached bytes.

No semantic-match claim: Vietnamese accents are normalized; the same distinct-term
weighting as the research lexical engine is reused, with explicit web chunking.
"""

import json
import time
import tomllib
import unicodedata

from smartregression.contracts.assistance import (
    FeatureMatch,
    FeatureSearch,
    ReadingGuide,
    ReadingStep,
)
from smartregression.contracts.explorer import GraphEvidence
from smartregression.core.explorer.graph import digest
from smartregression.core.explorer.policy import source_allowed
from smartregression.core.retrieval.lexical import distinct_score, tokenize


def terms(value):
    normalized = "".join(
        c
        for c in unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
        if not unicodedata.combining(c)
    )
    return set(tokenize(value)) | set(tokenize(normalized))


def evidence(graph, path, start, end):
    return GraphEvidence(
        id=digest(
            graph.repository_id,
            graph.commit,
            graph.config_digest,
            "assist/1",
            path,
            str(start),
            str(end),
        ),
        commit=graph.commit,
        path=path,
        line_start=start,
        line_end=end,
    )


def reading_guide(graph, sources):
    safe = {p: s for p, s in sources.items() if source_allowed(p, s.encode())}
    steps = []
    observed = set()
    limitations = [
        "Static reading order; not runtime execution order.",
        "Only eligible cached files and supported parser facts are used.",
    ]

    def entry(path, config):
        if path in safe and path in graph.coverage.analyzed_files and path not in observed:
            observed.add(path)
            steps.append(
                ReadingStep(
                    category="entrypoint",
                    path=path,
                    reason="Declared entrypoint in " + config,
                    evidence=evidence(graph, config, 1, max(1, len(safe[config].splitlines()))),
                )
            )

    for path, content in sorted(safe.items()):
        if path.rsplit("/", 1)[-1] not in {"package.json", "pyproject.toml"}:
            continue
        prefix = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
        try:
            if path.endswith("package.json"):
                data = json.loads(content)
                candidates = [data.get("main"), data.get("module")]
                exports = data.get("exports")
                candidates.extend([exports] if isinstance(exports, str) else [])
                for candidate in candidates:
                    if isinstance(candidate, str):
                        entry(prefix + candidate.removeprefix("./"), path)
            else:
                data = tomllib.loads(content)
                for target in data.get("project", {}).get("scripts", {}).values():
                    if isinstance(target, str):
                        module = target.split(":")[0].replace(".", "/")
                        for candidate in [
                            prefix + module + ".py",
                            prefix + "src/" + module + ".py",
                        ]:
                            entry(candidate, path)
        except ValueError, TypeError, AttributeError:
            limitations.append("Unreadable entrypoint configuration: " + path)
    files = {node.path: node for node in graph.nodes if node.kind == "file" and node.path in safe}
    fanin = {p: 0 for p in files}
    for edge in graph.edges:
        if edge.kind == "imports" and edge.target_path in fanin:
            fanin[edge.target_path] += 1
    for path in sorted(files, key=lambda p: (-fanin[p], p)):
        if path in observed:
            continue
        parts = path.lower().split("/")
        category = (
            "tests"
            if any(
                p in {"test", "tests", "__tests__"}
                or p.startswith("test_")
                or p.endswith((".test.js", ".spec.js"))
                for p in parts
            )
            else "data"
            if any(p in {"models", "schemas", "data", "storage", "database"} for p in parts)
            else "module"
        )
        node = files[path]
        proof = node.evidence or GraphEvidence(
            id=digest(
                graph.repository_id, graph.commit, graph.config_digest, "file-metadata", path
            ),
            commit=graph.commit,
            path=path,
            kind="metadata",
        )
        steps.append(
            ReadingStep(
                category=category,
                path=path,
                reason="Observed " + category + "; incoming imports: " + str(fanin[path]),
                evidence=proof,
            )
        )
    # Keep all categories visible even when modules dominate the repository.
    selected = []
    for category in ["entrypoint", "module", "data", "tests"]:
        selected.extend([s for s in steps if s.category == category][:10])
    if len(selected) < len(steps):
        limitations.append(
            "At most 10 files per reading category; use explorer for the remaining scope."
        )
    if not observed:
        limitations.append("Entrypoint not established from supported configuration.")
    return ReadingGuide(
        repository_id=graph.repository_id,
        commit=graph.commit,
        config_digest=graph.config_digest,
        entrypoint_status="observed" if observed else "unknown",
        steps=selected,
        limitations=limitations,
    )


def search_features(graph, sources, query, top_k=10):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 600 or not 1 <= top_k <= 10:
        raise ValueError("invalid_search_query")
    query_terms = terms(query)
    if len(query_terms) > 128:
        raise ValueError("search_term_limit")
    deadline = time.monotonic() + 5
    items = []
    chunks = 0
    truncated = False
    total = 0
    symbols = {}
    for node in graph.nodes:
        if node.symbol and node.evidence:
            symbols.setdefault(node.path, []).append(node)
    for path, text in sorted(sources.items()):
        if not source_allowed(path, text.encode()):
            continue
        lines = text.splitlines()
        for offset in range(0, len(lines), 40):
            if chunks >= 5000 or total >= 16_000_000 or time.monotonic() >= deadline:
                truncated = True
                break
            content = "\n".join(lines[offset : offset + 40])
            size = len(content.encode())
            if size > 8192:
                truncated = True
                continue
            total += size
            chunks += 1
            symbol = next(
                (
                    n.symbol
                    for n in symbols.get(path, [])
                    if n.evidence.line_start and offset < n.evidence.line_start <= offset + 40
                ),
                None,
            )
            matched = query_terms & terms(path + " " + (symbol or "") + " " + content)
            if not matched:
                continue
            items.append(
                FeatureMatch(
                    path=path,
                    symbol=symbol,
                    score=distinct_score(matched, query_terms, symbol, path),
                    matched_terms=sorted(matched),
                    evidence=evidence(graph, path, offset + 1, min(len(lines), offset + 40)),
                )
            )
        if chunks >= 5000 or total >= 16_000_000 or time.monotonic() >= deadline:
            break
    items.sort(key=lambda i: (-i.score, i.path, i.evidence.line_start))
    return FeatureSearch(
        repository_id=graph.repository_id,
        commit=graph.commit,
        config_digest=graph.config_digest,
        query=query,
        status="matched" if items else "no_evidence",
        items=items[:top_k],
        indexed_chunks=chunks,
        truncated=truncated,
        limitations=[
            "Lexical matches only; no semantic or dependency inference.",
            "Vietnamese accents normalized; no automatic translation.",
        ]
        + (["Index bounds reached; absence of a match is inconclusive."] if truncated else []),
    )
