"""Frozen PostgreSQL DDL for 20261103_02."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_02"
down_revision = "20261103_01"
branch_labels = None
depends_on = None

_DDL = (
    """
    CREATE TABLE smartregression.artifacts (
    repository_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    run_id TEXT,
    storage_key TEXT NOT NULL,
    kind TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    media_type TEXT NOT NULL,
    schema_version TEXT,
    access_class TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (repository_id, artifact_id),
    CONSTRAINT uq_artifact_run_scope UNIQUE (repository_id, run_id, artifact_id),
    CONSTRAINT fk_artifact_repository FOREIGN KEY(repository_id) REFERENCES
    smartregression.repositories (repository_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_artifact_run FOREIGN KEY(repository_id, run_id) REFERENCES
    smartregression.analysis_runs (repository_id, run_id) ON DELETE RESTRICT ON UPDATE
    RESTRICT,
    CONSTRAINT ck_artifact_id CHECK (octet_length(artifact_id) BETWEEN 1 AND 512 AND
    artifact_id = btrim(artifact_id)),
    CONSTRAINT ck_artifact_run_id CHECK (run_id IS NULL OR (octet_length(run_id) BETWEEN 1
    AND 512 AND run_id=btrim(run_id))),
    CONSTRAINT ck_artifact_storage_key CHECK (octet_length(storage_key) BETWEEN 1 AND 2048),
    CONSTRAINT ck_artifact_kind CHECK (kind IN
    ('snapshot','manifest','report_json','log','index')),
    CONSTRAINT ck_artifact_digest CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_artifact_size CHECK (size_bytes >= 0),
    CONSTRAINT ck_artifact_media_type CHECK (length(media_type) > 0),
    CONSTRAINT ck_artifact_access CHECK (access_class IN ('repository','service_only')),
    CONSTRAINT ck_artifact_report_metadata CHECK (kind <> 'report_json' OR (run_id IS NOT
    NULL AND schema_version IS NOT NULL AND schema_version = '2.0.0' AND media_type =
    'application/json' AND access_class = 'repository')),
    UNIQUE (storage_key)
    )
    """,
    """
    CREATE TABLE smartregression.run_reports (
    repository_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    report_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    analysis_status TEXT NOT NULL,
    stage_summary JSONB NOT NULL,
    analysis_duration_seconds DOUBLE PRECISION,
    llm_cost_usd DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (repository_id, run_id, report_id),
    CONSTRAINT fk_report_run FOREIGN KEY(repository_id, run_id) REFERENCES
    smartregression.analysis_runs (repository_id, run_id) ON DELETE RESTRICT ON UPDATE
    RESTRICT,
    CONSTRAINT fk_report_artifact FOREIGN KEY(repository_id, run_id, artifact_id) REFERENCES
    smartregression.artifacts (repository_id, run_id, artifact_id) ON DELETE RESTRICT ON
    UPDATE RESTRICT,
    CONSTRAINT ck_report_id CHECK (octet_length(report_id) BETWEEN 1 AND 512 AND report_id =
    btrim(report_id)),
    CONSTRAINT ck_report_schema_version CHECK (schema_version = '2.0.0'),
    CONSTRAINT ck_report_status CHECK (analysis_status IN
    ('not_implemented','not_run','completed','partial','failed')),
    CONSTRAINT ck_report_summary CHECK (jsonb_typeof(stage_summary) = 'object' AND
    stage_summary ?&
    ARRAY['snapshots','changes','graph','impact','inventory','retrieval','evidence','review_ordering']
    AND stage_summary -
    ARRAY['snapshots','changes','graph','impact','inventory','retrieval','evidence','review_ordering']
    = '{}'::jsonb AND jsonb_typeof((stage_summary->'snapshots')) = 'object' AND
    (stage_summary->'snapshots') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'snapshots')->'status') = 'string' AND
    (stage_summary->'snapshots')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'snapshots')->'limitations') = 'array' AND
    (stage_summary->'snapshots') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'changes')) = 'object' AND
    (stage_summary->'changes') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'changes')->'status') = 'string' AND
    (stage_summary->'changes')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'changes')->'limitations') = 'array' AND
    (stage_summary->'changes') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'graph')) = 'object' AND
    (stage_summary->'graph') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'graph')->'status') = 'string' AND
    (stage_summary->'graph')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'graph')->'limitations') = 'array' AND
    (stage_summary->'graph') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'impact')) = 'object' AND
    (stage_summary->'impact') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'impact')->'status') = 'string' AND
    (stage_summary->'impact')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'impact')->'limitations') = 'array' AND
    (stage_summary->'impact') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'inventory')) = 'object' AND
    (stage_summary->'inventory') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'inventory')->'status') = 'string' AND
    (stage_summary->'inventory')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'inventory')->'limitations') = 'array' AND
    (stage_summary->'inventory') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'retrieval')) = 'object' AND
    (stage_summary->'retrieval') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'retrieval')->'status') = 'string' AND
    (stage_summary->'retrieval')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'retrieval')->'limitations') = 'array' AND
    (stage_summary->'retrieval') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'evidence')) = 'object' AND
    (stage_summary->'evidence') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'evidence')->'status') = 'string' AND
    (stage_summary->'evidence')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'evidence')->'limitations') = 'array' AND
    (stage_summary->'evidence') - ARRAY['status','reason','error_code','limitations'] =
    '{}'::jsonb AND jsonb_typeof((stage_summary->'review_ordering')) = 'object' AND
    (stage_summary->'review_ordering') ?& ARRAY['status','limitations'] AND
    jsonb_typeof((stage_summary->'review_ordering')->'status') = 'string' AND
    (stage_summary->'review_ordering')->>'status' IN
    ('not_implemented','not_run','completed','partial','failed') AND
    jsonb_typeof((stage_summary->'review_ordering')->'limitations') = 'array' AND
    (stage_summary->'review_ordering') - ARRAY['status','reason','error_code','limitations']
    = '{}'::jsonb),
    CONSTRAINT ck_report_analysis_duration_seconds CHECK (analysis_duration_seconds IS NULL
    OR (analysis_duration_seconds >= 0 AND analysis_duration_seconds < 'Infinity'::float8
    AND analysis_duration_seconds <> 'NaN'::float8)),
    CONSTRAINT ck_report_llm_cost_usd CHECK (llm_cost_usd IS NULL OR (llm_cost_usd >= 0 AND
    llm_cost_usd < 'Infinity'::float8 AND llm_cost_usd <> 'NaN'::float8))
    )
    """,
)


def upgrade():
    for statement in _DDL:
        op.execute(sa.text(statement))


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")
