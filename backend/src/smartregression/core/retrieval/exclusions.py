"""Versioned conservative whole-file exclusions before index artifacts exist.

Recognized patterns are bounded safeguards, not a complete secret detector. Never
redact/normalize source bytes and then attribute the result to the original range.
"""

import re
import unicodedata
from pathlib import PurePosixPath

from smartregression.core.git.snapshots import validate_snapshot_paths

EXCLUSIONS_VERSION = "index-exclusions/1"
_FORBIDDEN = {
    ".git",
    ".ssh",
    ".aws",
    ".azure",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "secrets",
    "credentials",
}
_EVALUATION = re.compile(
    r"(?:^|[._/-])(?:fault[_-]?labels?|labels?|reference[_-]?outcomes?|"
    r"full[_-]?suite[_-]?(?:outcomes?|results?)|test[_-]?results?|results?|"
    r"evaluation|benchmarks?|coverage|junit)(?:$|[._/-])"
)
_OUTCOMES = re.compile(
    r"(?i)\b(?:fault[_-]?labels?|reference[_-]?outcomes?|full[_-]?suite[_-]?(?:outcomes?|results?))\b"
)
_SECRETS = re.compile(
    r"-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----|"
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b|"
    r"(?i:\b(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"authorization)\b[\s\"']{0,8}[:=]\s*[\"'][^\"'\r\n]{4,}[\"'])"
)


def exclusion_reason(path: str, content: bytes) -> str | None:
    """Return a safe reason only; the caller must not persist excluded content."""
    validate_snapshot_paths([path])
    folded = unicodedata.normalize("NFKC", path).casefold()
    parts = folded.split("/")
    if any(p in _FORBIDDEN or p.startswith(".env") for p in parts) or folded.endswith(
        (".pem", ".key", ".p12", ".pfx", ".keystore")
    ):
        return "forbidden_path"
    if _EVALUATION.search(folded):
        return "evaluation_data"
    suffix = PurePosixPath(folded).suffix
    docs = parts[0] in {"docs", "doc", "documentation"} or parts[-1].startswith("readme.")
    if suffix not in {".py", ".pyi", ".md", ".rst", ".txt"} or (
        suffix in {".md", ".rst", ".txt"} and not docs
    ):
        return "unsupported_path"
    if not isinstance(content, bytes) or b"\0" in content:
        return "unsupported_content"
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeError:
        return "unsupported_content"
    if _OUTCOMES.search(text):
        return "evaluation_content"
    if _SECRETS.search(text):
        return "recognized_secret"
    return None
