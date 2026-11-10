"""Backend-only explicit credential selection. No dotenv discovery."""

import hmac
from collections.abc import Mapping
from dataclasses import dataclass, field


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
