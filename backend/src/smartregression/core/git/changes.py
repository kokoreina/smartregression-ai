"""Parse explicitly requested Git name-status output, preserving path identity."""

from pathlib import PurePosixPath

from smartregression.contracts.models import ChangedComponent


def validate_path(path: str) -> str:
    if (
        not path
        or path != path.strip()
        or "\\" in path
        or ":" in path
        or any(ord(char) < 32 for char in path)
        or path.startswith("/")
        or any(p in {"", ".", ".."} for p in path.split("/"))
        or PurePosixPath(path).is_absolute()
    ):
        raise ValueError("unsupported_path")
    return path


def parse_name_status(raw: bytes) -> tuple[ChangedComponent, ...]:
    if not raw:
        return ()
    try:
        fields = raw.decode("utf-8", errors="strict").split("\0")
    except UnicodeDecodeError as exc:
        raise ValueError("unsupported_path_encoding") from exc
    if fields.pop() != "":
        raise ValueError("invalid_diff_output")
    changes = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        rename = status.startswith("R") and status[1:].isdigit() and 0 <= int(status[1:]) <= 100
        if status not in {"A", "M", "D"} and not rename:
            raise ValueError("unsupported_change_type")
        count = 2 if rename else 1
        if index + count > len(fields):
            raise ValueError("invalid_diff_output")
        previous = validate_path(fields[index]) if rename else None
        path = validate_path(fields[index + count - 1])
        changes.append(
            ChangedComponent(
                path=path,
                previous_path=previous,
                change="renamed"
                if rename
                else {"A": "added", "M": "modified", "D": "deleted"}[status],
            )
        )
        index += count
    return tuple(changes)
