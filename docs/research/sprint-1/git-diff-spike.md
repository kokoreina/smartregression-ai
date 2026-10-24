# 1.07 and G1 - read-only Git/Python spike

2026-10-24 integration by Codex assisting Nguyen Tan Huy; guide owner remains
Do Ha An. Proposed reviewer: Pham Phan Hoang Huy. No independent approval claimed.

[LocalGit](../../../backend/src/smartregression/adapters/git_local.py) implements
direct base-tree to target-tree diff for full lowercase 40/64-hex commit SHAs.
It checks object type, disables replacement objects, external diff/textconv,
fsmonitor and hooks, suppresses inherited Git redirection/config variables, uses
argument vectors and bounded output/time. Caller must authorize local repo identity.
It does not resolve mutable refs, choose merge-base, clone or alter the input tree.

Raw NUL-delimited diff supports ordinary regular-file add/modify/delete/rename,
50% Git rename threshold, previous_path and no-change pairs. Reads use literal
pathspec and blob object IDs, never working-tree content or symlink targets.
Reject symlinks/submodules/type changes, binary source, over-limit source and
unsafe/ambiguous paths (including whitespace trimmed by the shared contract).
Copy detection, undecodable names, Git LFS and rename heuristics remain limitations.
SHA-256 shape is accepted but only SHA-1 fixture repositories were exercised here.

[Python observations](../../../backend/src/smartregression/core/impact/python_snapshot.py)
use stdlib AST without import/exec: qualified symbols with decorator/line spans,
conservative source-span changes and absolute import edges among supplied modules.
Relative/star/dynamic imports are explicitly partial. No call graph, dynamic dispatch
resolution, third-party environment resolution or complete dependency guarantee.
Import reachability is possible influence, not verified impact or safe exclusion.
Syntax errors stop parsing instead of becoming empty successful analysis.

Tests: [Git fixture cases](../../../backend/tests/integration/test_git_local.py),
[AST cases](../../../backend/tests/unit/test_python_snapshot.py). G1 reproduction:
[harness](../../../scripts/g1/README.md). Exact observed results and limits are in
[new handoff](implementation-handoff-20261024.md), not the historical review.md.

This implements the explicit two-SHA fixture subset of [1.06](revision-semantics.md).
It does not accept Q01-Q09 PR policy on behalf of the team. An/Huy should review
PR semantics separately before PR ingestion depends on them.

Sources read 2026-10-24: [Git diff raw/NUL/rename behavior](https://git-scm.com/docs/git-diff),
[Python AST](https://docs.python.org/3.14/library/ast.html). No new public contract,
generated artifact, dependency or product API changed.
