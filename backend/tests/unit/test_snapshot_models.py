import pytest

from smartregression.core.git.snapshots import SnapshotLimits, validate_snapshot_paths


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "/absolute",
        "C:/escape",
        "a\\b",
        ".git/config",
        "a/../b",
        "a//b",
        "a\x00b",
        "CON.txt",
        "nul",
        "a.",
        "trailing ",
        "a/COM1.log",
        "a?b",
        "a*b",
        "a|b",
    ],
)
def test_unsafe_portable_paths_reject(path):
    with pytest.raises(ValueError, match="unsafe_snapshot_path"):
        validate_snapshot_paths([path])


@pytest.mark.parametrize("paths", [["A.py", "a.py"], ["a", "A/b"], ["x", "x"]])
def test_case_aliases_and_parent_collisions_reject(paths):
    with pytest.raises(ValueError, match="snapshot_path_collision"):
        validate_snapshot_paths(paths)


def test_supported_paths_and_empty_tree():
    validate_snapshot_paths(["src/code.py", "tests/test_code.py", ".gitignore", "data/ảnh.bin"])
    validate_snapshot_paths([])


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_limits(value):
    with pytest.raises(ValueError, match="invalid_snapshot_limits"):
        SnapshotLimits(max_files=value)
