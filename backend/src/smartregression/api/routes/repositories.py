"""Local web entrypoints. Public GitHub data only; no repository execution."""

from threading import Lock
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request

from smartregression.application.analysis import AnalysisError
from smartregression.application.repository_analysis import RepositoryService
from smartregression.contracts.repository import (
    RepositoryAnalysisRequest,
    RepositoryAnalysisResponse,
    RepositoryLookup,
    RepositoryOverview,
    RepositoryTree,
    RepositoryTreeRequest,
)


def repository_router(service: RepositoryService) -> APIRouter:
    router = APIRouter()
    busy = Lock()

    def check_origin(request: Request) -> None:
        if request.url.hostname not in {"localhost", "127.0.0.1", "testserver"}:
            raise HTTPException(403, "local_host_required")
        origin = request.headers.get("origin")
        if origin:
            try:
                parsed = urlsplit(origin)
                port = parsed.port
            except ValueError:
                raise HTTPException(403, "local_origin_required") from None
            if (
                parsed.scheme != "http"
                or parsed.hostname not in {"localhost", "127.0.0.1"}
                or port not in {5173, 8000}
            ):
                raise HTTPException(403, "local_origin_required")

    @router.post("/repositories/inspect", response_model=RepositoryOverview)
    def inspect_repository(body: RepositoryLookup, request: Request) -> RepositoryOverview:
        check_origin(request)
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "analysis_busy")
        try:
            return service.inspect(body.repository_url)
        except Exception:
            raise HTTPException(422, "github_lookup_failed_or_rate_limited") from None
        finally:
            busy.release()

    @router.post("/repositories/tree", response_model=RepositoryTree)
    def repository_tree(body: RepositoryTreeRequest, request: Request) -> RepositoryTree:
        check_origin(request)
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "analysis_busy")
        try:
            return service.tree(body)
        except ValueError as exc:
            safe = {
                "github_rate_limit",
                "github_timeout",
                "github_unavailable",
                "github_repository_or_commit_not_found",
                "github_redirect_rejected",
                "repository_tree_limit",
                "repository_tree_incomplete",
                "snapshot_mismatch",
            }
            code = str(exc)
            # _get also bounds the metadata JSON response at 2 MB.
            if code == "repository_limit":
                code = "repository_tree_limit"
            raise HTTPException(422, code if code in safe else "github_invalid_response") from None
        except KeyError, TypeError, AttributeError:
            raise HTTPException(422, "github_invalid_response") from None
        finally:
            busy.release()

    @router.post("/repository-analyses", response_model=RepositoryAnalysisResponse)
    def analyze_repository(
        body: RepositoryAnalysisRequest, request: Request
    ) -> RepositoryAnalysisResponse:
        check_origin(request)
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "analysis_busy")
        try:
            return service.analyze(body)
        except AnalysisError as exc:
            raise HTTPException(422, exc.code) from None
        except ValueError as exc:
            safe = {
                "github_rate_limit",
                "github_timeout",
                "repository_limit",
                "github_repository_or_commit_not_found",
                "unsupported_snapshot_entry",
                "sensitive_question",
                "snapshot_mismatch",
            }
            raise HTTPException(
                422, str(exc) if str(exc) in safe else "repository_analysis_failed"
            ) from None
        except Exception:
            raise HTTPException(500, "repository_analysis_internal_error") from None
        finally:
            busy.release()

    return router
