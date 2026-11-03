# Tasks 2.08 and 2.09 target inventory integration

Date: 2026-11-03. Local branch `feat/khanh-task-2.08-2.09-inventory` starts from
main `321c1cbc816f56ed5d50345a69e8314e1129fb2b`. The earlier independent work was
preserved when switching branches. After verification, the user authorized commit
and push on 2026-11-03 so the team can open/review the PR. Merge remains with the team.

## Why this can proceed now

Main contains merged 2.14 canonical stage reports, 2.15 frozen snapshots and 2.13
thin workflow. It also contains 2.03 static graph, 2.01 changed components and
2.02/2.07 validation/ordering. These are concrete producer/consumer inputs, not
evidence every sprint acceptance criterion has been met. The merged 2.20-A file is
a design checkpoint only: there is no PostgreSQL foundation adapter or migration
mechanism to consume yet. Tooling/minimum schema decisions remain proposed there.

Team branch examples are task-oriented: `feat/sprint-2-2.14-contracts`,
`feat/sprint-2-2.13-workflow`, `feat/an-task-2.15-snapshots`,
`feat/task-2.03-dependency-graph`, `feat/task-2.02-location-validation` and
`feat/task-2.07-review-ordering`. An also reused an older personal branch for 2.01;
the observed pattern is not a requirement to combine all personal tasks. The user
allowed task branches; these two tightly related inventory tasks share one branch.

## Scope and affected files

- `core/execution/inventory.py`: preserved internal identity/completeness validation.
- `application/inventory.py`: collector protocol, trusted-snapshot/config binding,
  revalidation and projection onto existing canonical `InventoryPayload`/`StageResult`.
- `application/analysis.py`: optional explicitly injected collector receives only
  this run's frozen target. Default CLI/composition still has no collector and runs
  no input code. KH is the local writer for this bounded inventory hook; H1 remains
  the workflow consumer/reviewer. No public API, CLI flags or generated schemas change.
- `adapters/runners/inventory_collector.py`: uses existing G1 Docker worker only for
  byte-identical fixtures in `inventory_fixtures.py`; other source bytes reject
  before materialization/execution. This does not authorize arbitrary Python repos.
- G1 worker: reports actual collection finish/error hooks and starts the result
  marker on a new line. Existing result fields remain; candidate worker still uses
  its own format. FixtureWorker rejects duplicate IDs with a specific code and
  rejects JSON non-object results instead of accessing them as dictionaries.
- Focused inventory/stage/collector/workflow tests; operator verification scripts
  under `scripts/inventory`. Runtime sources/reports/logs stay ignored under `var/`.

## Status and identity semantics

Successful collection with IDs maps to `completed` plus `completeness=complete`.
Successful empty requires pytest exit 5, collection-finish and no collection errors;
it maps to `completed` with an empty complete inventory, not a safety verdict.
Partial collection maps to `partial` plus explicit limitations and partial inventory.
Timeout is `failed` with `discovery_timeout`; collection/output/infra failures retain
stable safe codes and no success payload. Aggregate report may still be partial
because other stages completed; `analysis_exit_code` must remain 2 for a failed stage.

Repository/run/full target SHA/manifest snapshot ID and actual collector config hash
bind the internal result. The adapter hashes runtime image ID, limits, worker/seccomp
bytes and its fixed collection policy; configuration mutations reject. Trusted
manifest validation occurs before collection. Native IDs remain opaque; duplicated
or malformed IDs reject rather than being silently dropped.

Canonical `InventoryPayload.test_ids` currently uses `Text`, which strips outer
whitespace. The projection checks exact round-trip equality and returns
`native_test_id_normalization` if a native ID would change. It does not edit H1's
shared schema. Public policy for those IDs needs producer/consumer reconciliation.

Report v2 currently does not include config/runtime fields in InventoryPayload.
The internal result binds them and the operator evidence records them; durable
provenance still requires 2.20/domain persistence. Never infer DB acceptance from
the JSON report or from these local artifacts.

## Isolated execution boundary

The input byte allowlist consists exclusively of project-authored success, empty,
collection-error, partial, duplicate, timeout and output-limit fixtures. Test bodies
in the success fixture deliberately raise if executed; only collection is requested.
No network/download/build/install occurs in collection containers. Image building
uses the existing G1 Dockerfile's pinned Python digest and pytest requirement;
transitive dependencies are observed, not newly hash-locked by this task.

