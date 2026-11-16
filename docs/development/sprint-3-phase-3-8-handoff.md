# Sprint 3 phases 3–8 — local technical handoff

## Release checkpoint — 15 November 2026

This section supersedes the historical checkpoints below. Canonical task states
are in [audit75](sprint-3-phase-1-audit.md), not inferred from old checkpoints.
Baseline HEAD remains `5a30a7ac5a1e2ad87a45120fe7c043bae49be5d4`, branch
`feat/web-repository-analysis`, worktree `D:/smart-regression-ai/var/main-preview`.
All implementation remains local/uncommitted. The original 76 dirty-file snapshot
is preserved in ignored `var/phase3-8/baseline/`; no reset, Git publication, public
deployment or deletion outside the project was performed.

Implemented: owner-scoped projects, durable/idempotent runs and AI requests,
PostgreSQL quota/activity, Python/JavaScript graphs, bounded calls/impact/hotspots,
immutable one-file overlays and A/B/version comparison, notes/resume, static
reading/search with optional consented AI, dashboard snapshots, full JSON/CSV and
offline import/browser PDF. See [PB25–PB44 feature matrix](sprint-3-feature-acceptance.md)
and [operations/startup](sprint-3-local-operations.md) for consumers and limits.

### Actual verification

- Full backend: `python -m pytest backend/tests` with project-local TEMP/basetemp,
  **1,103 passed, 172 skipped**, 698.93 seconds. JUnit:
  `var/phase3-8/backend-release-final.xml`. Skips are not passes.
- Real PostgreSQL harness: **167 passed, 4 historical candidate-run skips**,
  restart and restore checks passed. Evidence:
  `var/storage-verification-3c29100ea7d543adb02102cd428d381b/evidence.json`.
- Focused reporting/AI/retention PostgreSQL slice: **10 passed**, including
  10,001-row refusal, frozen export/drilldown and mixed null/zero/known usage:
  `var/storage-verification-0e20d1474a71481bafd42e7d96b56339/evidence.json`.
- `ruff check backend scripts` and `ruff format --check backend scripts`: pass,
  274 Python files formatted. Integration test import ordering/string wrapping
  was corrected after the full run; those changes do not change behavior.
- Frontend lint/typecheck/build pass. Vite warns that the main bundle is about
  730 kB (217 kB gzip); warning retained. The 150-node browser profile records
  cold/cache 2,665/2,327 ms and sampled JS heap about 14.6 MB, not peak/native
  process memory. Artifact: `var/phase3-8/browser-performance/result.json`.
- Two HTTPS browser rehearsals: 18 groups each, actual PostgreSQL/SMTP delivery,
  synthetic GitHub fixtures, no provider calls. Artifacts:
  `var/phase3-8/browser-https-rehearsal-{1,2}/result.json`.
- HTTPS security browser: five groups including guest/unverified, 22 cross-owner
  reads/exports, CSRF/Origin/spoofing, reset across two sessions, change/logout and
  rate limiting with Retry-After. `var/phase3-8/security-browser-https/result.json`.
- Browser regression first reproduced stale impact after switching commits while
  the new response was delayed. Explorer now scopes impact/evidence by SHA/path
  and ignores stale materialization navigation. Regression artifact:
  `var/phase3-8/request-identity/result.json`.
- Saved real narrative imported with networking disabled, citation followed with
  keyboard focus: `var/phase3-8/live-ai/offline-browser.json`.
- Backend exporter `--check` and frontend `contracts:check` passed: 88 validation,
  11 report SSR, 60 repository consumer SSR and 20 auth SSR checks. These are
  consumer checks, separately from the actual browser evidence above. The
  development runtime regression also preserved React dependencies across SSR.
- After restart, primary `http://127.0.0.1:5173` and Compose
  `https://localhost:8443` both rendered login/reload and the signed-out report
  reader and rejected legacy demo POST. No provider call or user credential was
  used: `var/phase3-8/restarted-app-browser.json`.
- Browser PDF rendered and visually checked with Poppler; Vietnamese and table
  layout readable. Local HTTPS certificate exceptions are explicit test context
  configuration and do not prove public TLS.

### AI campaign and pending gates

Campaign `sprint3-acceptance-20261115` has **10 used reservations / USD 0.20 held**.
Actual provider billing remains unknown for those records; a zero known subtotal
must not be described as zero cost. Old ledgers remain intact. No more generation
or reservation release is permitted under this campaign.

Successful live types: commit narrative, hypothesis, reading guide, search and
file explanation. Folder output was rejected, and the last bounded-schema attempt
returned `provider_configuration`. Static folder context, consent/citation checks
and fallback exist; **live folder is still pending**. Saved full real outputs:
`var/phase3-8/live-ai/sqlparse-run.json` and `sqlparse-hypothesis.json`.

