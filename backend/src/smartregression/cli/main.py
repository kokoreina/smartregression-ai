"""Read-only Git change analysis and report validation for authorized local input."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from smartregression.adapters.git_local import LocalGit
from smartregression.application.changed_components import identify_changes
from smartregression.application.reports import validate_report_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smartregression")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-report", help="Validate a report JSON file")
    validate.add_argument("path", type=Path)
    changed = commands.add_parser(
        "changed-components", help="Identify changes between two Git SHAs"
    )
    changed.add_argument("--repository", type=Path, required=True)
    changed.add_argument("--base", required=True)
    changed.add_argument("--target", required=True)
    args = parser.parse_args(argv)
    if args.command == "changed-components":
        try:
            reader = LocalGit(args.repository)
            result = identify_changes(
                reader, repository=str(reader.repository), base=args.base, target=args.target
            )
        except OSError, UnicodeError:
            print("Cannot read authorized repository.", file=sys.stderr)
            return 2
        except ValueError as exc:
            codes = {
                "invalid_commit",
                "unsupported_path",
                "unsupported_file_mode",
                "unsupported_change",
                "git_unavailable_or_timeout",
                "repository_required",
            }
            code = str(exc) if str(exc) in codes else "change_analysis_failed"
            print(f"Cannot identify changes: {code}", file=sys.stderr)
            return 2
        print(json.dumps(asdict(result), ensure_ascii=True, indent=2))
        return 1 if result.status == "partial" else 0
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
