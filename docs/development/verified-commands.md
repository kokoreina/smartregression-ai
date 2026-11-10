# Lệnh đã đối chiếu với repository

## Task 3.15 contracts — 2026-11-10

Commands, reused environment, tests/consumer compatibility and actual results:
[task 3.15 handoff](task-3.15.md). The existing exporter/TypeScript generator now
also exports v3 workflow/request contracts; old API paths and v1/v2 schemas are
unchanged. No live-provider, DB migration or new browser acceptance is implied.

## Main integration for G0 — 2026-11-09

Fresh commands, actual results, environment failures and runtime artifacts are
recorded in [G0 integration](sprint-3-g0-integration.md). Older counts below apply
to their stated revision, not automatically to the main-integration candidate.
The historical Sprint 2 A07/A02/A03 browser waiver at completed-work `929b336`
means not performed, not browser pass; it does not cover Sprint 3.

## Sprint 2 completion acceptance checkpoint — 2026-11-09

Cwd `D:/smart-regression-ai/var/s2c`; same reused Python 3.14.3 and portable Git
as below. No clean dependency install is claimed.

```powershell
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --junitxml var/p6-final-full.xml --basetemp var/p6-final-full
python scripts/storage/run_checks.py
python scripts/integrity/verify.py --runtime-only
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
```

Default backend: **873 passed / 131 skipped**, one existing warning, exit 0.
Dedicated PostgreSQL: **131 passed / no skips**, exit 0, including actual candidate
CLI inventory/mapping/retrieval, conflicting and compatible concurrent writers,
legacy upgrade/exact replay, new migration `20261109_06`, restart and populated
metadata/artifact recovery. The default skips are 130 SQL cases subsequently run
in that campaign and one Windows-inapplicable POSIX FIFO test. One additional SQL
regression was added after default collection and passed in the dedicated campaign.
The last SQL-only read-order fix was exercised by the full SQL rerun. No skipped
case is counted as runtime acceptance. SQL inputs are the successful candidate and
mapping evidence variables described below; no external DSN is accepted.

The real isolated Docker integrity campaign passed **26 cases**; it deliberately
uses a recording SQL port and does not replace the real PostgreSQL campaign.
Ruff lint/format, exporter and diff checks passed. Failed intermediate runs, exact
evidence paths and observed timing limits are recorded in
[the completion plan](sprint-2-completion-plan.md).

Frontend used reused Node 22.14.0/npm 10.9.2 dependencies:

```powershell
npm --prefix frontend run contracts:check
npm --prefix frontend run lint
npm --prefix frontend run build
node frontend/scripts/test-reports.mjs <relative-sqlparse-report> <relative-tinydb-report>
node frontend/scripts/test-report-view.mjs <relative-sqlparse-report> <relative-tinydb-report>
```

The paths above are local generated P4 report inputs, not literal shell arguments.
Actual-input runs passed **87 validation / 13 SSR checks**; all 71 rejected
mutations were also rejected by backend validation. The normal contracts script
runs 85 validation / 11 SSR checks. Build includes TypeScript checking. All commands
exited 0. **SSR is not browser acceptance: A07 remains pending Browser access.**
The source UI is published for review as Draft PR #61.

## Sprint 2 completion workflow/mapping/retrieval — 2026-11-09

Cwd `D:/smart-regression-ai/var/s2c`, Python 3.14.3 reused from
`D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe`,
`PYTHONPATH=backend/src`, `PYTHONDONTWRITEBYTECODE=1`, portable Git prepended.
No clean install is claimed. Exact source/evidence and intermediate failures are in
[the completion plan](sprint-2-completion-plan.md).

```powershell
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp var/p4-full
python scripts/storage/run_checks.py
ruff check .
ruff format --check .
python scripts/export_contracts.py --check
```

