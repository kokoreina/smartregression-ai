# Sprint 1 integration evidence

Date: 2026-10-24. Scope authorized by Tran Hung Khanh: finish remaining group
Sprint 1 work, preserve member branches/rules and keep Khanh's own tasks separate.
Original baseline: 7c006ee09f0758b90bd348b99384d26003a78617. During the work, main
advanced to 7989209451058eb88f0f0130d3e27c9b48f24dd9 (PRs 6/7), integrated by
fast-forward after inspecting changed paths. No existing member file overwritten.
Integration branch: work/sprint-1-completion. Independent review is still required.

## Existing work found on GitHub

| Contributor / task | Observed repository evidence | Interpretation |
| --- | --- | --- |
| Nguyen Tan Huy / 1.01, 1.04, 1.08, 1.11, initial 1.12 | PR 3 merged; research/protocol/report drafts and access/lifecycle offline prototypes | Available implementation/drafts; does not establish live auth, worker or completed sprint |
| Dang Dai Viet / 1.02 | PR 2 merged; screening checklist | Screening design exists; no independently labeled dataset inferred |
| Dang Dai Viet / 1.03 | PR 4 merged; candidate/license records | Candidate draft reviewed by kokoreina; not proof collection/build/test succeeded |
| Do Ha An / 1.06 | PR 5 merged; revision-semantics.md | Draft reviewed by kokoreina; Q01-Q10 retain their documented status |
| Tran Hung Khanh / 1.05, 1.10 | PR 6 merged from feat/khanh-sprint-1-selection-ci, commit 7810edd | Personal environment/selection docs and handoff available |
| Nguyen Tan Huy / input choice | PR 7 merged, ADR 0002 | Python/pytest accepted for MVP input; versions, G1 and remaining decisions are separate |

Commit author/workstream owner and agent author of new additions are not
interchangeable. No new work is falsely attributed to An, Viet or either Huy.
The empty GitHub Issues list is not a task-completion tracker. Merge time or a
planned workbook date does not prove all acceptance criteria completed.

## New integration deliverables

| Task / gate | Addition | Boundary |
| --- | --- | --- |
| 1.07 / PB03 | Read-only Git adapter, NUL name-status parser, actual Git fixture tests | Explicit SHA and configurable rename threshold; no source execution |
| G1 dependency spike | Python AST symbols/imports/call observations | Incomplete static analysis reported, not a sound transitive impact engine |
| 1.09 / PB19 | rag-scope.md | Corpus/provenance/secrets/injection/leakage design, no index/provider chosen |
| G1 environment | Internal validated ExecutionConfig | Separate from public contracts; finite bounds, fixed command/argument allowlist |
| G1 worker | Docker owned-fixture adapter/entrypoint, image build recipe and run_g1.ps1 | Isolated collection and single-test mechanics only; no host fallback |
| 1.12 | This evidence ledger, git-diff-spike.md and g1-runbook.md | Current snapshot, not fabricated acceptance by a person |

Shared public models/OpenAPI/generated types, API/CLI wiring, DB/provider,
frontend, manifests/locks and existing source CI are unchanged by this integration.
New code is experimental and is not exposed as a product endpoint.

## Local verification ledger

Commands run from the integration checkout under the chat's work directory.
Python 3.14.5, locked dependencies installed with uv 0.12.23. The explicit Python
executable is D:/C1.SE26/Repo/.venv/Scripts/python.exe; PYTHONPATH points to the
integration checkout's backend/src so the changed source is actually exercised.

| Command / observation | Result | Limit |
| --- | --- | --- |
| uv sync --locked in D:/C1.SE26/Repo | PASS, 25 packages installed from unchanged lock | Clean local backend setup; not a Docker image |
| Initial pytest -q -p no:cacheprovider | 28 pass, 2 errors | Existing CLI tmp_path Windows ACL setup failure |
| Focused Git/config tests after implementation | 49 pass | Actual local Git histories; no candidate execution |
| Worker tests including bounded host process I/O | 17 pass | Simulated Docker boundary plus real trusted subprocess timeout/output-cap checks |
| Default full pytest after initial integration | 90 pass, 2 errors | Same two CLI setup ACL errors, no failing assertions |
| Diagnostic full pytest using external pytest_temp_compat fixture | 98 pass, 1 warning | This snapshot predates final additional cases; external fixture only replaces temp-directory allocation, not test assertions; not the default CI gate |
| Ruff check | PASS at recorded stage | Final result appended after final edits |
| Backend contract export --check | PASS | Public schema/demo consistency, not worker integration |
| Initial G1 attempt before Docker install | blocked / docker_unavailable, exit 2 | Fixture Git/diff/AST ran; Docker collection/execution did not |
| Docker after user installation | Client 28.5.1, engine named pipe access denied in sandbox | Does not establish Docker engine failure in the user's own terminal |

