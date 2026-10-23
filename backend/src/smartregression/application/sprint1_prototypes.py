"""Offline Sprint 1 spikes only; not public contracts or a real job service.

No network, credentials, repository execution, persistence or API wiring.
The injected transport returns synthetic HTTP status observations in tests.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal
from uuid import uuid4

State = Literal["queued", "running", "completed", "failed"]
Access = Literal["accessible", "unauthorized", "forbidden", "not_found_or_hidden", "service_error"]


def check_access(repository: str, transport: Callable[[str], int]) -> Access:
    """Classify observations, not authorization. Caller must allowlist repositories.

    Only owner/name is accepted. A 404 cannot distinguish missing from hidden.
    Unexpected transport exceptions propagate; never stringify them for consumers.
    """
    if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", repository):
        raise ValueError("invalid_repository")
    try:
        status = transport(repository)
    except TimeoutError, ConnectionError:
        return "service_error"
    return {
        200: "accessible",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found_or_hidden",
    }.get(status, "service_error")


@dataclass(frozen=True)
class Run:
    """Single-threaded immutable state exercise, not proof of pipeline completion.

    Creation always allocates a new ID; submission deduplication is unsupported.
    Terminal retries require a new run; same-state transitions are rejected.
    """

    run_id: str
    state: State
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failure_reason: str | None = None

    @classmethod
    def create(cls, at: datetime) -> Run:
        if at.utcoffset() is None:
            raise ValueError("timezone_required")
        return cls(str(uuid4()), "queued", at, at)

    def transition(self, state: State, at: datetime, reason: str | None = None) -> Run:
        allowed = {"queued": {"running", "failed"}, "running": {"completed", "failed"}}
        if state not in allowed.get(self.state, set()):
            raise ValueError("invalid_transition")
        if at.utcoffset() is None or at < self.updated_at:
            raise ValueError("invalid_timestamp")
        reasons = {"access_denied", "invalid_revision", "dependency_unavailable", "internal_error"}
        if (state == "failed" and reason not in reasons) or (state != "failed" and reason):
            raise ValueError("invalid_failure_reason")
        return replace(
            self,
            state=state,
            updated_at=at,
            failure_reason=reason,
            started_at=at if state == "running" else self.started_at,
            finished_at=at if state in {"completed", "failed"} else None,
        )
