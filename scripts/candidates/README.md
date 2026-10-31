# Two-candidate Sprint 1 reproducibility spike

Only `andialbrecht/sqlparse@60cdc649726bf1bc4f1b336050560b336da715ec` and
`msiemens/tinydb@edff96aeb2616402e9489d46e90a592c05565621` are supported.
No arbitrary URL/ref, API integration, production authorization or selector is added.
The chosen test is a fixed smoke test, not a recommendation from dependency/LLM analysis.

## Inputs and trust boundary

The host uses existing `gh` authentication only to read fixed public GitHub endpoints.
Credentials never enter a container. GitHub archive redirects are handled by `gh`;
no user-controlled host/URL is accepted. Trees must be complete ordinary blobs;
archive files are checked against Git blob hashes before writes. Path traversal,
Windows special/ambiguous names, symlinks/hardlinks, secret-like paths, duplicates,
oversize/missing files are rejected. Archives are bounded to 8 MB, snapshots to
2000 files / 32 MB, individual files to 2 MB. Sources remain ignored under `var/`.
This is source materialization from a frozen commit, not a live clone/PR resolver.

Image build installs only the four dependency packages declared in Dockerfile.
No candidate build hook runs during the online image build. The Python base digest
and top-level package versions are pinned; transitive versions are recorded by
the observer/image identity, not hash-locked for byte-identical future rebuilds.

Candidate wheel building, pytest collection (including conftest) and tests execute
only in a new Linux Docker container per stage: UID/GID 65534, read-only root/source,
no network, no capabilities, no-new-privileges, explicit seccomp, 1 CPU, 512 MiB
RAM/swap cap, 64 PIDs, 64 MiB noexec tmpfs, 512 KiB output cap. Timeouts: build 60s,
each collection 60s, single 30s, full suite 120s; create/cleanup are bounded separately.
There are no automatic retries. Docker create/inspect/start errors, quota mismatch,
timeout, malformed worker output and cleanup errors fail the invocation.

`seccomp.json` starts from the synthetic profile and adds build-child process
support: vfork/wait/kill, rmdir for temporary cleanup, pwrite64 for coverage SQLite
files on tmpfs, clone with namespace creation
flags denied, and clone3 returning ENOSYS so libc can use the restricted clone path.
The synthetic profile and FixtureWorker are unchanged. This is a bounded two-repo
spike sharing the Docker kernel, not proof of security for hostile repositories.
The image build uses ordinary Docker build networking to fetch dependency wheels;
candidate runtime/build hooks have network none. Operator supplies a trusted Docker
host. Concurrent host mutation of the private artifact directory is outside scope.

The trusted worker imports runtime probes from the existing G1 worker as a module;
the synthetic fixture execution path is not reused. Probe and Docker inspect checks
verify UID, seccomp, no-new-privileges, mounts, network and observed quotas.

## Commands (root PowerShell)

Prerequisites: existing project dev environment, GitHub CLI and running Linux Docker
engine. No system installation/reconfiguration is performed by this harness.

```powershell
docker version --format '{{.Server.Version}}'
docker build --network=default -t smartregression-candidates:sprint1-20261031 -f scripts/candidates/Dockerfile scripts/candidates
$candidateImage = docker image inspect smartregression-candidates:sprint1-20261031 --format '{{.Id}}'
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate sqlparse --image $candidateImage --output var/candidate-sqlparse-new --full-suite
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate tinydb --image $candidateImage --output var/candidate-tinydb-new --full-suite
docker ps -a --filter name=smartregression-candidate- --format '{{.Names}} {{.Status}}'
```

Output must be a new directory under this repository's `var/`. Use fresh names on
rerun so failed/excluded attempts remain visible. The harness downloads fixed public
source as data, builds a wheel offline, collects twice, compares ordered inventories,
and writes selection.json before single/full execution. It tests directly from the
same source snapshot via PYTHONPATH; wheel installation is not verified. TinyDB's
configured pytest-cov is explicitly loaded; lint/type/docs plugins are not enabled.
If a repository needs other plugins/dependencies, record failure and review the
environment instead of removing its configuration or enabling runtime network.

Artifacts: source snapshot, bounded stage logs, observations.json with timestamps,
exit codes, package/isolation observations, and selection.json with frozen identity
and native IDs. Unknown IDs, incomplete/unstable inventories or unexpected dispatched
IDs fail. A skipped/xfail selected smoke test is retained in reports and fails the
single-test acceptance check; it cannot stand in for an executed passing smoke test.
`reproducibility_checks_passed` means commands succeeded under this experiment;
use per-test reports to assess skips, and do not infer fault retention or safe selection.

## Validation and evidence

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_candidate_spike.py -q -p no:cacheprovider --tb=short
```

Unit tests use task-authored tar/JSON fixtures and never run external source on the
host. Runtime observations and exclusions are in
[candidate reproduction](../../docs/research/sprint-1/candidate-reproduction.md).
Local artifacts/logs are not committed. Respect retained candidate LICENSE notices.
Do not invoke the old FixtureWorker with these repositories.
