import json
from dataclasses import replace

import pytest
from test_run_store import inputs

from smartregression.application.run_store import (
    RunMetadataError,
    prepare_run_report,
    validate_run_report_write,
)
from smartregression.core.git.snapshots import canonical_json


def test_prepared_write_revalidates_and_detaches_identity(stage_artifacts):
    write = prepare_run_report(**inputs(stage_artifacts))
    checked = validate_run_report_write(write)
    assert checked == write
    assert checked.identity is not write.identity


@pytest.mark.parametrize(
    "change",
    [
        {"report_id": "bad\0id"},
        {"configuration_json": b"{}\n"},
        {"stage_summary_json": b"{}\n"},
        {"analysis_status": "completed"},
        {"analysis_duration_seconds": float("nan")},
        {"llm_cost_usd": -1.0},
        {"data_kind": "untrusted"},
        {"snapshots": ()},
    ],
)
def test_forged_write_rejected_before_sql(stage_artifacts, change):
    write = prepare_run_report(**inputs(stage_artifacts))
    with pytest.raises(RunMetadataError):
        validate_run_report_write(replace(write, **change))


def test_summary_cannot_drop_errors_or_add_source_data(stage_artifacts):
    write = prepare_run_report(**inputs(stage_artifacts))
    summary = json.loads(write.stage_summary_json)
    summary["inventory"]["data"] = {"private": "source"}
    with pytest.raises(RunMetadataError):
        validate_run_report_write(replace(write, stage_summary_json=canonical_json(summary)))


def test_config_cannot_smuggle_unknown_secret_options(stage_artifacts):
    write = prepare_run_report(**inputs(stage_artifacts))
    config = json.loads(write.configuration_json)
    config["database_url"] = "private"
    with pytest.raises(RunMetadataError) as error:
        validate_run_report_write(replace(write, configuration_json=canonical_json(config)))
    assert str(error.value) == "run_metadata_invalid"
