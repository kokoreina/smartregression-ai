import hashlib

import pytest

from smartregression.contracts.stages import (
    ImpactCandidate,
    ImpactPayload,
    SnapshotIdentity,
)
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot
from smartregression.core.retrieval.context import build_retrieval_payload
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest

REPOSITORY = "repo"
COMMIT = "a" * 40
INDEX_VERSION = "chunker/1"
CONFIGURATION = "cfg/1"


def snapshot():
    content = b"one\n two\n"
    blob = hashlib.sha1(b"blob 9\0" + content).hexdigest()
    return freeze_snapshot(
        REPOSITORY,
        COMMIT,
        (TreeEntry("src/a.py", "100644", blob, len(content)),),
        (content,),
    )


def impact_for(snapshot_value, *paths: str):
    identity = SnapshotIdentity(
        repository_id=snapshot_value.manifest.repository_id,
        commit=snapshot_value.manifest.commit,
        snapshot_id=snapshot_value.manifest.snapshot_id,
    )
    return ImpactPayload(
        snapshot=identity,
        candidates=[
            ImpactCandidate(
                id=f"candidate-{path}",
                path=path,
                relationship="changed",
                changed_component_id=f"component-{path}",
                path_ids=[],
            )
            for path in paths
        ],
        paths=[],
    )


def manifest_for(snapshot_value):
    return build_index_manifest(
        snapshot_value,
        (ChunkInput("src/a.py", 1, 1, b"one\n"),),
        index_version=INDEX_VERSION,
        configuration_id=CONFIGURATION,
    )


def test_retrieval_returns_provenance_for_relevant_candidate() -> None:
    value = snapshot()
    manifest = manifest_for(value)

    payload = build_retrieval_payload(
        value,
        manifest,
        impact_for(value, "src/a.py"),
        index_version=INDEX_VERSION,
        configuration_id=CONFIGURATION,
    )

    assert len(payload.items) == 1
    item = payload.items[0]
    assert item.path == "src/a.py"
    assert item.location.line_start == 1
    assert item.location.line_end == 1
    assert item.content_sha256 == hashlib.sha256(b"one\n").hexdigest()
    assert item.snapshot.snapshot_id == value.manifest.snapshot_id
    assert item.index_id == manifest.index_id
    assert item.configuration_id == CONFIGURATION


def test_retrieval_returns_explicit_empty_context_for_no_matching_chunks() -> None:
    value = snapshot()
    manifest = manifest_for(value)

    payload = build_retrieval_payload(
        value,
        manifest,
        impact_for(value, "src/other.py"),
        index_version=INDEX_VERSION,
        configuration_id=CONFIGURATION,
    )

    assert len(payload.sources) == 1
    assert payload.items == []


@pytest.mark.parametrize(
    ("repository_id", "commit", "snapshot_id", "error"),
    [
        ("other-repo", COMMIT, None, "retrieval_repository_mismatch"),
        (REPOSITORY, "b" * 40, None, "retrieval_commit_mismatch"),
        (REPOSITORY, COMMIT, hashlib.sha256(b"other").hexdigest(), "retrieval_snapshot_mismatch"),
    ],
)
def test_retrieval_rejects_wrong_repository_or_commit(
    repository_id: str, commit: str, snapshot_id: str | None, error: str
) -> None:
    value = snapshot()
    manifest = manifest_for(value)
    identity = SnapshotIdentity(
        repository_id=repository_id,
        commit=commit,
        snapshot_id=snapshot_id or value.manifest.snapshot_id,
    )
    impact = ImpactPayload(snapshot=identity, candidates=[], paths=[])

    with pytest.raises(ValueError, match=error):
        build_retrieval_payload(
            value,
            manifest,
            impact,
            index_version=INDEX_VERSION,
            configuration_id=CONFIGURATION,
        )


def test_retrieval_rejects_stale_index_configuration() -> None:
    value = snapshot()
    manifest = manifest_for(value)

    with pytest.raises(ValueError, match="stale_index"):
        build_retrieval_payload(
            value,
            manifest,
            impact_for(value, "src/a.py"),
            index_version=INDEX_VERSION,
            configuration_id="cfg/2",
        )


def test_retrieval_does_not_return_source_text_or_execution_metadata() -> None:
    value = snapshot()
    manifest = manifest_for(value)

    payload = build_retrieval_payload(
        value,
        manifest,
        impact_for(value, "src/a.py"),
        index_version=INDEX_VERSION,
        configuration_id=CONFIGURATION,
    )

    assert "two" not in payload.model_dump_json()
    assert "outcome" not in payload.model_dump_json()
    assert "fault" not in payload.model_dump_json()
