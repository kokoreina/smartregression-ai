"""Durable-run requests are distinct from canonical stage-report status."""

import pytest
from pydantic import ValidationError

from smartregression.contracts.web_runs import RunCreate


def test_run_creation_is_static_and_rejects_client_owner_or_short_sha():
    value = RunCreate(base="a" * 40, target="b" * 40, idempotency_key="test-request-1")
    assert value.base != value.target
    for extra in ({"owner_id": "spoof"}, {"use_llm": True}, {"target": "main"}):
        body = value.model_dump() | extra
        with pytest.raises(ValidationError):
            RunCreate.model_validate(body)
