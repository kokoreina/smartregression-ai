"""Export all canonical models plus API paths; deterministic and checkable without Git."""

import argparse
import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from smartregression.api.main import create_app
from smartregression.application.reports import validate_report_json
from smartregression.contracts.models import (
    AnalysisReport,
    AnalysisRequest,
    ErrorResponse,
)
from smartregression.contracts.stages import EvidenceBundle, StageAnalysisReport
from smartregression.contracts.workflow import ProposalRequest, WorkflowReport

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schema = create_app().openapi()
    _, models = models_json_schema(
        [
            (model, "validation")
            for model in (
                AnalysisReport,
                AnalysisRequest,
                ErrorResponse,
                StageAnalysisReport,
                EvidenceBundle,
                ProposalRequest,
                WorkflowReport,
            )
        ],
        ref_template="#/components/schemas/{model}",
    )
    schema.setdefault("components", {}).setdefault("schemas", {}).update(models["$defs"])
    content = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    target = ROOT / "contracts/generated/openapi.json"
    # Validate the one canonical demo fixture as part of export/check.
    demo = validate_report_json((ROOT / "examples/reports/demo.json").read_text("utf-8"))
    if demo.data_kind != "demo":
        raise ValueError("the demo fixture must be explicitly marked demo")
    for example in sorted((ROOT / "examples/reports").glob("stage-report.*.json")):
        report = validate_report_json(example.read_text("utf-8"))
        if not isinstance(report, StageAnalysisReport) or report.data_kind != "demo":
            raise ValueError("stage examples must be explicitly marked v2 demo")
    for example in sorted((ROOT / "examples/reports").glob("workflow-report.*.json")):
        report = validate_report_json(example.read_text("utf-8"))
        if not isinstance(report, WorkflowReport) or report.data_kind != "demo":
            raise ValueError("workflow examples must be explicitly marked v3 demo")
    ProposalRequest.model_validate_json(
        (ROOT / "examples/reports/proposal-request.demo.json").read_text("utf-8")
    )
    if args.check:
        if not target.exists() or target.read_text("utf-8") != content:
            print("Schema is stale: uv run python scripts/export_contracts.py")
            return 1
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
