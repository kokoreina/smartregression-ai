"""Explicit collection opt-in; argument guards precede acquisition and execution."""

import importlib

import pytest
from test_analysis_workflow import BASE, TARGET, Source
from test_mapping_workflow import Collector

import smartregression.composition as composition


@pytest.mark.parametrize(
    "options",
    [
        {"inventory_candidate": "sqlparse"},
        {"inventory_image": "sha256:" + "a" * 64},
        {"inventory_workspace": "worker"},
        {"mapping_artifact_root": "artifacts"},
        {
            "inventory_candidate": "unapproved",
            "inventory_image": "sha256:" + "a" * 64,
            "inventory_workspace": "worker",
            "mapping_artifact_root": "artifacts",
        },
        {
            "inventory_candidate": "sqlparse",
            "inventory_image": "latest",
            "inventory_workspace": "worker",
            "mapping_artifact_root": "artifacts",
        },
    ],
)
def test_invalid_opt_in_never_acquires_source(tmp_path, monkeypatch, options):
    monkeypatch.setattr(composition, "LocalGit", lambda _: pytest.fail("must reject first"))
    with pytest.raises(ValueError, match="invalid_inventory_arguments"):
        composition.analyze_local(
            repository=tmp_path,
            repository_id="fixture",
            authorized_root=tmp_path,
            base=BASE,
            target=TARGET,
            data_kind="demo",
            **options,
        )


def test_opt_in_uses_composition_collector_and_publishes_mapping(tmp_path, monkeypatch):
    from smartregression.adapters.runners import candidate_inventory

    repo, workspace, artifacts = (tmp_path / name for name in ("input", "worker", "artifacts"))
    for path in (repo, workspace, artifacts):
        path.mkdir()
    collector = Collector()
    monkeypatch.setattr(candidate_inventory, "CANDIDATES", {"fixture": ("fixture", TARGET, "tree")})
    calls = []

    def factory(name, image, project, worker):
        calls.append((name, image, project, worker))
        return collector

    monkeypatch.setattr(candidate_inventory, "CandidateInventoryCollector", factory)
    monkeypatch.setattr(composition, "LocalGit", lambda _: Source(repo))
    report = composition.analyze_local(
        repository=repo,
        repository_id="fixture",
        authorized_root=repo,
        base=BASE,
        target=TARGET,
        data_kind="demo",
        inventory_candidate="fixture",
        inventory_image="sha256:" + "a" * 64,
        inventory_workspace=workspace,
        mapping_artifact_root=artifacts,
    )
    assert collector.calls == 1
    assert calls[0][0] == "fixture"
    assert (calls[0][2] / "scripts/inventory/collect.py").is_file()
    assert calls[0][3] == workspace
    assert (artifacts / report.identity.run_id / (report.report_id + ".mapping.json")).is_file()


def test_cli_passes_explicit_inventory_options_to_composition(tmp_path, monkeypatch, capsys):
    module = importlib.import_module("smartregression.cli.main")
    captured = {}

    def observe(**kwargs):
        captured.update(kwargs)
        raise ValueError("invalid_inventory_arguments")

    monkeypatch.setattr(module, "analyze_local", observe)
    code = module.main(
        [
            "analyze",
            "--repository",
            str(tmp_path),
            "--repository-id",
            "sqlparse",
            "--authorized-root",
            str(tmp_path),
            "--base",
            BASE,
            "--target",
            TARGET,
            "--inventory-candidate",
            "sqlparse",
            "--inventory-image",
            "sha256:" + "a" * 64,
            "--inventory-workspace",
            str(tmp_path / "worker"),
            "--mapping-artifact-root",
            str(tmp_path / "artifacts"),
        ]
    )
    assert code == 2
    assert captured["inventory_candidate"] == "sqlparse"
    assert captured["inventory_workspace"] == tmp_path / "worker"
    assert "invalid_inventory_arguments" in capsys.readouterr().err


@pytest.mark.parametrize("mutation", ["repository", "target", "image", "workspace", "injected"])
def test_candidate_opt_in_rejects_mismatched_scope_before_execution(
    tmp_path, monkeypatch, mutation
):
    from smartregression.adapters.runners import candidate_inventory

    repo, workspace = tmp_path / "input", tmp_path / "worker"
    repo.mkdir()
    workspace.mkdir()
    monkeypatch.setattr(candidate_inventory, "CANDIDATES", {"fixture": ("fixture", TARGET, "tree")})
    monkeypatch.setattr(
        candidate_inventory,
        "CandidateInventoryCollector",
        lambda *a: pytest.fail("invalid opt-in must not create a collector"),
    )
    kwargs = dict(
        repository=repo,
        repository_id="fixture",
        authorized_root=repo,
        base=BASE,
        target=TARGET,
        data_kind="demo",
        inventory_candidate="fixture",
        inventory_image="sha256:" + "a" * 64,
        inventory_workspace=workspace,
        mapping_artifact_root=tmp_path / "artifacts",
    )
    kwargs.update(
        {
            "repository": {"repository_id": "foreign"},
            "target": {"target": BASE},
            "image": {"inventory_image": "latest"},
            "workspace": {"inventory_workspace": repo},
            "injected": {"mapping_collector": Collector()},
        }[mutation]
    )
    with pytest.raises(ValueError, match="invalid_inventory_arguments"):
        composition.analyze_local(**kwargs)


def test_compound_store_rejects_foreign_inventory_before_database(tmp_path):
    from test_mapping_workflow import execute

    from smartregression.adapters.storage.analysis_store import PostgresAnalysisStore
    from smartregression.application.inventory_store import prepare_inventory
    from smartregression.application.run_store import RunMetadataError

    execution = execute(tmp_path, Collector())
    report = execution.report
    inventory = prepare_inventory(
        identity=report.identity.model_copy(update={"run_id": "foreign-run"}),
        inventory_id="foreign-run-inventory",
        stage=report.stages.inventory,
        configuration=Collector.configuration,
    )
    with pytest.raises(RunMetadataError):
        PostgresAnalysisStore(object(), report, inventory=inventory)
