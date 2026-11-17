"""Versioned portable exports preserve full run/scenario and AI provenance."""

from typing import Literal

from pydantic import AwareDatetime

from smartregression.contracts.ai_requests import AiJob
from smartregression.contracts.repository import WebValue
from smartregression.contracts.scenarios import Scenario
from smartregression.contracts.web_runs import SavedRunReport


class DurableRunExport(WebValue):
    report_kind: Literal["saved-web-run"] = "saved-web-run"
    schema_version: Literal["1.0.0"] = "1.0.0"
    exported_at: AwareDatetime
    payload: SavedRunReport
    ai_requests: list[AiJob]


class ScenarioExport(WebValue):
    report_kind: Literal["saved-scenario"] = "saved-scenario"
    schema_version: Literal["1.0.0"] = "1.0.0"
    exported_at: AwareDatetime
    payload: Scenario
    ai_requests: list[AiJob]
