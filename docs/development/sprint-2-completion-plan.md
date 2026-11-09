# Sprint 2 completion — integration and acceptance

## Baseline and authority

Verified 2026-11-09: fetched `origin/main` is
`3ab7d6603a191e46ce86d3ca04ffb520374bc639`. Work starts in a separate
`work/sprint2-completion-20261109` checkout. The original workspace's renamed
Architecture/workbook and other untracked files are preserved.

Nguyễn Tấn Huy authorized the agent to execute all seven completion prompts,
including the other members' remaining implementation, local Docker/PostgreSQL/
browser checks and scoped commit/push/PR publication. Historical authorship stays
intact. Technical choices within Sprint 2 no longer wait for the old module owner.
This is not independent review, mentor approval or permission to bypass GitHub
rules. No merge is performed by this sequence.

Requirements remain the [team guide](sprint-2-team-guide.md#tasks), the tracked
workbook `Sprint 2 Backlog!B8:G27` and briefs `B55:Z173`,
[P3](task-2.05-p3.md), [P5](../architecture/decisions/0003-local-lexical-retrieval.md)
and [ADR 0004](../architecture/decisions/0004-sprint-2-integration-decisions.md).
Workbook progress is not acceptance evidence: tracked rows are all Not started;
the separately edited local workbook marks only 2.02/2.13/2.18 Ongoing. Neither
represents the actual missing integrations below. Estimates remain forecasts.

## Verified reconciliation

GitHub PRs 50–53 are merged **into feature branches**, not main. Commit ancestry
and main source confirm that their workflow/mapping/retrieval/UI changes are still
absent. PRs 54/55 are on main and add newer integrity tests and index persistence.
Do not replace these with an older branch tree.

| Reusable change | Commit | Reconciliation requirement |
| --- | --- | --- |
| Impact, verified evidence, compound persistence | `e488ebf` | Preserve newer inventory/integrity tests and existing EvidenceStore; align ordering entrypoints |
| Inventory/mapping sidecar | `34f1320` | Preserve exact native IDs, receipt guards and newer collector; no host execution |
| Actual lexical retrieval | `2f5c517` | Reuse core algorithm; reconcile competing index storage with main verified publication |
| UI validation and inspection | `a5f9123`, `2ee6886` | Preserve canonical schema; verify backend semantic parity and actual browser flow |
| Physical offsets and restart checks | `4c5a624` | Port affected optimization without dropping main exclusions/recovery tests |
| Historical runtime checkpoint | `a2692f0` | Reference only; it explicitly leaves browser A07 unverified |

Main has `20261105_05` index metadata migration. The older lexical implementation
also claims revision `20261105_05` for a different schema. Never overwrite that
applied revision or blindly cherry-pick the whole old stack. Prefer the main index
store/artifact protocol for the lexical backend; add a forward migration only if
an actual missing storage requirement is proven. One migration head is required.

## All twenty tasks

AC below summarize, not replace, the linked guide/workbook requirements. Existing
module tests and historical runtime records are evidence for their own revision,
not a pass for the final combined implementation.

| Task | Required behavior | Main evidence / gap | Completion prompt and gate |
| --- | --- | --- | --- |
| 2.01 | Add/modify/delete/rename, base/target locations, unsupported limits | `application/changed_components.py`, existing location/integrity tests; keep producer | 2/6: regression with frozen sources, A01/A04 |
| 2.02 | Independent expected locations and mismatch records | Actual producer/oracle reconciliation exists, PR 32 merged; local Ongoing stale | 6/7: verify oracle coverage and synchronize status |
| 2.03 | Supported graph direction, endpoints and unresolved imports | `core/impact/dependency_graph.py` exists | 2/6: graph semantics and propagation, A02/A03 |
| 2.04 | Reverse impact, cycles, deterministic paths | `potential_impact.py` exists; absent in default workflow | 2: actual wiring and bounded traversal, A01/A03 |
| 2.05 | Immutable evidence round-trip, identity and surfaced failures | PostgreSQL EvidenceStore exists; compound flow absent | 2/6: real DB atomicity/read-back, A04/A06 |
| 2.06 | Supported explanations and verified source references; reused UI | Resolver and EvidenceItem exist; producer absent from workflow | 2/5: source resolution, immutable re-inspection and browser |
| 2.07 | Stable changed/direct/indirect ordering, limitations | Multiple ordering paths disagree on empty-edge semantics; workflow not_run | 2: convergence tests and wiring, A02 |
| 2.08 | Isolated target inventory, receipt/config, durable storage | Collector/domain DB and candidate evidence exist; CLI not configured | 3/6: real collector and candidate-to-DB, A05/A06 |
| 2.09 | Empty/partial/failed/timeout distinct; native IDs | Existing collector/contract coverage; keep through integration | 3/6: negative runtime cases, A03/A05 |
| 2.10 | Excluded inputs, provenance chunks, verified ready index | Main acquisition/publication/index storage exists; automatic chunker absent | 4: reconcile lexical build with main storage, A04/A06 |
| 2.11 | Change-relevant search, correct frozen sources, no leakage | `context.py` constructs metadata only; lexical path absent | 4: actual bounded search, A01/A03/A04 |
| 2.12 | Rank/ties/dedup with provenance, exact-byte validation | `ranked_context.py` exists; actual retrieval consumer absent | 4/6: validated actual search results |
| 2.13 | Application/CLI incremental workflow, honest reports and reproducible demo | impact/evidence/retrieval not_implemented; inventory/ordering not_run | 2–6: integrated report and correct exit semantics, A01–A07 |
| 2.14 | Versioned identity/stage contracts without fake selection | v2/native-ID contracts and trusted acquisition exist | 2–6: preserve schemas or regenerate if justified; consumer checks |
| 2.15 | Authorized frozen snapshots, revision and worktree isolation | Existing acquisition and tests | 2/4/6: retain trust boundary, A04 |
| 2.16 | Component-to-existing-test mapping with inventory guards | Mapping API exists; run-bound sidecar absent in default flow | 3: receipt/identity-bound publication, A05 |
| 2.17 | Accurate scope, exclusions and limitations through consumers | Current stages covered; new stages need wiring | 2–6: failure/partial propagation and UI, A02/A03 |
| 2.18 | Validated real report loading, identity/states/navigation | Top-level-only validator; Run ID uses report_id; browser incomplete | 5: schema/semantic fixes and actual browser, A07 |
| 2.19 | Cross-module identity/failure regressions | Main has AN/KH suites; final integrated campaign missing | 6: complete A01–A07 campaign |
| 2.20 | Bounded PostgreSQL foundation, migrations, constraints and recovery | Foundation/domains exist; historical real-DB verification | 2–4/6: combined workflow, populated upgrade/restart/restore, A06 |

## Decisions and implementation order

Huy is accountable for this completion effort; previous member contributions are
not reassigned retroactively. The agent is the sequential writer for shared
workflow/contracts/migrations. Use PostgreSQL/Core/psycopg/Alembic, local structural
+ lexical retrieval, existing Python/pytest authorization and file-report UI.
Live LLM, embeddings, vector DB, new API analyze/auth/queue and production general
runner are outside these completion criteria.

1. **Reconciliation:** this plan, workbook/source inspection and ancestry checks.
   Documentation-only checks; no false fresh runtime claim.
2. **Core workflow:** port/reconcile `e488ebf`; resolve ordering divergence;
   focused regression plus dedicated PostgreSQL compound checks before publication.
3. **Inventory/mapping:** reconcile `34f1320`; run actual isolated discovery,
   mapping/sidecar and candidate-to-DB checks before publication.
4. **Retrieval:** adapt old lexical core to current publication/storage; preserve
   configured budgets and exclusions. Real DB/candidate/restart/restore checks.
5. **UI:** reconcile old consumer fixes; validate report semantics and real browser
   load/error/recovery/keyboard/narrow viewport. SSR is not A07.
6. **Acceptance:** final baseline, focused failures and full relevant regression,
   dedicated runtime gates, all AC traced to actual evidence. Fix defects in scope.
7. **Closeout:** update only drifted docs/Office/statuses with verification and
   preserved unrelated content. Distinguish technical verification, review and merge.

Publish each reviewable passing slice. Later branches may depend on the previous
slice while reviews are pending; every PR must state its base. No force push or
merge-protection change. Keep a single evolving completion record here.

## Acceptance matrix

| Gate | Required evidence on final integrated baseline | Current checkpoint |
| --- | --- | --- |
| A01 | Controlled complete fixture and authorized actual candidates; actual producers, source identities and report/artifact digests | Controlled eight-stage producer fixture passes with declared Git/collector/metadata doubles; both real candidates pass actual CLI/SQL with truthful partial limits |
| A02 | Docs/config/no-change/no-edge expectations, all paths retained; report/browser semantics | Backend/SSR checks pass; browser part awaits A07 |
| A03 | Partial, unresolved, build/query/runner budget failures propagated; no successful-empty substitution | Default, actual candidate/CLI failure, isolated Docker and SSR checks pass; browser recovery awaits A07 |
| A04 | Wrong repo/run/revision/snapshot/config/version, forged/tampered bytes/ranges/metadata rejected | Default suite, warm-cache guards, real SQL and Docker integrity checks pass |
| A05 | Isolated inventory, exact IDs, receipt/membership guards and matching mapping artifact; dedicated DB checks | Both actual candidates and runtime integrity/SQL checks pass |
| A06 | Real PostgreSQL transactions/concurrency/ambiguous commit; restart and consistent nonempty metadata/artifact restore | Final 131-case SQL campaign, restart/re-query and populated restore pass |
| A07 | Actual browser file load, malformed nested rejection/recovery, identity/provenance, states, keyboard/focus and narrow viewport | Unverified; Browser connection unavailable |

Use existing scripts and [verified commands](verified-commands.md), inspecting
their coverage before claiming a gate. Unit/mock passes and opt-in skips do not
replace runtime verification. Keep failed-run evidence and record exact environment
and source. Input code executes only in approved isolated runner containers.

## Execution record

- Prompt 1: source/ancestry/workbook reconciliation complete; plan links, 20 task
  rows, fences and diff checked before publication. No product change or new runtime result.
- Prompt 2: implementation reconciled from `e488ebf`, retaining current main
  storage/inventory/integrity changes. New raw/stage/impact no-edges regression
  initially failed twice; fixed inference to preserve only producer-confirmed
  partial_graph. Legacy tests updated to accepted ADR behavior, not weakened.
  Public schemas, generated types, dependencies and migrations are unchanged.
- Prompt 2 real DB: `scripts/storage/run_checks.py`, Python 3.14.3,
  PostgreSQL 17.11 pinned image, **112 passed / 2 candidate-to-DB skips**.
  Evidence `var/storage-verification-264a0d70129743ca89e327f87ca04f9e/evidence.json`
  verifies fresh/populated head, compound writes/rollback, evidence round-trip,
  backup/restore and index/artifact catalog consistency; owned container removed.
  The two candidate skips are assigned to Prompt 3, not counted as DB acceptance.
- Prompt 2 CLI demo: `scripts/demo_analysis.py --output <new-task-output>` exits 0;
  individual thin/failure/empty analyses exit **1/2/1**, preserving partial states.
  This is labelled DEMO, not full pipeline acceptance. Ruff lint/format and schema
  exporter `--check` pass. Full backend regression: **814 passed, 115 skipped,
  1 existing warning**, exit 0, 483.54s. Skips: 114 dedicated PostgreSQL cases
  (112 passed separately above, two candidate cases assigned to Prompt 3) and
  one POSIX FIFO case unavailable on Windows. JUnit/logs are retained under
  the ignored task artifact directory; no default-suite skip is counted as a pass.
- Prompt 3: mapping changes reconciled without replacing current main collector
  or storage. Explicit CLI candidate/image/workspace/root opt-in uses the trusted
  source-checkout observer and approved targets. Default execution remains read-only.
  Inventory is persisted with report/evidence in one SQL transaction; a test-case
  insertion failure must roll back the catalog/evidence/inventory together.
  CLI argument regression initially **8 failed**; PostgreSQL regression initially
  **1 failed / 112 passed / 2 skips**, proving inventory was absent after report
  persistence. Both failures drove the scoped implementation rather than weaker gates.
  Unit/CLI/mapping campaign: **699 passed, 1 existing warning**, exit 0.
  First real candidate collection reproduced **509/228** native IDs; actual CLI
  mapping passed both candidates with truthful partial exit 1. A failed CLI attempt
  using a historical image ID was retained; Docker confirmed it did not exist,
  and using the actual locally inspected image resolved the infrastructure failure.
  Full backend regression: **838 passed / 119 skipped / 1 existing warning**,
  exit 0, 668.46s. The skips are 118 dedicated PostgreSQL cases and one POSIX FIFO
  case unavailable on Windows; no skipped case is counted as acceptance.
  Docker failure fixtures: **12/12 passed**, including native Unicode/long IDs,
  empty/partial/failure, duplicate, timeout/output cap and malformed payloads.
  Combined runtime wrapper reached the SQL campaign but its old 180s whole-suite
  timeout terminated the expanded campaign. The harness now uses a bounded 600s
  whole-suite deadline and records timeout failures explicitly; individual 60s
  collection and DB timeouts are unchanged. Final SQL rerun: **118 passed / no
  skips**, exit 0, 282.41s. Includes actual CLI → approved Git/Docker collection →
  mapping/file publication → runtime-role report/evidence/inventory read-back for
  both candidates, plus inventory insert failure rolling back the whole SQL write.
  Final harness `var/storage-verification-96bd75c3678b47ad8f6c5d495c454c68/evidence.json`
  passed fresh/populated head, exact-row backup/restore, decoded evidence identity,
  nonempty index metadata/chunk/artifact restoration and owned-container removal.
  Candidate evidence: `var/candidate-inventory-verification-a3a2a9bfb3f346b7b107af1d9e5bbd21/evidence.json`;
  CLI mapping: `var/mapping-workflow-265465fe7bde45cda435eaf8803aaa2d/evidence.json`;
  Docker fixtures: `var/inventory-verification-80b4c88ace0147478b2b05d6aeb561f4/evidence.json`.
  Ruff lint/format, schema exporter, plan links/fences and diff checks pass.
  Public schemas, generated files, dependencies and migrations remain unchanged.
- Prompt 3 publication: commit `6199de2`, PR #59 targeting #58's branch.
  Both GitHub source CI runs succeeded (`42551658602`, `42551651535`).
- Prompt 4 is in progress on `feat/s2-completion-retrieval`. The historical lexical
  algorithm is adapted to the existing `IndexConfiguration`, current whole-file
  exclusions and main `index-artifact/1` publication/ready store. No old lexical
  migration/schema is imported. Trusted acquisition is repeated before ready reuse;
  terms/symbols are deterministically rebuilt from verified source bytes.
  Physical offsets are reused within an operation without a global source cache.
  CLI opt-in is `--index-artifact-root <existing-root>` together with persistence;
  the captured run configuration includes the actual retrieval config digest.
  Focused pure/publication/workflow/configuration checks: **109 passed**, exit 0.
  Unit campaign: **697 passed**, exit 0; acquisition/publication/CLI integration:
  **58 passed**, exit 0, one existing warning. Actual candidate SQL campaign then
  reproduced **2 failures / 117 passes**: both candidates truthfully exposed
  `lexical_query_timeout`. Repeated per-blob Git processes during re-verification
  consumed the unchanged 5s query budget. A bounded (64 MiB maximum), command-local
  immutable-object cache is enabled only for CLI retrieval. Each cached blob's Git
  hash/size is verified; caller byte bounds and fresh commit/root/tree acquisition
  still apply. Cache regression was **7 failed** before implementation; subsequent
  cache/lexical/workflow/persistence subset **34 passed**, exit 0. No budget is
  increased and no ready/source/artifact gate is removed. Full backend after the
  fix: **867 passed / 120 skipped / 1 existing warning**, exit 0, 422.11s. Skips
  are 119 dedicated SQL cases plus Windows FIFO; the dedicated SQL rerun then
  achieved **119 passed / no skips**, exit 0, 251.31s, including actual retrieval
  for both candidates. Its later restart probe exposed a harness reconnect bug:
  Docker Desktop changed the ephemeral loopback port. A dedicated owned-container
  reproduction confirmed this (`65019` → `65027`, cleanup true). The harness now
  re-reads loopback bindings from the exact labelled container after restart,
  preserves DB settings and compares all populated rows before lexical re-query.
  Final harness `var/storage-verification-f15208305d5f40b3a7499f288bbd548d/evidence.json`
  passed: **119 SQL tests / no skips**, 169.15s; fresh/populated head, exact-row
  restart comparison, actual lexical query after PostgreSQL restart, exact-row
  backup/restore, evidence decoding, nonempty index metadata/chunk/artifact restore,
  actual lexical query after restore and owned-container cleanup. The harness was
  rerun after its port fix; product source is unchanged from the full regression.
  Ruff lint/format, exporter, plan consistency and diff checks pass. Public schemas,
  generated files, dependency/lockfiles and the single migration head are unchanged.
- Prompt 4 publication: commit `bd659be`, PR #60 targeting #59's branch. Both
  GitHub source CI runs succeeded (`42554303258`, `42554297771`).
- Prompt 5 source work is on `feat/s2-completion-report-ui`, not yet published.
  Nested validation uses the generated canonical schema plus cross-field checks;
  report loading is bounded to 16 MiB, 250,000 schema visits and depth 64. Native
  test IDs remain exact; metadata follows the backend Unicode whitespace policy.
  Run ID and Report ID are distinct, retrieval provenance is inspectable, changed
  docs/config paths remain visible and stale asynchronous loads cannot replace a
  newer request. Actual P4 sqlparse/TinyDB reports passed **87 validation checks**
  and **13 server-rendered checks** (including two actual reports). All **71**
  rejected mutations were independently rejected by backend `StageAnalysisReport`.
  SSR exposed a misleading successful-empty message for partial retrieval: the
  focused test failed, the wording was corrected and the test passed. Canonical
  contracts check, ESLint and production build/typecheck exit 0. Reused Node/npm
  dependencies; no lockfile/dependency/public schema changes.
  Source checkpoint `18e14c9` is published as Draft PR #61, base #60; this does
  not close Prompt 5 or imply browser acceptance.
  Both source CI runs succeeded (`42561543624`, `42561535127`); neither runs A07.
  **A07 remains unverified:** Browser host is unavailable; native Chrome navigation
  was stopped by the tool because URL permission could not be verified. Opening
  Chrome did not restore that connection. SSR/HTTP checks do not replace A07;
  browser load/error/recovery, keyboard and responsive checks remain required.
- Prompt 6 independent acceptance work continues while A07 awaits the external
  browser connection. The suspected overlap race is now **confirmed** on real
  PostgreSQL: a report-only transaction paused after its absent-bundle read and
  a concurrent compound/standalone bundle writer both saved incompatible graphs.
  Red run: **2 failed / 2 passed**, harness
  `var/storage-verification-608545c9cac247c497372ea733ca24c8/evidence.json`.
  A lock alone cannot reject a contradictory writer arriving later. Under Huy's
  delegated technical authority, add forward revision `20261109_06` after the
  unchanged `20261105_05`: insert-only `run_stage_payloads` records canonical
  SHA-256 fingerprints for the four core bundle stages, scoped to repository/run.
  Report and evidence writers claim the same keys in their existing transaction;
  stable claim order, unique constraints and committed-byte comparison arbitrate
  overlap. Runtime needs SELECT/INSERT only; no UPDATE/DELETE or public DTO change.
  Missing legacy claims are not guessed from a different report: exact immutable
  report replay can seed its own claims; other legacy overlap fails explicitly
  until reconciled. No existing migration, report body or historical data is
  rewritten. Forward-only rollback requires a consistent metadata/artifact backup.
  Initial fix checks: **33 focused unit tests passed**; all four controlled
  concurrent SQL cases passed, fresh-head/restart/restore and owned cleanup passed
  in `var/storage-verification-e5e5bf6e35c8407e9d22d0148ca0dc4f/evidence.json`.
  Expanded PostgreSQL run: **129 passed / no skips**, 257.12s, including both
  actual candidate CLI cases, legacy exact replay/rejection, runtime permissions,
  fresh head, exact-row restart, lexical re-query and populated backup/restore.
  Evidence: `var/storage-verification-d9d059c43d754c06be48e3f0459dd152/evidence.json`.
  A supplemental populated `20261105_05` ? head upgrade/replay test then passed
  (**1 passed / 129 deselected**) with exact existing rows preserved, no inferred
  claims, idempotent upgrade and explicit exact-report replay. Its first fixture
  attempt incorrectly rolled back the migration with its enclosing read transaction;
  making that fixture transaction owner explicit resolved the setup failure.
  Evidence: `var/storage-verification-703d531643644497966a00f9a2ab602b/evidence.json`.
  Full backend first run: **871 passed / 130 skipped / 2 failed**, 496.24s; the two
  failures were schema-inventory/head assertions still expecting revision 05. Those
  assertions now include the new table/PK/FK and unchanged ordered prior revisions;
  focused rerun **2 passed**. The isolated real-Docker integrity campaign achieved
  **26 passed**, 357.93s, with worker cleanup assertions; its SQL boundary is a
  recording port, not a substitute for the dedicated PostgreSQL campaign.
  Evidence: `var/i-f292955f2a1f4f90abb055fccb857862/evidence.json`.
  A new compatible-writer interleaving check exposed a READ COMMITTED observation
  race in the initial legacy guard (**1 failed / 130 deselected**): selecting
  claims before reports could mistake a newly committed compatible report for
  legacy data. Reports are now materialized before reading claims; no isolation
  gate or lock timeout was relaxed. The expanded SQL campaign and default full
  rerun are in progress. An earlier focused attempt had an infrastructure-only
  `postgresql_fixture_not_ready` failure and verified owned cleanup; its case did
  not run and is not counted as a product failure or pass.
  The controlled pipeline explicitly verifies all eight completed stages; its Git,
  collector and metadata ports are declared doubles, distinct from the actual
  candidate SQL campaign. Warm-cache authorization/revision/size guards passed in
  that default campaign. Neither Prompt 6 nor final acceptance is yet closed.
- Prompt 7: pending final evidence and targeted Office/document reconciliation.
- AI assistance: OpenAI Codex reads/reconciles, implements and self-reviews under
  Huy's instruction. Proposal Appendix C/D remains applicable; Huy retains
  responsibility for understanding and verifying the contribution. No fabricated
  authorship ratio, independent approval or mentor sign-off.
