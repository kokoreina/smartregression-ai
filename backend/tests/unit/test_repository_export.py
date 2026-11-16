"""Offline report transport preserves AI and provenance, without provider calls."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from smartregression.contracts.repository import RepositoryAnalysisResponse, RepositoryReportExport


def response():
    report = json.loads(
        (
            Path(__file__).resolve().parents[3] / "examples/reports/stage-report.partial.json"
        ).read_text("utf-8")
    )
    return RepositoryAnalysisResponse.model_validate(
        dict(
            repository=dict(
                schema_version="1.0.0",
                repository_url="https://github.com/owner/repo",
                full_name="owner/repo",
                default_branch="main",
                commits=[],
            ),
            files=["app.py"],
            report=report,
            narrative=dict(
                status="completed",
                model="recorded-model",
                data=dict(
                    summary="Recorded explanation",
                    findings=[
                        dict(
                            path="app.py", explanation="Potential impact", evidence_ids=["change-0"]
                        )
                    ],
                    limitations=[],
                ),
            ),
            narrative_evidence=[dict(id="change-0", path="app.py")],
            limitations=["No execution"],
        )
    )


def test_export_round_trip_preserves_full_narrative_and_identity():
    original = response()
    exported = RepositoryReportExport(exported_at="2026-11-15T12:00:00Z", payload=original)
    restored = RepositoryReportExport.model_validate_json(exported.model_dump_json())
    assert restored.payload == original
    assert restored.payload.narrative.data.findings[0].evidence_ids == ["change-0"]
    assert restored.payload.execution_status == "not_run"


@pytest.mark.parametrize("timestamp", ["2026-11-15T12:00:00", "not-a-date"])
def test_export_requires_timezone_aware_export_time(timestamp):
    with pytest.raises(ValidationError):
        RepositoryReportExport(exported_at=timestamp, payload=response())


def test_export_rejects_wrong_version_and_broken_citation():
    value = RepositoryReportExport(
        exported_at="2026-11-15T12:00:00Z", payload=response()
    ).model_dump(mode="json")
    value["schema_version"] = "future"
    with pytest.raises(ValidationError):
        RepositoryReportExport.model_validate(value)
    value["schema_version"] = "1.0.0"
    value["payload"]["narrative"]["data"]["findings"][0]["evidence_ids"] = ["invented"]
    with pytest.raises(ValidationError):
        RepositoryReportExport.model_validate(value)


def test_real_report_must_match_repository_provenance():
    value = response().model_dump(mode="json")
    value["report"]["data_kind"] = "real"
    repository_id = "github-" + hashlib.sha256(b"owner/repo").hexdigest()

    def bind(data):
        if isinstance(data, dict):
            for key, item in data.items():
                if key == "repository_id":
                    data[key] = repository_id
                else:
                    bind(item)
        elif isinstance(data, list):
            for item in data:
                bind(item)

    bind(value["report"])
    assert RepositoryAnalysisResponse.model_validate(value).report.data_kind == "real"
    value["repository"]["repository_url"] = "https://github.com/other/repo"
    value["repository"]["full_name"] = "other/repo"
    with pytest.raises(ValidationError, match="repository_identity_mismatch"):
        RepositoryAnalysisResponse.model_validate(value)


@pytest.mark.parametrize(
    "status,extra",
    [
        ("completed", {"reason": "disabled"}),
        ("not_run", {"error_code": "provider_quota"}),
        ("failed", {"error_code": "provider_timeout", "reason": "disabled"}),
    ],
)
def test_conflicting_ai_states_are_rejected(status, extra):
    value = response().model_dump(mode="json")
    value["narrative"]["status"] = status
    if status != "completed":
        value["narrative"]["data"] = None
    value["narrative"].update(extra)
    with pytest.raises(ValidationError):
        RepositoryAnalysisResponse.model_validate(value)
