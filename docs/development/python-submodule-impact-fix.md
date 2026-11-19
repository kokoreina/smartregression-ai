# Python submodule import impact — local fix, 18/11/2026

## Reproduction and cause

Project `7f4a7c29-9943-407a-b679-b1bd90f37712`, sqlparse commit
`09dbe1eec31ed1b3cd05366748865f11ba427d32`, selected file
`sqlparse/engine/grouping.py`: the stored snapshot returned zero direct and
indirect dependents despite `engine/__init__.py:8` and `engine/filter_stack.py:11`
importing `grouping`. The latter calls `grouping.group(stmt)` at line 41.

Named imports resolved the package but omitted the child-module import edge.
Looking up a package's self-reexport also recursed into the same binding.
The UI faithfully displayed incomplete backend data; this is not AI training.

## Change

- Resolve named module bindings and record their dependency with import-line evidence.
- Preserve local alias roots and dotted module suffixes when following reexports.
- Separate import-statement dependencies from call-site lexical shadowing: assigning
  over an imported local name does not erase the import dependency.
- Keep explicit package symbols ahead of same-named submodules; retain cycle bounds.
- Advance parser config to v4 so old immutable snapshots cannot mask the fix.

No API/schema, dependency, migration, quota or provider changes. Input code is
parsed, never executed. Changes remain local on `feat/an-task-3.46-ownership`;
existing task 3.46 files are preserved. No commit, push or main checkout edits.

## Verification

Regression tests first failed for absolute/relative package reexports. Review
identified rebinding and dotted-prefix cases; their new tests also failed before
the fixes. The final relevant suite passed **487 tests**:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_python_submodule_impact.py backend/tests/unit/test_python_explorer_resolution.py backend/tests/unit/test_explorer_graph.py backend/tests/unit/test_scenarios_unit.py backend/tests/unit/test_snapshot_models.py backend/tests/unit/test_product_ownership_matrix.py -q --tb=short
```

Ruff check/format and `git diff --check` passed for changed Python files.
Automated technical review is not team approval.

The real project snapshot was rebuilt from its stored, digest-verified source
and tree at the same commit, then saved via `PostgresExplorerStore.save` under
the same owner/project and new parser config. Readback verified the new snapshot,
the preserved original snapshot and identical source bytes:

| Measure | Original | Rebuilt |
| --- | ---: | ---: |
| Selected changed file | 1 | 1 |
| Direct dependents | 0 | 2 |
| Indirect dependents | 0 | 28 |
| Potential scope including selected file | 1 | 31 |
| Analyzed files | 36 | 36 |

Direct files are `sqlparse/engine/__init__.py` and
`sqlparse/engine/filter_stack.py`. The broader indirect scope includes package
initialization dependencies and is conservative, not behavioral proof or a
failure probability. Remaining unresolved relations: 1,039; outside-scope files:
58. No exhaustive claim of soundness/completeness.

Local evidence: `var/local-app/fixed-parser-audit.json`; baseline evidence remains
in `C:/Users/DELL G3/smartregression-ai-1/var/run-local/result-audit/`.

## Running app

Frontend and fixed backend now run from this worktree, retaining the original
auth environment and PostgreSQL database from
`C:/Users/DELL G3/smartregression-ai-1/var/auth/web.env` (private, ignored).
Process metadata: `var/local-app/fixed-processes.json`. The original checkout's
startup script still starts its older backend; it does not contain this fix.
No credential or account migration occurred.

Health, capabilities (product mode) and CSRF endpoints responded successfully
through port 5173 after startup. Browser login with a user's password was not
performed. Refresh the existing project page and select `grouping.py` again.
Only this project/commit was regenerated; other cached snapshots need explicit
materialization under the new parser config. Historical runs and saved reports
were not rewritten.
