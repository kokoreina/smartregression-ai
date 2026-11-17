"""Static assistance must cite observed snapshot facts, without provider calls."""

import pytest

from smartregression.adapters.parsers.javascript import parse_javascript
from smartregression.core.explorer.assistance import reading_guide, search_features
from smartregression.core.explorer.graph import build_graph


def fixture():
    sources = {
        "package.json": '{"main":"app.js"}',
        "app.js": 'import {pay} from "./payment.js"; export function start(){return pay();}',
        "payment.js": "export function processPayment(){return 1;} // thanh toán",
        "tests/payment.js": 'import {processPayment} from "../payment.js";',
        ".env": "PASSWORD=not-a-real-secret",
    }
    graph = build_graph(
        "fixture", "a" * 40, {p: s for p, s in sources.items() if p != ".env"}, parse_javascript
    )
    return graph, sources


def test_reading_guide_entrypoint_is_config_evidenced_and_tests_are_observed():
    graph, sources = fixture()
    result = reading_guide(graph, sources)
    first = next(step for step in result.steps if step.category == "entrypoint")
    assert first.path == "app.js"
    assert first.evidence.path == "package.json"
    assert any(
        step.category == "tests" and step.path == "tests/payment.js" for step in result.steps
    )
    assert all(step.evidence.commit == graph.commit for step in result.steps)


def test_unknown_entrypoint_is_unknown_not_fabricated_from_filename():
    graph, sources = fixture()
    result = reading_guide(graph, {p: s for p, s in sources.items() if p != "package.json"})
    assert result.entrypoint_status == "unknown"
    assert not any(step.category == "entrypoint" for step in result.steps)


def test_search_vietnamese_accents_symbol_and_no_evidence():
    graph, sources = fixture()
    result = search_features(graph, sources, "thanh toan", 10)
    assert result.items[0].path == "payment.js"
    assert result.items[0].evidence.line_start == 1
    assert search_features(graph, sources, "processPayment", 1).items[0].path == "payment.js"
    assert search_features(graph, sources, "unfindablexyz", 10).status == "no_evidence"
    assert not search_features(graph, sources, "PASSWORD", 10).items


def test_search_bounds_and_exclusion():
    graph, sources = fixture()
    with pytest.raises(ValueError):
        search_features(graph, sources, "x" * 601, 10)
    with pytest.raises(ValueError):
        search_features(graph, sources, "payment", 11)
    sources["payment.js"] = 'const api_key="sk-' + "a" * 48 + '"; // thanh toán'
    assert not search_features(graph, sources, "thanh toan", 10).items


def test_scoped_ai_rejects_missing_consent_before_loading_or_reserving():
    from smartregression.application.assistance_ai import AssistanceAiService
    from smartregression.application.auth import AuthFailure
    from smartregression.contracts.ai_requests import AssistanceAiRequest

    service = AssistanceAiService(None, None, None, None)
    body = AssistanceAiRequest(
        commit="a" * 40, action="file", path="payment.js", idempotency_key="request-123"
    )
    with pytest.raises(AuthFailure, match="metadata_egress_consent_required"):
        service.create("owner", "project", body)
    body = body.model_copy(
        update={
            "allow_metadata_egress": True,
            "excerpts": [{"path": "payment.js", "start": 1, "end": 1}],
        }
    )
    with pytest.raises(AuthFailure, match="excerpt_egress_consent_required"):
        service.create("owner", "project", body)


