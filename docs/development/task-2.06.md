# Task 2.06 — Frozen-source evidence and explanation backend

## Scope and decisions

Prompt 5 follows [2.05](task-2.05.md) / PR #37 and [accepted P3](task-2.05-p3.md).
Branch `feat/sprint-2-2.06-evidence-resolution`; implementation depends on storage
branch, not claimed merged on main. VI's EvidenceItem/StageReportView already exist
on the main baseline; this slice changes no UI/public model/generated artifact.

Agent decisions under Nguyễn Tấn Huy's delegation, 2026-11-04:

- Support means a deterministic **static** claim: a changed source span plus actual
  snapshot import reachability, never proven behavioral change/fault probability.
- No provider/LLM, working-tree reads or execution. Rebuild import observations with
  the existing parser from hash-checked frozen bytes, check actual changed origin,
  and create candidate-scoped stable evidence IDs. Existing arbitrary explanations
  are replaced when producing a new explanation, not semantically certified.
- Re-inspection recognizes only the supported deterministic explanation/witness
  shape. Unknown/free-form claims stay support=unverified even with resolved source;
  contradictory deterministic facts may be unsupported. No fuzzy text matching.
- Span is 1-based inclusive, Python universal newlines CRLF/CR/LF, excluding an EOF
  phantom empty line. Unicode separators do not invent line breaks. Optional excerpts
  compare the exact requested span after existing contract Text normalization;
  symbols require exact parser name/span. No arbitrary trimming/search relocation.
- Missing file/out-of-range → missing; wrong excerpt/symbol → mismatched;
  binary/encoding/size/parse inability → unverified. Saved claims are always reset
  and recomputed before support evaluation. No source position invented for empty files.

## Behavior and architecture

`core/evidence/resolution.py` performs pure position checks, without DB/network/IO.
`application/evidence.py` validates full identity against trusted SnapshotPair hashes,
revalidates typed references, generates explanations with source witnesses and
returns typed evidence stages. File witnesses use actual nonempty source extents;
import-path witnesses cover the actual importer module rather than claiming exact
import-expression locations. Actual graph edge kinds must agree with parser output.
Partial/non-supported evidence yields limitations and partial stage, not completed.

`inspect_bundle` produces a detached transient stage. It neither updates the saved
bundle nor persists new verdicts; missing witnesses cannot become empty completed
inspection. Saving different results requires a new run under P3. All uploaded
resolution/support fields remain untrusted producer claims until inspection.
Caller still owns authorization; hash validation is not an access-control service.

## Handoff to VI

Existing StageEvidence shape can feed EvidenceItem directly. Show saved and inspected
results separately if inspection is added; never overwrite the stored producer claim.

| Backend result | Meaning for existing UI |
| --- | --- |
| resolved + supported | Exact source/span and deterministic static claim verified; explanation still says potential impact |
| resolved + unsupported | Source exists but deterministic claimed relationship contradicts checked facts |
| resolved + unverified | Source exists; arbitrary/unknown explanation is not certified |
| missing | Path/range is absent in the expected frozen revision |
| mismatched | Exact excerpt/symbol does not match; no silent relocation |
| unverified | Unsupported source/verification incomplete; no claim of safety |

`verification_reason` contains safe codes only. No new inspection API or UI component
is invented here. Browser/UI acceptance remains VI's evidence; backend self-review
does not independently certify it. Example cases are executable owned fixtures in
`backend/tests/unit/test_evidence_resolution.py`, including valid, missing, mismatched,
unsupported, arbitrary explanation, rename/delete and transient inspection scenarios.

## Verification and AI assistance

New tests first failed on absent application.evidence. Commands use the existing
locked venv and backend/src PYTHONPATH described in [2.05](task-2.05.md).
Final `python -m pytest backend/tests/unit -q -p no:cacheprovider --tb=short
--basetemp D:/smart-regression-ai/var/p5-unit-final2`: **534 passed** in 21.70s.
Ruff check/format, exporter --check, frontend contracts:check/typecheck and diff
checks passed. An initial oversized parameter test produced an excessively long
pytest node ID; explicit short IDs fixed test setup without changing the limit.
DB behavior is unchanged;
PostgreSQL evidence remains the prompt-4 run, not a fresh claim for this slice.

OpenAI Codex assisted implementation/tests/docs/self-review using Backend/Change
Impact profiles, TDD/security skills and rules 01/02/03/04/06/09/13. No dependencies,
source execution, provider calls or services. Independent human code review and
runtime/UI acceptance remain distinct. Prompt 6 wires this backend into analysis;
this PR does not claim the CLI already produces the new evidence stage.
