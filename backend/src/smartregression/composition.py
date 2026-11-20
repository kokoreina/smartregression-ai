"""Local CLI composition; no Git/filesystem adapters leak into application logic."""

import re
from collections.abc import Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from smartregression.adapters.git_local import LocalGit
from smartregression.application.analysis import analyze_execution
from smartregression.application.inventory import InventoryCollector
from smartregression.application.inventory_store import prepare_inventory
from smartregression.application.mapping_artifact import MappingCollector, verify_mapping_artifact
from smartregression.application.persistence import bundle_from_report, persist_report
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.contracts.stages import StageAnalysisReport

if TYPE_CHECKING:
    from smartregression.adapters.llm.gemini import GeminiProvider, GeminiSettings
    from smartregression.application.repository_analysis import RepositoryService


def account_service(stack: ExitStack, *, required: bool = False):
    """Runtime-only wiring; no DB connection or credentials required for OpenAPI."""
    from smartregression.adapters.account_mail import GmailMailer
    from smartregression.adapters.auth_security import PasswordHasher, token_hash
    from smartregression.adapters.storage.auth_store import PostgresAuthStore
    from smartregression.adapters.storage.config import load_database_settings
    from smartregression.adapters.storage.connection import database_engine
    from smartregression.application.auth import AuthService
    from smartregression.auth_config import AuthSettings, web_environment

    env = web_environment()
    if not required and "SMARTREGRESSION_CSRF_SECRET" not in env:
        return None
    settings = AuthSettings.load(env)
    database = load_database_settings(env, allow_loopback_test=settings.local_http)
    engine = stack.enter_context(database_engine(database))
    mailer = GmailMailer(
        env.get("SMARTREGRESSION_SMTP_USERNAME", ""),
        env.get("SMARTREGRESSION_SMTP_PASSWORD", ""),
        settings.frontend_origin,
    )
    return AuthService(PostgresAuthStore(engine), PasswordHasher(), mailer, token_hash), settings


def personal_project_service(auth):
    from smartregression.adapters.storage.project_store import PostgresProjectStore
    from smartregression.application.projects import ProjectService

    repository = repository_web_service()
    return ProjectService(
        PostgresProjectStore(auth.store.engine), repository.inspect, repository.tree
    )


def durable_run_service(stack, auth):
    from sqlalchemy import text

    from smartregression.adapters.storage.config import load_database_settings
    from smartregression.adapters.storage.connection import database_engine
    from smartregression.adapters.storage.web_run_store import PostgresWebRunStore
    from smartregression.application.web_runs import WebRunService
    from smartregression.auth_config import web_environment

    settings = load_database_settings(web_environment(), allow_loopback_test=True)
    lease_engine = stack.enter_context(database_engine(settings))
    lease = stack.enter_context(lease_engine.connect())
    if not lease.scalar(text("SELECT pg_try_advisory_lock(741032)")):
        raise RuntimeError("single_product_backend_required")
    lease.commit()
    store = PostgresWebRunStore(auth.store.engine)
    store.interrupt()
    return WebRunService(store, published_repository_service(auth).analyze)


def published_repository_service(auth):
    from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
    from smartregression.adapters.storage.report_publication import ReportFiles

    root = Path(__file__).resolve().parents[3] / "var/web-reports"

    def publish(execution, repository):
        root.mkdir(parents=True, exist_ok=True)
        report = execution.report
        persist_report(
            ReportFiles(root, source_repository=repository),
            PostgresAnalysisStore(auth.store.engine, report),
            report=report,
            configuration=execution.configuration,
            snapshot_manifests=execution.snapshot_manifests,
            artifact_id=report.report_id,
            storage_key=f"{report.identity.run_id}/{report.report_id}.json",
            bundle=bundle_from_report(report),
        )

    return repository_web_service(publisher=publish)


