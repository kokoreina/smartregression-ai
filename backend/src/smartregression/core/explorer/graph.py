"""Deterministic bounded explorer graphs and potential impact, never behavioral proof."""

import hashlib
import posixpath
import re
import time
from collections import defaultdict, deque
from collections.abc import Callable, Iterable, Mapping

from smartregression.contracts.explorer import (
    CallPaths,
    ClassifiedReference,
    ExplorerEdge,
    ExplorerGraph,
    ExplorerNode,
    GraphCoverage,
    GraphEvidence,
    GraphView,
    Hotspots,
    ImpactSummary,
    UnresolvedRelation,
)
from smartregression.core.explorer.coverage import update_diagnostics
from smartregression.core.explorer.parsing import ParsedFile
from smartregression.core.explorer.python import parse_python
from smartregression.core.explorer.python_resolution import BUILTINS, STDLIB, PythonResolver
from smartregression.core.git.snapshots import validate_snapshot_paths
from smartregression.core.impact.dependency_graph import build_dependency_graph

PARSER_CONFIG = hashlib.sha256(
    b"explorer-python-lexical-reexports-diagnostics-v3-js-ts0261-grammar0250"
    + "|".join(sorted(BUILTINS | STDLIB)).encode()
).hexdigest()


def digest(*values: str) -> str:
    return hashlib.sha256("\0".join(values).encode()).hexdigest()


def resolve(path: str, reference: str, files: set[str]) -> str | None:
    if path.endswith(".js"):
        if not reference.startswith(("./", "../")):
            return None
        value = posixpath.normpath(posixpath.join(posixpath.dirname(path), reference))
        if value.startswith("../") or value.startswith("/"):
            return None
        choices = [value] if value.endswith(".js") else [value + ".js", value + "/index.js"]
    else:
        level = len(reference) - len(reference.lstrip("."))
        module = reference[level:]
        if level:
            package = path.split("/")[:-1]
            if level > len(package):
                return None
            parts = package[: len(package) - level + 1]
        else:
            parts = []
        value = "/".join([*parts, *module.split(".")]) if module else "/".join(parts)
        choices = [value + ".py", value + "/__init__.py"]
    return next((choice for choice in choices if choice in files), None)


