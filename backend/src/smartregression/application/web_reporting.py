"""Shared filtering and portable exports; producer models remain the source."""

import csv
import io
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from smartregression.application.auth import AuthFailure
from smartregression.contracts.web_reporting import ReportFilter


def normalize_filter(project, start, end, status, timezone, now=None):
    now = now or datetime.now(UTC)
    try:
        ZoneInfo(timezone)
        end = end or now
        start = start or end - timedelta(days=30)
        if (
            not start.tzinfo
            or not end.tzinfo
            or start >= end
            or end > now
            or (end - start).days > 366
        ):
            raise ValueError("range")
        return ReportFilter(
            project_id=project, start=start, end=end, as_of=now, timezone=timezone, status=status
        )
    except ValueError, ZoneInfoNotFoundError, TypeError:
        raise AuthFailure("invalid_report_filter", 422) from None


def csv_text(rows):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    for row in rows:
        safe = []
        for value in row:
            cell = "" if value is None else str(value)
            if cell.lstrip().startswith(("=", "+", "-", "@")) or cell.startswith(
                ("\t", "\r", "\n")
            ):
                cell = "'" + cell
            safe.append(cell)
        writer.writerow(safe)
    return "\ufeff" + buffer.getvalue()


class WebReportingService:
    def __init__(self, store):
        self.store = store

    def create(self, owner, body):
        return self.store.dashboard(
            owner,
            normalize_filter(body.project_id, body.start, body.end, body.status, body.timezone),
        )

    def read(self, owner, identity):
        return self.store.read(owner, identity)["dashboard"]

    def page(self, owner, identity, offset, limit):
        return self.store.page(owner, identity, offset, limit)

    def csv(self, owner, identity):
        return self.store.export_csv(owner, identity)

    def usage(self, owner, identity, offset, limit):
        return self.store.usage_page(owner, identity, offset, limit)
