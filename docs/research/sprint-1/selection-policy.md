# 1.10 Conservative selection and fallback policy

Integration note 2026-10-24: [RAG scope](rag-scope.md) supplies the missing metadata/
leakage design dependency. G1 guards validate snapshot/ID membership and distinct
empty/error discovery on synthetic fixtures; this policy itself remains a proposed
design, not a production selector or approved fallback decision.

Prepared for Tran Hung Khanh, 2026-10-24. PB22 design deliverable, not a production
selector implementation. Proposed reviewer: Pham Phan Hoang Huy. Sources:
[rule 09](../../rules/09-impact-selection.md), [environment](test-environment.md),
[evaluation protocol](../evaluation-protocol.md), [RAG boundary rule](../../rules/08-llm-rag.md).
Policy below is proposed for review, not a claim that group/mentor approval exists.

## Inputs available before execution

- T: complete framework-native test inventory at the frozen target commit.
- D: existing target tests selected by dependency analysis, with recorded provenance.
- M: added/modified/renamed target tests identified by the change mapping. A deleted
  test at base is not a runnable target ID; missing mapping makes analysis partial.
- L: LLM-added candidates validated against T and supporting snapshot evidence.

An supplies immutable revisions/diff and structural limitations. Discovery supplies
T, adapter/framework version, completeness and inventory hash. RAG supplies permitted
source/test/document references with repo/SHA/path/range provenance. Source text and
LLM output cannot change the host's policy. Full-suite outcomes, fault labels,
future commits and evaluator-only artifacts are never selector inputs.

## Set invariants

S = (D ∪ M ∪ L) ∩ T. Persist not-selected = T minus S.

LLM can add but cannot remove D or M. Intersection is not permission to silently
drop unknown IDs: validate D/M membership first, record invalid L, then apply the
decision table. Unknown/duplicate IDs, invalid evidence and partial inputs require
explicit handling. Preserve exact parameterized nodeids; deterministic ordering
follows inventory order. Selection changes membership; prioritization is separate.

For a complete classified inventory: selected and not-selected are unique,
disjoint, and their union equals T. Every decision has a reason, evidence IDs when
applicable, target SHA, inventory/config/policy version/hash and fallback mode.
Public report schema cannot express all these fields yet; keep internal spike
metadata separate and propose a contract task before changing models/generated files.

## Proposed decision table

| Condition | Selection mode / action | Recorded reason |
| --- | --- | --- |
| Complete T, complete D/M, all proposed IDs and evidence valid | hybrid: use S | dependency / modified / validated LLM provenance |
| LLM timeout, malformed output, invalid evidence or unknown L ID; D/M complete and valid | dependency_modified: discard the entire untrusted L contribution; use D ∪ M | llm_unavailable or invalid_llm_evidence; record rejected IDs safely |
| D or M contains ID absent from T; mapping stale or wrong SHA | stop | invalid_required_mapping; do not erase required tests by intersection |
| Parser/dependency analysis partial, unsupported production code, changed build/config/dependencies | full_suite if T complete and environment is executable; otherwise stop | incomplete_analysis / configuration_change |
| Rename/delete cannot be mapped reliably | full_suite if T complete; otherwise stop | incomplete_change_mapping |
| Discovery failed or inventory is partial/unknown | stop | discovery_failed / incomplete_inventory; T is not trustworthy |
| Successful discovery produces T = empty | stop as no_tests | empty_inventory; no claim of zero regression risk |
| S = empty with nonempty T and no verified exclusion policy | full_suite | empty_selection; absence of candidates is not evidence of safety |
| Wrong repository/commit provenance or unverifiable snapshot | stop | invalid_snapshot; do not attach results to a different commit |
| Full-suite fallback cannot build/start, times out or crashes | execution/infrastructure failure | preserve actual mode and failure, never safe/passed |

Any full-suite mode is conditional on a complete inventory and enforced runner
limits. If a failed LLM leaves D ∪ M empty, the empty-selection rule upgrades the
mode to full_suite. Production fallback acceptance remains a team decision.

## Evidence validation

Validate schema, evidence IDs, repository, allowed commit, path and positive line
range; read content from that immutable snapshot to confirm existence and assess
whether it supports the stated reason. Deleted/renamed base code may be evidence,
but test inventory always belongs to target. Syntactic JSON validity or a high
LLM confidence score does not establish evidence correctness. Binary/empty-file
evidence limitations from 1.06 must propagate as uncertainty, not invented lines.

## Freeze and execution handoff

1. Resolve revisions; discover T only inside the approved worker.
2. Validate inputs and apply a versioned policy; record rejected proposals and mode.
3. Freeze S, T minus S, fallback reason, target/config/inventory hash and timestamp
   before any selected/full-suite execution or evaluator join.
4. Worker receives only validated IDs and frozen target identity through an
   argument vector. It does not execute a model-generated shell command.
5. Record dispatched IDs and actual mode separately from the initial recommendation.
   Join full-suite outcomes/fault ground truth only in evaluator-owned storage.

## Review cases

| Case | Expected check |
| --- | --- |
| D={a}, M={b}, L={c}, T={a,b,c,d} | selected={a,b,c}, not-selected={d}; L cannot remove a/b |
| Duplicate L IDs, parameterized IDs | detect duplicates; preserve exact native identity |
| L={unknown}, valid D/M | reject L; dependency_modified or empty-selection escalation |
| D={unknown} | stop; do not silently lose required coverage |
| Valid empty T versus collection error | distinct no_tests versus discovery_failed |
| Config changed, parser partial or rename mapping incomplete | full suite when feasible; otherwise stop with explicit reason |
| Evidence points to future/wrong commit or unsupported lines | reject contribution or stop as invalid_snapshot according to table |
| Full fallback fails | execution error; no fault-retention/safety conclusion |

Examples are design checks, not measured execution or benchmarks. Expected cases
become tests when the implementation task is assigned. [Protocol](../evaluation-protocol.md)
keeps planned reduction separate from dispatched reduction; unknown metrics stay
null/N/A and one failing test is not a verified fault.

Handoff to Pham Phan Hoang Huy for evidence/leakage review, An for dependency/M
mapping, Nguyen Tan Huy for lifecycle/protocol and Viet for evaluation consumer
consistency. AI assistance: Codex drafted/self-reviewed; independent review,
signatures and final policy approval are not asserted.
