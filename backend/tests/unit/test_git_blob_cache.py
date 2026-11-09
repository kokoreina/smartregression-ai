"""Bounded command-local immutable object reuse, with hash and caller-size guards."""

import hashlib

import pytest

from smartregression.adapters.git_local import LocalGit


def reader(tmp_path, monkeypatch, *, cap=64, content=b"value = 1\n", observed=None):
    source = LocalGit(tmp_path, cache_bytes=cap)
    oid = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    reads = []

    def git(*args):
        assert args[-1] == oid
        if args[1] == "-s":
            return str(len(content)).encode()
        reads.append(oid)
        return content if observed is None else observed

    monkeypatch.setattr(source, "_git", git)
    return source, oid, reads


def test_repeated_verified_object_avoids_repeated_git_processes(tmp_path, monkeypatch):
    source, oid, reads = reader(tmp_path, monkeypatch)
    assert source.read_blob(oid, max_bytes=64) == b"value = 1\n"
    assert source.read_blob(oid, max_bytes=64) == b"value = 1\n"
    assert len(reads) == 1
    # A cache hit is not permission to exceed a different caller's bound.
    with pytest.raises(ValueError, match="snapshot_limit"):
        source.read_blob(oid, max_bytes=1)


def test_cache_cap_does_not_become_unbounded_retention(tmp_path, monkeypatch):
    source, oid, reads = reader(tmp_path, monkeypatch, cap=1)
    assert source.read_blob(oid, max_bytes=64) == source.read_blob(oid, max_bytes=64)
    assert len(reads) == 2


def test_wrong_blob_bytes_are_never_cached_as_the_requested_identity(tmp_path, monkeypatch):
    source, oid, reads = reader(tmp_path, monkeypatch, observed=b"forged data")
    for _ in range(2):
        with pytest.raises(ValueError, match="snapshot_mismatch"):
            source.read_blob(oid, max_bytes=64)
    assert len(reads) == 2


@pytest.mark.parametrize("cap", [-1, True, "64", 64 * 1024 * 1024 + 1])
def test_invalid_cache_configuration_is_rejected(tmp_path, cap):
    with pytest.raises(ValueError, match="invalid_blob_cache_limit"):
        LocalGit(tmp_path, cache_bytes=cap)
