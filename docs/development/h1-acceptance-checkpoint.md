# Prompt 7 checkpoint — browser gate unverified

2026-11-05. Fetched origin/main still
`b3b251aa86854c63abeb6659a0be857b47e3505c`. Implementation stack is not merged;
do not describe it as latest-main acceptance or Sprint 2 Done.

Prompts 1–5: PRs #47–#51, source CI success previously observed; team review/merge
pending. Prompt 6 commit `2f5c517`, PR
[52](https://github.com/kokoreina/smartregression-ai/pull/52), base #51; also depends
on decision PR #46 merged locally. See [retrieval handoff](task-2.13-retrieval.md).
No automatic merge/approval occurred.

## Current execution evidence

| Case | Actual checks | Status and remaining gate |
| --- | --- | --- |
| A01 Actual producers | Both approved candidate Git pairs → isolated collector → index/search → mapping/report → real PostgreSQL; every required stage completed or honestly partial | Runtime passed on implementation stack, not merged-main/human acceptance |
| A02 Docs/config/no edges | Backend workflow/classification/no-edges regressions in the full backend; all changed files now have a dedicated UI section, including docs/config with file-only reasons; server rendering tested | Browser rendering unverified |
| A03 Partial/budget | Build/query timeout, chunk/byte/context caps, source exclusions, unresolved graph/report propagation; actual candidates remain partial | Browser visibility unverified |
| A04 Identity/corruption | Git acquisition, wrong identity/config/ranges, corrupt manifest/content/SQL metadata, separate deleted/base retrieval and target context | Backend checks passed; producer/consumer review remains assigned |
| A05 Inventory/mapping | Current sqlparse 509 / TinyDB 228 IDs, actual isolated receipt, run/report/hash-bound sidecar, failure/unknown ID regressions | Existing two historical candidate-to-inventory-DB opt-in cases still separate/skipped, not claimed run |
| A06 Persistence | 110 real PostgreSQL tests passed / 2 historical campaign skips, including 10,000 chunks, concurrency, rollback, lost ack and nonempty consistent backup/restore | Passed current local harness; no production deployment/retention claim |
| A07 UI | Nested schema + semantic/file-input validation, 80 checks; 67 negative cases separately rejected by canonical backend; 12 server-rendered checks including both actual candidates | **Browser gate unverified; Prompt 7 incomplete** |

Final P6 DB evidence:
`var/storage-verification-2c73751a0c514259a00d6b6a15ee6b5f/evidence.json`.
Current actual reports/evidence:

- sqlparse: `var/p5-candidate-flow-sqlparse-fead8de8d6e549fb9cb35f1f241f9a66/`;
  report SHA256 `7fe29c87864d257477cc16d0d4eae8e4f10e4b6cda2941faa415b6b8859c5fe9`.
- TinyDB: `var/p5-candidate-flow-tinydb-d0fb9cfac3a846a3b6f2d49d7517207f/`;
  report SHA256 `bad60c9ace697a2ab3609fab0ada1cc6f648ab159749ce934ec366ecf9ba74c3`.

## Prompt 7 local changes

Branch `feat/h1-sprint2-acceptance`, local implementation checkpoint. Existing loader
checked only a few top-level keys before casting; replaced with bounded validation
of canonical generated schema plus backend model relationships. Generated schema/types
unchanged. New report regression script runs with contracts:check using existing
TypeScript dependency; supported schema keyword coverage fails on unsupported drift.
File input cap 16 MiB; does not execute source or contact a new API. Loading sequence
guard prevents old reads from replacing a newer selection. Run ID now comes from
identity.run_id; report ID remains separate. UI exposes stage status text, limitations,
context provenance/ranges/hashes and unknown duration/cost without inventing zeroes.

Initial local checks: frontend typecheck, lint, contracts:check and
production build all exit 0. Build needed tool escalation because sandbox esbuild
spawn fails EPERM; no dependency/lockfile/security gate was relaxed. Actual-report
validation accepted both candidate artifacts. This is not browser acceptance.

Continuation verification: full backend **758 passed, 113 skipped, 1 existing
Starlette/httpx warning**, 230.73s, exit 0; JUnit at `var/p7-backend-tests.xml`.
112 skips require the separate dedicated PostgreSQL harness (110 passed / 2 old
campaign skips recorded above), one is a POSIX FIFO on Windows. Final frontend
checks now exercise **80** fixture/negative/file cases; **67** negative cases were
independently rejected by the backend model. A red regression exposed duplicate
evidence IDs after backend Text normalization; the consumer now normalizes metadata
and references before comparisons, preserving exact native test IDs. Four additional
cases check newline-tainted commit IDs. Oversized file is rejected before text read;
JSON errors remain sanitized. Schema/producer fields/generated types remain unchanged.

Server-rendered checks use existing React/Vite dependencies: 10 fixture/component
checks, **12 with both actual candidate reports**, passed. They assert separate
Run/Report IDs, revision metadata, all changed docs paths/limitations, empty/failed
rendering, HTML escaping and actual retrieval provenance. They are now included
in `npm --prefix frontend run contracts:check` through `test:reports`. No new
framework or package was installed. No SSR result is counted as a browser result.

Browser tooling inventory returned no browser host. Native Chrome window 263036
was available, but `cua.getApp` was stopped by the tool because it could not determine
the current browser URL confidently enough to enforce policy. No page interaction
or visual/keyboard/responsive result is claimed. CUA completion summary recorded
the blocked browser verification. Do not bypass this restriction with another UI
automation mechanism. Local Vite session 90560 was stopped via Ctrl-C after this.
The next turn rechecked inventory: browser host still unavailable. User answered
that they would reconnect the browser; work continues independently in the meantime.
After allowing time for reconnection, another inventory check still returned
`browser access host is unavailable`. No native workaround was attempted. This
remains the external-state dependency for actual browser acceptance.

Final frontend typecheck/lint/contracts:check/build all exit 0 after normalization
and file-visibility fixes. Ruff/format/exporter/diff checks also exit 0. PR #52 has
two successful source CI check runs (observed via gh on 2026-11-05); this is not CI
for the still-local Prompt 7 changes. The implementation checkpoint is committed
locally to preserve the reviewed work; no Prompt 7 ready PR is opened before A07.

Reproduce the independent checks from the execution worktree:

```powershell
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp var/p7-final-backend --junitxml var/p7-backend-tests.xml
python scripts/export_contracts.py --check
ruff check .
ruff format --check .
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run contracts:check
npm --prefix frontend run build
# Optional real report SSR inputs, preserved locally from the approved candidate runs:
node frontend/scripts/test-report-view.mjs var/p5-candidate-flow-sqlparse-fead8de8d6e549fb9cb35f1f241f9a66/artifacts/3ece66c4-e87f-46c3-afff-a4d32d07f856/d41b553f-37ee-4ef6-83a1-a3f083d51778.json var/p5-candidate-flow-tinydb-d0fb9cfac3a846a3b6f2d49d7517207f/artifacts/b910fc2d-6070-420b-bc6c-2fd28cce6ce7/2a7ccbf0-73c1-48ef-9d98-48e967d323db.json
```

Use the locked task environment/PYTHONPATH/MinGit described in the prior handoff;
do not replace the separate PostgreSQL harness with its skips in the general suite.

Next: exercise actual JSON file load, malformed-file
error/recovery, REAL/DEMO/empty/partial/failed states, full run/revision/source metadata,
keyboard and narrow viewport when browser tooling is available. Record observed
results; only then finalize Prompt 7 PR and implementation acceptance. Human owners/
reviewers still approve their boundaries; merge does not itself close the sprint.

Keep-awake helper PID 17648 was verified alive during work; it has a 12-hour safety
expiry from 09:13Z. No permanent power plan change. Stop via task-owned sentinel
when actual execution ends, or renew if continued work reaches its expiry.

OpenAI Codex assisted implementation/tests/docs/self-review; no independent review,
mentor approval or contribution ratios are fabricated.
