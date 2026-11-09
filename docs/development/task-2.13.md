# Task 2.13 — Incremental application workflow, CLI và demo

Follow-up 2026-11-05: [H1 prompt 4 handoff](h1-seven-prompt-handoff.md#publication-and-prompt-4-integration)
records actual impact/evidence/ordering wiring and compound SQL report/evidence
persistence. CLI `--persist` now requires the P3 evidence migration as well as
foundation/inventory migrations. Local regression/DB checks are recorded there;
review/merge and full inventory/retrieval acceptance remain separate. Historical
thin/report-only results below are not the latest implementation verification.

Follow-up [2.17](task-2.17.md): inventory producer đã có nhưng chưa cấu hình collector
được ghi `not_run`/`inventory_collector_not_configured`; graph source failure giữ path
trong stage limitations. Các kết quả kiểm chứng lịch sử bên dưới giữ theo baseline
của từng phiên, không phải kết quả chạy lại cho follow-up này.

<a id="persistence-wiring"></a>

## Persistence wiring follow-up — 2026-11-04

> Đối chiếu P3 ngày 2026-11-04: PR #30 đã merge tại main `9bcd6a4`; hai source
> CI checks của PR SUCCESS. [Spec P3](task-2.05-p3.md#p3-status) đã accepted
> theo H1 xác nhận cả nhóm đồng ý ngày 2026-11-04. Optional evidence/compound
> transaction chưa triển khai trên main tại baseline và không
> thay kết quả kiểm chứng lịch sử của report-only wiring bên dưới.

### Phạm vi, baseline và interface

- Main fetch: `f1dbe2da629da9b008f76cac43fdcf3882f46109`, đã merge NativeTestId.
- Checkout `D:\smart-regression-ai\var\main-review-20261103`, branch
  `feat/sprint-2-2.13-report-persistence`. Checkout gốc và công việc có sẵn giữ nguyên.
- Task chỉ nối run/report persistence, không làm EvidenceStore/P3, inventory,
  retrieval, new endpoint/UI hoặc migrations. Scope implementation ban đầu không
  commit/push; sau bàn giao user giao commit/push và mở PR để nhóm review/merge.
  Không tự approve/merge vào main; kiểm chứng ở dưới là bằng chứng local, CI riêng.
- Profiles/rules/skills theo Backend/Contracts, rules 01/02/03/04/06/07/12/13;
  api-contracts, test-driven-development, security-review, systematic-debugging.
  Không sub-agent hoặc xem open PR.

`application.analysis.analyze_execution` trả internal `AnalysisExecution` gồm validated
report, `RunConfiguration` và tuple manifests của chính SnapshotPair đã acquire.
Không acquire lại hoặc dựng manifests từ report identity. Không đưa config/manifests
vào public report, không giữ source contents trong execution result. `analyze` giữ
return type report cho callers cũ bằng compatibility wrapper, không có orchestration
thứ hai. `composition.analyze_local` vẫn trả report; optional `artifact_root` bật
persistence và nối adapters tại composition root.

Snapshot limits được resolve một lần, dùng cho acquisition và config. Source limit
256000 bytes được lấy từ cùng constant `MAX_PYTHON_SOURCE_BYTES` tại Python snapshot
parser; FrozenReader và graph gate tái sử dụng, không thay threshold/thuật toán.
Snapshot/materializer versions đến từ acquisition manifests, changes version đến
từ actual producer result. Graph/application version chưa có provenance đáng tin
thì null; không lấy installed package version khác checkout hoặc tự bịa version.
Graph policy target_imports/direct_two_tree được giữ theo execution hiện có.

Tái dùng `persist_report`, `ReportFiles`, `PostgresRunReportStore`, settings/engine
lifecycle của foundation. DB infrastructure chỉ import trong nhánh opt-in để default
CLI/help không nạp SQLAlchemy/psycopg. Không đổi contract v1/v2, generated artifacts,
stack/dependencies/lockfiles/schema/migrations hoặc thuật toán của thành viên khác.

### CLI và prerequisites

[Setup/vận hành](postgresql-setup.md#opt-in-cli-analysis-persistence) mô tả provision
repository, runtime credentials, artifact root, exit codes và orphan policy.

```powershell
uv run smartregression analyze --help
uv run smartregression analyze --repository D:/authorized/repo --repository-id repo-1 --authorized-root D:/authorized/repo --base <FULL_BASE_SHA> --target <FULL_TARGET_SHA> --persist --artifact-root D:/authorized-artifacts
```

Dòng thứ hai là template, không phải actual run với các placeholders này. Root phải
tồn tại, do operator kiểm soát và disjoint source. `--artifact-root` yêu cầu
`--persist`; hai flags không dùng với `--output`. Invalid combinations được reject
trước acquisition/publication. Runtime load settings không fallback credentials
migration, không tự migrate/provision hoặc nới TLS.

Report file có storage key `<run_id>/<report_id>.json`; artifact ID lấy report ID
trong artifact namespace. JSON stdout chỉ xuất sau save thành công; stderr giữ
analysis status và thông báo `Persistence saved`. Analysis exit 1/2 vẫn được giữ
cho incomplete/stage-failed report đã lưu. Storage/config/metadata errors dùng
`Persistence failed: <safe_code>`, exit 2, không JSON/success giả hoặc DSN/SQL echo.

File publish trước SQL; publication failure không gọi save. SQL failure rollback
metadata, giữ complete orphan file để reconciliation; ambiguous commit không được
tự delete/retry. New analyze tạo identity mới, không phải retry. Exact retry được
test bằng giữ nguyên captured execution qua composition, không phân tích lại.
Không có distributed transaction, CLI resume hay GC mới.

### Kiểm chứng thực tế

Cwd là checkout trên, Windows/Python 3.14.3. Dùng Python/Ruff của
`D:/smart-regression-ai/var/task-2.20-b-venv/Scripts`, PYTHONPATH trỏ `backend/src`
checkout, PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8. Git portable được prepend
từ `D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd`. Node 22.14.0/npm 10.9.2 và
dependency junction có sẵn; không claim clean install.

- Test-first CLI persistence: 5 failed do chưa có flags/semantics cần triển khai.
- Focused workflow/CLI đầu: 33 passed; thêm composition/failure tests: 44 passed.
- Full backend lần đầu: 429 passed, 1 failed, 44 skipped; existing subprocess guard
  phát hiện eager DB import từ composition. Đã sửa bằng imports trong opt-in branch,
  giữ nguyên guard và bổ sung subprocess analyze thực kiểm không nạp DB libraries.
- Focused import/lifecycle/CLI sau fix: 42 passed, 1 existing Starlette/httpx warning.
- `python scripts/storage/run_checks.py`: **43 passed** trên PostgreSQL 17.11,
  16.33s; migrations/fresh head/backup-restore/catalog+artifact digest và cleanup pass.
  Evidence local ignored:
  `var/storage-verification-d91f1f5526aa40a18d772595599dfa48/evidence.json`.
- Image pinned: `postgres@sha256:0b81cec82228160abfa753aeaad0609b709eb26eeb950f2e404ad2326e1cc370`.
  Harness chỉ xóa đúng container có label do nó tạo, không dùng DB/shared volumes.
- Ba DB cases mới kiểm actual CLI main/composition, Git acquisition/dirty-tree
  isolation, file publication/reload, runtime SQL, config/manifests, partial/failed
  stages, exact retry/conflict và unprovisioned repository. Chỉ settings factory được
  inject cho explicit harness loopback exception; production TLS không đổi. Đây là
  CLI main in-process acceptance, không claim TLS-enabled subprocess run thực.
- `python scripts/demo_analysis.py --output D:/smart-regression-ai/var/task-2.13-persist-default-demo`
  với runtime DB environment invalid cố ý: exit 0, thin=1/failure=2/empty=1 đúng kỳ vọng.
  Git fixture tự sở hữu; không chạy Python đầu vào. Analysis vẫn incomplete.
- Ruff check/format và exporter --check pass; frontend contracts:check/typecheck pass.
  `analyze --help` hiển thị flags mới. Không đổi UI nên không browser acceptance.

- Full backend final:
  `python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/task-2.13-persist-full-2`
  → **430 passed, 44 skipped**, 1 existing warning, exit 0, 123.58s. 44 skips gồm
  43 opt-in DB tests và POSIX FIFO trên Windows; DB tests đã chạy riêng ở trên.
- `git diff --check` và local links/anchors/fences của các Markdown đã đổi: pass.

Scope này sẵn sàng review về implementation/acceptance cục bộ. CI của diff mới và
independent human review chưa có; không suy toàn bộ task 2.13 hoặc sprint hoàn thành.

### Kiểm chứng trước xuất bản sau tích hợp main

User giao push/mở PR. Fetch mới thấy main `64d343b` đã merge inventory 2.08/2.09
và potential impact 2.04. Merge vào nhánh task, giữ collector hook mới của KH và
forward `inventory_collector` qua compatibility wrapper tới execution; không tự
bật discovery trong CLI. Giữ cả hai phần verified-commands khi giải quyết conflict.

- Backend với basetemp `D:/smart-regression-ai/var/task-2.13-persist-publish-main`:
  **549 passed, 75 skipped**, 1 existing warning, exit 0, 248.59s; collector compatibility
  tests trên main đều pass. 75 skips gồm 74 opt-in DB/candidate cases và POSIX FIFO.
- PostgreSQL harness sau merge: **72 passed, 2 skipped**, 48.23s; hai skip là real
  candidate-to-DB checks yêu cầu inventory harness riêng, không phải report persistence.
  Revision head `20261104_03`, fresh migration/recovery/backup-restore/artifact catalog
  và exact owned-container cleanup pass. Evidence local ignored:
  `var/storage-verification-0aa218893c5f4d04b130babb801745c5/evidence.json`.
- Lần harness đầu của bước publish dừng trước tạo container vì Docker engine tắt;
  không dùng làm code failure/success evidence. Khởi động Docker Desktop nền, chạy
  lại bằng container mới và đạt kết quả trên; không nới gate hoặc đổi database target.
- Ruff lint/format (219 files), exporter --check, frontend contracts:check/typecheck
  và diff checks sau merge pass. Kết quả implementation baseline phía trên là lịch sử.

### Bàn giao và giới hạn

Operator thực hiện prerequisites trong setup trước khi dùng persistence trên target
được phép. KH/AN có thể tái sử dụng boundary tests cho 2.19; các fixture/fakes trong
unit tests không thay acceptance DB. H1 tiếp tục P3/2.05 và integration producer khi
có handoff; task 2.13 toàn phần vẫn pending các stage còn thiếu và human acceptance.

Đặc tả tiếp nối: [P3](task-2.05-p3.md) giữ immutable domain bundle và report status
riêng, preflight overlap trước publish và một SQL transaction khi supplied bundle.
Không nối standalone save bundle sau report save để claim compound atomicity;
standalone adapter là prompt 4, compound workflow wiring là prompt 6 sau 2.06.

OpenAI Codex hỗ trợ implementation/tests/docs/debugging/self-review. Đã đối chiếu
Proposal Appendix C/D trong cùng chuỗi công việc; nhóm cần đọc/hiểu/review trước
nghiệm thu. Không suy independent approval hoặc assistance percentage. Docker Desktop
được mở để chạy verification; container test đã được harness xóa, không có DB service
do task để lại. Không tự tắt Docker Desktop của người dùng.

---

Các phần dưới là handoff thin workflow ban đầu; trạng thái “chưa có persistence”
thuộc baseline lịch sử, đã được follow-up phía trên bổ sung.

## Task và trạng thái

Nguồn: [team guide 2.13](sprint-2-team-guide.md#task-213),
`Sprint 2 Backlog!B127:Z131` trong [workbook](../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx),
và [bàn giao 2.14](task-2.14.md#213--có-thể-bắt-đầu). Workbook chỉ đọc, không đổi.

- H1: Nguyễn Tấn Huy, 12h theo backlog. Human reviewer/acceptance còn pending.
- Checkout: `D:\smart-regression-ai\var\main-review-20261103`.
- Nhánh local: `feat/sprint-2-2.13-workflow`, base `115c7c4756a4d4e41b240876043ede0f0ee3b244`.
- Fetch origin và `gh pr view 20` xác nhận PR 2.14 đã merge vào commit trên.
  Đây là main quan sát lúc bắt đầu, không tự bảo đảm remote chưa đổi sau đó.
- Scope implementation ban đầu: code/tests/docs/self-review, không commit/push/merge.
  Sau bàn giao, user giao commit/push và mở PR để thành viên review/merge; quyền
  mới áp dụng cho phần thin workflow 2.13 này, không tự approve hoặc merge.
- Checkout gốc và các file untracked có sẵn được giữ nguyên. Không sửa algorithms
  của AN/H2/VI, contract/generated artifacts, dependency hoặc lockfile.

Profiles: Backend/Contracts, Coordinator; Change Impact cho frozen-source bridge.
Rules 00/01/02/03/06/09/13; 05/07 cho Git/bàn giao và debugging.
Skills: api-contracts, test-driven-development, security-review,
systematic-debugging; spreadsheets chỉ để đọc backlog.

## Behavior và files

Trước đây các CLI producer tách rời, chưa xuất một run report từ shared workflow.
Nay có `analyze` gọi application và xuất canonical `StageAnalysisReport` v2.
Không thêm API endpoint, UI, lựa chọn/chạy tests đầu vào hoặc LLM call.

| File | Trách nhiệm |
| --- | --- |
| [application/analysis.py](../../backend/src/smartregression/application/analysis.py) | Validate request, authorization/acquisition, UUID run/report, stage orchestration, aggregation và exit policy |
| [application/frozen_reader.py](../../backend/src/smartregression/application/frozen_reader.py) | Existing change producer đọc verified frozen bytes; đối chiếu mọi phía thay đổi của diff với manifest |
| [composition.py](../../backend/src/smartregression/composition.py) | Nối LocalGit vào use case; application không import adapter |
| [cli/main.py](../../backend/src/smartregression/cli/main.py) | Parse flags, gọi composition/application, validate trước output, diagnostics đã redacted |
| [adapters/report_output.py](../../backend/src/smartregression/adapters/report_output.py) | Xuất JSON hoàn chỉnh, exclusive atomic link; không overwrite hoặc ghi vào input repo |
| [demo_analysis.py](../../scripts/demo_analysis.py) | Tạo repo fixture mới và chạy ba scenario qua CLI subprocess; giữ command/config/identity/exit |

Contract/schema v1/v2 giữ nguyên; legacy commands vẫn có tests. API vẫn chỉ health;
frontend demo v1 không nhận report v2 tự động. Unknown measurements giữ null.

### Source identity và dependency

Local operator truyền binding `--repository-id` + `--authorized-root`; root phải
trùng repository thực, không phải prefix cho phép mọi repo con. Đây là CLI trust
boundary cho người dùng local, chưa phải authentication/authorization của dịch vụ.
Repository ID là opaque ID, không lấy path/URL làm ID. Chỉ nhận full lowercase
SHA-1/SHA-256, direct two-tree; không resolve branch/moving refs hoặc merge-base.

`prepare_snapshots` lấy bytes từ Git blobs có giới hạn; workflow kiểm repo/commit,
source root và hash qua `identity_from_snapshots`. Snapshots ở RAM, không bắt buộc
materialize filesystem. Diff dùng cùng SHA pair; bridge kiểm old/new delta coverage
theo blob/mode, kể cả rename rồi tái sử dụng đường dẫn cũ. Parser chỉ đọc frozen bytes.
Graph đọc toàn bộ Python target snapshot, importer → importee; không phải call graph.
Deleted/base spans vẫn nằm trong changes, không bị chuyển thành target evidence.

| Stage | Tích hợp/kiểm chứng | Dependency/giới hạn |
| --- | --- | --- |
| snapshots | Có, Git thật + hash validation | Acquisition lỗi chưa đủ identity trả request error, không bịa report |
| changes | Có, real producer 2.01 | Frozen pair + pinned diff; parse/file limitations giữ nguyên |
| graph | Có, real producer 2.03 | Target snapshot; có thể tiếp tục khi changes fail vì nguồn độc lập |
| impact | `not_implemented` | Chờ actual producer 2.04 |
| inventory | `not_implemented` | Chờ isolated 2.08/09; không chạy collect trên host |
| retrieval | `not_implemented` | Chờ 2.10–12 và provenance/config |
| evidence | `not_implemented` | Chờ source/support verifier 2.06 |
| review_ordering | `not_run` | `producer_review_pending`; `dependency_failed` nếu changes/graph fail |

Reconfirmed trên source base: `_resolve_from_import` chỉ lấy `node.names[0]`
cho `from . import a, b`, raw review API còn executable-seed gap như bàn giao 2.14.
Không sửa producer ngoài scope. Workflow nhận diện cú pháp alias bị ảnh hưởng,
giữ graph observations nhưng gắn `graph_relative_alias_omission` theo path và partial.
Unresolved imports vẫn có reference/reason của producer. Ordering bị chặn chờ
producer fixes/semantics review; không tự coi projection 2.14 là human approval.

Graph parse/UTF-8/binary/source-limit failure không bị silently skip thành graph
hoàn chỉnh. Failed stage không có success payload. Unexpected exceptions ở CLI
trả lỗi đã redacted, không báo empty success. Không đọc/import/execute input Python,
không install/discover tests, gửi source ra ngoài hoặc thêm persistence giả.

## CLI, output và exit codes

```powershell
uv run smartregression analyze --help
uv run smartregression analyze --repository D:/authorized/repo --repository-id repo-1 --authorized-root D:/authorized/repo --base <FULL_BASE_SHA> --target <FULL_TARGET_SHA> --output D:/artifacts/new-report.json
```

Dòng thứ hai là template: thay SHA/path đã được phép, không phải command đã chạy.
Omit `--output` để JSON ra stdout; diagnostics ra stderr. Fixture phải thêm
`--data-kind demo`; label là caller-declared, không phải certification dữ liệu thật.

| Exit | Nghĩa của `analyze` |
| --- | --- |
| 0 | Report completed, không stage failed; thin flow hiện chưa đạt mức này |
| 1 | Report incomplete/partial, không stage failed; downstream thiếu vẫn nonzero |
| 2 | Stage failed, request/authorization/acquisition/internal/output/schema error; đọc code/stages |

Aggregate `partial` có thể chứa graph failed vì snapshots/changes đã có dữ liệu;
exit vẫn là 2. `validate-report` exit 0 chỉ xác nhận tài liệu hợp schema, kể cả
report failed/partial; không thay analysis acceptance hoặc safety verdict.

Output file có parent sẵn, ở ngoài input repo; chặn symlink/junction trong ancestry.
Ghi tempfile trong cùng parent, flush/fsync, publish bằng exclusive hard link rồi
xóa tempfile thuộc run. Existing/concurrent destination không bị overwrite; lỗi
publish không để lại JSON dở dang. Filesystem không hỗ trợ hard link sẽ báo I/O
failure, không fallback sang overwrite. Parent phải do operator kiểm soát; không
tuyên bố chống attacker đồng thời thay directory hoặc crash-durable directory fsync.
Cleanup failure sau publish vẫn trả failure; inspect artifact trước retry.

JSON artifacts không phải PostgreSQL durable persistence. Không thêm DB/tooling,
job system hoặc store fake vào production. Bundle load không suy ra report completed.

## Reproduction đã chạy

Cwd: checkout nêu trên. Python 3.14.3 từ venv checkout gốc, `PYTHONPATH` trỏ source
checkout này, `PYTHONDONTWRITEBYTECODE=1`. Không claim clean dependency install.

Git hệ thống 2.44.0.windows.1 vẫn không hỗ trợ `--no-lazy-fetch`. Dùng MinGit
2.56.0.windows.4 chính thức từ git-for-windows, chỉ prepend PATH trong từng process,
không thay Git hệ thống/config, không bỏ protection:

- Archive URL: `https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/MinGit-2.56.0.4-64-bit.zip`.
- SHA256 archive quan sát: `e3bf78351fe777fba47ddee5950082f8a98bb0f02604fdc7ba3ee2cb68ffa877`.
- Local executable: `D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd/git.exe`.
- Thành viên có Git tương thích không cần dùng đường dẫn tool local này.

```powershell
$env:PYTHONPATH = 'D:/smart-regression-ai/var/main-review-20261103/backend/src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PATH = 'D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd;' + $env:PATH
D:/smart-regression-ai/.venv/Scripts/python.exe scripts/demo_analysis.py --output D:/smart-regression-ai/var/task-2.13-demo-20261103
D:/smart-regression-ai/.venv/Scripts/python.exe -m smartregression.cli.main validate-report D:/smart-regression-ai/var/task-2.13-demo-20261103/thin.json
D:/smart-regression-ai/.venv/Scripts/python.exe -m smartregression.cli.main analyze --help
```

Đã quan sát script exit 0, validator exit 0, help exit 0. Script tự assert CLI
thin=1, failure=2, empty=1; exit 0 của script nghĩa reproduction đúng kỳ vọng,
không có nghĩa toàn pipeline completed. Output directory phải mới cho lần tiếp.
Portable command: `uv run python scripts/demo_analysis.py --output var/demo-2.13-new`.

Local artifacts: `D:/smart-regression-ai/var/task-2.13-demo-20261103/` gồm
`thin.json`, `failure.json`, `empty.json`, từng stderr và `reproduction.json`
ghi exact CLI commands, config, Git/Python, SHA, hashes/run IDs và statuses.
Đây là actual workflow output trên DEMO fixture tự sở hữu, không chỉnh JSON tay.
Input working tree bị cố tình làm bẩn, vẫn đọc committed snapshots. Không execute
Python của fixture. Script không được dùng để sửa repository có sẵn.

Đã chạy lại script phiên bản cuối với `--output
D:/smart-regression-ai/var/task-2.13-demo-final-20261103` (exit 0), validate
`failure.json` (exit 0) và so hai lượt: toàn bộ stage payloads/identity snapshots
giống nhau, run IDs khác nhau. Retry cùng output directory bị từ chối exit 2;
không ghi đè. Các artifacts phiên bản cuối nằm ở directory `demo-final` này.

## Kiểm chứng và self-review

Test-first: lần đầu collect fail vì thiếu application.analysis; regression rename
source-path reuse quan sát failed trước sửa, sau sửa focused suite pass.
Lần chạy sandbox gặp WinError 5 tại basetemp, chạy lại elevated với directory mới;
không skip tests hay bỏ protection để né lỗi môi trường.

| Lệnh tại checkout (Python/PATH như trên) | Kết quả quan sát |
| --- | --- |
| `python -m pytest backend/tests/unit/test_analysis_workflow.py backend/tests/unit/test_report_output.py backend/tests/integration/test_analysis_cli.py -q -p no:cacheprovider --basetemp D:/smart-regression-ai/var/task-2.13-focused3 --tb=short` | 29 passed (trước thêm junction regression) |
| `python -m pytest backend/tests/unit/test_report_output.py -q -p no:cacheprovider --basetemp D:/smart-regression-ai/var/task-2.13-output-final --tb=short` | 4 passed, gồm actual Windows junction |
| `python -m pytest backend/tests -q -p no:cacheprovider --basetemp D:/smart-regression-ai/var/task-2.13-backend-final --tb=short` | **313 passed, 1 skipped, 1 warning**, exit 0; 38.32s |
| `python scripts/export_contracts.py --check` | Pass, exit 0 |
| `npm.cmd --prefix frontend run contracts:check` | Pass, exit 0 |
| `npm.cmd --prefix frontend run typecheck` | Pass, exit 0 |
| `python -m ruff check backend scripts` | Pass |
| `python -m ruff format --check backend scripts` | Pass, 70 files |
| `git diff --check` + kiểm local Markdown links/fences của tài liệu đổi | Pass |

Tests workflow unit dùng acquisition doubles nhưng actual frozen hashing/change/graph
producers. Git integration chạy LocalGit thật, CLI function/subprocess, dirty tree,
delete/rename/same revision, partial/failure, output/validation/exception behavior.
Output tests kiểm actual concurrent writers và junction; fake I/O failure được ghi
rõ. Tests 2.13 không thay campaign đầy đủ 2.19 hoặc PostgreSQL/runner isolation tests.

Security self-review: request → authorization → bounded Git blobs → frozen bridge
→ pure producers → validated report → exclusive output. Không shell interpolation,
input execution, raw source/exception logging hoặc unexpected overwrite. Đây là
self-review cùng phiên, không independent security approval.

Skip là POSIX FIFO test cũ không áp dụng Windows; warning Starlette/httpx cũ không
bị suppress. Full gate đã chạy với portable Git, không chỉ lấy focused subset hoặc
kết quả 2.14. Không chạy PostgreSQL/Docker/browser, CI cho diff này, remote candidate
hoặc clean install. API/UI không đổi. Frontend checks dùng node_modules junction
có sẵn từ phiên 2.14 và hai lockfile trùng nhau, không claim install sạch.

## Acceptance và tiếp nối

| AC | Trạng thái kỹ thuật |
| --- | --- |
| Thin shared application flow + CLI calls application | Đạt với snapshots/changes/graph thật |
| Honest stages, revision-bound report, không giả selection/execution | Đạt trên fixtures/tests |
| Reproducible smoke/demo + commands/config/results | Đạt với artifacts local và script |
| Tích hợp toàn bộ các stage Sprint 2 khi sẵn sàng | Pending dependencies và producer review |
| Human review/acceptance | Pending; không tự gán reviewer đã approve |

- VI/2.18: dùng v2 loader/runtime validation; hiển thị DEMO, stage errors và
  identity/base-target/spans. Thin=partial khác failure=partial+graph failed;
  report validity không phải evidence/support verification. Không ép frontend v1.
- KH/AN/2.19: dùng shared use case/CLI boundary; mở rộng wrong repo/SHA, invalid
  evidence, stale index, unknown native IDs và failed discovery khi producer có.
  Existing smoke tests không đóng thay task cross-module này.
- H2/VI: sửa/review graph alias và ordering semantics tại task gốc; tiếp đó nối
  ordering_inputs/review_result kèm dependency/status regression, không đổi v2 shape.
- 2.04/2.08–12: thay đúng unavailable stage bằng actual producer, pin identity/config;
  bổ sung integration, status/exit và smoke evidence trước nghiệm thu.
- 2.20/2.05: PostgreSQL đã được nhóm chọn, tooling/migrations checkpoint vẫn riêng.
  Nối durable store sau khi có, lưu run/config/status/limitations ngoài domain bundle.
- 2.06: source resolution và conclusion support phải kiểm chứng thực, không nâng
  unverified bằng JSON validation. 2.13 không tự làm evidence verifier.

AI disclosure: OpenAI Codex hỗ trợ thiết kế, code/tests, debugging, docs và
self-review trong phiên này. Đã đối chiếu Proposal v1.4 Appendix C/D; chữ ký cũ
không phê duyệt thay đổi này. Agent đã chạy các checks ghi thực ở đây; Tấn Huy và
nhóm vẫn cần đọc/hiểu/review implementation trước nghiệm thu. Không bịa tỉ lệ
đóng góp, approval hoặc mentor acceptance. Không để service local chạy; artifacts,
test directories và MinGit portable còn trong var bị ignore.
