"""Provider-neutral proposal boundary; neither selection nor execution authority."""

from typing import Protocol

from smartregression.contracts.workflow import ProposalRequest, ProviderResult


class ProposalProvider(Protocol):
    def propose(self, request: ProposalRequest) -> ProviderResult:
        """Return a typed outcome; do not retry or execute model-generated commands."""
        ...
