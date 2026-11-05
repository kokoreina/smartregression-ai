# Prompt 6 — actual bounded local retrieval

## Authorization and boundary

On 2026-11-05 H1 explicitly answered **“chưa triển khai hãy làm luôn đi”** when
informed that H2/KH build/search, PostgreSQL metadata and ready/recovery were absent.
This implements those dependencies plus H1 wiring under accepted ADR 0003/0004.
Accountability/reviewer assignments remain unchanged. No independent approval,
manifest freeze or Sprint 2 Done is claimed by the implementation author.

Branch `feat/h1-p5-lexical-retrieval` stacks on Prompt 5 (#51) and merges the existing
accepted decision branch `docs/sprint-2-p5-local-retrieval` (8aeeaea). That merge brings
its existing workbook/ADR edits; runtime code does not rewrite Office documents.

## Implementation

- `core/retrieval/lexical.py`: existing AST parser, nonoverlapping bounded physical
  chunks, canonical config, exclusions, deterministic query and lexical score.
  Distinct matched terms +4 exact symbol +2 exact module; existing 2.12 tiers/ranker.
- `adapters/storage/lexical_index.py`: expected plan rebuilt from acquired sources;
  PostgreSQL metadata and immutable content packs. Each pack is at most 16 MiB;
  chunk hashes/ranges remain individual. Canonical manifest order determines pack
  offsets. All packs are verified against the complete rebuilt plan on each read.
  Metadata contains references/lengths, not source bytes. Packs avoid thousands of
  guarded filesystem operations per query without skipping verification.
- `application/retrieval.py`: ensure and fresh persisted-ready load, target-default
  and separate deleted/base sources, bounded context and explicit failure/partial.
  Core consistency primitives and `IndexBuild.ready()` do not become trust grants.
- `composition.py`/CLI `analyze --index-root`: opt-in local PostgreSQL index path.
  Existing authorized Git/full SHA acquisition runs first; no input imports/hooks.
  Default absent backend is honestly `not_run/retrieval_backend_not_configured`.
- Internal run configuration optionally records retrieval config digest; old bytes
  omit it when unconfigured. Public v2 schema/generated types remain unchanged.

Caps stay 128 physical lines/8 KiB per chunk, 10,000 chunks/32 MiB content per index,
64 query terms, 20 chunks/64 KiB context, build 60s and query 5s. Initial defaults
are not benchmark claims. Limits/exclusions remain visible; empty is not safe.
Source/comments are untrusted data. No embeddings, paid/provider call or dispatch.

## Migration, permissions and recovery

Append-only revision `20261105_05` extends `20261104_04` (evidence). Adds scoped
`knowledge_indexes` and `knowledge_chunks`, config/version identity, lexical backend
with NULL embedding model, lifecycle trigger and bounds. Ready metadata is immutable.
Upgrade runs only by migration operator, never app startup. Existing rows stay intact;
destructive downgrade is refused. Production retention/ACL remains outside this slice.

Runtime needs schema USAGE and SELECT/INSERT on the two new tables, plus existing
snapshot SELECT/INSERT. Grant only
`UPDATE(state,attempt_id,error_code,updated_at)` on `knowledge_indexes`; no chunk
UPDATE/DELETE/DDL/owner role. The dedicated test harness verifies runtime restrictions.

Publish complete hashed packs and manifest before ready transaction. Chunk inserts
are batched in the same transaction to stay below PostgreSQL's parameter cap at
10,000 chunks. Failure rolls SQL back, keeps traceable artifacts and marks only its
own building attempt failed where possible. Explicit retry reconciles failed/building
state; corrupt ready is rejected, never silently overwritten. Lost commit ack reports
failure; no automatic replay/delete. Concurrent builders converge through scoped keys
and locked transaction. A crashed building row is not readable as ready.

Back up metadata and artifact root consistently (quiesce writers); restore both,
then load with the original authorized snapshots/config and verify every byte.
Harness tests a nonempty CRLF index after actual PostgreSQL/artifact backup/restore.
Test-only restored DB owner credentials stay memory-only; no credential is written
to evidence or production policy. Orphan GC/automatic retention is not implemented.

## Actual verification and diagnosis

Windows Python 3.14 task venv, MinGit 2.56, PYTHONPATH=backend/src, no bytecode;
commands run from the execution worktree. Sandbox temp/Docker access requires tool
escalation; no sandbox permission error is labeled a source regression.

- Full backend before final extra regression cases: **755 passed, 112 skipped**,
  one existing Starlette/httpx warning, 211.49s. Storage cases are separately run
  against PostgreSQL; POSIX FIFO remains skipped on Windows.
- Focused range/pack/lexical cases: **39 passed**, 2.28s.
- Real PostgreSQL plus approved candidate flow: **109 passed, 2 skipped**, 101.81s;
  the two skips are the separately invoked old candidate-inventory-to-DB campaign.
  Evidence: `var/storage-verification-c73e5505e1e7453d96f7cf34224b6682/evidence.json`.
  Includes new actual sqlparse/TinyDB collection/index/mapping/report persistence,
  corruption/config/revision, concurrency/failure/lost-ack and nonempty restore.
- Ruff, formatting, backend schema exporter passed; final checks below are recorded
  after the 10,000-chunk regression and final exclusion changes.

Final gate: **110 PostgreSQL tests passed, 2 separate historical candidate campaign
skips**, 242.88s, including the actual 10,000-chunk SQL round-trip and both current
candidate workflows. Harness pass/cleanup/nonempty restore evidence:
`var/storage-verification-2c73751a0c514259a00d6b6a15ee6b5f/evidence.json`.
Final units: **649 passed**, 29.56s. Ruff/format/exporter, frontend generated-contract
check/typecheck and diff check exit 0. No public/generated contract changed.

The first full-candidate run failed honestly: a Docker image config digest copied
from build output was not an addressable image ID on this engine. Rebuilt the
existing locked Dockerfile and used `docker image inspect ... --format '{{.Id}}'`:
`sha256:8044792784e0ade7bfd011c9982e32d9b6cccda07f58da32a80fa786551dae70`.
The next run exposed query timeout from repeated Python byte scanning and thousands
of guarded small-file reads. Optimized physical boundary finding (same CR/LF/CRLF
semantics) and complete bounded packs; retained all integrity checks and 5s cap.
Standalone sqlparse pure build/search measured about 1.2s/1.0s after byte-scan fix;
this is an environment observation, not a quality/performance benchmark.

The opt-in full storage-suite process deadline is 420s instead of 180s because it
now includes two real Git+isolated-runner pipelines. Default DB-only stays 180s;
product build/query/runner budgets are unchanged. Failed run evidence is preserved.

```powershell
docker build --pull=false -t smartregression-inventory:h1-p6-20261105 -f scripts/inventory/Dockerfile scripts/inventory
docker image inspect smartregression-inventory:h1-p6-20261105 --format '{{.Id}}'
# Set SMARTREGRESSION_P5_CANDIDATE_IMAGE to that inspected ID, and
# SMARTREGRESSION_P5_CANDIDATE_ROOT to the existing approved cached source folder.
python scripts/storage/run_checks.py
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp var/p6-final-backend
python -m pytest backend/tests/unit -q -p no:cacheprovider --basetemp var/p6-final-unit
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
npm --prefix frontend run contracts:check
npm --prefix frontend run typecheck
```

## Remaining acceptance

Prompt 7 must exercise A01–A07 including actual UI file loading, invalid-report
rejection, correct Run ID and visible provenance/limitations. Typecheck is not browser
acceptance. H2/KH/AN/VI review and human acceptance remain distinct from these checks.
LLM provider integration and research selection/quality metrics are outside Sprint 2.

OpenAI Codex assisted implementation, tests, debugging, documentation and self-review.
The team must read/understand/verify changes under Proposal v1.4 Appendix C/D; no
contribution ratio, mentor approval or independent review is invented.
