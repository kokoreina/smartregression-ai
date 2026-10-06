import pytest
from pydantic import ValidationError

from smartregression.contracts.models import AnalysisReport


def test_demo_is_explicit_and_measurements_unknown(demo_data: dict) -> None:
    report = AnalysisReport.model_validate(demo_data)
    assert report.data_kind == "demo"
    assert report.analysis_status == "not_implemented"
    assert report.execution_status == "not_run"
    assert report.execution_results == []
    assert report.analysis_duration_seconds is None
    assert report.llm_cost_usd is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("schema_version", "2.0.0"), ("data_kind", "unknown"), ("llm_cost_usd", -1)],
)
def test_invalid_fields(demo_data: dict, field: str, value: object) -> None:
    demo_data[field] = value
    with pytest.raises(ValidationError):
        AnalysisReport.model_validate(demo_data)


@pytest.mark.parametrize("case", ["lines", "commit", "reference", "duplicate", "execution"])
def test_semantic_consistency(demo_data: dict, case: str) -> None:
    match case:
        case "lines":
            demo_data["evidence"][0]["line_end"] = 1
        case "commit":
            demo_data["evidence"][0]["commit"] = "a" * 40
        case "reference":
            demo_data["findings"][0]["evidence_ids"] = ["missing"]
        case "duplicate":
            demo_data["selection"]["skipped"] = demo_data["selection"]["selected"]
        case "execution":
            demo_data["execution_status"] = "completed"
    with pytest.raises(ValidationError):
        AnalysisReport.model_validate(demo_data)


def test_test_failure_is_not_a_fault_label(demo_data: dict) -> None:
    demo_data["execution_status"] = "completed"
    result = {
        "test_id": demo_data["selection"]["selected"][0]["test_id"],
        "outcome": "failed",
    }
    demo_data["execution_results"] = [result]
    assert AnalysisReport.model_validate(demo_data).execution_results[0].outcome == "failed"
    result["fault_detected"] = True
    with pytest.raises(ValidationError):
        AnalysisReport.model_validate(demo_data)