def product_ai_service(auth, runs, *, recover=True):

    from smartregression.adapters.llm.budget import BudgetLedger
    from smartregression.adapters.llm.gemini import WEB_MODEL, GeminiSettings
    from smartregression.adapters.llm.repository_summary import GeminiRepositoryNarrator
    from smartregression.adapters.storage.web_ai_store import PostgresAiStore
    from smartregression.application.web_ai import WebAiService
    from smartregression.contracts.repository import NarrativeResult
    from smartregression.gemini_config import GeminiCredential, credential_environment

    def explain(context, identity, batch, campaign, *, model=None):
        try:
            if not re.fullmatch(r"[a-z0-9-]{1,80}", campaign) or batch not in {1, 2}:
                raise ValueError("invalid_ai_campaign")
            if model not in {None, WEB_MODEL, "gemini-3.5-flash-lite"}:
                raise ValueError("invalid_ai_model")
            from smartregression.auth_config import web_environment

            secret_file = web_environment().get("SMARTREGRESSION_GEMINI_ENV_FILE")
            credential = GeminiCredential.from_environment(
                credential_environment(Path(secret_file) if secret_file else None)
            )
            root = Path(__file__).resolve().parents[3] / "var/web-ai" / campaign
            if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
                raise ValueError("unsafe_workspace")
            root.mkdir(parents=True, exist_ok=True)
            transport = gemini_provider(
                api_key=credential.api_key,
                settings=GeminiSettings(model=model or WEB_MODEL, api_version="v1beta"),
            )
            narrator = GeminiRepositoryNarrator(
                transport,
                BudgetLedger(root / f"batch-{batch}.json", session_id=f"{campaign}-batch-{batch}"),
            )
            return narrator.explain(context, run_id=identity)
        except ValueError, OSError:
            return NarrativeResult(status="failed", error_code="provider_configuration")

    store = PostgresAiStore(auth.store.engine)
    if recover:
        store.interrupt()
    return WebAiService(store, runs.store.report, explain)


def product_scenario_service(auth, explorer):
    from smartregression.adapters.storage.scenario_store import PostgresScenarioStore
    from smartregression.application.scenarios import ScenarioService

    return ScenarioService(PostgresScenarioStore(auth.store.engine), explorer)


def product_reporting_service(auth):
    from smartregression.adapters.storage.web_reporting import PostgresWebReporting
    from smartregression.application.web_reporting import WebReportingService

    return WebReportingService(PostgresWebReporting(auth.store.engine))


def product_note_service(auth):
    from smartregression.adapters.storage.note_store import PostgresNoteStore
    from smartregression.application.notes import NoteService

    return NoteService(PostgresNoteStore(auth.store.engine))


def product_explorer_service(auth):
    from smartregression.adapters.parsers.javascript import parse_javascript
    from smartregression.adapters.storage.explorer_store import PostgresExplorerStore
    from smartregression.application.explorer import ExplorerService

    repository = repository_web_service()
    return ExplorerService(
        PostgresExplorerStore(auth.store.engine), repository.source_factory, parse_javascript
    )


def product_repo_assistant_service(auth, explorer, projects, ai):
    from smartregression.adapters.storage.assistant_store import PostgresAssistantStore
    from smartregression.application.repo_assistant import RepositoryAssistantService

    return RepositoryAssistantService(
        PostgresAssistantStore(auth.store.engine),
        explorer,
        projects,
        repository_web_service().source_factory,
        ai,
    )