def test_large_file_metadata_is_bounded_with_explicit_omissions_before_ai():
    import json
    from types import SimpleNamespace

    from smartregression.application.assistance_ai import AssistanceAiService
    from smartregression.contracts.ai_requests import AssistanceAiRequest

    sources = {
        "many.py": "\n".join(f"def function_{index}():\n    return {index}" for index in range(200))
    }
    graph = build_graph("fixture", "a" * 40, sources, parse_javascript)
    explorer = SimpleNamespace(read=lambda *args: (SimpleNamespace(graph=graph), sources))
    service = AssistanceAiService(None, explorer, None, None)
    context, scope = service.context(
        "owner",
        "project",
        AssistanceAiRequest(
            commit="a" * 40,
            action="file",
            path="many.py",
            idempotency_key="large-file-test",
            allow_metadata_egress=True,
        ),
    )
    assert len(json.dumps(context, ensure_ascii=True).encode()) <= 28000
    assert context["context"]["omitted_observation_count"] > 0
    assert any(o["kind"] == "file_metadata" for o in context["observations"])
    assert scope["provenance"]["context_hash"] == scope["hash"]


def test_folder_context_discloses_omitted_files_and_empty_folder_is_404():
    from types import SimpleNamespace

    from smartregression.application.assistance_ai import AssistanceAiService
    from smartregression.application.auth import AuthFailure
    from smartregression.contracts.ai_requests import AssistanceAiRequest

    sources = {f"folder/file{index}.js": "export function pay(){}" for index in range(12)}
    graph = build_graph("fixture", "a" * 40, sources, parse_javascript)
    explorer = SimpleNamespace(read=lambda *args: (SimpleNamespace(graph=graph), sources))
    service = AssistanceAiService(None, explorer, None, None)
    body = AssistanceAiRequest(
        commit="a" * 40, action="folder", path="folder", idempotency_key="folder-test"
    )
    context, _ = service.context("owner", "project", body)
    assert len(context["files"]) == 8 and context["context"]["omitted_file_count"] == 4
    assert set(context["context"]["included_files"]) == set(context["files"])
    with pytest.raises(AuthFailure, match="source_not_available"):
        service.context("owner", "project", body.model_copy(update={"path": "missing"}))


def test_excerpt_outside_selected_scope_is_rejected_before_source_access():
    from types import SimpleNamespace

    from smartregression.application.assistance_ai import AssistanceAiService
    from smartregression.application.auth import AuthFailure
    from smartregression.contracts.ai_requests import AssistanceAiRequest, ExcerptRange

    sources = {"payment.js": "export function pay(){}"}
    graph = build_graph("fixture", "a" * 40, sources, parse_javascript)
    explorer = SimpleNamespace(read=lambda *args: (SimpleNamespace(graph=graph), sources))
    service = AssistanceAiService(None, explorer, None, None)
    body = AssistanceAiRequest(
        commit="a" * 40,
        action="file",
        path="payment.js",
        idempotency_key="excerpt-test",
        allow_metadata_egress=True,
        allow_excerpt_egress=True,
        excerpts=[ExcerptRange(path=".env", start=1, end=1)],
    )
    with pytest.raises(AuthFailure, match="excerpt_scope_mismatch"):
        service.create("owner", "project", body)


def test_folder_generation_schema_binds_known_file_paths_and_evidence_ids():
    import json

    from smartregression.adapters.llm.repository_summary import (
        response_schema,
        validate_explanation,
    )

    payload = {
        "action": "folder",
        "files": ["engine/a.py", "engine/b.py"],
        "observations": [
            {"id": "proof-a", "path": "engine/a.py"},
            {"id": "proof-b", "path": "engine/b.py"},
        ],
    }
    schema = response_schema(payload)
    finding = schema["properties"]["findings"]["items"]["properties"]
    assert finding["path"]["enum"] == ["engine/a.py", "engine/b.py"]
    assert finding["evidence_ids"]["items"]["enum"] == ["proof-a", "proof-b"]
    with pytest.raises(ValueError):
        validate_explanation(
            json.dumps(
                {
                    "summary": "Folder",
                    "findings": [
                        {
                            "path": "engine/a.py",
                            "explanation": "Wrong evidence",
                            "evidence_ids": ["proof-b"],
                        }
                    ],
                    "limitations": [],
                }
            ),
            payload,
        )
