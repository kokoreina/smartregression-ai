"""Unit tests for deterministic context ranking, deduplication, and validation (Task 2.12)."""

import hashlib

import pytest

from smartregression.contracts.stages import (
    ChangePayload,
    FileCoverage,
    ImpactCandidate,
    ImpactPath,
    ImpactPayload,
    RetrievalItem,
    RetrievalPayload,
    RetrievalSource,
    SnapshotIdentity,
    SourceLocation,
    StageComponent,
    StageResult,
)
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot
from smartregression.core.retrieval.context import build_retrieval_payload
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest
from smartregression.core.retrieval.ranked_context import (
    RULE_VERSION,
    ContextProvenance,
    ValidatedContextItem,
    ValidatedContextResult,
    rank_and_validate_context,
    validate_retrieval_stage,
)

REPOSITORY = "test-repo"
COMMIT = "a" * 40
INDEX_VERSION = "chunker/1"
CONFIG_1 = "cfg/1"
CONFIG_2 = "cfg/2"


@pytest.fixture
def sample_snapshot():
    content_a = b"def alpha():\n    return 1\n"
    content_b = b"def beta():\n    return 2\n"
    blob_a = hashlib.sha1(b"blob 26\0" + content_a).hexdigest()
    blob_b = hashlib.sha1(b"blob 25\0" + content_b).hexdigest()

    return freeze_snapshot(
        REPOSITORY,
        COMMIT,
        (
            TreeEntry("src/a.py", "100644", blob_a, len(content_a)),
            TreeEntry("src/b.py", "100644", blob_b, len(content_b)),
        ),
        (content_a, content_b),
    )


@pytest.fixture
def snapshot_identity(sample_snapshot):
    return SnapshotIdentity(
        repository_id=sample_snapshot.manifest.repository_id,
        commit=sample_snapshot.manifest.commit,
        snapshot_id=sample_snapshot.manifest.snapshot_id,
    )


@pytest.fixture
def manifest(sample_snapshot):
    return build_index_manifest(
        sample_snapshot,
        (
            ChunkInput("src/a.py", 1, 1, b"def alpha():\n"),
            ChunkInput("src/a.py", 2, 2, b"    return 1\n"),
            ChunkInput("src/b.py", 1, 1, b"def beta():\n"),
            ChunkInput("src/b.py", 2, 2, b"    return 2\n"),
        ),
        index_version=INDEX_VERSION,
        configuration_id=CONFIG_1,
    )


def test_happy_path_single_payload_ranked_and_validated(
    sample_snapshot, snapshot_identity, manifest
) -> None:
    impact = ImpactPayload(
        snapshot=snapshot_identity,
        candidates=[
            ImpactCandidate(
                id="c1",
                path="src/a.py",
                relationship="changed",
                changed_component_id="comp1",
                path_ids=[],
            )
        ],
        paths=[],
    )

    raw_payload = build_retrieval_payload(
        sample_snapshot,
        manifest,
        impact,
        index_version=INDEX_VERSION,
        configuration_id=CONFIG_1,
    )

    result = rank_and_validate_context(sample_snapshot, raw_payload, impact=impact)

    assert isinstance(result, ValidatedContextResult)
    assert result.status == "completed"
    assert result.limitations == ()
    assert result.rule_version == RULE_VERSION
    assert len(result.items) == 2

    # Check rank sequential numbering 1..N
    assert [item.rank for item in result.items] == [1, 2]
    assert [item.rank for item in result.payload.items] == [1, 2]

    # Check item metadata
    first = result.items[0]
    assert isinstance(first, ValidatedContextItem)
    assert first.path == "src/a.py"
    assert first.tier == 1
    assert len(first.provenance) == 1
    assert isinstance(first.provenance[0], ContextProvenance)
    assert first.provenance[0].original_rank == 1

    # StageResult conversion
    stage_res = result.to_stage_result()
    assert isinstance(stage_res, StageResult)
    assert stage_res.status == "completed"
    assert stage_res.data == result.payload
    assert stage_res.limitations == []


