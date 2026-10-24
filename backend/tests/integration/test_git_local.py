import subprocess
from pathlib import Path

import pytest

from smartregression.adapters.git_local import LocalGit


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def test_immutable_diff_and_reads_preserve_worktree(tmp_path):
    repo = tmp_path / "fixture"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    for name in ["modify.py", "delete.py", "old.py"]:
        (repo / name).write_text("def stable():\n    return 1\n", encoding="utf-8")
    (repo / "old.py").write_text('def renamed():\n    return "unique renamed source"\n')
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "modify.py").write_text("def stable():\n    return 2\n", encoding="utf-8")
    (repo / "delete.py").unlink()
    (repo / "old.py").rename(repo / "new.py")
    (repo / "added.py").write_text("answer = 42\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "target")
    target = git(repo, "rev-parse", "HEAD")
    reader = LocalGit(repo)
    changes = reader.diff(base, target)
    actual = {(x.path, x.change, x.previous_path) for x in changes}
    assert actual == {
        ("modify.py", "modified", None),
        ("delete.py", "deleted", None),
        ("new.py", "renamed", "old.py"),
        ("added.py", "added", None),
    }
    (repo / "modify.py").write_text("dirty worktree", encoding="utf-8")
    assert reader.read_text(base, "modify.py").endswith("return 1\n")
    assert reader.read_text(target, "modify.py").endswith("return 2\n")
    assert reader.read_text(base, "delete.py").endswith("return 1\n")
    with pytest.raises(ValueError, match="missing_snapshot_path"):
        reader.read_text(target, "delete.py")
    assert (repo / "modify.py").read_text() == "dirty worktree"
    assert reader.diff(target, target) == []
    for revision in ["HEAD", "--help", "a" * 40]:
        with pytest.raises(ValueError):
            reader.diff(revision, target)
    for path in ["../secret", "/absolute", "modify.py:evil", " file.py"]:
        with pytest.raises(ValueError):
            reader.read_text(target, path)


def test_blob_sha_is_not_a_commit(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "blob").write_text("data")
    blob = git(tmp_path, "hash-object", "-w", "blob")
    with pytest.raises(ValueError, match="invalid_commit"):
        LocalGit(tmp_path).diff(blob, blob)


def test_binary_and_symlink_modes_fail_closed(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "commit", "--allow-empty", "-qm", "empty base")
    base = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "binary").write_bytes(b"hello\0binary")
    git(tmp_path, "add", "binary")
    oid = git(tmp_path, "hash-object", "-w", "binary")
    git(tmp_path, "update-index", "--add", "--cacheinfo", "120000," + oid + ",link")
    git(tmp_path, "commit", "-qm", "unsupported modes")
    target = git(tmp_path, "rev-parse", "HEAD")
    reader = LocalGit(tmp_path)
    with pytest.raises(ValueError, match="unsupported_file_mode"):
        reader.diff(base, target)
    with pytest.raises(ValueError, match="binary_source"):
        reader.read_text(target, "binary")
