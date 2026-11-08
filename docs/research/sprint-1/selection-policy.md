# 1.10 Conservative selection and fallback policy

**Accepted design baseline, 2026-11-08; policy revision s1-selection-v1.**
Nguyen Tan Huy authorized finalizing this policy by executing the three Sprint 1
closeout prompts. This accepts the bounded design, not a production selector,
independent code review, mentor approval or whole-sprint acceptance.

Originally prepared for Tran Hung Khanh, 2026-10-24; remaining closeout work is
taken over by Nguyen Tan Huy. Proposed historical reviewer: Pham Phan Hoang Huy.
The [RAG scope](rag-scope.md) supplies metadata/leakage requirements. G1 exercises
snapshot/ID guards and empty/error discovery, not the whole decision table. Sources:
[rule 09](../../rules/09-impact-selection.md), [environment](test-environment.md),
[evaluation protocol](../evaluation-protocol.md), [RAG boundary rule](../../rules/08-llm-rag.md).
Proposal v1.4 §12.6 was read directly for this update. See
[current closeout decisions](closeout-decisions.md) for scope and implementation limits.

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

## Accepted decision table

Correction 2026-10-31: Proposal v1.4 §12.6 distinguishes provider failure from
invalid evidence affecting selection. The previous draft grouped both under
dependency_modified; that was inconsistent with the proposal. The table below
aligns the design with that source. The 2026-11-08 authorization accepts this
design; production implementation and acceptance remain separate.

| Condition | Selection mode / action | Recorded reason |
| --- | --- | --- |
| Complete T, complete D/M, all proposed IDs and evidence valid | hybrid: use S | dependency / modified / validated LLM provenance |
| LLM timeout or malformed output; D/M complete and valid and configured policy permits dependency-only fallback | dependency_modified: discard L; use D ∪ M; otherwise full_suite when feasible or stop | llm_unavailable; preserve the configured fallback decision |
| Invalid evidence affecting selection or unknown L ID | reject L; full_suite if T is complete and execution is feasible; otherwise stop | invalid_llm_evidence / unknown_llm_test; never silently downgrade to D ∪ M |
| D or M contains ID absent from T; mapping stale or wrong SHA | stop | invalid_required_mapping; do not erase required tests by intersection |
| Parser/dependency analysis partial, unsupported production code, changed build/config/dependencies | full_suite if T complete and environment is executable; otherwise stop | incomplete_analysis / configuration_change |
| Rename/delete cannot be mapped reliably | full_suite if T complete; otherwise stop | incomplete_change_mapping |
| Discovery failed or inventory is partial/unknown | stop | discovery_failed / incomplete_inventory; T is not trustworthy |
| Successful discovery produces T = empty | stop as no_tests | empty_inventory; no claim of zero regression risk |
| S = empty with nonempty T and no verified exclusion policy | full_suite if execution is feasible; otherwise stop | empty_selection; absence of candidates is not evidence of safety |
| Wrong repository/commit provenance or unverifiable snapshot | stop | invalid_snapshot; do not attach results to a different commit |
| Full-suite fallback cannot build/start, times out or crashes | execution/infrastructure failure | preserve actual mode and failure, never safe/passed |

Any full-suite mode is conditional on a complete inventory and enforced runner
limits. If a failed LLM leaves D ∪ M empty, the empty-selection rule upgrades the
mode to full_suite when eligible, otherwise stop. Production implementation is
outside task 1.10 and must be verified separately.
Snapshot/provenance and inventory validity are prerequisites: wrong repo/SHA or
failed discovery always stops before considering a full-suite fallback. Budget
exhaustion uses the configured valid fallback only if it can finish within hard
limits; otherwise stop. A duplicate valid L ID is recorded and deduplicated;
deduplication does not excuse invalid IDs or evidence. This precedence avoids
choosing a permissive row when more than one condition applies.

Apply overlapping conditions in this order:

1. Unverifiable repository/snapshot identity, failed/partial inventory or invalid
   required D/M IDs always stop; another row cannot override these failures.
2. Only after those prerequisites pass, a valid empty T produces no_tests.
3. Invalid L membership/support or incomplete analysis requires eligible full
   suite or stop, even when a provider timeout also occurred.
4. Provider failure alone permits configured dependency_modified only when D/M
   are complete and valid. If its result is empty with nonempty T, use step 3.
5. Otherwise freeze the valid hybrid selection. Missing runner/resource eligibility
   prevents dispatch regardless of selection mode.

Full-suite eligibility means authorized execution of the exact frozen target,
complete trusted T, a compatible prebuilt environment and enforced isolation,
time/output/resource limits. Budget exhaustion cannot bypass any prerequisite.
Duplicates of valid D/M/L IDs are recorded and deduplicated, preserving inventory
order; duplicates never repair invalid IDs. Missing/unresolved mapping is partial
analysis, whereas a mapping with a wrong identity or invalid required ID is invalid
and stops. A reference belonging to a different repository or disallowed snapshot
stops; unsupported semantic evidence within the allowed snapshot follows step 3.

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
| L={unknown}, valid D/M | reject L; full suite if complete T and runnable; otherwise stop |
| D={unknown} | stop; do not silently lose required coverage |
| Valid empty T versus collection error | distinct no_tests versus discovery_failed |
| Config changed, parser partial or rename mapping incomplete | full suite when feasible; otherwise stop with explicit reason |
| Evidence points to future/wrong commit | stop as invalid_snapshot |
| Evidence has unsupported lines or does not support selection | full suite if complete T and runnable; otherwise stop |
| Full fallback fails | execution error; no fault-retention/safety conclusion |

Examples are design checks, not measured execution or benchmarks. Expected cases
become tests when the implementation task is assigned. [Protocol](../evaluation-protocol.md)
keeps planned reduction separate from dispatched reduction; unknown metrics stay
null/N/A and one failing test is not a verified fault.

Historical consumer/reviewer roles remain recorded above; Nguyen Tan Huy now
owns the remaining closeout and does not wait for those members to implement.
AI assistance: Codex drafted and self-reviewed this update. Independent review,
mentor signatures and sprint acceptance are not asserted.
