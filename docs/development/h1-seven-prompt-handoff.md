# H1 — Seven-prompt implementation handoff

Baseline: `b3b251aa86854c63abeb6659a0be857b47e3505c`, fetched 2026-11-05.
The user authorized sequential implementation, tests, commit/push and PR creation;
merge and independent approval remain separate. Worktree:
`D:/smart-regression-ai/var/h1-execution-20261105`. Existing root checkout/untracked
files and the previous implementation checkout are preserved.

## Reconciliation

| Existing work | Baseline evidence | Action |
| --- | --- | --- |
| 2.14 v2 reports/native IDs | Present on main | Preserve public schemas; extend internal acquisition boundary only |
| `e03312a` EvidenceStore | Commit and domain adapter absent on main | Reconcile codec/adapter/tests against current migration head in prompt 2 |
| `1c2e011` resolver | Commit and resolver absent on main | Reuse after checking current impact producers in prompt 3 |
| `f88e823` compound workflow | Main still leaves impact/evidence/retrieval unavailable | Reconcile in prompt 4; preserve newer inventory hooks |
| `b7ac7a2` impact bounds | Not an ancestor of main | Assess behavior/test equivalence before porting bounds |
| Inventory/mapping and context/ranker | Modules present; workflow integration incomplete | Wire actual implementations in prompts 5/6 |
| PostgreSQL foundation | Existing Core/psycopg/Alembic infrastructure | Reuse; KH remains migration-chain owner/reviewer boundary |

## Prompt 1 — Index source acquisition

`application/index_sources.py` supplies `acquire_index_snapshot` and
`verify_index_sources`. Both use the existing authorization and Git-blob acquisition
path. Persisted manifests are checked against freshly acquired committed bytes,
the expected commit, version and configuration; a self-consistent forged snapshot
is insufficient. Dirty worktree bytes are not substituted for frozen Git content.

`SnapshotSource` implementations are trusted composition dependencies. An operator's
explicit local path/ID binding is the current authorization mechanism, not a new
multi-user auth service. This change does not publish artifacts or enable index
ready; `IndexBuild.ready()` retains its fail-closed guard. Public v1/v2 contracts
and generated consumers are unchanged. Internal `index/1` and `chunk/1` stay at
their existing shape; producer/consumer review and runtime readiness are separate.

Tests use real local Git fixtures whose source must never execute. Expected cases
include wrong authorization/revision/config/version, base-target mismatch,
self-consistent forgery, source tampering and invalid manifest ranges. Existing
manifest tests cover physical CR/LF/CRLF and exact-byte hashes.

### Actual checks

- Red: new integration test collection failed with missing `index_sources` module.
- Initial sandbox run: Windows `WinError 5` on pytest basetemp; environment failure,
  not evidence of a product defect. No gate weakened.
- Elevated focused suite: **57 passed, 1 skipped** (POSIX FIFO on Windows), exit 0.
- Ruff check/format and exporter `--check`: exit 0.
- Full backend regression: **695 passed, 75 skipped, 1 existing Starlette/httpx
  deprecation warning**, exit 0, 178.62s. Skips are 74 opt-in PostgreSQL cases
  (later dedicated harness) and one Windows/POSIX FIFO case.

Commands ran from the worktree with Python/Ruff in
`D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/`, `PYTHONPATH=backend/src`,
`PYTHONDONTWRITEBYTECODE=1`, portable Git prepended from
`D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd`:

```powershell
python -m pytest backend/tests/integration/test_index_acquisition.py backend/tests/unit/test_index_manifest.py backend/tests/integration/test_snapshot_preparation.py -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p1-focused-external
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p1-full
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
```

No PostgreSQL/browser checks are required for this internal source boundary alone;
they remain required for their later integration slices. No independent review or
Sprint 2 acceptance is claimed.

## Remaining sequence

1. Publish prompt 1 after the regression gate.
2. EvidenceStore PostgreSQL/P3 plus real DB acceptance.
3. Source resolver/explanation and freeze/re-inspection.
4. Core workflow/CLI/compound persistence.
5. Inventory/mapping sidecar.
6. Actual retrieval integration; verify producer/storage dependencies first.
7. A01–A07 checks, bounded fixes and H1 acceptance evidence.

If a dependency is absent, complete independent work and record the specific missing
deliverable; never mark a mock integration or missing runtime gate as complete.

OpenAI Codex assisted implementation/tests/docs and self-review. The team retains
responsibility for understanding the diff; no independent approval is fabricated.
