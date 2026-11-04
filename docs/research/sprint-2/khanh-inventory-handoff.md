# Khánh handoff for the independent part of 2.08 and 2.09

**Update 2026-11-04:** [Current handoff](../../development/task-2.08-2.09-completion.md)
supersedes the historical status below. Accepted decisions, native-ID dependency,
candidate collector and PostgreSQL inventory domain are now integrated on the task
branch. The documented operator run passed: 521 default tests, both real candidates,
12 Docker fixtures and 71 actual PostgreSQL tests. Independent team review remains.

Update 2026-11-03: preserved historical independent delivery below. Current branch,
canonical report/workflow integration and isolated fixture collector are documented
in [task 2.08/2.09](../../development/task-2.08-2.09.md). The dependencies described
below were accurate for 2026-11-01; 2.14/2.15/2.13 have since merged.

Date: 2026-11-01. Branch: `feat/khanh-s2`. Base: `977a9b9e6c500da48c1c0c671ea515995847e130`.
Implementation is local and uncommitted. No push or independent review has occurred.

## Scope and status

User authorized the independent inventory/discovery work, deferring shared work.
This is **partial delivery of 2.08/2.09**, not acceptance of either complete task.
It validates observations as data without collecting or executing input-repository code.
Public stage contracts (2.14), authorized snapshots (2.15), persistence foundation
(2.20), real isolated collection and workflow/report propagation remain outstanding.

## Changes

- `backend/src/smartregression/core/execution/inventory.py`: pure internal validation,
  immutable observation result and consumer completeness guard.
- `backend/tests/unit/test_inventory.py`: 52 focused cases.
- This technical handoff. The user's separate Word learning document is outside Git.

Identity includes repository/run, frozen full target SHA, snapshot SHA-256 and
configuration SHA-256. Identity mismatches reject; equality alone is not evidence
of authorization, correct configuration or isolation. A future trusted controller
must derive/check these references against actual runtime inputs, not trust worker claims.

Native IDs are opaque and preserved exactly, including parameter text/order.
Duplicates and invalid/control/surrogate text reject without echoing input.
IDs are never transformed into paths or shell arguments here. Local parser caps
are 10,000 IDs, 8,192 UTF-8 bytes per ID and 512 KiB total ID bytes. They are defensive
implementation limits, not accepted runner resource defaults; exceeding them errors,
never silently truncates. JSON transport still requires an independent byte cap.

Internal payload has exactly `ids`, `exit_code`, `collection_finished`, and
`collection_errors`. It is **not** the current G1/candidate worker format and is not
an accepted serialized stage contract. Do not assume old worker output can be passed
directly or infer completion/error counts from exit code alone.

| Observation | Internal result | Consumer receives usable IDs |
| --- | --- | --- |
| Completed, no collection errors, exit 0, nonempty | complete | Yes |
| Completed, no collection errors, exit 5, empty | empty | Empty tuple; no safety claim |
| IDs observed but collection errors/unfinished/non-success exit | partial | No |
| No IDs with collection errors/unfinished/non-success exit | failed | No |
| Contradictory exit 0/empty or exit 5/nonempty | failed | No |
| Trusted controller timeout | timeout | No |
| Trusted controller output/infra failure | failed | No |
| Malformed/duplicate/over-limit payload or wrong identity | Validation error | No |

Observed IDs on incomplete results are diagnostic only. Controller termination
overrides a valid success-looking payload. Malformed payloads are rejected even
when a termination signal is supplied. Public status mapping and database partial
semantics require 2.14/2.20; no shared models/generated types were edited.

## Actual verification

Cwd: `D:\C1.SE26\Repo-Sprint2-Khanh`. Interpreter reused from
`D:\C1.SE26\Repo\.venv\Scripts\python.exe`; `PYTHONPATH` points to this checkout's
`backend/src`. No new dependencies or lockfile changes.

- Focused pytest: **52 passed**, exit 0.
- Full default pytest in the user's ordinary PowerShell: **106 passed**, one existing
  Starlette/httpx deprecation warning, 5.41s; user supplied the complete output.
- Sandbox full-suite attempts initially encountered temporary-directory ACL errors.
  A diagnostic fixture outside the repo gave 106 passed; this is not the default gate.
  The later ordinary-terminal run above provides the default-suite result.
- Ruff check: passed. Ruff format check: 127 files already formatted. Contract
  exporter `--check`: exit 0. No frontend/contract source changes require regeneration.
- No new isolated discovery, PostgreSQL integration or browser checks were performed.

Reproduction in root PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path 'backend/src').Path
& 'D:\C1.SE26\Repo\.venv\Scripts\python.exe' -m pytest
& 'D:\C1.SE26\Repo\.venv\Scripts\python.exe' -m ruff check .
& 'D:\C1.SE26\Repo\.venv\Scripts\python.exe' -m ruff format --check .
& 'D:\C1.SE26\Repo\.venv\Scripts\python.exe' scripts/export_contracts.py --check
```

## Integration handoff

H1/2.14 must review identity fields, actual collection observations, stable failure
reasons and serialized statuses. AN/2.15 supplies verified immutable target snapshots.
Runner wiring must collect actual finish/error events inside an authorized isolated
worker and retain timeout/output/cleanup failures from its trusted controller.
H1/KH/2.20 decide minimum schema/tooling and persist identity/completeness on real
PostgreSQL. Then propagate through 2.13/2.17 and supply 2.16 with usable inventory.
Do not add APIs, infer missing fields or mark tasks done just to fit existing reports.

AGENTS and profiles Coordinator, Regression Selection and DevOps/Runner were read;
rules 00/01/02/03/05/06/09/10/12/13 and task routing apply. Project skills
test-driven-development, security-review and api-contracts were opened. Only internal
types were added; no public contract changes. Self-review occurred in the author's
session; human producer/consumer review and acceptance remain pending.

OpenAI Codex assisted implementation, test design and explanations. Khánh must review,
understand and verify before submission, per Proposal v1.4 Appendix C/D. No assistance
percentage, human approval or academic acceptance is claimed.
