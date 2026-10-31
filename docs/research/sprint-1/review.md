# 1.12 — Sprint 1 local technical review, 2026-10-31

**NOT READY FOR FORMAL ACCEPTANCE.** The local technical package is prepared and
the executed checks pass. Final human review of this new harness/docs, explicit
acceptance of the bounded G1/candidate/revision design, and integration to main
remain outstanding. This is Codex self-review, not a mentor/team sprint approval.

Scope is the user's current brief: research foundation + technical spike,
1.01–1.12/G1; not production PB01–04/PB23. See [scope/decisions](closeout-decisions.md).
Main observed on GitHub: `e937f669fefada31d5254b355f92f24e88e41725`. Starting local
tree `c3ac49aba58b9f50f933dc0b02aead28ee3d4217` already contains the research/RAG
tree of merged PR #10. Current branch: `work/sprint-1-local-closeout-20261031`.
The technical closeout was prepared without a commit/push/PR merge. A subsequent
user instruction authorizes committing and pushing this branch for manual merge;
main merge remains the user's action. The handoff describes both main-to-delivery
and preparation-session changes; publication does not itself update remote main.

The [original review snapshot](https://github.com/kokoreina/smartregression-ai/blob/e937f669fefada31d5254b355f92f24e88e41725/docs/research/sprint-1/review.md)
and [Huy handoff](huy-handoff.md) preserve historical results. They are superseded
for current status, not rewritten into a record of tests they did not run.

## Task acceptance matrix

`design-ready` means the requested design is supplied; `spike-verified` means the
specified bounded implementation was executed. Neither means formally accepted.

| Task | Required output / current status | Evidence | Remaining acceptance or implementation boundary |
| --- | --- | --- | --- |
| 1.01 | RQs/baselines/formulas/overhead/split: design-ready | [RQ](research-questions.md), [source audit](research-sources-20261024.md), [protocol](../evaluation-protocol.md); includes impact precision/recall | Literature audit is historical limited-section inspection, not a new systematic review or measured model result; #10 content still local relative to main |
| 1.02 | License/history/reproducibility/fault/flaky/infra screening: design-ready | [screening](repository-screening.md), corrected pilot-tuning rule; PR #2 draft reviewed | Final updates need review; target/sampling decisions precede dataset recruitment, not the offline checklist |
| 1.03 | Primary/backup proposal and reproducibility: spike-verified | [candidate reproduction](candidate-reproduction.md): sqlparse 509 stable IDs, TinyDB 228; wheel build, two collections, existing single test and full suite | Owner accepts proposed repositories; xfail/xpass/optional YAML skip retained; no dataset enrollment or historical fault cohort |
| 1.04 | Authorized-identity/access observation prototype: spike-verified as double | [access](repository-access.md), [prototype](../../../backend/src/smartregression/application/sprint1_prototypes.py); tests pass in full suite | Synthetic HTTP statuses exercise classification, not live auth; guide permits doubles; no clone/auth service claim |
| 1.05 | Framework/config/resource constraints: design-ready plus bounded execution | [environment](test-environment.md), [candidate harness](../../../scripts/candidates/README.md), G1 artifacts | Only measured versions/plugins/snapshots; production persistence/general runner outside spike scope |
| 1.06 | Direct pair/PR freeze/evidence rules: design-ready, approval pending | [revision semantics](revision-semantics.md), [Q01–Q10 reconciliation](closeout-decisions.md#revision-semantics), PR #5 | An/Huy and consumers need to accept final semantics; no live PR resolver/race implementation claimed; pending records remain pending |
| 1.07 | Read-only diff/metadata and dependency prototype: spike-verified | [Git/AST spike](git-diff-spike.md), immutable Git fixture tests, [implementation handoff](implementation-handoff-20261024.md), current full suite | SHA-1 fixtures only; incomplete imports explicit; no complete dependency/call graph or verified impact guarantee |
| 1.08 | Run ID/transitions/timestamps/failure/retry semantics: spike-verified in memory | [lifecycle](run-lifecycle.md), prototype tests in current full suite | New UUID on retry and rejected duplicate transitions documented; no durable queue/idempotent submissions/cancel service |
| 1.09 | RAG source/metadata/provenance/secret/leakage scope: design-ready | [RAG scope](rag-scope.md), reviewed historical PR #10 content | New fallback consistency edit needs review; no provider/index/egress implemented |
| 1.10 | Selection invariants/decision table/safety boundaries: design-ready | [policy](selection-policy.md), Proposal §12.6 alignment; invalid evidence uses full-suite/stop, invalid snapshot stops | Final design approval pending; no production selector or empirical recall claim |
| 1.11 | Cohort/split/adjudication/metrics/reporting: design-ready | [protocol](../evaluation-protocol.md), [report template](evaluation-report-template.md); explicit evidence and fallback denominators | Model/budget/sample/repeat decisions needed before corresponding experiment stages; no fabricated benchmark results |
| 1.12 | Current matrix/G1/demo/decisions compiled: local package prepared | This review, [session handoff](closeout-handoff-20261031.md), reproducible commands below | Human review/demo acceptance and integration remain; this document does not accept itself |

## G1 evidence and limits

| Gate | Current-session evidence | Boundary |
| --- | --- | --- |
| One language/framework | ADR 0002 accepts Python + pytest; both candidates support measured Python version | Not universal plugin/version support |
| Frozen snapshot | Synthetic full SHAs and candidate commit/blob verification before materialization | Immutable blob materialization replaces checkout; no filters/hooks or input checkout mutation; reviewer assesses bounded gate equivalence |
| File diff | Add/modify/delete/rename/previous_path, dirty-tree immutable reads and invalid commit tests | Direct two-SHA subset; not live GitHub PR ingestion |
| Dependency/symbol prototype | AST spans/direct symbol edits and absolute module-import edge in G1 | Partial relative/star/dynamic imports; no fault ground truth |
| Discovery | Synthetic 5 IDs; sqlparse 509/TinyDB 228 identical IDs across two collections each | Native IDs bind to materialized target; collection inside offline Docker |
| Selection freeze and single execution | selection.json precedes container start; selected ID setup/call/teardown passed for fixture and both candidates | Fixed smoke choice, not an implemented selector or reduction experiment |
| Guard/error paths | G1 wrong snapshot/unknown ID reject before dispatch; timeout/output cap; empty vs collection error; candidate timeout-cleanup unit test | G1 limit cases synthetic, not hostile-code security proof |
| Cleanup | docker ps queries found no named candidate/G1 containers after runs | Images/artifact directories remain for reproduction |

Current synthetic artifacts: `var/g1-closeout-20261031/selection.json` and
`observations.json`; base `b6354da3ada6e3e79540738fdbf628ea7857ed32`, target
`60e3a7d249db423c91123f3433e02ff5a72ebd96`. Candidate outcomes include sqlparse
506 passed/2 xfailed/1 xpassed, TinyDB 227 passed/1 skipped. These are product test
observations, not verified faults or impact/fault-retention evaluation metrics.

## Human review evidence already present

Queried only merged PRs on 2026-10-31; no open PR was inspected. Recorded approvals
are real GitHub review states on those revisions, not new statements by this agent:

| PR | Review observed | Destination / relevance |
| --- | --- | --- |
| [#2](https://github.com/kokoreina/smartregression-ai/pull/2) | kokoreina APPROVED | main; original 1.02 checklist |
| [#3](https://github.com/kokoreina/smartregression-ai/pull/3) | KaiTrann APPROVED | main; 1.01/1.04/1.08/1.11 initial work |
| [#4](https://github.com/kokoreina/smartregression-ai/pull/4) | kokoreina APPROVED | main; candidate draft |
| [#5](https://github.com/kokoreina/smartregression-ai/pull/5) | kokoreina APPROVED | main; 1.06 draft, not explicit closure of Q01–Q10 |
| [#6](https://github.com/kokoreina/smartregression-ai/pull/6) | kokoreina APPROVED | main; environment/fallback draft |
| [#7](https://github.com/kokoreina/smartregression-ai/pull/7) | KaiTrann APPROVED | main; Python/pytest decision |
| [#9](https://github.com/kokoreina/smartregression-ai/pull/9) | KaiTrann APPROVED | main; Git/AST/isolated fixture |
| [#10](https://github.com/kokoreina/smartregression-ai/pull/10) | KaiTrann APPROVED | feat/s1-git-discovery-spike; RAG/research tree reused locally, absent from remote main |

No approval above covers the new candidate harness or changed closeout documents.

## Demo and completion actions

1. Open the task matrix, decision checkpoints and candidate outcomes; identify
   frozen SHAs and native test IDs before showing outcomes.
2. Re-run [G1 commands](../../../scripts/g1/README.md) with the recorded image and
   a new output directory. Show diff, import edge, inventory, freeze timestamp,
   selected phases and distinct failure/empty/error guards.
3. Use [candidate commands](../../../scripts/candidates/README.md) with new output
   names. Show matching inventories, selection-before-execution and actual outcome
   categories; do not call them model-selected tests.
4. Review new code/docs and explicitly record whether bounded revision/G1 and
   candidate proposal is accepted. Reviewers must be real people with actual decisions.
5. Authorized maintainer integrates the complete local diff into main and verifies
   CI at the resulting commit. No GitHub action is performed by this task.

Workbook `Sprint 1 Backlog!F8:F19` still says Not started; H/J values are zero.
Suggested tracking update is “technical work supplied, awaiting review/acceptance”
with links to this matrix; 1.06 keeps its policy-decision caveat and 1.12 awaits
acceptance. Do not enter Done/Completed hours from a passing suite. Actual effort
is unknown. The Office workbook was only read; formulas/estimates unchanged.

Codex assisted local implementation, tests, debugging, source inspection, integration
preparation and this self-review. Humans must understand and review their adopted
work. No mentor approval, signature or contribution percentage has been invented.
