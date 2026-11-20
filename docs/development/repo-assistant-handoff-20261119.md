# Repository assistant and Gemini 503 handoff

Implemented locally in `D:\C1.SE26\Repo`, branch
`feat/repository-assistant-gemini-recovery-20261119`, baseline main `effd115`. The user
approved [the proposal](repo-assistant-change-notifications-proposal-20261119.md),
requested detailed execution, selected Gemini 3.8 Flash and requested a 503 fix.
Existing work/data were retained. Publication through a feature branch and pull
request is authorized; merge remains for the team. No public deployment.

## Delivered behavior

- New project onboarding opens **Trợ lý & thay đổi**. Static overview, reading
  order, source preview, snapshot-pinned conversations and cited questions.
- Personal path scope, watched branch, durable manual/polling checks, immutable
  base/target change notifications, read state and dependency chains. Both graphs
  retain deleted relationships. Signed webhook/dedup is implemented; installation
  and public HTTPS are separate operational steps.
- Forward migration `20261119_16`, five tables; local owned DB backed up/upgraded.
  Docker changed its dynamic loopback port on restart; only private DB URL ports
  were synchronized, with prior env preserved and passwords/data retained.
- Light/Dark/mobile UI uses the existing neutral/teal system. Initial screenshots
  exposed a global header background leak; scoped styling fixed it. HTTP 204
  responses are now accepted by the shared product client. Acquisition requests
  have bounded time for snapshot preparation.
- Backend-only ignored `backend/.env` is configured. No secret is included in
  source, generated frontend types, provider prompts or shared logs.

## Confirmed 503 cause and fix

Google accepted model lookup for `gemini-3.8-flash`, reporting generateContent
support. Actual generation returned ServerError HTTP 503 with:

> This model is currently experiencing high demand. Spikes in demand are usually
> temporary. Please try again later.

This establishes temporary model demand for the observed failures. It does not
prove every possible 503 has the same cause. Requests were bounded <=8192 input
tokens, with no Search/Maps grounding. No evidence implicated key syntax or prompt
size in this case. API subscription/tier billing remains independently determined.

The application now classifies 503 as `provider_unavailable`, retries after
2s/4s plus <=0.5s jitter, and admits every new attempt under the same atomic quota
and ledger. At most 3 attempts; auth/config/quota errors are not retried. Explicit
fallback permits 3.5 Flash-Lite on the last attempt. SDK-level hidden retries stay
off. UI explains overload, displays attempt/model and can draft a retry without
making another API call. Old failed attempts remain readable and unchanged.

Live recovery passed: 3.8 returned 503 twice; explicitly allowed 3.5 Flash-Lite
then returned a validated, cited Vietnamese overview. Evidence:
`var/assistant-recovery-20261119/result-attempt-1.json`. This confirms the recovery
path, not recovered capacity of 3.8. The default model is still 3.8; fallback is
off unless selected. Historic research CLI/model policy stays separate.

Initial campaign: 3 failed reservations, retained under
`var/assistant-acceptance-20261119/`. Recovery campaign: 3 admitted calls, final
fallback completed. Combined ceiling: 6 attempts / USD .12 reserved; actual billing
is unknown, not assumed zero. Both campaigns are consumed; no automatic top-up.

## Verification

Final checks on the implemented source:

- Full backend: **1,144 passed, 181 skipped**, 191.42s;
  `python -m pytest backend/tests -q --basetemp var/assistant-final-1119b --junitxml var/assistant-backend-final.xml`.
  Skips are opt-in PostgreSQL plus Windows-unavailable POSIX FIFO, not passes.
- Full real PostgreSQL: **176 passed, 4 skipped**, 72.66s; dedicated candidate
  runs remain separate. Backup/restore passed in
  `var/storage-verification-474d57389b534ec3b32d4420654cd8e0/evidence.json`.
- Frontend Node 22: build, lint and contracts:check pass (88 validation, 11 report
  SSR, 60 repository SSR, 20 auth/transport). Existing ~795 kB bundle warning remains.
- Browser suite: **60 passed**, 38.7s, including all 12 assistant cases and
  shared account, project, report, theme and accessibility regressions.
- Ruff check and format check pass across backend/scripts/migrations: 305 files.
  Backend contract exporter --check and git diff --check pass.
- Replaying the successful live recovery request returned the same result with
  campaign counts still 3/3 and 3/3; no additional generation occurred.
- Actual owned development DB backup and isolated restore passed:
  `var/backups/backup-20261119T114619Z-9d20b42522ed4e55850cc891c92c03de.json`.
- Configured-key scan of nonignored Git files and built frontend assets found
  zero matches; backend/.env is ignored. This is a bounded configured-value check,
  not proof that every possible secret pattern has been found.
- Fresh-clone guide, credential example and local links were checked offline
  against the actual configuration loader; this did not spend API quota or issue
  another grant on the existing development DB.

Earlier targeted checks retained as evidence:

- Provider/adapter/runtime: 75 passed, including 503 classification and a single
  generation per narrator attempt.
- Real PostgreSQL assistant slice: 9 passed, including retry recovery, optional
  fallback, no retry on auth error and refusal to spend another campaign's grant.
  `var/storage-verification-9a9dc891c92a479694f56f7e9e0b43ea/evidence.json`.
- Browser assistant slice: 12 passed in the final full run, including overload/
  fallback UI, source consent, read/unread, quota failure, isolated history,
  watch interval/version, notification questions and five widths in Light/Dark. Screenshots in
  `var/uiux-playwright/assistant-{light,dark}-{1440,375}.png`.
- Previous full PostgreSQL campaign: 172 passed, 4 candidate-only skips;
  `var/storage-verification-8ab1dda40b2842a48f47a161776576d1/evidence.json`.

## Operational limits and next steps

Backend/worker need to remain running for monitoring. Local loopback cannot receive
GitHub events without an authorized reachable HTTPS endpoint. No App/hook has been
installed. Anonymous GitHub acquisition was rate-limited during the live read probe;
the application exposes that error and preserves baseline. Optional backend-only
`SMARTREGRESSION_GITHUB_TOKEN` supports public reads, and polling backs off >=1h.
No private-repo capability is implied.

Latest read-only GitHub quota probe confirmed anonymous core remaining **0 / 60**;
this is separate from the Gemini API issue. No token was extracted from another
tool/account or written to the project. Backend8000, frontend5173 and one standalone
watcher are running from this checkout after reload. Runtime OpenAPI includes the
fallback flag; frontend returned HTTP200. See the [UI self-check](repo-assistant-ui-self-check.md)
for design gate evidence.

Monitoring does not observe local/unpushed work or guarantee complete event history,
runtime dispatch, cross-language relationships or confirmed regressions. A missing
edge is not a safety verdict. Lexical question retrieval is bounded and is not a
full semantic translation/search engine.

Independent review, deployed webhook acceptance and broader real-provider question
quality evaluation remain separate from this local self-check. Detailed setup:
[local operations](repo-assistant-local-operations.md), [API](../contracts/repository-assistant.md),
[ADR 0005](../architecture/decisions/0005-repository-assistant.md).
Fresh-clone instructions and the backend-only API key location are in
[team local setup](team-local-setup.md).

Codex assisted implementation, debugging, tests and documentation. The team must
review/understand the work per Proposal Appendix C/D; no contribution percentage
or mentor/independent approval is invented.
