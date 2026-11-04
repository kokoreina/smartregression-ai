# Task 2.05 — PostgreSQL EvidenceStore

## Scope, decision and ownership

Implemented locally on `feat/sprint-2-2.05-evidence-store`, dependent on accepted
[P3](task-2.05-p3.md) in PR #36; main baseline `53356e6` was merged before editing.
User assigned prompts 4–7 plus commit/push/PR for each, and delegated technical
decisions. No merge/approval/deploy authorization is inferred.

Agent decision under Nguyễn Tấn Huy's authorization, 2026-11-04: implement the
minimal additive shared-schema/harness prerequisite for this slice because it did
not exist on main. KH remains shared migration/harness owner and requested human
reviewer; no claim KH approved. Revision `20261104_04` follows inventory `_03`.
One head, no rewritten released migrations, no dependencies or public schema changes.

## Behavior and files

- Application evidence port now includes bounded canonical codec and safe errors.
  Exact serialization follows P3, including one LF, escaped Unicode and array order.
  Oversized payloads fail before a connection; reload verifies codec/hash/model,
  canonical byte equality and full expected identity. Nested lists are detached.
- `adapters/storage/evidence_store.py`: standalone and bound implementations share
  immutable INSERT/compare logic; full base/target SHA/hash checked against run rows.
  Missing runs are not provisioned. Existing-key different bytes conflict; exact
  retry preserves created_at. Bound calls require a live caller-owned transaction.
- Existing transaction/connection failures are mapped to safe EvidenceStorageError,
  including ambiguous commit; no automatic replay/delete or raw DSN/SQL output.
- Shared metadata and additive migration implement scoped FK, codec/digest/size
  checks. Runtime grants exist only in the disposable harness; operators provision
  real-server grants explicitly as documented in [setup](postgresql-setup.md).
- Recovery harness now seeds a labelled DEMO domain fixture, includes bytea rows
  in exact DB backup/restore comparison and decodes/revalidates the restored bundle.
  pytest basetemp stays under this project's ignored var directory.

No source resolver or CLI workflow wiring is included here. Adapter fixtures are
not candidate analysis evidence, and static/schema validation is not source support.

## Verification

Cwd: `D:/smart-regression-ai/var/main-review-20261103`.
Python/Ruff: existing `D:/smart-regression-ai/var/task-2.20-b-venv/Scripts`;
PYTHONPATH points to this backend/src, PYTHONDONTWRITEBYTECODE=1, portable Git
from `var/task-2.13-tools/mingit/cmd` prepended for Git integration tests.

Test-first: new codec tests initially failed importing the absent codec.
Focused codec/schema/port tests: **13 passed**. Real PostgreSQL final harness:
**90 passed, 2 skipped** (separate real candidate → inventory DB harness needed).
Evidence: ignored `var/storage-verification-973a8a7f4ebd45ceafa2338a7e05fd2e/evidence.json`.
PostgreSQL 17.11, pinned image from scripts/storage/postgres-image.json; fresh head,
exact-row backup/restore, artifact digest/catalog, restored evidence decode/identity
and exact owned-container cleanup all passed.

Real tests cover same/different concurrent writes, read/write snapshot mismatch,
corruption, runtime UPDATE/DELETE/TRUNCATE/DDL denial, oversize SQL CHECK, rollback,
closed transaction, and unavailable connection on a task-reserved non-listening
loopback socket. Commit-ack loss is fault-injected after an actual commit, followed
by load/exact retry; it is not claimed as a real network partition experiment.

An initial DB test incorrectly assumed the harness failure database had no schema;
earlier tests had migrated it. Replaced with an owned reserved port to reproduce
actual connection refusal. Failed run is retained as evidence; no gates suppressed.
Subsequent DB runs passed. Ruff check/format, exporter --check and diff check passed.
Full backend command `python -m pytest backend/tests -q -p no:cacheprovider --tb=short
--basetemp D:/smart-regression-ai/var/p4-backend-final`: **582 passed, 91 skipped**,
one existing Starlette/httpx warning, 205.71s. Two final opt-in DB cases were added
after this run and ran in the final 90-pass PostgreSQL run above; full default
suite skip count predates those two cases. No runtime behavior changed after that
full run. Commands also run: `python scripts/storage/run_checks.py`,
`ruff check backend scripts`, `ruff format --check backend scripts`,
`python scripts/export_contracts.py --check`, `git diff --check`.

## Handoff and AI assistance

Prompt 5: source resolution and support validation. Prompt 6: compound report/bundle
writer and workflow integration. KH reviews shared schema/recovery changes. VI owns
the component already merged on main. Review/merge and whole Sprint acceptance remain
separate; P3 design acceptance does not attest runtime source verification.

OpenAI Codex assisted implementation/tests/docs and self-review using Backend and
Coordinator profiles, TDD/security skills and routed rules. Human understanding and
independent review are pending, no fabricated percentages/approval. No new service
left running; test containers were owned and removed; ignored evidence remains in var.
