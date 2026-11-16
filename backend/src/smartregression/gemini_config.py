"""Backend-only explicit credential selection. No dotenv discovery."""

import hmac
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GeminiCredential:
    api_key: str = field(repr=False)

    @classmethod
    def from_environment(cls, env: Mapping[str, str]) -> GeminiCredential:
        primary = env.get("GEMINI_API_KEY", "")
        alias = env.get("GOOGLE_API_KEY", "")
        if not primary or not primary.strip():
            raise ValueError("missing_gemini_api_key")
        if primary != primary.strip():
            raise ValueError("invalid_gemini_api_key")
        if alias and not hmac.compare_digest(primary, alias):
            raise ValueError("conflicting_gemini_api_keys")
        return cls(primary)


def credential_environment(path: Path | None = None) -> dict[str, str]:
    """Read only explicitly selected backend credentials, never arbitrary dotenv discovery."""
    import os

    env = {k: os.environ[k] for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if k in os.environ}
    if path is None:
        return env
    if (
        any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))
        or path.stat().st_size > 65536
    ):
        raise ValueError("invalid_secret_file")
    values = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        key = key.strip()
        if key not in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}:
            continue
        if key in values:
            raise ValueError("duplicate_secret_configuration")
        values[key] = value.strip().strip("\"'")
    for key, value in values.items():
        if key in env and env[key] != value:
            raise ValueError("conflicting_secret_sources")
        env[key] = value
    return env
