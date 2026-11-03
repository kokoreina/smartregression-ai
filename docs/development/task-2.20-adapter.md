# Task 2.20 run report adapter completion

Date: 2026-11-03. Branch: `feat/khanh-task-2.20-migrations`; prior published schema
commit `b856fa7`. User explicitly conveyed Huy's handoff and assigned KH to finish
the adapter as well, then commit/push. This extends the earlier file-writer split
for this task; no message to Huy, independent approval or merge is inferred.

## Resulting implementation

- `adapters/storage/run_store.py` implements the existing save-only RunReportStore
  port. PostgresRunReportStore owns one transaction through H1's context;
  BoundRunReportStore uses an existing live transaction and never commits/retries.
- All snapshot/run/artifact/report metadata inserts are atomic. Existing repository
  binding is required; an untrusted report cannot provision a repository.
- PostgreSQL INSERT ON CONFLICT DO NOTHING RETURNING followed by exact scoped-row
  comparison provides immutable identical-retry no-op and different-value conflict.
  No UPDATE/DELETE, select-then-insert race or rowcount assumption is used. Timestamp
  defaults are excluded from retry equality. PK/FK/global storage-key conflicts do
  not produce partial successful writes.
- `application/run_store.validate_run_report_write` detaches/revalidates identity,
  exact canonical config/summary bytes, versions, known snapshots, native ID/metadata
  boundaries, legal statuses, aggregate completeness and finite nullable measurements
  before SQL. It does not claim source authorization/hash verification from metadata.
- `application/persistence.persist_report` validates before publication, publishes
  complete bytes first, then calls the SQL store. It returns the prepared immutable
  write only after save returns. Caller retains responsibility for repository access,
  trusted acquisition manifests and approved artifact root/configuration.
- `adapters/storage/report_publication.ReportFiles` provides exclusive same-volume
  atomic hard-link publication with file fsync, exact retry and conflict detection.
  Source/artifact roots must be disjoint; portable paths, ancestor links/junctions,
  root containment, exact size/hash and expected run/report identity are checked.
  Reads validate actual v2 bytes, not a report reconstructed from stage summary.

File publication fails -> no DB call. DB failure after publish -> rollback/no success,
complete orphan file retained for reconciliation. A simulated lost acknowledgement
after a real commit preserves that file; exact retry is safe. There is no automatic
file deletion after an ambiguous DB failure and no distributed transaction/GC.

ReportFiles imposes a local file-adapter cap of 16 MiB; metadata storage keys remain
bounded to 2048 UTF-8 bytes. Unsupported values are rejected, never truncated; these
are documented adapter limits, not changes to canonical public report models.
The controlled local filesystem assumption excludes a concurrent privileged host
attacker replacing files during checks. File fsync/atomic publication do not promise
power-loss durability across every filesystem/server platform.

## Verification and recovery

Focused preparation/file/connection tests passed locally during implementation.
New regressions were observed failing before their implementations/fixes, including
unknown module/helper and existing-file mismatch classification. Ruff and exporter
check pass without public schema/type changes or new dependencies.

The dedicated PostgreSQL suite now has 40 cases: the original 25 foundation cases
plus actual adapter round-trip/retry, immutable mismatches, nonexistent authorized
repository, late multi-table failure rollback, identical/different concurrent saves,
outer-transaction ownership, invalid metadata, file/DB publication, simulated lost
ack after real commit and real authentication failure with a safe error code.
Run the existing `scripts/storage/verify.ps1` for default checks plus real DB tests.
Recovery fixture now uses BoundRunReportStore, not the old direct metadata SQL,
so backup/restore exercises data actually written by this adapter.

Final operator evidence inspected:

- Default backend suite: **400 passed, 41 skipped**, one existing Starlette/httpx
  warning, 47.52s. Forty opt-in DB cases ran separately; one POSIX FIFO case is
  skipped on Windows. Default skips are not used as DB acceptance.
- Actual PostgreSQL **17.11**: **40 passed**, 3.08s, using the pinned official
  Linux/amd64 image. Fresh migrations, adapter recovery backup/restore rows/file
  digest/catalog and exact owned-container removal all passed.
- Evidence: `var/storage-verification-3aa4dc4ad7624fd4a717172f86d5e692/evidence.json`;
  JUnit records each actual DB test. Runtime evidence/dumps/secrets are not committed.
- Ruff lint/format, contract exporter check and diff checks passed. No migrations,
  public reports/generated types, dependencies, frontend or existing CLI changed.

Earlier task-2.20-c.md evidence remains historical schema/25-case evidence. The
accepted bounded 2.20 foundation implementation and local PostgreSQL verification
are complete; team review/CI and human acceptance remain separate gates. No
whole-sprint completion is inferred.

## Consumer usage

```python
from smartregression.adapters.storage.run_store import PostgresRunReportStore
from smartregression.adapters.storage.report_publication import ReportFiles
from smartregression.application.persistence import persist_report

# engine is owned by H1's database_engine context; repository is already authorized
# and provisioned. Report/config/trusted manifests come from the analysis caller.
write = persist_report(
    ReportFiles(artifact_root, source_repository=source_root),
    PostgresRunReportStore(engine),
    report=report,
    configuration=actual_configuration,
    snapshot_manifests=trusted_manifests,
    artifact_id=artifact_id,
    storage_key=storage_key,
)
```

No API/CLI default auto-connect, migration-on-startup or implicit DB settings were
added. Workflow composition can opt into this use case after receiving actual
config/manifests. Normal read-only analyze/health stays independent of DB config.

## Scope remaining outside 2.20

P3 EvidenceBundle policy/adapter (2.05), P5 retrieval decisions/index domain tables,
inventory/test-case domain migration/adapter (2.08/2.09), full history/report catalog
reader and live multi-user authorization remain their own work. This foundation
does not turn the fixture-only inventory collector into an arbitrary candidate
runner. Inventory PR may be reviewed/merged incrementally but not marked fully Done.

User assigned the formerly H1 adapter slice to KH; all changes are on the same
2.20 branch for review. Codex assisted implementation/tests/docs/self-review; student
review/understanding remains required by Proposal Appendix C/D. No assistance
percentage, reviewer receipt, mentor approval or fabricated benchmark is claimed.
