# 1.01 - Research questions

Draft by Nguyen Tan Huy; proposed reviewer: Dang Dai Viet. Scope comes from the
[Sprint guide](../../development/sprint-1-team-guide.md). No measured research results.
Primary literature verification update is linked below.

| RQ | Comparison | Measures |
| --- | --- | --- |
| RQ1 | Selection versus full suite | Planned/dispatched reduction, end-to-end saving |
| RQ2 | Retain independently verified faults detected by full suite? | Fault retention, missed faults |
| RQ3 | Explanations tied to correct snapshot and supporting evidence? | Evidence validity and semantic correctness |
| RQ4 | Contribution of retrieval? | Paired hybrid versus hybrid no-RAG, quality/cost/fallback |
| RQ5 | Correctly identify affected functions/methods? | Impact precision/recall against independent labels, not dependency reachability |

## Proposed baselines (not implemented or approved)

- Full suite: execute all target inventory IDs; no selection stage.
- Dependency-only: structural dependency policy from An; partial parsing must not imply safety.
- LLM-only: allowed diff/local context, without dependency selector/retrieval; same ID/evidence validation.
- Hybrid: combine D/M/L under Khanh's policy; define D and M before experiments.
- Hybrid no-RAG: same hybrid/model/prompt/budget/validator, disable retrieval;
  report actual token/context differences. This is not automatically LLM-only.

Same commit pairs, inventory, environment and comparable budgets across methods.
Freeze heuristic/model/prompt/fallback before held-out data; do not weaken baselines
post hoc. See [protocol](../evaluation-protocol.md#metrics) for denominators.

## Hand calculations - illustrative only

Inventory 10, selection 4: planned reduction = 1-4/10 = 0.6. Fallback dispatching
all 10: dispatched reduction = 0. One fault A causes three test failures and B one;
selected catches A only: retention = 1/2, not 3/4. Full time 10, method time 12:
saving = -0.2. Zero denominator means N/A; missing observations stay null.
These checks are not benchmarks or automated metric implementation tests.

## Split and threats

Separate pilot/tuning from held-out by time/repository. Keep the same fault/fix and
near-duplicate changes out of both splits. Freeze split and artifact hashes before
tuning; exclude labels, full-suite outcomes, future commits and evaluator artifacts
from selector/retrieval. Count overhead including analysis and validation.
Threats: small repository cohort, survivorship bias, flaky tests, cache/warm-start,
model nondeterminism, subjective evidence rubric and omitted indexing costs.

Pending: Viet supplies candidate reproducibility/cohort evidence; An/Khanh supply
input-version/plugin and dependency support evidence. Python/pytest is accepted
by ADR 0002. The new RAG scope awaits owner/reviewer feedback; Huy coordinates
team decisions on sample size, budget, repeats and rubric.
Primary literature was checked in the network-authorized integration task:
[research sources](research-sources-20261024.md). This does not validate our method.
