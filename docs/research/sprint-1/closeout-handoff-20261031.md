# Handoff — Sprint 1 local closeout, 2026-10-31

## Task, authority and baseline

User requested completion of the local technical/doc package for 1.01–1.12/G1
under research foundation + technical spike. See [scope/decisions](closeout-decisions.md)
and [full current matrix](review.md). **NOT READY FOR FORMAL ACCEPTANCE:** new changes
need real review, the bounded revision/G1/candidate proposal needs acceptance, and
remote integration/CI remain. All currently executable scoped work has been prepared
and verified locally; this is not a claim that the sprint is approved.

Publication follow-up on 2026-10-31: the user explicitly requested commit and push
of this package so they can merge into main. That supersedes the original no-commit/
no-push limit for this branch only; it does not authorize main merge or sprint
acceptance. Earlier local-only statements below describe the preparation session.

- Cwd: `D:/smart-regression-ai`; branch `work/sprint-1-local-closeout-20261031`.
- Preparation HEAD before publication: `c3ac49aba58b9f50f933dc0b02aead28ee3d4217`.
- Main read directly from GitHub: `e937f669fefada31d5254b355f92f24e88e41725`.
- Starting tree equals merged PR #10 tree `b37d1086af2f73882dcdf3367da40fe46fbcdd69`.
  Its destination was the technical branch, so it is not in main. Already-present
  research/RAG content is reused; no manual duplicate integration was necessary.
- Existing untracked `start-cliproxy-management.bat` preserved and excluded from work.
- No AGENTS child was found. No sub-agent, commit, push, PR merge, settings change,
  deployment, paid model call or Office edit. Docker was opened by the user after
  the initial diagnostic; the agent did not install/reconfigure system software.

Profiles/rules used: Coordinator, QA/Research, DevOps/Runner, Regression Selection,
RAG/LLM; root AGENTS and rules 00/01/02/03/04/05/06/07/08/09/10/11/12/13 as relevant.
Skills: security-review, evaluation-integrity, focused TDD, api-contracts for the
internal harness observations, systematic-debugging for runtime failures. Product
contract documentation and producer/consumer boundary were inspected; public models,
OpenAPI/types, API/CLI, frontend, manifests/locks and G1 code/profile are unchanged.

## Changes and why

At baseline the primary gaps were candidate execution, stale five-task review,
unreconciled Q01–Q10, and research/RAG content missing from remote main. Candidate
and G1 observations were not conflated with production features or dataset metrics.

- `scripts/candidates/`: narrow orchestration for two fixed public commit snapshots,
  archive/tree/blob verification, host path guards, separate dependency Dockerfile,
  offline build/collection/test stages, enforced quotas/seccomp and cleanup.
- `backend/tests/unit/test_candidate_spike.py`: five meaningful tests for traversal/
  Windows paths, symlink and snapshot mismatch/incompleteness, matching inventories,
  unknown IDs, real selected pass and cleanup on timeout. No external code runs on host.
- `candidate-reproduction.md`: exact candidate/environment/outcomes, failed attempts,
  artifact hashes, time boundaries and primary/backup recommendation.
- `selection-policy.md` / `rag-scope.md`: invalid evidence affecting selection now
  aligns with Proposal §12.6 full-suite/stop rather than dependency-only fallback;
  provider failure, invalid provenance, duplicate IDs and budget precedence explicit.
- Screening/protocol/template: pilot tuning allowed, held-out protected; evidence
  denominator and accepted-cohort vs attempted-run fallback ratios distinguished.
- Revision doc/`closeout-decisions.md`: review of original draft acknowledged; Q01–Q10
  reconciled with actual implementation without manufacturing accepted decisions.
- `review.md`: all twelve tasks, current G1, real historical PR reviews, demo steps,
  tracking recommendations and acceptance boundaries. Historical review remains
  linked to its immutable Git revision and original handoffs.
- Guide/decision register/verified commands/README: current scope/evidence linked;
  historical bootstrap snapshots retained; one session handoff is this file.

