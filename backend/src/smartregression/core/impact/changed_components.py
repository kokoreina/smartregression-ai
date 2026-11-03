"""Snapshot-local textual change mapping. Source is parsed, never executed."""

from dataclasses import dataclass
from typing import Literal

from smartregression.core.impact.python_snapshot import Symbol, inspect_python

ChangeKind = Literal["added", "modified", "deleted", "renamed"]


@dataclass(frozen=True)
class Location:
    line_start: int
    line_end: int


@dataclass(frozen=True)
class ComponentChange:
    path: str
    previous_path: str | None
    kind: Literal["file", "module", "class", "function", "method"]
    symbol: str | None
    change: ChangeKind
    base_location: Location | None
    target_location: Location | None
    reason: str


def _inventory(source: str | None) -> dict[str, Symbol]:
    if source is None:
        return {}
    result = {}
    for symbol in inspect_python(source).symbols:
        if symbol.name in result:
            raise ValueError("ambiguous_symbol")
        result[symbol.name] = symbol
    return result


def _location(symbol: Symbol | None) -> Location | None:
    return Location(symbol.start, symbol.end) if symbol else None


def _text(lines: list[str], symbol: Symbol | None) -> tuple[str, ...] | None:
    if symbol is None:
        return None
    return tuple(lines[symbol.start - 1 : symbol.end])


def _children(inventory: dict[str, Symbol]) -> dict[str, list[Symbol]]:
    children: dict[str, list[Symbol]] = {}
    for name, symbol in inventory.items():
        owner = name.rpartition(".")[0]
        children.setdefault(owner, []).append(symbol)
    return children


def _own_text(lines: list[str], parent: Symbol, children: list[Symbol]) -> tuple[str, ...]:
    # Remove nested definitions to distinguish a container from a direct edit.
    nested_lines = set()
    for child in children:
        nested_lines.update(range(child.start, child.end + 1))
    return tuple(
        line
        for number, line in enumerate(lines[parent.start - 1 : parent.end], parent.start)
        if number not in nested_lines and line.strip()
    )


def _lines(source: str | None) -> list[str]:
    # AST counts Python physical newlines. str.splitlines also splits Unicode
    # separators inside string literals, shifting spans and hiding literal edits.
    if not source:
        return []
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _module_location(lines: list[str]) -> Location | None:
    return Location(1, len(lines)) if lines else None


def compare_python(
    base: str | None, target: str | None, *, path: str, previous_path: str | None = None
) -> tuple[ComponentChange, ...]:
    """Map direct source edits, retaining old/new locations relative to the commit pair.

    None denotes an absent file, distinct from an empty file. Pure symbol renames
    are delete+add. Repeated qualified names are ambiguous and reject this file.
    No module import, behavior/impact inference or source execution takes place.
    """
    old, new = _inventory(base), _inventory(target)
    old_lines, new_lines = _lines(base), _lines(target)
    old_children, new_children = _children(old), _children(new)
    if base == target and previous_path is None:
        return ()
    change: ChangeKind = "modified"
    if base is None:
        change = "added"
    elif target is None:
        change = "deleted"
    elif previous_path:
        change = "renamed"
    records = [
        ComponentChange(
            path,
            previous_path,
            "module",
            None,
            change,
            _module_location(old_lines),
            _module_location(new_lines),
            "path_changed" if base == target else "content_changed",
        )
    ]
    changed_names = {
        name
        for name in old.keys() | new.keys()
        if name not in old
        or name not in new
        or old[name].kind != new[name].kind
        or _text(old_lines, old[name]) != _text(new_lines, new[name])
    }
    for name in sorted(changed_names):
        before, after = old.get(name), new.get(name)
        change = "modified"
        reason = "content_changed"
        if before is None:
            change, reason = "added", "symbol_added"
        elif after is None:
            change, reason = "deleted", "symbol_deleted"
        elif (
            before.kind == after.kind
            and any(
                child.name in changed_names
                for child in old_children.get(name, []) + new_children.get(name, [])
            )
            and _own_text(old_lines, before, old_children.get(name, []))
            == _own_text(new_lines, after, new_children.get(name, []))
        ):
            reason = "contains_changed_symbol"
        symbol = after if after is not None else before
        records.append(
            ComponentChange(
                path,
                previous_path,
                symbol.kind,
                name,
                change,
                _location(before),
                _location(after),
                reason,
            )
        )
    return tuple(records)
