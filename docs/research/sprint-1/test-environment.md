# 1.05 Test environment and execution constraints

Prepared for Tran Hung Khanh, 2026-10-24. Design deliverable for PB02; proposed
reviewer: Do Ha An. This document does not implement a runner or select the
production framework. Sources: [guide](../../development/sprint-1-team-guide.md),
[candidates](repository-candidates.md), [runner security](../../rules/10-runner-security.md).

## Candidate comparison and decision boundary

| Option | Evidence currently available | Limitation | Proposal |
| --- | --- | --- | --- |
| Python / pytest | All four candidate repositories have Python source and pytest-related configuration in Viet's 1.03 draft; SmartRegression has a working Python test toolchain | Candidate collection, dependencies and test stability have not been measured in an isolated worker | Use one Python/pytest experimental adapter for G1; D05 remains pending for the product |
| Java / JUnit | No matching candidate or adapter evidence in this repository | Would require different parser, build and discovery spike | Defer pending evidence; do not claim unsupported languages have been benchmarked |
| JavaScript / Jest | No matching candidate or adapter evidence in this repository | Node used for our dashboard is not evidence of an input-repository adapter | Defer pending evidence |

Candidate identity/license permalinks are in 1.03. Its estimates and test-file
counts are not measured runtime or successful discovery. TinyDB is a candidate
for a small smoke spike, not a representative final benchmark. Larger candidates
still need an independent reproducibility check. No candidate code was executed
for this document. Candidate choice and final D05 acceptance remain team decisions.

## Proposed configuration

One immutable configuration per repository and target SHA:

| Field | Example for the G1 fixture | Validation / meaning |
| --- | --- | --- |
| framework | pytest | Exact supported identifier; other values rejected |
| language | python | Matches experimental adapter |
| command | python -m pytest | An executable plus fixed argument vector; never a shell string supplied by the repository |
| test_paths | [tests] | Repository-relative POSIX paths; no absolute path, drive, backslash, dot/dot-dot components or symlink escape |
| approved_args | [-q] | Host-owned allowlist; reject -c, -p, --override-ini, --rootdir and unknown flags from requests |
| timeout_seconds | 30 | Finite positive value with a configured upper bound; no bool/NaN/infinity |
| cpu_count | 1 | Finite positive CPU quota |
| memory_mib | 256 | Positive bounded memory; do not silently ignore unenforceable limits |
| output_bytes | 65536 | Positive output cap; terminate the workload when exceeded, not only truncate a log afterwards |
| network | none | Worker runtime has no outbound network |
| install_policy | prebuilt-image-only | No setup.py, install hooks or dependency download from the input repository during execution |
| image | locally approved image digest | Pin tools and dependencies; record the actual digest and versions in run artifacts |

Numbers above are proposed fixture limits, not measured suitable defaults for
all candidates. Record actual command/args, tool versions, config revision/hash,
repository identity, frozen target SHA, inventory hash, timestamps and exit status.
Resolve revisions before work begins; branch names are not immutable run identity.

## Isolation and trust model

The API/dashboard never executes input code. Only an explicitly requested worker
may run it. A test ID is an address, not proof the test is safe. Pytest discovery
imports modules and conftest.py, so collection needs the same isolation as execution.

Proposed container spike: non-root user, read-only root filesystem and source mount,
no network, dropped capabilities, no-new-privileges, CPU/RAM/PID/time/output limits,
bounded tmpfs and cleanup on success, error and interruption. No host credentials,
Docker socket, privileged mode, arbitrary environment variables or writable project
mounts inside the test workload. Orchestration must run on a disposable development
worker with no deployment credentials. A container shares a kernel and is not a
guarantee against malicious repositories; arbitrary hostile input is outside G1.

Dependency installation occurs separately in a reviewed image build. An image
containing pytest does not prove candidate dependencies are installed. Missing
dependencies are setup/infrastructure failures. Do not silently install them online
or retry with network access. Docker/image unavailable means stop, not host execution.

## Discovery and result states

| Observation | Required result |
| --- | --- |
| Collection succeeds with one or more stable nodeids | complete inventory tied to target SHA/framework/adapter version |
| Collection succeeds, no tests collected | empty inventory; explicit no-tests policy, no safety conclusion |
| Import, collection or plugin error | discovery_failed, never an empty successful inventory |
| Timeout or output/resource limit | distinct worker failure; inventory incomplete and not eligible for selection |
| Selected ID absent from the frozen inventory | reject before dispatch |
| Test not selected | selection decision, not a pytest skip |
| Dispatched test skipped by pytest | runner-skipped outcome |
| Assertion, build/setup, timeout or infrastructure failure | separate categories; none automatically means a verified fault |

## Acceptance cases and handoff

| Input/case | Expected behavior |
| --- | --- |
| Empty/unknown framework or command with shell metacharacters | reject before launching any process |
| Timeout/CPU/RAM/output <= 0, bool, NaN, infinity, over cap | reject configuration |
| ../tests, absolute path, drive path, symlink outside snapshot | reject before reading/mounting |
| Discovery exit 2 / timeout | failure, no dispatch |
| Discovery exit 5 with empty collection | empty inventory, distinct from failure |
| Inventory belongs to a different target SHA | reject dispatch |
| Selected test is parameterized | preserve exact framework-native nodeid; do not split or reinterpret it as a command |
| Container fails to start or cleanup fails | infrastructure failure; no passing report |

Handoff: An reviews config/revision mapping; Nguyen Tan Huy consumes lifecycle and
evaluation environment fields; Viet consumes candidate feasibility observations;
Pham Phan Hoang Huy consumes the pre-execution inventory boundary. See
[selection policy](selection-policy.md). G1 runtime evidence is a separate task;
do not mark these design cases executed merely because they are listed.

AI assistance: Codex drafted this design from repository rules and existing
handoffs, and self-reviewed it. Human review/understanding and final D05/D07 policy
approval remain pending; no reviewer approval, signature or contribution ratio inferred.
