from smartregression.contracts.models import HealthResponse


def service_health() -> HealthResponse:
    """Report this process only; no dependency readiness is asserted."""
    return HealthResponse()
