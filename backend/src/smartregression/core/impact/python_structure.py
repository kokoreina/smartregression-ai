"""AST-only dependency observations; does not claim complete dynamic call graphs."""

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    line_start: int
    line_end: int


@dataclass(frozen=True)
class PythonStructure:
    path: str
    symbols: tuple[Symbol, ...]
    imports: tuple[str, ...]
    calls: tuple[str, ...]
    limitations: tuple[str, ...]


def analyze_python(source: str, path: str) -> PythonStructure:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return PythonStructure(path, (), (), (), ("syntax_error",))
    symbols: list[Symbol] = []

    def visit(node: ast.AST, scope: str = "") -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = f"{scope}.{node.name}" if scope else node.name
            symbols.append(Symbol(scope, node.lineno, node.end_lineno or node.lineno))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree)
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, (ast.Name, ast.Attribute)):
                calls.add(ast.unparse(node.func))
    return PythonStructure(
        path,
        tuple(symbols),
        tuple(sorted(imports)),
        tuple(sorted(calls)),
        ("static_observations_only", "dynamic_dispatch_and_import_resolution_not_complete"),
    )
