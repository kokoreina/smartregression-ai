# Repository assistant API

Additive API, schema version `1.0.0`, implemented locally on 19 November 2026.
Source models: [repo_assistant.py](../../backend/src/smartregression/contracts/repo_assistant.py).
Research report v1/v2/v3 and existing analysis/selection contracts are unchanged.

## Owner APIs

Prefix `/api/v1/projects/{project_id}/assistant`. Every operation verifies the
session owner. POST/PUT/DELETE require product CSRF and Origin checks. Reads do
not spend AI quota. Archived projects can read existing history; new acquisition,
messages, watches and checks require an active project.

| Method/path | Meaning |
| --- | --- |
| POST `/overview?commit=<optional SHA>` | Materialize/cache a public snapshot and return static overview. Omitted SHA resolves the repository's default branch. Body `{}`; no provider call. |
| GET/POST `/threads` | List latest 30 or create/replay a thread at an immutable commit/config. Create body: commit, title, idempotency_key. |
| DELETE `/threads/{thread_id}` | Delete the owner's conversation/messages, HTTP 204. Provider attempts/audit remain. |
| GET/POST `/threads/{thread_id}/messages` | Read saved messages or ask a question. A new AI request is explicit and reserved before external work. |
| POST `/threads/{thread_id}/preview` | Retrieve static facts/snippets for this question without saving a message or calling the provider. |
| GET/PUT `/watch` | Read optional watch or save branch/paths/automatic/interval_seconds/version. Initial version 0; conflicts return 409. Saving validates the remote branch and selected paths. |
| POST `/check` | Persist a manual check and return 202. Background processing can start immediately; the standalone worker can recover the request. |
| GET `/notifications` | Latest 30 immutable two-snapshot change reports, plus mutable read_at. |
| POST `/notifications/{notification_id}/read` | Idempotently mark read, HTTP 204. |

## Messages, consent and identity

`MessageCreate` contains question (1–600 characters), action `chat|overview|changes`,
idempotency_key, use_llm, allow_model_fallback (default false),
allow_metadata_egress, allow_excerpt_egress and explicit
excerpt ranges. `use_llm=false` returns static lexical/structural evidence only.
For AI, metadata consent is required. Source excerpt egress needs separate consent;
ranges must belong to selected evidence paths and the thread's commit. At most
16 KB of source excerpts, 24 provider observations and 28 KB serialized context.

Each message saves the question, static reply/evidence and optional AI job ID.
Excerpts are reconstructed from the pinned snapshot when read and are not copied
into the chat row. The provider prompt is transient. At most three prior user
questions are included; assistant output never becomes source evidence. Known
secret patterns are rejected, without claiming detection of every possible secret.

An idempotency key binds the complete request. Replaying the same key returns the
saved message/current attempt; different content returns 409. Provider admission/start is atomic,
and a queued job starts at most once. API restart fails interrupted provider jobs
instead of silently regenerating. A missing/old parser config requires a new thread.
Limits: 100 threads/project, 100 messages/thread; owner APIs can delete a thread.

AI actions `overview|chat|changes` extend the existing `AiJob.action` enum. Updated
consumers must regenerate OpenAPI/TS. An older strict consumer may reject these
actions on a shared snapshot AI listing; do not promise reverse compatibility.

HTTP 503 maps to the additional `provider_unavailable` error enum. Assistant
orchestration retries only this confirmed response, with delays 2s/4s plus <=0.5s
jitter and at most three attempts. Every attempt has its own AiJob/reservation,
references retry_of/attempt/requested_model, and must fit the original campaign.
No SDK retry or borrowing another grant bypasses admission. Auth/config/quota
errors stop. Optional fallback uses verified 3.5 Flash-Lite only on attempt 3;
actual model stays visible. Other narrative routes retain their explicit attempt
policy. Old error rows are not rewritten. Consumers need the expanded error enum.

## Change meaning and queue semantics

One branch watch per project. `paths` are exact file/directory prefixes, not
inferred work ownership or task assignments. Empty paths means general changes,
not a personalized impact verdict. Branch names use the bounded ASCII policy in
`WatchInput`. Private repositories remain unsupported.

`ChangeReport` pins base/target/config, changed paths, watched scope, static impact
chains/evidence, coverage on both snapshots and truncation/limitations. Analysis
uses both graphs so a removed import can still affect a base consumer. Rename is
delete/add; direct two-tree comparison does not simulate a merge or inspect local
uncommitted/unpushed work. Unknown or absent edges are not a safety guarantee.

The worker claims a watch with a 10-minute lease and row lock/skip locked. Requests
are coalesced; a lease token and optimistic version prevent stale publication.
Report insertion/dedup and baseline advancement commit together. Errors keep the
old baseline and expose an error code. A crashed manual job is reclaimable even
when automatic polling is off. Checks are bounded; no input code/tests execute.

Polling defaults to 600 seconds, allowed 300–86400. GitHub rate limits defer
automatic work by at least one hour; a new webhook does not bypass this backoff.
An operator may configure backend-only `SMARTREGRESSION_GITHUB_TOKEN` for public
API reads. It is sent only to api.github.com, not codeload, logs or provider input.
Authenticated access does not enable private-repository acquisition.

## Signed webhook

POST `/api/v1/github/webhook`, JSON up to 64 KiB. No browser session/CSRF; instead
requires a backend `SMARTREGRESSION_GITHUB_WEBHOOK_SECRET` (at least 32 bytes),
HMAC-SHA256 over raw body, bounded fields and a UUID X-GitHub-Delivery. Invalid
signature returns 401; missing configuration returns 503. Receipt and scheduling
commit before response; the route does not wait for acquisition/AI.

Accepted events: push to heads, create/delete branch, closed+merged PR on the base
repo, ping. Tags and irrelevant PR actions are ignored. Only configured automatic
watches for the matching public repository/ref are scheduled. Same delivery/hash
replays; same delivery with different bytes conflicts. Stored projection excludes
raw payload and source. Current-head reconciliation prevents out-of-order events
or push+merge duplicates from rewinding progress. Short-lived events may be missed;
this is not a complete Git event history.

The endpoint must be reachable through authorized public HTTPS before installing
a GitHub App/repository webhook. Local polling works without installing a hook,
but needs a running backend/worker and available GitHub quota. No external hook or
public deployment is created by this implementation.

## Storage and verification

Forward migration `20261119_16`: threads, messages, watches, change notifications,
GitHub delivery receipts; extends the AI action check. No historical migration or
data rewrite. Existing cache retention protects referenced assistant snapshots.
Upgrade requires backup and runtime grants; restore is the rollback procedure.

See [implementation](../development/repo-assistant-implementation-20261119.md) and
[handoff](../development/repo-assistant-handoff-20261119.md) for actual checks,
provider model, operational state and limits. Compile/types do not establish AI
answer correctness or live webhook delivery.
