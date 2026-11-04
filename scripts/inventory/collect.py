"""Trusted observer, invoked only inside a reviewed offline candidate container."""

import json
import subprocess
import sys
import time
from importlib.metadata import distributions

import pytest
from isolation import isolation_observations


class Observer:
    def __init__(self):
        self.ids = []
        self.errors = 0
        self.finished = False
        self.skips = []
        self.configuration = {}

    def pytest_configure(self, config):
        self.configuration = {
            key: config.getini(key)
            for key in (
                "addopts",
                "norecursedirs",
                "python_files",
                "python_classes",
                "python_functions",
            )
        }

    def pytest_collectreport(self, report):
        self.errors += int(report.failed)
        if report.skipped:
            self.skips.append({"nodeid": report.nodeid, "reason": "collection_skip"})

    def pytest_collection_finish(self, session):
        self.ids = [item.nodeid for item in session.items]
        self.finished = True


def main():
    mode, profile, identity = sys.argv[1:]
    identity = json.loads(identity)
    isolation = isolation_observations()
    started = time.monotonic()
    observer = Observer()
    if mode == "build":
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
        if profile == "tinydb":
            args += ["-p", "pytest_cov.plugin"]
        args += ["--collect-only", "tests"]
        code = int(pytest.main(args, plugins=[observer]))
    print(
        "\nSMARTREGRESSION_INVENTORY="
        + json.dumps(
            {
                "protocol": "inventory/1",
                "identity": identity,
                "mode": mode,
                "collection": {
                    "ids": observer.ids,
                    "exit_code": code,
                    "collection_finished": observer.finished,
                    "collection_errors": observer.errors,
                },
                "isolation": isolation,
                "environment": {
                    "python": sys.version.split()[0],
                    "packages": {
                        d.metadata["Name"].lower().replace("_", "-"): d.version
                        for d in distributions()
                    },
                },
                "exclusions": {
                    "configuration": observer.configuration,
                    "collection_skips": observer.skips,
                },
                "duration_seconds": time.monotonic() - started,
            },
            ensure_ascii=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
