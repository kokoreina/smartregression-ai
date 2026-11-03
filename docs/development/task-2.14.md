# Task 2.14 — Integration contracts và stage reports

## Baseline và quyết định triển khai

- Checkout: `D:\smart-regression-ai\var\main-review-20261103`, branch `main`.
- Baseline: `8ffb879380506f7f69a8feee35ce3310da4a77ae`; fetch `origin/main`
  ngày 2026-11-03 xác nhận cùng commit. Checkout ban đầu không bị thay đổi.
- Brief: Sprint 2 Backlog `B133:Z137`; accountable H1, allocation 12h.
- Scope: canonical contracts, boundary conversion/validation, exporter, examples,
  tests và docs. Không orchestration, DB implementation hoặc thuật toán impact.
- Profiles/rules: Backend/Contracts, Coordinator; rules 00/01/02/03/04/06/09/13.
  Skills: api-contracts, test-driven-development, security-review, spreadsheet
  read-only extraction. Không chạy sub-agent hoặc xem open PR.

Quyết định trong scope task: giữ nguyên `AnalysisReport` v1.0.0, demo và consumers
cũ; thêm `StageAnalysisReport` v2.0.0. Version mới phải xuất hiện rõ ở root.
Nested v2 models kế thừa version root, không có default version 1.0.0.
Validator application/CLI nhận hai loại; không tự migrate report cũ hoặc hạ
report mới về report cũ. `extra=forbid` áp dụng cho cả hai. Producer-specific
versions `snapshot/1`, `changed-components/1` không bị đổi bằng task này.

Lý do: selection bắt buộc ở v1 không phù hợp stage analysis. Thêm field vào v1
cũng không tương thích với strict old readers. Consumers cũ tiếp tục đọc v1;
frontend real-report consumer v2 thuộc 2.18, chưa tự được triển khai nhờ type export.
Không thêm API endpoint để export models.

## Producer/consumer mapping

| Producer | Hiện có / gap | Boundary trong 2.14 | Consumer tiếp nối |
| --- | --- | --- | --- |
| 2.15 SnapshotPair | Manifest có repo/commit/hash; không run ID | Validate frozen pair, giữ manifest identity, caller cấp run ID | 2.13/2.20 |
| 2.01 ChangeAnalysis | Rich dataclasses; CLI hiện dùng local path | So identity, giữ kind/reason/base-target spans/file statuses | 2.13/2.04/2.05 |
| 2.03 DependencyGraph | Node-scoped repo/revision; edges là objects | Kiểm node/edge identity; tuple projection riêng cho ordering | 2.04/2.07 |
| 2.07 ReviewOrder | Không tự mang repo/snapshot; không impact paths | Caller khai snapshot; report kiểm graph scope và giữ rule/limitations | 2.13/2.18 |
| 2.04 impact | Chưa có producer trên baseline | Contract/example có supported paths; không sinh paths | 2.05/2.06 |
| 2.08/09 inventory | Chưa có Sprint 2 producer | Target snapshot/native IDs/completeness contract | KH/2.13 |
| 2.11/12 retrieval | Chưa có producer | Snapshot/index/config/hash/range/rank contract | H2/VI/2.13 |
| 2.06 evidence | Chưa có source verifier | Resolution khác support; JSON không xác nhận source | VI/2.06/2.18 |
| Legacy report/demo | Selection bắt buộc; frontend demo chỉ đọc v1 | Giữ nguyên; application validator nhận thêm v2 | CLI/exporter |

## Trạng thái bàn giao — 2026-11-03

Implementation sẵn sàng review với giới hạn môi trường: bộ contract/consumer
94 passed; full backend 263 passed, 20 failed, 1 skipped. Không tuyên bố full gate
pass. Self-review không thay independent review; AN/VI chỉ là reviewers đề xuất,
chưa có approval. Không sửa workbook, commit/push/merge hoặc xem open PR.

### Cập nhật quyền xuất bản

Sau bàn giao implementation, user yêu cầu commit/push task 2.14 để các thành viên
review/approve trước merge. Thay đổi được đưa lên nhánh
`feat/sprint-2-2.14-contracts`, PR base `main`. Quyền mới cho commit/push và mở PR
review; không bao gồm tự approve/merge. Các dòng không commit/push phía trên ghi
lại phạm vi của phiên implementation ban đầu. Kết quả checks không thay đổi vì
bước xuất bản chỉ bổ sung ghi chú tài liệu này.

