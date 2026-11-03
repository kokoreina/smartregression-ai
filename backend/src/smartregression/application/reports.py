"""Shared report validation used by entrypoints; no analysis or execution."""

from pydantic import TypeAdapter

from smartregression.contracts.models import AnalysisReport
from smartregression.contracts.stages import StageAnalysisReport

_REPORT = TypeAdapter(AnalysisReport | StageAnalysisReport)


def validate_report_json(content: str) -> AnalysisReport | StageAnalysisReport:
    """Version literals and forbidden extra fields reject ambiguous documents.

    Omitted version remains accepted only by the unchanged legacy contract.
    No source access, authorization or evidence verification occurs here.
    """
    return _REPORT.validate_json(content)
