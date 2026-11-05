"""Pure source-position checks. Finding a source is not proof of a claim."""

from pydantic import TypeAdapter

from smartregression.contracts.models import Text
from smartregression.contracts.stages import StageEvidence
from smartregression.core.impact.python_snapshot import MAX_PYTHON_SOURCE_BYTES, inspect_python


def source_lines(source: str) -> list[str]:
    """Python universal newlines, without treating Unicode separators as line breaks."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return lines[:-1] if lines[-1] == "" else lines


def resolve_source(item: StageEvidence, raw: bytes | None) -> StageEvidence:
    resolution, reason = "resolved", "source_span_verified"
    if raw is None:
        resolution, reason = "missing", "evidence_path_missing"
    elif len(raw) > MAX_PYTHON_SOURCE_BYTES or b"\0" in raw:
        resolution, reason = "unverified", "evidence_source_unsupported"
    else:
        try:
            source = raw.decode("utf-8", errors="strict")
            lines = source_lines(source)
            start, end = item.location.line_start, item.location.line_end
            if end > len(lines):
                resolution, reason = "missing", "evidence_range_missing"
            elif (
                item.excerpt is not None
                and TypeAdapter(Text).validate_python("\n".join(lines[start - 1 : end]))
                != item.excerpt
            ):
                resolution, reason = "mismatched", "evidence_excerpt_mismatch"
            elif item.symbol is not None and not any(
                s.name == item.symbol and (s.start, s.end) == (start, end)
                for s in inspect_python(source).symbols
            ):
                resolution, reason = "mismatched", "evidence_symbol_mismatch"
        except UnicodeError, ValueError, RecursionError:
            resolution, reason = "unverified", "evidence_source_unsupported"
    return item.model_copy(
        update={
            "resolution": resolution,
            "support": "unverified",
            "verification_reason": reason,
        }
    )
