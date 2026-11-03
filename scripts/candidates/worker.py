"""Trusted observer for the two reviewed candidates, inside a bounded container only."""

import json
import subprocess
import sys
import time
from importlib.metadata import version

import pytest

# The same runtime probes as the synthetic worker; no fixture execution is reused.
from isolation import isolation_observations


class Observer:
    def __init__(self) -> None:
        self.ids = []
        self.reports = []

    def pytest_collection_finish(self, session) -> None:
        self.ids = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report) -> None:
        self.reports.append(
            {
                "test_id": report.nodeid,
                "phase": report.when,
                "outcome": report.outcome,
                "was_xfail": hasattr(report, "wasxfail"),
            }
        )


if __name__ == "__main__":
    isolation = isolation_observations()
    observer = Observer()
    stage, candidate = sys.argv[1:3]
    started = time.monotonic()
    if stage == "build":
        # Candidate build hooks execute only here, with network disabled.
        code = subprocess.call(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir=/tmp/wheels",
                "/repo",
            ]
        )
    else:
        args = ["-q", "-p", "no:cacheprovider", "--rootdir=/repo", "--basetemp=/tmp/pytest"]
        if candidate == "tinydb":
            args += ["-p", "pytest_cov.plugin"]
        args += (
            ["--collect-only", "tests"]
            if stage == "collect"
            else [sys.argv[3]]
            if stage == "single"
            else ["tests"]
        )
        code = int(pytest.main(args, plugins=[observer]))
    print(
        "SMARTREGRESSION_CANDIDATE="
        + json.dumps(
            {
                "exit_code": code,
                "ids": observer.ids,
                "reports": observer.reports,
                "stage": stage,
                "duration_seconds": time.monotonic() - started,
                "isolation": isolation,
                "python": sys.version.split()[0],
                "packages": {
                    name: version(name)
                    for name in [
                        "pytest",
                        "pytest-cov",
                        "coverage",
                        "build",
                        "hatchling",
                        "packaging",
                        "pluggy",
                    ]
                },
            }
        ),
        flush=True,
    )
