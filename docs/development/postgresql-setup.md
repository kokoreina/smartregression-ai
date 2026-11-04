# PostgreSQL foundation setup and recovery

KH owns this five-table migration/setup interface; see [handoff](task-2.20-c.md),
[H1 config](task-2.20-b.md) and [checkpoint](task-2.20-checkpoint.md). There are no
automatic migrations at API/CLI startup. H1 owns pyproject/uv.lock; use the locked
Python 3.14 environment rather than adding dependencies independently.

## Dedicated test command

From ordinary PowerShell with Linux Docker and this checkout's locked `.venv`:

```powershell
& .\scripts\storage\verify.ps1
```

The wrapper checks default backend tests, Ruff and contracts, then launches one
fresh labelled PostgreSQL container. It uses the pinned official Linux/amd64 image
in `scripts/storage/postgres-image.json`, ephemeral loopback port, random memory-only
credentials and dedicated databases. It accepts no external DSN and verifies its
exact container label before cleanup, including its own anonymous volume. No prune,
existing DB/volume use, credentials in argv or secret artifacts are involved.

To rerun only the DB work when other checks already have sufficient evidence:

```powershell
& .\scripts\storage\verify.ps1 -DatabaseOnly
```

The PostgreSQL tests are opt-in. After inventory/main integration, the 2.13 publishing
check passed 72 cases and skipped two candidate-to-DB cases requiring the inventory
harness. Default pytest skips DB cases without the harness
context; those skips are not PostgreSQL acceptance. Fixtures check the exact labelled
container, published loopback port, dedicated DB name and PostgreSQL major version.
The observed server is 17.11; a mutable tag is never treated as an image digest.

## Separately provisioned server

Use an already authorized dedicated target with a migration owner allowed to create
the fixed `smartregression` schema. Supply `SMARTREGRESSION_MIGRATION_DATABASE_URL`
through the backend secret/environment mechanism in H1's `postgresql+psycopg` format.
Remote TLS requires verify-full. No password/URL belongs in ini, argv, Git or logs.
Ordinary Alembic commands do not enable the plaintext loopback test exception.
The scoped test harness instead constructs explicit validated DatabaseSettings.

```powershell
uv run alembic current
uv run alembic upgrade head
uv run alembic current
```

Expected head after P3 evidence integration is `20261104_04`. Revision one creates
repositories/snapshots/runs; revision two creates artifact/report catalog; revision
three adds inventory/test-case tables; revision four adds bounded immutable
evidence_bundles. Reapplying head changes no data.
Unexpected objects, conflicting revisions or a shared/unknown target must be
investigated; do not stamp/drop/reset to bypass errors. Offline DDL review needs
neither credentials nor a connection:

```powershell
uv run alembic upgrade head --sql
```

Runtime uses `SMARTREGRESSION_DATABASE_URL`, a separate role with schema USAGE and
SELECT/INSERT on the required foundation/domain tables (including evidence_bundles
for 2.05), not table ownership, DDL, UPDATE/DELETE
or Alembic version access. Provisioning roles/grants on existing infrastructure is
an explicitly authorized operator action. Migrations do not create accounts or
change shared-server permissions. A provisioned row does not authorize users to
read repository data; multi-user backend authorization remains separate.

## Opt-in CLI analysis persistence

The prompt-6 integration branch uses one SQL transaction for report metadata and
an optional complete EvidenceBundle, as specified by [P3](task-2.05-p3.md#p3-integration).
Typed unavailable/failed stages never receive fabricated bundle data. Diagnostics
distinguish evidence saved from not included. Database migrations/grants must include
revision `20261104_04`; existing report-only deployments require upgrade first.
See [integration handoff](task-2.13.md#evidence-integration) for actual verification
and dependency/merge status; this note does not claim the branch is already on main.

After migrations, a trusted operator must provision the repository ID explicitly;
the report/CLI cannot register it. For example, on the authorized target only:

```sql
INSERT INTO smartregression.repositories (repository_id, source_kind)
VALUES ('repo-1', 'local');
```

This establishes metadata scope, not permission to read any local repository or
multi-user authorization. Independently verify the operator's exact source-root/ID
binding. Create an existing controlled artifact directory disjoint from the source
root (neither may contain the other); links/junctions in artifact ancestry are rejected.

Supply runtime credentials through the existing backend environment/secret mechanism,
never argv, ini, shared logs or Git. The runtime URL uses `postgresql+psycopg` and
TLS verify-full; no migration-credential fallback or production TLS bypass exists.

```powershell
uv run smartregression analyze --repository D:/authorized/repo --repository-id repo-1 --authorized-root D:/authorized/repo --base <FULL_BASE_SHA> --target <FULL_TARGET_SHA> --persist --artifact-root D:/authorized-artifacts
```

The command is a template requiring authorized paths/SHA/credentials. `--persist`
and `--artifact-root` must be supplied together; `--output` cannot be combined with
them. Source is inspected from frozen Git bytes, never imported/executed.

The canonical JSON artifact is published as `<run_id>/<report_id>.json` under the
root; its artifact ID equals the report ID within the artifact namespace. After SQL
save returns, JSON is printed on stdout; stderr states analysis status and
`Persistence saved` with run/report IDs. Successful persistence preserves analyze
exit codes: 0 complete, 1 incomplete without failed stages, 2 stage failure. Thus
exit 1 or 2 can accompany a successfully saved partial report; inspect diagnostics.
`Persistence failed: <safe_code>` is exit 2 without stdout JSON or a saved message.

File publication precedes the metadata transaction. Failed SQL saves roll back
metadata; a complete file may remain, including after an ambiguous commit. Do not
delete it automatically or assume absence of DB rows. Inspect the selected artifact
root/catalog before reconciliation. No distributed transaction, automatic retry,
garbage collector or CLI resume protocol is provided. Running analyze again makes
a new run/report, not an exact retry of a failed save.

Without `--persist`, analyze/help/health do not load DB infrastructure/settings or
require a database, even if DB environment variables are invalid. No automatic
migrations or repository provisioning are introduced. Actual verification and
limitations are recorded in [task 2.13](task-2.13.md#persistence-wiring).

## Failure and recovery

Transactional DDL keeps migration/version changes atomic. The test injects failure
between the tables in revision two: artifacts and the new version must both be
absent, revision one stays, and retry succeeds. H1 transaction contexts roll back
multi-row business/database failures and surface safe codes without retrying an
ambiguous commit.

Downgrade is intentionally unsupported with `forward_only_migration_restore_backup`.
Recreating structures is not restoring deleted bytes. Back up before operational
changes; restore into a distinct authorized isolated database/root before switching
consumers. Never overwrite the source as a diagnostic shortcut.

The harness demonstrates a **quiescent synthetic foundation recovery drill**:
a fresh DB upgrades to head, then a real DEMO report/file is prepared through H1's
metadata boundary and stored through BoundRunReportStore. All writers stop before
dumping. The fixed schema restores into a second fresh DB; the fixture artifact
tree copies to a new root. Exact rows, artifact digest/size/bytes and restored
catalog references are compared. Nullable measurements and partial report status
survive. Repository provisioning remains labelled fixture setup; run/report
metadata save uses the same adapter supplied for application callers.

The dump uses `--no-owner --no-acl`. Operational recovery must provision/reapply and
verify owner/runtime privileges separately. This is not a live distributed backup
protocol or recovery SLA. Publication/conflict/retry/domain adapters still need
their own work. Retained ignored dumps contain synthetic fixture data only.