Eight tasks remain Ongoing: **3.09, 3.13** (folder live), **3.14** (PR/main CI/review),
**3.15** (full acceptance dependencies), **3.33** (staging email), **3.43** (public
staging), **3.44** (off-host backup), **3.60** (independent review). The other 67
task entries record local AC self-verification, not external approval. No estimate
was copied into actual effort and no human contribution/signature was invented.

### Storage, operations and review boundaries

Migration head `20261115_15` is applied to the owned primary development database.
Compose has its own persistent database, runtime without DDL, PostgreSQL
certificate validation, Caddy HTTPS loopback8443 and no published database/backend
ports. Compose is a separate installation: it does not inherit primary accounts
or AI grants and must not be used to replenish the acceptance budget.

Daily limited-user Windows task `SmartRegression-MainPreview-LocalBackup` is
registered at02:00, with start-when-available and no overlap; Docker and the same
logged-in user are required. Backup uses a consistent exported PostgreSQL snapshot,
checks table/artifact hashes and restores into an isolated disposable database
with application readback. Seven recognized local bundles are retained.
Off-host encryption/upload needs an actual destination and remains pending.

Final backup and isolated restore passed:
`var/backups/backup-20261115T100959Z-e98c137c4c164db4874fbd313edb0ff7.json`.
The daily task was observed Ready. Dedicated browser fixture shut down gracefully
and removed its disposable database/role; the test-only8444 proxy was stopped.
Primary5173/8000 and Compose8443 are left running.

Workbook source and review copy were updated only after artifact-tool authoring,
XML preservation assertions and read-only native Excel/Poppler visual QA. Final
output: `outputs/sprint3-phase3-8/SmartRegression_AI_Scrum_Project_Aligned.xlsx`.
Verification preserves 68 unrelated ZIP parts, IDs/PBs/owners/English descriptions,
formulas, layout, validations and actual effort. It records 67 Done / 8 Ongoing,
with local/self-verification qualifications. Evidence:
`var/phase3-8/workbook/workbook-verification.json`.

Configured-private-value scan of changed/untracked nonignored files and the
frontend bundle found no matches. Documentation links and all76 preserved
baseline file hashes passed. `var/phase3-8/release-self-check.json` records scope;
this bounded scan does not prove absence of every possible secret.

Review group A: backend/contracts, additive migrations, parser/storage/security,
operations and generated OpenAPI. Group B: frontend/generated TypeScript,
browser/SSR tests, documentation and workbook. No commit/PR was created. This is
technical self-check by the implementing agent, not independent review.

AI disclosure: Codex assisted coding, debugging, tests and documentation. The human
author must review and understand the changes under the project's policy. Nothing
here asserts mentor approval or a measured contribution percentage.

## Historical checkpoints below

The following notes describe earlier work-in-progress states only. Their older
migration, test and budget statements must not be used as current status.

## Historical checkpoint — graph/scenarios and assistance/reporting

- Migration head is now `20261115_15`; the user's owned local database is still
  at `_13` until verified upgrade/restart. Running backend may serve older routes.
- Notes and immutable code/diff/hypothesis scenarios, A/B and graph evolution are
  implemented. Overlay provenance is distinct from Git; graph containment metadata
  does not invent line numbers. Scenario PostgreSQL slice: 21 passed, restore pass,
  `var/storage-verification-bb7d97c52e65439ca4fd162ae69c035f/evidence.json`.
- Static reading guide and bounded lexical feature search now support Python/JS,
  Vietnamese accent normalization, explicit unknown/no-evidence and exclusions.
  Scoped Gemini file/folder/search/reading/hypothesis actions share existing grants
  and atomic quota. Excerpts require separate consent and preview, stay in memory;
  persisted provenance contains ranges/context hashes, not raw prompts/source.
- PostgreSQL scoped AI and schema: 6 passed, including shared quota, replay,
  owner isolation and metadata-only persistence:
  `var/storage-verification-ae4e542aae5f42cbbb5f807b7acc1f46/evidence.json`.
- Dashboard snapshots freeze summary/drilldown/export with repeatable-read;
  separate known cost, unknown records and reservation. Versioned durable
  run/scenario downloads and independent `/reports` offline reader added.
- Latest browser fixture: **13 groups passed**, actual PostgreSQL + SMTP,
  synthetic GitHub and no live provider: graph, source, notes/resume, payment.js
  overlays/A-B, static assistance, JSON download/offline/reject malformed import,
  dashboard/CSV/PDF and responsive states. `var/phase3-8/browser/result.json`.
  Prior A/B screenshot inspected visually. This is not full end-to-end acceptance.
- Unit assistance/reporting slice: 7 passed; related narrative/schema slice:
  19 passed. Current full backend/PostgreSQL suites are running. Initial full
  backend collection found duplicate test module names; explicit test packages
  added and rerun. Docker restart mapping check now waits for a loopback-only
  mapping to become ready rather than assuming it exists immediately.
