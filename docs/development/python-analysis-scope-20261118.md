# Python Explorer resolution and coverage explanation

Completed locally on 2026-11-18 in `D:\C1.SE26\Repo`, branch
`feat/web-uiux-project-workspace`. The user authorized clearer coverage UI and
stronger Python import/alias/internal-call handling. Existing unpushed work remains;
immediate UI inputs are archived at
`var/python-analysis-review-20261117/ui-before.zip`.

## Behavior and implementation

The old parser flattened function imports into a file-level alias map, collected
nested assignments as outer-scope shadows, could resolve a reassigned function as
its original definition, and missed package re-exports/dotted module calls.
Focused tests reproduced these faults before implementation.

`core/explorer/python.py`, `parsing.py` and new `python_resolution.py` retain lexical
import scope, scope parents/kinds, conservative parameter/assignment shadows,
relative/package re-exports and dotted-module prefixes. Package attributes take
precedence over same-named child modules; namespace submodules need no init file.
Re-export traversal is bounded to 32 lookup states and detects cycles. Nested
functions are not invented as attributes of their enclosing function. Rebound
class members remain unresolved. Parameter/object dispatch, lambda/comprehension
calls, wildcard imports and dynamic expressions retain explicit uncertainty.

Recognized unshadowed Python built-ins and standard-library references retain
path, line and category separately from unresolved relations. They are not turned
into internal edges or treated as behavioral validation. A same-named local module,
including a known path excluded from source reads, blocks stdlib classification.
The trusted runtime's builtin/stdlib catalog participates in the parser digest.

New `core/explorer/coverage.py` groups unsupported paths by filename/extension and
retains an independent source-policy exclusion list. It counts unresolved reasons
and classified reference kinds separately. `application/explorer.py` supplies known
snapshot paths and updates diagnostics after source exclusions.
`application/scenarios.py` preserves baseline unsupported/excluded coverage in
overlays, so cached source filtering cannot make an overlay look more complete.

`CoverageDetails.tsx` and its CSS, used by Explorer and ImpactOverview, show syntax
success/failure counts, unsupported groups/file lists, unresolved reasons,
recognized references and configuration caveats. The warning describes global
snapshot counts, not errors of the selected file. The 150-node display bound is
separate. Partial status remains conservative. Old payloads without diagnostics
receive an unavailable-breakdown explanation instead of invented classifications.

Import edges still feed file-level potential impact; calls remain additional
static information. The historical research selector/runner were not rewritten.
No input source/tests/dependencies are executed or installed to build these graphs.
This does not establish runtime dispatch, fault probabilities or test retention.

## Contract and cache compatibility

`contracts/explorer.py` adds defaulted/optional `GraphCoverage.diagnostics` and
`ExplorerGraph.classified_references`, plus their source models. OpenAPI and TS
were regenerated with existing exporters. Updated readers accept old payloads;
strict older readers may reject new fields and need an update before consuming
new exports. Reverse compatibility with old strict readers is not promised.

The parser has a new configuration digest; immutable earlier cache rows and
scenario/report evidence remain intact. New analyses are stored separately and
cross-config comparisons retain identity guards. No table migration, new endpoint,
authentication change or dependency was needed. Reopen/materialize a snapshot
when a project lacks a cache entry for the current parser.

## Same-input TinyDB comparison

Public `msiemens/tinydb`, commit `edff96aeb2616402e9489d46e90a592c05565621`.
Task-owned QA snapshot inputs were verified against original payload/source digests
and parsed offline. The final new snapshot was saved/read back through
PostgresExplorerStore, preserving earlier rows. No GitHub fetch or provider call.

| Measure | Before | After |
| --- | ---: | ---: |
| Files parsed | 21 | 21 |
| Parse failures | 0 | 0 |
| Unsupported files | 44 | 44 |
| Unresolved occurrences | 1,435 | 914 |
| Internal static call edges | 154 | 328 |
| Separately recorded recognized references | not separated | 346 |

The 346 comprise 273 builtin calls, 37 stdlib calls and 36 stdlib imports. Remaining
uncertainty: 693 parameter/variable-shadowed calls, 115 dynamic/complex calls,
47 unsupported-scope calls, 40 unresolved static calls, 13 external-or-unresolved
imports and 6 ambiguous symbols. The missing relative package-attribute import was
resolved. This is a regression comparison, not an accuracy/recall benchmark; more
edges alone are not evidence of correctness. Independent expected-edge/non-edge
fixtures test the supported behavior.

The 44 paths are 21 documentation/assets, 13 configuration/dependency files and
10 other unsupported files. Thirty-two are additionally excluded by source policy.
These categories do not grant source access or prove configuration has no effect.

Evidence under `var/python-analysis-review-20261117/`: `comparison.json`,
`graph-after.json`, `coverage-full-{dark,light}.jpg`,
`coverage-details-{dark,light}.jpg`, `coverage-mobile-{dark,light}.jpg`.
Panel images are faithful crops of the full captures; original baseline inputs
remain locally in this ignored directory.

## Verification

Root commands use the existing `.venv`:

- `python -m pytest backend/tests --basetemp var/af-1118-final -q`:
  **1,128 passed, 172 skipped in 196.33s**. Skips are opt-in PostgreSQL and the
  Windows-unavailable POSIX FIFO case, not passes.
- `python scripts/storage/run_checks.py --pytest-filter 'explorer or scenarios'`:
  **4 passed, 167 deselected**, fresh owned PostgreSQL campaign passed.
  Evidence: `var/storage-verification-769374f9830b4f01a7c3c868cfeabffd/evidence.json`.
- Focused Python resolution/core graph/overlay checks: **44 passed**; 25 cases are
  in the new Python resolution module. Cases include aliases, re-exports, lexical
  scope, shadows, cycles, missing members, dynamic namespaces, excluded local
  module names, package attribute precedence and legacy payloads.
- Ruff check/format check on changed backend modules/tests and contract export
  `--check`: pass.

Frontend commands from `frontend`, Node 22:

- `npm run build`: pass with TypeScript. Existing large-chunk advisory remains
  (about 767 kB main JS before gzip).
- `npm run lint`: pass.
- `npm run contracts:check`: pass, 88 validation + 11 report SSR + 60 repository
  consumer + 20 authentication/transport checks.
- `npm run test:workspace`: **48 passed in 37.4s**. New tests cover diagnostic
  categories/counts/file lists and legacy payloads, plus existing UI cases.
- Manual IAB: actual updated QA snapshot and pytest config list, desktop light/dark,
  mobile without document overflow. No hosted-user or independent acceptance claim.

`git diff --check`: pass; zero original files missing from the prior 134-file
local-edit manifest. An initial broader pytest attempt hit existing Windows temp
cleanup permissions; successful runs used new dedicated basetemp directories.
No assertions were weakened to hide failures.

Frontend remains at `http://127.0.0.1:5173`, backend at
`http://127.0.0.1:8000` in product/auth mode. No commit, push or deployment.
