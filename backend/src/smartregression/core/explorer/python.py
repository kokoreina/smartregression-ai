"""Python syntax and lexical bindings; input is parsed, never imported or executed."""

import ast
from collections import Counter

from smartregression.core.explorer.parsing import CallFact, ImportFact, ParsedFile, SymbolFact
from smartregression.core.impact.python_snapshot import inspect_python


def _bindings(body, parameters=()):
    assigned = set(parameters)
    declared = Counter()

    def visit(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            declared[node.name] += 1
            return
        if isinstance(
            node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        ):
            if not isinstance(node, ast.Lambda):
                assigned.update(
                    child.target.id
                    for child in ast.walk(node)
                    if isinstance(child, ast.NamedExpr) and isinstance(child.target, ast.Name)
                )
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            assigned.add(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            expression = _expression(node)
            if expression:
                assigned.add(expression.split(".")[0])
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            assigned.update(node.names)
        if isinstance(node, ast.ExceptHandler) and node.name:
            assigned.add(node.name)
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            assigned.add(node.name)
        if isinstance(node, ast.MatchMapping) and node.rest:
            assigned.add(node.rest)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "exec"
        ):
            assigned.add("*")
        if isinstance(node, ast.Import):
            declared.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            declared.update(alias.asname or alias.name for alias in node.names)
            if any(alias.name == "*" for alias in node.names):
                assigned.add("*")
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in body:
        visit(statement)
    return assigned | {name for name, count in declared.items() if count > 1}


def _expression(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expression(node.value)
        return prefix + "." + node.attr if prefix else None
    return None


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
    result.scope_kinds[""] = "module"
    result.shadowed[""] = _bindings(tree.body)

    def walk(node, scope=""):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            qualified = (scope + "." if scope else "") + node.name
            result.scope_parents[qualified] = scope
            result.scope_kinds[qualified] = (
                "class" if isinstance(node, ast.ClassDef) else "function"
            )
            parameters = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parameters = [
                    a.arg
                    for a in [
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                        *([node.args.vararg] if node.args.vararg else []),
                        *([node.args.kwarg] if node.args.kwarg else []),
                    ]
                ]
                for default in [*node.args.defaults, *node.args.kw_defaults]:
                    if default is not None:
                        walk(default, scope)
            else:
                for base in [*node.bases, *(keyword.value for keyword in node.keywords)]:
                    walk(base, scope)
            result.shadowed[qualified] = _bindings(node.body, parameters)
            for decorator in node.decorator_list:
                walk(decorator, scope)
            for statement in node.body:
                walk(statement, qualified)
            return
        if isinstance(
            node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        ):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    result.issues.append(("unsupported_scope_call", child.lineno))
            return
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(
                    ImportFact(
                        alias.name,
                        node.lineno,
                        ((alias.asname or alias.name.split(".")[0], "*"),),
                        scope or None,
                        alias.name if not alias.asname else None,
                    )
                )
        if isinstance(node, ast.ImportFrom):
            ref = "." * node.level + (node.module or "")
            if any(alias.name == "*" for alias in node.names):
                result.issues.append(("wildcard_import", node.lineno))
            result.imports.append(
                ImportFact(
                    ref,
                    node.lineno,
                    tuple((a.asname or a.name, a.name) for a in node.names),
                    scope or None,
                )
            )
        if isinstance(node, ast.Call):
            expression = _expression(node.func)
            if expression:
                result.calls.append(CallFact(scope or None, expression, node.lineno))
            else:
                result.issues.append(("dynamic_or_shadowed_call", node.lineno))
        for child in ast.iter_child_nodes(node):
            walk(child, scope)

    walk(tree)
    return result
