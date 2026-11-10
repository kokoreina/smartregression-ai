# Sprint 3 G0 — Sprint 2 main integration

## Baseline and scope

Started 2026-11-09 for Nguyen Tan Huy under the explicit integration/3.15 brief.
Fetched main is `ac2f55283c8be865c72ca25308a4e00e5e3a827e`.
Worktree: `D:/smart-regression-ai/var/g0-integration`, branch
`integration/sprint-2-g0-20261109`. Existing root workspace Office renames,
untracked planning documents, outputs and helper files are preserved.

This record covers integration and fresh checks, not whole-sprint acceptance.
G0 requires the verified changes on main. PR readiness is not G0 and task 3.15
dependent implementation has not begun.

## Reconciliation

Main and completed work diverge from `44fa753d1a624a69595395caf9c30ba3d4dba32e`.
Both ancestry and source diff confirmed the missing code, not just PR titles.

| Slice | Reused source | Integration commit | Verification boundary |
| --- | --- | --- | --- |
| Analysis/evidence/compound persistence | `21fea51` | `b40ba01` | Stage propagation, immutable evidence and atomic SQL |
| Isolated inventory/mapping | `6199de2` | `a68fe65` | Exact native IDs, trusted receipts, report-bound sidecars |
| Bounded lexical retrieval | `bd659be` | `2abb854` | Frozen source, ready lifecycle, exclusions, restart/re-query |
| Nested UI validation/provenance | `18e14c9` | `e255319` | Schema/semantic rejection and run/report distinction |
| Immutable overlap claims | `21cdf84` | `026ab15` | Forward revision 06, concurrent writers and recovery |

All five source commits were inspected, applied in dependency order without
conflicts and retain historical author metadata. Backend/frontend/scripts/migrations
were byte-identical to completed-work `929b336` at checkpoint `026ab15`. The fresh
actual-report SSR run then exposed a null-retrieval assumption in the test harness.
`test-report-view.mjs` now shares its assertions with the default inactive-stage
fixtures and checks retrieval items only when data exists. It still asserts the
identity, data-kind and provenance of available items; inactive retrieval must
not display the successful-empty message. Main-only Sprint 1
policy/closeout remains intact. Completed-work's Office/doc closeout commit is not
imported; no Office files are changed by this task.

Public v1/v2 schemas, generated contracts, dependencies and lockfiles are unchanged.
The migration adds `20261109_06` after `20261105_05`; do not rewrite older revisions.
Runtime requires SELECT/INSERT on `run_stage_payloads`, not UPDATE/DELETE. The
forward-only migration requires consistent metadata/artifact backup and restore;
the local disposable test database is not a production migration.

## Verification ledger

Cwd is the integration worktree unless stated. Python 3.14.3 and dependencies are
reused from `D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe`.
`PYTHONPATH` points to this worktree's `backend/src`; bytecode is disabled and
portable Git is prepended from `var/task-2.13-tools/mingit/cmd` in the root workspace.
Node is 22.14.0; ignored `frontend/node_modules` is a junction to the existing root
installation. This is not a clean install or a new dependency-resolution claim.

| Check | Actual result |
| --- | --- |
| Ruff lint and format | Exit 0; 298 files already formatted |
| `python scripts/export_contracts.py --check` | Exit 0; unchanged canonical schema |
| `npm.cmd --prefix frontend run contracts:check` | Exit 0; 85 validation and 11 SSR checks |
| Frontend lint/typecheck/build | All exit 0; production build succeeds |
| Default backend regression | Exit 0; 873 passed / 132 skipped, 529.56s; `var/g0-elevated-default.xml` |
| Actual CLI report validation/SSR | 87 validation and 13 SSR checks; exit 0 after the harness fix |
| Frontend/backend semantic parity | All 71 rejected frontend mutations also rejected by backend |
| `python -m alembic heads` | Exit 0; only `20261109_06` |
| Inventory/mapping runtime | Both approved candidates reproduced twice (509/228 exact native IDs); mapping/CLI and 12 Docker fixture cases pass |
| Dedicated PostgreSQL runtime | Exit 0; 131 passed / no skips, 256.71s; upgrade, concurrent writers, restart/re-query and populated restore pass |
| Isolated Docker integrity | Exit 0; 26 passed, 382.50s; SQL is a declared recording port, not a database |
| Browser A07/A02/A03 subchecks | Not performed; historical user waiver only |