- No new Gemini generation. Acceptance grant remains 10 / USD 0.20, zero consumed.
- Remaining: complete security/browser matrix, retention/backup/restore and local
  HTTPS/Compose, live AI smoke within cap, final audit75/Excel/docs/feature gates.
  No phase or task batch marked Done by this checkpoint.

Implementation started 15 November 2026 in `var/main-preview`, baseline
`5a30a7ac5a1e2ad87a45120fe7c043bae49be5d4`. Existing 76 dirty files were copied and
hashed under ignored `var/phase3-8/baseline`; no Git publication is authorized.

The user authorized the six-phase plan, local HTTPS first, a new acceptance AI
campaign capped at USD 0.20 / 10 generations (USD 0.02 each), preserving historical
ledgers. No new generation has been made by this implementation checkpoint.
No deletion outside the project, VPS/domain purchases, public deployment or Git
commit/push/PR/merge. Independent approval cannot be self-issued.

## Checkpoint 1 — projects and durable static-run foundation

- Added owner-scoped projects, optimistic version conflicts, atomic three-active
  limit, archive/restore and transactional append-only activity. Repository URL is
  immutable for a project. Product routes enforce session, verified email and CSRF.
- Added project UI connected to real API, retaining existing account and local demo.
- Frozen migration `20261115_08` adds projects/activity; metadata and test harness
  include the additions without changing historical migrations/research meanings.
- PostgreSQL campaign **147 passed, 4 historical skips**, restart and restore pass:
  `var/storage-verification-73dc4bee6006467fa3d0814a878a9456/evidence.json`.
- Project contract/session/CSRF + storage-schema tests: **4 passed**. Frontend
  typecheck/build and lint pass after sandbox esbuild restriction was resolved.
- Run requests/lifecycle and legacy repository analysis/schema targeted suite:
  **27 passed**; sandbox tmpdir errors were rerun in the authorized environment.
- Migration `20261115_09` and run publication/recovery tests are being verified.
  Static reports reuse the immutable research report store, with owner-scoped web
  lifecycle records and full response sidecars. Do not mark run tasks accepted yet.
- Dependencies installed through tools: Tree-sitter 0.26.1, JS grammar 0.25.0,
  React Flow, Dagre and Playwright. No generated file or lockfile was hand edited.

## Next work

Finish run PostgreSQL verification and UI, quota, dedicated browser/SMTP fixture,
local backup/migration/restart of the owned development database, then continue
graph/what-if/assistance/dashboard/final acceptance in the accepted order. Existing
Gmail verification/recovery manual evidence remains in phase-2 handoff.

Public staging/email, off-host backup, PR/main CI and independent acceptance remain
external gates under the user's selected local-only delivery. The 75-task audit is
the status source; this handoff records evidence, not a second backlog.

## Checkpoint 2 — durable runs, quotas, browser and explorer

- Root cause fixed in project registration: provision the validated GitHub identity
  in the canonical repository catalog, atomically with project creation. Existing
  report-store provisioning guards remain unchanged.
- Run/report PostgreSQL diagnostic: 11 pass; publication, owner readback, interrupted
  recovery, idempotency and archive guards verified. Artifact
  `var/storage-verification-ed7017f9815846419164d58cb02bf986/evidence.json`.
- Added campaign/account grants, atomic conservative reservations and separate AI
  request lifecycle. Zero quota by default, no public grant API, unknown costs stay
  reserved. PostgreSQL quota diagnostics: 15 pass; artifact
  `var/storage-verification-f08dbd5beb33451d93e1ef54ff291872/evidence.json`.
- The explicit acceptance grant has been provisioned idempotently for the verified
  configured sender account. No Gemini generations have been called at this point.
- Dedicated Chromium browser with isolated profile and real PostgreSQL/SMTP fixture:
  seven groups pass: signup/mail confirmation, login/project reload, static run and
  canonical readback, three viewport widths, basic keyboard/reduced-motion. Synthetic
  GitHub transport is labelled; no live AI or full accessibility acceptance implied.
  `var/phase3-8/browser/result.json`; mobile screenshot inspected visually. Windows
  MIME issue in test server fixed, expected guest /auth/me 401 separated from errors.
- Added Python reuse + Tree-sitter JS explorer graph/calls/hotspots, immutable source
  cache with digest checks, owner-scoped bounded APIs, React Flow/Dagre UI and source
  range inspector. Initial six independent fixtures pass; added shadowing negatives
  while hardening the supported static-call scope.
- Added versioned notes/pins and debounced resume state. PostgreSQL latest diagnostics
  **19 pass**, upgrade/restart/restore pass:
  `var/storage-verification-6152cd23d3324dd49f0bf1bd761cd14d/evidence.json`.
- Current migration head `20261115_12`; local user database was backed up/upgraded
  through `_10`; upgrade remaining head and restart actual app after verification.
  Legacy app server may still serve prior backend until that owned restart.
- Next: finish graph/browser checks, retention, immutable what-if/A-B/version diff,
  then assistance/dashboard/HTTPS/backup/final gates. No task batch marked Done.
