"""Read-only, full-SHA local Git spike. No checkout, hooks, filters or repo execution.

Caller authorizes the repository directory. Only ordinary UTF-8 file paths are
supported; ambiguous modes/names are rejected instead of silently normalised.
"""

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from smartregression.adapters.bounded_process import bounded_command
from smartregression.contracts.models import ChangedComponent


class LocalGit:
    def __init__(self, repository: Path) -> None:
        self.repository = repository.resolve(strict=True)

    def _git(self, *args: str) -> bytes:
        # Do not inherit Git redirect/config/credential variables from the caller.
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
            GIT_NO_REPLACE_OBJECTS="1",
            GIT_OPTIONAL_LOCKS="0",
        )
        try:
            return bounded_command(
                [
                    "git",
                    "-c",
                    "core.fsmonitor=false",
                    "-c",
                    "core.hooksPath=",
                    "-C",
                    str(self.repository),
                    *args,
                ],
                timeout=15,
                cap=2_000_000,
                env=env,
                merge_stderr=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("git_unavailable_or_timeout") from exc

    def _commit(self, sha: str) -> None:
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", sha):
            raise ValueError("invalid_commit")
        try:
            kind = self._git("cat-file", "-t", sha).strip()
        except ValueError as exc:
            raise ValueError("invalid_commit") from exc
        if kind != b"commit":
            raise ValueError("invalid_commit")

    @staticmethod
    def _path(path: str) -> str:
        if (
            not path
            or path != path.strip()
            or path.startswith("/")
            or any(c in path for c in "\\:\x00\n\r\t")
            or any(p in {"", ".", ".."} for p in path.split("/"))
            or PurePosixPath(path).is_absolute()
        ):
            raise ValueError("unsupported_path")
        return path

    def diff(self, base: str, target: str) -> list[ChangedComponent]:
        """Direct two-tree comparison, never silently substitute merge-base."""
        self._commit(base)
        self._commit(target)
        fields = self._git(
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--raw",
            "--no-abbrev",
            "-z",
            "--find-renames=50%",
            base,
            target,
            "--",
        ).split(b"\0")
        changes = []
        cursor = 0
        while cursor < len(fields) and fields[cursor]:
            header = fields[cursor].decode("ascii").split()
            old_mode, new_mode, _, _, status = header
            if old_mode[1:] not in {"000000", "100644", "100755"} or new_mode not in {
                "000000",
                "100644",
                "100755",
            }:
                raise ValueError("unsupported_file_mode")
            path = self._path(fields[cursor + 1].decode("utf-8", errors="strict"))
            previous = None
            cursor += 2
            if status.startswith("R"):
                previous = path
                path = self._path(fields[cursor].decode("utf-8", errors="strict"))
                cursor += 1
                change = "renamed"
            else:
                change = {"A": "added", "M": "modified", "D": "deleted"}.get(status)
            if change is None:
                raise ValueError("unsupported_change")
            changes.append(ChangedComponent(path=path, change=change, previous_path=previous))
        return changes

    def read_text(self, sha: str, path: str) -> str:
        self._commit(sha)
        path = self._path(path)
        # Literal pathspec prevents glob/magic expansion; only inspect a regular blob.
        entry = self._git("ls-tree", "-z", sha, "--", ":(literal)" + path).split(b"\0")[0]
        if not entry:
            raise ValueError("missing_snapshot_path")
        metadata, actual = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        if actual.decode("utf-8") != path or mode not in {b"100644", b"100755"} or kind != b"blob":
            raise ValueError("unsupported_file_mode")
        size = int(self._git("cat-file", "-s", oid.decode("ascii")))
        if size > 256_000:
            raise ValueError("source_limit")
        content = self._git("cat-file", "blob", oid.decode("ascii"))
        if b"\0" in content:
            raise ValueError("binary_source")
        return content.decode("utf-8", errors="strict")
