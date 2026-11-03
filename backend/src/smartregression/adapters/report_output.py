"""Publish complete UTF-8 JSON using an exclusive atomic link, never overwrite."""

import os
import tempfile
from pathlib import Path


def report_destination(output: Path, repository: Path) -> Path:
    source = repository.resolve(strict=True)
    absolute = output.absolute()
    parent = absolute.parent.resolve(strict=True)
    destination = parent / absolute.name
    if destination.resolve().is_relative_to(source):
        raise ValueError("output_inside_repository")
    # Refuse links/junctions in the output ancestry rather than following a
    # redirected path. Local parent directories must be controlled by the operator.
    if any(p.is_symlink() or p.is_junction() for p in (absolute, *absolute.parents)):
        raise ValueError("unsafe_output_path")
    if destination.exists():
        raise ValueError("output_exists")
    return destination


def write_report(output: Path, text: str, *, repository: Path) -> None:
    destination = report_destination(output, repository)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=".smartregression-",
            dir=destination.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Same-volume link is atomic and fails if another publisher got there first.
        # No rename/replace fallback: unsupported filesystems must fail visibly.
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise ValueError("output_exists") from exc
    finally:
        if temporary is not None:
            temporary.unlink()
