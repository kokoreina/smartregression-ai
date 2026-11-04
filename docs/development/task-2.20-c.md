# Task 2.20 C schema migrations and PostgreSQL checks

Follow-up: user handed the adapter slice from H1 to KH on 2026-11-03. The adapter
and publication use case are now implemented on this same branch; current
verification is in [adapter handoff](task-2.20-adapter.md). Historical schema
verification and the original writer split below are retained for traceability.

Date: 2026-11-03. Owner: Trần Hùng Khánh. Branch:
`feat/khanh-task-2.20-migrations`, based on main `62d5045` (merged H1 2.20-B).
Checkout: `D:\C1.SE26\Repo-Sprint2-Khanh-2.20`. The separate inventory checkout
and all its changes are preserved. After verification, the user authorized commit
and push on 2026-11-03 for team PR review. Merge/approval remain with the team.

## Scope and accepted inputs

P1/P2/P4 in [checkpoint](task-2.20-checkpoint.md) and
[D14](decision-register.md) are accepted: SQLAlchemy Core/psycopg/Alembic,
five-table foundation and KH/H1 file ownership. [H1 handoff](task-2.20-b.md)
provides configuration, engine/transaction contexts and RunReportWrite metadata.

KH owns Table metadata, one Alembic head, M001/M002 and dedicated PostgreSQL
test setup/integration/recovery evidence. H1 continues to own manifests/lock,
config/connection and the future run/report adapter. P3 evidence bundles, P5
retrieval, inventory domain migrations and workflow persistence remain outside
this foundation. Do not implement H1's adapter or silently add domain tables.

## Implementation and consumer interface

`smartregression.adapters.storage.schema` exports:

- `SCHEMA = "smartregression"` and `metadata`.
- `repositories`, `snapshots`, `analysis_runs`, `artifacts`, `run_reports` as
  SQLAlchemy Core Table objects. H1 should import these rather than redefine tables.
- Text IDs, full lowercase SHA-1/SHA-256, SHA-256 digests, scoped RESTRICT FKs,
  nullable unknown snapshot identities, timezone-aware timestamps, v2 stage summary
  JSONB and nullable finite/nonnegative measurements match checkpoint §5.
- `analysis_runs` PK is `(repository_id, run_id)`. `run_reports` PK adds `report_id`.
  Artifact references include repo/run, preventing cross-run catalog references.
- Metadata IDs are bounded to 512 UTF-8 bytes; storage keys to 2048 UTF-8 bytes
  for the unique B-tree key. The latter is an explicit implementation storage limit,
  not a change to ReportArtifact/public contract; H1 must translate rejected storage
  values and must never truncate them. Actual path authorization remains application-side.
- Config/summary byte limits remain H1's canonical-byte checks; PostgreSQL JSONB text
  formatting is not used to impose a different byte count on the same JSON value.
- JSON shape/basic checks are not complete report validation, hash/source verification
  or immutable-write conflict logic. The upcoming H1 adapter must keep those checks.

## Migration lifecycle

`alembic.ini` has no URL or credentials. `migrations/env.py` uses the explicit H1
migration credential loader/engine context, or an explicitly supplied trusted
connection for tests. No migration runs at import, web startup or health/analyze.

Revisions generated through Alembic are `20261103_01` (repositories/snapshots/runs)
then `20261103_02` (artifact/report catalog). Revision DDL is frozen in the files,
not imported from evolving metadata; no `create_all` replaces upgrade history.
DDL/version changes are transactional on PostgreSQL. Reapplying head is a no-op.

Downgrades intentionally raise `forward_only_migration_restore_backup`. This task
does not supply destructive down migrations. Recover data from verified backups
into an isolated target; do not stamp/drop/reset to disguise a failed migration.
`alembic_version` lives in the fixed schema; the migration role owns it, runtime
does not receive its INSERT/SELECT rights as part of application table grants.

## Dedicated real database verification

Run from an ordinary PowerShell with Linux Docker and the locked task environment:

```powershell
& 'D:\C1.SE26\Repo-Sprint2-Khanh-2.20\scripts\storage\verify.ps1'
```