def repository_web_service(*, publisher=None) -> RepositoryService:
    """Lazy local-web dependencies; no network or secret loading on application import."""
    from contextlib import contextmanager
    from tempfile import TemporaryDirectory

    import httpx

    from smartregression.adapters.github_repository import GithubRepository
    from smartregression.adapters.llm.budget import BudgetLedger
    from smartregression.adapters.llm.repository_summary import GeminiRepositoryNarrator
    from smartregression.application.repository_analysis import RepositoryService
    from smartregression.contracts.repository import NarrativeResult
    from smartregression.gemini_config import GeminiCredential, credential_environment

    root = Path(__file__).resolve().parents[3] / "var" / "web-analysis"

    @contextmanager
    def source_factory(url: str) -> Iterator[GithubRepository]:
        from smartregression.auth_config import web_environment

        root.mkdir(parents=True, exist_ok=True)
        if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
            raise ValueError("unsafe_workspace")
        with (
            TemporaryDirectory(dir=root) as workspace,
            httpx.Client(trust_env=False, follow_redirects=False, timeout=20) as client,
        ):
            yield GithubRepository(
                url,
                Path(workspace),
                client,
                token=web_environment().get("SMARTREGRESSION_GITHUB_TOKEN") or None,
            )

    class LazyNarrator:
        def explain(self, payload: dict, *, run_id: str) -> NarrativeResult:
            from smartregression.adapters.llm.gemini import WEB_MODEL, GeminiSettings

            try:
                from smartregression.auth_config import web_environment

                secret_file = web_environment().get("SMARTREGRESSION_GEMINI_ENV_FILE")
                credential = GeminiCredential.from_environment(
                    credential_environment(Path(secret_file) if secret_file else None)
                )
                root.mkdir(parents=True, exist_ok=True)
                transport = gemini_provider(
                    api_key=credential.api_key,
                    settings=GeminiSettings(model=WEB_MODEL, api_version="v1beta"),
                )
                return GeminiRepositoryNarrator(
                    transport,
                    BudgetLedger(root / "budget.json", session_id="web-repository-summary-v1"),
                ).explain(payload, run_id=run_id)
            except OSError, ValueError:
                return NarrativeResult(status="failed", error_code="provider_configuration")

    return RepositoryService(source_factory, LazyNarrator(), publisher=publisher)


def gemini_provider(*, api_key: str, settings: GeminiSettings | None = None) -> GeminiProvider:
    """Explicit opt-in factory. No key lookup or network request on import/creation."""
    from google import genai

    from smartregression.adapters.llm.gemini import GeminiProvider, GeminiSettings

    if not api_key or not api_key.strip():
        raise ValueError("missing_gemini_api_key")

    def client_factory(options: genai.types.HttpOptions) -> genai.Client:
        options.base_url = "https://generativelanguage.googleapis.com"
        options.client_args = {"trust_env": False}
        options.async_client_args = {"trust_env": False}
        return genai.Client(api_key=api_key, enterprise=False, http_options=options)

    return GeminiProvider(client_factory, settings or GeminiSettings())


def _candidate_collector(
    *,
    name: str,
    image: str | None,
    workspace: Path | None,
    repository: Path,
    repository_id: str,
    target: str,
) -> MappingCollector:
    from smartregression.adapters.runners.candidate_inventory import (
        CANDIDATES,
        CandidateInventoryCollector,
    )

    if (
        name not in CANDIDATES
        or repository_id != name
        or target != CANDIDATES[name][1]
        or image is None
        or re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None
        or workspace is None
    ):
        raise ValueError("invalid_inventory_arguments")
    if any(p.is_symlink() or p.is_junction() for p in (workspace, *workspace.parents)):
        raise ValueError("invalid_inventory_arguments")
    source, worker = repository.resolve(strict=True), workspace.resolve(strict=True)
    if worker.is_relative_to(source) or source.is_relative_to(worker) or not worker.is_dir():
        raise ValueError("invalid_inventory_arguments")
    # This opt-in runs the trusted observer shipped in the source checkout, never
    # scripts selected from the input repository. The collector hashes that observer.
    return CandidateInventoryCollector(name, image, Path(__file__).resolve().parents[3], worker)


