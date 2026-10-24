# Synthetic Python/pytest G1 spike

This harness runs **only the task-authored fixture it generates**. It is not a
general repository runner, benchmark, or API endpoint. Do not point FixtureWorker
at external code. Product unit tests may run on the host; input discovery/test
execution below occurs in Docker only. No credentials or project .env are read.

## Prepare and run (root of monorepo)

Prerequisites: existing dev environment, Git and a working Linux Docker engine.
The task does not install or reconfigure system software. Image build downloads
pytest from PyPI before execution; the fixture workload has no network/install hooks.

```powershell
docker build -t smartregression-g1:python314-pytest911 -f scripts/g1/Dockerfile scripts/g1
$g1Image = docker image inspect smartregression-g1:python314-pytest911 --format '{{.Id}}'
uv run python scripts/g1/run_spike.py --image $g1Image --output var/g1-new-run
```

Output directory must be new. The base image is pinned in Dockerfile; record the
actual built image ID (not the intermediate config digest printed by BuildKit).
pytest is pinned, but transitive resolution can change on a later rebuild; the
image ID is the precise runtime identity. Record installed versions for each run.
Never claim a rebuild produces identical bytes without a dependency hash lock.

The script creates a temporary synthetic Git repo, commits a base and target,
reads file diff/symbols/module-import edges, and materializes only two reviewed
Python blobs from the immutable target (no Git hooks or input setup/install).
It discovers test IDs, writes selection.json before execution, runs the selected
test and failure/skip/timeout/output-limit/empty-discovery/collection-error cases.
Artifacts stay in ignored var/; no synthetic test outcome is a fault label.

## Enforcement and limits

Workload: immutable image ID, user 65534, read-only root and source/worker mounts,
cap-drop ALL, no-new-privileges, explicit seccomp syscall allowlist, network none,
1 CPU, 256 MiB RAM and swap cap, 64 PIDs, 30s execution deadline, 64 KiB output
cap, 16 MiB bounded tmpfs, no Docker socket/host credentials. Limit-test cases use
shorter deadline/output cap. Overflow kills the attached client and finally removes
the named container; cleanup failures are errors, never success. No log persistence
in Docker. Docker inspect validates configuration before start. Worker checks UID,
NoNewPrivs, Seccomp, loopback-only interfaces, failed source/root writes and cgroup
quotas (v1/v2). Source hash binds inventory/dispatch; unknown IDs are rejected.

Seccomp profile is intentionally narrow for this fixture, not an accepted arbitrary
repository policy. Docker Desktop shares infrastructure/kernel boundaries; local
spike checks do not prove security for hostile repositories or production tenancy.
Concurrent snapshot mutation is outside this task-authored, private-temp fixture
model; future ingestion needs immutable storage/authorization and stronger isolation.

If Docker/image/quota/seccomp is unavailable, stop G1 and record the reason. Never
retry input execution on the host. Temporary repo is removed by its owning Python
TemporaryDirectory; images and local artifact directories remain for reproduction.

Sources: [pytest invocation](https://docs.pytest.org/en/stable/how-to/usage.html),
[exit codes](https://docs.pytest.org/en/stable/reference/exit-codes.html),
[Docker limits](https://docs.docker.com/engine/containers/resource_constraints/).
Read 2026-10-24. Runtime support measured here is Python 3.14.3/pytest 9.1.1 on
this Linux container; ADR 0002 does not yet promise all Python versions/plugins.
