# 2.16 verification — 2026-11-04

Khánh ran `scripts/mapping/verify.ps1` in ordinary Windows PowerShell on the task
branch based on main `53356e6ada1a145a3cb988a926928e838136e152`. The agent then
read both JSON evidence records, revalidated collection receipts against the
unchanged current collector/config hashes, compared exact two-run native IDs and
item.path metadata, and checked cleanup flags. No runtime implementation changed
after the successful run. Subsequent edits fixed test-helper loading for the console
`pytest` invocation used by CI and updated handoff documentation; production mapper
and observer bytes stayed unchanged.

## Observed results

- Default suite: **609 passed, 75 skipped**, one existing Starlette/httpx warning,
  63.67s. Of the skips, 74 require dedicated PostgreSQL opt-in and one is POSIX FIFO
  unavailable on Windows. SQL/schema/DB adapter code did not change in this task;
  this run does not claim renewed PostgreSQL acceptance.
- Ruff lint/format: passed, 230 Python files formatted. Exporter --check: passed,
  generated public OpenAPI/types unchanged. PowerShell syntax check passed.
- Focused mapping/receipt/Git tests: 45 passed; tests include 25 pure mapping cases,
  7 application/real-Git integration cases, 13 candidate transport tests.
  A subsequent console `pytest` check reproduced a test-helper import error hidden
  by `python -m pytest` adding the working directory to sys.path. The fixture now
  explicitly loads only the task-owned helper via importlib. After that fix,
  console pytest: 44 passed (non-Git subset); the real-Git case passed separately
  with the documented external sandbox temp fixture. Final Ruff lint/format pass
  (231 files). This diagnostic targeted check does not replace the full ordinary
  terminal run above; remote CI must still run against the publication commit.
- Candidate offline builds and two collections each: sqlparse 509 IDs, TinyDB
  228 IDs, matching exact values/order and item.path metadata between repetitions.
  All observed paths were available; metadata transport used `inventory/2` and
  observer `pytest-item-path/1`. Candidate build/collection cleanup flags passed.
- Mapping probes: both passed and rejected stale inventory receipts. Results
  deliberately remain partial with unresolved records; this is expected behavior.

| Probe fixture seed | Expected source-file relationship | Observed existing IDs / relationships |
| --- | --- | --- |
| sqlparse/lexer.py | tests/test_keywords.py, tests/test_parse.py | 94 native IDs / 94 routes |
| tinydb/operations.py | tests/test_operations.py, tests/test_tinydb.py | 128 native IDs / 128 routes |

Seeds are **synthetic changed-component fixtures** joined with actual collected
metadata and actual static graph/impact producers. They are not actual Git diffs,
benchmark cohorts, selected test sets, test outcomes or evidence of fault retention.
Expected file sets were authored before running; IDs were independently joined
from the inventory/observed path metadata, then compared with mapping output.

The output retains 467 unresolved records for the sqlparse probe and 134 for TinyDB.
These include unrelated observed test IDs and graph scope limitations; they are not
counts of unsupported tests alone and are not interpreted as safe exclusions.
File-level import reachability does not establish test-function call coverage.
Real changed-component acquisition/diff integration is separately verified using
the task-owned Git fixture and declared collector double in
`backend/tests/integration/test_component_test_mapping_flow.py`.

## Identity and local evidence

Candidate image ID:
`sha256:4a373a4d428c565f75a98ff23f9b826ba84db9e573be2eea3e6b60d371e965e9`.
The dependency manifest/lock, base Python digest and isolation/resource budgets
are unchanged from accepted inventory policy. The local image manifest identity
differs from the earlier build; both were actually inspected and are recorded per
run. Input runtime Python 3.14.3, pytest 9.1.1; actual locked package versions are in
candidate observations. Metadata is included in the existing 512 KiB output cap.

| Hash | sqlparse | TinyDB |
| --- | --- | --- |
| Collector configuration | `4c9588d537d34c29de6eed3441d3905c0067dba68a9a02a342309848a5e92d9a` | `1a84d1bbe6b9d4a8e372d5221bf268bccb8f1d37e8e6d6ab4d5d37d41dfee641` |
| Ordered IDs (project canonical JSON) | `a088a4f30f867c368762c3ab4e75bf1d772e8763260fd62bde6ed2c20542f6d7` | `4f8cd2c2610eb5f6545a8c808a3b966acb99cde8675e23e3437da03b88169c2e` |
| Source receipt (project canonical JSON) | `6fba9820ce867f2d9863fbf92b88a102627ba8f296da10efc2f8abddef65b377` | `2c882a52e02370f8a14d871072370a2332fea1a8010ff05b50880a322f7cf6f6` |
| Mapping file | `730011e6193f4177af46e280c4649901251dd07304f969e27b6a6a55a918bc48` | `f30b44e7ad874866928fa929088f8719a3758a9ede7ce78eec399bcf01fd7bb7` |

Ignored primary records relative to the checkout:

- `var/candidate-inventory-verification-0579bb8491144dea9e2e69d24e078e94/evidence.json`;
  snapshot manifests/source, collection logs/observations, inventory-write.json and
  test-sources.json beside it. Evidence file SHA-256:
  `144f24eae09a222684c202f9bede79116836eaa4ab699e86b602f3111853fe39`.
- `var/mapping-verification-a05e759cfda343b998c005a55ae3535c/evidence.json`;
  `sqlparse-mapping.json` and `tinydb-mapping.json` beside it.

Raw artifacts/source/logs remain local and are not supplied simply by cloning this
Markdown. No secrets or dump/source artifacts are committed. Full historical ID
arrays were not available in the committed Sprint 1 record; this run compares two
new exact arrays and records historical count comparison, not unsupported claims
of byte-identical equality with unavailable historical arrays.

OpenAI Codex assisted design, tests, implementation, evidence inspection and this
self-review record. Independent H2/consumer review and team acceptance remain
separate; no mentor approval or measured safety/performance claim is asserted.
