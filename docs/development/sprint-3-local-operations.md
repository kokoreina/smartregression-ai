# SmartRegression local operations

Use `D:/smart-regression-ai/var/main-preview`, branch
`feat/web-repository-analysis`. Baseline HEAD is `5a30a7a`; the new web code is
local and uncommitted. Do not run the older root checkout or reset the worktree.

## Start and stop

The primary account database/configuration remain in ignored `var/auth/`. Never
paste their contents into chat, logs, screenshots or frontend variables. Existing
Gmail verification/recovery was confirmed by Huy during phase 2.

In one PowerShell terminal at the worktree:

```powershell
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = 'D:/smart-regression-ai/var/main-preview/var/auth/web.env'
$env:SMARTREGRESSION_GEMINI_ENV_FILE = 'D:/smart-regression-ai/.env'
$env:SMARTREGRESSION_WEB_MODE = 'product'
$env:TEMP = 'D:/smart-regression-ai/var/main-preview/var/phase3-8/browser-tmp'
.venv/Scripts/python.exe -m uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

In a second terminal:

```powershell
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173/login`. Product mode does not mount the old demo POST
routes. `/reports` is an independent local-file reader, including while signed out.
Stop each foreground service with Ctrl+C. Only one backend may hold the product
database lease; a second backend fails closed rather than interrupting live work.
An unexpected restart marks queued/running work interrupted; it does not rerun AI.

Python 3.14, Node 22.14–22.x/npm10, Git and Docker Desktop are the verified local
tools. Locked install commands are `uv sync --locked` and `npm --prefix frontend ci`.
Use the project caches `D:/smart-regression-ai/.uv-cache` and `.npm-cache` when
installing. Do not edit generated types or lockfiles manually.

## Local HTTPS packaging

Compose has a separate persistent database/volume. It does not copy primary
accounts, projects or AI grants, and must not be used to obtain a second acceptance
budget. The primary local campaign/ledger remain unchanged.

```powershell
.venv/Scripts/python.exe scripts/auth/prepare_https.py
npm --prefix frontend run build
docker compose -f deploy/local/compose.yaml build
docker compose -f deploy/local/compose.yaml up -d db
docker compose -f deploy/local/compose.yaml run --rm migrate
docker compose -f deploy/local/compose.yaml up -d backend frontend
```

Open `https://localhost:8443`. Caddy uses a local CA, with no host trust-store
installation. A browser security exception is expected outside the dedicated test
context. Browser acceptance uses a separate `ignoreHTTPSErrors` context; this does
not verify public TLS. PostgreSQL uses certificate validation with `verify-full`
and rejects network connections without TLS. Database/backend ports are not
published. Runtime has DML permissions only; migration is an explicit setup job.
Private configuration is generated under ignored `var/local-https/`; it includes
the already configured Gmail sender privately. The local DB certificate lasts 90
days and belongs to this local acceptance setup, not a public deployment.
The primary app reads the existing Gemini environment separately. The Compose
installation does not mount that credential and has no AI grant; saved outputs
remain readable there. Do not copy acceptance grants or reset ledgers to enable
another live campaign.

Stop with `docker compose -f deploy/local/compose.yaml stop`. Never use `down -v`,
Docker-wide prune or unqualified database/volume cleanup. Owned resources carry
the `smartregression.local-https` label. Input repositories are only parsed; there
is no web route that installs dependencies or executes their source/tests.

## Demo and saved real AI

Public demo repository: `andialbrecht/sqlparse`.

- Base: `91149dffdf691945dc5e20d9c9623390d9b96ffb`.
- Target: `be3b7a68d07af5a22b49765e26d2541be640999f`.
- Saved real run: `var/phase3-8/live-ai/sqlparse-run.json`.
- Saved hypothesis: `var/phase3-8/live-ai/sqlparse-hypothesis.json`.

Open these files at `/reports`. They preserve narrative, SHA, evidence and export
time. Importing does not create an authenticated server result or a new AI call.
The reader retains the prior valid report when the next JSON is invalid. The
live-offline browser test disabled networking before import and followed a real
Gemini citation to its evidence with keyboard focus.