G1 applies non-root UID, read-only root/source, no network/capabilities, explicit
seccomp, no-new-privileges and bounded CPU/RAM/PIDs/output/time/tmpfs. The adapter
checks the worker's actual isolation/quota observations before publishing results.
Finally cleanup from G1 removes containers even on timeout/overflow; the collector
removes only its fresh exclusively owned materialization directory after checking
its resolved parent. Concurrent privileged host mutation remains outside this spike.
Collection has no host fallback. This is not production isolation certification.

## Verification

Root cwd is `D:\C1.SE26\Repo-Sprint2-Khanh`. Existing Python 3.14.5 environment is
reused from `D:\C1.SE26\Repo\.venv`; PYTHONPATH points to this checkout's backend/src.
Git 2.49.0 supports `--no-lazy-fetch` here. No dependencies/lockfiles were changed.

Initial new stage/collector tests failed with missing modules, then passed after
implementation. Focused inventory and existing workflow checks passed during work.
Ruff lint passed after formatting; exporter `--check` passed without regeneration.
A diagnostic full-suite run in the sandbox used an external temporary-fixture
adapter: 380 passed, 6 existing snapshot/Git environment failures, 1 POSIX skip and
one existing Starlette warning. This is not a default/full gate success claim.

Normal-terminal default suite and real Docker checks are requested using:

```powershell
& 'D:\C1.SE26\Repo-Sprint2-Khanh\scripts\inventory\verify.ps1' -PythonExe 'D:\C1.SE26\Repo\.venv\Scripts\python.exe'
```

The script runs default pytest, Ruff check/format and exporter check, builds the
existing G1 image and runs seven task-authored Git fixtures through actual snapshot
preparation, analysis, collector and canonical reports. Each invocation creates a
fresh `var/inventory-verification-<uuid>/` with evidence.json and per-case reports.
Expected statuses/IDs are specified before observing output; no benchmark/reference
test outcomes are supplied to mapping or selection. The operator result has now
been inspected:

- Default pytest in ordinary PowerShell: **386 passed, 1 skipped**, one existing
  Starlette warning, 61.54s. The skip is the pre-existing POSIX FIFO case on Windows.
- Ruff lint/format and contract exporter check passed in that invocation.
- Docker checks: all seven actual cases matched their independently specified
  expected status/error/IDs. Evidence directory:
  `var/inventory-verification-392720d8f77349b48fa9a467824ae09d/`.
- Runtime image: `sha256:8f10bf07ea7b10ecf95f784c3edc07e821290032853593ac61f71e5420c052f0`.
- Success/empty/error/partial worker observations record UID 65534, seccomp 2,
  no-new-privileges, only loopback networking, 256 MiB memory, 64 PIDs and 1 CPU.
  Timeout/output/duplicate do not invent a successful final runtime observation;
  their controller/validation failure codes are retained.
- Actual snapshot preparation and v2 report validation run for each owned Git
  fixture. Collection success despite the raising test body demonstrates that
  these invocations did not execute that body. There is no source-host fallback.
- Full suite still needs CI/POSIX verification by the normal team process; this
  operator evidence is local, not a GitHub Actions run or human acceptance.
- Final script path review additionally normalizes `..` before checking output
  containment under var; an outside-var path is rejected before creating output.

## Remaining work and handoff

- 2.08: PostgreSQL inventory persistence requires real 2.20 foundation and domain
  schema/migrations; broader candidate collection requires an explicit approved
  runtime/dependency policy. Do not mark the whole task Done yet.
- 2.09: owned-fixture runtime state matrix is verified; consumer/human acceptance
  and DB partial-state mapping remain pending, not invented here.
- 2.16: graph 2.03 is present but 2.04 potential-impact producer is still missing.
  Do not replace it with guessed mappings or claim selector implementation.
- 2.10 exclusions support awaits index/retrieval producer/configuration decisions.
- 2.17 receives the implemented inventory limitations through the optional workflow
  path. This is not a claim the entire shared limitations task is finished.
- 2.19 can use the new inventory/workflow failure regressions, but they do not prove
  all identity/evidence/index boundaries or replace AN's independent cases.
- H1/AN review the bounded workflow hook and exact identity/config/status semantics.
  Since the baseline audit, main merged H1 2.20-B and accepted P1/P2/P4; KH's
  schema/migrations are delivered separately on feat/khanh-task-2.20-migrations.
  Inventory domain mapping/adapter and producer acceptance still remain separate.

OpenAI Codex assisted implementation, tests and this handoff. Review in this session
is self-review, not independent acceptance. Khánh must understand and validate the
work before submission per Proposal v1.4 Appendix C/D. Personal Word notes from
2026-11-01 remain outside Git and describe that earlier independent delivery.
