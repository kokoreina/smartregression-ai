"""Real Git acquisition verifies index provenance without executing input code."""

import subprocess
from dataclasses import replace

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.application.index_sources import acquire_index_snapshot, verify_index_sources
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.core.git.snapshots import TreeEntry, freeze_snapshot
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def acquisition(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()
    git(repo, "init", "-q", "--object-format=sha1")
    git(repo, "config", "user.name", "Index Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    content = b"raise RuntimeError('must not execute')\r\n# base\r\n"
    (repo / "code.py").write_bytes(content)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "code.py").write_bytes(content.replace(b"base", b"next"))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "target")
    target = git(repo, "rev-parse", "HEAD")
    source = LocalGit(repo)
    args = dict(
        source=source,
        authorization=RepositoryAuthorization("fixture", repo),
        repository_id="fixture",
        commit=base,
    )
    snapshot = acquire_index_snapshot(**args)
    manifest = build_index_manifest(
        snapshot,
        [ChunkInput("code.py", 1, 1, b"raise RuntimeError('must not execute')\r\n")],
        index_version="chunker/1",
        configuration_id="a" * 64,
    )
    return args, snapshot, manifest, target


def verify(args, manifest, **changes):
    return verify_index_sources(
        **(
            args
            | dict(manifest=manifest, index_version="chunker/1", configuration_id="a" * 64)
            | changes
        )
    )


def test_reacquires_exact_committed_bytes_despite_dirty_worktree(acquisition):
    args, snapshot, manifest, _ = acquisition
    (args["source"].repository / "code.py").write_bytes(b"dirty tree")
    assert verify(args, manifest) == snapshot
    assert manifest.chunks[0].line_end == 1


@pytest.mark.parametrize(
    "change",
    [
        dict(repository_id="other"),
        dict(commit="HEAD"),
        dict(commit="--help"),
        dict(commit="a" * 39),
    ],
)
def test_rejects_invalid_scope_before_source_read(acquisition, monkeypatch, change):
    args, _, manifest, _ = acquisition
    monkeypatch.setattr(
        args["source"], "snapshot_entries", lambda *_: pytest.fail("must reject before source read")
    )
    with pytest.raises(ValueError, match="unauthorized_repository|invalid_commit"):
        verify(args, manifest, **change)


def test_wrong_authorized_path_is_rejected(acquisition, tmp_path):
    args, _, manifest, _ = acquisition
    with pytest.raises(ValueError, match="unauthorized_repository"):
        verify(args, manifest, authorization=RepositoryAuthorization("fixture", tmp_path))


@pytest.mark.parametrize(
    "change", [dict(index_version="chunker/2"), dict(configuration_id="b" * 64)]
)
def test_rejects_wrong_config_or_version(acquisition, change):
    args, _, manifest, _ = acquisition
    with pytest.raises(ValueError, match="stale_index"):
        verify(args, manifest, **change)


def test_base_manifest_cannot_be_relabelled_as_target(acquisition):
    args, _, manifest, target = acquisition
    with pytest.raises(ValueError, match="stale_index"):
        verify(args, manifest, commit=target)


def test_self_consistent_forged_snapshot_is_not_acquisition_proof(acquisition):
    args, snapshot, _, _ = acquisition
    content = b"forged\n"
    import hashlib

    blob = hashlib.sha1(b"blob 7\0" + content).hexdigest()
    forged = freeze_snapshot(
        "fixture",
        snapshot.manifest.commit,
        (TreeEntry("code.py", "100644", blob, len(content)),),
        (content,),
    )
    manifest = build_index_manifest(
        forged,
        [ChunkInput("code.py", 1, 1, content)],
        index_version="chunker/1",
        configuration_id="a" * 64,
    )
    with pytest.raises(ValueError, match="stale_index"):
        verify(args, manifest)


def test_tampered_source_blob_is_rejected(acquisition, monkeypatch):
    args, _, manifest, _ = acquisition
    monkeypatch.setattr(args["source"], "read_blob", lambda *a, **k: b"tampered")
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        verify(args, manifest)


def test_unsupported_manifest_version_is_rejected(acquisition):
    args, _, manifest, _ = acquisition
    forged = object.__new__(type(manifest))
    for key, value in vars(manifest).items():
        object.__setattr__(forged, key, value)
    object.__setattr__(forged, "schema_version", "index/2")
    with pytest.raises(ValueError, match="invalid_index_schema"):
        verify(args, forged)


def test_wrong_range_digest_does_not_pass_manifest_validation(acquisition):
    args, _, manifest, _ = acquisition
    forged = object.__new__(type(manifest))
    for key, value in vars(manifest).items():
        object.__setattr__(forged, key, value)
    object.__setattr__(forged, "chunks", (replace(manifest.chunks[0], line_end=50),))
    with pytest.raises(ValueError, match="inconsistent_chunk_identity"):
        verify(args, forged)
