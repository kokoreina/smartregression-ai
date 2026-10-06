"""API composition root. Demo data is a static frontend fixture, not an API result."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from smartregression.api.routes.health import router
from smartregression.contracts.models import ErrorResponse


def create_app() -> FastAPI:
    app = FastAPI(title="SmartRegression AI", version="0.1.0")
    app.include_router(router)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        error = ErrorResponse(code=f"http_{exc.status_code}", message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())

    return app


app = create_app()
