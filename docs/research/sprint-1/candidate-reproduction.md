# 1.03 — Candidate reproducibility, 2026-10-31

This is evidence for two proposed spike repositories, not dataset enrollment or
method evaluation. sqlparse is proposed primary because of its parsing modules and
larger inventory; TinyDB is backup with a smaller suite. No fault labels, commit-pair
cohort, impact accuracy, test reduction or time savings are inferred from these runs.

## Frozen source and license

| Candidate | Commit / Git tree | Source and environment evidence |
| --- | --- | --- |
| [sqlparse](https://github.com/andialbrecht/sqlparse) | `60cdc649726bf1bc4f1b336050560b336da715ec` / `0652386b2d4a79d8f37b9c4ab2e8cfcc41ab32d1` | [BSD-3-Clause LICENSE](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/LICENSE), [pyproject](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/pyproject.toml), [fixtures](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/tests/conftest.py); Python ≥3.10, Hatchling; 93 regular snapshot files, 10 `tests/test_*.py` files |
| [TinyDB](https://github.com/msiemens/tinydb) | `edff96aeb2616402e9489d46e90a592c05565621` / `52a3d82ceab13b0da98cc3b2808218ac02fde924` | [MIT LICENSE](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/LICENSE), [pyproject](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/pyproject.toml), [pytest.ini](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/pytest.ini); Python ≥3.10,<4; pytest~=9.0 and pytest-cov~=7.0 in dev group; 7 `tests/test_*.py` files |

Commit/tree/config/license/selected test source were read through GitHub API in this
session. Source bytes were verified against Git blob IDs; runtime materialization
requires a complete tree with every archive file matching its blob. There was no
candidate import, collection or build hook on the host. License notices remain in
the local snapshots; this does not audit every historical revision or third-party
data license. The earlier candidate document's 12/9 file estimates are not inventory
counts and are superseded only for these measured snapshots.

## Reproduction and time boundaries

Use [harness commands and threat model](../../../scripts/candidates/README.md).
Image: `sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e`.
Observed Linux container Python 3.14.3, pytest 9.1.1, pytest-cov 7.0.0,
coverage 7.17.0, build 1.3.0, hatchling 1.27.0, packaging 26.3, pluggy 1.7.0.
This input version choice is supported by both inspected configs, not imposed by
the SmartRegression host interpreter. Other versions/plugins remain unverified.

Each stage runs in a new offline container with the same read-only source snapshot.
Wheel build uses preinstalled dependencies and no-isolation, within the Docker
boundary. Tests execute from source with PYTHONPATH; built wheel installation,
all optional dev plugins, Windows/macOS input execution and full history are untested.
TinyDB retains its coverage configuration; pycodestyle/mypy/docs plugins are outside
this pytest execution environment. PyYAML is absent and its optional test is skipped.

Primary records: `selection.json`, `observations.json` and bounded stage logs under
`var/candidate-*-20261031-final/`; these are ignored local artifacts, not committed
source or durable shared storage. Full-suite pytest time is execution-only; observer
duration additionally includes pytest startup, and host timestamps include Docker
attachment/observation. None includes download/image-build/analysis overhead, so none
is an end-to-end savings comparison. No repeats beyond the two inventories and one
single/full execution per final run are claimed; timing is one observation.

## Final observed results

All commands exited 0 on the final harness/profile. Artifact hashes bind the exact
uncommitted runner/observer/seccomp versions; raw logs/JSON retain timestamps.

| Candidate / artifact directory | Build / two collections | Selected smoke test | Full-suite observation |
| --- | --- | --- | --- |
| sqlparse / `var/candidate-sqlparse-20261031-final` | Wheel built; 509 identical ordered IDs; collections 5.592s / 5.510s observer durations | `tests/test_parse.py::test_parse_tokenize`; setup/call/teardown passed; frozen before start | 506 passed, 2 xfailed, 1 xpassed; observer 11.921s; native markers retained |
| TinyDB / `var/candidate-tinydb-20261031-final` | Wheel built; 228 identical ordered IDs; collections 4.752s / 4.024s observer durations | `tests/test_tinydb.py::test_drop_tables[memory]`; setup/call/teardown passed; frozen before start | 227 passed, 1 skipped; observer 5.558s; optional `test_yaml` skips because PyYAML is absent |

sqlparse's full inventory is 509, not 506; the latter is the ordinary passed count.
TinyDB's full inventory is 228, not 227. Exit 0 is not a claim that every test passed
or that an xpass identifies a verified fault. Outcome categories remain distinct.
Final run start/end UTC: sqlparse 07:00:21–07:01:18, TinyDB 07:01:51–07:02:27,
2026-10-31 (local UTC+7: 14:00–14:02). No timing claim is generalized beyond these runs.

| Runtime identity | SHA-256 |
| --- | --- |
| sqlparse archive | `7ba92ce1ddb6340cc7d597a3d3c0fa0371bbc4e84fb560bb8c86a2dc846e284e` |
| TinyDB archive | `18abc0559c67f3c251f97e8503ab6605175f69fe710fd88da573980cda159d9c` |
| run_candidates.py | `0301e559ee1cfa7e42e9a9205f272122b4dd627b4e71ac88a36be6d908331ccc` |
| worker.py | `8bcd266d9726c1c42b957118e3f02d914276d9a49ddd35af54ac3f9f31ee7c0e` |
| seccomp.json | `050f509d855dc982fe2d521ed19d6023af2ebe21061cd0adb133180f1fc4c642` |

Docker inspect and in-container probes observed UID 65534, seccomp mode 2,
NoNewPrivs=1, loopback only, memory.max=536870912, pids.max=64 and CPU quota 1.
All named candidate/G1 containers were absent after runs. No OOM/PID/CPU stress
test or arbitrary-hostile-code isolation guarantee is claimed.

## Attempts retained

| Attempt | Observed outcome | Classification / action |
| --- | --- | --- |
| sqlparse `var/candidate-sqlparse-20261031-a` | Build exit 1; seccomp denied rmdir during temporary-directory cleanup | Environment failure, not a code fault. Separate probe/build log retained; added rmdir in candidate profile |
| sqlparse `var/candidate-sqlparse-20261031-b` | Build, both collections, single and full exited 0; 509 stable IDs; 506 passed, 2 xfailed, 1 xpassed | Successful development run; final run records final observer/profile hashes |
| TinyDB `var/candidate-tinydb-20261031-a` | Build exit 0, first collection exit 3 with 228 observed IDs; coverage SQLite disk I/O error | Failed discovery, not a valid inventory. Isolated os.pwrite probe confirmed missing pwrite64; added that file-write syscall under existing mount/quota constraints |
| TinyDB `var/candidate-tinydb-20261031-b` | Build, both collections, single and full exited 0; 228 stable IDs; 227 passed, 1 skipped | Successful development run; skip is upstream PyYAML-not-installed case; final run binds observer/profile hashes |

First diagnostics intentionally remain separate from final results. No candidate
configuration, test or assertion was removed to obtain a passing command. The
candidate profile adds only required process/temp-file operations to the G1 syscall
set; root/source read-only, network none, UID, capabilities and quotas were retained.
The G1 seccomp file and FixtureWorker are unchanged. See final measured results in
the [closeout handoff](closeout-handoff-20261031.md).

## Recommendation and limits

Both are suitable candidates to present for a bounded Python/pytest spike after
reviewing final evidence. Accepting them into the evaluation dataset is a separate
owner decision requiring historical pairs, reproducibility at those revisions and
independent labels. sqlparse's xpass/xfail markers and TinyDB's optional skip must
remain visible in any later eligibility policy. They do not confirm real faults.

The small runtimes may make analysis/LLM overhead exceed savings; retain negative
results rather than tuning the cohort to make AI look faster. Claims about model
contamination, 30/50 commit pairs, ≥15 faults and held-out performance remain unverified.
Codex assisted source inspection, harness, debugging and this report. Final changes
have agent self-review only; no new owner/mentor approval is asserted.