Final check results and actual user-run G1 evidence are recorded below when observed.
Do not copy expected results into this ledger. Product tests are not benchmark
evaluation; unknown metrics/time/cost remain null/N/A. FastAPI's pre-existing
Starlette/httpx deprecation warning is not repaired by unrelated dependency changes.

### Latest checks after the runner error classification fix

- Ruff check: PASS; Ruff format --check: 116 files already formatted.
- Default full pytest: 99 passed, 2 setup errors, 1 warning; exit 1. Both errors are
  the unchanged CLI tmp_path Windows ACL failure. No assertion failure observed.
- Diagnostic full pytest with the external temp-allocation fixture: 101 passed,
  1 warning, exit 0. No repository conftest/assertion/gate changed to obtain this.
- Backend contract exporter --check: exit 0. New Markdown local links/fences/UTF-8/
  whitespace: PASS. PowerShell run_g1.ps1 parsed with no syntax errors.
- Frontend runtime obtained from official nodejs.org: Node 22.14.0, archive SHA256
  checked against upstream SHASUMS256.txt. npm ci failed at dependency install
  script spawn with EPERM in the sandbox, before a usable installation completed.
  A direct typecheck attempt then reported missing TypeScript module. No frontend
  lint/typecheck/build success claimed; no lockfile/engine changed to hide it.
- Docker Desktop installed by user: client 28.5.1 at the standard binary location.
  Agent sandbox cannot access dockerDesktopLinuxEngine named pipe. A named-pipe
  permission request cannot be represented by the permission tool. No Docker
  security settings, ACLs or TCP exposure changed. User was given run_g1.ps1 to
  execute in their own authorized terminal; actual runtime evidence remains pending.

The runtime-termination reason is distinct from Docker exit code 125: container
startup failure must not be mislabeled output_limit. Structured pytest events use
an explicit newline so normal pytest progress cannot corrupt their line prefix.

### First user-terminal Docker run

User ran scripts/run_g1.ps1 in their own PowerShell. Image build succeeded using
local image sha256:b1c2bb5bf34631fe09e32a382b8936a4582656c4675560b0c2d2b01f457494da.
Artifact var/g1/33909cb369804912b706a9d556ce58b1/evidence.json records base
0a01885a3ae8b7e787fa75cd63d42bad04112646, target
2cf72f1e74d27f001399fa884b95d31cee59a71d, a modified module.py, and a complete
inventory of two pytest IDs. Selected test test_ok returned exit 0 but no parseable
result event was retained; G1 correctly remained failed rather than assuming pass.
The newline/event-prefix fix has a focused regression test and must be validated
by a new runtime artifact. Dockerfile's empty default base-image ARG was also
replaced with the verified immutable digest to remove InvalidDefaultArgInFrom.
Focused worker tests after this correction: 19 passed, exit 0.

### Successful isolated fixture run

Verified user-terminal artifact: var/g1/982f571662ec4b4689e4d5f2fc64dfd0/evidence.json.
Start 2026-10-24T09:10:52.839354Z; finish 2026-10-24T09:10:55.080738Z (16:10 local).
Result: demonstrated_on_owned_fixture. Base c7e491e31afc59a7e8bdceb87932df25c032459f;
target 63cefe29e3db93af78c5fa64a716187e583641b0. Two discovered target nodeids,
selected tests/test_demo.py::test_ok; one matching call event passed, exit 0.
Selection artifact was frozen at 2026-10-24T09:10:54.369974Z before the execution
result. Snapshot hash 9260c63f71c355b8785128078c6d9ebeb75151bdba510b07f7e195d50c270753,
inventory hash 1e725b23191973a5df630b8b8aec2f3e24a8a66f6b2e1d8134f796cecb5ebb52.
Local image sha256:4d6a981d5bc2a2663462e43723a4cf22741d686d076ecefa776e223dea98c59a.