The first default-suite attempt inside the sandbox produced fixture setup errors
and was interrupted. The frontend sandbox attempt passed 85 validation cases but
failed SSR with `spawn EPERM`. Re-execution uses the permitted external process
environment; no tests, limits or gates were weakened to address sandbox failures.
The 132 default skips are 131 opt-in PostgreSQL cases and one POSIX FIFO case on
Windows. The dedicated database campaign is separate; skips are not runtime passes.
One existing Starlette/httpx deprecation warning remains. Actual-input SSR initially
failed with a null retrieval TypeError; default contract/SSR and lint gates plus
the same actual-report reproduction passed after the harness fix. No production
source change resulted from that fix, so backend regression was not repeated.

Executed commands (the Python prefix/environment above applies):

```powershell
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp var/g0-elevated-default --junitxml var/g0-elevated-default.xml
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
python -m alembic heads
npm.cmd --prefix frontend run contracts:check
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/inventory/verify_complete.ps1 -PythonExe D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe -RuntimeOnly
python scripts/integrity/verify.py --runtime-only
```

The PowerShell command uses a process-scoped execution-policy argument for the
existing harness, not a persistent policy change. Actual-input frontend scripts
were additionally run with both `var/mapping-workflow-927a06a9aee94a73b8b562b555163ad0/`
candidate `artifacts/cli-report.json` paths. An inline Python loop revalidated all
entries of `var/frontend-report-tests/rejected.json` with `validate_report_json`.

Fresh local evidence under this worktree (not committed runtime data):

- `var/candidate-inventory-verification-5f934bff787e4420aaea7da2064faae2/evidence.json`
- `var/mapping-workflow-927a06a9aee94a73b8b562b555163ad0/evidence.json`
- `var/inventory-verification-8784ca016a0a47529767b2078434dd80/evidence.json`
- `var/i-dbe1a45951c84934aaf3e33c5fe7675d/evidence.json`
- `var/storage-verification-a38b14a93bd74813accf744709407e45/evidence.json`
- `var/g0-elevated-default.xml`

The database ledger confirms fresh head `20261109_06`, exact populated rows after
restart, real lexical re-query after restart and restore, evidence identity/digest,
nonempty index metadata/chunks/artifacts, restored catalog integrity and removal
of the exact owned PostgreSQL container. No external DSN or user database was used.

The actual candidate reports intentionally remain partial: sqlparse retains 56
unresolved mappings, TinyDB 266. Successful integration checks do not turn those
limits into complete semantic coverage or a safe regression selection. Mapping
receipts/sidecar binding, wrong-report rejection and owned-container cleanup were
verified; no test-selection quality or live-model claim is made.

Browser inventory was checked in this session and reports `browser access host
is unavailable`. The earlier Huy waiver is recorded at completed-work `929b336`,
`docs/development/sprint-2-completion-plan.md` and `verified-commands.md`. It is
limited to Sprint 2 A07 and A02/A03 browser subchecks. No browser pass, new waiver,
or waiver for Sprint 3 is claimed. SSR is not browser verification.

## Publication and gate status

Read-only GitHub inspection found an active main ruleset `24593151`, no bypass
actors, one required approving review and allowed merge/squash/rebase methods.
The current account can push, but cannot substitute for independent approval.
No repository settings were changed. Source CI and merge status are pending
publication at this checkpoint. G0 remains blocked until actual main integration
and the applicable verification/CI evidence exist.

## Next task: 3.15

Independent design preparation is local only in `var/task-3.15-design.md`.
It maps existing v1/v2 models, strict report readers, exporter and frontend runtime
consumers to the required request/proposal/selection/result/error boundaries.
No new public DTOs, provider implementation, speculative database migration,
Gemini dependency or fake success has been added.

After approved merge, fetch main, record its SHA and confirm the tested source
and migration/consumer consistency. Then implement 3.15 on a separate main-based
branch: focused contract tests, minimum canonical types/ports, explicit version
compatibility, generated artifacts and consumer parity. Live Gemini belongs to
3.04/3.16, not this gate or contract task.

Codex assisted reconciliation, execution, documentation and self-review. No
independent human review, mentor approval, actual effort or benchmark claim is
inferred from these checks. No API key was read and no provider inference ran.