## File/consumer impact

- `contracts/stages.py`: canonical v2 models, legal stage states, report aggregation,
  identity/path/reference validation; EvidenceBundle cho persistence checkpoint.
- `application/stage_conversion.py`: frozen-pair → identity/snapshot stage;
  ChangeAnalysis → changes stage; DependencyGraph → graph stage; explicit legacy
  ordering projection và ReviewOrder → review stage. Không nối thành full workflow.
- `application/reports.py`: typed v1/v2 validation, dùng chung bởi CLI/exporter.
  `validate-report` giữ exit semantics: 0 là valid document, không phải analysis success.
- `application/evidence_store.py`: typed Protocol, conflict/failure codes và
  save/load boundary revalidation; chưa có database adapter.
- `scripts/export_contracts.py`: export public v2 models và EvidenceBundle, validate
  stage examples. `contracts/generated/openapi.json`, `frontend/src/types/generated.ts`
  được regenerate bằng công cụ.
- `backend/tests/unit/test_stage_{reports,conversion,storage}.py`: semantic,
  real pure producer conversion, persistence boundary và failure tests.
- `backend/tests/integration/test_cli.py`, `backend/tests/conftest.py`: examples
  v2 được consumer validate; lỗi không echo private input.
- `examples/reports/stage-report.{partial,empty,failed,not-implemented}.json`:
  DEMO examples, không phải actual repository analysis hoặc acceptance của producer
  chưa triển khai. Partial có snapshot hashes tính từ tiny fixture bằng producer thật;
  impact/evidence trong đó vẫn là contract-only examples.
- [Contract docs](../contracts/stage-reports.md) mô tả field/status/interface details;
  [README contracts](../contracts/README.md) liên kết compatibility mới.

`AnalysisReport` v1, demo v1 và frontend runtime consumers không đổi. So sánh JSON
schema trước/sau xác nhận toàn bộ legacy component schemas và API paths bằng nhau.
Type export v2 không tự thêm frontend support. Không có thay đổi lockfile/dependency.

## Identity và trust boundaries

| Boundary | Đã kiểm | Chưa chứng minh |
| --- | --- | --- |
| Snapshot conversion | validate_frozen_snapshot kiểm hashes/content; giữ repo/commit/manifest identity | Quyền caller đọc repository, OS immutability |
| Changes conversion | Declared repo/base/target/version/comparison mode đúng RunIdentity, giữ spans/reasons | Dataclass chưa có run/hash không tự chứng minh source acquisition đúng snapshot |
| Graph conversion | Mọi node/edge đúng declared repo/commit, endpoints hợp graph; unresolved thành partial | AST source thuộc trusted snapshot, import graph đầy đủ/behavioral impact |
| Report validation | Run envelope, revision scope, paths có edges hỗ trợ, references/IDs/statuses; inventory target, retrieval source/index/config | Source tồn tại, native test IDs đã discover, evidence supports conclusion, authorization |
| Ordering projection | Graph snapshot thuộc identity, giữ tuple direction và limitations, bỏ non-executable/file-only/container seeds | Projection không phục hồi thông tin mà producer chưa cung cấp; workflow phải gắn đúng stage outputs |
| Evidence save/load helpers | Revalidate nested mutable data, reload đúng toàn bộ RunIdentity; không nuốt lỗi storage | PostgreSQL unique/FK/atomicity/concurrency, quyền đọc report |

Không gọi source resolver, runner hoặc LLM. Evidence verified/supported fields là
producer assertions, không phải chứng nhận do JSON validator cấp. Một untrusted
report tự khai supported vẫn phải đi qua trusted resolver ở 2.06 trước dùng như proof.
Paths có static import edges chỉ mô tả khả năng ảnh hưởng, không xác nhận fault.

## Compatibility và quyết định

- V1 reader không tự nhận v2: giữ format cũ và chọn public v2 root riêng. V2 không
  có selection/execution. Root version 2.0.0 bắt buộc; v1 omission behavior giữ nguyên.
- Nested v2 values strict unknown fields; defaults/nullable/required được thể hiện
  trong generated schema. Không hand-edit generated artifacts.