def test_ranking_priority_tiers(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    # Chunks for a.py (line 1), b.py (line 1)
    chunk_a = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-a",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=hashlib.sha256(b"def alpha():\n").hexdigest(),
        rank=1,
    )
    chunk_b = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-b",
        path="src/b.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=hashlib.sha256(b"def beta():\n").hexdigest(),
        rank=2,
    )

    # Put chunk_b first in raw payload
    raw_payload = RetrievalPayload(sources=[source], items=[chunk_b, chunk_a])

    # Mark src/a.py as changed (Tier 1) and src/b.py as direct dependent (Tier 2)
    impact = ImpactPayload(
        snapshot=snapshot_identity,
        candidates=[
            ImpactCandidate(
                id="c-a",
                path="src/a.py",
                relationship="changed",
                changed_component_id="comp-a",
                path_ids=[],
            ),
            ImpactCandidate(
                id="c-b",
                path="src/b.py",
                relationship="direct",
                changed_component_id="comp-a",
                path_ids=["p1"],
            ),
        ],
        paths=[ImpactPath(id="p1", changed_component_id="comp-a", nodes=["src/b.py", "src/a.py"])],
    )

    result = rank_and_validate_context(sample_snapshot, raw_payload, impact=impact)

    assert result.status == "completed"
    # Even though chunk_b came first in payload, chunk_a must rank #1 because it is Tier 1
    assert result.items[0].path == "src/a.py"
    assert result.items[0].tier == 1
    assert result.items[0].rank == 1

    assert result.items[1].path == "src/b.py"
    assert result.items[1].tier == 2
    assert result.items[1].rank == 2


def test_ranking_tie_breaks_scores_and_positions(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    # Two chunks in src/a.py (lines 1 and 2)
    chunk_1 = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-line1",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=hashlib.sha256(b"def alpha():\n").hexdigest(),
        rank=10,
        score=0.75,
    )
    chunk_2 = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-line2",
        path="src/a.py",
        location=SourceLocation(line_start=2, line_end=2),
        content_sha256=hashlib.sha256(b"    return 1\n").hexdigest(),
        rank=20,
        score=0.95,  # higher score
    )

    raw_payload = RetrievalPayload(sources=[source], items=[chunk_1, chunk_2])

    result = rank_and_validate_context(sample_snapshot, raw_payload)

    # chunk_2 should be ranked #1 because score 0.95 > 0.75
    assert result.items[0].id == "item-line2"
    assert result.items[0].rank == 1
    assert result.items[1].id == "item-line1"
    assert result.items[1].rank == 2


def test_deduplication_preserves_provenance(sample_snapshot, snapshot_identity) -> None:
    src_1 = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    src_2 = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-2",
        configuration_id=CONFIG_2,
    )

    sha = hashlib.sha256(b"def alpha():\n").hexdigest()

    item_src1 = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-from-src1",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha,
        rank=5,
        score=0.80,
    )
    item_src2 = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-2",
        configuration_id=CONFIG_2,
        id="item-from-src2",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha,
        rank=2,
        score=0.92,
    )

    payload = RetrievalPayload(sources=[src_1, src_2], items=[item_src1, item_src2])

    result = rank_and_validate_context(sample_snapshot, payload)

    assert result.status == "completed"
    # Deduplicated into exactly 1 item
    assert len(result.items) == 1
    assert len(result.payload.items) == 1

    item = result.items[0]
    assert item.path == "src/a.py"
    assert item.rank == 1
    assert item.score == 0.92  # Best score preserved

    # Full provenance preserved
    assert len(item.provenance) == 2
    prov_sources = {p.source.configuration_id for p in item.provenance}
    assert prov_sources == {CONFIG_1, CONFIG_2}
    prov_ranks = {p.original_rank for p in item.provenance}
    assert prov_ranks == {2, 5}

    # Payload retains both sources
    assert len(result.payload.sources) == 2


