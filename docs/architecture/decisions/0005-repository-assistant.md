# ADR 0005: repository assistant and remote-change monitoring

- Status: accepted for local implementation by the user on 19/11/2026.
- Source: user approved the proposal and asked “hãy lên plan chi tiết và thực thi”.
  Later requests selected Gemini 3.8 Flash and asked to diagnose/fix HTTP 503.
- Budget selection was delegated by the user; this is not team/mentor acceptance
  or authorization for unlimited usage, public deployment or Git publication.
- Baseline: main `effd115`, local branch `feat/repository-assistant-watch-20261119`.

## Context and options

The product already has public GitHub acquisition, immutable snapshots, Python
analysis, a limited JS Explorer, lexical search, PostgreSQL and consented Gemini
requests. Stateless reading guides cannot represent a multi-turn conversation or
durable watch progress. A generic code-executing agent would exceed the approved
scope and existing execution boundary.

Choose a snapshot-bound, owner-scoped assistant using existing adapters, with a
PostgreSQL coalesced watch queue. No new provider, vector DB, broker, framework,
automatic input-code execution or cross-repository analysis is introduced.

## Decision

1. Static overview/retrieval first, optional grounded AI. Evidence retains SHA,
   path/range and parser configuration. Unknown/partial stays visible. “My work”
   means explicitly selected paths, not inferred task ownership from login email.
2. Conversations pin a snapshot/config. Save questions, static facts and AI attempt
   references; reconstruct source snippets from cache. Metadata and source egress
   have separate consent, with bounded preview/ranges.
3. One watch per project, manual checks and a standalone polling worker. Use both
   base/target graphs for deletion/removed relationships; changes are potential
   static impact, not executed-test outcomes. Rename is delete/add.
4. Durable leases, optimistic watch versions, dedup and atomic report/baseline
   writes. Reconcile current ref head instead of trusting webhook order. It is
   not a complete Git event history. Rate limits defer automatic work >=1 hour.
5. Signed webhook receiver with bounded projection and delivery dedup. No hook/App
   is installed without actual repository permissions and reachable public HTTPS.
   Public URL access alone does not grant installation or private-repo access.
6. Web default model `gemini-3.8-flash`, LOW thinking. Research CLI remains on its
   historical 3.5 Flash-Lite policy. Optional per-message fallback uses the verified
   `gemini-3.5-flash-lite`; default is off. Report actual requested/returned models
   and retry lineage; never relabel fallback output as 3.8 or mix research cohorts.
7. Confirmed Google 503/high-demand errors get `provider_unavailable`. Assistant
   retries after 2s and 4s plus bounded jitter, at most 3 admitted attempts. Each
   attempt reserves a new AI job against the **same campaign**, before network use.
   Do not retry auth/config/quota errors, or borrow another grant when exhausted.
   The final attempt may use fallback only after explicit consent. API restart
   interrupts generation rather than silently resuming a paid/uncertain call.
8. SDK automatic retries remain disabled to prevent retries outside application
   quota/ledger accounting. Narrator still performs one generation per admitted
   attempt. Static results remain usable on provider failure.

## Consequences and compatibility

The new owner APIs, MessageCreate fallback flag, AI action values and
`provider_unavailable` error value require refreshed OpenAPI/TypeScript consumers.
Older strict readers may reject new enum values. Existing report shapes/versions
and old saved attempt rows are retained. Optional false fallback is omitted from
the message idempotency digest to preserve pre-flag request replay.

Initial acceptance: <=3 attempts / USD .06 reserved. After a separate explicit
503-repair request, a new recovery campaign permits <=3 / USD .06; the old records
remain intact. Total local allowance <=6 / USD .12 reserved, not observed billing.
No more live generations are made after those campaigns are consumed. Google API
tier/billing is separate from a Gemini app subscription; no billing is enabled.

## Migration and recovery

Forward migration `20261119_16` adds five tables and extends the AI action check.
It is frozen after local application; no historical migrations/data are rewritten.
Backup precedes upgrade; runtime gets only required table access. Cache retention
protects referenced assistant snapshots. Restore an actual backup for rollback;
dropping/recreating tables does not restore conversation/history.

See [API](../../contracts/repository-assistant.md),
[implementation plan](../../development/repo-assistant-implementation-20261119.md),
[operations](../../development/repo-assistant-local-operations.md) and
[handoff](../../development/repo-assistant-handoff-20261119.md).

Revisit after group review, live monitoring setup and language-specific evaluation.
Gemini 3.8's verified price bound needs review before 01/01/2027. Local tests and
a successful fallback answer do not prove Google 3.8 capacity has recovered.

Codex assisted design/code/tests/documentation. The group must understand/review
the work under Proposal Appendix C/D; no independent or mentor approval is implied.
