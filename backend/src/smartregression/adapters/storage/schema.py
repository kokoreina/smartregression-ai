"""Five-table PostgreSQL foundation owned by KH, checkpoint 2.20 P1/P2/P4.

No connections or create_all side effects. H1's adapters import these Table objects;
versioned migrations contain frozen DDL rather than importing evolving metadata.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "smartregression"
metadata = sa.MetaData(schema=SCHEMA)
_SHA = "^([0-9a-f]{40}|[0-9a-f]{64})$"
_DIGEST = "^[0-9a-f]{64}$"
_STATES = "('not_implemented','not_run','completed','partial','failed')"
STAGES = (
    "snapshots",
    "changes",
    "graph",
    "impact",
    "inventory",
    "retrieval",
    "evidence",
    "review_ordering",
)


def _check(expression: str, name: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(expression, name=name)


def _id_check(column: str, name: str) -> sa.CheckConstraint:
    return _check(
        f"octet_length({column}) BETWEEN 1 AND 512 AND {column} = btrim({column})",
        name,
    )


def _created() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def _fk(local: list[str], remote: list[str], name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        local,
        [SCHEMA + "." + value for value in remote],
        name=name,
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


repositories = sa.Table(
    "repositories",
    metadata,
    sa.Column("repository_id", sa.Text, primary_key=True),
    sa.Column("source_kind", sa.Text, nullable=False),
    _created(),
    _check("repository_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'", "ck_repository_id"),
    _check("source_kind IN ('local','github')", "ck_repository_source_kind"),
)

snapshots = sa.Table(
    "snapshots",
    metadata,
    sa.Column("repository_id", sa.Text, primary_key=True),
    sa.Column("commit_sha", sa.Text, primary_key=True),
    sa.Column("snapshot_id", sa.Text, primary_key=True),
    sa.Column("manifest_version", sa.Text, nullable=False),
    sa.Column("materializer_version", sa.Text, nullable=False),
    _created(),
    _fk(["repository_id"], ["repositories.repository_id"], "fk_snapshot_repository"),
    _check(f"commit_sha ~ '{_SHA}'", "ck_snapshot_commit"),
    _check(f"snapshot_id ~ '{_DIGEST}'", "ck_snapshot_digest"),
    _check("length(manifest_version) BETWEEN 1 AND 128", "ck_snapshot_manifest_version"),
    _check("length(materializer_version) BETWEEN 1 AND 128", "ck_snapshot_materializer_version"),
)

analysis_runs = sa.Table(
    "analysis_runs",
    metadata,
    sa.Column("repository_id", sa.Text, primary_key=True),
    sa.Column("run_id", sa.Text, primary_key=True),
    sa.Column("base_sha", sa.Text, nullable=False),
    sa.Column("target_sha", sa.Text, nullable=False),
    sa.Column("base_snapshot_id", sa.Text),
    sa.Column("target_snapshot_id", sa.Text),
    sa.Column("comparison_mode", sa.Text, nullable=False),
    sa.Column("data_kind", sa.Text, nullable=False),
    sa.Column("configuration", JSONB, nullable=False),
    sa.Column("configuration_sha256", sa.Text, nullable=False),
    _created(),
    _fk(["repository_id"], ["repositories.repository_id"], "fk_run_repository"),
    *[
        _fk(
            ["repository_id", f"{side}_sha", f"{side}_snapshot_id"],
            ["snapshots.repository_id", "snapshots.commit_sha", "snapshots.snapshot_id"],
            f"fk_run_{side}_snapshot",
        )
        for side in ("base", "target")
    ],
    _id_check("run_id", "ck_run_id"),
    *[_check(f"{side}_sha ~ '{_SHA}'", f"ck_run_{side}_sha") for side in ("base", "target")],
    *[
        _check(
            f"{side}_snapshot_id IS NULL OR {side}_snapshot_id ~ '{_DIGEST}'",
            f"ck_run_{side}_digest",
        )
        for side in ("base", "target")
    ],
    _check(
        "base_sha <> target_sha OR base_snapshot_id IS NULL OR target_snapshot_id IS NULL "
        "OR base_snapshot_id = target_snapshot_id",
        "ck_run_same_commit",
    ),
    _check("comparison_mode = 'direct_two_tree'", "ck_run_comparison"),
    _check("data_kind IN ('demo','real')", "ck_run_data_kind"),
    _check("jsonb_typeof(configuration) = 'object'", "ck_run_configuration"),
    _check(f"configuration_sha256 ~ '{_DIGEST}'", "ck_run_configuration_digest"),
)

artifacts = sa.Table(
    "artifacts",
    metadata,
    sa.Column("repository_id", sa.Text, primary_key=True),
    sa.Column("artifact_id", sa.Text, primary_key=True),
    sa.Column("run_id", sa.Text),
    sa.Column("storage_key", sa.Text, nullable=False, unique=True),
    sa.Column("kind", sa.Text, nullable=False),
    sa.Column("sha256", sa.Text, nullable=False),
    sa.Column("size_bytes", sa.BigInteger, nullable=False),
    sa.Column("media_type", sa.Text, nullable=False),
    sa.Column("schema_version", sa.Text),
    sa.Column("access_class", sa.Text, nullable=False),
    _created(),
    sa.UniqueConstraint("repository_id", "run_id", "artifact_id", name="uq_artifact_run_scope"),
    _fk(["repository_id"], ["repositories.repository_id"], "fk_artifact_repository"),
    _fk(
        ["repository_id", "run_id"],
        ["analysis_runs.repository_id", "analysis_runs.run_id"],
        "fk_artifact_run",
    ),
    _id_check("artifact_id", "ck_artifact_id"),
    _check(
        "run_id IS NULL OR (octet_length(run_id) BETWEEN 1 AND 512 AND run_id=btrim(run_id))",
        "ck_artifact_run_id",
    ),
    _check("octet_length(storage_key) BETWEEN 1 AND 2048", "ck_artifact_storage_key"),
    _check("kind IN ('snapshot','manifest','report_json','log','index')", "ck_artifact_kind"),
    _check(f"sha256 ~ '{_DIGEST}'", "ck_artifact_digest"),
    _check("size_bytes >= 0", "ck_artifact_size"),
    _check("length(media_type) > 0", "ck_artifact_media_type"),
    _check("access_class IN ('repository','service_only')", "ck_artifact_access"),
    _check(
        "kind <> 'report_json' OR (run_id IS NOT NULL AND schema_version IS NOT NULL "
        "AND schema_version = '2.0.0' AND media_type = 'application/json' "
        "AND access_class = 'repository')",
        "ck_artifact_report_metadata",
    ),
)

_stage_keys = "ARRAY[" + ",".join("'" + key + "'" for key in STAGES) + "]"
_summary_checks = [
    "jsonb_typeof(stage_summary) = 'object'",
    f"stage_summary ?& {_stage_keys}",
    f"stage_summary - {_stage_keys} = '{{}}'::jsonb",
]
for _stage in STAGES:
    _item = f"(stage_summary->'{_stage}')"
    _summary_checks.extend(
        [
            f"jsonb_typeof({_item}) = 'object'",
            f"{_item} ?& ARRAY['status','limitations']",
            f"jsonb_typeof({_item}->'status') = 'string'",
            f"{_item}->>'status' IN {_STATES}",
            f"jsonb_typeof({_item}->'limitations') = 'array'",
            f"{_item} - ARRAY['status','reason','error_code','limitations'] = '{{}}'::jsonb",
        ]
    )

run_reports = sa.Table(
    "run_reports",
    metadata,
    sa.Column("repository_id", sa.Text, primary_key=True),
    sa.Column("run_id", sa.Text, primary_key=True),
    sa.Column("report_id", sa.Text, primary_key=True),
    sa.Column("artifact_id", sa.Text, nullable=False),
    sa.Column("schema_version", sa.Text, nullable=False),
    sa.Column("analysis_status", sa.Text, nullable=False),
    sa.Column("stage_summary", JSONB, nullable=False),
    sa.Column("analysis_duration_seconds", sa.Double),
    sa.Column("llm_cost_usd", sa.Double),
    _created(),
    _fk(
        ["repository_id", "run_id"],
        ["analysis_runs.repository_id", "analysis_runs.run_id"],
        "fk_report_run",
    ),
    _fk(
        ["repository_id", "run_id", "artifact_id"],
        ["artifacts.repository_id", "artifacts.run_id", "artifacts.artifact_id"],
        "fk_report_artifact",
    ),
    _id_check("report_id", "ck_report_id"),
    _check("schema_version = '2.0.0'", "ck_report_schema_version"),
    _check(f"analysis_status IN {_STATES}", "ck_report_status"),
    _check(" AND ".join(_summary_checks), "ck_report_summary"),
    *[
        _check(
            f"{column} IS NULL OR ({column} >= 0 AND {column} < 'Infinity'::float8 "
            f"AND {column} <> 'NaN'::float8)",
            f"ck_report_{column}",
        )
        for column in ("analysis_duration_seconds", "llm_cost_usd")
    ],
)
