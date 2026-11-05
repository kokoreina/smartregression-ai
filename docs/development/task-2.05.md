# H1 2.05 — Immutable PostgreSQL EvidenceStore

Baseline: main `b3b251a`, 2026-11-05. Branch `feat/h1-2.05-evidence-store`.
User authorized implementation, verification and publication of seven sequential
slices. This slice is independent of prompt 1 PR #47 and targets main directly.

Reconciled the existing `e03312a` implementation instead of rebuilding storage:
bounded canonical codec, `PostgresEvidenceStore`/transaction-bound adapter, domain
metadata, migration, recovery fixture and integration tests. Current main's sole
migration head is `20261104_03`; the existing evidence revision `20261104_04`
extends that exact head without a competing branch. This is reuse of the previous
implementation, not a new migration numbering decision. KH remains migration-chain
owner; team review of migration/grants/recovery is required before merge.

## Behavior and compatibility

P3: one immutable bundle per repository/run; canonical JSON in bytea, at most
2,097,152 bytes. Save preflights typed data, canonical bytes and size. Load checks
format/size/digest/canonical representation and full immutable run identity.
Matching retries are no-ops; different payloads conflict. Concurrent inserts use
database uniqueness. Infrastructure failures are sanitized; there is no automatic
transaction retry. Bound adapters never commit/rollback their caller's transaction.

No public schema/generated types/dependencies changed. The additive table references
existing runs; callers must supply authorization and source verification separately.
The runtime test role has SELECT/INSERT only. Downgrade is forward-only: restore a
consistent backup rather than claim dropped evidence could be recovered by DDL.
No production/external database is used by the verification harness.

## Actual verification

Python/Ruff: `D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/` (existing locked
environment, not a new clean install). Cwd: current execution worktree.
`PYTHONPATH=backend/src`, `PYTHONDONTWRITEBYTECODE=1`; portable Git prepended when
needed. DB/unit tests ran elevated to avoid known Windows sandbox temp/pipe limits.

- Red: codec test collection failed because baseline lacks `EVIDENCE_FORMAT`.
- Focused codec/schema/storage tests: **13 passed**, exit 0.
- All backend unit tests: **595 passed**, exit 0, 17.98s.
- PostgreSQL harness after adding explicit concurrent lock-timeout coverage:
  **91 passed, 2 skipped**, exit 0. Skips are separate candidate-to-DB cases;
  they are not reported as candidate verification.
- Harness evidence: `var/storage-verification-9472c132919945f4918cbf917e415c95/evidence.json`.
  Fresh/upgrade paths, exact backup/restore rows, restored artifact digest/catalog,
  evidence codec/identity restore, and owned-container cleanup passed.
- Ruff lint/format, exporter check and diff check: exit 0.

```powershell
python -m pytest backend/tests/unit/test_evidence_codec.py backend/tests/unit/test_storage_schema.py backend/tests/unit/test_stage_storage.py -q -p no:cacheprovider --tb=short
python -m pytest backend/tests/unit -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p2-unit
python scripts/storage/run_checks.py
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
```

DB tests cover real round-trip/retry/concurrent conflict, locked-insert timeout,
identity/corruption/codec errors, transactional rollback, connection failure and
runtime privilege boundaries. No browser/CI or full workflow acceptance is claimed.
Source verification and compound workflow belong to prompts 3/4.

OpenAI Codex assisted reconciliation, tests/docs and self-review. Independent review
and human acceptance are pending; neither historical code nor green tests supplies
an approval on behalf of KH/AN/the team.
