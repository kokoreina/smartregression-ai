"""Parser-neutral facts; adapters may parse syntax but never execute repository code."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SymbolFact:
    name: str
    kind: str
    start: int
    end: int


@dataclass(frozen=True)
class ImportFact:
    reference: str
    line: int
    bindings: tuple[tuple[str, str], ...] = ()
    scope: str | None = None
    module_name: str | None = None


@dataclass(frozen=True)
class CallFact:
    caller: str | None
    expression: str
    line: int


@dataclass
class ParsedFile:
    symbols: list[SymbolFact] = field(default_factory=list)
    imports: list[ImportFact] = field(default_factory=list)
    calls: list[CallFact] = field(default_factory=list)
    exports: dict[str, str] = field(default_factory=dict)
    issues: list[tuple[str, int]] = field(default_factory=list)
    syntax_error: bool = False
    shadowed: dict[str, set[str]] = field(default_factory=dict)
    scope_parents: dict[str, str] = field(default_factory=dict)
    scope_kinds: dict[str, str] = field(default_factory=dict)
