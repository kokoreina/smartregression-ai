# Web repository analysis — local MVP, 2026-11-10

## Repository tree addition — 2026-11-13

Entering a public GitHub URL and choosing **Đọc repository** now loads an expandable
folder/file tree at the newest returned commit. Search preserves parent folders;
selecting a file shows its path and size. Download exports the complete tree as text
with repository URL and commit. **Xem cây tại target commit** reloads a chosen SHA.
Only committed paths appear; local-only dependencies are not invented.

`POST /repositories/tree` accepts repository URL and a full commit SHA. It verifies
the public repository, commit-to-tree identity and complete recursive Git metadata.
Limits: 5,000 entries, 40 path segments, 2,048 characters/path and the existing 2 MB
JSON cap. Invalid/duplicate paths, missing parents and truncated trees fail visibly.
Symlinks and submodules are displayed without following their targets. This path
does not download blobs/archives, execute code, call Gemini or require consent to
LLM egress. Existing snapshot limits still apply to impact analysis.

The tree supports arbitrary file extensions as metadata. It represents containment,
not dependency or behavioral impact. Existing two-commit Python analysis remains
separate; a general dependency graph or arbitrary-file what-if analysis is not
implemented by this addition. No database or dependency changes were needed.

Verification for this addition:

- Repository-tree/web, stage-report and API integration subset: **100 passed**, two
  existing SDK warnings. Ruff, OpenAPI exporter `--check` and `git diff --check` pass.
- Frontend lint/build and contracts:check pass; **88** report validation checks,
  **11** report SSR checks and **31** repository consumer/SSR checks pass.
- Live local API request for `X-BRAIN-CDO-09/Triage-Hub-CDO09` at
  `abd8c751ed5941f6bd89bdbe7e6e6f38c0056345`: HTTP 200, **434 entries**, including
  **106 directories and 328 files**. Ignored evidence: `var/tree-live-triage.json`.
  This is a real metadata check, not successful full-repository impact analysis.
- Browser tool reported host unavailable; interactive, keyboard and visual browser
  acceptance remains unverified. No paid LLM call or full-suite rerun in this change.


