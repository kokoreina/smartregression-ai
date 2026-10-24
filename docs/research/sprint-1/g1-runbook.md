# G1 owned fixture runner demonstration

Experimental script, not a production runner or a benchmark. Requires a disposable
development Docker worker with no deployment credentials. No host fallback.
See [test environment](test-environment.md) and [Git spike](git-diff-spike.md).

## Build the reviewed worker image separately

Supply an approved official Python 3.14 image pinned to its verified digest:

```text
docker build --build-arg PYTHON_IMAGE=python@sha256:<verified-digest> -t smartregression-g1 -f scripts/g1-image/Dockerfile scripts/g1-image
docker image inspect --format={{.Id}} smartregression-g1
```

Do not paste a literal placeholder into a shell. The repository does not invent an
upstream image digest. Review the base image/dependency pins and record its actual
image ID. Image building can access package registries and is outside the test
workload; candidate install hooks are not run. Supply additional candidate
dependencies only in a separate reviewed image, never by relaxing runtime network.

## Run the owned fixture spike

On Windows the helper pins the verified upstream base-image index digest, builds
the image, obtains its actual local image ID and runs the script:

```powershell
.\scripts\run_g1.ps1 -PythonExe .\.venv\Scripts\python.exe
```

The pinned index digest is recorded in [integration evidence](integration-evidence.md).
Run this in a terminal authorized to reach Docker Desktop. The Codex sandbox may
be denied access to its named pipe even when the user's terminal works; changing
Docker permissions or exposing an unauthenticated TCP endpoint is not a workaround.

After locked SmartRegression setup, from repository root:

```text
uv run python scripts/spike_g1.py --image sha256:<actual-local-image-id>
```

Script creates an owned Git fixture under `var/g1/<run-id>`, freezes two actual
commits, reads diff and AST observations, materializes selected target files by
Git object reads, then performs pytest collection inside Docker. It validates the
inventory, writes selection.json before execution, dispatches one known ID inside
a new container and records structured events in evidence.json. Success requires
exactly one passing call result for the selected ID. No raw pytest source/error
logs are exported by the script; artifacts are local and ignored by Git.

The fixed image uses non-root execution, read-only source/root mounts, disabled
network, dropped capabilities, no-new-privileges and CPU/RAM/PID/time/output/tmpfs
limits. A host output reader caps memory and terminates the client on timeout or
overflow; finally removes the named container. Cleanup failure is an error. A
container is not a full hostile-code sandbox; this spike is scoped to original
project-owned fixtures. Do not point it at an unreviewed external repository.

Inventory binds target SHA, config hash, source snapshot digest and exact native
nodeids. The worker verifies those before dispatch. The host-owned snapshot is
expected to remain private/read-only during execution; this is not a proof against
concurrent privileged mutation or malicious kernel escape. Worker transport and
public report/job schemas remain separate future tasks.

## Evidence classification

| Result | Meaning |
| --- | --- |
| demonstrated_on_owned_fixture, exit 0 | Git-to-discovery-to-single-test mechanics observed for this fixture/image |
| empty, failed, timeout, output_limit, exit 2 | Gate not demonstrated; inspect structured failure category |
| blocked / docker_unavailable | Docker executable/engine/image prerequisite unavailable; do not execute on host |
| cleanup_failed | Cleanup could not be confirmed; operator must inspect the named workload |

Owned-fixture success is not proof of public candidate compatibility, full-suite
speed, fault retention or production isolation. A real candidate needs its own
approved license, image, immutable pair and recorded runtime observations. D05
final input-framework choice and independent review stay separate decisions.

## Current machine observation

On 2026-10-24 Docker was absent from PATH and the standard Docker Desktop binary
location. Script was exercised with a syntactically valid placeholder image ID
as an unavailable-runtime diagnostic; it returned blocked/docker_unavailable and
exit 2, before any workload could launch. This is failure-path evidence only;
the placeholder is not an approved image or successful image run. Current G1
runtime remains pending. No infrastructure is installed or privilege changed.

Update after user installation: Docker client 28.5.1 is now present, but the agent
sandbox receives access denied on dockerDesktopLinuxEngine. Runtime remains
pending until the user's terminal produces evidence.json. This supersedes only
the current-installation observation, preserving the earlier failure-path record.

First user-terminal run built the image and discovered two tests. The dispatched
test exited 0, but result-event parsing failed; gate was reported failed. A newline
framing regression test covers the correction. See integration evidence for the
immutable artifact identity and subsequent runtime status; no earlier failure is
rewritten as success.

The subsequent user-terminal artifact
var/g1/982f571662ec4b4689e4d5f2fc64dfd0/evidence.json confirms
demonstrated_on_owned_fixture: two target IDs discovered and exactly one selected
test call passed. Full SHA/image/hash/timestamp evidence is recorded in the
integration ledger. Candidate execution and official sprint acceptance remain
separate. To rerun source checks and G1 together from the operator terminal:

```powershell
.\scripts\verify_sprint1.ps1 -PythonExe .\.venv\Scripts\python.exe
```