Suggested 7–10 minute presentation: login/project; tree/search/TXT; choose commits;
run/history; explorer and one direct/indirect relationship; one overlay and A/B;
saved Gemini citation; dashboard/CSV/PDF; export/reload/import. The timed browser
rehearsals are automated flow checks, not evidence that a human presentation took
7–10 minutes. Label synthetic browser fixtures separately from the real sqlparse
AI outputs. Static impact does not prove a failure and no regression test was run.

## Limits and interpretation

- Python reuses the existing engine; JS uses Tree-sitter0.26.1/grammar0.25.0, `.js`
  relative imports and literal CommonJS only. No TS/JSX, bundler aliases, dynamic
  dispatch or cross-repository analysis. Syntax/unsupported cases stay partial.
- Tree: 5,000 entries. Acquisition: 1,000 files/16MB per snapshot, 20MB archive,
  1MB per file. The parser has a lower 256KiB file limit. No cap is raised for demo.
- Canvas: 150 nodes, separate full-scope totals and list pagination. Static calls:
  depth10, 150 visited nodes, 20 paths; unresolved/cycles have explicit stops.
- Impact counts changed/direct/indirect files without overlap. Percentages use
  analyzed file scope; missing/zero denominator is N/A, not failure probability.
- What-if is one existing Python/JS file, code/diff256KiB or description2,000 chars.
  It never modifies the original repository. A/B requires same repo/base/config.
- Search is bounded lexical retrieval, including accent normalization; it does
  not establish semantic equivalence. Entrypoint inference uses observed config.
- AI is explicit, metadata by default. Excerpts require separate consent and
  preview, max5 files/20KiB and the existing8,192-token limit. Source/prompts are
  not stored with provider requests; evidence ranges and context hashes are.
- Account quota starts at zero. Grants are operator-only. Reservations/unknown
  cost are distinct from actual cost; cached outputs never call the provider.
- Dashboard freezes summary/drilldown/export under the same repeatable-read view,
  expiring after24h. Runs use started_at; AI usage uses created_at. The status
  filter excludes snapshot-only assistance, as stated in the report limitations.
- CSV exports all matching rows up to10,000 and guards formula injection. PDF is
  browser print, with provenance/filter/limitations and no server PDF service.

## Backup and cache operations

```powershell
.venv/Scripts/python.exe scripts/auth/backup_local.py --restore-check
.venv/Scripts/python.exe scripts/auth/retention_local.py
.venv/Scripts/python.exe scripts/auth/explain_local.py
```

These commands validate the exact labelled primary development container/DB.
Backup uses a PostgreSQL exported snapshot, table counts/hashes and report artifact
hashes. Restore creates a random separate DB, checks readback, then removes only
that owned restore DB. It never restores over the primary database. Seven complete
local backup bundles are retained under `var/backups`.

Windows task `SmartRegression-MainPreview-LocalBackup` is registered daily at02:00,
with start-when-available, limited privileges and no overlap. It requires the same
user logged in and Docker available. Its definition is recorded under ignored
`var/phase3-8/backup-task.xml`. The runtime DB role has no DDL privilege. Cache
retention is dry-run unless `--apply` is explicitly supplied, only removes expired
unreferenced cache/view-state and preserves reports, scenarios, notes and AI anchors.

Off-host backup is not configured. Provisioning it requires an actual destination,
encryption recipient/key custody, restricted uploader credential and a restore
drill from that destination. A second directory/volume on this host is not off-host
backup. No upload or new provider is configured by this release.

## Verification and review

See the [phase3–8 handoff](sprint-3-phase-3-8-handoff.md),
[canonical audit75](sprint-3-phase-1-audit.md) and
[feature acceptance matrix](sprint-3-feature-acceptance.md). Public staging/email,
off-host backup, PR/main CI and independent review are separate pending gates.
No commit, push, PR, merge, public deployment or independent approval occurred.
