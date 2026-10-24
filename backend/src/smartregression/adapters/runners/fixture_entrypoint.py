"""Container entrypoint: input collection and test imports occur only in the worker."""

import json
import sys

import pytest

PREFIX = "\nSMARTREGRESSION_EVENT "


class Events:
    def pytest_collection_finish(self, session):
        if sys.argv[1] == "discover":
            print(
                PREFIX + json.dumps({"kind": "inventory", "ids": [i.nodeid for i in session.items]})
            )

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.failed or report.skipped:
            print(
                PREFIX
                + json.dumps(
                    {
                        "kind": "result",
                        "test_id": report.nodeid,
                        "phase": report.when,
                        "outcome": report.outcome,
                        "duration_seconds": report.duration,
                    }
                )
            )


def main() -> int:
    mode = sys.argv[1]
    request = json.loads(sys.argv[2])
    args = ["-q", "-p", "no:cacheprovider", "--rootdir=/input", *request["args"]]
    if mode == "discover":
        args += ["--collect-only", *request["paths"]]
    elif mode == "run":
        args += [request["test_id"]]
    else:
        return 2
    return int(pytest.main(args, plugins=[Events()]))


if __name__ == "__main__":
    raise SystemExit(main())
