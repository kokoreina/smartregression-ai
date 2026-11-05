# H1 2.06 — Verified source resolution and static explanations

Baseline `b3b251a`, branch `feat/h1-2.06-verified-evidence`, 2026-11-05.
Reconciles resolver/explanation code from the old H1 implementation (`b7ac7a2`
contains the later support-check fixes) against actual main producers. This PR
targets main independently of acquisition #47 and EvidenceStore #48; its tests use
canonical serialization directly rather than import an unmerged persistence codec.

## Behavior

The application resolver validates the complete frozen snapshot pair, repository/
base/target identity and exact content hashes, then checks paths, physical source
spans, symbols and excerpts. Base evidence remains separate for deleted/renamed
components. Pure resolution does not attest to a claim. Application support checks
rederive changes/import paths from source and generate deterministic static
potential-impact explanations, never a behavioral-change or security guarantee.

Saved bundles are inspected transiently without changing their producer claims or
canonical bytes. Arbitrary free-form explanations are not promoted because their
source happens to exist. Missing witnesses/unsupported sources remain explicit.
Caller must obtain the pair through authorized acquisition; a self-consistent
snapshot alone does not grant access. Source comments never supply policy.

No public/generated contracts, DB migrations/dependencies or VI UI changes.
Prompt 4 must wire verification before persistence/freeze. Existing EvidenceItem
consumer can use resolution/support/reason fields already present in v2.

## Actual checks

Existing locked Python/Ruff in `D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/`;
cwd current execution worktree; `PYTHONPATH=backend/src`, no bytecode writes.
Git test prepends the existing portable Git. Unit suite/real Git fixture ran elevated
to avoid Windows sandbox temporary-directory limitations.

- Red: resolver test collection failed because main lacks `application.evidence`.
- Port reconciliation found tests importing the unmerged P3 codec; replaced that
  test-only dependency with existing canonical JSON checks for immutability.
  An intermediate run caught four leftover test references; corrected them.
- Focused resolver suite: **18 passed**, exit 0.
- All backend unit tests: **605 passed**, exit 0, 11.92s.
- Real Git source integration: **1 passed**, exit 0, 4.48s. CRLF sources, actual
  diff/graph/impact producers, dirty-tree independence and tampering rejection.
  Fixture Python contains an execution trap and is never imported/executed.
- Ruff lint/format, exporter check and diff check: pass.

```powershell
python -m pytest backend/tests/unit/test_evidence_resolution.py -q -p no:cacheprovider --tb=short
python -m pytest backend/tests/unit -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p3-unit
python -m pytest backend/tests/integration/test_evidence_sources.py -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p3-git
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
```

No DB/browser acceptance is claimed for this source-only slice. Persisted compound
workflow and consumer UI verification remain prompts 4/7. Independent review is
pending; the user authorized PR creation but not merge/approval.

OpenAI Codex assisted reconciliation, implementation, testing/docs and self-review.
The team retains responsibility for understanding/reviewing the change.
