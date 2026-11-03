import json
import subprocess

import pytest

from smartregression.adapters.git_local import LocalGit
from smartregression.application.changed_components import identify_changes
from smartregression.cli.main import main


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def revisions(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    files = {
        "edit.py": "class A:\n    def run(self):\n        return 1\n",
        "gone.py": "def deleted():\n    return 0\n",
        "old.py": "# stable rename fixture\n" * 20 + "def stable():\n    return 7\n",
        "broken.py": "def ok():\n    pass\n",
        "README.md": "before\n",
    }
    for name, source in files.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "edit.py").write_text(files["edit.py"].replace("return 1", "return 2"))
    (tmp_path / "gone.py").unlink()
    (tmp_path / "old.py").rename(tmp_path / "new.py")
    (tmp_path / "added.py").write_text("def added():\n    return 3\n")
    (tmp_path / "broken.py").write_text("def invalid(")
    (tmp_path / "README.md").write_text("after\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "target")
    return tmp_path, base, git(tmp_path, "rev-parse", "HEAD")


def test_real_git_changes_partial_parse_and_dirty_tree(revisions):
    repo, base, target = revisions
    result = identify_changes(LocalGit(repo), repository="fixture", base=base, target=target)
    assert result.status == "partial"
    file_records = [r for r in result.components if r.kind == "file"]
    assert {(r.path, r.change, r.previous_path) for r in file_records} == {
        ("edit.py", "modified", None),
        ("gone.py", "deleted", None),
        ("new.py", "renamed", "old.py"),
        ("added.py", "added", None),
        ("broken.py", "modified", None),
        ("README.md", "modified", None),
    }
    deleted = next(r for r in result.components if r.symbol == "deleted")
    assert deleted.base_location.line_start == 1 and deleted.target_location is None
    failed = next(f for f in result.files if f.path == "broken.py")
    assert failed.status == "partial" and "python_parse_failed" in failed.limitations
    (repo / "edit.py").write_text("dirty input should never be parsed")
    assert (
        identify_changes(LocalGit(repo), repository="fixture", base=base, target=target) == result
    )
    assert result == identify_changes(
        LocalGit(repo), repository="fixture", base=base, target=target
    )
    assert result.base_sha == base and result.target_sha == target


def test_same_commit_and_invalid_identity(revisions):
    repo, base, _ = revisions
    result = identify_changes(LocalGit(repo), repository="fixture", base=base, target=base)
    assert result.components == () and result.status == "completed"
    with pytest.raises(ValueError, match="invalid_commit"):
        identify_changes(LocalGit(repo), repository="fixture", base="HEAD", target=base)
    with pytest.raises(ValueError, match="repository_required"):
        identify_changes(LocalGit(repo), repository=" ", base=base, target=base)


def test_cli_json_partial_and_invalid_input(revisions, capsys):
    repo, base, target = revisions
    args = ["changed-components", "--repository", str(repo), "--base", base, "--target", target]
    assert main(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "changed-components/1"
    assert payload["base_sha"] == base and payload["status"] == "partial"
    args[-1] = base
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["components"] == []
    args[-1] = "HEAD"
    assert main(args) == 2
    captured = capsys.readouterr()
    assert not captured.out and "invalid_commit" in captured.err


def test_cli_missing_repository_is_clean_error(capsys, tmp_path):
    assert (
        main(
            [
                "changed-components",
                "--repository",
                str(tmp_path / "absent"),
                "--base",
                "a" * 40,
                "--target",
                "b" * 40,
            ]
        )
        == 2
    )
    assert not capsys.readouterr().out


@pytest.mark.parametrize(
    "content,expected",
    [(b"\xff", "source_not_utf8"), (b"x\0y", "binary_source"), (b"#" * 256001, "source_limit")],
    ids=["invalid-encoding", "binary", "oversized"],
)
def test_source_read_limitations_keep_file_record(revisions, content, expected):
    repo, _, base = revisions
    (repo / "added.py").write_bytes(content)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "unsupported source")
    target = git(repo, "rev-parse", "HEAD")
    result = identify_changes(LocalGit(repo), repository="fixture", base=base, target=target)
    assert result.status == "partial"
    assert len(result.components) == 1
    assert result.components[0].kind == "file"
    assert result.files[0].limitations == (expected,)


def test_cli_preserves_existing_report_validation(capsys):
    assert main(["validate-report", "examples/reports/demo.json"]) == 0
    assert "Valid report [DEMO]" in capsys.readouterr().out