The wrapper runs default backend tests, Ruff and exporter checks, then the scoped
operator harness. Default pytest skips the real DB cases when no harness context
exists; those skips do not count as PostgreSQL acceptance.

`scripts/storage/run_checks.py` accepts no external DSN. It creates a fresh labelled
container using the official PostgreSQL 17 Linux/amd64 image pinned in
`postgres-image.json`, publishes only a random loopback port, generates three
memory-only passwords and provisions dedicated fixture DBs/roles. It never uses
existing/shared database names on an external server. Test fixtures verify the
container label/port/database/version before connecting. Runtime is SELECT/INSERT
only, with no DDL/UPDATE/DELETE or public-schema CREATE. Owner credentials are separate.

The harness removes only the exact created container after verifying its nonce
label, including its anonymous fixture volume. It does not prune Docker resources.
Artifacts are a new ignored `var/storage-verification-<uuid>/`: redacted evidence,
JUnit XML and a synthetic foundation dump. No passwords/URLs are written there.

Integration checks cover scoped keys/FKs, JSON shape/finite metrics, null failure
snapshots, multi-row rollback through H1 transaction contexts, runtime permission
negatives, two-connection uniqueness, M001 populated upgrade/reapply and injected
M002 DDL failure with unchanged revision/no half-applied table then retry. A separate
fresh database upgrades straight to head. Backup is restored into another isolated
database and compared to original rows, not called a down migration.
The final recovery drill copies a quiescent synthetic report artifact to a new root
and checks digest/size/bytes against the restored catalog. Fixture publication uses
H1's metadata preparation and explicit test SQL, not a production RunReportStore.
Dump ownership/ACL restoration is excluded; see [setup](postgresql-setup.md).

## Verification status

- Locked `uv sync` installed the 32 packages from H1's unchanged uv.lock into this
  checkout's `.venv` using Python 3.14.5; no manifest or lock edits.
- Test-first unit suite failed because schema.py was absent, then focused schema
  plus existing H1 config/connection/metadata tests passed: **72 passed**.
- Alembic offline `upgrade head --sql` succeeded; one-head/two-revision unit check
  passed. Ruff lint and format passed during implementation.
- Operator default suite: **385 passed, 26 skipped**, one existing warning, 53.88s.
  Skips are the 25 opt-in PostgreSQL tests and existing Windows POSIX FIFO case;
  the real DB tests run separately below, not counted as accepted from those skips.
- First PostgreSQL 17.11 run: **24 passed, 1 failed**. The concurrency test used
  driver rowcount, which returned -1 for both statements. It now checks RETURNING
  and exactly one persisted row, preserving the uniqueness invariant. Earlier
  evidence remains in `var/storage-verification-1dd7561e362e410cbebb4e97e9c86f7d/`;
  owned-container cleanup succeeded.
- Final DB-only run: **25 passed**, 1.08s. Actual evidence inspected at
  `var/storage-verification-da7c798d876b40d4b01fa050d57b3b4c/evidence.json`.
  Fresh head, populated upgrade/reapply, migration failure/retry, real constraints,
  rollback/concurrency/permissions, exact backup/restore rows, restored artifact
  digest/catalog and owned-container removal passed. PostgreSQL 17.11 used pinned
  image `sha256:0b81cec82228160abfa753aeaad0609b709eb26eeb950f2e404ad2326e1cc370`.
- Ruff lint/format and contract exporter --check passed after the final code edits.
  No new GitHub CI, POSIX run or human acceptance is claimed.

## Next handoff and limits

H1 can consume the Table objects after review, implement its scoped transactional
RunReportStore adapter and run domain conflict/retry/file-publication tests using
these fixtures. Foundation DB checks do not prove that adapter or full report
filesystem publication has been implemented. Inventory/test-case migrations require
their separate mapping/checkpoint; P3/P5 remain pending. Human review/acceptance and
CI remain separate from the local checks. Reviewer AN is proposed, not assumed.

OpenAI Codex assisted implementation, tests, documentation and self-review. Khánh
must understand/review/verify before submission under Proposal v1.4 Appendix C/D.
No assistance percentage, human approval or mentor acceptance is claimed.
