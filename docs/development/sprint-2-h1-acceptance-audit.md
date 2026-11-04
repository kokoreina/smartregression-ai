# Sprint 2 H1 acceptance audit — prompt 7

## Baselines and authority

Audit date: 2026-11-04 (UTC+07). Latest fetched main:
`53356e6ada1a145a3cb988a926928e838136e152`. Separate read-only baseline worktree:
`D:/smart-regression-ai/var/p7-main-baseline`; implementation/audit worktree:
`D:/smart-regression-ai/var/main-review-20261103` on
`fix/sprint-2-h1-acceptance-audit`, based on prompt-6 `f88e823`.
The original checkout and its existing untracked files were not modified.

User assigned execution of prompts 4–7 and commit/push/one PR per prompt, delegating
technical choices. No GitHub approval/merge/deploy or whole-Sprint closure inferred.
Self-review using Reviewer/QA/Backend/Change Impact profiles and routed rules,
TDD/systematic-debugging/security skills; no independent reviewer is claimed.

## Merge status versus verified implementation

| Slice | Source / acceptance evidence | On fetched main? | Result and next action |
| --- | --- | --- | --- |
| 2.14 NativeTestId | `contracts/stages.py`; test_stage_reports native-ID round-trip/nonempty/legacy cases; test_inventory_stage normalization guard | Yes, ancestor `f1dbe2d` verified | Exact whitespace/Unicode/order preserved, duplicates rejected; legacy trimming intentionally unchanged. Reader upgrade/recollection caveats in 2.14 remain |
| 2.20 H1 config/engine/metadata boundary | adapters/storage config/connection, application/run_store, unit metadata and real PostgreSQL tests | Yes; KH foundation/adapter already merged | Default non-DB behavior, sanitized errors, transaction ownership, runtime permissions verified; do not attribute KH's implementation to H1 |
| Initial 2.13 report persistence | application/persistence, composition, CLI; real file/Git/DB cases | Yes, ancestor PR #30 `9bcd6a4` verified | Report-only baseline remains usable; new evidence integration is separate |
| P3 / prompt 3 | accepted spec and decision-register D16 | No: PR #36 OPEN at observation | Design accepted via H1 confirmation; GitHub review/merge separate |
| 2.05 / prompt 4 | [handoff](task-2.05.md), codec/SQL adapter/migration, real round-trip/concurrency/FK/privileges/recovery | No: PR #37 / `e03312a` | Verified on stack, await review/merge; KH shared-schema review pending |
| 2.06 backend / prompt 5 | [handoff](task-2.06.md), source resolution/support/inspection tests and actual frozen Git workflow | No: PR #38 / `1c2e011` | Backend verified locally; source claims rechecked, deterministic static support only. Prompt 6 includes module-span tightening |
| VI 2.06 component / 2.18 | EvidenceItem and StageReportView on main | Yes, PR #34/#35 in main history | Existing UI contribution retained; two confirmed UI findings below prevent claiming complete UI acceptance |
| 2.13 integration / prompt 6 | [handoff](task-2.13.md#evidence-integration), actual producers, compound SQL, smoke/exit/failure tests | No: PR #39 / `f88e823` | H1 integration slice verified; full 2.13 still depends on real retrieval and explicitly configured isolated collection |
| Prompt 7 bounds + audit | Bounded impact expansion and tests below; this report | No, current audit branch | Ready for human review after CI; not silently marked completed on main |

PR #36, #37, #38 and #39 were OPEN with both source CI checks SUCCESS when checked.
PR #39 Linux run `41852996903` explicitly reported **609 passed, 94 skipped**,
one existing warning, on its commit; not evidence for the later prompt-7 diff.
No unrelated open PRs were inspected. Merge ancestors were checked using
`git merge-base --is-ancestor`, not inferred from filenames or branch names.

## Requirement checks on the implementation stack

| Requirement | Authoritative evidence and limits |
| --- | --- |
| Full repo/run/base/target SHA/hash binding | Real SQL tests reject wrong expected snapshot on load and foreign rebound payload on save; validate_artifacts checks nested graph/path/component/evidence references |
| Canonical bounded immutable bundle | Codec tests preserve order/defaults/null/Unicode/escaped NUL, cap and cap+1; PostgreSQL CHECK and codec/hash/corruption/format cases; byte comparison, not digest-only equality |
| Atomicity and retry | Standalone/bound evidence tests; concurrent same/different writes; created_at preserved; actual compound SQL rollback after bundle failure; existing committed data not deleted |
| Commit ambiguity and errors | Safe typed errors for reserved-port connection refusal and DB errors; injected lost ack after real commit, followed by exact load/retry. Not a real network-partition experiment |
| Runtime permissions and recovery | Runtime SELECT/INSERT with UPDATE/DELETE/TRUNCATE/DDL denied; additive migration `_04`, one head; dedicated fresh/upgrade/reapply, exact-row DB/artifact backup/restore and evidence decode/identity passed |
| Resolve source versus support | Frozen-hash verification, base/target rename/delete, spans/symbol/excerpt, Unicode/CRLF/unsupported bytes; arbitrary explanations not certified; importer edges rederived from actual source |
| Immutable inspection | inspect_bundle returns detached evidence; actual DB reload → inspection → bytes/reload unchanged checked in workflow persistence integration |
| Stage/failure semantics | Actual impact/review/evidence, failed dependencies no fabricated bundle, partial omissions/limitations retained, 2.17 unchanged graph-source failures preserved, unsupported retrieval honest |
| CLI/default DB isolation | Default/help/health don't require DB; opt-in flags validated, actual CLI file/SQL flow, stdout/stderr/exit and evidence saved/not-included diagnostics verified |
| Configuration and acquisition | Acquire once; actual manifests/config captured; injected collector digest stable and stored, mutation fails; old absent optional config key preserves canonical bytes |
| Contract/consumer compatibility | Public models/generated artifacts unchanged; exporter/frontend contracts/typecheck/lint/build passed; v1 and exact NativeTestId regressions included. Build does not verify browser behavior |
| No candidate execution on host/web | Frozen source parsed as data; owned fixture contains executable traps but is not imported. Collector remains explicit isolated interface; no new shell interpolation/provider/outcome/fault-label input |

## Confirmed findings and disposition

### Fixed in prompt 7 — bounded impact expansion

Confirmed source: `core/impact/potential_impact.py`, former recursive
`_simple_reverse_paths`. Enumerating all simple paths had no path/candidate bound;
a dense DAG has exponential path count and cycles/depth could exhaust recursion.
P3's serialized-byte cap occurred after producer allocation, so it did not bound
this work. This is a source/algorithm resource issue, not proof of an actual outage.

Agent decision under H1 delegation, 2026-11-04: cap **4,096 path records total across
origins** and **10,000 candidates**, use iterative traversal, and fail explicitly
with impact_path_limit / impact_candidate_limit. No truncated payload is returned
as completed; downstream evidence/review are not_run/dependency_failed. Values
can be reviewed with H2 on representative data; they are protective policy, not
measured optimal thresholds. Internal producer version `bounded-static-impact/1`
records the fixed policy in actual run configuration. Lower optional test budgets
are allowed; raising beyond these caps requires a deliberate version/policy change.

Tests reproduce absence of budget handling, then verify exact small budget,
global exhaustion across origins, dense DAG and candidate exhaustion. Existing
potential-impact tests prove stable semantics/order below bounds. H2 remains producer
owner/reviewer; no new runtime service/dependency/public model or generic framework.

### Fixed in prompt 7 — arbitrary explanations remain unverified

Reproduced an inspection edge case: if recomputed static support was unsupported,
an unrelated arbitrary explanation could inherit that negative verdict. Source
resolution does not justify either positive or negative semantic certification of
unknown prose. Inspection now evaluates support only for the deterministic known
explanation family and matching witnesses. Free-form claims stay unverified;
regression and final unit/DB/full suites passed. Original persisted claims remain
unchanged; this is a transient inspection correction, not an UPDATE of stored data.

### Open VI follow-up — uploaded report validation (P1, confirmed)

Location: `frontend/src/features/reports/stageReport.ts`, validateStageReport,
especially return at line 41. It checks root fields only and casts the object.
Controlled local reproduction transpiled that owned module using existing TypeScript
and invoked its actual validator with:

```json
{"schema_version":"2.0.0","report_id":"audit-fixture","data_kind":"real","identity":{},"stages":{}}
```

UI validator accepted it; actual backend StageAnalysisReport rejected it.
Data path: local uploaded JSON → shallow validator → typed StageReportView/EvidenceItem.
Impact: malformed data can reach unchecked nested accesses and forged saved support
states can appear credible; accepting JSON is not source verification. The UI may
crash on missing nested identity; no arbitrary-code execution claim is made.

VI next action: validate complete v2 shape/state/reference invariants at the upload
boundary, distinguish untrusted saved claims from server/frozen-source inspection,
and cover malformed/forged cases. Runtime schema validation alone cannot certify
source support. This needs a focused frontend/contract change and browser QA;
not rewritten inside H1's backend acceptance task. Human/UI acceptance stays pending.

### Open VI follow-up — displayed run identity (P2, confirmed)

Location: `frontend/src/features/reports/StageReportView.tsx:64` labels report_id as
“Run ID”, although identity.run_id is distinct. Impact: users can copy the wrong
identifier when locating persisted evidence. Use identity.run_id under Run ID and
label report_id separately. No browser verification claimed for this source finding.

### Remaining dependencies, not fabricated successes

Retrieval is still unavailable on main/stack; P5 and H2 producer/config ownership
remain distinct from P3. Default CLI has no configured collector; the explicit
application/composition injection is available, and real candidate → DB inventory
acceptance remains in KH's separate harness. Do not infer selection/execution,
fault detection, benchmark metrics, complete 2.13 or complete Sprint 2.

## Actual verification in this audit

Locked Python/Ruff and MinGit environment match [2.05](task-2.05.md). No clean
dependency installation was claimed. All basetemps/evidence are under project var.

- Main-only baseline: **109 passed** for test_stage_reports, test_run_store and
  test_analysis_workflow, using PYTHONPATH to the separate main worktree. This is
  focused baseline verification, not a full main-suite claim.
- Full final stack: **612 passed, 95 skipped**, one existing Starlette/httpx
  warning, 1404.66s elapsed (not a performance benchmark). Command:
  `python -m pytest backend/tests -q -p no:cacheprovider
  --tb=short --basetemp D:/smart-regression-ai/var/p7-acceptance-publish --junitxml
  D:/smart-regression-ai/var/p7-backend-publish.xml`. XML independently confirms
  707 cases / 0 failures / 0 errors / 95 skipped. Final unit subset: **548 passed**,
  18.74s. Default skips are dedicated DB/candidate
  tests and one Windows-inapplicable POSIX FIFO test, not DB acceptance.
- Fresh dedicated PostgreSQL 17.11: **92 passed, 2 skipped** (KH candidate harness
  only), 38.23s, `python scripts/storage/run_checks.py`. Final evidence:
  ignored `var/storage-verification-fd2539620e3b4588beb4b14a92bd0ba6/evidence.json`.
  Head `_04`, exact backup/restore, artifact/catalog digest, bundle decode and
  exact owned-container cleanup all passed. No production DB touched.
- `python scripts/demo_analysis.py --output D:/smart-regression-ai/var/p7-demo-final`:
  exit 0; actual subprocess CLI thin=1/failure=2/empty=1, canonical bundle captures
  and reload verified; parser never executes fixture modules. Still incomplete analysis.
- Ruff check/format, exporter --check, frontend contracts:check/typecheck/lint/build:
  passed. Frontend 42 modules built; no new browser or production TLS acceptance.
- Actual UI validator controlled reproduction versus backend rejection as above.
  No new dependency or scanner was installed; source/security review is self-review.
- Docs validation: 12 changed Markdown files across the stack, 414 local links/anchors,
  44 tables, fences/UTF-8/whitespace passed; git diff --check passed. Original checkout
  still has only the preexisting untracked outputs/ and start-cliproxy-management.bat.

## Handoff / merge order

Review and merge **#36 → #37 → #38 → #39 → prompt-7 PR**, retargeting dependent
PR bases to main after each prerequisite lands. Do not squash/cherry-pick blindly
across the stack or force-push others' work. Required reviews/checks depend on actual
GitHub settings; no policy changes or auto-merge were made.

H1 storage/backend/integration slices have local/runtime evidence and are ready
for human review, not yet complete on main. After merges, fetch actual main and
revalidate affected gates/AC; this audit does not retroactively attest a future SHA.
VI handles the two frontend findings; H2 retrieval and KH collector/config/harness
follow-ups retain ownership. No need to reselect PostgreSQL or reapprove accepted P3.

OpenAI Codex assisted code/tests/audit/docs/self-review under user delegation.
Human understanding/review, academic acceptance and signatures are not inferred.
No new background service or candidate runner was left; Docker Desktop remains the
user's existing app, dedicated test containers were removed. The main-baseline
worktree and ignored verification artifacts remain inside the project for inspection.
