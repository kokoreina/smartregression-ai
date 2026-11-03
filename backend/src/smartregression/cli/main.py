"""Read-only Git change analysis and report validation for authorized local input."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.report_output import report_destination, write_report
from smartregression.adapters.snapshot_store import materialize_pair
from smartregression.application.analysis import AnalysisError, analysis_exit_code
from smartregression.application.changed_components import identify_changes
from smartregression.application.reports import validate_report_json
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.composition import analyze_local
from smartregression.contracts.stages import StageAnalysisReport
from smartregression.core.git.snapshots import pair_manifest


def _analyze(args: argparse.Namespace) -> int:
    try:
        if args.output is not None:
            report_destination(args.output, args.repository)
        report = analyze_local(
            repository=args.repository,
            repository_id=args.repository_id,
            authorized_root=args.authorized_root,
            base=args.base,
            target=args.target,
            data_kind=args.data_kind,
        )
        # Revalidate nested mutable values at the serialization boundary.
        report = StageAnalysisReport.model_validate_json(report.model_dump_json())
        document = report.model_dump_json(indent=2)
        if args.output is None:
            print(document)
        else:
            write_report(args.output, document, repository=args.repository)
        code = analysis_exit_code(report)
    except AnalysisError as exc:
        print(f"Analysis failed: {exc.code}", file=sys.stderr)
        return 2
    except ValidationError:
        print("Analysis failed: report_validation_failed", file=sys.stderr)
        return 2
    except ValueError as exc:
        safe = {"output_exists", "output_inside_repository", "unsafe_output_path"}
        code = str(exc) if str(exc) in safe else "analysis_failed"
        print(f"Analysis failed: {code}", file=sys.stderr)
        return 2
    except OSError, UnicodeError:
        print("Analysis failed: analysis_io_error", file=sys.stderr)
        return 2
    except Exception:
        # Last-resort process boundary: redact unexpected exception/source text,
        # fail visibly, never convert an internal failure into an empty report.
        print("Analysis failed: analysis_internal_error", file=sys.stderr)
        return 2
    print(
        f"Analysis [{report.data_kind.upper()}]: {report.analysis_status}; exit={code}",
        file=sys.stderr,
    )
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smartregression")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-report", help="Validate a report JSON file")
    validate.add_argument("path", type=Path)
    analysis = commands.add_parser(
        "analyze", help="Analyze an explicitly authorized immutable SHA pair"
    )
    analysis.add_argument("--repository", type=Path, required=True, help="Local input repository")
    analysis.add_argument("--repository-id", required=True, help="Opaque application repository ID")
    analysis.add_argument(
        "--authorized-root",
        type=Path,
        required=True,
        help="Exact repository root authorized by the local operator",
    )
    analysis.add_argument("--base", required=True, help="Full lowercase base commit SHA")
    analysis.add_argument("--target", required=True, help="Full lowercase target commit SHA")
    analysis.add_argument(
        "--data-kind",
        choices=("demo", "real"),
        default="real",
        help="Use demo for fixtures; label is caller-declared",
    )
    analysis.add_argument(
        "--output", type=Path, help="New JSON file outside input repo; default stdout"
    )
    changed = commands.add_parser(
        "changed-components", help="Identify changes between two Git SHAs"
    )
    changed.add_argument("--repository", type=Path, required=True)
    changed.add_argument("--base", required=True)
    changed.add_argument("--target", required=True)
    snapshot = commands.add_parser("prepare-snapshots", help="Prepare an authorized local SHA pair")
    snapshot.add_argument("--repository", type=Path, required=True)
    snapshot.add_argument("--repository-id", required=True)
    snapshot.add_argument("--authorized-root", type=Path, required=True)
    snapshot.add_argument("--base", required=True)
    snapshot.add_argument("--target", required=True)
    snapshot.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return _analyze(args)
    if args.command == "prepare-snapshots":
        try:
            reader = LocalGit(args.repository)
            pair = prepare_snapshots(
                reader,
                authorization=RepositoryAuthorization(args.repository_id, args.authorized_root),
                repository_id=args.repository_id,
                base=args.base,
                target=args.target,
            )
            materialize_pair(pair, args.output, source_repository=reader.repository)
        except OSError, UnicodeError:
            print("Snapshot preparation failed: snapshot_io_error", file=sys.stderr)
            return 2
        except ValueError as exc:
            codes = {
                "unauthorized_repository",
                "invalid_commit",
                "invalid_repository_root",
                "unsupported_snapshot_entry",
                "unsafe_snapshot_path",
                "snapshot_path_collision",
                "snapshot_limit",
                "snapshot_objects_missing",
                "snapshot_mismatch",
                "snapshot_destination_exists",
                "snapshot_destination_inside_source",
                "snapshot_parent_missing",
                "unsafe_snapshot_destination",
                "git_unavailable_or_timeout",
                "output_limit",
            }
            code = str(exc) if str(exc) in codes else "snapshot_preparation_failed"
            print(f"Snapshot preparation failed: {code}", file=sys.stderr)
            return 2
        print(json.dumps(pair_manifest(pair), indent=2, ensure_ascii=True))
        return 0
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
