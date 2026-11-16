"""Explicit, trusted server configuration. No file/network access on import."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


def web_environment():
    values = dict(os.environ)
    path = values.get("SMARTREGRESSION_WEB_ENV_FILE")
    if path:
        try:
            for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
                if not raw.strip() or raw.lstrip().startswith("#"):
                    continue
                key, value = raw.split("=", 1)
                key = key.strip()
                if not key.startswith("SMARTREGRESSION_"):
                    raise ValueError()
                values.setdefault(key, value.strip().strip('"').strip("'"))
        except OSError, ValueError:
            raise ValueError("web_configuration_required") from None
    return values


@dataclass(frozen=True)
class AuthSettings:
    frontend_origin: str
    csrf_secret: bytes = field(repr=False)
    local_http: bool = False

    def __post_init__(self):
        url = urlsplit(self.frontend_origin)
        if (
            len(self.csrf_secret) < 32
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path
            or not url.hostname
            or self.frontend_origin.endswith("/")
            or (
                self.local_http
                and (url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1"})
            )
            or (not self.local_http and url.scheme != "https")
        ):
            raise ValueError("web_configuration_required")
        try:
            port = url.port
            if port is not None and not 1 <= port <= 65535:
                raise ValueError()
        except ValueError:
            raise ValueError("web_configuration_required") from None

    @property
    def session_cookie(self):
        return "sr_dev_session" if self.local_http else "__Host-sr_session"

    @property
    def csrf_cookie(self):
        return "sr_dev_csrf" if self.local_http else "__Host-sr_csrf"

    @classmethod
    def load(cls, env):
        try:
            local = env.get("SMARTREGRESSION_AUTH_LOCAL_HTTP", "0")
            if local not in {"0", "1"}:
                raise ValueError()
            return cls(
                env["SMARTREGRESSION_FRONTEND_ORIGIN"],
                env["SMARTREGRESSION_CSRF_SECRET"].encode(),
                local == "1",
            )
        except KeyError, ValueError:
            raise ValueError("web_configuration_required") from None
