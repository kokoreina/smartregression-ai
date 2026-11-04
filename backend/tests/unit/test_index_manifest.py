import hashlib
from dataclasses import replace

import pytest

from smartregression.core.git.snapshots import (
    FrozenSnapshot,
    TreeEntry,
    freeze_snapshot,
)
from smartregression.core.retrieval.index_manifest import (
    ChunkInput,
    ChunkManifest,
    IndexBuild,
    IndexManifest,
    _new_index_build,
    build_index_manifest,
    canonical_manifest_bytes,
    start_index_build,
    validate_index_manifest,
)


def snapshot():
    content = b"one\n two\nthree\n"
    blob = hashlib.sha1(b"blob 15\0" + content).hexdigest()
    return freeze_snapshot(
        "repo",
        "a" * 40,
        (TreeEntry("src/a.py", "100644", blob, len(content)),),
        (content,),
    )


def chunk(content=b"one\n"):
    return ChunkInput("src/a.py", 1, 1, content)


def build(
    snapshot_value=None,
    chunks=None,
    *,
    index_version="chunker/1",
    configuration_id="cfg/1",
):
    snapshot_value = snapshot_value or snapshot()
    chunks = (chunk(),) if chunks is None else chunks
    return build_index_manifest(
        snapshot_value,
        chunks,
        index_version=index_version,
        configuration_id=configuration_id,
    )


def test_manifest_and_chunk_ids_are_deterministic_and_serialized_canonically():
    first = build()
    second = build()

    assert first == second
    assert first.chunks[0].content_sha256 == hashlib.sha256(b"one\n").hexdigest()
    assert canonical_manifest_bytes(first).endswith(b"\n")


def test_manifest_rejects_snapshot_ranges_and_content_mismatches():
    with pytest.raises(ValueError, match="invalid_source_range"):
        build(
            snapshot(),
            (ChunkInput("src/a.py", 1, 4, b"one\n"),),
        )
    with pytest.raises(ValueError, match="chunk_content_mismatch"):
        build(
            snapshot(),
            (ChunkInput("src/a.py", 1, 1, b"changed\n"),),
        )


def test_manifest_rejects_stale_snapshot_and_config():
    manifest = build()
    with pytest.raises(ValueError, match="stale_index"):
        validate_index_manifest(
            snapshot(),
            manifest,
            index_version="chunker/2",
            configuration_id="cfg/1",
        )


def test_index_build_cannot_publish_incomplete_or_failed_build():
    index_build = start_index_build(
        snapshot(),
        index_version="chunker/1",
        configuration_id="cfg/1",
        expected_chunks=2,
    ).add_chunk(chunk())
    with pytest.raises(ValueError, match="trusted_snapshot_acquisition_required"):
        index_build.ready()
    failed = index_build.fail("chunking_failed")
    with pytest.raises(ValueError, match="invalid_index_transition"):
        failed.ready()
    with pytest.raises(ValueError, match="index_not_ready"):
        _ = index_build.manifest


def test_index_build_ready_transition_fails_closed_without_trusted_acquisition():
    index_build = start_index_build(
        snapshot(),
        index_version="chunker/1",
        configuration_id="cfg/1",
        expected_chunks=1,
    ).add_chunk(chunk())

    with pytest.raises(ValueError, match="trusted_snapshot_acquisition_required"):
        index_build.ready()


def test_index_build_cannot_accept_snapshot_as_ready_evidence():
    index_build = start_index_build(
        snapshot(),
        index_version="chunker/1",
        configuration_id="cfg/1",
    ).add_chunk(chunk())
    with pytest.raises(ValueError, match="trusted_snapshot_acquisition_required"):
        index_build.ready()


def test_duplicate_chunk_identity_is_rejected():
    with pytest.raises(ValueError, match="duplicate_chunk_identity"):
        build(
            snapshot(),
            (chunk(), chunk()),
        )


@pytest.mark.parametrize(
    "snapshot_value",
    [
        lambda: FrozenSnapshot(
            replace(snapshot().manifest, repository_id="other"), snapshot().contents
        ),
        lambda: FrozenSnapshot(replace(snapshot().manifest, commit="b" * 40), snapshot().contents),
        lambda: FrozenSnapshot(
            replace(
                snapshot().manifest,
                files=(replace(snapshot().manifest.files[0], sha256="f" * 64),),
            ),
            snapshot().contents,
        ),
        lambda: FrozenSnapshot(snapshot().manifest, (b"other\n",)),
    ],
)
def test_index_requires_an_internally_consistent_snapshot(snapshot_value):
    value = snapshot_value()
    with pytest.raises(ValueError):
        build(value)