def build_graph(
    repository_id: str,
    commit: str,
    sources: Mapping[str, str],
    parse_javascript: Callable[[str], ParsedFile],
    *,
    overlay_identity: tuple[str, str] | None = None,
    known_paths: Iterable[str] = (),
) -> ExplorerGraph:
    if not repository_id or not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("invalid_snapshot_identity")
    validate_snapshot_paths(list(sources))
    deadline = time.monotonic() + 20
    if len(sources) > 5000:
        raise ValueError("graph_file_limit")
    parsed = {}
    unparsed = []
    unsupported = []
    unresolved = []
    classified = []
    for path, source in sorted(sources.items()):
        if time.monotonic() > deadline:
            raise ValueError("graph_timeout")
        if not path.endswith((".py", ".js")):
            unsupported.append(path)
            continue
        try:
            facts = parse_python(source) if path.endswith(".py") else parse_javascript(source)
        except ValueError, RecursionError, UnicodeError:
            facts = ParsedFile(syntax_error=True)
        if facts.syntax_error:
            unparsed.append(path)
        parsed[path] = facts
        unresolved.extend(
            UnresolvedRelation(path=path, reference="", reason=reason, line=line)
            for reason, line in facts.issues
        )
    nodes = {}
    edges = {}

    def evidence(path, line=None, end=None):
        return GraphEvidence(
            id=digest(
                repository_id,
                commit,
                PARSER_CONFIG,
                overlay_identity[1] if overlay_identity else "git",
                path,
                str(line),
                str(end or line),
            ),
            commit=commit,
            path=path,
            kind="metadata" if line is None else "source_range",
            line_start=line,
            line_end=end or line,
            source_kind="overlay" if overlay_identity and overlay_identity[0] == path else "git",
            overlay_digest=overlay_identity[1]
            if overlay_identity and overlay_identity[0] == path
            else None,
        )

    def node(path, kind, label, symbol=None, line=None, end=None):
        identity = digest(
            repository_id,
            commit,
            PARSER_CONFIG,
            overlay_identity[1] if overlay_identity else "git",
            path,
            kind,
            symbol or "",
        )
        if identity not in nodes and len(nodes) >= 10000:
            raise ValueError("graph_size_limit")
        value = ExplorerNode(
            id=identity,
            path=path,
            kind=kind,
            label=label,
            symbol=symbol,
            evidence=evidence(path, line, end) if line else None,
        )
        nodes[identity] = value
        return value

    def edge(source, target, kind, where):
        identity = digest(source.id, target.id, kind, where.id)
        if identity not in edges and len(edges) >= 30000:
            raise ValueError("graph_size_limit")
        edges[identity] = ExplorerEdge(
            id=identity,
            source=source.id,
            target=target.id,
            source_path=source.path,
            target_path=target.path,
            kind=kind,
            evidence=where,
        )

    directories = {}
    file_nodes = {}
    symbols = {}
    for path in sorted(sources):
        parts = path.split("/")
        previous = None
        for index in range(1, len(parts)):
            folder = "/".join(parts[:index])
            current = directories.setdefault(folder, node(folder, "directory", parts[index - 1]))
            if previous:
                edge(previous, current, "contains", evidence(path))
            previous = current
        file_nodes[path] = node(path, "file", parts[-1])
        if previous:
            edge(previous, file_nodes[path], "contains", evidence(path))
    for path, facts in parsed.items():
        if facts.syntax_error:
            continue
        names = defaultdict(list)
        for fact in facts.symbols:
            names[fact.name].append(fact)
        for name, items in names.items():
            if len(items) > 1:
                unresolved.append(
                    UnresolvedRelation(path=path, reference=name, reason="ambiguous_symbol")
                )
                continue
            fact = items[0]
            value = node(path, fact.kind, name.rsplit(".", 1)[-1], name, fact.start, fact.end)
            symbols[path, name] = value
            edge(file_nodes[path], value, "contains", evidence(path, fact.start, fact.end))
    # Reuse the canonical Python import engine on the parseable subset.
    py_sources = {p: sources[p] for p in parsed if p.endswith(".py") and not parsed[p].syntax_error}
    try:
        canonical = build_dependency_graph(
            repository=repository_id, revision=commit, sources=py_sources
        )
    except ValueError:
        canonical = None
        unresolved.append(
            UnresolvedRelation(
                path=next(iter(py_sources), ""), reference="", reason="ambiguous_python_modules"
            )
        )
    python_resolver = PythonResolver(parsed, symbols, resolve, known_paths)
    bindings = {}
    for path, facts in parsed.items():
        if facts.syntax_error:
            continue
        aliases = {}
        for imported in facts.imports:
            target = resolve(path, imported.reference, set(parsed))
            if path.endswith(".py") and not target and imported.bindings:
                suffix = "" if imported.reference.endswith(".") else "."
                submodules = [
                    resolve(path, imported.reference + suffix + name, set(parsed))
                    for _, name in imported.bindings
                ]
                for module in set(submodules) - {None}:
                    edge(
                        file_nodes[path],
                        file_nodes[module],
                        "imports",
                        evidence(path, imported.line),
                    )
                if all(submodules):
                    continue
            if target and target != path:
                edge(file_nodes[path], file_nodes[target], "imports", evidence(path, imported.line))
            elif target == path:
                edge(file_nodes[path], file_nodes[path], "imports", evidence(path, imported.line))
            else:
                if path.endswith(".py") and python_resolver.stdlib(imported.reference):
                    classified.append(
                        ClassifiedReference(
                            path=path,
                            reference=imported.reference,
                            category="stdlib",
                            kind="import",
                            line=imported.line,
                        )
                    )
                else:
                    internal = path.endswith(".py") and (
                        imported.reference.startswith(".")
                        or imported.reference.split(".")[0] in python_resolver.local_roots
                    )
                    unresolved.append(
                        UnresolvedRelation(
                            path=path,
                            reference=imported.reference,
                            reason="unresolved_internal_import"
                            if internal
                            else "external_or_unresolved_import",
                            line=imported.line,
                        )
                    )
            if target:
                for local, export in imported.bindings:
                    if local in aliases:
                        aliases[local] = None
                    else:
                        aliases[local] = (target, export)
        bindings[path] = aliases
    if canonical:
        observed_imports = {
            (e.source_path, e.target_path) for e in edges.values() if e.kind == "imports"
        }
        for item in canonical.edges:
            if (item.source.path, item.target.path) not in observed_imports:
                edge(
                    file_nodes[item.source.path],
                    file_nodes[item.target.path],
                    "imports",
                    evidence(item.source.path),
                )
    for path, facts in parsed.items():
        if time.monotonic() > deadline:
            raise ValueError("graph_timeout")
        if facts.syntax_error:
            continue
        for call in facts.calls:
            if path.endswith(".py"):
                result = python_resolver.call(path, call.caller, call.expression)
                caller = symbols.get((path, call.caller)) if call.caller else file_nodes[path]
                target = (
                    symbols.get((result.path, result.name)) if result.kind == "symbol" else None
                )
                if caller and target:
                    edge(caller, target, "calls", evidence(path, call.line))
                elif result.kind in {"builtin", "stdlib"}:
                    classified.append(
                        ClassifiedReference(
                            path=path,
                            reference=call.expression,
                            category=result.kind,
                            kind="call",
                            line=call.line,
                        )
                    )
                else:
                    unresolved.append(
                        UnresolvedRelation(
                            path=path,
                            reference=call.expression,
                            line=call.line,
                            reason="shadowed_call"
                            if result.kind == "shadowed"
                            else "unresolved_static_call",
                        )
                    )
                continue
            if call.expression.split(".")[0] in facts.shadowed.get(call.caller or "", set()):
                unresolved.append(
                    UnresolvedRelation(
                        path=path, reference=call.expression, reason="shadowed_call", line=call.line
                    )
                )
                continue
            caller = symbols.get((path, call.caller)) if call.caller else file_nodes[path]
            target = None
            expression = call.expression
            # Resolve same-file function names lexically from inner to outer scope.
            prefix = call.caller.rsplit(".", 1)[0] if call.caller and "." in call.caller else ""
            for candidate in ([prefix + "." + expression] if prefix else []) + [expression]:
                if (path, candidate) in symbols and "." not in expression:
                    target = symbols[path, candidate]
                    break
            alias = expression.split(".")[0]
            binding = bindings.get(path, {}).get(alias)
            if target is None and binding:
                other, export = binding
                if export == "*" and "." in expression:
                    export = expression.split(".", 1)[1]
                if export != "*":
                    target = symbols.get((other, parsed[other].exports.get(export, export)))
            if caller and target:
                edge(caller, target, "calls", evidence(path, call.line))
            else:
                unresolved.append(
                    UnresolvedRelation(
                        path=path,
                        reference=expression,
                        reason="unresolved_static_call",
                        line=call.line,
                    )
                )
    if len(nodes) > 10000 or len(edges) > 30000:
        raise ValueError("graph_size_limit")
    analyzed = sorted(p for p in parsed if p not in unparsed)
    coverage = GraphCoverage(
        status="partial" if unparsed or unsupported or unresolved else "complete",
        analyzed_files=analyzed,
        unparsed_files=sorted(unparsed),
        unsupported_files=sorted(unsupported),
    )
    result = ExplorerGraph(
        repository_id=repository_id,
        commit=commit,
        config_digest=PARSER_CONFIG,
        overlay_digest=overlay_identity[1] if overlay_identity else None,
        nodes=sorted(nodes.values(), key=lambda n: (n.path, n.kind, n.symbol or "")),
        edges=sorted(edges.values(), key=lambda e: e.id),
        unresolved=sorted(unresolved, key=lambda u: (u.path, u.line, u.reason, u.reference)),
        classified_references=sorted(
            classified, key=lambda r: (r.path, r.line, r.category, r.reference)
        ),
        coverage=coverage,
    )
    update_diagnostics(result)
    return result


