"""Shared report validation used by entrypoints; no analysis or execution."""

from smartregression.contracts.models import AnalysisReport


def validate_report_json(content: str) -> AnalysisReport:
    return AnalysisReport.model_validate_json(content)