This confirms Git/diff/AST/discovery/single-test mechanics on an owned fixture in
the configured container. It is not measured external-candidate compatibility,
fault detection, final cohort evaluation or a production hostile-code guarantee.
Afterwards an additional Git symlink-entry regression test exposed unsupported
tree metadata being accepted as ordinary source; the adapter now validates
regular-file modes using literal pathspecs before exposing diff/source. Actual
Git fixture tests cover this behavior. A final source/G1 recheck is prepared in
scripts/verify_sprint1.ps1, without diagnostic pytest fixtures.

## Candidate and research source observations

TinyDB read-only fetch: target edff96aeb2616402e9489d46e90a592c05565621, parent
0ba5727f2d915dedafb192e92f65dd64a21e3411, MIT LICENSE and pytest configuration
read from committed objects. No external code installed/imported/executed.

Bibliographic metadata for Gregg Rothermel and Mary Jean Harrold, "A safe,
efficient regression test selection technique", ACM Transactions on Software
Engineering and Methodology (April 1997), DOI
[10.1145/248233.248262](https://doi.org/10.1145/248233.248262), was verified via
the Crossref DOI record on 2026-10-24. This confirms publication identity only;
the paper's complete contents and empirical claims were not reviewed here.
Do not cite it as evidence of measured SmartRegression accuracy or a literature
review completed in full. Huy's RQ/protocol drafts remain the source for the
proposed five-method comparison and research validity requirements.

Python 3.14-slim upstream image index digest was retrieved from the official
Docker registry on 2026-10-24:
sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8.
The index contains linux/amd64. Actual locally built image ID belongs in the
runtime evidence; verifying registry metadata is not evidence that an image ran.

## Decision and acceptance boundaries

Accepted by existing ADR 0002: Python/pytest input choice. Authorized in this
session: local Sprint 1 implementation/design and Khanh branch publication.
Experimental choices (50 percent rename tests, owned-fixture image/limits and
worker command protocol) are bounded spike settings, not new product-wide policy.
D06-D09 and unapproved revision/lifecycle decisions stay pending. No GitHub
permission, branch protection, secret or deployment setting has been changed.

Still required before claiming full Sprint 1 acceptance: review of new integration
code/docs by humans, external-candidate runtime where required, and group decisions
explicitly identified as pending in the guide/protocol. Reviewers must validate
the research sources, dataset/cohort/budget plan and any decision that affects the
next sprint. Agent self-review is not an independent member review.

AI disclosure: Codex inspected source/PRs/rules, wrote new spike code/tests/design
and performed local checks for Tran Hung Khanh. Proposal Appendix C/D was read;
members remain responsible for understanding, verification and disclosure. No
signature, contributor percentage or mentor approval is supplied by this work.

## Acceptance matrix for all twelve tasks

| Task | Engineering deliverable now available | Remaining acceptance boundary |
| --- | --- | --- |
| 1.01 | Huy's RQs/five baselines/metric definitions, plus verified publication metadata | Complete literature reading and independent research review |
| 1.02 | Viet's merged screening, leakage/split and label-adjudication checklist | Candidate/data acceptance by group; no labels fabricated |
| 1.03 | Viet's merged candidate shortlist, TinyDB license/SHA read-only cross-check | External-candidate build/discovery/runtime feasibility still to be measured |
| 1.04 | Existing access classifier with mock success/auth/error cases, real public fetch observation | Live private access and production credential handling not claimed |
| 1.05 | Khanh's merged test-environment design; internal fixture config validator tested separately for G1 | Production input versions/plugins/limits require evidence and acceptance |
| 1.06 | An's merged frozen revision and PR semantics design | Q01-Q10 production decisions remain at the source's documented status |
| 1.07 | New read-only diff/regular-source validation and actual Git fixture coverage | Human review and broader unsupported/object-format cases |
| 1.08 | Huy's tested immutable lifecycle prototype and design | No persistence/concurrency/live worker service claimed |
| 1.09 | New RAG scope/provenance/secret/injection/leakage design | Pham Phan Hoang Huy / An review; provider/index choice remains separate |
| 1.10 | Khanh's merged conservative selection/fallback decision table | Final policy acceptance; production selector is outside this design task |
| 1.11 | Huy's protocol/report template, environment/fallback/RAG handoffs supplied | Group pre-run sample/budget/repeat choices and independent review |
| 1.12 | This integration evidence ledger, G1 success and explicit failure history | Group review/acceptance, not an agent marking itself approved |

Member-assigned tasks remain attributed to their original owners. New integration
assistance and experimental code are disclosed explicitly. Engineering artifacts
for the scoped Sprint 1 spike are available, with remaining human/research/candidate
runtime conditions visible rather than marked complete.
