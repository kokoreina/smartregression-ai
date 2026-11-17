"""Tree-sitter JavaScript syntax adapter. No JS runtime, eval, or candidate install."""

import tree_sitter_javascript
from tree_sitter import Language, Parser

from smartregression.core.explorer.parsing import CallFact, ImportFact, ParsedFile, SymbolFact


def parse_javascript(source: str) -> ParsedFile:
    raw = source.encode("utf-8")
    if len(raw) > 256000:
        raise ValueError("source_limit")
    parser = Parser(Language(tree_sitter_javascript.language()))
    tree = parser.parse(raw)
    result = ParsedFile(syntax_error=tree.root_node.has_error)

    def text(node):
        return raw[node.start_byte : node.end_byte].decode("utf-8") if node else ""

    def literal(node):
        if node is None or node.type != "string":
            return None
        content = text(node)
        if len(content) < 2 or "\\" in content[1:-1]:
            return None
        return content[1:-1]

    def walk(node, scope=None, in_class=False):
        line = node.start_point.row + 1
        next_scope = scope
        if node.type in {"function_declaration", "class_declaration", "method_definition"}:
            name = text(node.child_by_field_name("name"))
            if name:
                qualified = (scope + "." if scope else "") + name
                kind = (
                    "class"
                    if node.type == "class_declaration"
                    else "method"
                    if node.type == "method_definition"
                    else "function"
                )
                result.symbols.append(SymbolFact(qualified, kind, line, node.end_point.row + 1))
                next_scope = qualified
                parameters = node.child_by_field_name("parameters")
                shadow = set()

                def identifiers(part):
                    if part.type in {"identifier", "shorthand_property_identifier_pattern"}:
                        shadow.add(text(part))
                    for child in part.named_children:
                        identifiers(child)

                if parameters:
                    identifiers(parameters)
                body = node.child_by_field_name("body")

                def local_bindings(part):
                    if part.type in {
                        "function_declaration",
                        "function_expression",
                        "arrow_function",
                        "class_declaration",
                    }:
                        return
                    if part.type == "variable_declarator":
                        name_node = part.child_by_field_name("name")
                        if name_node:
                            identifiers(name_node)
                    for child in part.named_children:
                        local_bindings(child)

                if body:
                    local_bindings(body)
                result.shadowed[qualified] = shadow
                if node.parent and node.parent.type == "export_statement":
                    result.exports[
                        "default" if "default" in text(node.parent).split()[:2] else name
                    ] = qualified
        if node.type in {"arrow_function", "function_expression"}:
            named_parent = node.parent and node.parent.type in {
                "variable_declarator",
                "assignment_expression",
            }
            next_scope = scope if named_parent else (scope or "") + f".$anonymous{line}"
            shadow = set()

            def parameters(part):
                if part.type in {"identifier", "shorthand_property_identifier_pattern"}:
                    shadow.add(text(part))
                for child in part.named_children:
                    parameters(child)

            argument_node = node.child_by_field_name("parameters") or node.child_by_field_name(
                "parameter"
            )
            if argument_node:
                parameters(argument_node)
            result.shadowed[next_scope or ""] = shadow
        if node.type == "variable_declarator":
            name = text(node.child_by_field_name("name"))
            value = node.child_by_field_name("value")
            if (
                value
                and value.type in {"arrow_function", "function_expression"}
                and node.child_by_field_name("name").type == "identifier"
            ):
                qualified = (scope + "." if scope else "") + name
                result.symbols.append(
                    SymbolFact(qualified, "function", line, node.end_point.row + 1)
                )
                next_scope = qualified
                if (
                    node.parent
                    and node.parent.parent
                    and node.parent.parent.type == "export_statement"
                ):
                    result.exports[name] = qualified
            if (
                value
                and value.type == "call_expression"
                and text(value.child_by_field_name("function")) == "require"
            ):
                args = value.child_by_field_name("arguments")
                reference = (
                    literal(args.named_children[0])
                    if args and len(args.named_children) == 1
                    else None
                )
                if reference:
                    if node.child_by_field_name("name").type == "identifier":
                        bindings = ((name, "*"),)
                    else:
                        bindings = tuple(
                            (text(c), text(c))
                            for c in node.child_by_field_name("name").named_children
                            if c.type == "shorthand_property_identifier_pattern"
                        )
                    result.imports.append(ImportFact(reference, line, bindings))
                else:
                    result.issues.append(("dynamic_require", line))
        if node.type in {"import_statement", "export_statement"}:
            reference = literal(node.child_by_field_name("source"))
            if reference:
                bindings = []

                def collect(part):
                    if part.type == "import_specifier":
                        name = text(part.child_by_field_name("name"))
                        alias = text(part.child_by_field_name("alias")) or name
                        bindings.append((alias, name))
                        return
                    if part.type == "namespace_import":
                        names = [c for c in part.named_children if c.type == "identifier"]
                        if names:
                            bindings.append((text(names[-1]), "*"))
                        return
                    if (
                        part.type == "identifier"
                        and part.parent
                        and part.parent.type == "import_clause"
                    ):
                        bindings.append((text(part), "default"))
                        return
                    for child in part.named_children:
                        collect(child)

                collect(node)
                result.imports.append(ImportFact(reference, line, tuple(bindings)))
        if node.type == "export_statement" and node.child_by_field_name("source") is None:
            for clause in node.named_children:
                if clause.type == "export_clause":
                    for spec in clause.named_children:
                        name = text(spec.child_by_field_name("name"))
                        alias = text(spec.child_by_field_name("alias")) or name
                        if name:
                            result.exports[alias] = name
        if node.type == "assignment_expression":
            left = text(node.child_by_field_name("left"))
            right = node.child_by_field_name("right")
            if left.startswith(("exports.", "module.exports.")):
                exported = left.split(".")[-1]
                if right and right.type == "identifier":
                    result.exports[exported] = text(right)
                elif right and right.type in {"function_expression", "arrow_function"}:
                    result.symbols.append(
                        SymbolFact(exported, "function", line, node.end_point.row + 1)
                    )
                    result.exports[exported] = exported
                    next_scope = exported
            elif left == "module.exports" and right and right.type == "object":
                for member in right.named_children:
                    if member.type == "shorthand_property_identifier":
                        result.exports[text(member)] = text(member)
                    elif member.type == "pair":
                        key = member.child_by_field_name("key")
                        value = member.child_by_field_name("value")
                        if key and value and value.type == "identifier":
                            result.exports[text(key)] = text(value)
        if node.type == "call_expression":
            function = node.child_by_field_name("function")
            expression = text(function)
            if expression not in {"require", "import"}:
                if function and (
                    function.type == "identifier"
                    or function.type == "member_expression"
                    and function.child_by_field_name("property")
                    and function.child_by_field_name("property").type == "property_identifier"
                ):
                    result.calls.append(CallFact(scope, expression, line))
                else:
                    result.issues.append(("dynamic_call", line))
            elif expression == "import":
                result.issues.append(("dynamic_import", line))
        if node.type in {"ERROR", "jsx_element", "jsx_self_closing_element"}:
            result.issues.append(("unsupported_syntax", line))
        for child in node.named_children:
            walk(child, next_scope, node.type == "class_declaration")

    walk(tree.root_node)
    if result.syntax_error:
        result.issues.append(("javascript_parse_error", 1))
    return result
