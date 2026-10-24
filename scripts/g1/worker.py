"""Trusted fixture-only harness, run inside Docker, not imported by host tests."""

import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

import pytest


def isolation_observations():
    status = Path("/proc/self/status").read_text()
    assert os.getuid() == 65534
    assert "NoNewPrivs:\t1" in status and "Seccomp:\t2" in status
    assert set(os.listdir("/sys/class/net")) == {"lo"}
    for path in ["/repo/probe", "/root/probe"]:
        try:
            Path(path).write_text("must fail")
        except OSError:
            pass
        else:
            raise RuntimeError("writable_source_or_root")
    cgroup = Path("/sys/fs/cgroup")
    if (cgroup / "memory.max").exists():
        memory = (cgroup / "memory.max").read_text().strip()
        pids = (cgroup / "pids.max").read_text().strip()
        cpu = (cgroup / "cpu.max").read_text().strip()
    else:
        memory = (cgroup / "memory/memory.limit_in_bytes").read_text().strip()
        pids = (cgroup / "pids/pids.max").read_text().strip()
        cpu = (
            (cgroup / "cpu/cpu.cfs_quota_us").read_text().strip()
            + " "
            + (cgroup / "cpu/cpu.cfs_period_us").read_text().strip()
        )
    return {
        "uid": os.getuid(),
        "seccomp": 2,
        "no_new_privileges": True,
        "network": ["lo"],
        "memory_max": memory,
        "pids_max": pids,
        "cpu_max": cpu,
    }


class Observations:
    def __init__(self):
        self.ids = []
        self.reports = []

    def pytest_collection_finish(self, session):
        self.ids = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report):
        self.reports.append(
            {"test_id": report.nodeid, "phase": report.when, "outcome": report.outcome}
        )


if __name__ == "__main__":
    isolation = isolation_observations()
    observations = Observations()
    args = ["-q", "-s", "-p", "no:cacheprovider", "--rootdir=/repo"]
    args += ["--collect-only"] if sys.argv[1] == "collect" else [sys.argv[2]]
    exit_code = int(pytest.main(args, plugins=[observations]))
    print(
        "SMARTREGRESSION_RESULT="
        + json.dumps(
            {
                "exit_code": exit_code,
                "ids": observations.ids,
                "reports": observations.reports,
                "isolation": isolation,
                "python": sys.version.split()[0],
                "pytest": pytest.__version__,
                "packages": {
                    name: version(name)
                    for name in ["pytest", "iniconfig", "packaging", "pluggy", "pygments"]
                },
            }
        )
    )