def import_adjacency(graph: ExplorerGraph):
    adjacency = {p: set() for p in graph.coverage.analyzed_files}
    for item in graph.edges:
        if item.kind == "imports":
            adjacency.setdefault(item.source_path, set()).add(item.target_path)
    return adjacency


def impact(graph: ExplorerGraph, changed: set[str]) -> ImpactSummary:
    known = set(graph.coverage.analyzed_files)
    if not changed <= {n.path for n in graph.nodes if n.kind == "file"}:
        raise ValueError("unknown_changed_path")
    reverse = defaultdict(set)
    for source, targets in import_adjacency(graph).items():
        for target in targets:
            reverse[target].add(source)
    distance = {p: 0 for p in changed}
    predecessors = {}
    queue = deque(sorted(changed))
    while queue:
        current = queue.popleft()
        for dependent in sorted(reverse[current]):
            if dependent not in distance:
                distance[dependent] = distance[current] + 1
                predecessors[dependent] = current
                queue.append(dependent)
    direct = sorted(p for p, d in distance.items() if d == 1 and p not in changed)
    indirect = sorted(p for p, d in distance.items() if d > 1 and p not in changed)
    changed_known = sorted(changed & known)
    paths = {}
    paths_truncated = len(distance) > 150
    for candidate in sorted(distance)[:150]:
        if distance[candidate] >= 20:
            paths_truncated = True
            continue
        sequence = [candidate]
        while sequence[-1] in predecessors:
            sequence.append(predecessors[sequence[-1]])
        paths[candidate] = list(reversed(sequence))
    denominator = len(known) or None
    counts = {
        "changed": len(changed_known),
        "direct": len(set(direct) & known),
        "indirect": len(set(indirect) & known),
        "potential": len((changed | set(direct) | set(indirect)) & known),
    }
    return ImpactSummary(
        changed=sorted(changed),
        direct=direct,
        indirect=indirect,
        denominator=denominator,
        percentages={
            k: round(v * 100 / denominator, 2) if denominator else None for k, v in counts.items()
        },
        counts=counts,
        unknown_changed_count=len(changed - known),
        paths=paths,
        paths_truncated=paths_truncated,
        coverage=graph.coverage,
        unresolved_count=len(graph.unresolved),
    )


