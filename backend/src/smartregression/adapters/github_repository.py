"""Bounded public GitHub acquisition; archives are read in memory, never extracted/executed."""

import hashlib
import io
import json
import re
import time
import zipfile
from pathlib import Path
from urllib.parse import quote

import httpx

from smartregression.contracts.models import ChangedComponent
from smartregression.contracts.repository import (
    RepositoryLookup,
    RepositoryOverview,
    RepositoryTree,
)
from smartregression.core.git.snapshots import TreeEntry, validate_snapshot_paths


class GithubRepository:
    def __init__(
        self, url: str, workspace: Path, client: httpx.Client, *, token: str | None = None
    ) -> None:
        self.url = RepositoryLookup(repository_url=url).repository_url
        self.slug = self.url.removeprefix("https://github.com/")
        self.repository = workspace
        self.client = client
        if token is not None and (
            not token
            or token != token.strip()
            or len(token) > 2000
            or any(ord(c) < 32 for c in token)
        ):
            raise ValueError("invalid_github_credential")
        self._token = token
        self.deadline = time.monotonic() + 75
        self._entries: dict[str, tuple[TreeEntry, ...]] = {}
        self._blobs: dict[str, bytes] = {}
        self._verified_public = False

    def _get(self, path: str, *, archive: bool = False) -> bytes:
        host = "codeload.github.com" if archive else "api.github.com"
        if time.monotonic() >= self.deadline:
            raise ValueError("github_timeout")
        try:
            with self.client.stream(
                "GET",
                f"https://{host}/{path}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "SmartRegression-AI",
                    "Accept-Encoding": "identity",
                    **(
                        {"Authorization": f"Bearer {self._token}"}
                        if self._token and not archive
                        else {}
                    ),
                },
                timeout=min(20, self.deadline - time.monotonic()),
                follow_redirects=False,
            ) as response:
                if response.is_redirect:
                    raise ValueError("github_redirect_rejected")
                if response.status_code in {403, 429}:
                    raise ValueError("github_rate_limit")
                if response.status_code == 404:
                    raise ValueError("github_repository_or_commit_not_found")
                if response.status_code != 200:
                    raise ValueError("github_unavailable")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise ValueError("github_unexpected_encoding")
                limit = 20_000_000 if archive else 2_000_000
                chunks, size = [], 0
                for chunk in response.iter_bytes(chunk_size=65536):
                    size += len(chunk)
                    if size > limit or time.monotonic() > self.deadline:
                        raise ValueError("repository_limit")
                    chunks.append(chunk)
                return b"".join(chunks)
        except httpx.TimeoutException:
            raise ValueError("github_timeout") from None
        except httpx.HTTPError:
            raise ValueError("github_unavailable") from None

    def _json(self, path: str):
        try:
            return json.loads(self._get(path))
        except json.JSONDecodeError, UnicodeError:
            raise ValueError("github_invalid_response") from None

    def _public(self) -> dict:
        value = self._json("repos/" + self.slug)
        if (
            value.get("private") is not False
            or value.get("full_name", "").lower() != self.slug.lower()
        ):
            raise ValueError("public_github_repository_required")
        self._verified_public = True
        return value

    def inspect(self) -> RepositoryOverview:
        value = self._public()
        commits = self._json(f"repos/{self.slug}/commits?per_page=10")
        return RepositoryOverview(
            repository_url=self.url,
            full_name=value["full_name"],
            default_branch=value["default_branch"],
            commits=[
                dict(
                    sha=c["sha"],
                    message=c["commit"]["message"].split("\n")[0][:300],
                    date=c["commit"]["author"]["date"],
                )
                for c in commits[:10]
            ],
        )

    def resolve_branch(self, branch: str) -> str:
        from smartregression.contracts.repo_assistant import WatchInput

        WatchInput(branch=branch)
        if not self._verified_public:
            self._public()
        result = self._json(f"repos/{self.slug}/git/ref/heads/{quote(branch, safe='')}")
        value = result.get("object", {})
        if value.get("type") != "commit" or not re.fullmatch("[0-9a-f]{40}", value.get("sha", "")):
            raise ValueError("github_invalid_response")
        return value["sha"]

    def tree(self, sha: str) -> RepositoryTree:
        """List the pinned Git tree without reading blobs, archives or submodules."""
        if not re.fullmatch("[0-9a-f]{40}", sha):
            raise ValueError("invalid_commit")
        if not self._verified_public:
            self._public()
        commit = self._json(f"repos/{self.slug}/git/commits/{sha}")
        if commit["sha"] != sha or not re.fullmatch("[0-9a-f]{40}", commit["tree"]["sha"]):
            raise ValueError("snapshot_mismatch")
        value = self._json(f"repos/{self.slug}/git/trees/{commit['tree']['sha']}?recursive=1")
        if value.get("sha") != commit["tree"]["sha"]:
            raise ValueError("snapshot_mismatch")
        if value.get("truncated") is not False:
            raise ValueError("repository_tree_incomplete")
        items = value["tree"]
        if not isinstance(items, list):
            raise ValueError("github_invalid_response")
        if len(items) > 5000:
            raise ValueError("repository_tree_limit")
        kinds = {
            ("tree", "040000"): "directory",
            ("blob", "100644"): "file",
            ("blob", "100755"): "file",
            ("blob", "120000"): "symlink",
            ("commit", "160000"): "submodule",
        }
        entries = []
        for item in items:
            kind = kinds.get((item["type"], item["mode"]))
            if kind is None or not re.fullmatch("[0-9a-f]{40}", item["sha"]):
                raise ValueError("github_invalid_response")
            entries.append(dict(path=item["path"], kind=kind, size=item.get("size")))
        return RepositoryTree(
            repository_url=self.url, commit=sha, tree_sha=value["sha"], entries=entries
        )

    def snapshot_entries(self, sha: str) -> tuple[TreeEntry, ...]:
        if not re.fullmatch("[0-9a-f]{40}", sha):
            raise ValueError("invalid_commit")
        if sha in self._entries:
            return self._entries[sha]
        if not self._verified_public:
            self._public()
        commit = self._json(f"repos/{self.slug}/git/commits/{sha}")
        if commit["sha"] != sha or not re.fullmatch("[0-9a-f]{40}", commit["tree"]["sha"]):
            raise ValueError("snapshot_mismatch")
        tree = self._json(f"repos/{self.slug}/git/trees/{commit['tree']['sha']}?recursive=1")
        if tree.get("truncated") is not False or tree.get("sha") != commit["tree"]["sha"]:
            raise ValueError("repository_limit")
        entries = []
        for item in tree["tree"]:
            if item["type"] == "tree":
                continue
            if item["type"] != "blob" or item["mode"] not in {"100644", "100755"}:
                raise ValueError("unsupported_snapshot_entry")
            if (
                type(item.get("size")) is not int
                or not 0 <= item["size"] <= 1_000_000
                or not re.fullmatch("[0-9a-f]{40}", item["sha"])
            ):
                raise ValueError("repository_limit")
            entries.append(TreeEntry(item["path"], item["mode"], item["sha"], item["size"]))
        validate_snapshot_paths([e.path for e in entries])
        if len(entries) > 1000 or sum(e.size for e in entries) > 16_000_000:
            raise ValueError("repository_limit")
        raw = self._get(f"{self.slug}/zip/{sha}", archive=True)
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
                if len(zipped.infolist()) > 4000:
                    raise ValueError("repository_limit")
                members = [m for m in zipped.infolist() if not m.is_dir()]
                by_path = {}
                for member in members:
                    parts = member.filename.split("/", 1)
                    if len(parts) != 2 or parts[1] in by_path:
                        raise ValueError("snapshot_mismatch")
                    by_path[parts[1]] = member
                if set(by_path) != {e.path for e in entries}:
                    raise ValueError("snapshot_mismatch")
                for entry in entries:
                    if time.monotonic() > self.deadline:
                        raise ValueError("github_timeout")
                    member = by_path[entry.path]
                    if member.file_size != entry.size:
                        raise ValueError("snapshot_mismatch")
                    content = zipped.read(member)
                    digest = hashlib.sha1(
                        b"blob " + str(len(content)).encode() + b"\0" + content
                    ).hexdigest()
                    if digest != entry.blob_id:
                        raise ValueError("snapshot_mismatch")
                    self._blobs[entry.blob_id] = content
        except zipfile.BadZipFile, RuntimeError:
            raise ValueError("github_invalid_archive") from None
        self._entries[sha] = tuple(sorted(entries, key=lambda e: e.path))
        return self._entries[sha]

    def read_blob(self, oid: str, *, max_bytes: int) -> bytes:
        raw = self._blobs[oid]
        if len(raw) > max_bytes:
            raise ValueError("snapshot_limit")
        return raw

    def diff(self, base: str, target: str) -> list[ChangedComponent]:
        old = {e.path: e for e in self.snapshot_entries(base)}
        new = {e.path: e for e in self.snapshot_entries(target)}
        # No similarity guesses: rename is truthfully represented as delete+add.
        return [
            ChangedComponent(
                path=p,
                change="added" if p not in old else "deleted" if p not in new else "modified",
            )
            for p in sorted(old.keys() | new.keys())
            if p not in old or p not in new or old[p] != new[p]
        ]
