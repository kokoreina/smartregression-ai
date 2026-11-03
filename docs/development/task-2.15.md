# Task 2.15 — Authorized immutable snapshots

Branch `feat/an-task-2.15-snapshots` starts from An's personal branch
`codex/s1-1-06-closeout`, commit `1bfef08`. This task produces base/target source
snapshots for graph, inventory and indexing consumers.

## Interface checkpoint for 2.14

`prepare_snapshots(source, authorization=RepositoryAuthorization(repo_id, local_path),
repository_id=repo_id, base=full_sha, target=full_sha)` binds a local source to an
explicit caller authorization decision before reading Git. A mismatched ID/path is
rejected. Service authentication/permission lookup remains with the caller.

The local CLI treats `--authorized-root` as the operator's explicit authorization
of that exact repository root. It does not constitute server-side user authentication.
The source must be a local non-bare repository rooted at the supplied path.
PR/ref resolution is upstream. This interface accepts two full commit IDs and uses
their exact trees. It does not select merge-base or re-resolve mutable refs.

New internal documents use `snapshot/1` and `snapshot-pair/1`. Review these proposed
stage interfaces with Tấn Huy/Khánh before wiring a shared workflow in 2.14/2.13.
Canonical AnalysisReport, OpenAPI and generated frontend types remain unchanged.

Each SnapshotManifest records repository_id, commit, files, snapshot_id,
schema_version and materializer_version. File metadata contains path, Git mode,
blob_id, byte size and SHA-256. Snapshot ID hashes canonical manifest content,
including repository/commit/materializer identity. Git blob IDs are recomputed from
the raw bytes before publication. Repository identity is never inferred from a hash.

## CLI

From the project root after `uv sync --locked`:

```powershell
$repoPath = 'D:\approved-input-repository'
$baseSha = git -C $repoPath rev-parse HEAD~1
$targetSha = git -C $repoPath rev-parse HEAD
uv run smartregression prepare-snapshots --repository $repoPath --repository-id team-example --authorized-root $repoPath --base $baseSha --target $targetSha --output var/snapshot-run-001
```

Use an approved input repository and a NEW output directory. The output parent
must already exist. Output must be outside the input repository. Exit 0 returns a
manifest pair on stdout; exit 2 prints a sanitized error code to stderr. Existing
output directories are preserved, including their files. A successful export has:

```text
snapshot-run-001/
  base/manifest.json
  base/files/<paths from base commit>
  target/manifest.json
  target/files/<paths from target commit>
  pair.json
```

Consumers parse pair.json and verify the trusted manifests before use. The pair
marker is published by a final rename after its complete contents are written.
Source bytes are copied from
Git blobs directly, preserving CRLF, binary files and empty files. Worktree changes,
checkout filters and source hooks do not supply bytes. Git's executable mode is
recorded in the manifest; exported files are read-only data, with no promise that
host filesystem permissions recreate the original execution environment.

Git reads use --no-lazy-fetch and GIT_NO_LAZY_FETCH=1 so a partial clone cannot acquire
missing blobs implicitly. Required objects must already be local. Git must support
--no-lazy-fetch; unsupported Git versions fail rather than silently acquiring data. See the
[Git environment documentation](https://git-scm.com/docs/git#Documentation/git.txt-GITNOLAZYFETCH).

## Integrity, bounds and failure behavior

- Default per-snapshot bounds are 1,000 files, 1,000,000 bytes/file and 16,000,000
  total bytes. SnapshotLimits can tighten these values. Its hard maxima are 10,000
  files, 1,000,000 bytes/file and 64,000,000 total bytes. Git subprocess limits remain
  15 seconds and 2,000,000 output bytes per command.
- Ordinary Git blobs with mode 100644/100755 are supported. Symlinks and gitlinks
  are rejected. LFS pointer blobs are preserved as stored; LFS objects are not fetched.
- Portable path validation rejects traversal, absolute paths, control characters,
  Windows reserved names/characters, .git components, case/normalization aliases
  and file/directory prefix collisions before any materialization.
- Both snapshots are prepared and validated before disk writes. Materialization
  reserves a fresh output directory exclusively. An incomplete owned directory is
  removed on failure; unrelated/existing directories are preserved. A crash can
  leave an incomplete directory without pair.json; consumers must not use it.
- Snapshot content files are marked read-only. `verify_snapshot(path,
  expected=trusted_manifest)` checks the manifest, exact file set, sizes and hashes.
  The expected manifest must come from a trusted run record, not from the directory
  being checked. Use verification before consuming a stored snapshot.
- The store rejects filesystem symlinks/junctions at output ancestors and during
  verification. It assumes a caller-controlled local workspace. Read-only flags
  are not an OS sandbox or write-once storage, and this implementation does not
  prevent a concurrent privileged host process from replacing files during access.
- Preparation is bounded local data handling. It does not execute input code,
  install dependencies, discover tests, acquire repositories or implement a general
  isolated runner. Workflow and persistence integration require separate review.

## Verification

```powershell
uv run pytest backend/tests/unit/test_snapshot_models.py backend/tests/integration/test_snapshot_preparation.py -q
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python scripts/export_contracts.py --check
```

Tests use synthetic local Git repositories, independently specified bytes and
expected identities. Coverage includes authorization before reads, wrong SHA and
wrong object type, exact Git bytes, dirty trees, empty files/trees, binary data,
SHA-256 Git, source limits, unsupported symlink entries, portable path collisions,
forged manifests, existing output preservation, cleanup on failure and CLI behavior.

Codex assisted design, implementation, tests and reporting. Team review and
consumer acceptance of the proposed interface remain pending.

### Observed verification, 2026-11-02

Windows, Python 3.14.10 and Git 2.55. Full suite: 118 passed, one POSIX FIFO case
skipped on Windows and one pre-existing Starlette/httpx deprecation warning.
Ruff check/format, schema export --check, canonical DEMO validation and diff check
passed. The FIFO case runs on POSIX CI. Independent agent review reproduced Git
lazy acquisition in a partial clone; the regression now rejects missing objects
with the object pack set and missing-object list unchanged.

CLI smoke on a new synthetic Git fixture exited 0, exporting base with one file
and target with two files. Both snapshots passed independent trusted-manifest
verification with exact CRLF/binary bytes despite a dirty worktree. A whole-project
smoke intentionally rejected the 1,394,320-byte Database DOCX at the default
1,000,000-byte per-file quota (snapshot_limit), before creating output. This bounded
implementation requires input repositories within the declared resource limits.