Baseline `5a30a7a` (PR #68 merged); implementation branch
`feat/web-repository-analysis`, worktree `var/main-preview`. Huy requested a usable
GitHub repository → static impact → Gemini explanation path in the local dashboard.
This is an additive web slice, not completion of Sprint 3 selection/execution/G2.

## Use

Open http://127.0.0.1:5173/, enter a public GitHub URL and choose **Đọc repository**.
Choose two full commit SHAs (recent commits are supplied), enter an optional focus
question, enable Gemini and consent to the displayed metadata egress, then choose
**Phân tích thay đổi**. Unticking Gemini gives static analysis without paid calls.

The result shows target file structure, the existing canonical v2 stage report,
changed-file impact filtering, validated model explanations, exact bounded metadata
observations and downloadable v2 JSON. Existing report-file/DEMO viewing remains
under a separate disclosure. Loading, errors and model failure preserve honest
not-run states; no selection or execution is inferred.

```powershell
$env:SMARTREGRESSION_GEMINI_ENV_FILE='D:/smart-regression-ai/.env'
uv run uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

The env-file path is an explicit trusted operator configuration, never chosen by a
request or input repository. Alternatively set canonical backend `GEMINI_API_KEY`.
No automatic dotenv discovery or key in frontend. Reuse the existing model,
Developer API client factory and v1beta compatibility settings.

## Architecture and limits

- API → `RepositoryService` → existing `application.analysis` snapshot, change,
  graph, potential impact and evidence producers. A separate narrator port provides
  metadata explanations, not regression-test proposals with an invented inventory.
- `GithubRepository` accesses only pinned HTTPS `api.github.com` and
  `codeload.github.com` endpoints derived from a validated public GitHub owner/repo.
  No auth token, private repo, arbitrary URL, redirects, Git hooks, clone checkout,
  subprocess or repository-code execution. Archives stay in memory. Every file is
  matched against the full commit's Git tree and its native blob hash; existing
  immutable snapshot identities are preserved.
- Limits: 1,000 files, 1 MB/file, 16 MB/snapshot, 20 MB archive response, 4,000 zip
  members, 2 MB API JSON, bounded acquisition deadline/timeouts. Symlinks/submodules,
  truncated trees, export-ignore archive mismatch and unsupported paths fail visibly.
  Rename is represented as delete+add; no similarity guess. Python AST/import scope
  is explicit; import paths do not prove behavioral effects.
- Local use only: bind to loopback, reject hostile Host/Origin on operations, require
  JSON and cap POST bodies to 8 KB. One lookup/analysis at a time; no durable job or
  cancellation protocol. Browser timeout stops waiting, not necessarily server work.
- Gemini receives only bounded paths, symbols, commits, static change/import/impact
  observations and the user's question. No source/excerpt. Content is untrusted data;
  function calling and SDK automatic continuation are disabled. Validate JSON then
  exact observation IDs and their associated paths; never render raw HTML.
- One generation attempt, 5-second pre-count, 15-second generation, 25-second overall
  provider deadline; 8,192 counted input and 2,048 output/thinking token caps.
  Existing atomic locked ledger `var/web-analysis/budget.json` enforces 5 runs/session,
  USD 0.02/run, USD 0.10/session. Unknown usage keeps the full 7,578 micro-USD
  reservation; displayed unknown cost stays null. Never auto-reset the ledger or
  silently switch model/API. Price/config limitations from task 3.16 remain applicable.
- Reports are returned to the browser, not persisted to PostgreSQL by this slice.
  The independently restored inspection database is unchanged. No schema migration.

## Verification

Focused automated checks cover public URL/redirect rejection, archive/blob identity,
path traversal/symlink/size/truncated-tree rejection, canonical static orchestration,
host/origin/body/validation redaction, egress consent, exact counted/generated wire,
unknown model references, timeout/no retries, persistent five-run budget, explicit
credential conflicts and consumer rendering/escaping. SDK/GitHub boundaries are
recorded doubles, not paid unit calls.

Live local API inspection read `andialbrecht/sqlparse`, 10 recent commits; a real
two-commit run returned 94 target files, 5 changed files and 55 potential impact
candidates. Gemini `gemini-3.5-flash-lite` returned validated Vietnamese metadata
explanations, 7,380 total reported tokens. That is a real-source metadata smoke, not
a benchmark or proof all impacts are correct. Selection/execution remain not_run.
Artifacts and exact SHAs/request/results are ignored files under `var/web-*`.

Schema/types are regenerated using the existing exporter and TypeScript generator.
Existing `httpx` is promoted from dev-only to runtime using uv; no new package or
version upgrade is intended. No locks are edited manually or settings/permissions changed. Browser host
availability is separate from SSR/HTTP verification; no browser pass is implied.
## Observed final checks

Python 3.14.3, existing locked environment `../s3-gemini/.venv`; explicit
`PYTHONPATH=backend/src`, local TEMP, portable Git 2.56.0 on PATH. `httpx` promotion
was performed with `uv add --no-sync` then `uv remove --dev --no-sync`; lock diff
changes only the root dependency classification, no package versions. `uv lock --check` passed.

```powershell
../s3-gemini/.venv/Scripts/python.exe -m pytest backend/tests/integration/test_api.py backend/tests/integration/test_analysis_cli.py backend/tests/unit/test_repository_web.py backend/tests/unit/test_repository_narrative.py backend/tests/unit/test_stage_reports.py backend/tests/unit/test_gemini_smoke.py -q -p no:cacheprovider --basetemp var/web-api-verified --junitxml var/web-api-verified.xml --tb=short
../s3-gemini/.venv/Scripts/python.exe scripts/export_contracts.py --check
../s3-gemini/.venv/Scripts/ruff.exe check .
../s3-gemini/.venv/Scripts/ruff.exe format --check .
npm --prefix frontend run contracts:check
npm --prefix frontend run lint
npm --prefix frontend run build
node frontend/scripts/test-repository-view.mjs var/web-analysis-final-vietnamese.json
```

- API/CLI/contracts/legacy Gemini smoke subset: **114 passed**, 2 upstream SDK
  warnings, 117.40s, exit 0. Final Vietnamese prompt plus new-route/API narrator
  subset: **28 passed**, 10.03s, exit 0.
- Frontend canonical validation: 88 checks; existing report SSR: 11 checks.
  Repository UI/consumer guards: 12 fixture checks plus one final real report
  render, **13 passed**. This covers metadata citations, escaping, invalid model
  metadata, malformed versions/outcomes and duplicate citations; not browser input.
- Lint, formatting, exporter, generated TypeScript, frontend lint/typecheck/build,
  lock and diff checks passed. No browser click/visual acceptance: Browser host was
  unavailable and native Chrome automation was previously stopped by its tool.
- Broad backend run 1: **1019 passed / 1 failed / 132 skipped**, 648.07s. The failure
  was a historical assertion that only `/health` exists. It was updated to require
  exactly the health route and both new POST contracts, without weakening report checks.
- Broad run 2: **1024 passed / 1 failed / 132 skipped**, 786.71s, before the final
  middleware scope fix had been loaded. Its remaining failure was POST to unknown
  routes returning 415 instead of legacy 404. JSON/body guards now apply only to
  the two new routes; the subsequent API/CLI regression above and actual HTTP
  `/api/analyze` verify 404. No final all-green full-suite run is claimed.
- One diagnostic CLI run without portable Git failed 6 cases (`invalid_commit`);
  system Git 2.44 lacks the existing adapter's flags. Rerunning with the required
  portable Git passed all 114 cases; no product Git behavior was changed.

Final real HTTP request through Vite `/api/repository-analyses`:

- Repo `andialbrecht/sqlparse`, base `91149dffdf691945dc5e20d9c9623390d9b96ffb`,
  target `be3b7a68d07af5a22b49765e26d2541be640999f`.
- Run `0f5cbcb1-9a7b-4c07-8a9e-2c950c8dcb99` was a valid live response but its summary
  was English despite the original instruction. Prompt revision 2 explicitly adds
  Vietnamese-only wording; a subsequent live run succeeded in Vietnamese.
- Final response `var/web-analysis-final-vietnamese.json`: 94 files, 5 changed files,
  55 potential impact candidates, 128 displayed metadata observations; Gemini
  `gemini-3.5-flash-lite`, input **6641**, output **656**, total **7297**, provider
  duration **5.967s**. Thinking and billed cost remain null. Response validates with
  canonical backend models and frontend renderer.
- Three total live web runs in the same ledger; unknown reservations retained,
  no session reset. Earlier synthetic sessions and database inspection are untouched.
  API key was read from the explicit trusted backend file and never printed.

Reports remain local/unpersisted, no tests of the input repo were run, and this
branch is not committed, pushed, independently approved or merged by this task.

## Repository failure diagnosis — 2026-11-10

The user's `X-BRAIN-CDO-09/Triage-Hub-CDO09` request reproduced HTTP 422
`github_rate_limit` through Vite, without enabling Gemini. GitHub's unauthenticated
API returned HTTP 403, remaining 0 of 60 requests. Separately, authenticated `gh`
read-only tree inspection of target `abd8c751ed5941f6bd89bdbe7e6e6f38c0056345`
found 328 files totalling 125,604,953 bytes, including a 51,384,541-byte video
and several oversized JSON datasets. This snapshot also exceeds the current
acquisition limits; waiting for rate-limit reset alone will not make it supported.
No authentication policy, acquisition caps or snapshot completeness was changed.

Three regression cases reproduced lost error codes: rate limit, timeout and size
limit during snapshot acquisition became `snapshot_acquisition_failed`. The shared
analysis allowlist now preserves those three safe codes. The consumer explains
that file limits also include datasets/media, and gives a specific acquisition
fallback without exposing arbitrary server exception text. Report schema unchanged.

Verification: `pytest` repository-web, stage-report and API integration modules:
**88 passed**, 2 existing SDK warnings. Repository consumer/SSR checks: **17 passed**,
including safe API-error rendering. Ruff check/format, frontend lint/build and
`git diff --check` passed. Preview backend restarted; live `/health` returned 200
and the user's no-LLM request still correctly returned `github_rate_limit`.
No paid generation, full-suite rerun or browser acceptance was performed here.

## Demo completion checkpoint — 2026-11-15

### Scope and baseline

Huy is authorized to implement all six demo packages: 3.01, the demo slices of
3.02/3.04, 3.64, 3.68, 3.12 and 3.73/3.75. These IDs refer to the revised 75-task
web backlog, not the archived research Sprint 3 numbering. This checkpoint does
not mark the full parent tasks or the 18-feature sprint Done.

Worktree: `D:/smart-regression-ai/var/main-preview`, branch
`feat/web-repository-analysis`. Fetch succeeded; HEAD and origin/main were both
`5a30a7ac5a1e2ad87a45120fe7c043bae49be5d4` at inspection. Existing dirty work was
retained. No commit, push, PR, database migration or dependency installation.

Profiles: Coordinator, Backend/Contracts, Frontend and RAG/LLM; rules
00/01/02/03/06/08/13. Skills: api-contracts, test-driven-development, ui-design,
accessibility-review, security-review, webapp-testing and systematic-debugging.
Checks below are self-verification, not independent review.

### Changes

- Added canonical `RepositoryReportExport`: kind `repository-analysis`, format
  version `1.0.0`, timezone-aware `exported_at`, and the complete response payload.
  Export time is explicitly not analysis time. Existing endpoints and stage-v2
  report format remain compatible. OpenAPI and TypeScript were regenerated.
- Full JSON download now preserves Gemini narrative, metadata evidence, usage,
  pinned commit identity and limitations. Offline import validates the envelope
  or legacy full response; legacy reports show unknown time. The old stage-v2
  loader is preserved. Import checks the existing 16 MiB file limit before reading.
- Added duplicate-request and stale-response guards, cleanup on unmount, immutable
  displayed report identity, and preserved analysis results while refreshing tree.
- Added evidence links opening the metadata details and moving keyboard focus,
  explicit impact units, an accessible workflow outline, responsive wrapping and
  reduced-motion-aware hover transitions. Tree includes repository/target identity.
- Invalid JSON, unsupported version, invalid timestamp, broken/duplicate citations,
  malformed metadata and non-JSON proxy failures are rejected with bounded errors.

### Actual checks

Environment: existing Python 3.14.3 in `../s3-gemini/.venv`, Node 22.14.0,
portable Git in `../task-2.13-tools/mingit/cmd`. No clean install is claimed.
Commands use worktree root unless marked frontend; Python uses
`PYTHONPATH=backend/src` and portable Git prepended to PATH.

| Check | Actual result |
| --- | --- |
| pytest repository-web/tree/narrative/export, stage reports, API integration | 113 passed, exit 0; `var/demo-verified-20261115.xml` |
| Ruff check and format check | Passed; 326 Python files already formatted |
| `python scripts/export_contracts.py --check` | Passed |
| `npm --prefix frontend run contracts:check` | 88 report validation, 11 report SSR, 51 repository checks passed |
| `npm --prefix frontend run lint` and `build` | Passed; build includes TypeScript |
| `node frontend/scripts/test-repository-view.mjs var/web-analysis-final-vietnamese.json var/demo-static-20261115.json` | 53 checks passed, including full response export/import round trips |
| `git diff --check` | Passed |
| Actual Vite proxy inspect/tree | HTTP 200; target tree 106 entries / 94 files |
| Actual Vite proxy no-consent AI request | HTTP 422; no provider call |
| Actual Vite proxy static analysis | HTTP 200; 94 files, 5 changed files, 55 impact candidates; AI not_run |

Initial sandbox pytest run failed on temporary-directory permissions; the same
subset rerun with appropriate local access passed. Vite initially hit sandbox
spawn EPERM; later consumer/build checks passed outside that sandbox restriction.
One diagnostic SSR run emitted a dependency-scan shutdown warning; the final
contracts gate passed without that warning. No full backend suite was rerun.

### Gemini and browser limits

The existing ledger already contains 5/5 runs. It was not reset or increased.
No paid generation occurred in this checkpoint. Historical real Vietnamese Gemini
output was revalidated with backend and frontend; model
`gemini-3.5-flash-lite`, 128 metadata observations. This is historical output, not
a fresh provider success. Gemini failure fallback remains covered by mocked tests.

Browser host is unavailable. After the user restored Chrome, native accessibility
was unavailable and Computer Use stopped because it could not verify the browser
URL. No further native/browser automation was attempted. Interactive inputs,
focus movement, download dialog, responsive rendering and two rehearsals remain
unverified; SSR and HTTP checks do not replace these checks.

### Local demo and manual acceptance

Services started by this task: backend on `http://127.0.0.1:8000`, frontend on
`http://127.0.0.1:5173`. Both bind only to loopback.

1. Open frontend; read `https://github.com/andialbrecht/sqlparse`.
2. Set base `91149dffdf691945dc5e20d9c9623390d9b96ffb`, target
   `be3b7a68d07af5a22b49765e26d2541be640999f`; load target tree.
3. Search and select a file; press Enter in tree search and confirm no analysis
   starts. Expand/collapse using keyboard; check a narrow window and long paths.
4. Disable Gemini for a fresh static run. Check changed-file filter, potential
   direct/indirect relationships and full commit identity. Refresh tree and confirm
   the report remains visible. Changing base/target must clear the old report.
5. Use **Mở báo cáo đã lưu** with
   `var/demo-20261115/sqlparse-gemini-saved.json` to demonstrate historical real AI.
   It must say **Báo cáo đã lưu**. Follow an evidence link and verify focus lands on
   the referenced entry. This opens a local file; it is not a fresh Gemini call.
6. Download the full JSON, reload, reopen it; verify AI/evidence remain. Repeat
   offline with the backend stopped when convenient, then restart for the demo.
   Invalid JSON must show an error and retain the previous valid report.
7. Rehearse twice; report any failed steps instead of marking browser acceptance.

Saved artifacts are local under `var/`, not deliverable source: real static HTTP
response, target tree, exported historical Gemini response and test XML. The saved
AI file's timestamp is today's export time; analysis time is not recorded.
The web analysis flow still has no PostgreSQL history, auth or input-repo test
execution. Those features and full parent-task acceptance remain separate work.

## Blank dev page fix — 2026-11-15

The reported blank Chrome page was traced to Vite's React dependency URLs:
`/node_modules/.vite/deps/react*.js?v=...` returned HTTP 504 and the shared `deps`
directory was missing. The SSR test servers used the same default cache directory
as the running frontend. SSR optimization/cleanup could invalidate the live cache;
HTML and API still returned 200, which did not prove client rendering.

Both SSR scripts now use distinct cache directories and disable unused client
dependency discovery. No application/API contract or dependencies were changed.
Vite was restarted with `--force` to rebuild the damaged dev cache.

`node frontend/scripts/test-dev-runtime.mjs http://127.0.0.1:5173` reproduced the
504 before the fix, then passed after it: application React runtime URLs remained
HTTP 200 JavaScript before and after both SSR suites (11 report and 51 repository
checks). This opt-in local-server regression does not replace browser acceptance.
Native Chrome verification was again stopped by the tool because it could not
verify the browser URL. No interactive or visual pass is claimed.
