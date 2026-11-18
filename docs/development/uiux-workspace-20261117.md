# Local workspace UI and explorer fix

Implemented on 2026-11-17 in `D:\C1.SE26\Repo`, branch
`feat/web-uiux-project-workspace`. Baseline is main
`a55e44bc52eea22387c1d174f13d78eae80d2b99` (PR #69). A remote main check at the
end of this session returned the same commit. Changes are local and uncommitted.

## Behavior and design

Opening a signed-in project previously showed administration/history first.
The explorer required a manually entered commit and one rejected graph/tree
request could hide the entire workspace. Project detail now opens the explorer,
with separate sections for analysis/history, activity and settings.

On first entry, the explorer checks saved view state before resolving and opening
the latest public repository commit. A saved or explicit commit only reads the
cached snapshot until the user chooses to open it again. A failed saved-state
request does not silently replace the saved position. Tree, graph, node list and
hotspots can fail independently. Selecting a file shows its potential static
impact, with a visible failure state when the request fails. Selecting the same
file again retains its impact result.

The visual direction is evondevKit Clean / Neutral with a light labeled sidebar,
muted blue controls and native system typography, following the user's visual
review. Mobile navigation supports Escape; the explorer switches
between tree, graph and details at small widths. See [DESIGN.md](../../DESIGN.md)
for layout, tokens and rationale.

Main changes: `frontend/src/app/workspace.css`, `Application.tsx`,
`features/projects/Projects.tsx`, `features/explorer/Explorer.tsx` and
`ResumeState.tsx`. No backend source, migrations or public contracts changed.
The interim font package was removed with npm when switching to native fonts. Generated types were not
edited. The user-requested evondevKit skill is installed project-locally at
[.agents/skills/ui-ux](../../.agents/skills/ui-ux/SKILL.md), pinned to upstream
`5a892ceac93d1bb286391663eb01cbd011706886`; provenance and MIT license are included.

## Verification

Commands ran on Windows. Final Node checks invoked Node 22.14.0 directly with the
installed npm CLI, with its binary directory prepended to the process PATH so
child scripts also use Node 22. The system Node installation was not changed.

| Check | Result | Scope |
| --- | --- | --- |
| `npm --prefix frontend run lint` | Pass | Final frontend source |
| `npm --prefix frontend run build` | Pass | TypeScript and Vite production build |
| `npm --prefix frontend run contracts:check` | Pass | 88 report validation, 11 report SSR, 60 repository consumer/SSR, 20 auth transport/UI checks |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Pass | Contract export consistency |
| Targeted pytest files `test_explorer_graph.py`, `test_projects_unit.py`, `test_repository_web.py` | 38 passed | Relevant backend regression coverage |
| `npm --prefix frontend run test:workspace` | 29 passed | Mock API browser regression and theme cases described below |
| `git diff --check` | Pass | Whitespace consistency |
| Manual signed-in local project | Pass | Real API, local PostgreSQL, public TinyDB snapshot, tree selection and impact including reselecting the same file |

The browser suite at `frontend/tests/project-workspace.spec.mjs` covers automatic
initial acquisition, independent request failures, saved-state restoration,
explicit commit links, saved-state unavailability, visible impact errors, mobile
selection/navigation and horizontal overflow at 375/768/1024/1280/1440px. Its API
fixtures and screenshots are labelled DEMO; these are not evidence of remote
account data or analysis quality. Artifacts are under ignored
`var/uiux-playwright/`. It also checks that the inspector remains in the third
column at 1152px, without an inherited breakpoint pushing it below an empty column.

`saved-reports.spec.mjs` covers signed-out reading, keyboard file selection,
original-byte JSON download, invalid replacement, the 16 MiB limit, drag/drop
including multiple-file rejection, scenario hypothesis labeling and responsive
layout. `dashboard-start.spec.mjs` checks actual-project rendering, empty and
unavailable project responses, responsive layout and no automatic reporting POST.

`theme.spec.mjs` adds OS/manual preference, reload and cross-tab synchronization,
blocked storage behavior, pre-React initialization, login/skip-link colors,
representative AA text contrast and readable print output. The dark explorer case
checks all three panel surfaces as well as graph nodes and controls. See the
[product analysis and review](uiux-review-20261117.md) for findings and resolution.

## Follow-up visual review

The user found the first neutral version too sparse and supplied examples of
duplicated labels. Source scanning across the frontend found no duplicated retry,
logout or offline labels matching the screenshots; their alternate translations
were absent from the source. The existing HTML language was already Vietnamese.
Standard no-translation flags were added to discourage bilingual injection and
changes to file paths; extensions can override those hints. One awkward phrase
in evidence status copy was shortened without changing its meaning.

The review identified a tall project header, a plain report import screen outside
the app shell, and a dashboard with only filters before loading a reporting view.
The resulting UI has a compact project header, stronger work-panel boundaries,
clear active navigation and a real report drop target. Reports share the shell
while remaining public for offline file reading. Dashboard startup uses existing
project responses for continuation links and provides a report entry point.
It does not create metrics, analysis jobs or reporting snapshots automatically.

Manual checks used the local QA account, the real TinyDB tree/impact and a clearly
marked DEMO stage-report fixture for import. Current screenshots are
`var/uiux-dashboard-neutral.jpg`, `var/uiux-reports-neutral.jpg` and
`var/uiux-workspace-neutral.jpg`.

The final reports quick probe is under `var/uiux-probe-reports-neutral/` and marks
zero items as “Hỏng”. Its remaining advisory categories include signed-out 401,
hidden native file input, scrollbar parsing, content-row height differences and
the intentionally stronger dividers. Small-label and narrow-title findings were
adjusted after the probe. These heuristics are not a full accessibility audit.

The installed skill's quick login probe ran at the same five widths, with zero
items marked “Hỏng” in `var/uiux-probe-login-final/report.json`. Advisory groups
remain: the expected signed-out `/auth/me` 401; the password field width heuristic
beside its show/hide button; and the scrollbar parser's transparent-thumb result.
This is not a claim of a complete accessibility audit. The production build
retains Vite's large-chunk advisory (about 737 kB before gzip); code splitting was
not part of this change.

The real manual project is labelled `TinyDB · kiểm thử UI local`, from public
`msiemens/tinydb`, snapshot `edff96aeb2616402e9489d46e90a592c05565621`.
Selecting `tinydb/table.py` returned 1/21 changed, 3/21 direct and 7/21 indirect
files. Coverage is partial, with 1435 unresolved relations and 44 unsupported
files; these counts do not represent fault probability or proof of safety.
The captured real view is `var/uiux-real-desktop.jpg`.

## Running locally

Frontend is running at `http://127.0.0.1:5173`; backend at
`http://127.0.0.1:8000`. The task created a separate labelled local PostgreSQL
container with the repository's `scripts/auth/prepare_local.py` and
`scripts/auth/migrate_local.py`. Its private configuration remains in ignored
`var/auth/web.env` and `var/auth/local-context.json`. Existing containers and the
machine's other PostgreSQL service were not changed.

To restart the backend from the repository root after stopping the current one:

```powershell
$env:PYTHONPATH = 'D:\C1.SE26\Repo\backend\src'
$env:SMARTREGRESSION_WEB_ENV_FILE = 'D:\C1.SE26\Repo\var\auth\web.env'
$env:SMARTREGRESSION_WEB_MODE = 'product'
& '.\.venv\Scripts\python.exe' -m uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

In a second terminal, resolve Node 22 and run npm with that runtime (the system's
npm.cmd can otherwise invoke its adjacent Node 24 binary):

```powershell
Set-Location 'D:\C1.SE26\Repo'
$taskNode = (& npm.cmd exec --yes --package=node@22.14.0 -- node -p process.execPath | Select-Object -Last 1)
$taskNpmCli = Join-Path (Split-Path (Get-Command npm.cmd).Source) 'node_modules\npm\bin\npm-cli.js'
$env:PATH = (Split-Path $taskNode) + ';' + $env:PATH
& $taskNode $taskNpmCli --prefix frontend run dev -- --port 5173 --strictPort
```

The local database does not contain the team's hosted accounts. Testing used
`ui-review@example.com`, a clearly labelled synthetic local QA account with an
in-memory verification mailbox. Its password is not recorded in tracked files.
No external email was sent and no Gemini call was made. The user's supplied
hosted account was not modified or verified against this new local database.

## Handoff and limits

The user requested discarding the previous checkout and continuing only in
`D:\C1.SE26\Repo`. The old repo was removed from that active path and put in the
Windows Recycle Bin, without a separate backup checkout. Old task 3.01 changes
were not carried over. `Repo-UIUX` was unregistered and its source files removed;
only an empty directory remains. Windows previously held it open, and the final
empty-directory removal attempt was rejected by automatic command review with
“blocked by policy”. No process belonging to the user was terminated.

This was an AI-assisted implementation and self-review, not an independent team
review. Local behavior and the checks above were exercised; no production
deployment, full backend/DB suite, hosted-account verification or remote Git
publication was performed. Frontend, backend and the owned local DB are left
running for the user to inspect. The next step is team review of this local
branch and any further visual preferences before publishing.