Full backend: **867 passed / 120 skipped**, one existing warning. Dedicated SQL
campaign: **119 passed / no skips**, including actual candidate CLI collection,
mapping and retrieval; restart and populated metadata/artifact restore queries
passed. The SQL command used `SMARTREGRESSION_INVENTORY_CANDIDATES` and
`SMARTREGRESSION_MAPPING_WORKFLOW` pointing to successful current-checkout evidence
from `verify_candidates.py` and `scripts/mapping/verify_workflow.py`. Without those
inputs the four candidate cases skip and are not acceptance. No external DSN is
accepted; the script provisions and removes only its owned PostgreSQL container.

CLI options/use are in [mapping](task-2.13-mapping.md) and
[retrieval](task-2.13-retrieval.md). Browser A07 and final integrated closeout are
separate remaining gates. Old dated results below remain historical.

## Integrity 2.19 ngày 2026-11-05

`scripts/integrity/verify.ps1 -PythonExe <locked-backend-python>` chạy full suite,
Ruff/format/contracts rồi cùng 26 ca cross-module qua Docker fixture worker.
Full suite quan sát 748 passed/94 opt-in/platform skips; source checks pass.
Sau sửa Windows fixture paths/ACL workspace, `-RuntimeOnly` đạt 26 passed, 82.99s,
actual worker và cleanup kiểm chứng. Không chạy lại default suite sau sửa test setup;
không đổi production source/DB/contracts. Default suite dùng transport double;
runtime dùng Docker thật, SQL vẫn recording port. Evidence/giới hạn ở
[handoff KH](task-2.19-khanh.md) và
[verification](../research/sprint-2/integrity-verification-20261105.md).

## Mapping 2.16 ngày 2026-11-04

`scripts/mapping/verify.ps1 -PythonExe <locked-backend-python>` chạy từ root trong
PowerShell thường với Linux Docker: default suite 609 passed/75 existing skips,
Ruff/format/contracts pass; hai candidate collect hai lần với metadata item.path,
mapping probes và stale-receipt rejection pass. Probe dùng synthetic component seeds,
không là actual diff hoặc test-selection benchmark. Chi tiết:
[task](task-2.16.md), [evidence](../research/sprint-2/mapping-verification-20261104.md).
`-RuntimeOnly` phục vụ debug, không thay default suite; không đổi DB/migrations.

## Xuất bản 2.13 sau tích hợp main ngày 2026-11-04

