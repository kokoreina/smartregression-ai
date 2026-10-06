from fastapi import APIRouter

from smartregression.application.health import service_health
from smartregression.contracts.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return service_health()
