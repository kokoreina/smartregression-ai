"""Snapshot-scoped static dependency graph observations for Python sources.

Edges point from the importing source node to the imported module node. This is
an import graph, not a call graph or proof of behavioral impact.
"""

import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass

_FULL_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


@dataclass(frozen=True)
class GraphNode:
    path: str
    repository: str
    revision: str

    def __post_init__(self) -> None:
        if not self.repository.strip() or not _FULL_SHA.fullmatch(self.revision):
            raise ValueError("invalid_snapshot_identity")


@dataclass(frozen=True)
class GraphEdge:
    source: GraphNode
    target: GraphNode
    kind: str

    def __post_init__(self) -> None:
        if (
            self.source.repository != self.target.repository
            or self.source.revision != self.target.revision
        ):
            raise ValueError("cross_snapshot_edge")


@dataclass(frozen=True)
class UnresolvedImport:
    source_path: str
    reference: str
    kind: str
    reason: str


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    unresolved: tuple[UnresolvedImport, ...]

    def __post_init__(self) -> None:
        identities = {(node.repository, node.revision) for node in self.nodes}
        if len(identities) > 1:
            raise ValueError("mixed_snapshot_nodes")
        node_paths = {node.path for node in self.nodes}
        for edge in self.edges:
            if edge.source.path not in node_paths or edge.target.path not in node_paths:
                raise ValueError("edge_endpoint_not_in_graph")
            if identities and (
                (edge.source.repository, edge.source.revision) not in identities
                or (edge.target.repository, edge.target.revision) not in identities
            ):
                raise ValueError("edge_snapshot_not_in_graph")
        for item in self.unresolved:
            if item.source_path not in node_paths:
                raise ValueError("unresolved_source_not_in_graph")


def build_dependency_graph(
    *,
    repository: str,
    revision: str,
    sources: Mapping[str, str],
) -> DependencyGraph:
    """Build a deterministic graph from one authorized, already-frozen snapshot.

    The caller owns authorization and snapshot materialization. This function
    never reads or executes repository files and never substitutes another
    revision.
    """
    GraphNode(path="__snapshot_validation__.py", repository=repository, revision=revision)

    module_paths: dict[str, str] = {}
    trees: dict[str, ast.Module] = {}
    nodes: dict[str, GraphNode] = {}
    for path, source in sources.items():
        module = _module_name(path)
        if module in module_paths:
            raise ValueError("ambiguous_module")
        try:
            tree = ast.parse(source)
        except (SyntaxError, RecursionError, ValueError) as exc:
            raise ValueError("python_parse_failed") from exc
        module_paths[module] = path
        trees[path] = tree
        nodes[path] = GraphNode(path=path, repository=repository, revision=revision)

    edges: set[tuple[str, str, str]] = set()
    unresolved: set[tuple[str, str, str, str]] = set()
    for path, tree in trees.items():
        dynamic_names, dynamic_modules = _dynamic_import_aliases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _record_reference(
                        path,
                        alias.name,
                        "absolute_import",
                        module_paths,
                        edges,
                        unresolved,
                    )
            elif isinstance(node, ast.ImportFrom):
                reference, resolution_reason = _resolve_from_import(path, node)
                kind = "relative_import" if node.level else "absolute_import"
                if any(alias.name == "*" for alias in node.names):
                    unresolved.add(
                        (path, reference or "<relative>", "star_import", "unsupported_import")
                    )
                elif reference is None:
                    unresolved.add(
                        (
                            path,
                            "<relative>",
                            kind,
                            resolution_reason or "relative_import_unresolved",
                        )
                    )
                else:
                    _record_reference(
                        path,
                        reference,
                        kind,
                        module_paths,
                        edges,
                        unresolved,
                    )
            elif isinstance(node, ast.Call):
                reference = _dynamic_reference(node, dynamic_names, dynamic_modules)
                if reference is not None:
                    unresolved.add((path, reference, "dynamic_import", "unsupported_import"))

    return DependencyGraph(
        nodes=tuple(nodes[path] for path in sorted(nodes)),
        edges=tuple(
            GraphEdge(source=nodes[source], target=nodes[target], kind=kind)
            for source, target, kind in sorted(edges)
        ),
        unresolved=tuple(
            UnresolvedImport(
                source_path=source,
                reference=reference,
                kind=kind,
                reason=reason,
            )
            for source, reference, kind, reason in sorted(unresolved)
        ),
    )


def _module_name(path: str) -> str:
    if not path.endswith(".py") or "\\" in path or not path.strip():
        raise ValueError("python_path_required")
    module = path[:-3].replace("/", ".")
    if module.endswith(".__init__"):
        module = module[:-9]
    if not module or any(part in {"", ".", ".."} for part in module.split(".")):
        raise ValueError("python_path_required")
    return module


def _resolve_from_import(
    path: str,
    node: ast.ImportFrom,
) -> tuple[str | None, str | None]:
    current = _module_name(path)
    package = current.split(".") if path.endswith("__init__.py") else current.split(".")[:-1]
    if node.level:
        if node.level > len(package):
            return None, "relative_import_beyond_root"
        base = package[: len(package) - node.level + 1]
        if node.module:
            base.append(node.module)
        elif node.names:
            base.append(node.names[0].name)
        if not base:
            return None, "relative_import_unresolved"
        return ".".join(base), None
    return node.module, None


def _record_reference(
    source_path: str,
    reference: str,
    kind: str,
    module_paths: Mapping[str, str],
    edges: set[tuple[str, str, str]],
    unresolved: set[tuple[str, str, str, str]],
) -> None:
    target = module_paths.get(reference)
    if target is None:
        unresolved.add((source_path, reference, kind, "target_not_in_snapshot"))
    else:
        edges.add((source_path, target, kind))


def _dynamic_import_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    function_names = {"import_module"}
    module_names = {"importlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    function_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    module_names.add(alias.asname or alias.name)
    return function_names, module_names


def _dynamic_reference(
    node: ast.Call,
    function_names: set[str],
    module_names: set[str],
) -> str | None:
    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
        if (
            node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            return node.args[0].value
        return "<dynamic>"
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in module_names
        and node.args
    ):
        if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            return node.args[0].value
        return "<dynamic>"
    if isinstance(node.func, ast.Name) and node.func.id in function_names and node.args:
        if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            return node.args[0].value
        return "<dynamic>"
    return None