Main `64d343b` đã có inventory/domain migration mới và potential impact. Nhánh 2.13
merge main, giữ collector hook qua analyze/analyze_execution. Dùng cùng môi trường
implementation bên dưới: backend pytest với basetemp
`D:/smart-regression-ai/var/task-2.13-persist-publish-main` đạt **549 passed, 75 skipped**,
1 existing warning. PostgreSQL `scripts/storage/run_checks.py` đạt **72 passed,
2 skipped** (candidate-to-DB checks riêng), fresh head `20261104_03`, recovery và
cleanup pass. Chi tiết [handoff](task-2.13.md#persistence-wiring). Ruff lint/format,
exporter --check, frontend contracts:check/typecheck và diff checks pass. Các counts
ở implementation baseline dưới đây là lịch sử, không thay kết quả sau tích hợp này.

## Bổ sung task 2.13 persistence wiring ngày 2026-11-04

CLI đã có `analyze --persist --artifact-root <EXISTING_AUTHORIZED_ROOT>`.
Hai flags phải đi cùng nhau và không kết hợp `--output`. Actual config/acquisition
manifests theo cùng execution; không auto-migrate/provision repository. Setup và
exit/orphan semantics ở [PostgreSQL setup](postgresql-setup.md#opt-in-cli-analysis-persistence),
bằng chứng/giới hạn ở [handoff 2.13](task-2.13.md#persistence-wiring).

Cwd `D:\smart-regression-ai\var\main-review-20261103`, main baseline `f1dbe2d`.
Python executable `D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe`,
PYTHONPATH trỏ `backend/src`, PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8;
Git portable prepend từ `D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd`.
Tái dùng environment locked có sẵn, không claim clean install.

Các commands dưới đã chạy bằng executable trên:

```powershell
python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/task-2.13-persist-full-2
python scripts/storage/run_checks.py
python scripts/demo_analysis.py --output D:/smart-regression-ai/var/task-2.13-persist-default-demo
python -m smartregression.cli.main analyze --help
python scripts/export_contracts.py --check
```

Full backend **430 passed, 44 skipped**, 1 existing Starlette/httpx warning.
Dedicated PostgreSQL 17.11 **43 passed**, fresh migrations/recovery/file digest/
catalog/owned-container cleanup pass. Default skips không thay DB acceptance.
DB workflow cases gọi actual CLI main in-process, inject settings factory cho test
loopback exception; không claim production TLS-enabled subprocess acceptance.
Non-DB demo với runtime URL invalid cố ý exit 0, thin=1/failure=2/empty=1.
Các output directories thuộc lần chạy này, không ghi đè để chạy lại.

Ruff check/format, frontend contracts:check/typecheck và diff/docs checks pass.
Không đổi public schema/generated artifacts, dependency/lockfile hoặc UI; không
chạy browser/CI hoặc product/frontend build mới cho scope này. Không commit artifacts,
dump hoặc credentials. Wrapper portable `scripts/storage/verify.ps1` vẫn yêu cầu
`.venv` của checkout; phiên này gọi run_checks.py bằng venv thực có sẵn.

## Inventory 2.08/2.09 ngày 2026-11-04

`scripts/inventory/verify_complete.ps1 -PythonExe <locked-backend-python>` đã chạy
trong PowerShell thường: 521 default tests pass (72 opt-in/platform skips), Ruff/
format/contracts pass; hai candidate thật collect hai lần, 12 Docker fixtures và
71 PostgreSQL tests đều pass. Xem [kết quả và giới hạn](../research/sprint-2/inventory-verification-20261104.md).
`-RuntimeOnly` chỉ phục vụ debug runtime sau source checks, không thay default gate.
Script tải đúng hai public SHA như dữ liệu; build hooks/collection chỉ trong Docker,
DB test là container riêng. Evidence tạo mới dưới `var/`; không cần DSN có sẵn.
Các mục có ngày cũ bên dưới giữ lịch sử, không phải trạng thái hiện tại của inventory.

## Bổ sung task 2.20-B ngày 2026-11-03

H1 đã triển khai local config/connection/application metadata boundary, chưa có
schema/migrations/durable adapter. Chi tiết [handoff 2.20-B](task-2.20-b.md).
Cwd `D:\smart-regression-ai\var\main-review-20261103`; Python 3.14.3 và
packages cài locked trong `D:/smart-regression-ai/var/task-2.20-b-venv`.
Các lệnh dưới dùng tool path thực đã chạy; member dùng uv theo setup hiện hành.

```powershell
$env:UV_PROJECT_ENVIRONMENT='D:/smart-regression-ai/var/task-2.20-b-venv'
& D:/smart-regression-ai/.tools/bin/uv.exe sync --locked --cache-dir D:/smart-regression-ai/.uv-cache --python D:/smart-regression-ai/.venv/Scripts/python.exe
& D:/smart-regression-ai/.tools/bin/uv.exe lock --check --offline --cache-dir D:/smart-regression-ai/.uv-cache
& D:/smart-regression-ai/.tools/bin/uv.exe sync --locked --offline --cache-dir D:/smart-regression-ai/.uv-cache
& D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/ruff.exe check .
& D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/ruff.exe format --check .
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PATH='D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd;' + $env:PATH
& D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/task-2.20-b-pytest-final
& D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe scripts/export_contracts.py --check
```

Exit 0 cho các lệnh trên. Locked install tạo venv mới/cài 32 packages; subsequent
offline sync chỉ xác minh environment đã cài, không phải cache-cold install.
Full backend: **383 passed, 1 skipped, 1 warning**; skip POSIX FIFO trên Windows,
warning Starlette/httpx có sẵn. Ruff check/format và exporter pass.

Non-DB demo với runtime/migration URL invalid cố ý: script `scripts/demo_analysis.py`
với output mới `D:/smart-regression-ai/var/task-2.20-b-demo-1` exit 0, xác nhận
thin=1/failure=2/empty=1. DEMO analysis incomplete, không gọi PostgreSQL.
Không tái dùng output cũ; pytest basetemp tự quản lý cleanup nên khi chạy lại hãy
chọn thư mục dành riêng cho test, không dùng thư mục artifacts/dữ liệu cần giữ.

Chưa verified migration commands hoặc PostgreSQL connect/commit/rollback thật.
Docker Linux engine chưa chạy và KH schema/fixtures chưa có trên fetched main;
driver doubles không thay acceptance DB. Không có CI run cho diff local này.

## Bổ sung task 2.13 ngày 2026-11-03

CLI có `analyze`: shared read-only flow snapshots → changes → target import graph,
xuất v2 report, các producer thiếu có status rõ. [Hướng dẫn và kết quả thực](task-2.13.md)
ghi checkout/môi trường, authorization, limits, output và phần chờ.

```powershell
uv run smartregression analyze --help
uv run python scripts/demo_analysis.py --output var/demo-2.13-new
```

Commands đã đối chiếu với entrypoint/script; actual run dùng Python executable và
PYTHONPATH của checkout như handoff. Demo output directory phải mới, parent có sẵn;
script chỉ tạo fixture sở hữu mới, không chạy Python của input. Script exit 0 xác
nhận CLI thin=1, failure=2, empty=1 đúng kỳ vọng; không phải full pipeline completed.
`validate-report` exit 0 chỉ nghĩa schema hợp lệ. Git cần hỗ trợ `--no-lazy-fetch`;
local đã dùng portable Git tương thích, giữ protection và không đổi Git hệ thống.

## Bổ sung Sprint 1 ngày 2026-10-31

Các bảng 2026-10-06 bên dưới là lịch sử. Kết quả mới ở
[handoff closeout](../research/sprint-1/closeout-handoff-20261031.md): backend cuối
54 passed, Ruff lint/format và exporter check pass; main GitHub CI `e937f66` success
được đọc lại, không phải CI cho diff local. Source/frontend không đổi trong phiên
ngoài harness/tests riêng; không chạy lại frontend checks.

Command mới đã chạy thật, cwd root:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_candidate_spike.py -q -p no:cacheprovider --tb=short
docker build --network=default -t smartregression-candidates:sprint1-20261031 -f scripts/candidates/Dockerfile scripts/candidates
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate sqlparse --image sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e --output var/candidate-sqlparse-20261031-final --full-suite
.venv/Scripts/python.exe scripts/candidates/run_candidates.py --candidate tinydb --image sha256:61b7968ca478436ad158889e8bbe235e616380316f6efded3347cf8ada92809e --output var/candidate-tinydb-20261031-final --full-suite
.venv/Scripts/python.exe scripts/g1/run_spike.py --image sha256:3cd7035210103639f0e52d72b96628a9ef22aea527e5b13f346117ee79cf88ad --output var/g1-closeout-20261031
```

Mọi output directory phải mới; image ID là local artifact identity, không hứa rebuild
giống byte. Candidate commands dùng GitHub public source/gh và Docker Linux, không
chạy input code trên host; [giới hạn](../../scripts/candidates/README.md). Schema/CLI
không thay đổi. Không tái chạy command với output cũ rồi ghi đè evidence.

## Snapshot bootstrap 2026-10-06

Đối chiếu ngày 2026-10-06. Cwd của mọi lệnh dưới đây là **root monorepo** chứa
pyproject.toml và frontend/, hiện là D:\smart-regression-ai. Hai mức bằng chứng:

- **Định nghĩa xác minh:** command/script/entrypoint tồn tại trong manifest, script,
  CLI hoặc CI; không đồng nghĩa đã chạy thành công.
- **Kết quả quan sát:** lệnh đã chạy có evidence, ghi môi trường và giới hạn. Kết quả
  từ review trước dẫn [verification](verification.md); không phải chạy lại trong task Markdown.

Không có frontend test/e2e script, runner command, LLM benchmark command hoặc migration
command đã được xác minh; không dùng tên lệnh phỏng đoán cho các module đó.

**Bổ sung 2026-10-24:** đã có command cho **fixture-only G1** trong
[harness README](../../scripts/g1/README.md); đây là spike tách khỏi production runner.
Các kết quả lịch sử bên dưới giữ nguyên. Evidence mới và exact commands nằm ở
[handoff tích hợp](../research/sprint-1/implementation-handoff-20261024.md).

## Runtime và nguồn

[pyproject](../../pyproject.toml) yêu cầu Python >=3.14,<3.15;
[package](../../frontend/package.json) yêu cầu Node >=22.14,<23, npm >=10.
[CI](../../.github/workflows/ci.yml) chọn Python 3.14, Node 22.14.0, uv 0.12.23.
Tool local đã quan sát: Python 3.14.3, Node 22.14.0, npm 10.9.2, uv 0.12.23.
Phiên bản dependency cụ thể lấy từ [uv.lock](../../uv.lock) và
[package-lock](../../frontend/package-lock.json), không chép phiên bản vào nhiều hướng dẫn.

`uv` chưa có trong PATH máy bootstrap: review dùng `.tools/bin/uv.exe` hoặc binary
trong `.venv/Scripts`. Thành viên cài uv theo [setup](setup.md), không phụ thuộc .tools.
`uv run` có thể sync/build package trước khi chạy; chạy executable sẵn có thành công
không chứng minh một clean `uv sync` sẽ thành công offline.

## Setup và chạy

| Lệnh chuẩn | Định nghĩa đã đối chiếu | Kết quả/giới hạn đã quan sát |
| --- | --- | --- |
| `uv sync --locked` | pyproject/uv.lock, CI | Dependencies từng được cài bằng uv; chưa xác nhận setup sạch mới; offline thiếu hatchling ở lần review |
| `npm --prefix frontend ci` | package/lock, CI | Dry-run offline đã pass; chưa coi là clean install/scripts pass |
| `uv run uvicorn smartregression.api.main:app --reload --host 127.0.0.1 --port 8000` | api/main.py, Uvicorn dependency, setup | Uvicorn live health đã pass bằng Python module không reload; chưa xác nhận --reload trong mọi client |
| `npm --prefix frontend run dev` | script dev = Vite bind loopback | Review trước bị EPERM; lần mở web sau đã khởi động Vite bằng node entrypoint, HTTP hiện trả 200; chưa coi là browser e2e |
| `uv run smartregression --help` | project.scripts → cli/main.py | CLI executable/module đã chạy --help thành công trong review |
| `uv run smartregression validate-report examples/reports/demo.json` | CLI subcommand/fixture, CI | Executable/module đã trả exit 0 và nhãn DEMO; invalid/missing file smoke riêng trả 1/2 |

PowerShell dùng `npm.cmd` thay `npm` nếu execution policy chặn npm.ps1; không cần
thay policy toàn máy. Cài lần đầu cần network/dependency access hợp lệ, không tắt sandbox.

## Checks và tái sinh contract

| Lệnh chuẩn | Nguồn xác minh | Kết quả review trước / giới hạn |
| --- | --- | --- |
| `uv run ruff check .` | pyproject Ruff/dev deps, CI | .venv Ruff đã PASS |
| `uv run ruff format --check .` | Ruff formatter, CI | .venv Ruff đã PASS |
| `uv run pytest` | pyproject testpaths, backend/tests, CI | .venv Python pytest: 14 pass, 2 setup errors quyền thư mục tạm; full suite chưa pass |
| `uv run python scripts/export_contracts.py --check` | exporter argparse, CI | .venv Python đã PASS; kiểm cả fixture demo |
| `uv run python scripts/export_contracts.py` | exporter write mode | Đã sinh OpenAPI; chỉ chạy khi cần cập nhật nguồn chuẩn, không dùng thay --check trong CI |
| `npm --prefix frontend run contracts:generate` | package + frontend/scripts/contracts.mjs | Đã sinh types bằng openapi-typescript, không sửa tay |
| `npm --prefix frontend run contracts:check` | package + generator --check, CI | PASS; option defaultNonNullable=false giữ optional fields đúng schema |
| `npm --prefix frontend run lint` | package + eslint.config.js, CI | PASS |
| `npm --prefix frontend run typecheck` | package + tsconfig strict, CI | PASS |
| `npm --prefix frontend run build` | package: tsc --noEmit rồi vite build, CI | Bị spawn EPERM ở esbuild trong review; build chưa được xác nhận sau khi dev chạy |
| `uv lock --check --offline --cache-dir .uv-cache` | uv CLI, manifest/lock | .tools uv đã PASS; không chứng minh cache có đủ packages để sync |

Đổi contract: export rồi generate, sau đó chạy cả hai check và consumer tests. Đổi
fixture cũng phải validate backend; `npm run build` riêng không chạy Pydantic.
Chọn subset pytest theo module khi debug, nhưng không thay full suite của CI bằng
subset rồi tuyên bố tất cả pass. Xem [Testing](../rules/06-testing-quality.md).

## HTTP smoke trong task tài liệu

Dev servers từ yêu cầu mở web trước vẫn chạy, không được khởi động lại hoặc đổi cấu
hình trong task này. Các lệnh PowerShell read-only đã chạy:

```powershell
Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing
Invoke-RestMethod 'http://127.0.0.1:5173/api/health'
```

Kết quả: UI HTTP 200; health có schema_version=1.0.0, status=ok,
service=smartregression-api, scope=service_only. Đây là HTTP/proxy smoke, không xác
nhận browser rendering, full build, LLM, storage hay runner readiness.

## Giới hạn và cập nhật

Không chạy product suite lại cho đợt chỉ sửa Markdown. GitHub CI, Linux/macOS,
browser e2e, required checks/branch protection và setup sạch vẫn chưa xác minh.
Không có .git nên không có git diff/index/history đáng tin để báo; task docs dùng
hash snapshot trước/sau để kiểm source/manifests/CI không đổi.

Khi thêm script, cập nhật bảng từ implementation thật và ghi kết quả riêng. Gate
planned ở [enforcement](../rules/14-enforcement.md), không invent command ở đây.

## Sprint 3 Gemini — task 3.16, 2026-11-10

Commands below are implemented and were run from the task worktree on Python
3.14.3. They do not imply an analyze CLI extension, public Gemini endpoint or G2.
Use the locked project environment; set TEMP/cache inside a permitted workspace.

| Command | Actual scope/result |
| --- | --- |
| `python scripts/llm/smoke.py --session-root var/gemini-g1-session` | Dry-run synthetic repository/snapshots/request only, no network; exit 0 |
| `python scripts/llm/smoke.py --live --session-root var/gemini-g1-session --env-file <trusted-backend-env-file>` | Explicit opt-in, synthetic-only, guarded Gemini count/generation; final run exit 0/G1 true. The flag reads only canonical/alias key configuration and does not auto-discover dotenv |
| `python -m pytest backend/tests/unit/test_gemini_runtime.py -q -p no:cacheprovider --basetemp var/runtime-checked` | 28 runtime/config/ledger cases passed at checkpoint; no paid API calls |
| `python -m pytest backend/tests/unit/test_gemini_smoke.py backend/tests/unit/test_gemini_runtime.py -q -p no:cacheprovider --basetemp var/s316-fixture-final` | 31 cases passed, including real synthetic Git snapshots and canonical source evidence; no fixture code/inference executed |

The live session has reached its five-run limit; do not reuse commands to bypass
the existing ledger by deleting/renaming it or implicitly starting a new session.
Session reservations include unknown usage, not just successful calls. See
[3.16 evidence/decisions](task-3.16.md) for exact model/API/schema changes, hashes,
budget, unsuccessful attempts and nullable thinking/cost. Unit/CI remains offline.
