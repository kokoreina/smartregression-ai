"""Bounded lexical/name resolution; no type inference, dependency loading or execution."""

import builtins
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass

from smartregression.contracts.explorer import ExplorerNode
from smartregression.core.explorer.parsing import ImportFact, ParsedFile

BUILTINS = frozenset(name for name in dir(builtins) if not name.startswith("_"))
STDLIB = frozenset(sys.stdlib_module_names)


@dataclass(frozen=True)
class Resolution:
    kind: str
    path: str = ""
    name: str = ""


class PythonResolver:
    def __init__(
        self,
        parsed: Mapping[str, ParsedFile],
        symbols: Mapping[tuple[str, str], ExplorerNode],
        resolve: Callable[[str, str, set[str]], str | None],
        known_paths: Iterable[str] = (),
    ) -> None:
        self.parsed, self.symbols, self.resolve = parsed, symbols, resolve
        self.files = set(parsed)
        self.bindings: dict[tuple[str, str, str], tuple[ImportFact, str]] = {}
        self.local_roots = {
            p.split("/")[0].removesuffix(".py")
            for p in self.files | set(known_paths)
            if p.endswith(".py")
        }
        for path, facts in parsed.items():
            if not path.endswith(".py"):
                continue
            for item in facts.imports:
                for local, exported in item.bindings:
                    self.bindings[path, item.scope or "", local] = (item, exported)

    def stdlib(self, reference: str) -> bool:
        root = reference.split(".")[0]
        return bool(root and root in STDLIB and root not in self.local_roots)

    def scopes(self, path: str, scope: str) -> Iterator[str]:
        facts = self.parsed[path]
        yield scope
        while scope:
            scope = facts.scope_parents.get(scope, "")
            if facts.scope_kinds.get(scope) != "class":
                yield scope

    def declared(self, path: str, name: str) -> bool:
        facts = self.parsed[path]
        return (
            (path, "", name) in self.bindings
            or name in facts.shadowed.get("", set())
            or "*" in facts.shadowed.get("", set())
            or any(symbol.name == name for symbol in facts.symbols)
        )

    def lookup(
        self,
        path: str,
        scope: str,
        name: str,
        seen: frozenset[tuple[str, str, str]] = frozenset(),
        allow_builtin: bool = True,
    ) -> Resolution:
        key = (path, scope, name)
        if key in seen or len(seen) >= 32:
            return Resolution("unknown")
        seen = seen | {key}
        facts = self.parsed[path]
        if facts.syntax_error:
            return Resolution("unknown")
        for current in self.scopes(path, scope):
            if name in facts.shadowed.get(current, set()) or "*" in facts.shadowed.get(
                current, set()
            ):
                return Resolution("shadowed")
            candidate = (current + "." if current else "") + name
            if (path, candidate) in self.symbols:
                return Resolution("symbol", path, candidate)
            binding = self.bindings.get((path, current, name))
            if binding:
                item, exported = binding
                return self.import_binding(path, item, name, exported, seen)
        if allow_builtin and name in BUILTINS:
            return Resolution("builtin", "", name)
        return Resolution("unknown")

    def import_binding(
        self,
        path: str,
        item: ImportFact,
        name: str,
        exported: str,
        seen: frozenset[tuple[str, str, str]] = frozenset(),
    ) -> Resolution:
        """Resolve the import itself, independently of later local rebinding."""
        destination = self.resolve(path, item.reference, self.files)
        # A package importing its own child must not recurse into this binding.
        self_binding = destination == path and not item.scope and exported == name
        if (
            destination
            and exported != "*"
            and not self_binding
            and self.declared(destination, exported)
        ):
            resolved = self.lookup(destination, "", exported, seen, allow_builtin=False)
            return (
                Resolution("module", resolved.path, ".".join([name, *resolved.name.split(".")[1:]]))
                if resolved.kind == "module"
                else resolved
            )
        if exported != "*":
            suffix = "" if item.reference.endswith(".") else "."
            module = self.resolve(path, item.reference + suffix + exported, self.files)
            if module:
                return Resolution("module", module, name)
        if destination:
            if exported == "*":
                return Resolution("module", destination, item.module_name or name)
            return self.lookup(destination, "", exported, seen, allow_builtin=False)
        if self.stdlib(item.reference):
            return Resolution("stdlib", "", item.reference)
        return Resolution("unknown")

    def call(self, path: str, scope: str | None, expression: str) -> Resolution:
        root, *members = expression.split(".")
        resolved = self.lookup(path, scope or "", root)
        if not members or resolved.kind in {"unknown", "shadowed", "stdlib"}:
            return resolved
        if resolved.kind == "module":
            prefix = resolved.name.split(".")
            remaining = expression.split(".")[len(prefix) :]
            if expression.split(".")[: len(prefix)] != prefix or not remaining:
                return Resolution("unknown")
            current = self.lookup(resolved.path, "", remaining[0], allow_builtin=False)
            for member in remaining[1:]:
                if current.kind == "module":
                    current = self.lookup(current.path, "", member, allow_builtin=False)
                elif current.kind == "symbol":
                    if self.symbols[current.path, current.name].kind != "class":
                        return Resolution("unknown")
                    symbol = current.name + "." + member
                    current = (
                        Resolution("symbol", current.path, symbol)
                        if (
                            (current.path, symbol) in self.symbols
                            and member
                            not in self.parsed[current.path].shadowed.get(current.name, set())
                        )
                        else Resolution("unknown")
                    )
                else:
                    return Resolution("unknown")
            return current
        if resolved.kind == "symbol":
            if self.symbols[resolved.path, resolved.name].kind != "class":
                return Resolution("unknown")
            candidate = resolved.name + "." + ".".join(members)
            if (resolved.path, candidate) in self.symbols and members[0] not in self.parsed[
                resolved.path
            ].shadowed.get(resolved.name, set()):
                return Resolution("symbol", resolved.path, candidate)
        return Resolution("unknown")
