# Task 3.16 — bounded Gemini runtime and G1

**Current: G1 achieved on synthetic fixture on 2026-11-10 at 10:35 UTC.**
Readiness/open-PR snapshots below are history, not current live blockers.
Final source/check/publication status is recorded at the end. G2 remains 3.17.
Final canonical-resolver smoke succeeded at 10:40 UTC, run ac181e223b6041e9b55f119fe7951c97.

## Prompt 3 checkpoint

Started 2026-11-10 from 3.04 head `1661b35`, branch
`feat/s3-3.16-gemini-guards`, worktree `D:/smart-regression-ai/var/s3-gemini`.
Dependency [PR #67](https://github.com/kokoreina/smartregression-ai/pull/67) and
readiness [PR #66](https://github.com/kokoreina/smartregression-ai/pull/66) are open;
no review/merge is inferred. Huy authorized all four prompts and synthetic-only
bounded live smoke, <=USD 0.02/run, <=USD 0.10/session, <=5 runs. All writes/cache/
TEMP stay under the project; original root Office/planning changes are preserved.

## Decisions under Huy's delegation

- Keep SDK async transport, existing synchronous application contract and public
  v3 unchanged. Runtime coordinates one count and <=2 individually validated
  generation attempts. No thread-based background requests or nested SDK retry.
- Atomic local JSON ledger, OS file lock held across a run, <=5 runs/session.
  No new DB, migration or service. Unknown reservation remains committed across
  failures/restarts; corrupt/mismatched session data blocks admission.
- Store reservation/charged-to-budget separately from nullable observed nominal
  token cost. Cost calculated from observed tokens is not a billing invoice.
- Explicit GEMINI_API_KEY only; same-value GOOGLE_API_KEY allowed but different
  values block configuration. No automatic dotenv discovery. Credential repr is
  redacted; SDK base URL and Developer API backend are explicit.
- Runtime quote is pinned to standard text model/pricing observed 2026-11-10;
  <=8192 counted input tokens, <=2048 combined output/thought tokens. Reserve
  **7578 micro-USD** per generation (ceiling), based on full input cap rather than
  a smaller fixture count. Unknown usage holds the full amount; 2 attempts reserve
  <=15156 micro-USD. Count journals a zero reservation under the unbilled policy.
- Retry only classified transport/timeout/rate-limit; unknown 429 is quota.
  Respect numeric or HTTP-date Retry-After and remaining deadline. SDK automatic
  continuation is disabled separately from HTTP retries (fix already on #67).

## Sources resolving readiness gates

Read public sources on 2026-11-10, no credential used:

1. [Official llms index](https://aistudio.google.com/llms.txt) exposes separate
   generateContent docs, which were missed when reading the default Interactions
   view. [Thinking for generateContent](https://aistudio.google.com/docs/thinking.md?generate-content=true)
   explicitly says max_output_tokens caps output **including thought tokens**,
   with a hard infrastructure cutoff. Minimal thinking is not zero-token proof.
2. [CountTokens v1 reference](https://aistudio.google.com/api-reference/tokens/count-tokens.md?api-version=v1)
   documents the exact v1 endpoint and full generateContentRequest. Public v1
   discovery lists that method. Keep exact packed request/model/schema/instructions
   shared with generation; endpoint acceptance still requires live verification.
3. [Firebase Google count guide](https://firebase.google.com/docs/ai-logic/count-tokens)
   explicitly states countTokens has no charge. [Google staff clarification](https://discuss.ai.google.dev/t/188451/2)
   maps the billing FAQ's GetTokens wording to direct REST models.countTokens,
   including generateContentRequest, without inference billing/quota.
4. Schema counting has conflicting staff explanations: the general answer above
   excludes generation config; [model-specific 3.5 Flash-Lite answer](https://discuss.ai.google.dev/t/189068/2)
   says structured schema is included. The follow-up does not establish a strict
   inequality between pre-count and actual prompt usage. Therefore report the
   8192 limit as a **counted admission cap**, reserve full cap, record actual usage
   and stop further spending on an observed cap violation. Do not claim exact
   provider TPM prediction or an independent Google billing hard cap.

Source snapshots/hashes are local `var/provider-sources/` (ignored, not committed).
No silent API/model fallback. Real account/quota/billing access remains unverified
at this offline checkpoint. These decisions do not represent mentor approval.

## Offline evidence and remaining work

Test-first collection failed for the missing runtime/ledger modules. Initial
guards: 15 passed; expanded runtime/config/ledger tests: 26 passed. Combined
adapter/runtime checkpoint: 60 passed, two upstream SDK SyntaxWarnings. Focused
count/generation HTTP parity and provenance integration cases are being finalized.

Prompt 4 must add the opt-in synthetic harness, verify real endpoint/account,
record permitted request/config/snapshot hashes and a validated nonempty proposal,
run final regression, then publish the PR. **G1/G2 not performed at this checkpoint.**
No source repository/private data is authorized for egress; 3.17 requires its own
manifest. No selection/runner/UI/storage extension belongs in this task.

Codex assisted implementation/tests/source review and self-review, using routed
profiles/rules, test-driven-development/security-review/systematic-debugging and
api-contracts for internal producer-consumer ports. Huy/team understanding and
independent review remain separate; no effort/approval/ratio is fabricated.

## Prompt 4 compatibility decision log

The first two live runs used explicit v1. Count succeeded (the second observed
484 tokens), but generation returned HTTP 400 without an allowlisted parameter
diagnostic. Both remain failed evidence with 7578 micro-USD held each; no retry
or refund was inferred. This does not establish that v1 is generally unsupported.

Under Huy's delegated compatibility authority, select explicit v1beta for the
next controlled test, using the same model, schema, caps and session ledger. This
matches the provider's generateContent examples; it is an explicit recorded
configuration change, not runtime fallback. Policy/configuration hash changes;
offline runtime tests (28) pass before the next live request. If this fails too,
preserve the evidence and diagnose without exceeding five session runs.

The v1beta comparison also returned HTTP 400 / INVALID_ARGUMENT after a valid
484-token count. Root cause is still unconfirmed. Next controlled compatibility
change reduces the provider JSON schema to object/array/string/required/properties
only; canonical local validation still forbids unknown fields, duplicate IDs and
invalid lengths. Configuration fingerprint advances to suggestions/2-common-subset.
Combined adapter/runtime checks: 62 passed before the fourth session run. No model
change, budget increase or inference retry beyond the coordinator was introduced.

## Live G1 result

Run `be494c2c7302402ebdd7eafb0af8e8c8` succeeded on the fourth session run:

| Observation | Value |
| --- | --- |
| Model / API | configured and observed `gemini-3.5-flash-lite`, explicit v1beta |
| Count / generation usage | count 484; observed input 484, output 107, total 591; thinking missing => null |
| Attempts / time | one generation attempt; runtime 7.222s |
| Proposal | `tests/test_math.py::test_add_negative`, evidence synthetic-e1/e2; reason correctly connects max(0,a+b) to changed negative-sum behavior |
| Budget | 7578 micro-USD reserved for this attempt; missing thinking usage => cost null, reservation held |
| Entire session | four count requests and four generation attempts; 30312 micro-USD (USD 0.030312) held conservatively, <=USD 0.10; no invoice/spend claim |
| Stages | selection/execution not_run; no test input code executed |

Source/evidence:

- Synthetic base `5e53ff660ffbd19ced15b67e191334eafb45bef6`,
  target `762e0b3aff94321cc735c13e4fea9721e7235ecb`; materialized snapshots
  `6ba96dc884371cccecdbcf2e4eb2d91f1b2de73711489de9ac0e53eccf7bef22` /
  `6dfb337d71b2d2cca25961a44217d75fce9684a47a1272f49b79ad9cdaea91af`.
- Configuration `793fe304f4d4d0f9a9d690647e51bb60fd62e58ef2d566054236d3227e75a107`.
- Request SHA256 `bc1e5998aa4377dd53c2fa9df292c718ea14905548d6c386f2239a7e25871406`.
- Implementation SHA256 recorded by harness:
  `3379b9ec2a08ec8f531d5102e7f6607e835bc3ab15d562b76aa1a501edcb5c2f`.
  Parent commit at run was 1661b35; 3.16 source was uncommitted and is identified
  by that content hash, not misrepresented as already committed.
- Local artifacts under
  `var/gemini-g1-session/runs/be494c2c7302402ebdd7eafb0af8e8c8/`:
  request.synthetic.json, provider-result.json, evidence.json, synthetic repo;
  shared session budget.json retains all prior failed attempts.

Commands actually run from this worktree with local TEMP, bytecode disabled and
portable Git prepended:

```powershell
.venv/Scripts/python.exe scripts/llm/smoke.py --session-root var/gemini-g1-session
.venv/Scripts/python.exe scripts/llm/smoke.py --live --session-root var/gemini-g1-session --env-file D:/smart-regression-ai/.env
```

`--env-file` is an explicit trusted backend secret-file input, not dotenv discovery
from cwd/input repo; key values are never printed/copied. All writes are within
the project. Harness rejects output outside its source worktree. Dry run created
fixtures without network; live only sent generated synthetic data. No cloud billing
settings or quota were changed. Account access is established only for this smoke,
not arbitrary models/tiers/capacity or long-term key validity.

The comparison narrows compatibility to the working common-subset schema/API
combination; it does not prove which individual schema keyword caused earlier 400s.
Canonical local constraints remain enforced. Keep model/API/schema/config explicit;
do not silently restore earlier schema constraints or switch API/model in production.

Explanation/evidence support was self-reviewed against frozen synthetic bytes.
This demonstrates connectivity/typed proposal/guards, not benchmark selection
quality, independent human approval, real-source egress or G2 completion.

Final fixture self-review found Windows CRLF evidence excerpts were labelled
resolved by the harness rather than passed through the canonical source resolver.
The actual synthetic content/support was correct, but this was insufficient
verification provenance. Harness now normalizes only Evidence Text according to
the existing resolver and calls resolve_source on frozen bytes; context hashes
still retain exact original bytes. A dedicated fixture regression verifies both
source_span_verified and expected text. The fifth/final allowed session run will
verify this final fixture; prior successful run is historical connectivity proof.

## Final canonical-resolver smoke

Run `ac181e223b6041e9b55f119fe7951c97` completed with one generation attempt:
count **480**, observed input **480**, output **110**, total **590**; thinking/cost
remain null, reservation held. Actual model `gemini-3.5-flash-lite`, runtime
**7.264s**. Suggestion is test_add_negative with synthetic-e1/e2, explanation
correctly identifies the negative-sum behavior change. Selection/execution not_run.

- Base/target Git SHA: `a9778ad27d17f90894c51f34fb72685faf675168` /
  `4001e08b0d348b5859f60a886645e30c431f116f`.
- Request SHA256 `3a304d3d8c2063c9c9f66de1f6ef5c6fa6facabddd46f421dcc1984d72d3bda1`.
- Final implementation SHA256
  `17252f5abc7f4c2ad789b80f96efaca415e2bc6bbe7039c748b875d80175ca13`;
  recomputed after live and matches the harness evidence. Hash includes the
  exact adapter/ledger/coordinator/credential/harness source in listed order.
- Artifacts: same session root, `runs/ac181e223b6041e9b55f119fe7951c97/`.
- Session now contains exactly **5 runs / 5 generation attempts**, **37890
  micro-USD (USD 0.037890) held**, including failed and missing-usage requests.
  No actual billed-spend total is known. No more requests are permitted in this
  session; it was not reset or replaced to evade run limits.

Source is evaluated through canonical resolve_source; context bytes/hashes remain
unchanged by display normalization. Fixture regression verifies the native IDs,
source span and hashes without importing/executing the fixture's Python code.

The full final regression completed on this exact product source:
**1000 passed / 132 skipped / 2 upstream warnings**, exit 0, 519.63s.
Evidence `var/s316-final.xml` and `var/s316-final.log`. Skips are 131 dedicated
PostgreSQL opt-in tests and one Windows POSIX FIFO. No additional inference was
needed or performed after the five-run limit. Ruff lint/format, canonical exporter,
local docs links/fences/key-pattern and git diff checks also passed.

Before the canonical-resolver fixture fix, a focused run had one fixture assertion
failure (CRLF/Text normalization) and 122 passes; the corrected fixture/runtime
subset passed 31 cases, then all committed-source candidates passed the full gate.
No assertion was weakened to hide a source-verification failure.

3.04 head 1661b35 independently passed source CI on Linux/Python 3.14.10:
[PR CI 42798684371](https://github.com/kokoreina/smartregression-ai/actions/runs/42798684371),
970 passed / 131 SQL opt-in skipped / 2 warnings; push CI also success. That is
separate from 3.16 CI and from independent human approval/main integration.

Final command (local TEMP/cache, bytecode disabled, portable Git prepended):

```powershell
.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider --basetemp var/s316-final --junitxml var/s316-final.xml --tb=short
```

No public schema/generated artifacts, API routes, input analysis CLI, database
schema, migrations, Office documents, frontend or dependency locks changed in
3.16. Artifact/ledger/source snapshots remain ignored local evidence. This PR
adds a smoke command, not a public general-repository invocation service.

## Next task / completion boundary

3.04 and 3.16 have implementation, offline checks and synthetic G1 evidence. Publish
3.16 against main with explicit dependency on #67; review/merge remain separate.
G2 is still open: 3.17 must acquire permitted real frozen context/inventory, reuse
the runtime/guards and canonical contracts, wire CLI/application and verify main/CI.
Do not send real-source context without an egress manifest or infer selection/
execution/semantic-support completion from the synthetic smoke.
