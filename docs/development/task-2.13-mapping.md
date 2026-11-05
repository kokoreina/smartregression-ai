# H1 prompt 5 — Inventory/mapping workflow sidecar

Branch `feat/h1-2.13-mapping-sidecar`, based on prompt 4 `e488ebf` / PR #50.
Main baseline remains `b3b251a` (fresh fetch 2026-11-05). No automatic merge.

## Implementation and use

`analyze_execution(..., mapping_collector=collector)` collects exactly once using
the injected existing collector, verifies its unchanged inventory configuration and
trusted `pytest-item-path/1` receipt, then calls the existing mapping application
API with actual report stages and the frozen target snapshot. Simultaneously
supplying an inventory-only collector is rejected rather than collecting twice.

The optional internal execution field `mapping_artifact` contains bounded canonical
`report-mapping/1` bytes and a digest descriptor. The envelope binds full run/repo/
base/target identity, report ID and exact serialized report hash to the existing
`component-test-mapping/1` payload. Exact native IDs, provenance, unresolved and
`safe_to_exclude=false` are retained. Scope remains test-file-to-component-module;
relationships are not coverage, test selection or permission to dispatch.

`analyze_local(..., mapping_collector=collector, mapping_artifact_root=root)` uses the
existing guarded immutable byte publisher; when persisting, artifact_root is the
default mapping root. Sidecar-only mode does not load DB settings. Paths use
`<run>/<report>.mapping.json`; report publication/catalog remains unchanged. The
sidecar is not falsely cataloged as a report. A later DB/report error preserves
published sidecars for reconciliation. Invalid root/receipt/size fails visibly.

No public report fields, dashboard, endpoint, dependency or migration is added.
Ordinary CLI analyze still leaves collection unconfigured; trusted composition
injects the existing allowlisted collector. A runnable integration command below
exercises this boundary. Serialized receipt/sidecar JSON is not authorization;
consumers need trusted producer output or must recompute under authorized sources.

## Verification evidence

Cwd current execution worktree; existing Python/Ruff under
`D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/`, PYTHONPATH=backend/src,
PYTHONDONTWRITEBYTECODE=1; portable Git prepended. Elevated tests avoid Windows
sandbox temp/pipe limitations. No input Python or build hooks execute on host.

- Red: mapping workflow tests fail collection because the sidecar module is absent.
- Focused workflow/publication tests: **10 passed**, exit 0. Includes partial/failed
  discovery, unknown IDs/wrong receipt/config, report mismatch/tamper, size cap and
  unsafe output root. Collector doubles are explicitly labelled.
- Unit + existing mapping integration: **641 passed**, exit 0 (before two final
  focused partial/size tests were added).
- Backend regression: **743 passed, 96 skipped, 1 existing warning**, exit 0,
  169.45s (same two added tests checked in the focused run). Dedicated DB checks
  are not inferred from default skips.
- Dedicated PostgreSQL: **94 passed, 2 candidate-to-DB skips**, exit 0, 24.33s.
  New real SQL/Git/files test binds sidecar/report digest and persisted evidence;
  its collector is a declared double. Fresh/upgrade/recovery/cleanup also pass.
  Evidence: `var/storage-verification-fa83e275f7404c379cf7fecb076abbaa/evidence.json`.
- Ruff lint/format, exporter and diff checks pass; final preflight recorded before commit.

### Actual candidate integration (separate from doubles)

Built the existing hash-locked inventory Dockerfile, image
`sha256:45fddb16e6b0f2aa69d1a0b2ff887d5ae18a1159bae90a80d3a9848fceafb803`.
`scripts/mapping/verify_workflow.py` fetches only the two allowlisted Git targets
and their actual parents without checkout. Existing CandidateInventoryCollector
executes collection/hooks only within its network-none, read-only, nonroot bounded
Docker runner. It uses actual diff/graph/impact/evidence and mapping, not synthetic
component seeds. This is integration evidence, not a fault/selection benchmark.

| Candidate | Base → target | Actual results |
| --- | --- | --- |
| sqlparse | `d279be4f8be0260a3c0a9a53b04d566f2fbc48e3` → `60cdc649726bf1bc4f1b336050560b336da715ec` | 509 native IDs; 2 changed files; 1,206 relationships; partial, 56 unresolved |
| tinydb | `0ba5727f2d915dedafb192e92f65dd64a21e3411` → `edff96aeb2616402e9489d46e90a592c05565621` | 228 native IDs; 1 changed file; 0 relationships; partial, 266 unresolved |

Both sidecars passed report/digest readback and wrong-report rejection, with owned
containers removed. Zero relationships is not a safe exclusion result. Evidence:
`var/mapping-workflow-98640b42214e494982e16ce693e2103d/evidence.json`.

```powershell
python -m pytest backend/tests/unit/test_mapping_workflow.py backend/tests/unit/test_mapping_publication.py -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p5-extra
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/sprint2-h1-execution/p5-full
python scripts/storage/run_checks.py
docker build -t smartregression-inventory:candidates-locked -f scripts/inventory/Dockerfile scripts/inventory
python scripts/mapping/verify_workflow.py --image sha256:45fddb16e6b0f2aa69d1a0b2ff887d5ae18a1159bae90a80d3a9848fceafb803
```

No browser/retrieval/complete Sprint 2 acceptance is claimed. OpenAI Codex assisted
implementation/tests/docs and self-review; independent review is pending.
