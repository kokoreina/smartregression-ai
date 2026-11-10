# Task 3.04 — Gemini adapter

## Prompt 1 checkpoint

Started 2026-11-10 from main `f729e6ecb3fdb74093632ca5e3946aac3f087a8b`.
Branch `feat/s3-3.04-gemini`, worktree `D:/smart-regression-ai/var/s3-gemini`.
Readiness depends on [PR #66](https://github.com/kokoreina/smartregression-ai/pull/66),
head `20166b0`, still open at start. No root Office/planning changes imported.

Huy authorized all four prompts, two publication PRs and bounded synthetic-only
live verification at 3.16. This checkpoint is offline 3.04, not G1/G2.

Decisions under Huy's delegation:

- Keep canonical synchronous ProposalProvider/application boundary. SDK async
  generation runs inside a cancellable event loop; no thread-based fake timeout.
  `propose()` is one attempt; 3.16 owns coordination/retry and admission.
- Request packing is frozen JSON, small provider schema, explicit model/v1,
  minimal thinking, tools disabled. Composition accepts explicit key, no env lookup.
- Explicit SDK attempts=1. Unknown 429 defaults to quota; retry requires structured
  rate-limit evidence. Raw errors/input never become report messages.
- SDK installed by uv with existing pins retained; no core SDK imports or changes
  to v1/v2/v3 contracts/generated types/storage/migrations.

Test-first collection failed for missing adapter before implementation.
First checkpoint: 16 adapter cases and 58 existing workflow cases **74 passed**.
Fresh project `uv sync --locked` installed 49 packages including editable project
under `.venv`; caches/TEMP are inside this worktree. Upstream SDK emits two
Python 3.14 SyntaxWarning docstrings; not suppressed or edited.

Prompt 2 still needs expanded error/cleanup/security/parity cases, full relevant
regression, final self-review and publication. No live request or credential read.

## Prompt 2 implementation and checks

Expanded adapter coverage to 33 cases: native IDs/evidence, unknown references,
duplicates, settings, cancellation, structured 429, refusal/tools, factory failure,
wire envelope limits and injection separation. Final affected adapter/workflow
subset: **91 passed**. Ruff lint/format and canonical exporter check passed.

An initial network-denial fixture blocked Windows asyncio's internal loopback
socketpair. Corrected the fixture to allow only internal loopback while all HTTP
still uses mock transport; no external API request was sent.

The first full backend checkpoint loaded code before the cleanup fix: **963 passed,
3 failed, 132 skipped**. The three failures demonstrated that SDK aclose does not
close injected clients. Adapter now explicitly closes its factory-owned injected
transport; all 33 affected adapter cases pass after the fix. A fresh full final
regression completed: **968 passed / 132 skipped / 2 upstream SDK warnings**,
exit 0, 449.33s. Evidence `var/s304-final.xml` and `var/s304-final.log`.
The skips are 131 dedicated SQL opt-in cases and one POSIX FIFO on Windows.

Wire budgets use SDK's escaped JSON serialization and include the larger complete
count envelope. Compact UTF-8 context alone would undercount non-ASCII wire bytes.
No existing locked package version changed; uv added the SDK/auth/transport
transitive packages. No schema/generated drift or Office/migration changes.

Actual commands from this worktree, with TEMP/TMP/UV_CACHE_DIR inside its var:

```powershell
uv add google-genai==3.0.0 --no-sync
uv sync --locked --python D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_gemini_adapter.py backend/tests/unit/test_workflow_contracts.py -q -p no:cacheprovider --basetemp var/adapter-focused-final --tb=short
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
uv lock --check
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider --basetemp var/s304-final --junitxml var/s304-final.xml --tb=short
```

`uv` resolves to `D:/smart-regression-ai/.tools/bin/uv.exe`; PYTHONDONTWRITEBYTECODE=1,
portable Git prepended. New .venv was installed from the updated lockfile, unlike
the reused compatibility environment in 3.14. Dedicated SQL opt-in checks and
Windows POSIX FIFO skip are reported separately; no database behavior changed.

## Security/self-review and next task

Sync API rejects nested event-loop use rather than blocking a running web loop.
The async method is for the bounded 3.16 coordinator; neither method authorizes
egress or spending. Caller must supply approved data and admission guards. SDK
defaults/retries are not trusted, provenance is attached from frozen pre-call bytes,
and cleanup failures log stable codes without raw exceptions.

3.16 must add config/credential resolution, full-request count, atomic session
budget/unknown reservation accounting, bounded retry/deadline and actual synthetic
smoke. 3.04 does not implement G1, semantic support, selection or execution.

Codex assisted code/tests/dependency setup and self-review under Huy's request.
Profiles/rules and test-driven-development/security-review/systematic-debugging
were applied. Human understanding/review and main integration remain separate;
no approval, author percentage, effort or live success is fabricated.

Ready for focused publication after the final passing checks. No live inference
or key access was performed in Prompts 1–2. Main approval/merge is not inferred.

## Follow-up before live admission

While implementing 3.16, self-review found SDK 3.0.0 enables automatic continuation
by default, separately from HTTP retries. A two-response mocked regression proved
one propose call could dispatch twice after CONTINUATION. Explicit
`automatic_continuation=False` now preserves the one-attempt invariant; focused
regression is rerun and CI covers the complete updated PR. No live call occurred.
