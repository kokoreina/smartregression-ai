"""Shared eligibility for web snapshot source and assistance; no source execution."""

from smartregression.core.retrieval.exclusions import exclusion_reason


def source_allowed(path: str, raw: bytes) -> bool:
    check = path[:-3] + ".py" if path.endswith(".js") else path
    if path.rsplit("/", 1)[-1] in {"pyproject.toml", "package.json", "setup.cfg"}:
        check = path.rsplit("/", 1)[0] + "/README.md" if "/" in path else "README.md"
    return exclusion_reason(check, raw) is None
