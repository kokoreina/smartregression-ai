"""Consent must be enforced before any data access, reservation, or provider call."""

import pytest

from smartregression.application.auth import AuthFailure
from smartregression.application.web_ai import WebAiService
from smartregression.contracts.web_runs import AiRequest


def test_missing_consent_never_calls_other_boundaries():
    def forbidden(*args):
        raise AssertionError("Boundary called without consent")

    service = WebAiService(None, forbidden, forbidden)
    with pytest.raises(AuthFailure, match="metadata_egress_consent_required"):
        service.create("owner", "project", "run", AiRequest(idempotency_key="request-1"))
