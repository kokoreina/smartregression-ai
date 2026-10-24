# 1.09 RAG scope and snapshot provenance

Prepared with Codex assistance during Tran Hung Khanh's request to complete the
remaining group Sprint 1 work on 2026-10-24. Workstream owner remains Pham Phan
Hoang Huy; proposed reviewer is Do Ha An. This is a design handoff for review,
not evidence that the owner authored/approved it or that an index/provider exists.
Sources: [revision semantics](revision-semantics.md), [rule 04](../../rules/04-data-storage.md),
[rule 08](../../rules/08-llm-rag.md), [protocol](../evaluation-protocol.md).

## Permitted corpus and exclusion rules

| Input | Include only when | Exclude |
| --- | --- | --- |
| Production source | License/permission verified, at frozen target; base only to explain changed/deleted source | Credentials, generated/vendor/build/cache files, files outside approved snapshot |
| Existing test code | Target snapshot, stable native inventory mapping | Generated tests, deleted base-only runnable IDs, evaluation verdicts |
| Repository documentation | Relevant to current code/test behavior and recorded at an allowed SHA | Embedded instructions asking to change system/tool policy, secrets, unrelated personal data |
| Diff/dependency observations | Explicit base/target pair and parser limitations attached | Future commit history, silently mixed revisions, claims that static edges prove behavior |
| Evaluation artifacts | Never in retrieval context | Fault labels, full-suite outcomes, selected-run outcomes, held-out answers, reviewer verdicts and metric result files |

Repository access is not permission to transmit its source to an external model.
G1 is local-only and contains no provider call. Private/copyrighted data egress
requires the actual data policy and provider decision first. Do not assume a
public license resolves every privacy or benchmark contamination question.

## Proposed metadata contract for an internal chunk

Each chunk needs canonical repository identity, snapshot SHA, optional actual
diff base/target SHA, repository-relative path, language, optional qualified symbol,
1-based inclusive line range, content digest, corpus kind (source/test/docs),
extraction/chunking version, origin/license reference and retrieval/index version.
Test chunks also reference target inventory hash and native test IDs where mapping
exists. Empty/binary content without valid line evidence is explicitly unsupported.

Example is illustrative, not a real measured retrieval result:

```json
{
  "repository": "fixture/owned-g1",
  "snapshot_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "path": "module.py",
  "symbol": "value",
  "line_start": 1,
  "line_end": 2,
  "corpus_kind": "source",
  "chunking_version": "g1-design-v1",
  "content_digest": "example-placeholder-not-a-content-hash"
}
```

Index/cache key must incorporate repo + SHA + corpus filter + parser/chunker version
+ embedding/model configuration if later adopted. Same path on two commits is not
the same evidence. A head update creates a new snapshot/index identity; never reuse
old results as new. Base and target references are distinct for rename/delete.

## Retrieval behavior and validation

1. Filter by authorized repository and allowed SHA before ranking.
2. Apply exclusions before chunking/indexing, including label/outcome locations.
3. Bound file/chunk/context sizes. Proposed G1 policy uses static files only, no
   symlink traversal and no installation, code import or repository execution.
4. Return references with rank/retrieval method and explicit empty/partial/error
   states. Similarity score is not a verified dependency or relevance label.
5. Validate each cited path/SHA/line range against the original immutable content;
   semantic support still needs a rubric/reviewer, not just schema validation.
6. On stale/empty/failed retrieval, preserve uncertainty and let the approved
   [selection policy](selection-policy.md) decide fallback or stop.

No index/vector database/LLM provider is chosen in this task. An implementation
will need a separate brief for chunking, storage, erasure/retention, budgets,
provider configuration and tests at those boundaries (D06 remains pending).

## Untrusted text and leakage review cases

| Case | Required result |
| --- | --- |
| Comment says to reveal token or skip validation | Treat as data; do not call tools, change policy or leak secret |
| Same file/path on wrong SHA | Reject stale reference/cache hit |
| Deleted symbol | Read base evidence with base SHA; runnable inventory stays at target |
| Label/outcome copied into a documentation directory | Exclude by data classification as well as path; review allowed corpus manifest |
| Empty retrieval or unsupported parser | Explicit incomplete context; no claim of no impact |
| Evidence path/range exists but does not support reason | Semantic review failure, not a successful citation |
| Two snapshots happen to have equal text | Keep distinct repo/SHA provenance even if storage deduplicates bytes |

Handoff: An confirms snapshot/evidence semantics; Khanh consumes validated evidence
and inventory limits; Nguyen Tan Huy/Viet audit the evaluation-only data boundary.
No full-suite labels or outcomes are passed to selector. Self-review only; independent
review, production settings and mentor acceptance remain pending. AI use: Codex
drafted the design and checked links/rules; no fabricated sources or measurements.
