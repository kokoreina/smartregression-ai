# KH to H1 schema handoff for task 2.20

Update 2026-11-03: after this schema handoff, user assigned KH the run/report
adapter as well. See [adapter completion](task-2.20-adapter.md) for current code
and verification; the original handoff below preserves its earlier scope.

Owner: Trần Hùng Khánh. Consumer: Nguyễn Tấn Huy. Date: 2026-11-03.
Base main: `62d5045b00a52a76a7b37e023bf4d9bb6600c654` (H1 2.20-B).
Branch: `feat/khanh-task-2.20-migrations`. User authorized publishing the branch
on 2026-11-03 for team PR review. Huy receipt/review and adapter implementation
are not inferred from publishing this handoff.

## Stable imports

```python
from smartregression.adapters.storage.schema import (
    SCHEMA,
    metadata,
    repositories,
    snapshots,
    analysis_runs,
    artifacts,
    run_reports,
)
```

These are SQLAlchemy Core Table objects in fixed schema `smartregression`.
They do not connect, create tables or run migrations when imported. H1's future
`adapters/storage/run_store.py` should import them; do not define duplicate Tables
or write migration versions in the adapter task. KH remains migration writer.

## Column mapping from H1 RunReportWrite

| Table | Columns H1 uses | Constraints / input |
| --- | --- | --- |
| repositories | repository_id, source_kind | RepositoryId PK; trusted local/github binding provisioned upstream, not inferred from uploaded report |
| snapshots | repository_id, commit_sha, snapshot_id, manifest_version, materializer_version | Composite PK; map directly from write.snapshots; validate acquisition before SQL |
| analysis_runs | repository_id, run_id, base_sha, target_sha, base_snapshot_id, target_snapshot_id, comparison_mode, data_kind, configuration, configuration_sha256 | Composite repo/run PK; hashes nullable for failure; scoped snapshot FKs; configuration=json.loads(write.configuration_json) |
| artifacts | repository_id, artifact_id, run_id, storage_key, kind, sha256, size_bytes, media_type, schema_version, access_class | PK repo/artifact; UQ repo/run/artifact; report_json requires non-null run, 2.0.0, application/json and repository access |
| run_reports | repository_id, run_id, report_id, artifact_id, schema_version, analysis_status, stage_summary, analysis_duration_seconds, llm_cost_usd | PK repo/run/report; FK includes repo/run/artifact; stage_summary=json.loads(write.stage_summary_json); unknown metrics stay None |

Every table has server-generated timezone-aware created_at. Do not include fresh
timestamps in equality checks for an otherwise identical retry. No other column
has a fabricated default; application-supplied values remain explicit.

Safe preparation remains H1's `prepare_run_report`: verify published bytes/digest,
revalidate v2/identity/config/summary and pass trusted manifest versions. SQL regex
checks do not verify content hash or actual authorization. Metadata IDs are limited
to 512 UTF-8 bytes, storage_key to 2048 UTF-8 bytes; reject unsupported input without
truncation. Native test IDs are not subject to this metadata-ID cap.

## Transaction and immutable write behavior

Use H1's `database_transaction`/bound connection. The adapter must not independently
commit/rollback/retry. Register/compare trusted snapshot rows, immutable run binding,
artifact descriptor and report summary in the same transaction; repository binding
must already exist and be authorized. FK order is repositories -> snapshots -> runs
-> artifacts -> reports. Failure runs can have null snapshot hashes without fake rows.

DB PK/FKs arbitrate identities; H1 still implements exact-retry/no-op versus
immutable mismatch conflict and preserves ambiguity on lost commit acknowledgement.
Do not UPDATE existing runs/artifacts/reports to satisfy conflicts. PostgreSQL
INSERT ON CONFLICT plus RETURNING/read/compare can preserve the transaction for
conflict checks; driver rowcount may be -1 and is not proof of an insert outcome.
Catch/translate domain conflicts without leaking SQL or bound parameters.

Runtime privileges tested are schema USAGE and SELECT/INSERT on the five tables.
DDL, UPDATE/DELETE, public schema CREATE and Alembic version writes are not granted.
The migration owner is separate. Privilege setup on external/shared infrastructure
is an authorized operator action, not an adapter side effect. Multi-user read
authorization/RLS and retention/purge are not supplied by this foundation.

## Migrations and setup

Alembic environment is at root `alembic.ini` and `migrations/env.py`. One head:

1. `20261103_01`: repositories, snapshots, analysis_runs.
2. `20261103_02`: artifacts, run_reports.

DDL is frozen in each revision; no live metadata import rewrites migration history.
Run `uv run alembic upgrade head` using explicit migration credentials loaded by
H1's config, not a URL in ini/argv. Do not use create_all/stamp/startup migration.
Downgrade refuses destructive changes; [setup/recovery](postgresql-setup.md)
explains backup/restore and dedicated test commands.

## Actual verification and evidence

- Locked environment installed from H1's unchanged manifest/lock: Python 3.14.5,
  SQLAlchemy 2.1.6, psycopg 3.3.7, Alembic 1.20.1.
- Default backend suite: **385 passed, 26 skipped**, one pre-existing warning.
  Twenty-five opt-in DB cases then ran independently on real PostgreSQL.
- Final real DB suite: **25 passed** on PostgreSQL **17.11**, pinned Linux/amd64
  image `sha256:0b81cec82228160abfa753aeaad0609b709eb26eeb950f2e404ad2326e1cc370`.
- Fresh upgrade, populated M001 -> M002/reapply, rollback of failed M002 and retry,
  cross-repo/run/SHA FKs, invalid JSON/NaN/Infinity, multi-row rollback, runtime
  permissions, two-connection uniqueness, backup/restore exact rows, restored
  artifact digest/catalog and exact owned-container cleanup passed.
- Evidence: `var/storage-verification-da7c798d876b40d4b01fa050d57b3b4c/evidence.json`.
  Prior failed rowcount-test evidence retained in task handoff. No secrets in evidence.
- Ruff and exporter --check passed. No public/generated/frontend/CI/lock changes.

## H1 next scope

Implement the actual run/report adapter using these Tables, then test exact retry,
immutable mismatch/concurrency and full prepared-metadata round-trip through that
adapter with publication failure semantics. Existing foundation tests deliberately
use direct fixture SQL; they are not evidence the production adapter already works.
P3 evidence bundle and P5 retrieval remain pending. Inventory/test-case tables need
their separate domain checkpoint/migrations after foundation; do not add them here.

This is a prepared KH handoff and self-review; H1/AN receipt, review, CI and human
acceptance are not assumed. Codex assisted implementation/tests/docs; students must
review and understand the work before submission per Proposal Appendix C/D.
