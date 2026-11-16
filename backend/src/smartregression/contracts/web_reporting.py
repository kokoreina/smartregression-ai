"""A persisted report view freezes summary, drill-down and export together."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from smartregression.contracts.repository import WebValue


class ReportFilter(WebValue):
    project_id: UUID | None = None
    start: AwareDatetime
    end: AwareDatetime
    as_of: AwareDatetime
    timezone: str
    status: Literal["queued", "running", "completed", "failed", "interrupted"] | None = None


class DashboardQuery(WebValue):
    project_id: UUID | None = None
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None
    timezone: str = Field(default="UTC", max_length=80)
    status: Literal["queued", "running", "completed", "failed", "interrupted"] | None = None


class Dashboard(WebValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    snapshot_id: UUID
    filters: ReportFilter
    expires_at: AwareDatetime
    total_runs: int
    project_count: int
    static_statuses: dict[str, int]
    ai_statuses: dict[str, int]
    daily_runs: dict[str, int]
    known_actual_micro_usd: int | None
    unknown_actual_count: int
    reservation_micro_usd: int
    stored_rows: int
    export_limit: int = 10000
    limitations: list[str]


class UsageRecord(WebValue):
    id: UUID
    project_id: UUID
    run_id: UUID | None
    action: str
    status: str
    created_at: AwareDatetime
    reservation_micro_usd: int
    actual_micro_usd: int | None


class UsagePage(WebValue):
    items: list[UsageRecord]
    next_cursor: str | None = None