def neighborhood(
    graph: ExplorerGraph,
    focus_path: str | None = None,
    limit: int = 150,
    direction: str = "both",
    depth: int = 2,
) -> GraphView:
    if (
        not 1 <= limit <= 150
        or not 0 <= depth <= 10
        or direction not in {"both", "dependencies", "dependents"}
    ):
        raise ValueError("invalid_graph_bound")
    adjacency = defaultdict(set)
    for edge in graph.edges:
        if direction in {"both", "dependencies"}:
            adjacency[edge.source].add(edge.target)
        if direction in {"both", "dependents"}:
            adjacency[edge.target].add(edge.source)
    if focus_path:
        focus = next((n.id for n in graph.nodes if n.path == focus_path and n.kind == "file"), None)
        if focus is None:
            raise ValueError("unknown_focus_path")
        queue = deque([(focus, 0)])
        visited = set()
        order = []
        while queue:
            current, distance = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            order.append(current)
            if distance < depth:
                queue.extend((n, distance + 1) for n in sorted(adjacency[current]))
    else:
        order = [n.id for n in graph.nodes]
    selected = set(order[:limit])
    nodes = [n for n in graph.nodes if n.id in selected]
    edges = [e for e in graph.edges if e.source in selected and e.target in selected]
    return GraphView(
        repository_id=graph.repository_id,
        commit=graph.commit,
        config_digest=graph.config_digest,
        coverage=graph.coverage,
        nodes=nodes,
        edges=edges[:1000],
        total_nodes=len(graph.nodes),
        total_edges=len(graph.edges),
        truncated=len(order) > limit or len(edges) > 1000,
    )


def hotspots(graph: ExplorerGraph) -> Hotspots:
    adjacency = import_adjacency(graph)
    reverse = defaultdict(set)
    for source, targets in list(adjacency.items()):
        for target in targets:
            reverse[target].add(source)
            adjacency.setdefault(target, set())
    visited = set()
    order = []
    for start in sorted(adjacency):
        stack = [(start, False)]
        while stack:
            current, exit_ = stack.pop()
            if exit_:
                order.append(current)
                continue
            if current in visited:
                continue
            visited.add(current)
            stack.append((current, True))
            stack.extend(
                (n, False) for n in sorted(adjacency[current], reverse=True) if n not in visited
            )
    assigned = set()
    cycles = []
    for start in reversed(order):
        if start in assigned:
            continue
        stack = [start]
        component = []
        while stack:
            current = stack.pop()
            if current in assigned:
                continue
            assigned.add(current)
            component.append(current)
            stack.extend(reverse[current] - assigned)
        if len(component) > 1 or start in adjacency[start]:
            cycles.append(sorted(component))
    return Hotspots(
        cycles=sorted(cycles),
        fan_in={p: len(reverse[p]) for p in sorted(adjacency)},
        fan_out={p: len(adjacency[p]) for p in sorted(adjacency)},
        cross_module_edges=[
            e.id
            for e in graph.edges
            if e.kind == "imports" and e.source_path.split("/")[0] != e.target_path.split("/")[0]
        ],
    )


def call_paths(graph: ExplorerGraph, start: str, depth: int = 10, limit: int = 20) -> CallPaths:
    if not 1 <= depth <= 10 or not 1 <= limit <= 20 or start not in {n.id for n in graph.nodes}:
        raise ValueError("invalid_call_path_query")
    adjacency = defaultdict(set)
    for edge in graph.edges:
        if edge.kind == "calls":
            adjacency[edge.source].add(edge.target)
    paths = []
    stack = [[start]]
    truncated = False
    visited = set()
    while stack and len(paths) < limit and len(visited) < 150:
        path = stack.pop()
        visited.add(path[-1])
        children = sorted(adjacency[path[-1]])
        if len(path) - 1 >= depth:
            paths.append(path)
            truncated |= bool(children)
            continue
        if not children:
            paths.append(path)
            continue
        for child in reversed(children):
            if child in path:
                paths.append(path + [child])
            else:
                stack.append(path + [child])
            if len(paths) >= limit:
                break
    truncated |= bool(stack)
    source_paths = {n.path for n in graph.nodes if n.id in visited}
    return CallPaths(
        paths=paths[:limit],
        nodes=[node for node in graph.nodes if node.id in visited],
        unresolved=[u for u in graph.unresolved if u.path in source_paths],
        truncated=truncated,
    )
