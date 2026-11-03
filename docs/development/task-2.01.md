# Task 2.01 — Changed components

Task 2.01 identifies changed files and Python modules/classes/functions/methods
between two explicit commits. Git reads use the existing read-only LocalGit adapter.
Source is parsed with Python AST. The application entry point accepts a snapshot
reader so integration can supply an authorized reader and repository identity.

## Run

Requirements follow the root README: Python 3.14, uv and Git. From repository root:

```powershell
uv sync --locked
$baseSha = git rev-parse HEAD~1
$targetSha = git rev-parse HEAD
uv run smartregression changed-components --repository . --base $baseSha --target $targetSha
```

Choose commits in a repository you are authorized to inspect. `base` and `target`
must be full commit SHAs. Comparisons use their two trees directly. The caller
supplies PR resolution policy when integrating a PR workflow.

JSON is written to stdout. Exit 0 means completed within the declared scope,
1 means partial and still returns JSON, 2 means invalid input or fatal Git error
with a sanitized diagnostic on stderr. A bad SHA emits no successful JSON result.
The existing `validate-report` command continues to accept canonical AnalysisReport.

## Stage output and identity

`schema_version: changed-components/1` identifies this task-specific stage document.
It carries repository identity, base_sha, target_sha, comparison_mode, status,
components and per-file status/limitations. The local CLI uses the resolved local
repository path as identity. Integration must supply its authorized repository ID
to `identify_changes(reader, repository=..., base=..., target=...)`.

This stage shape is proposed for consumers in tasks 2.02/2.03/2.13/2.14. It is
separate from the canonical AnalysisReport and has no selection/execution payload.
Canonical Pydantic schemas, generated types and frontend report consumers are
unchanged. Consumer acceptance and a future shared stage-schema decision remain
with the integration owners. CLI emits paths/symbols but omits source excerpts.

Each ComponentChange has path, previous_path, kind, symbol, change,
base_location, target_location and reason. A Location has 1-based inclusive
line_start/line_end. Base locations refer to previous_path (when present), otherwise
path, at base_sha. Target locations refer to path at target_sha. Deleted components
have only a base location; additions only a target location. Empty modules have no
source-line location. File records describe Git metadata and carry no line span.

## Mapping semantics

- Each Git change produces one file record. Python content/path changes also produce
  a module record after successful parsing. Metadata-only changes such as executable
  mode changes retain their file record. The module identity is its snapshot path,
  avoiding guesses about Python import roots or package configuration.
- Function/class matching uses qualified lexical names within the paired file.
  Methods include async methods directly scoped under a class. Nested functions
  retain qualified names. Decorators are included in source spans.
- Existing symbols compare source lines inside their spans. A symbol shifted to
  other line numbers with identical source is omitted from modified-symbol records.
  Comments/formatting inside a symbol remain observable textual changes. These
  records describe source edits; behavior and dependency impact require later stages.
- A changed container gets reason `contains_changed_symbol` when a child changes and
  its own nonblank source outside nested definitions is identical. Its child gets a separate
  record. Consumers should use kind/reason when counting changes to avoid counting
  a method and its container as independent direct edits.
- Pure file rename produces file/module rename records. Unchanged contained symbols
  stay unchanged. Rename plus edits retains previous_path and both locations.
  Git's existing 50% similarity rule determines file-rename recognition. Pure symbol
  renames are delete+add, with no heuristic identity matching.
- Imports and global assignments remain visible through file/module records.
  Non-Python files, including tests/config/dependency files, retain file metadata
  with status `file_only` and limitation `non_python_file_level_only`.
- Syntax errors, duplicate qualified symbols, oversized/binary/non-UTF-8 Python
  sources and bounded source-read failures retain the file record and return partial.
  Both sides must parse to emit paired Python records. Validating Git commits and
  unsupported entries in the existing Git diff adapter can stop the stage entirely.
- Output ordering is deterministic by path and qualified symbol name. Python input
  files are limited by the existing 256,000-byte parser/reader guard. Static analysis
  inherits the host Python grammar. Repeated definitions and dynamically generated
  symbols do not receive guessed identities. LFS pointers, submodules and unsupported
  file modes retain the existing adapter restrictions.

## Verification and handoff

```powershell
uv run pytest backend/tests/unit/test_changed_components.py backend/tests/integration/test_changed_components_flow.py -q
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python scripts/export_contracts.py --check
uv run smartregression validate-report examples/reports/demo.json
```

Tests define their expected results independently of observed output and create
synthetic local Git fixtures. Integration covers file add/modify/delete/rename,
base-only deleted evidence, dirty-worktree isolation, invalid input, partial parsing
and CLI JSON/exit codes. Unit cases cover module-level edits, methods, decorators,
async/nested names, signature changes, containment, relocation, ambiguous symbols,
source limits and empty files. Task 2.02 can independently validate these locations
by reading the specified Git blobs.

Codex assisted implementation, tests and this handoff. Human review of the changes
and consumer integration remain required before the team records task acceptance.

### Observed checks on 2026-11-02

Windows, Python 3.14.10, dependencies installed with `uv sync --locked` from the
committed lockfile. Full suite: **81 passed**, one existing Starlette/httpx
deprecation warning. Ruff check and format check passed, as did schema export
`--check`, canonical DEMO CLI validation and `git diff --check`.

The CLI also compared actual repository commits `e937f669fefada31d5254b355f92f24e88e41725`
and `977a9b9e6c500da48c1c0c671ea515995847e130`: exit 0, completed, 29 file records
and 49 total component records. These counts describe that commit pair only.

Independent agent code review found a physical-line counting defect for Unicode
separators inside Python literals. Regression tests reproduced the failure, then
passed after the fix. A containment-label edge case also received a regression and
fix. Review and tests are engineering checks; team acceptance remains pending.

The user subsequently chose the existing personal branch
`codex/s1-1-06-closeout` for ongoing work. Task 2.01 was moved there with its
original Sprint 1 closeout commit retained. On that branch the full suite ran
**76 passed**, one existing deprecation warning. The earlier 81-test result used
the newer main baseline, which also includes five candidate-harness tests.
