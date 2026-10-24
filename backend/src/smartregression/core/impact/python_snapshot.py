"""Static Python AST observations only. Never imports/executes the input module."""

import ast
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    start: int
    end: int


@dataclass(frozen=True)
class PythonSnapshot:
    symbols: tuple[Symbol, ...]
    imports: tuple[str, ...]
    limitations: tuple[str, ...]


def inspect_python(source: str) -> PythonSnapshot:
    if len(source.encode("utf-8")) > 256_000:
        raise ValueError("source_limit")
    try:
        tree = ast.parse(source)
    except (SyntaxError, RecursionError, ValueError) as exc:
        raise ValueError("python_parse_failed") from exc
    symbols = []
    imports = set()
    limitations = {"import_observations_only_not_complete_dependency_graph"}

    def visit(node: ast.AST, scope: str = "") -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            name = scope + node.name
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            symbols.append(Symbol(name, start, node.end_lineno or node.lineno))
            scope = name + "."
        if isinstance(node, ast.Import):
            imports.update(n.name for n in node.names)
        if isinstance(node, ast.ImportFrom):
            if node.level:
                limitations.add("relative_import_unresolved")
            elif node.module:
                imports.add(node.module)
            if any(n.name == "*" for n in node.names):
                limitations.add("star_import")
        if isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
        ):
            limitations.add("dynamic_import")
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    try:
        visit(tree)
    except RecursionError as exc:
        raise ValueError("python_parse_failed") from exc
    return PythonSnapshot(tuple(symbols), tuple(sorted(imports)), tuple(sorted(limitations)))


def module_edges(sources: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    """Direct absolute module imports among supplied .py files only; not a call graph.

    Caller binds this closed fixture set to a snapshot. Missing/external/relative
    dependencies remain unknown, so these edges cannot justify skipping tests.
    """
    modules = {}
    for path in sources:
        if not path.endswith(".py"):
            raise ValueError("python_path_required")
        module = path[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        if module in modules:
            raise ValueError("ambiguous_module")
        modules[module] = path
    edges = set()
    for path, source in sources.items():
        for imported in inspect_python(source).imports:
            if imported in modules:
                edges.add((path, modules[imported]))
    return tuple(sorted(edges))


def changed_symbols(base: str, target: str) -> tuple[str, ...]:
    """Conservative text-span comparison; reports direct edits, not verified impact."""

    def spans(source: str) -> dict[str, str]:
        lines = source.splitlines()
        result = {}
        for symbol in inspect_python(source).symbols:
            if symbol.name in result:
                raise ValueError("ambiguous_symbol")
            result[symbol.name] = "\n".join(lines[symbol.start - 1 : symbol.end])
        return result

    old, new = spans(base), spans(target)
    return tuple(sorted(name for name in old.keys() | new.keys() if old.get(name) != new.get(name)))
