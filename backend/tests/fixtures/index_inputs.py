"""Task-owned Git bytes and declared producer/config fixtures; no input execution."""

import subprocess

from smartregression.adapters.git_local import LocalGit
from smartregression.application.index_sources import acquire_index_snapshot
from smartregression.application.index_store import IndexConfiguration
from smartregression.application.snapshots import RepositoryAuthorization
from smartregression.core.retrieval.exclusions import exclusion_reason
from smartregression.core.retrieval.index_manifest import ChunkInput, build_index_manifest


def index_inputs(root, repository_id="index-fixture", contents=None):
    repo = root / "input"
    repo.mkdir(parents=True)

    def git(*args):
        return subprocess.check_output(
            [
                "git",
                "-c",
                "core.hooksPath=",
                "-c",
                "commit.gpgsign=false",
                "-C",
                str(repo),
                *args,
            ],
            text=True,
            stderr=subprocess.PIPE,
            timeout=20,
        ).strip()

    git("init", "-q", "--object-format=sha1")
    git("config", "user.name", "Index Storage Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "core.autocrlf", "false")
    contents = (
        contents
        if contents is not None
        else {
            "src/calc.py": b"raise RuntimeError('input_must_not_execute')\r\n# owned fixture\r\n",
            "docs/usage.md": b"Owned documentation\rLine two\n",
            ".env": b"PRIVATE_FIXTURE=synthetic_excluded_marker\n",
            "labels/outcomes.py": b"synthetic_excluded_marker = 1\n",
        }
    )
    for path, raw in contents.items():
        file = repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    git("add", ".")
    git("commit", "-qm", "owned source")
    commit = git("rev-parse", "HEAD")
    source = LocalGit(repo)
    authorization = RepositoryAuthorization(repository_id, repo)
    snapshot = acquire_index_snapshot(
        source, authorization=authorization, repository_id=repository_id, commit=commit
    )
    config = IndexConfiguration(
        "fixture-parser/1",
        "fixture-chunker/1",
        "fixture-tokenizer/1",
        "fixture-query/1",
        "fixture-scoring/1",
        "fixture-ranking/1",
    )
    chunks = []
    for path, raw in contents.items():
        if exclusion_reason(path, raw) is None and raw:
            import re

            lines = len(re.findall(rb"\r\n|\r|\n", raw)) + int(not raw.endswith((b"\r", b"\n")))
            chunks.append(ChunkInput(path, 1, lines, raw))
    manifest = build_index_manifest(
        snapshot, chunks, index_version="fixture-index/1", configuration_id=config.digest
    )
    return dict(
        source=source,
        authorization=authorization,
        snapshot=snapshot,
        manifest=manifest,
        configuration=config,
        git=git,
    )
