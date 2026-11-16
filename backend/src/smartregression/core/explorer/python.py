"""Reuse Python snapshot symbols, augment with bounded static call/import facts."""

import ast

from smartregression.core.explorer.parsing import CallFact, ImportFact, ParsedFile, SymbolFact
from smartregression.core.impact.python_snapshot import inspect_python


def parse_python(source: str) -> ParsedFile:
    result = ParsedFile()
    if len(source.encode()) > 256000:
        result.syntax_error = True
        result.issues.append(("source_limit", 1))
        return result
    try:
        observed = inspect_python(source)
        tree = ast.parse(source)
    except ValueError, SyntaxError, RecursionError:
        result.syntax_error = True
        result.issues.append(("python_parse_error", 1))
        return result
    result.symbols = [
        SymbolFact(item.name, item.kind, item.start, item.end) for item in observed.symbols
    ]
    result.exports = {s.name: s.name for s in result.symbols if "." not in s.name}

    def walk(node, scope=None, shadow=frozenset()):
        next_scope = scope
        local_shadow = shadow
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            next_scope = (scope + "." if scope else "") + node.name
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                local_shadow = frozenset(
                    arg.arg
                    for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                )
                local_shadow |= frozenset(
                    n.id
                    for n in ast.walk(node)
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(
                    ImportFact(
                        alias.name, node.lineno, ((alias.asname or alias.name.split(".")[0], "*"),)
                    )
                )
        if isinstance(node, ast.ImportFrom):
            ref = "." * node.level + (node.module or "")
            if node.module is None:
                for alias in node.names:
                    result.imports.append(
                        ImportFact(
                            ref + alias.name, node.lineno, ((alias.asname or alias.name, "*"),)
                        )
                    )
            else:
                result.imports.append(
                    ImportFact(
                        ref, node.lineno, tuple((a.asname or a.name, a.name) for a in node.names)
                    )
                )
        if isinstance(node, ast.Call):
            expression = None
            if isinstance(node.func, ast.Name) and node.func.id not in local_shadow:
                expression = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id not in local_shadow
            ):
                expression = node.func.value.id + "." + node.func.attr
            if expression:
                result.calls.append(CallFact(scope, expression, node.lineno))
            else:
                result.issues.append(("dynamic_or_shadowed_call", node.lineno))
        for child in ast.iter_child_nodes(node):
            walk(child, next_scope, local_shadow)

    walk(tree)
    return result
