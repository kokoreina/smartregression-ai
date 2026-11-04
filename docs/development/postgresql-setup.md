# PostgreSQL foundation setup and recovery

KH owns this five-table migration/setup interface; see [handoff](task-2.20-c.md),
[H1 config](task-2.20-b.md) and [checkpoint](task-2.20-checkpoint.md). There are no
automatic migrations at API/CLI startup. H1 owns pyproject/uv.lock; use the locked
Python 3.14 environment rather than adding dependencies independently.

## Dedicated test command

From ordinary PowerShell with Linux Docker and this checkout's locked `.venv`:

```powershell
& 'D:\C1.SE26\Repo-Sprint2-Khanh-2.20\scripts\storage\verify.ps1'
```

The wrapper checks default backend tests, Ruff and contracts, then launches one
fresh labelled PostgreSQL container. It uses the pinned official Linux/amd64 image
in `scripts/storage/postgres-image.json`, ephemeral loopback port, random memory-only
credentials and dedicated databases. It accepts no external DSN and verifies its
exact container label before cleanup, including its own anonymous volume. No prune,
existing DB/volume use, credentials in argv or secret artifacts are involved.

To rerun only the DB work when other checks already have sufficient evidence:

```powershell
& 'D:\C1.SE26\Repo-Sprint2-Khanh-2.20\scripts\storage\verify.ps1' -DatabaseOnly
```

The 40 PostgreSQL tests are opt-in. Default pytest skips them without the harness
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

Expected head is `20261103_02`. Revision one creates repositories/snapshots/runs;
revision two creates artifact/report catalog. Reapplying head changes no data.
Unexpected objects, conflicting revisions or a shared/unknown target must be
investigated; do not stamp/drop/reset to bypass errors. Offline DDL review needs
neither credentials nor a connection:

```powershell
uv run alembic upgrade head --sql
```

Runtime uses `SMARTREGRESSION_DATABASE_URL`, a separate role with schema USAGE and
SELECT/INSERT on the five application tables, not table ownership, DDL, UPDATE/DELETE
or Alembic version access. Provisioning roles/grants on existing infrastructure is
an explicitly authorized operator action. Migrations do not create accounts or
change shared-server permissions. A provisioned row does not authorize users to
read repository data; multi-user backend authorization remains separate.

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