- Failure trước khi materialize có snapshot_id=null, nhưng phân tích cần hashes
  thật. Commit chưa resolve thì dùng request/acquisition error thay vì bịa identity.
- Persistence checkpoint đã xác định atomic EvidenceBundle, repository/run key,
  identical retry/no-op, conflict/failure/not-found semantics. Adapter implementation
  và normalized minimum schema/FKs chờ H1/KH trong 2.20; PostgreSQL engine đã accepted,
  ORM/driver/migration tool chưa chọn trong task này.
- Version/model/interface này là quyết định implementation trong task user giao;
  cần AN/VI producer/consumer review, chưa coi là team/mentor approval.

## Kiểm chứng thực tế

Mọi lệnh dưới chạy tại checkout clone, Windows, Python 3.14.3, Node 22.14.0,
npm 10.9.2, Git 2.44.0.windows.1. Set environment trước Python commands:

```powershell
$env:PYTHONPATH = 'D:\smart-regression-ai\var\main-review-20261103\backend\src'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Python executable `D:/smart-regression-ai/.venv/Scripts/python.exe` tái dùng
dependencies có sẵn; đã xác nhận import smartregression từ clone. Không chạy clean
install. Frontend node_modules trong clone là junction tới checkout ban đầu;
hai package-lock hashes bằng nhau trước tái dùng, không sửa dependency directory.

| Command (Python prefix là executable trên) | Actual result |
| --- | --- |
| `git fetch origin main` | Exit 0, origin/main vẫn `8ffb879` |
| `python -m pytest backend/tests/unit/test_stage_reports.py -q -p no:cacheprovider --tb=short` lần test-first đầu | Report v2 bị legacy validator từ chối; test legacy framework assertion ban đầu sai đã đối chiếu fixture và sửa |
| `python -m pytest backend/tests/unit/test_stage_conversion.py -q -p no:cacheprovider --tb=short` trước implementation | Module conversion chưa có; sau implementation focused suite đạt |
| Tests snapshot failure/null hash và multiple supported paths trước fix | Tái hiện rejection; bổ sung validation đúng và chạy lại đạt |
| `python -m pytest backend/tests/unit/test_stage_reports.py backend/tests/unit/test_stage_conversion.py backend/tests/unit/test_stage_storage.py backend/tests/integration/test_cli.py backend/tests/unit/test_contracts.py backend/tests/integration/test_api.py -q -p no:cacheprovider --basetemp D:/smart-regression-ai/var/task-2.14-final-contracts --tb=short` | **94 passed**, 1 existing Starlette warning, exit 0 |
| `python -m pytest backend/tests -q -p no:cacheprovider --basetemp D:/smart-regression-ai/var/task-2.14-final-backend --tb=line` | **263 passed, 20 failed, 1 skipped**, 1 warning, exit 1 |
| `git --no-lazy-fetch --version` | Exit 129, unknown option; Git hiện tại không đáp ứng prerequisite của LocalGit |
| `python -m ruff check backend scripts` | Exit 0, all checks passed |
| `python -m ruff format --check backend scripts` | Exit 0, 62 files formatted |
| `python scripts/export_contracts.py` | Exit 0, generated schema và examples valid |
| `npm.cmd --prefix frontend run contracts:generate` | Exit 0, generated TypeScript |
| `python scripts/export_contracts.py --check` | Exit 0 |
| `npm.cmd --prefix frontend run contracts:check` | Exit 0 |
| `npm.cmd --prefix frontend run typecheck` | Exit 0 |
| `git diff --check` | Exit 0 |

Sandbox ban đầu gây WinError 5 cho pytest temporary directory. Chạy lại tests
của SmartRegression ngoài sandbox bằng thư mục tạm mới để phân biệt môi trường.
Không dùng retries đó làm lý do bỏ tests hoặc đổi production protection.

20 failures full suite đều ở existing Git integration paths của changed components,
LocalGit và snapshots, cùng tập lỗi quan sát trên baseline trước task. Chúng gặp
unsupported --no-lazy-fetch rồi surfaced invalid_commit; không sửa/bỏ protection.
POSIX FIFO test skipped theo platform Windows có sẵn. Warning Starlette/httpx cũ
không bị che bằng suppression. Full Git gate cần chạy lại với Git hỗ trợ option này.

Không chạy PostgreSQL/Docker/browser/CI cho task này. Không có browser consumer
behavior thay đổi, frontend kiểm generated types. Không chứng minh clean install,
DB round-trip hoặc runner isolation bằng các tests trên.

## Known issues và phần chưa tích hợp

- Graph 2.03 baseline bỏ sót alias b trong `from . import a, b` (resolver dùng
  node.names[0]); cần H2 fix kèm regression. Contract không tự sửa omission.
- 2.07 raw API có thể tier-1 README. Explicit application projection bỏ metadata
  khỏi executable input; producer fix và VI review semantics vẫn cần.
- 2.02 actual output reconciliation và decorator/container oracle cần AN/VI review.
- 2.04 chưa có producer paths thực, inventory/retrieval/evidence source verifier
  chưa triển khai. Contract fixtures không thay các task đó.
- Các CLI changed-components/prepare-snapshots hiện vẫn xuất producer format cũ;
  conversion functions đã có nhưng shared analysis workflow chưa nối — task 2.13.
- Empty graph không có node identity để mapper tự kiểm source; caller phải cung
  cấp trusted snapshot. Caller không được relabel dữ liệu giữa repositories/runs.

## Checklist tiếp nối

### 2.13 — có thể bắt đầu

- Cấp repository ID/run ID ở authorized boundary, gọi identity_from_snapshots;
  không dùng local CLI path làm application ID.
- Nối snapshots → identify_changes → build_dependency_graph qua frozen sources,
  dùng conversion helpers và validate StageAnalysisReport trước xuất.
- Giữ stage statuses/limitations; không substitute producer absent bằng payload rỗng.
- Gọi ordering_inputs/review_result sau producer fixes và review semantics.
- Mở workflow command và document exit behavior khác validate-report; chưa tự thêm API.
- Nhận actual 2.04/inventory/retrieval khi sẵn sàng, gắn contract regression evidence
  cho KH/AN task 2.19. Không chạy input repo code trên host/web process.

### 2.20 — checkpoint cùng KH

- Chọn driver/data access/migration tool qua quyết định rõ; versioned migrations
  một writer. Map RunIdentity/EvidenceBundle vào minimum prerequisites/FKs.
- Bundle không thay toàn bộ report: lưu run/config/stage-status/limitations metadata
  phù hợp, không suy completed từ việc domain bundle load thành công.
- Transaction save atomic, concurrent same-key retry/conflict, foreign identity
  rejection; load absent khác connection failure; config secrets backend-only.
- Kiểm trên PostgreSQL thật và setup/recovery evidence; fake tests không thay thế.

### 2.05 — chuẩn bị được, acceptance chờ dependencies

- Nhận 2.04 paths theo candidate → changed direction và graph revision đúng.
- Implement EvidenceStore dựa trên foundation, giữ ordering/identity/spans qua reload.
- Round-trip, rollback/failure và concurrent immutable-write tests trên DB thật.

### 2.06 — payload checkpoint với VI

- Dùng StageEvidence/ImpactCandidate, kiểm actual trusted snapshot path/span/symbol.
- Phân biệt resolved source và supported conclusion; missing/mismatch là unverified
  cho người dùng, không tự nâng thành supported.
- Nhận persisted evidence từ 2.05; VI implement reusable evidence component,
  real report loading/navigation thuộc 2.18.

## Review và AI disclosure

AI tool: OpenAI Codex, hỗ trợ thiết kế trong task, implementation, tests, docs và
self-review phiên này. Các lệnh/kết quả trên đã được agent chạy/đối chiếu. Đã đọc
Proposal v1.4 Appendix C/D; signatures/assistance estimates lịch sử không được dùng
làm approval hoặc mức hỗ trợ của thay đổi này. Tấn Huy/nhóm cần đọc, hiểu và review
diff trước nghiệm thu; không ghi họ đã thực hiện review. AN/VI review còn pending.
Không có phần trăm đóng góp hoặc mentor approval mới. Không có service/process
local còn chạy từ task; chỉ artifacts/tests temporary directories và frontend
dependency junction ở clone. Checkout gốc giữ nguyên hai untracked entries ban đầu.