def analyze_local(
    *,
    repository: Path,
    repository_id: str,
    authorized_root: Path,
    base: str,
    target: str,
    data_kind: Literal["demo", "real"],
    artifact_root: Path | None = None,
    inventory_collector: InventoryCollector | None = None,
    mapping_collector: MappingCollector | None = None,
    mapping_artifact_root: Path | None = None,
    inventory_candidate: str | None = None,
    inventory_image: str | None = None,
    inventory_workspace: Path | None = None,
    index_artifact_root: Path | None = None,
) -> StageAnalysisReport:
    if index_artifact_root is not None and artifact_root is None:
        raise ValueError("invalid_retrieval_arguments")
    if inventory_candidate is not None:
        if (
            inventory_collector is not None
            or mapping_collector is not None
            or (mapping_artifact_root is None and artifact_root is None)
        ):
            raise ValueError("invalid_inventory_arguments")
        mapping_collector = _candidate_collector(
            name=inventory_candidate,
            image=inventory_image,
            workspace=inventory_workspace,
            repository=repository,
            repository_id=repository_id,
            target=target,
        )
    elif (
        inventory_image is not None
        or inventory_workspace is not None
        or (mapping_artifact_root is not None and mapping_collector is None)
    ):
        raise ValueError("invalid_inventory_arguments")
    with ExitStack() as stack:
        source = (
            LocalGit(repository, cache_bytes=64 * 1024 * 1024)
            if index_artifact_root is not None
            else LocalGit(repository)
        )
        engine = None
        retrieval_store = None
        mapping_publisher = None
        if mapping_collector is not None:
            from smartregression.adapters.storage.report_publication import ReportFiles

            mapping_root = mapping_artifact_root or artifact_root
            if mapping_root is None:
                raise ValueError("mapping_artifact_root_required")
            mapping_publisher = ReportFiles(mapping_root, source_repository=source.repository)
        elif mapping_artifact_root is not None:
            raise ValueError("mapping_collector_required")
        if artifact_root is not None:
            # Keep CLI help/default analysis independent even of loading DB infrastructure.
            from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
            from smartregression.adapters.storage.config import load_database_settings
            from smartregression.adapters.storage.connection import database_engine
            from smartregression.adapters.storage.report_publication import ReportFiles

            settings = load_database_settings()
            publisher = ReportFiles(artifact_root, source_repository=source.repository)
            if index_artifact_root is not None:
                from smartregression.adapters.storage.index_artifacts import IndexArtifactFiles
                from smartregression.adapters.storage.index_store import PostgresIndexStore
                from smartregression.application.retrieval import PublishedLexicalIndex

                index_files = IndexArtifactFiles(
                    index_artifact_root, source_repository=source.repository
                )
                engine = stack.enter_context(database_engine(settings))
                retrieval_store = PublishedLexicalIndex(
                    source,
                    authorization=RepositoryAuthorization(repository_id, authorized_root),
                    store=PostgresIndexStore(engine),
                    artifacts=index_files,
                )
        execution = analyze_execution(
            source,
            authorization=RepositoryAuthorization(repository_id, authorized_root),
            repository_id=repository_id,
            base=base,
            target=target,
            data_kind=data_kind,
            inventory_collector=inventory_collector,
            mapping_collector=mapping_collector,
            retrieval_store=retrieval_store,
        )
        report = StageAnalysisReport.model_validate_json(execution.report.model_dump_json())
        inventory = None
        if artifact_root is not None and mapping_collector is not None:
            inventory = prepare_inventory(
                identity=report.identity,
                inventory_id=report.identity.run_id + "-inventory",
                stage=report.stages.inventory,
                configuration=mapping_collector.configuration,
            )
            if (
                inventory.configuration_sha256
                != execution.configuration.inventory_configuration_digest
            ):
                raise ValueError("mapping_configuration_mismatch")
        if mapping_publisher is not None:
            sidecar = execution.mapping_artifact
            if sidecar is None:
                from smartregression.application.run_store import RunMetadataError

                raise RunMetadataError()
            verify_mapping_artifact(sidecar.raw, expected=sidecar, report=report)
            # Same guarded immutable byte publisher; ReportFiles.read stays report-only.
            # Preserve this complete sidecar if subsequent report/DB publication fails.
            mapping_publisher.publish(sidecar.descriptor, sidecar.raw)
        if artifact_root is not None:
            if engine is None:
                engine = stack.enter_context(database_engine(settings))
            persist_report(
                publisher,
                PostgresAnalysisStore(engine, report, inventory=inventory),
                report=report,
                configuration=execution.configuration,
                snapshot_manifests=execution.snapshot_manifests,
                artifact_id=report.report_id,
                storage_key=f"{report.identity.run_id}/{report.report_id}.json",
                bundle=bundle_from_report(report),
            )
        return report
