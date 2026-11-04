# Retrieval

`index_manifest.py` contains provisional, backend-neutral snapshot/index/chunk metadata
primitives for Task 2.10 coordination. These are not canonical Task 2.14 stage
contracts until the pending retrieval decision and consumer review are accepted.
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
`index/1` and `chunk/1` shapes, and Task 2.20 P5 must resolve retrieval backend and
configuration decisions before downstream integration or metadata persistence.

This module deliberately does not choose a chunking policy, embedding model, vector
database, retrieval backend, retention policy or PostgreSQL tables. Source bytes are
only accepted transiently to verify a manifest; they are not stored in the manifest.
Retrieval consumers must continue to treat source content as untrusted data.
