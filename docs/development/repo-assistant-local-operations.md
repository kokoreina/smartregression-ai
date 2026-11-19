# Repository assistant local operations

For a fresh clone on another teammate's machine, start with
[team setup and API key instructions](team-local-setup.md). The commands below
describe the existing developer installation; its private DB/config are not in Git.

Current workspace: `D:\C1.SE26\Repo`. Use Node 22 LTS, the existing Python venv
and owned PostgreSQL configuration in ignored `var/auth/web.env`. Start Docker
Desktop first; do not run an older checkout or expose this installation publicly.

## Start

Backend terminal:

```powershell
Set-Location -LiteralPath 'D:\C1.SE26\Repo'
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = 'D:\C1.SE26\Repo\var\auth\web.env'
$env:SMARTREGRESSION_WEB_MODE = 'product'
.\.venv\Scripts\python.exe -m uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

Frontend terminal, with Node 22 on PATH:

```powershell
Set-Location -LiteralPath 'D:\C1.SE26\Repo'
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Worker terminal:

```powershell
Set-Location -LiteralPath 'D:\C1.SE26\Repo'
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = 'D:\C1.SE26\Repo\var\auth\web.env'
.\.venv\Scripts\python.exe scripts/assistant/worker.py
```

Open `http://127.0.0.1:5173`, sign in, then Projects → open project →
**Trợ lý & thay đổi**. Creating a new project opens this tab. Accounts on a
deployed installation are not automatically copied into the local DB. This task
does not change an account password or verification state.

For automatic monitoring, leave the worker running and enable the watch. Manual
checks persist before processing and are recoverable. Stop each service with
Ctrl+C; do not remove the database/volume to restart.

## Gemini

Web AI uses `gemini-3.8-flash`, thinking LOW; research CLI retains its frozen
3.5 Flash-Lite policy. Credentials belong in ignored `backend/.env`:

```dotenv
GEMINI_API_KEY=<backend credential>
```

`SMARTREGRESSION_GEMINI_ENV_FILE` in `var/auth/web.env` points to that file. No
dotenv discovery, VITE key or frontend secret is used. Do not commit it. API jobs
also need an operator-issued grant; a key does not grant unlimited app quota.

Free-tier availability depends on the Google API project/model. A Gemini app
subscription does not establish that tier. Google pricing lists free standard
input/output for 3.8 Flash as checked 19/11/2026. USD reservations bound unknown
cost and are not invoices; no Cloud billing settings are changed.

The initial acceptance and separate 503-recovery campaign each permit at most
3 attempts / USD 0.06 reserved. Do not reset old records. Both are consumed; current
status is in the handoff. Confirmed 503 responses have bounded 2s/4s backoff with
jitter, and every retry reserves its own quota under the same campaign. Fallback
is off unless explicitly enabled in the question form; it uses 3.5 Flash-Lite on
the last attempt. No retries run outside budget or silently resume after restart.

## GitHub and webhook

Without a token, reads share GitHub's anonymous IP quota. An operator can configure
backend-only `SMARTREGRESSION_GITHUB_TOKEN` for public API reads. It is not sent to
codeload or AI. This does not enable private repos or install a hook. Rate limits
preserve baseline and defer automatic retry by at least an hour.

`/api/v1/github/webhook` additionally requires backend
`SMARTREGRESSION_GITHUB_WEBHOOK_SECRET` (32+ bytes) and public HTTPS reachable by
GitHub. Installing a GitHub App/repository hook needs repository permission.
No hook is installed by this task; local polling is the operating mode. Do not
expose the test e2e server or disable signature verification.

## Database and checks

Migration head `20261119_16`. For this owned local installation:

```powershell
.\.venv\Scripts\python.exe scripts/auth/migrate_local.py
```

It verifies container ownership, backs up, upgrades and grants runtime access.
Migration never runs on app startup. If Docker changes a dynamic host port,
verify the labelled container/loopback binding and synchronize only the DB URL
ports, retaining credentials/data. Verification uses disposable owned containers
via `scripts/storage/run_checks.py`, separately from the application DB/volume.

See [contract](../contracts/repository-assistant.md),
[implementation](repo-assistant-implementation-20261119.md) and
[handoff](repo-assistant-handoff-20261119.md) for actual evidence and limits.