def test_deduplication_across_multiple_payloads(sample_snapshot, snapshot_identity) -> None:
    src_1 = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    src_2 = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-2",
        configuration_id=CONFIG_2,
    )

    sha_a = hashlib.sha256(b"def alpha():\n").hexdigest()
    sha_b = hashlib.sha256(b"def beta():\n").hexdigest()

    # Payload 1 has chunk A and chunk B
    p1 = RetrievalPayload(
        sources=[src_1],
        items=[
            RetrievalItem(
                snapshot=snapshot_identity,
                index_id="idx-1",
                configuration_id=CONFIG_1,
                id="p1-a",
                path="src/a.py",
                location=SourceLocation(line_start=1, line_end=1),
                content_sha256=sha_a,
                rank=1,
            ),
            RetrievalItem(
                snapshot=snapshot_identity,
                index_id="idx-1",
                configuration_id=CONFIG_1,
                id="p1-b",
                path="src/b.py",
                location=SourceLocation(line_start=1, line_end=1),
                content_sha256=sha_b,
                rank=2,
            ),
        ],
    )

    # Payload 2 also has chunk A (duplicate)
    p2 = RetrievalPayload(
        sources=[src_2],
        items=[
            RetrievalItem(
                snapshot=snapshot_identity,
                index_id="idx-2",
                configuration_id=CONFIG_2,
                id="p2-a",
                path="src/a.py",
                location=SourceLocation(line_start=1, line_end=1),
                content_sha256=sha_a,
                rank=1,
            ),
        ],
    )

    result = rank_and_validate_context(sample_snapshot, [p1, p2])

    assert result.status == "completed"
    assert len(result.items) == 2  # A and B
    assert [it.rank for it in result.items] == [1, 2]
    # Chunk A should have 2 provenance records
    chunk_a = next(it for it in result.items if it.path == "src/a.py")
    assert len(chunk_a.provenance) == 2


def test_empty_retrieval_payload_valid(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    empty_payload = RetrievalPayload(sources=[source], items=[])

    result = rank_and_validate_context(sample_snapshot, empty_payload)

    assert result.status == "completed"
    assert result.items == ()
    assert result.payload.items == []
    assert len(result.payload.sources) == 1
    assert result.limitations == ()

    stage_res = result.to_stage_result()
    assert stage_res.status == "completed"
    assert stage_res.data == result.payload


def test_content_hash_mismatch_strict_and_partial(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    bad_item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="bad-hash-item",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256="0" * 64,  # Incorrect hash
        rank=1,
    )
    payload = RetrievalPayload(sources=[source], items=[bad_item])

    # Strict mode rejects
    with pytest.raises(ValueError, match="chunk_content_mismatch"):
        rank_and_validate_context(sample_snapshot, payload, strict=True)

    # Non-strict mode exposes partial
    result = rank_and_validate_context(sample_snapshot, payload, strict=False)
    assert result.status == "partial"
    assert result.items == ()
    assert len(result.limitations) == 1
    assert result.limitations[0].code == "chunk_content_mismatch"
    assert result.limitations[0].path == "src/a.py"

    stage_res = result.to_stage_result()
    assert stage_res.status == "partial"
    assert len(stage_res.limitations) == 1


def test_unknown_snapshot_path_strict_and_partial(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    unknown_path_item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="unknown-item",
        path="src/nonexistent.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256="a" * 64,
        rank=1,
    )
    payload = RetrievalPayload(sources=[source], items=[unknown_path_item])

    with pytest.raises(ValueError, match="unknown_snapshot_path"):
        rank_and_validate_context(sample_snapshot, payload, strict=True)

    result = rank_and_validate_context(sample_snapshot, payload, strict=False)
    assert result.status == "partial"
    assert result.items == ()
    assert result.limitations[0].code == "unknown_snapshot_path"
    assert result.limitations[0].path == "src/nonexistent.py"


def test_invalid_source_range_strict_and_partial(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    # src/a.py only has 2 lines; line 10 is out of bounds
    out_of_bounds_item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="oob-item",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=10),
        content_sha256="b" * 64,
        rank=1,
    )
    payload = RetrievalPayload(sources=[source], items=[out_of_bounds_item])

    with pytest.raises(ValueError, match="invalid_source_range"):
        rank_and_validate_context(sample_snapshot, payload, strict=True)

    result = rank_and_validate_context(sample_snapshot, payload, strict=False)
    assert result.status == "partial"
    assert result.items == ()
    assert result.limitations[0].code == "invalid_source_range"
    assert result.limitations[0].path == "src/a.py"


