"""Accepted inventory domain; append-only to the merged foundation.

Inventory and case rows must commit together. Recovery uses backup/restore;
downgrade deliberately refuses to discard frozen inventories.
"""

from alembic import op

revision = "20261104_03"
down_revision = "20261103_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE smartregression.analysis_runs ADD CONSTRAINT uq_run_invent"
        "ory_target UNIQUE (repository_id, run_id, target_sha, target_snapshot_"
        "id)"
    )
    op.execute(
        "CREATE TABLE smartregression.test_inventories (\n\trepository_id TEXT NO"
        "T NULL, \n\trun_id TEXT NOT NULL, \n\tinventory_id TEXT NOT NULL, \n\ttarget"
        "_sha TEXT NOT NULL, \n\ttarget_snapshot_id TEXT, \n\tframework TEXT NOT NU"
        "LL, \n\tcollector_version TEXT NOT NULL, \n\timage_id TEXT, \n\tconfiguratio"
        "n JSONB NOT NULL, \n\tconfiguration_sha256 TEXT NOT NULL, \n\tstage_status"
        " TEXT NOT NULL, \n\tcompleteness TEXT, \n\ttest_count INTEGER, \n\treason TE"
        "XT, \n\terror_code TEXT, \n\tlimitations JSONB NOT NULL, \n\texit_code INTEG"
        "ER, \n\tduration_seconds DOUBLE PRECISION, \n\tdiagnostic_artifact_id TEXT"
        ", \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT "
        "NULL, \n\tPRIMARY KEY (repository_id, run_id, inventory_id), \n\tCONSTRAIN"
        "T uq_inventory_run UNIQUE (repository_id, run_id), \n\tCONSTRAINT fk_inv"
        "entory_run FOREIGN KEY(repository_id, run_id) REFERENCES smartregressi"
        "on.analysis_runs (repository_id, run_id) ON DELETE RESTRICT ON UPDATE "
        "RESTRICT, \n\tCONSTRAINT fk_inventory_run_target FOREIGN KEY(repository_"
        "id, run_id, target_sha, target_snapshot_id) REFERENCES smartregression"
        ".analysis_runs (repository_id, run_id, target_sha, target_snapshot_id)"
        " ON DELETE RESTRICT ON UPDATE RESTRICT, \n\tCONSTRAINT fk_inventory_snap"
        "shot FOREIGN KEY(repository_id, target_sha, target_snapshot_id) REFERE"
        "NCES smartregression.snapshots (repository_id, commit_sha, snapshot_id"
        ") ON DELETE RESTRICT ON UPDATE RESTRICT, \n\tCONSTRAINT fk_inventory_dia"
        "gnostic FOREIGN KEY(repository_id, run_id, diagnostic_artifact_id) REF"
        "ERENCES smartregression.artifacts (repository_id, run_id, artifact_id)"
        " ON DELETE RESTRICT ON UPDATE RESTRICT, \n\tCONSTRAINT ck_inventory_id C"
        "HECK (octet_length(inventory_id) BETWEEN 1 AND 512 AND inventory_id = "
        "btrim(inventory_id)), \n\tCONSTRAINT ck_inventory_sha CHECK (target_sha "
        "~ '^([0-9a-f]{40}|[0-9a-f]{64})$'), \n\tCONSTRAINT ck_inventory_snapshot"
        " CHECK (target_snapshot_id IS NULL OR target_snapshot_id ~ '^[0-9a-f]{"
        "64}$'), \n\tCONSTRAINT ck_inventory_framework CHECK (framework = 'pytest"
        "'), \n\tCONSTRAINT ck_inventory_collector CHECK (length(collector_versio"
        "n) BETWEEN 1 AND 128), \n\tCONSTRAINT ck_inventory_image CHECK (image_id"
        " IS NULL OR image_id ~ '^sha256:[0-9a-f]{64}$'), \n\tCONSTRAINT ck_inven"
        "tory_config_hash CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$'), \n\tCO"
        "NSTRAINT ck_inventory_configuration CHECK (jsonb_typeof(configuration)"
        " = 'object'), \n\tCONSTRAINT ck_inventory_limitations CHECK (jsonb_typeo"
        "f(limitations) = 'array'), \n\tCONSTRAINT ck_inventory_exit CHECK (exit_"
        "code IS NULL OR exit_code BETWEEN 0 AND 255), \n\tCONSTRAINT ck_inventor"
        "y_duration CHECK (duration_seconds IS NULL OR (duration_seconds >= 0 A"
        "ND duration_seconds < 'Infinity'::float8 AND duration_seconds <> 'NaN'"
        "::float8)), \n\tCONSTRAINT ck_inventory_state CHECK ((stage_status IN ('"
        "not_implemented','not_run') AND completeness IS NULL AND test_count IS"
        " NULL AND reason ~ '^[a-z][a-z0-9_]*$' AND error_code IS NULL AND limi"
        "tations = '[]'::jsonb) OR (stage_status = 'failed' AND completeness IS"
        " NULL AND test_count IS NULL AND reason IS NULL AND error_code ~ '^[a-"
        "z][a-z0-9_]*$') OR (stage_status IN ('completed','partial') AND target"
        "_snapshot_id IS NOT NULL AND image_id IS NOT NULL AND test_count BETWE"
        "EN 0 AND 10000 AND reason IS NULL AND error_code IS NULL AND ((stage_s"
        "tatus = 'completed' AND completeness = 'complete' AND limitations = '["
        "]'::jsonb) OR (stage_status = 'partial' AND completeness = 'partial' A"
        "ND jsonb_array_length(limitations) > 0)))), \n\tCONSTRAINT ck_inventory_"
        "presence CHECK (stage_status IN ('not_implemented','not_run','failed',"
        "'completed','partial') AND (stage_status NOT IN ('completed','partial'"
        ") OR (completeness IS NOT NULL AND test_count IS NOT NULL)) AND (stage"
        "_status NOT IN ('not_implemented','not_run') OR reason IS NOT NULL) AN"
        "D (stage_status <> 'failed' OR error_code IS NOT NULL))\n)"
    )
    op.execute(
        "CREATE TABLE smartregression.test_cases (\n\trepository_id TEXT NOT NULL"
        ", \n\trun_id TEXT NOT NULL, \n\tinventory_id TEXT NOT NULL, \n\ttest_id_sha2"
        "56 TEXT NOT NULL, \n\ttest_id TEXT NOT NULL, \n\tordinal INTEGER NOT NULL,"
        " \n\tPRIMARY KEY (repository_id, run_id, inventory_id, test_id_sha256), "
        "\n\tCONSTRAINT uq_test_case_ordinal UNIQUE (repository_id, run_id, inven"
        "tory_id, ordinal), \n\tCONSTRAINT fk_test_case_inventory FOREIGN KEY(rep"
        "ository_id, run_id, inventory_id) REFERENCES smartregression.test_inve"
        "ntories (repository_id, run_id, inventory_id) ON DELETE RESTRICT ON UP"
        "DATE RESTRICT, \n\tCONSTRAINT ck_test_case_nonempty CHECK (octet_length("
        "test_id) > 0), \n\tCONSTRAINT ck_test_case_digest CHECK (test_id_sha256 "
        "= encode(sha256(convert_to(test_id, 'UTF8')), 'hex')), \n\tCONSTRAINT ck"
        "_test_case_ordinal CHECK (ordinal BETWEEN 0 AND 9999)\n)"
    )
    op.execute(
        "CREATE FUNCTION smartregression.check_inventory_rows() RETURNS trigger"
        "\nLANGUAGE plpgsql SET search_path = pg_catalog, smartregression AS $$\n"
        "DECLARE r text; n text; i text; expected integer; actual bigint; highe"
        "st integer; bytes bigint;\nBEGIN\n  IF TG_OP = 'DELETE' THEN\n    r := OL"
        "D.repository_id; n := OLD.run_id; i := OLD.inventory_id;\n  ELSE\n    r "
        ":= NEW.repository_id; n := NEW.run_id; i := NEW.inventory_id;\n  END IF"
        ";\n  SELECT COALESCE(test_count, 0) INTO expected FROM smartregression."
        "test_inventories\n    WHERE repository_id=r AND run_id=n AND inventory_"
        "id=i;\n  IF NOT FOUND THEN RETURN NULL; END IF;\n  SELECT count(*), max("
        "ordinal), COALESCE(sum(octet_length(test_id)), 0)\n    INTO actual, hig"
        "hest, bytes FROM smartregression.test_cases\n    WHERE repository_id=r "
        "AND run_id=n AND inventory_id=i;\n  IF actual <> expected OR (actual > "
        "0 AND highest <> actual - 1) OR bytes > 524288 THEN\n    RAISE EXCEPTIO"
        "N 'inventory rows inconsistent' USING ERRCODE='23514';\n  END IF;\n  RET"
        "URN NULL;\nEND $$"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER test_inventories_rows_consistent AFTER INSER"
        "T OR UPDATE OR DELETE ON smartregression.test_inventories DEFERRABLE I"
        "NITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION smartregression.check_"
        "inventory_rows()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER test_cases_rows_consistent AFTER INSERT OR U"
        "PDATE OR DELETE ON smartregression.test_cases DEFERRABLE INITIALLY DEF"
        "ERRED FOR EACH ROW EXECUTE FUNCTION smartregression.check_inventory_ro"
        "ws()"
    )


def downgrade():
    raise RuntimeError("Restore a verified backup; inventory downgrade is destructive.")
