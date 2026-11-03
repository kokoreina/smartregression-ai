import hashlib
import json
import os
import subprocess
from dataclasses import replace

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.adapters.snapshot_store import materialize_pair, verify_snapshot
from smartregression.application.snapshots import RepositoryAuthorization, prepare_snapshots
from smartregression.cli.main import main
from smartregression.core.git.snapshots import SnapshotLimits


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def revisions(tmp_path):
    repo = tmp_path / "input"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Snapshot Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "code.py").write_bytes(b"def f():\r\n    return 1\r\n")
    (repo / "asset.bin").write_bytes(b"\x00\xff\x80")
    git(repo, "-c", "core.autocrlf=false", "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "code.py").write_bytes(b"def f():\n    return 2\n")
    (repo / "empty").write_bytes(b"")
    git(repo, "-c", "core.autocrlf=false", "add", ".")
    git(repo, "commit", "-qm", "target")
    return repo, base, git(repo, "rev-parse", "HEAD")


def prepare(revisions, **kwargs):
    repo, base, target = revisions
    return prepare_snapshots(
        LocalGit(repo),
        authorization=RepositoryAuthorization("fixture", repo),
        repository_id="fixture",
        base=base,
        target=target,
        **kwargs,
    )


def test_byte_identity_manifests_and_dirty_tree(revisions, tmp_path):
    repo, base, target = revisions
    pair = prepare(revisions)
    (repo / "code.py").write_bytes(b"dirty tree")
    assert prepare(revisions) == pair
    assert pair.base.manifest.commit == base
    assert pair.target.manifest.commit == target
    assert pair.base.manifest.snapshot_id != pair.target.manifest.snapshot_id
    output = tmp_path / "result"
    materialize_pair(pair, output, source_repository=repo)
    assert (output / "base/files/code.py").read_bytes() == b"def f():\r\n    return 1\r\n"
    assert (output / "target/files/asset.bin").read_bytes() == b"\x00\xff\x80"
    assert (output / "target/files/empty").read_bytes() == b""
    manifest = verify_snapshot(output / "target", expected=pair.target.manifest)
    assert manifest == pair.target.manifest
    assert json.loads((output / "pair.json").read_text())["schema_version"] == "snapshot-pair/1"
    for item in manifest.files:
        content = (output / "target/files" / item.path).read_bytes()
        assert item.sha256 == hashlib.sha256(content).hexdigest()
        assert item.size == len(content)
    assert (repo / "code.py").read_bytes() == b"dirty tree"


def test_authorization_before_any_git_read(revisions, tmp_path, monkeypatch):
    repo, base, target = revisions
    reader = LocalGit(repo)
    monkeypatch.setattr(reader, "snapshot_entries", lambda *_: pytest.fail("Git must not be read"))
    for auth, identity in [
        (RepositoryAuthorization("fixture", repo), "other"),
        (RepositoryAuthorization("fixture", tmp_path), "fixture"),
        (RepositoryAuthorization("", repo), ""),
    ]:
        with pytest.raises(ValueError, match="unauthorized_repository"):
            prepare_snapshots(
                reader, authorization=auth, repository_id=identity, base=base, target=target
            )


@pytest.mark.parametrize("revision", ["HEAD", "a" * 40, "--help"])
def test_invalid_commits_reject(revisions, revision):
    repo, _, target = revisions
    with pytest.raises(ValueError, match="invalid_commit"):
        prepare((repo, revision, target))


def test_blob_cannot_be_used_as_commit(revisions):
    repo, _, target = revisions
    blob = git(repo, "rev-parse", target + ":code.py")
    with pytest.raises(ValueError, match="invalid_commit"):
        prepare((repo, blob, target))


@pytest.mark.parametrize(
    "limits",
    [
        SnapshotLimits(max_files=1),
        SnapshotLimits(max_file_bytes=1),
        SnapshotLimits(max_total_bytes=1),
    ],
    ids=["file-count", "file-size", "total-size"],
)
def test_resource_limits(revisions, limits):
    with pytest.raises(ValueError, match="snapshot_limit"):
        prepare(revisions, limits=limits)


def test_reject_symlink_entry_without_executing_it(revisions):
    repo, base, _ = revisions
    blob = git(repo, "rev-parse", base + ":code.py")
    git(repo, "update-index", "--add", "--cacheinfo", "120000," + blob + ",link")
    git(repo, "commit", "-qm", "unsupported symlink")
    with pytest.raises(ValueError, match="unsupported_snapshot_entry"):
        prepare((repo, base, git(repo, "rev-parse", "HEAD")))


def test_output_must_be_fresh_and_outside_input(revisions, tmp_path):
    repo, _, _ = revisions
    pair = prepare(revisions)
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep").write_text("keep")
    with pytest.raises(ValueError, match="snapshot_destination_exists"):
        materialize_pair(pair, existing, source_repository=repo)
    assert (existing / "keep").read_text() == "keep"
    with pytest.raises(ValueError, match="snapshot_destination_inside_source"):
        materialize_pair(pair, repo / "output", source_repository=repo)


def test_verifier_rejects_changed_content_and_wrong_identity(revisions, tmp_path):
    repo, _, _ = revisions
    pair = prepare(revisions)
    output = tmp_path / "result"
    materialize_pair(pair, output, source_repository=repo)
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        verify_snapshot(
            output / "target", expected=replace(pair.target.manifest, repository_id="other")
        )
    file = output / "target/files/code.py"
    file.chmod(0o600)
    file.write_bytes(b"changed")
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        verify_snapshot(output / "target", expected=pair.target.manifest)


def test_cli_prepares_pair_and_does_not_overwrite(revisions, tmp_path, capsys):
    repo, base, target = revisions
    output = tmp_path / "cli-output"
    args = [
        "prepare-snapshots",
        "--repository",
        str(repo),
        "--repository-id",
        "fixture",
        "--authorized-root",
        str(repo),
        "--base",
        base,
        "--target",
        target,
        "--output",
        str(output),
    ]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["base"]["commit"] == base
    assert result["target"]["repository_id"] == "fixture"
    assert main(args) == 2
    captured = capsys.readouterr()
    assert not captured.out and "snapshot_destination_exists" in captured.err


def test_forged_manifest_path_is_rejected_before_any_write(revisions, tmp_path):
    repo, _, _ = revisions
    pair = prepare(revisions)
    files = pair.target.manifest.files
    forged_file = replace(files[0], path="../../../escape.bin")
    forged_manifest = replace(pair.target.manifest, files=(forged_file, *files[1:]))
    forged = replace(pair, target=replace(pair.target, manifest=forged_manifest))
    parent = tmp_path / "safe"
    parent.mkdir()
    try:
        with pytest.raises(ValueError, match="unsafe_snapshot_path"):
            materialize_pair(forged, parent / "result", source_repository=repo)
        assert not (parent / "escape.bin").exists()
        assert not (parent / "result").exists()
    finally:
        if (parent / "escape.bin").exists():
            (parent / "escape.bin").chmod(0o600)


def test_write_failure_removes_only_owned_output(revisions, tmp_path, monkeypatch):
    repo, _, _ = revisions
    pair = prepare(revisions)
    keep = tmp_path / "keep"
    keep.write_text("keep")

    def fail(*args, **kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr("smartregression.adapters.snapshot_store.verify_snapshot", fail)
    with pytest.raises(OSError, match="simulated write failure"):
        materialize_pair(pair, tmp_path / "result", source_repository=repo)
    assert not (tmp_path / "result").exists()
    assert keep.read_text() == "keep"


def test_sha256_git_and_empty_tree(tmp_path):
    repo = tmp_path / "sha256"
    repo.mkdir()
    git(repo, "init", "-q", "--object-format=sha256")
    git(repo, "config", "user.name", "Snapshot Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "commit", "--allow-empty", "-qm", "empty")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "file").write_bytes(b"content\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "file")
    pair = prepare((repo, base, git(repo, "rev-parse", "HEAD")))
    assert len(pair.target.manifest.commit) == 64
    assert len(pair.target.manifest.files[0].blob_id) == 64
    assert pair.base.manifest.files == ()
    materialize_pair(pair, tmp_path / "result", source_repository=repo)
    assert verify_snapshot(tmp_path / "result/base", expected=pair.base.manifest)


def test_git_read_environment_blocks_lazy_fetch_and_redirects(revisions, monkeypatch):
    from smartregression.adapters import git_local

    original = git_local.bounded_command
    monkeypatch.setenv("GIT_NO_LAZY_FETCH", "0")
    monkeypatch.setenv("GIT_DIR", "untrusted-redirect")

    def checked(args, **kwargs):
        assert "--no-lazy-fetch" in args
        assert kwargs["env"]["GIT_NO_LAZY_FETCH"] == "1"
        assert "GIT_DIR" not in kwargs["env"]
        return original(args, **kwargs)

    monkeypatch.setattr(git_local, "bounded_command", checked)
    assert prepare(revisions).base.manifest.files


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO support required")
def test_verifier_rejects_extra_special_file(revisions, tmp_path):
    repo, _, _ = revisions
    pair = prepare(revisions)
    output = tmp_path / "result"
    materialize_pair(pair, output, source_repository=repo)
    os.mkfifo(output / "target/files/extra-pipe")
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        verify_snapshot(output / "target", expected=pair.target.manifest)


def test_partial_clone_does_not_fetch_missing_blobs(revisions, tmp_path):
    source, _, target = revisions
    git(source, "config", "uploadpack.allowFilter", "true")
    partial = tmp_path / "partial"
    subprocess.run(
        [
            "git",
            "clone",
            "-q",
            "--no-checkout",
            "--filter=blob:none",
            source.as_uri(),
            str(partial),
        ],
        check=True,
        capture_output=True,
    )
    blob = git(source, "rev-parse", target + ":asset.bin")
    missing_before = git(partial, "rev-list", "--objects", "--missing=print", target)
    assert "?" + blob in missing_before
    packs_before = tuple((partial / ".git/objects/pack").glob("*.pack"))
    with pytest.raises(ValueError):
        prepare((partial, target, target))
    assert tuple((partial / ".git/objects/pack").glob("*.pack")) == packs_before
    assert git(partial, "rev-list", "--objects", "--missing=print", target) == missing_before