Internal observation format is used only by worker → candidate orchestrator and
tests: exit_code, IDs, phase reports (including was_xfail), durations, isolation,
versions and timestamps; ledger adds source/image/harness hashes and status. It is
not an AnalysisReport/API shape and has no public schema migration. Raw bounded
candidate output stays local under ignored var; shared docs contain summary/hash
evidence, not candidate source or credentials.

## Commands and actual results

All dated 2026-10-31, cwd root. Source image build uses network only to install
declared dependencies; candidate build hooks/collection/tests run network none.

| Command/check | Result actually observed | Limits |
| --- | --- | --- |
| `gh api repos/kokoreina/smartregression-ai/commits/main`; merged-only PR query | main `e937f66`; approvals/destinations recorded in review | Open PRs neither listed nor inspected; initial sandbox proxy failed, read-only retry with tool permission succeeded |
| `gh run list --repo kokoreina/smartregression-ai --branch main --limit 1` | [main CI success](https://github.com/kokoreina/smartregression-ai/actions/runs/40091611121) | Historical run for exact main commit; no CI claim for uncommitted changes |
| `git switch -c work/sprint-1-local-closeout-20261031` | branch created | Initial .git write blocked by sandbox; permitted retry succeeded; no commit |
| Fixed GitHub commit/tree/config/license reads | blob bytes verified; source-inspection evidence in `var/sprint1-closeout-20261031` | Source inspection, not execution; earlier source record's Docker-blocked state is historical |
| Focused pytest before implementation | collection failed: missing scripts.candidates | TDD red phase, no environment ambiguity |
| `.venv/Scripts/python.exe -m pytest backend/tests/unit/test_candidate_spike.py -q -p no:cacheprovider --tb=short` after implementation | **5 passed** | Task-authored archive/JSON fixtures and mocked Docker-tool boundary only |
| `docker version --format '{{.Server.Version}}'` | Initially engine pipe missing; later **27.3.1** after user opened Desktop | No host execution fallback |
| `docker build --network=default -t smartregression-candidates:sprint1-20261031 -f scripts/candidates/Dockerfile scripts/candidates` | exit 0; image `sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e` | Pinned base/top-level tools; transitive rebuild not hash-locked |
| Candidate commands below, final harness | Both exit 0: wheel build, matching double inventory, selected test and full suite | sqlparse 509 IDs: 506 pass/2 xfail/1 xpass; TinyDB 228: 227 pass/1 optional YAML skip; no fault claim |
| G1 command below | exit 0, synthetic checks complete | 5 IDs; guard/timeout/output/empty/error checks; not general runner |
| `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=short` final | **54 passed**, 1 Starlette/httpx deprecation warning, 15.38s | Existing environment with permitted temp access; no clean dependency install claimed |
| `.venv/Scripts/pytest.exe -q -p no:cacheprovider --tb=short` (CI-style entrypoint) | **54 passed**, 1 warning | New test module explicitly loads the trusted script by path so installed pytest need not find scripts as a package |
| `.venv/Scripts/ruff.exe check .` / `format --check .` | pass / 124 files already formatted at final check | Formatting/lint only |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | exit 0 | Public schema/fixture consistency; no generated writes |
| `.venv/Scripts/python.exe -m smartregression.cli.main validate-report examples/reports/demo.json` | exit 0, `Valid report [DEMO]` | Bootstrap DEMO, not candidate report |
| `docker ps -a --filter name=smartregression-candidate- ...` and G1 filter | no named containers left | Images and local artifacts retained |
| `.venv/Scripts/python.exe var/sprint1-closeout-20261031/verify_delivery.py` | 197 local links, Markdown fences/tables/whitespace and candidate harness hash/timestamp checks passed; git diff --check passed | Temporary task checker, not a project dependency or general Markdown validator |
| `.venv/Scripts/python.exe var/sprint1-closeout-20261031/prepare_patches.py` | main-integration.patch and session.patch include all 10 new files; reverse apply --check passed against current delivery | No staging/commit/apply performed; pre-existing untracked bat and ignored artifacts excluded |

Final candidate and G1 commands (use NEW output names when reproducing):

```powershell
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate sqlparse --image sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e --output var/candidate-sqlparse-20261031-final --full-suite
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate tinydb --image sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e --output var/candidate-tinydb-20261031-final --full-suite
.venv/Scripts/python.exe scripts/g1/run_spike.py --image sha256:3cd7035210103639f0e52d72b96628a9ef22aea527e5b13f346117ee79cf88ad --output var/g1-closeout-20261031
```

Final candidate observer durations: sqlparse full 11.921s, TinyDB full 5.558s;
these include observer/pytest startup, exclude Docker preparation and image/source
download, and are not a method benchmark or savings calculation. Earlier attempts
have different durations and remain reported separately.

## Failures, self-review and limits

- sqlparse initial build failed because candidate seccomp lacked rmdir; build trace
  isolated temporary-directory cleanup. TinyDB discovery then failed on coverage
  SQLite I/O; an isolated os.pwrite probe confirmed denied pwrite64. Candidate-only
  profile adds these file operations plus build process creation with namespace
  flags restricted. Network, mounts, user and resource gates were retained.
- Retained attempts `var/candidate-sqlparse-20261031-a/b` and TinyDB `-a/b` distinguish
  environment failure, development success and final measured source/profile hashes.
  The one shell-quoted diagnostic command that produced SyntaxError is not evidence
  for a syscall; the subsequent argv-based probe is the relevant diagnostic.
- CI-style pytest initially could not import scripts because unlike python -m pytest
  it does not guarantee repository root on sys.path. The new test now loads only its
  trusted harness file explicitly; no global import-path/manifest change or test skip.
- Host GitHub/source → bounded gh output → complete tree/blob verification → private
  snapshot → read-only Docker mount → offline build/pytest → validated observations.
  No candidate code is imported/executed by host tests or API. Docker daemon remains
  a privileged external host service, not a workload socket. Containers share a kernel;
  concurrent host snapshot mutation and hostile arbitrary repo support are out of scope.
- Unit guards and measured runtime probes are agent self-review, not an independent
  security audit. No scanner, OOM/PID stress test, cross-platform candidate matrix,
  wheel-install smoke, complete historical fault cohort or model evaluation claimed.
- Frontend checks/browser not rerun: frontend/config/generated types unchanged in
  session; main CI is historical evidence only. External papers reused from prior
  audited sections; no new systematic literature review. Office text/cells only,
  not layout/formula recalculation; workbook remains unchanged.

## Integration, tracking and next person

For reviewers, compare both `git diff e937f669fefada31d5254b355f92f24e88e41725 --`
(full delivery including already-committed #10 content) and `git diff HEAD --`
(session changes). New untracked candidate scripts/tests/docs must also be included
in the eventual review; Git's ordinary diff omits them until staged. Do not include
the pre-existing start-cliproxy-management.bat or ignored var artifacts. The task
prepares a local delivery; nothing has been integrated into remote main here.
Complete patches (including new files) and hash manifests are available locally at
`var/sprint1-closeout-20261031/main-integration.patch`, `session.patch`,
`delivery-manifest.json` and `patch-manifest.json`. These are review aids, not commits;
regenerate them if any handed-off file changes. No candidate source/log is included.

1. An/Huy and affected consumers review final 1.06 definitions/Q01–Q10; accept or
   explicitly revise the bounded G1 snapshot equivalence and candidate proposal.
2. Human reviewer examines new harness/profile/docs, including marker/skip limits
   and corrected fallback. Old PR approvals do not cover this new diff.
3. Authorized maintainer may then commit/push/prepare integration with full #10
   content, run CI for the resulting commit and record sprint acceptance. Those
   operations require a separate instruction; no automatic approval is inferred.
4. Update workbook/board statuses from accepted AC evidence. Completed hours use
   workbook convention, actual effort must come from people, neither from this agent.
   Workbook read-only snapshot still shows 12 Not started and zero completed/effort.
5. Before experiments: resolve 30 vs 50 target, candidate enrollment, split, model,
   budget/repeats/statistics and independent labels. These are future-stage decisions,
   not reasons to fabricate a current dataset or implement production modules.

Codex assisted coding, tests, debugging, source inspection and reporting. Adoption
requires human understanding and review; no contribution percentages/signatures or
mentor approval supplied. No task-created service/container remains running; Docker
Desktop started by the user and the two local images/artifacts are retained.
