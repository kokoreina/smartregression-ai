# 2.08/2.09 runtime verification — 2026-11-04

Khánh ran `scripts/inventory/verify_complete.ps1` from ordinary Windows PowerShell,
using the existing locked backend environment at
`D:\C1.SE26\Repo-Sprint2-Khanh-2.20\.venv\Scripts\python.exe`.
Host: Python 3.14.5, pytest 9.1.1, pluggy 1.6.0. The agent inspected the resulting
JSON ledgers and JUnit and compared configuration hashes with the current collector.
Source runtime behavior was unchanged after this successful run. This is local
verification and self-review, not independent approval or benchmark evidence.

## Results

| Check | Actual result |
| --- | --- |
| Default pytest | 521 passed, 72 skipped, one existing Starlette/httpx warning, 59.08s |
| Ruff check / format | Passed; 213 files formatted |
| Contract export check | Passed, no generated changes |
| sqlparse | Offline wheel build plus two completed collections; 509 exact ordered IDs each |
| TinyDB | Offline wheel build plus two completed collections; 228 exact ordered IDs each |
| Owned Docker fixtures | 12/12 expected statuses/IDs/error codes matched |
| Actual PostgreSQL 17.11 | 71 passed, zero failures/errors/skips; pytest CLI 6.72s |
| Migrations | Fresh head, populated upgrade and reapply passed at `20261104_03` |
| Recovery | Exact restored metadata rows, including inventory/cases; report artifact digest/catalog matched |
| Cleanup | Candidate build/collection and dedicated DB container removal recorded as successful |

The 72 default skips are 71 explicitly opt-in PostgreSQL cases plus the existing
POSIX FIFO test unavailable on Windows. The later dedicated container invocation
actually ran all 71 database cases, including both real candidate inventories.
JUnit records 71 tests, zero errors/failures/skips (suite time 5.729s; CLI includes
additional startup). No unrelated tests or limits were disabled to obtain a pass.

Fixture cases: success, empty, failed import, partial, duplicate, timeout,
output_limit, plugin_error, missing_result, malformed_result, unsupported_id,
native_ids. Trusted empty partial checkpoints and failed-payload consumer rejection
also have focused validation/DB cases; no timeout streaming checkpoint is claimed.
Failure diagnostics never became a successful empty inventory or eligible IDs.

## Input and environment identity

Exact repository/commit/tree scope is in the
[accepted decisions](../../development/task-2.08-2.09-decisions.md).
The host independently verified every Git blob and the complete accepted Git tree.

Candidate image ID:
`sha256:70f895149ae1b096c39346e5680b7df0fb35b7e062e9dfd2a8c25058b14f1a73`.
Dependency lock SHA-256:
`9c798c79b53ac36ed4afb9fef3c46e2bf6c3bf059dd2b225692d1a58dee8728d`.
Image Python 3.14.3; pinned packages: pytest 9.1.1, pytest-cov 7.0.0,
coverage 7.17.0, build 1.3.0, hatchling 1.27.0, iniconfig 2.3.1,
packaging 26.3, pathspec 1.1.1, pluggy 1.7.0, pygments 2.21.0,
pyproject-hooks 1.3.3, trove-classifiers 2026.9.21.13; base-image pip 25.3.
Input dependencies are separate from the backend lock and are not installed during
collection. Only TinyDB explicitly loads pytest_cov.plugin; autoload is disabled.

| Identity | sqlparse | TinyDB |
| --- | --- | --- |
| Profile/config SHA-256 | `91912ee63630920c95857f98b74983691a230ca6617f3b2fea222b45340466b8` | `f16615e21401f7df993ca169624610857f1c28cede9d5a32c8be5ee3693779eb` |
| Ordered ID array SHA-256 | `a088a4f30f867c368762c3ab4e75bf1d772e8763260fd62bde6ed2c20542f6d7` | `4f8cd2c2610eb5f6545a8c808a3b966acb99cde8675e23e3437da03b88169c2e` |
| Downloaded archive SHA-256 | `9b580056783fd97c37c04da7acd40676bb57dd2617317c83552f15285700efd3` | `99f6de856e39a5832a3e82fa75ec68150b4d20fb255dcffe82ede8597d725b6e` |

Ordered-array digests use the project's canonical JSON bytes, including its final
newline. Both new collections match exact IDs/order and historical counts 509/228.
Complete historical ID arrays were not present in committed Sprint 1 evidence;
exact equality to those unavailable arrays is not claimed. This harness downloads
from codeload, while the earlier spike used GitHub's API tarball endpoint; archive
hashes differ, but complete Git blob/tree identity matches the fixed commits.
Collection does not execute test bodies; this run makes no new claim about TinyDB's
optional PyYAML execution skip or full-suite pass counts.

Actual Docker inspection/runtime probes checked the accepted isolation/resource
profile. This is evidence on two reviewed snapshots, not proof for hostile arbitrary
repositories, production authorization, fault retention, safe selection or savings.

## Local primary records

All paths below are relative to this checkout, ignored, and intentionally not
committed. Preserve them for reviewers; do not infer raw artifacts are available
merely by cloning the Markdown record.

- Candidates: `var/candidate-inventory-verification-beed6f8ffd9841e7aa0f5157f66414e7/evidence.json`;
  source/manifests, per-attempt observations/logs and frozen inventory writes beside it.
- Fixtures: `var/inventory-verification-c1bebd24134949d5b378ae0b5a0b130d/evidence.json`;
  per-case canonical reports beside it.
- DB: `var/storage-verification-52dff2316d4e482b92a67b07af8e7b7a/evidence.json`;
  `postgresql-tests.xml`, recovery artifact fixture and dump beside it.
- Recovery dump SHA-256:
  `4cacd1ae53709ca116ae2f59997336541aa0fd98ddd2adbf5c563c1bb80611cd`.

Candidate image ID, config and native IDs round-tripped through the canonical
contract, actual PostgreSQL adapter and guarded consumer. DB tests also cover
nullable pre-acquisition snapshots, scoped FKs, states, row counts/order, exact
native text/digests, retry/conflicts, concurrent writes, late rollback, simulated
digest collision rejection and forbidden runtime UPDATE/DELETE/DDL. These results
do not implement or accept task 2.16 component mapping or other members' tasks.

Code assistance: OpenAI Codex for implementation, test design, evidence inspection
and this record. Khánh remains responsible for understanding the submission.
Independent reviewer/academic acceptance is not asserted.
