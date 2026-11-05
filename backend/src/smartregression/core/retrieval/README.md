# Local structural and lexical retrieval

P5 is implemented by `lexical.py`, `application/retrieval.py` and
`adapters/storage/lexical_index.py`, under accepted ADR 0003/0004. See the
[current implementation handoff](../../../../../docs/development/task-2.13-retrieval.md).
The user explicitly authorized completing the missing H2/KH implementation.
Accountable owners/reviewers remain as assigned; implementation is not human approval.

`LexicalConfig` versions AST chunking, snake/camel identifier tokenization,
distinct-term scoring (+4 exact symbol, +2 exact module), exclusions and limits.
Python uses the existing parser; physical CR/LF/CRLF bytes are preserved. Each
line belongs to one chunk, with the smallest enclosing symbol. Oversized physical
lines, parse failures or incomplete builds fail explicitly. Policy exclusions,
binary and unsupported encoding omissions remain visible limitations.

Caps: 128 lines/8 KiB per chunk; 10,000 chunks/32 MiB per index; 64 query terms;
20 chunks/64 KiB context; build 60s/query 5s. These are initial operational caps,
not benchmark quality claims. Changed/direct/indirect/context tiers reuse 2.12;
lexical scores only sort within tiers. Limited context is partial, never safe exclusion.

`index_manifest.py` and `context.py` remain backend-neutral, consistency-only
primitives. `IndexBuild.ready()` still fails closed. A caller manifest/hash/boolean
does not authorize repository access. The actual application acquires immutable
Git sources using the authorized root and explicit full SHAs, then the storage
adapter rebuilds expected metadata from those bytes. Ready requires complete
verified artifacts plus committed SQL metadata; every persisted read revalidates
both. Pure `search_lexical` does not attest persisted readiness.

`ranked_context.py` validates identities/ranges/hashes, deduplicates with provenance
and applies rule `2.12-v1`. Target is default; deleted base context retains its own
snapshot/index/config and is never relabeled as target. No source is executed.
Input comments/docs remain untrusted data. Secret/evaluation paths and recognized
credential content are excluded before chunking, without claiming universal detection.

Chunk content is stored in bounded immutable packs; SQL stores chunk metadata,
not source text. Retrieval reports retain metadata only. No embedding model,
vector dependency, external provider/LLM call, selector or test dispatch was added.
Public `StageAnalysisReport`/generated types are unchanged. Internal manifest shapes
remain subject to the assigned producer/consumer human review before freeze.
