# Sprint 2 completion — actual local lexical retrieval

Prompt 4 of [the completion sequence](sprint-2-completion-plan.md), based on
inventory/mapping commit `6199de2` / PR #59. Accepted policy remains ADR 0003/0004;
this implementation does not select an LLM provider or add embeddings.

## Implementation

`core/retrieval/lexical.py` reuses the earlier bounded AST/lexical algorithm from
`2f5c517`/`a2692f0`, with current main whole-file exclusions. Python/pyi symbols
use the existing AST inspector; other eligible files use bounded physical chunks.
CR/LF/CRLF bytes and ranges remain exact. Tokenization uses distinct casefolded
terms with identifier splitting; scores rank within the existing structural tiers.
Context caps and incomplete source/graph/query scope remain explicit limitations.

`PublishedLexicalIndex` composes the existing authorized acquisition,
`publish_index`/`load_ready_index`, PostgreSQL index store and guarded artifact
files. It uses `IndexConfiguration` and `index-artifact/1`; no second index schema,
lexical table family or conflicting migration is introduced. Terms/symbols are
rebuilt from verified frozen bytes and the rebuilt manifest must match ready
metadata. An in-memory plan alone is never proof of committed-ready publication.

CLI retrieval enables a bounded, command-local Git object cache (at most 64 MiB).
It retains only size/hash-verified immutable blob bytes and honors each caller's
read bound. Commit/root/tree acquisition, canonical snapshot validation and SQL/
artifact ready verification still run; there is no global or serialized trust
cache. This avoids repeated Git processes within the unchanged 5s query budget.

The workflow retrieves target context and separately identified base context for
deleted components. Mapping sidecars bind the final report, including retrieval.
The internal run metadata records the actual retrieval configuration digest;
legacy records without it retain their previous canonical bytes. Public report
schema/generated types and dependency manifests are unchanged.

## CLI configuration

Add `--index-artifact-root <existing-root>` to an authorized `analyze --persist
--artifact-root <existing-report-root>` invocation. Index files may share that
artifact root. Both roots must be outside the input repository. The application
uses the existing runtime DB configuration; no auto-provision or auto-migrate is
added. Inventory requires its separate explicit candidate/image/workspace opt-in.

No index flag keeps the default read-only analysis independent of DB/search.
An index root without persistence is rejected before acquisition. Partial/failed
analysis preserves the canonical stage and CLI exit semantics; no empty result is
presented as proof that tests can safely be excluded.

## Verification status

Focused tests cover physical bytes, exclusions before publication, deterministic
ranking/empty/context caps, budgets, source/config mismatch, tampered artifacts,
lost commit/building state and workflow publication. Metadata/collection doubles
are labelled. The completion plan records commands and fresh runtime results;
historical branch results do not substitute for combined verification.

Fresh final results, Python 3.14.3 in the reused environment (not a clean install):

- Full backend: **867 passed / 120 skipped / 1 existing warning**, exit 0.
  119 SQL cases ran separately; one POSIX FIFO case is unavailable on Windows.
- Dedicated PostgreSQL 17.11: **119 passed / no skips**, exit 0, including actual
  approved sqlparse/TinyDB CLI inventory/mapping/retrieval/persistence. Candidate
  reports remain partial because their graph/source scope has explicit limitations.
- Actual lexical query survives an owned PostgreSQL process restart and a populated
  metadata/artifact restore; exact rows and evidence identity also match. Final
  evidence: `var/storage-verification-f15208305d5f40b3a7499f288bbd548d/evidence.json`.
- Initial runtime exposed query timeouts on both candidates; bounded verified blob
  reuse fixed this without increasing budgets. A later harness-only restart failure
  was traced to Docker Desktop changing an ephemeral loopback port; the harness
  re-inspects the same owned container and keeps loopback-only bindings.
- Ruff lint/format, schema exporter, plan links/fences and diff checks pass.

SQL tests call the actual CLI main in-process with the dedicated harness's scoped
loopback settings factory; production TLS deployment is not claimed. Browser A07
is the next completion slice, not inferred from these backend results.

OpenAI Codex assists implementation/tests/docs and self-review under Huy's
instruction. Independent/human review and GitHub merge are separate from local
technical verification.
