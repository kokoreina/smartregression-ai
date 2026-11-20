"""Add repository assistant conversations, durable watches and webhook receipts."""

from alembic import op

revision = "20261119_16"
down_revision = "20261115_15"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
CREATE TABLE smartregression.web_assistant_threads (
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	project_id UUID NOT NULL,
	commit TEXT NOT NULL,
	config_digest TEXT NOT NULL,
	title TEXT NOT NULL,
	idempotency_key TEXT NOT NULL,
	input_digest TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
        FOREIGN KEY(owner_id, project_id) REFERENCES smartregression.web_projects (owner_id, id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
	UNIQUE (owner_id, project_id, id),
	UNIQUE (owner_id, project_id, idempotency_key),
        FOREIGN KEY(owner_id, project_id, commit, config_digest) REFERENCES
smartregression.web_explorer_snapshots (owner_id, project_id, commit, config_digest) ON DELETE
RESTRICT ON UPDATE RESTRICT,
	CHECK (length(title) BETWEEN 1 AND 120)
);
CREATE INDEX ix_assistant_threads_project ON smartregression.web_assistant_threads (owner_id,
project_id, created_at DESC);
CREATE TABLE smartregression.web_assistant_messages (
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	project_id UUID NOT NULL,
	thread_id UUID NOT NULL,
	idempotency_key TEXT NOT NULL,
	input_digest TEXT NOT NULL,
	question TEXT NOT NULL,
	reply JSONB NOT NULL,
	reply_digest TEXT NOT NULL,
	ai_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
        FOREIGN KEY(owner_id, project_id, thread_id) REFERENCES
smartregression.web_assistant_threads (owner_id, project_id, id) ON DELETE RESTRICT ON UPDATE
RESTRICT,
	UNIQUE (owner_id, project_id, thread_id, idempotency_key),
	CHECK (length(question) BETWEEN 1 AND 600),
	CHECK (jsonb_typeof(reply)='object' AND octet_length(reply::text)<=131072),
        FOREIGN KEY(ai_id) REFERENCES smartregression.web_ai_requests (id) ON DELETE RESTRICT ON
UPDATE RESTRICT
);
CREATE INDEX ix_assistant_messages_thread ON smartregression.web_assistant_messages (thread_id,
created_at);
CREATE TABLE smartregression.web_repo_watches (
	owner_id UUID NOT NULL,
	project_id UUID NOT NULL,
	branch TEXT NOT NULL,
	paths JSONB NOT NULL,
	automatic BOOLEAN NOT NULL,
	interval_seconds INTEGER NOT NULL,
	version INTEGER NOT NULL,
	last_commit TEXT NOT NULL,
	checked_at TIMESTAMP WITH TIME ZONE,
	next_check_at TIMESTAMP WITH TIME ZONE NOT NULL,
	pending BOOLEAN DEFAULT FALSE NOT NULL,
	lease_token UUID,
	lease_until TIMESTAMP WITH TIME ZONE,
	error_code TEXT,
	PRIMARY KEY (owner_id, project_id),
        FOREIGN KEY(owner_id, project_id) REFERENCES smartregression.web_projects (owner_id, id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
	CHECK (jsonb_typeof(paths)='array' AND jsonb_array_length(paths)<=20),
	CHECK (interval_seconds BETWEEN 300 AND 86400 AND version>0),
	CHECK (last_commit ~ '^[0-9a-f]{40}$')
);
CREATE TABLE smartregression.web_change_notifications (
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	project_id UUID NOT NULL,
	report JSONB NOT NULL,
	report_digest TEXT NOT NULL,
	identity_digest TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	read_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
        FOREIGN KEY(owner_id, project_id) REFERENCES smartregression.web_projects (owner_id, id)
ON DELETE RESTRICT ON UPDATE RESTRICT,
	UNIQUE (owner_id, project_id, identity_digest),
	CHECK (jsonb_typeof(report)='object' AND octet_length(report::text)<=1048576)
);
CREATE INDEX ix_change_notifications_project ON smartregression.web_change_notifications
(owner_id, project_id, created_at DESC);
CREATE TABLE smartregression.web_github_deliveries (
	id UUID NOT NULL,
	payload_digest TEXT NOT NULL,
	repository TEXT NOT NULL,
	event TEXT NOT NULL,
	branch TEXT NOT NULL,
	actor TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	CHECK (length(repository)<=140 AND length(event)<=40 AND length(branch)<=200)
);
DO $$ DECLARE item RECORD; BEGIN
FOR item IN SELECT conname FROM pg_constraint WHERE
conrelid='smartregression.web_ai_requests'::regclass
AND contype='c' AND position('folder' in pg_get_constraintdef(oid))>0 LOOP
EXECUTE format('ALTER TABLE smartregression.web_ai_requests DROP CONSTRAINT %I',item.conname);
END LOOP; END $$;
ALTER TABLE smartregression.web_ai_requests ADD CONSTRAINT ck_web_ai_assistant_actions
CHECK(action IN
('commit','hypothesis','reading_guide','search','file','folder','overview','chat','changes'));
    """)


def downgrade():
    raise RuntimeError("forward_only_migration_restore_backup")