@pytest.mark.parametrize(
    ("repo_id", "commit_id", "snap_id", "error_code"),
    [
        ("wrong-repo", COMMIT, None, "retrieval_repository_mismatch"),
        (REPOSITORY, "b" * 40, None, "retrieval_commit_mismatch"),
        (REPOSITORY, COMMIT, "c" * 64, "retrieval_snapshot_mismatch"),
    ],
)
def test_identity_mismatch_fails_closed(
    sample_snapshot, repo_id, commit_id, snap_id, error_code
) -> None:
    foreign_identity = SnapshotIdentity(
        repository_id=repo_id,
        commit=commit_id,
        snapshot_id=snap_id or sample_snapshot.manifest.snapshot_id,
    )
    source = RetrievalSource(
        snapshot=foreign_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    payload = RetrievalPayload(sources=[source], items=[])

    with pytest.raises(ValueError, match=error_code):
        rank_and_validate_context(sample_snapshot, payload)


def test_partial_stage_with_mixed_valid_and_invalid_items(
    sample_snapshot, snapshot_identity
) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )

    valid_sha = hashlib.sha256(b"def alpha():\n").hexdigest()

    valid_item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-valid",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=valid_sha,
        rank=1,
    )
    corrupted_item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-corrupt",
        path="src/b.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256="f" * 64,  # wrong hash
        rank=2,
    )

    payload = RetrievalPayload(sources=[source], items=[valid_item, corrupted_item])

    result = rank_and_validate_context(sample_snapshot, payload, strict=False)

    assert result.status == "partial"
    assert len(result.items) == 1
    assert result.items[0].id == "item-valid"
    assert result.items[0].rank == 1

    assert len(result.limitations) == 1
    assert result.limitations[0].code == "chunk_content_mismatch"
    assert result.limitations[0].path == "src/b.py"

    stage_result = result.to_stage_result()
    assert stage_result.status == "partial"
    assert len(stage_result.limitations) == 1
    assert stage_result.data == result.payload


def test_validate_retrieval_stage_helper(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    sha = hashlib.sha256(b"def alpha():\n").hexdigest()
    item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-1",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha,
        rank=1,
    )
    payload = RetrievalPayload(sources=[source], items=[item])

    stage_res = validate_retrieval_stage(sample_snapshot, payload)

    assert isinstance(stage_res, StageResult)
    assert stage_res.status == "completed"
    assert len(stage_res.data.items) == 1


def test_integration_with_change_payload(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    sha_a = hashlib.sha256(b"def alpha():\n").hexdigest()
    sha_b = hashlib.sha256(b"def beta():\n").hexdigest()

    item_a = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-a",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha_a,
        rank=10,
    )
    item_b = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-b",
        path="src/b.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha_b,
        rank=1,
    )

    # In payload, item_b has rank 1, item_a has rank 10
    payload = RetrievalPayload(sources=[source], items=[item_b, item_a])

    # Pass ChangePayload where src/a.py was modified
    changes = ChangePayload(
        components=[
            StageComponent(
                id="c1",
                path="src/a.py",
                kind="file",
                change="modified",
                reason="edited",
            )
        ],
        files=[FileCoverage(path="src/a.py", status="completed", limitations=[])],
    )

    result = rank_and_validate_context(sample_snapshot, payload, changes=changes)

    # Since src/a.py was modified, it gets Tier 1 and ranks first!
    assert result.items[0].path == "src/a.py"
    assert result.items[0].tier == 1
    assert result.items[0].rank == 1

    assert result.items[1].path == "src/b.py"
    assert result.items[1].tier == 4  # Unchanged
    assert result.items[1].rank == 2


def test_no_execution_or_outcome_leakage(sample_snapshot, snapshot_identity) -> None:
    source = RetrievalSource(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
    )
    sha = hashlib.sha256(b"def alpha():\n").hexdigest()
    item = RetrievalItem(
        snapshot=snapshot_identity,
        index_id="idx-1",
        configuration_id=CONFIG_1,
        id="item-clean",
        path="src/a.py",
        location=SourceLocation(line_start=1, line_end=1),
        content_sha256=sha,
        rank=1,
    )
    payload = RetrievalPayload(sources=[source], items=[item])

    result = rank_and_validate_context(sample_snapshot, payload)
    dumped = result.payload.model_dump_json()

    assert "outcome" not in dumped
    assert "fault" not in dumped
    assert "failure" not in dumped
    assert "test_pass" not in dumped
