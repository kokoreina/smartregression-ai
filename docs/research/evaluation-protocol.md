# Evaluation protocol - Sprint 1 draft, no results

Writer: Nguyen Tan Huy (1.11); proposed reviewer: Dang Dai Viet. User authorized
this draft update; team approval of experiments is pending. Sources:
[rule 11](../rules/11-research-evaluation.md), [Sprint guide](../development/sprint-1-team-guide.md),
[RQs/baselines](sprint-1/research-questions.md). No external citations verified offline.

## Manifest, cohort and split

Unit: repository identity + frozen base/target SHA + environment + target inventory.
Record license/permission/provenance, pair ID, split, inventory IDs/hash, framework,
config/tool/model/prompt/retrieval version, seed/budget and protocol revision.
Evaluator-only artifacts store fault IDs/provenance separately from selector inputs.
A failing test is not a verified fault label.

Viet proposes screening/candidates; team confirms before sampling. Separate pilot/
tuning and held-out by time/repository; group the same fault/fix and near-duplicate
changes within one split. Freeze manifests, eligibility/exclusions, baselines,
heuristics/model/prompt and metrics before runs. Sample size, repeats, budget and
split boundaries pending. Targets are not collected samples. Preserve excluded
pairs with reasons to expose selection bias.

## Leakage boundary and execution order

1. Authorize repository; resolve immutable SHAs under approved revision semantics;
   discover target inventory.
2. Selector sees only permitted diff/source/evidence snapshot and inventory. No
   labels, full-suite outcomes, future commits or evaluator artifacts in retrieval.
3. Validate IDs/evidence and freeze selection/fallback/config/hash/time in an
   immutable artifact BEFORE execution or joining outcomes.
4. Future isolated worker runs selected/full suites with same commit/environment;
   record actual dispatched IDs, timestamps, exit status, limits and cache state.
5. Separate evaluator joins outcomes to independent ground truth and audits order.

No worker/benchmark implemented here. Repository access is not permission to execute
its code. Index must be scoped by repo/SHA and exclude secrets/evaluation labels.
No source egress authorized. Repository comments cannot change tool policy.

## Baselines and fairness

Full, dependency-only, LLM-only, hybrid and hybrid no-RAG are defined in the RQ draft.
Same inventory/cohort/commits/environment and declared comparable budgets. No-RAG
keeps other hybrid parts fixed; disclose context/token changes. Do not silently
replace a failed provider/baseline. Record planned selection separately from actual
full-suite fallback dispatch. Discovery failure differs from empty inventory;
neither proves safety. Stop/fallback production policy awaits Khanh's 1.10.

## Ground truth and eligibility

Real fault requires fault ID/provenance and independent review; an issue or test
failure alone is insufficient. Mutation needs operator/seed/mutant identity and
predeclared equivalent-mutant policy. Report real and mutation separately. Multiple
failing tests for one fault count as one fault. Flaky handling needs repeat and
adjudication policy before execution. Setup/build/network/timeout/crash are infra or
inconclusive, never confirmed fault detection.

Every attempted run enters a ledger, including failed/excluded. Retention uses
paired runs with comparable full/selected verdicts and verified ground truth.
Method errors remain visible via failure rate and missing cohort coverage; do not
claim dataset-wide retention from successful subset. Methods must not compare
different eligibility cohorts. Full suite detecting no fault does not yield 100% retention.

## Metrics

I: common inventory; S: valid selected IDs; A: actual dispatched IDs; F: independently
verified fault IDs detected by full suite in paired eligible cohort; F_S: faults in
F detected by selection under identical adjudication.

| Metric | Numerator / denominator | Zero/unknown policy |
| --- | --- | --- |
| Selected fraction | abs(S)/abs(I) | empty I -> N/A |
| Planned reduction | 1-abs(S)/abs(I) | empty I -> N/A |
| Dispatched reduction | 1-abs(A)/abs(I) | empty I -> N/A; not completed-test count |
| Fault retention | abs(F_S)/abs(F) | empty F -> N/A |
| Missed fault rate | abs(F minus F_S)/abs(F) | same F/cohort; empty F -> N/A |
| Time saving | (T_full-T_method)/T_full | zero T_full -> N/A; keep negative values |
| Fallback rate | fallback runs / attempted selection runs | zero attempts -> N/A |
| Valid-ID rate | unique proposed IDs in I / unique proposed IDs | empty proposals -> N/A; duplicates separately |
| Evidence correctness | rubric-confirmed references / reviewed references | no review/zero -> N/A |
| Method failure rate | method-error runs / attempted method runs | zero -> N/A |

T_method includes preprocessing, per-change indexing/retrieval, LLM, validation,
execution and report. T_full uses equivalent common preparation/report boundaries.
Record stages separately; avoid double-counting concurrency. Initial index cost
reported separately; amortize only with predeclared reuse count/assumptions. Split
cold and warm cohorts. Unknown time/cost/usage remains null, not zero. Price and
usage must be verified when live evaluation is authorized; none measured here.

Report per-pair/per-repo and macro mean over eligible ratios; micro uses summed
numerators/denominators on the same eligible cohort (micro reduction:
1-sum(abs(S))/sum(abs(I))). Do not turn N/A into zero. Report eligible/attempted/
excluded counts per metric, distributions and uncertainty. Statistical interval,
repeat count and resampling unit must be chosen before runs, not after results.
Proposed evidence rubric separates repo/SHA/path/range existence from semantic
support; independent reviewers adjudicate disagreements with recorded reasons.
Hand calculations in RQ cover zero denominators, duplicate fault failures,
fallback and negative savings; not a metric implementation or benchmark.

## Pending owners and reporting

| Input | Proposed supplier | Unblocking evidence |
| --- | --- | --- |
| License/candidates/cohort | Viet -> Huy | reviewed manifest |
| Language/framework/revisions/dependency | An/Khanh -> team | spike + decision |
| Isolation/environment/flaky/fallback | Khanh | 1.05/1.10 and G1 |
| RAG scope and leakage review | Pham Phan Hoang Huy | 1.09 handoff |
| Sample/budget/repeats/rubric/statistics | Huy coordinates team | recorded pre-run decision |

Use [report template](sprint-1/evaluation-report-template.md), retain exclusions,
protocol deviations, replication commands and redacted artifact references.
Threats: sampling bias, flaky tests, small cohort, model nondeterminism, cache state,
subjective rubric and indexing cost. No benchmark command/dataset/results supplied.
Codex assisted draft/self-review; Huy must understand/verify before adoption and
Viet must independently review. No human approval/signature/contribution estimate assumed.
