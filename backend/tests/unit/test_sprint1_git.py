import os
import shutil
import stat
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from smartregression.adapters.git.local import GitError, LocalGitRepository
from smartregression.core.git.changes import parse_name_status
from smartregression.core.impact.python_structure import analyze_python


@pytest.fixture
def history():
    root = Path("var/git-spike-tests").resolve()
    root.mkdir(parents=True, exist_ok=True)
    repo = root / uuid4().hex
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Sprint fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "core.autocrlf", "false")
    for name, content in {
        "modify.py": "value = 1\n",
        "delete.py": "gone = True\n",
        "old name.py": "def stable():\n    return 42\n",
    }.items():
        (repo / name).write_text(content, encoding="utf-8", newline="\n")
    git("add", ".")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (repo / "modify.py").write_text("value = 2\n", encoding="utf-8", newline="\n")
    (repo / "delete.py").unlink()
    (repo / "old name.py").rename(repo / "new name.py")
    (repo / "added.py").write_text("new = True\n", encoding="utf-8", newline="\n")
    git("add", "-A")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "target")
    target = git("rev-parse", "HEAD")
    try:
        yield repo, base, target, git
    finally:
        if repo.parent == root:

            def remove_readonly(function, path, error):
                if not Path(path).resolve().is_relative_to(repo):
                    raise error
                os.chmod(path, stat.S_IWRITE)
                function(path)

            shutil.rmtree(repo, onexc=remove_readonly)


def test_real_git_diff_uses_commits_and_preserves_input_worktree(history):
    repo, base, target, git = history
    (repo / "modify.py").write_text("dirty local change\n", encoding="utf-8")
    before = git("status", "--porcelain")
    changes = LocalGitRepository(repo).diff(base, target, rename_threshold=50)
    actual = {c.path: (c.change, c.previous_path) for c in changes}
    assert actual == {
        "added.py": ("added", None),
        "delete.py": ("deleted", None),
        "modify.py": ("modified", None),
        "new name.py": ("renamed", "old name.py"),
    }
    assert LocalGitRepository(repo).read_text(base, "delete.py") == "gone = True\n"
    assert git("status", "--porcelain") == before
    assert (repo / "modify.py").read_text() == "dirty local change\n"


def test_empty_diff_and_frozen_ref_remain_bound_to_old_commit(history):
    repo, base, target, git = history
    adapter = LocalGitRepository(repo)
    frozen = adapter.resolve("HEAD")
    git("update-ref", "refs/heads/moved", base)
    assert adapter.diff(target, target, rename_threshold=50) == ()
    assert frozen == target
    assert adapter.resolve("moved") == base
    assert adapter.resolve("HEAD") == frozen


@pytest.mark.parametrize("value", ["", "HEAD", "--help", "a" * 39, "A" * 40, "0" * 40])
def test_diff_rejects_invalid_or_missing_commit(history, value):
    repo, _, target, _ = history
    with pytest.raises(GitError):
        LocalGitRepository(repo).diff(value, target, rename_threshold=50)


def test_blob_id_is_not_a_commit(history):
    repo, _, target, git = history
    blob = git("rev-parse", "HEAD:modify.py")
    with pytest.raises(GitError, match="not_commit"):
        LocalGitRepository(repo).diff(blob, target, rename_threshold=50)


@pytest.mark.parametrize(
    "raw",
    [
        b"T\0file.py\0",
        b"M\0../escape.py\0",
        b"A\0 padded.py\0",
        b"R100\0only-one\0",
        b"M\0bad\xff.py\0",
    ],
)
def test_unsupported_and_malformed_paths_are_not_silently_dropped(raw):
    with pytest.raises(ValueError):
        parse_name_status(raw)


def test_parser_preserves_unicode_and_internal_spaces():
    changes = parse_name_status("A\0tests/tên file.py\0".encode())
    assert changes[0].path == "tests/tên file.py"


def test_ast_analysis_never_executes_source_and_reports_uncertainty():
    source = (
        "import os\nfrom library import value\nclass A:\n"
        ' def method(self):\n  return value()\nos.system("must not run")\n'
    )
    result = analyze_python(source, "module.py")
    assert {s.name for s in result.symbols} == {"A", "A.method"}
    assert result.imports == ("library", "os")
    assert set(result.calls) == {"os.system", "value"}
    assert result.limitations
    assert result.symbols[1].line_start == 4


def test_ast_syntax_error_is_explicit_partial_result():
    result = analyze_python("def broken(", "broken.py")
    assert result.symbols == ()
    assert result.limitations == ("syntax_error",)


def test_rename_score_outside_git_range_is_rejected():
    with pytest.raises(ValueError):
        parse_name_status(b"R101\0old.py\0new.py\0")


def test_branch_tag_ambiguity_and_merge_base_are_explicit(history):
    repo, base, target, git = history
    git("branch", "ambiguous", base)
    git("tag", "ambiguous", target)
    adapter = LocalGitRepository(repo)
    with pytest.raises(GitError, match="missing_or_ambiguous_ref"):
        adapter.resolve("ambiguous")
    assert adapter.resolve("refs/heads/ambiguous") == base
    assert adapter.merge_base(base, target) == base


def test_symlink_tree_entry_cannot_be_presented_as_regular_source(history):
    repo, _, target, git = history
    blob = git("rev-parse", "HEAD:modify.py")
    git("update-index", "--add", "--cacheinfo", f"120000,{blob},link.py")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "symlink fixture metadata")
    linked = git("rev-parse", "HEAD")
    adapter = LocalGitRepository(repo)
    with pytest.raises(GitError, match="unsupported_tree_entry"):
        adapter.diff(target, linked, rename_threshold=50)
    with pytest.raises(GitError, match="unsupported_tree_entry"):
        adapter.read_text(linked, "link.py")
