"""Offline-testable provider boundary, with no provider SDK or transport policy."""

from pydantic import ValidationError

from smartregression.contracts.workflow import (
    ProposalRequest,
    ProviderResult,
    validate_proposal_references,
)
from smartregression.core.selection.proposals import ProposalProvider


class ProposalBoundaryError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def request_proposal(provider: ProposalProvider, request: ProposalRequest) -> ProviderResult:
    """Check one adapter invocation; membership alone does not validate support.

    The caller owns authorized acquisition/egress and deadline/budget enforcement.
    No real adapter is wired until 3.04/3.16. Revalidate nested mutable values at
    both boundaries; frozen Pydantic values do not freeze their child lists.
    """
    try:
        request_bytes = request.model_dump_json()
        checked = ProposalRequest.model_validate_json(request_bytes)
    except ValidationError, AttributeError, ValueError:
        raise ProposalBoundaryError("invalid_proposal_request") from None
    try:
        result = provider.propose(checked)
        if not isinstance(result, ProviderResult):
            raise ProposalBoundaryError("invalid_provider_output")
        result = ProviderResult.model_validate_json(result.model_dump_json())
    except Exception:
        # Adapter implementations must classify expected transport failures. This
        # last boundary redacts unexpected raw exception/source/credential values.
        raise ProposalBoundaryError("invalid_provider_output") from None
    # The adapter receives a separate copy. A malicious/buggy adapter can mutate
    # child lists or bypass frozen fields; compare against the pre-call bytes.
    expected = ProposalRequest.model_validate_json(request_bytes)
    if result.provenance is not None and result.provenance != expected.provenance:
        raise ProposalBoundaryError("proposal_provenance_mismatch")
    try:
        validate_proposal_references(result, expected.inventory, expected.evidence)
    except ValueError as exc:
        raise ProposalBoundaryError(str(exc)) from None
    return result
