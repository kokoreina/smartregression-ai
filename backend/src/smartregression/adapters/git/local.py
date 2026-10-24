"""Read-only local Git spike. Does not checkout files or execute repository code."""

import os
import re
import subprocess
from pathlib import Path

from smartregression.contracts.models import ChangedComponent
from smartregression.core.git.changes import parse_name_status, validate_path


class GitError(ValueError):
    pass


class LocalGitRepository:
    def __init__(self, root: Path, *, timeout_seconds: float = 10):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir() or not 0 < timeout_seconds <= 60:
            raise GitError("invalid_repository_or_timeout")
        self.timeout = timeout_seconds
        observed = self._git("rev-parse", "--show-toplevel").decode().strip()
        if Path(observed).resolve() != self.root:
            raise GitError("wrong_repository_root")

    def _git(self, *args: str) -> bytes:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_OPTIONAL_LOCKS="0",
            GIT_TERMINAL_PROMPT="0",
        )
        try:
            result = subprocess.run(
                [
                    "git",
                    "--literal-pathspecs",
                    "-c",
                    "core.fsmonitor=false",
                    "-c",
                    "core.quotePath=false",
                    "-C",
                    str(self.root),
                    *args,
                ],
                capture_output=True,
                timeout=self.timeout,
                env=env,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GitError("git_unavailable_or_timeout") from exc
        if result.returncode:
            raise GitError("git_operation_failed")
        if len(result.stdout) > 8 * 1024 * 1024:
            raise GitError("git_result_too_large")
        return result.stdout

    def validate_commit(self, sha: str) -> str:
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", sha):
            raise GitError("invalid_sha")
        if self._git("cat-file", "-t", sha).strip() != b"commit":
            raise GitError("not_commit")
        return sha

    def resolve(self, revision: str) -> str:
        if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision):
            return self.validate_commit(revision)
        if revision == "HEAD":
            return self.validate_commit(self._git("rev-parse", "--verify", "HEAD").decode().strip())
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]*", revision):
            raise GitError("invalid_ref")
        refs = (
            (revision,)
            if revision.startswith("refs/")
            else (
                f"refs/heads/{revision}",
                f"refs/tags/{revision}",
            )
        )
        candidates = []
        for ref in refs:
            try:
                value = self._git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
            except GitError:
                continue
            candidates.append(value.decode().strip())
        if len(candidates) != 1:
            raise GitError("missing_or_ambiguous_ref")
        return self.validate_commit(candidates[0])

    def merge_base(self, base_tip: str, head: str) -> str:
        self.validate_commit(base_tip)
        self.validate_commit(head)
        if self._git("rev-parse", "--is-shallow-repository").strip() != b"false":
            raise GitError("incomplete_history")
        bases = self._git("merge-base", "--all", base_tip, head).decode().splitlines()
        if len(bases) != 1:
            raise GitError("non_unique_merge_base")
        return self.validate_commit(bases[0])

    def diff(
        self, base: str, target: str, *, rename_threshold: int
    ) -> tuple[ChangedComponent, ...]:
        self.validate_commit(base)
        self.validate_commit(target)
        if type(rename_threshold) is not int or not 1 <= rename_threshold <= 100:
            raise GitError("invalid_rename_threshold")
        raw = self._git(
            "diff",
            "--name-status",
            "-z",
            "--no-ext-diff",
            "--no-textconv",
            f"--find-renames={rename_threshold}%",
            base,
            target,
            "--",
        )
        try:
            changes = parse_name_status(raw)
            for change in changes:
                self._regular_blob(base, change.previous_path or change.path, required=False)
                self._regular_blob(target, change.path, required=False)
            return changes
        except ValueError as exc:
            raise GitError(str(exc)) from exc

    def _regular_blob(self, commit: str, path: str, *, required: bool = True) -> None:
        observed = self._git("ls-tree", "-z", commit, "--", path)
        if not observed and not required:
            return
        metadata = observed.split(b"\t", 1)[0].split()
        if len(metadata) != 3 or metadata[0] not in {b"100644", b"100755"}:
            raise GitError("unsupported_tree_entry")

    def read_text(self, commit: str, path: str) -> str:
        self.validate_commit(commit)
        validate_path(path)
        self._regular_blob(commit, path)
        try:
            return self._git("show", f"{commit}:{path}").decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise GitError("unsupported_source_encoding") from exc
