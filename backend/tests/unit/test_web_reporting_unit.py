"""Reports preserve unknown values and spreadsheet-safe portable CSV."""

import csv
import io

import pytest

from smartregression.application.web_reporting import csv_text, normalize_filter


def test_csv_quotes_unicode_newlines_and_formula_injection():
    result = csv_text(
        [["name", "text"], ["=2+3", 'Tiếng Việt, "đúng"\nxong'], ["\t@SUM(A1)", "ok"]]
    )
    rows = list(csv.reader(io.StringIO(result.lstrip("\ufeff"))))
    assert rows[1] == ["'=2+3", 'Tiếng Việt, "đúng"\nxong']
    assert rows[2][0].startswith("'\t@")


def test_filter_timezones_and_asof_are_validated():
    from datetime import UTC, datetime, timedelta

    from smartregression.application.auth import AuthFailure

    now = datetime.now(UTC)
    value = normalize_filter(None, None, None, None, "Asia/Ho_Chi_Minh", now)
    assert value.end == value.as_of and value.start == now - timedelta(days=30)
    with pytest.raises(AuthFailure, match="invalid_report_filter"):
        normalize_filter(None, None, None, None, "not/a/timezone", now)
    with pytest.raises(AuthFailure, match="invalid_report_filter"):
        normalize_filter(None, now, now - timedelta(days=1), None, "UTC", now)
