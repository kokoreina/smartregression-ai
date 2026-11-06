from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from smartregression.adapters.storage.schema import metadata


def test_foundation_and_inventory_have_scoped_keys_and_foreign_keys():
    assert set(metadata.tables) == {
        "smartregression." + name
        for name in (
            "repositories",
            "snapshots",
            "analysis_runs",
            "artifacts",
            "run_reports",
            "evidence_bundles",
            "test_inventories",
            "test_cases",
            "knowledge_indexes",
            "index_chunks",
        )
    }
    runs = metadata.tables["smartregression.analysis_runs"]
    assert list(runs.primary_key.columns.keys()) == ["repository_id", "run_id"]
    reports = metadata.tables["smartregression.run_reports"]
    assert list(reports.primary_key.columns.keys()) == ["repository_id", "run_id", "report_id"]
    assert {tuple(fk.column_keys) for fk in reports.foreign_key_constraints} == {
        ("repository_id", "run_id"),
        ("repository_id", "run_id", "artifact_id"),
    }
    for table in metadata.tables.values():
        assert table.schema == "smartregression"
        for fk in table.foreign_key_constraints:
            assert fk.ondelete == "RESTRICT" and fk.onupdate == "RESTRICT"
    sql = str(CreateTable(reports).compile(dialect=dialect()))
    assert "stage_summary" in sql and "JSONB" in sql
    assert "NaN" in sql and "Infinity" in sql


def test_migration_chain_has_one_head_and_ordered_revisions():
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20261105_05"]
    assert [(r.revision, r.down_revision) for r in script.walk_revisions()] == [
        ("20261105_05", "20261104_04"),
        ("20261104_04", "20261104_03"),
        ("20261104_03", "20261103_02"),
        ("20261103_02", "20261103_01"),
        ("20261103_01", None),
    ]
