# 1.07 Read only Git diff and Python structure spike

Prepared with Codex assistance on 2026-10-24 under Tran Hung Khanh's request to
complete remaining group Sprint 1 work. Workstream owner: Do Ha An; proposed
reviewer: Pham Phan Hoang Huy. Separate integration branch; does not overwrite
An's [1.06 draft](revision-semantics.md) or declare its Q01-Q10 approved.

## Explicit experimental scope

The adapter takes a local repository root and two full lowercase commit SHAs.
It verifies the root and object types, then requests name-status NUL-delimited
Git diff with external diff/textconv disabled. Rename similarity is an explicit
call argument; tests use 50 as the proposed experimental threshold. No checkout,
reset, install, Git hook execution or input Python execution occurs in the adapter.
Dirty working-tree content is excluded because reads address committed objects.

| Case | Behavior covered by tests |
| --- | --- |
| Add/modify/delete/rename | Canonical ChangedComponent using current model; rename preserves previous_path |
| Unicode/internal spaces | Preserve original path identity |
| Missing/malformed/unknown SHA or blob instead of commit | Fail, never return empty diff |
| Identical base/target | Valid empty diff |
| Dirty working tree | Leave it unchanged; compare committed trees only |
| Named ref moves after freeze | Frozen full SHA remains the run identity |
| Unsupported status/type/path encoding, leading/trailing whitespace, traversal | Explicit error instead of normalization or omission |

Core parser: `backend/src/smartregression/core/git/changes.py`. Git subprocess
adapter: `backend/src/smartregression/adapters/git/local.py`. Real local Git history
is created by tests only under their own uniquely named ignored `var` directory.
Tests remove only that owned fixture tree and handle Windows read-only Git objects.

## Revision resolution boundary

Resolver accepts HEAD, exact branch/tag/ref or full SHA; ambiguous branch/tag names
are rejected. PR helper requires one merge-base and non-shallow history. It does
not fetch PR metadata, detect live GitHub races or choose production PR policy.
Direct diff makes no ancestry assumption. Input path encodings/type changes,
submodules and symlinks outside contract support fail explicitly. Git version and
rename threshold must be recorded with any exported spike evidence.

The 8 MiB captured Git-result check is a result-size guard, not an enforced peak
subprocess-memory limit. Worker resource isolation is a different boundary. No
production arbitrary-repository security guarantee is made by this local adapter.

## G1 Python parser and dependency observations

`core/impact/python_structure.py` uses Python ast.parse only. It records qualified
class/function symbols with line ranges, imports and syntactic call expressions.
It never imports or executes input source. Syntax failure is explicit partial
analysis. Every successful result still reports limits: static observations do not
resolve dynamic dispatch/reflection, import graphs or complete transitive impact.
This is a parser/dependency prototype, not a sound whole-program impact engine.

## Public candidate read only check

TinyDB was fetched with `git clone --no-checkout --depth 2` into ignored
`var/candidates/tinydb`. Target `edff96aeb2616402e9489d46e90a592c05565621`, parent
`0ba5727f2d915dedafb192e92f65dd64a21e3411`. LICENSE contains MIT, and pyproject lists
pytest dev dependencies and Python >=3.10,<4. This matches Viet's license permalink.
No TinyDB checkout, dependency install, pytest discovery or test execution occurred.
The clone is shallow, so it is not evidence that arbitrary PR merge-base resolution
works on that candidate. It is not an approved final benchmark cohort.

## Verification and handoff

Focused Git/config tests: 49 passed on Windows/Python 3.14.5 using local fixtures.
Worker tests add separate simulated-transport evidence, not actual Docker execution.
See [integration evidence](integration-evidence.md) for final commands/results.
No public contract/generated artifact changed. D05/Q approvals, candidate runtime
and independent human review remain pending. Codex authored/tested this integration
spike; do not attribute the new code to An or claim approval by another member.
