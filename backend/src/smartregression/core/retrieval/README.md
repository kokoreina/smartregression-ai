# Retrieval

## KH exclusions/storage boundary — 2026-11-05

`exclusions.py` provides the versioned whole-file pre-index policy. The application
`index_publication` boundary independently reacquires authorized Git bytes, checks
manifest/config/exclusions/eligible physical coverage, publishes an immutable local
artifact and commits PostgreSQL ready metadata. Verified loading repeats source,
config, metadata/chunk-row and exact artifact checks. This is an additional explicit
application path; provisional `IndexBuild.ready()` remains closed. H2 retains chunk
generation/query/scoring/search and H1 workflow wiring. No public contract changes.
See [KH handoff](../../../../../docs/development/task-2.10-khanh.md) for internal API,
budgets, false-positive/unknown-secret limits, migration and recovery commands.
Baseline descriptions below remain historical where this section supersedes them.

## Accepted integration decisions — 2026-11-05

[ADR 0004](../../../../../docs/architecture/decisions/0004-sprint-2-integration-decisions.md)
records the team-approved chunk/query/scoring direction, initial budgets (not
benchmarked), assigned reviews, trusted publication/recovery, internal manifest
compatibility and work packages W02–W05/W08. Implementation notes below remain
baseline descriptions, not pending backend choices. Shapes still require actual
producer-consumer review before freeze; ready acquisition/persistence is not
implemented by this documentation change.

## Accepted P5 direction — 2026-11-05

[ADR 0003](../../../../../docs/architecture/decisions/0003-local-lexical-retrieval.md)
records H1's confirmation that the team accepted local structural + lexical
retrieval, PostgreSQL metadata and hashed local chunk/manifest artifacts, without
embeddings or an external provider in Sprint 2. Target is the default context;
base context for deletions/comparison keeps separate revision provenance.

Backend selection is no longer pending. The notes below describe the implementation
baseline: provisional shape/consumer review, trusted acquisition-to-ready integration,
chunk/query configuration, metadata migrations, local search/resolution and workflow
wiring remain implementation work. `IndexBuild.ready()` still fails closed; this
documentation does not bypass it or claim retrieval/LLM runtime acceptance.

`index_manifest.py` contains provisional, backend-neutral snapshot/index/chunk metadata
primitives for Task 2.10 coordination. These are not canonical Task 2.14 stage
contracts until consumer review accepts their shapes under the approved P5 direction.
It validates repository, commit, snapshot, path, source-range and content-hash
consistency, and emits deterministic JSON. `IndexBuild` supports building and failed
states, but ready publication is blocked until Task 2.15 provides independently
acquired snapshot evidence.

The provisional source-range convention uses physical CR, LF, and CRLF boundaries
without normalizing the underlying bytes. Other control characters, including form
feed, are not line boundaries. Task 2.14 must confirm this convention before this
module becomes a canonical producer. Internal validation of a `FrozenSnapshot`
recomputes its exact bytes and manifest identity; it does not establish trusted
provenance. A caller-supplied `SnapshotManifest`, boolean, or wrapper is not
accepted as trust evidence.

The current repository has no independent trusted acquisition result or resolver.
Consequently, this module cannot publish a ready index. The `ready` transition fails
closed with `trusted_snapshot_acquisition_required` until Task 2.15/H1 approves and
exposes an acquisition boundary.

Before that boundary exists, the module is suitable for provisional in-memory
manifest construction, exact-byte consistency checks, deterministic identity
fixtures, and failed-build handling only. It must not be used as a production
retrieval source or persisted ready index. Task 2.14 must approve the provisional
`index/1` and `chunk/1` shapes. Implement the accepted P5 configuration, acquisition
and persistence boundaries before downstream integration or metadata publication.

This module has not implemented the accepted chunking/query/default-budget policy
or PostgreSQL index tables. Backend and initial policy are selected in ADR 0003/0004;
embedding/provider and production retention remain outside this slice. Source bytes are
only accepted transiently to verify a manifest; they are not stored in the manifest.
Retrieval consumers must continue to treat source content as untrusted data.

## Task 2.11 context payload boundary

`context.build_retrieval_payload` is a backend-neutral, in-memory builder for
`RetrievalPayload`. It consumes a validated Task 2.10 `IndexManifest` and the
Task 2.04 `ImpactPayload`, checks repository/commit/snapshot/configuration identity,
and returns matching chunk provenance (`path`, physical source range, content hash,
snapshot identity, index identity, configuration identity and a deterministic
manifest-order contract rank; it does not perform relevance ranking).
It returns an explicit empty `items` list when no candidate path has a matching
chunk. It does not return source text.

Wrong repository, commit, snapshot, stale configuration, invalid manifest, and
inconsistent source data are rejected. Candidate and source text remain opaque data;
the builder does not execute content and does not accept outcomes, fault labels or
execution results.

This builder is not a retrieval backend and does not authorize an index. It must not
be used to bypass `IndexBuild.ready()`: ready publication remains blocked until
Task 2.15/H1 supplies independently acquired snapshot evidence. Backend selection,
ranking/deduplication/verification, persistence and workflow integration remain
outside this builder and follow the accepted P5 and downstream task boundaries.

## Task 2.12 context ranking, deduplication, and verification boundary

`ranked_context.rank_and_validate_context` (and `validate_retrieval_stage`) provides
deterministic context ranking, deduplication, and verification against an immutable
`FrozenSnapshot` (from Task 2.15).

- **Ranking & Tie-Break (Rule 2.12-v1):**
  - Priority by relevance tier: Tier 1 (directly changed files from Task 2.01),
    Tier 2 (direct dependents from Task 2.04), Tier 3 (indirect dependents from
    Task 2.04), and Tier 4 (other candidate / retrieved context).
  - Relevance score descending (higher similarity / score first).
  - Best original retrieval rank ascending.
  - Stable alphabetical / numerical tie-break: `(path, line_start, line_end, id)` ascending.
  - Sequential ranks 1..N assigned to the final deduplicated items.

- **Deduplication with Provenance Preservation:**
  - Identical physical chunks `(path, line_start, line_end, content_sha256)` across
    queries or index sources are merged into a single ranked item.
  - Provenance is strictly preserved: `ContextProvenance` retains all source references,
    original item IDs, original ranks, and scores.
  - All queried sources are retained in `RetrievalPayload.sources`.

- **Verification against Immutable Sources:**
  - Validates repository ID, commit SHA, and snapshot ID against `FrozenSnapshot`.
  - Validates file existence in snapshot (`unknown_snapshot_path`).
  - Validates physical line ranges within the file bounds (`invalid_source_range`).
  - Re-computes SHA-256 of physical range bytes against `content_sha256` (`chunk_content_mismatch`).

- **Reject / Expose Partial:**
  - Revision/snapshot identity violations fail closed with `ValueError`.
  - With `strict=True`, any corrupted chunk raises `ValueError`.
  - With `strict=False` (default), unresolvable/corrupted chunks are excluded from
    valid items and recorded in `limitations` as `StageIssue(code=..., path=...)`,
    yielding a `status="partial"` `ValidatedContextResult` and `StageResult[RetrievalPayload]`.

