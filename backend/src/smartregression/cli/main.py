"""Local validation only. Never clones or executes an input repository."""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from smartregression.application.reports import validate_report_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smartregression")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-report", help="Validate a report JSON file")
    validate.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_report_json(args.path.read_text(encoding="utf-8"))
    except OSError, UnicodeError:
        print("Cannot read report as UTF-8.", file=sys.stderr)
        return 2
    except ValidationError as exc:
        # Omit input values; reports may contain proprietary source text.
        print(f"Invalid report: {exc.error_count()} contract error(s).", file=sys.stderr)
        return 1
    print(f"Valid report [{report.data_kind.upper()}]: {report.report_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