def test_internal_consistency_accepts_a_valid_snapshot():
    value = snapshot()
    assert build(value).snapshot_id == value.manifest.snapshot_id


def test_caller_supplied_manifest_is_not_a_trust_boundary():
    value = snapshot()
    with pytest.raises(TypeError):
        build_index_manifest(
            value,
            (chunk(),),
            index_version="chunker/1",
            configuration_id="cfg/1",
            trusted_manifest=value.manifest,
        )


def test_ready_publication_fails_closed_without_acquisition_evidence():
    build_state = start_index_build(
        snapshot(),
        index_version="chunker/1",
        configuration_id="cfg/1",
        expected_chunks=1,
    ).add_chunk(chunk())
    with pytest.raises(ValueError, match="trusted_snapshot_acquisition_required"):
        build_state.ready()


def test_index_build_constructor_cannot_bypass_lifecycle():
    with pytest.raises(TypeError):
        IndexBuild("ready", "repo", "a" * 40, "f" * 64, "chunker/1", "cfg/1", 0)


def test_private_index_build_factory_cannot_construct_ready_state():
    with pytest.raises(ValueError, match="invalid_index_state"):
        _new_index_build(
            state="ready",
            repository_id="repo",
            commit="a" * 40,
            snapshot_id="f" * 64,
            index_version="chunker/1",
            configuration_id="cfg/1",
            expected_chunks=0,
            chunks=(),
            error_code=None,
            manifest=None,
        )


def test_index_build_rejects_inconsistent_snapshot_at_start():
    value = snapshot()
    forged = FrozenSnapshot(replace(value.manifest, commit="b" * 40), value.contents)
    with pytest.raises(ValueError):
        start_index_build(
            forged,
            index_version="chunker/1",
            configuration_id="cfg/1",
        )


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"one\n two\n", b"one\n"),
        (b"one\r\n two\r\n", b"one\r\n"),
        (b"one\r two", b"one\r"),
        (b"one\n two", b"one\n"),
        (b"\xc3\xa9\n", b"\xc3\xa9\n"),
        (b"\x00\x0cone\n", b"\x00\x0cone\n"),
    ],
)
def test_line_ranges_use_cr_lf_boundaries_and_preserve_exact_bytes(content, expected):
    blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    value = freeze_snapshot(
        "repo",
        "a" * 40,
        (TreeEntry("src/a.py", "100644", blob, len(content)),),
        (content,),
    )
    assert build(value, (ChunkInput("src/a.py", 1, 1, expected),))


def test_empty_file_has_no_valid_source_range():
    content = b""
    blob = hashlib.sha1(b"blob 0\0").hexdigest()
    value = freeze_snapshot(
        "repo",
        "a" * 40,
        (TreeEntry("empty.py", "100644", blob, 0),),
        (content,),
    )
    with pytest.raises(ValueError, match="invalid_source_range"):
        build(value, (ChunkInput("empty.py", 1, 1, b""),))


def test_manifest_objects_validate_identity_and_serialization():
    with pytest.raises(ValueError, match="invalid_repository_identity"):
        ChunkManifest("f" * 64, "", "a" * 40, "f" * 64, "a.py", 1, 1, "f" * 64)
    with pytest.raises(ValueError, match="invalid_repository_identity"):
        ChunkManifest("f" * 64, " ", "a" * 40, "f" * 64, "a.py", 1, 1, "f" * 64)
    with pytest.raises(ValueError, match="invalid_content_hash"):
        ChunkManifest("f" * 64, "repo", "a" * 40, "f" * 64, "a.py", 1, 1, "bad")
    with pytest.raises(ValueError, match="invalid_index_identity"):
        IndexManifest("bad", "repo", "a" * 40, "f" * 64, "chunker/1", "cfg/1", ())
    with pytest.raises(ValueError, match="invalid_chunk_manifest"):
        IndexManifest("f" * 64, "repo", "a" * 40, "f" * 64, "chunker/1", "cfg/1", ("chunk",))
    with pytest.raises(ValueError, match="invalid_index_manifest"):
        canonical_manifest_bytes(object())


def test_build_rejects_non_chunk_inputs_at_the_manifest_boundary():
    with pytest.raises(ValueError, match="invalid_chunk_manifest"):
        build(snapshot(), (object(),))
