# Sprint 3 contracts — v3.0.0

Canonical source: [workflow.py](../../backend/src/smartregression/contracts/workflow.py).
This implements task 3.15, not a Gemini adapter, selector, runner or persistence
implementation. Technical choices below are made under Huy's explicit delegation;
independent review and main integration are separate.

## Compatibility and readers

`WorkflowReport` requires `schema_version: "3.0.0"` and embeds the unchanged
`StageAnalysisReport` under `analysis`. That nested report still has its required
`2.0.0` version and owns report/run/repository identity and demo/real labeling.
Its `analysis_status` describes the eight source-analysis stages only. There is
no synthetic global success label: read proposal, selection and execution states
separately. A valid document, a proposed test and a passing test are distinct.

The shared application reader and CLI `validate-report` accept v1/v2/v3. Version
omission remains legacy v1 only; unsupported versions and unknown fields reject.
All preexisting OpenAPI schemas and actual API paths are unchanged. v3 export
does not create an HTTP endpoint. The existing `analyze` command still emits v2.

The current dashboard is intentionally v2-only and rejects the whole v3 envelope;
it must not silently render `analysis` as if it were the complete workflow. Tests
cover rejection of all three v3 examples. Generated TypeScript includes v3 types
for VI's task 3.11; runtime v3 validation/rendering remains that task's work.

## Request and proposal

`ProposalRequest` requires version 3.0.0, `ProposalProvenance`, complete target
inventory, retrieval/evidence metadata and an ordered `context` list. Fingerprints
are SHA-256 of canonical UTF-8 JSON using the existing `canonical_json` routine
on normalized model values, including defaults. Typed fingerprint helpers define
the exact representation; native test IDs are never trimmed.

Provenance binds run/base/target materialized snapshots, inventory/context/evidence
fingerprints, prompt version, provider/model and configuration digest. `context`
matches retrieval items in order; text UTF-8 bytes match each item content hash.
Representation ceilings are 16 chunks, 4 KiB/chunk and 32 KiB total context text.
These do not enforce the total provider wire payload, tokens, deadline or cost:
3.16/3.18 must enforce those before real egress. No key is a request field.

`ProviderResult` has exactly three states:

| State | Required | Forbidden |
| --- | --- | --- |
| not_run | reason, attempts=0 | provenance, proposal data, error, usage, actual model version |
| completed | provenance, typed data, attempts>=1 | reason, error |
| failed | provenance, classified provider error | reason, proposal data |

Failure can have zero attempts for local preflight rejection. Attempts are actual
generation attempts, not token-count requests. Only observed model version is
reported. Missing usage/latency/cost stays null; measured zero remains zero.
Usage token fields mirror separate provider observations; no guessed totals or
implicit addition/double-counting of thinking tokens. Adapter/config tasks own
actual mapping, budget ledger, retry ownership and accounting.

Provider error codes cover auth, permission, configuration, quota/rate-limit,
timeout/transport, refusal, empty/truncated/invalid output and budget exhaustion.
Raw SDK errors do not belong in these fields. A refusal is a failed proposal,
not an empty successful suggestion list.

`TestProposal` contains unique native test IDs, reasons and nonempty evidence
references. `request_proposal` calls the provider once, revalidates input/output
JSON, compares provenance against pre-call bytes and checks inventory/evidence
membership. Adapter mutation of nested objects cannot redefine expected inputs.
Unexpected adapter exceptions are redacted to a stable boundary error. The port
does not authorize egress, implement retry, or verify semantic support. Task 3.05
must still establish that the cited evidence supports each suggestion.

Requests may contain authorized context text; reports contain provenance and
suggestions, not a copy of the full request/prompt. Source/comment/model text is
untrusted data and cannot change policy or tool permissions.

## Selection and execution contracts

`SelectionManifest` binds manifest ID, run identity, complete target inventory and
its digest, fixed `s1-selection-v1`, configuration and mode/reason. Selected and
not-selected lists are unique, disjoint, cover T and preserve its order. Unknown
IDs are rejected, not dropped by intersection. Nonempty T forbids empty selection;
full-suite mode includes all T; no-tests mode requires empty T.

These are structural invariants. 3.01/3.02 must verify trusted inputs and freeze
the artifact; 3.05/3.06/3.07/3.08 own semantic support, mandatory D/M inclusion,
fallback precedence and full-suite eligibility. A serialized manifest is not a
capability to dispatch code, and this task does not implement those policies.

`ExecutionPayload` binds the same run and manifest ID, actual dispatched IDs,
unique observations and termination (exited/timeout/cancelled/infrastructure error/
output limit). Observations belong to dispatched IDs; `exited` requires observations
for all dispatched tests. Durations are nullable; no fault label is inferred.

In the v3 envelope, selection payload requires a completed selection stage and
the same inventory. Execution requires that manifest; dispatched IDs are an
ordered subset of selected IDs. Completed execution requires all selected tests
dispatched and exited. Partial execution retains observations with explicit
termination and limitations. No-tests manifests keep execution not-run; zero
tests do not produce a passing execution report. Actual runner/authorization/
isolation and outcome categorization belong to 3.09/3.10.

## Consumer and storage handoff

| Task | Boundary to use | Work still owned downstream |
| --- | --- | --- |
| H1 3.04/3.16 | ProposalProvider, ProposalRequest, ProviderResult | Gemini SDK adapter, verified model/config, finite budgets/retries and live smoke |
| H1 3.17 | shared report reader, request_proposal, WorkflowReport | Trusted real context/collection, CLI wiring and G2 |
| H2 3.18/3.05/3.06 | PromptContext, TestProposal and provenance | Egress/context policy, evidence support and conservative selection |
| AN 3.02/3.07/3.08 | SelectionManifest, typed failures and state fixtures | Trusted membership/eligibility and fallback decision table |
| KH 3.01/3.09/3.10 | SelectionManifest, ManifestRunner, ExecutionPayload | Freeze/dispatch/isolation and actual observations |
| KH 3.19 | WorkflowReport and identity/digest references | Durable v3 codec/catalog/read-back and forward schema decisions |
| VI 3.11 | generated components schemas, DEMO examples | v3 runtime validation and dashboard/browser acceptance |

Current PostgreSQL writers/codecs remain explicitly v2-only; do not pass a v3
envelope to them or drop its proposal/selection/execution fields. No stored bytes,
old migration or schema head is changed by 3.15. KH must design versioned v3
persistence in 3.19 against actual producer needs; no speculative migration here.

Examples: `examples/reports/workflow-report.{proposal,provider-error,not-run}.json`,
`proposal-request.demo.json`; invalid-state fixture under `backend/tests/fixtures`.
These are synthetic DEMO data, not live-model evidence or a dataset benchmark.
Export/generate/check commands remain those in the [contract index](README.md).
