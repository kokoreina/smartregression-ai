# Task 2.17 — Analysis scope và limitations

## Phạm vi và baseline

Đỗ Hà An: analysis status, estimate 6h theo [brief 2.17](sprint-2-team-guide.md#task-217).
Khánh có 4h inventory propagation riêng; reviewer đề xuất là Nguyễn Tấn Huy, chưa
tự coi đã nhận review hoặc nghiệm thu. Nhánh `feat/an-task-2.17-analysis-scope`,
baseline `9bcd6a4` (main đã có 2.14, 2.13, inventory và report persistence).

Task này kiểm khoảng thiếu trước khi sửa. Report v2 đã biểu diễn đủ scope và reasons
cho các producer hiện có; không thêm model/manifest song song, dependency, schema,
generated types, coverage percentage, UI hoặc thuật toán graph/impact.

## Khoảng thiếu được sửa

1. Graph source failure trước đây chỉ có error code, mất path của file gây lỗi.
   Trường hợp quan trọng là file lỗi **không thay đổi**: changes chỉ xét diff nên
   không cung cấp path thay thế. Nay failed graph giữ `limitations: [{code, path}]`
   cho file target bị từ chối đầu tiên: parse, UTF-8, binary hoặc source limit.
2. Inventory producer đã được triển khai nhưng workflow không nhận collector vẫn
   ghi `not_implemented`. Nay ghi `not_run`, reason
   `inventory_collector_not_configured`; không tự bật collector hoặc chạy input code.

Graph vẫn fail-fast, `data=null`. File prefix đã kiểm tra trước lỗi không được xuất
thành graph hoàn tất/partial; chưa có danh sách đầy đủ mọi lỗi trong snapshot.
Path của graph issue luôn thuộc target. Error code có sẵn giữ nguyên; không echo
source, exception text, local absolute path hoặc worker logs.

## Manifest hiện hành và cách consumer đọc

| Stage | Phạm vi có thể đọc | Reasons/trạng thái cần bảo toàn |
| --- | --- | --- |
| snapshots | `identity.base/target` và `stages.snapshots.data`; commit/hash được đóng băng | Acquisition thất bại có thể chưa đủ identity để tạo report; không dựng report giả |
| changes | `data.files` là file thuộc diff; `components` có kind/symbol và base/target spans | File-only/parse/read limits ở files và stage limitations; không đại diện toàn bộ repo |
| graph | `data.nodes` là module paths trong graph được chấp nhận, gắn `data.snapshot` | `unresolved`/limitations khi partial; failed graph chỉ có error + first offending path khi biết, không có accepted graph scope |
| inventory | `data.snapshot` là target, framework/test IDs và `completeness` | Partial/failed/timeout/not_run không phải completed empty; không suy inventory scope từ changed files |
| downstream | Stage results thực tế của workflow | Producer chưa được nối có thể vẫn `not_implemented`; không suy đã tích hợp từ việc PR producer đã merge |

Ví dụ graph failure trong report v2 (đoạn minh họa, không phải một report đầy đủ):

```json
{
  "status": "failed",
  "data": null,
  "reason": null,
  "limitations": [{"code": "python_parse_failed", "path": "unchanged.py"}],
  "error_code": "python_parse_failed"
}
```

Các payload fields trên chính là manifest scope/limitations dùng bởi 2.13/2.18/2.19;
không có API hoặc command scope mới. Module scope là static import graph, không phải
call graph hay bằng chứng mọi ảnh hưởng hành vi đã được tìm thấy. Coverage ở đây là
phạm vi phân tích, không phải runtime test coverage, recall hay chứng nhận an toàn.

## Ma trận trạng thái và exit policy

Quy tắc ưu tiên cho toàn bộ bảng: **bất kỳ stage nào failed thì CLI exit 2**,
kể cả changes/inventory đã completed hoặc downstream vẫn chưa hoàn tất. Các ô exit 1
dưới đây chỉ áp dụng khi không có failed stage.

| Tình huống | Stage behavior | CLI analysis exit |
| --- | --- | --- |
| Diff rỗng hợp lệ | changes completed, lists rỗng; graph vẫn phải xử lý target độc lập | 1 nếu downstream chưa hoàn tất; không suy no impact |
| Non-Python diff | changes partial; file_only/non_python_file_level_only | 1 nếu không stage failed |
| Unresolved import | graph partial, giữ source path/reference/reason | 1 nếu không stage failed |
| Target source bị từ chối | graph failed, data null, giữ code và path đầu tiên | 2 dù root report partial |
| Không cấu hình inventory collector | inventory not_run/inventory_collector_not_configured | 1 nếu không stage failed |
| Discovery complete nonempty hoặc successful empty | inventory completed, completeness complete; empty là IDs [] | 1 khi downstream vẫn thiếu |
| Discovery partial | inventory partial, giữ observed IDs/completeness partial và reason | 1 nếu không stage failed |
| Discovery failed/timeout | inventory failed, data null, giữ error code | 2 |
| Producer unavailable / dependency không cho chạy | not_implemented / not_run và reason hiện hành | Theo toàn bộ stages |

Root aggregate và `analysis_exit_code` giữ đúng [contract v2](../contracts/stage-reports.md).
Một report partial có thể chứa failed stage. `validate-report` exit 0 chỉ xác nhận
schema; không biến analysis exit 2 thành thành công. Consumer phải đọc stage fields,
không chỉ root status hoặc số components/test IDs. Deleted spans giữ ở base; rename
giữ previous_path; không gộp chúng vào accepted graph target.

## Inventory và persistence

Tái sử dụng converter của KH, không sửa collector, discovery policy, native IDs,
completeness hoặc DB schema. Matrix tests kiểm complete, empty, partial, failed và
timeout xuyên workflow và JSON; collector là double có khai báo, không phải evidence
pytest discovery/Docker isolation thật. Trường hợp collector chưa cấu hình được kiểm
qua CLI thật. Không thêm exclusions/profile metadata chưa tồn tại trong payload;
consumer không được suy IDs là toàn bộ mọi test có thể có ngoài collection config.

Report publication test đọc lại artifact thật và kiểm `stage_summary_json` giữ
graph path/reason và inventory status. SQL store trong test này là double; không
tuyên bố đã chạy PostgreSQL thật. Existing storage tests opt-in vẫn áp dụng.

## Kiểm chứng

Baseline full backend: **549 passed, 75 skipped, 1 warning**, 91.99s. Skips là
74 PostgreSQL opt-in cases và một POSIX FIFO case không áp dụng Windows; warning
Starlette/httpx đã có. Trước sửa, sáu regression cases fail đúng tại missing graph
path và inventory status. Sau sửa, focused workflow/conversion/persistence/inventory
suite: **53 passed**, 2.22s.

Kiểm chứng trên diff mới:

| Check | Kết quả local |
| --- | --- |
| Full backend | 561 passed, 75 existing skips, 1 existing warning; 118.44s |
| Real Git scope/inventory integration | 7 passed; 21.19s |
| Ruff lint / format check | Pass; 221 Python files formatted |
| Schema exporter check | Pass, không đổi generated schema |
| Canonical DEMO v1 / partial stage report v2 validation | Pass |
| Existing reproducible demo CLI | Script exit 0; actual analysis exits thin=1, failure=2, empty=1 |
| Git diff whitespace | Pass |

Demo artifacts local nằm trong `var/task-2.17/demo/` (Git ignored): `thin.json`,
`failure.json`, `empty.json`, stderr và `reproduction.json` có actual commands,
revisions và identities. Report failure có `python_parse_failed`/`a.py`; cả ba
report giữ inventory not_run với reason mới. Không commit runtime artifacts.
Chưa chạy PostgreSQL/Docker discovery, frontend browser hoặc remote CI trong phần
kiểm chứng local này; không đổi frontend/schema nên không claim UI checks.

Lệnh đã dùng tại repository root:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests -q
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe -m smartregression.cli.main validate-report examples/reports/demo.json
.venv/Scripts/python.exe -m smartregression.cli.main validate-report examples/reports/stage-report.partial.json
.venv/Scripts/python.exe scripts/demo_analysis.py --output var/task-2.17/demo
git diff --check
```

## Handoff

- H1/2.13: giữ scope/reasons khi tiếp tục nối impact/retrieval; không tự nâng stage
  status để tổng report xanh. Existing persistence summary chứa metadata, artifact
  report chứa payload scope đầy đủ.
- VI/2.18: hiển thị failed graph + path, not_run inventory và limitations; không
  hiển thị rỗng là không có rủi ro hoặc gọi completed stage là toàn pipeline hoàn tất.
- KH/AN/2.19: dùng unchanged invalid source/no-diff regression và inventory matrix;
  mở rộng kiểm boundary thực khi có producer/runner. Unit cases của task này không
  tự đóng toàn bộ 2.19.

OpenAI Codex hỗ trợ audit, implementation, tests, debugging và tài liệu. Kết quả
local/agent review không thay human review, xác nhận hiểu code của tác giả hoặc
nghiệm thu Sprint 2. Không sửa main hoặc nhánh của thành viên khác.
