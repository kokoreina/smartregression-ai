# Hà An — Reporting, CSV, history và usage (3.47, 3.49, 3.50, 3.51)

Ngày thực hiện: 19/11/2026. Baseline `effd115`. Nhánh cá nhân
`feat/an-task-3.46-ownership`; main không đổi. Theo yêu cầu mới nhất, cả bốn task
được tiếp nhận cùng với các đầu ra 3.46/3.48 đã chuẩn bị trước đó.

## Đầu ra theo task

| Task | Kết quả |
| --- | --- |
| 3.47 | Kiểm chứng frozen dashboard/shared filters/as_of, biên ngày [start,end), owner và pagination. Sửa giới hạn 366 ngày để kiểm thời lượng chính xác, không làm tròn xuống số ngày. |
| 3.49 | CSV chứa mọi dòng trong frozen view, tối đa 10.000; giữ UTF-8 và bảo vệ formula injection. Bổ sung view ID/start/end/status và số file changed/direct/indirect từ báo cáo run đã lưu, không lấy từ graph hiện tại. |
| 3.50 | Bộ lọc trạng thái lịch sử tại server, giữ qua URL/reload; cursor có cùng predicate, xử lý timestamp trùng và reset component khi đổi filter. Mở lại report không tạo run/AI job mới. |
| 3.51 | Kiểm chứng aggregation hiện có trên SQL thật: null/0/known khác nhau; reservation riêng; usage theo created_at, run theo started_at; static status khác AI status; owner/quota B tách biệt. Không sửa lại logic đã đúng chỉ để tạo thay đổi code. |

Các metrics CSV là **unique file counts từ saved static report**, không phải số
component hay kết quả chạy test. Changed loại khỏi direct/indirect, direct ưu tiên
indirect. Stage không có data thì để trống, không giả zero. CSV có analysis_status
và impact_stage_status để phân biệt report partial với lifecycle run completed.
Partial coverage vẫn chỉ cho kết luận trong phạm vi phân tích, không xác suất lỗi.

View cũ chưa có map metrics vẫn đọc/export được; cột impact bổ sung để trống, cần
tạo view mới để có dữ liệu mới. Báo cáo nguồn được validate và đối chiếu digest
trước khi freeze metrics; không ghi lại payload lịch sử.

## Contract và tích hợp

- GET `/api/v1/projects/{project_id}/runs` thêm query **status** tùy chọn:
  queued/running/completed/failed/interrupted. Không gửi vẫn giữ hành vi cũ.
  Giá trị không hợp lệ trả 422; owner/project predicate luôn được giữ.
- CSV append cột mới, giữ các cột cũ theo đúng thứ tự: view_id, filter_start,
  filter_end, filter_status, analysis_status, impact_stage_status,
  changed_file_count, direct_file_count, indirect_file_count, impact_scope.
  Consumer dùng vị trí cột cố định cần tiếp nhận các cột bổ sung.
- OpenAPI và TypeScript được sinh lại bằng tool của repo, không sửa tay.
- Không migration, dependency/provider/quota thay đổi hoặc gọi AI trả phí.
- Chỉ thao tác source của SmartRegression; không thực thi code các repo đầu vào.

## Bằng chứng kiểm tra

**Chín ca PostgreSQL thật đạt** trong native harness độc lập:

1. Export trên 10.000 dòng bị từ chối, yêu cầu thu hẹp filter.
2. Dashboard/drilldown/CSV dùng cùng owner/filter.
3. Frozen usage giữ null/zero/known và reservation riêng.
4. 31 dòng với timestamp trùng: đủ các trang/CSV; start inclusive/end exclusive;
   dữ liệu mới chỉ xuất hiện trong view mới; B không đọc/export view A.
5. CSV giữ view ID và frozen filter provenance.
6. History filter theo status và keyset qua timestamp trùng không mất/đếm lặp;
   owner khác bị chặn.
7. Tạo báo cáo thật bằng parser + mocked GitHub, đọc lại bằng store mới vẫn giống.
8. CSV từ report đó có changed=1/direct=1/indirect=0, không đếm component thành file.
9. Usage nằm trong kỳ theo created_at dù run ngoài kỳ; status filter theo static
   lifecycle, không AI status; tài khoản khác có quota bằng 0; provider chỉ là mock.

Native harness tạo cluster ngẫu nhiên riêng dưới ignored var, role runtime theo
grants hiện có, kiểm data_directory, chỉ bind loopback và tắt đúng cluster sau chạy.
Không lấy credential, ghi hoặc reset database tài khoản người dùng. PostgreSQL
thực dùng phiên bản **18** trên máy này; đây là bằng chứng bổ sung, không thay thế
identity/version gate Docker PostgreSQL 17. Docker fixtures gốc không bị sửa.
Hai ca harness ban đầu lỗi do PIPE Windows và bind UUID/text trong seed; đã sửa
harness, chạy lại. Đây không phải lỗi dữ liệu sản phẩm và không tính lần fail là pass.

**16 ca browser mục tiêu đạt** với fixture có nhãn, không phải dữ liệu tài khoản
thật: dashboard ready/empty/unavailable, status filtering/reload/pagination, mở lại
saved partial report không POST hoặc gọi AI, responsive/login/chart boundaries và
usage null/0/known không cộng reservation. Một selector test ban đầu sai tên region
đã được đối chiếu DOM và sửa; không sửa sản phẩm để né assertion.

Các ca RED → GREEN của sản phẩm đã quan sát:

- Filter vượt 366 ngày một giây: trước không bị từ chối; sau trả lỗi đúng.
- History status không hợp lệ: trước bị bỏ qua; sau 422 trước data boundary.
- Native CSV thiếu view_id và impact counts: trước KeyError; sau khớp fixture.
- Native history chưa có status argument và browser chưa có filter: trước fail;
  sau các ca SQL/browser đạt.

Log runtime dưới `var/tasks-347-349-350/`. Kết quả full-suite và trạng thái publish
được cập nhật trong phần chốt cuối trước khi push. Không gọi các skip là Pass.

### Kiểm tra cuối trước publish

- Toàn bộ backend: **1.558 passed, 181 skipped**, không có failure, 606,20 giây.
  Skip gồm opt-in PostgreSQL harness/native không bật trong lượt full và case
  POSIX FIFO trên Windows; không gộp skip thành bằng chứng đạt.
- Native PostgreSQL 18 chạy opt-in riêng: **9 passed**, 32,56 giây.
- Toàn bộ browser Playwright, bản mới nhất: **56 passed**, khoảng 2,2 phút;
  gồm ba ca bổ sung archive/foreign run/revoked session và không phát sinh AI POST.
- OpenAPI/type generation drift check, TypeScript typecheck, Vite build,
  scoped ESLint và Ruff đạt. Vite còn cảnh báo bundle lớn hơn 500kB; không phải lỗi build.
- Fresh-context review tự động: không có finding quan trọng trong reporting/history.
  Không suy ra rằng CI trên GitHub hoặc reviewer nhóm đã approve.

Các đầu ra 3.46 và 3.48 được commit riêng lần lượt `1cb4da2` và `9228349` trước
commit của bốn task này. Người dùng đã cho phép push cùng nhánh cá nhân; main
giữ baseline `effd115`. Nhánh remote sẽ là nguồn xác minh publish sau khi push.

## Chạy lại

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_web_reporting_unit.py backend/tests/unit/test_history_filter_api.py -q
$env:SMARTREGRESSION_NATIVE_PG_BIN = 'C:/Program Files/PostgreSQL/18/bin'
.venv/Scripts/python.exe -m pytest backend/tests/integration/native_reporting -q --tb=short
Remove-Item Env:SMARTREGRESSION_NATIVE_PG_BIN
.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short
```

Tại frontend, dùng Node 22.14.0 đã cài và locked node_modules:

```powershell
node scripts/contracts.mjs --check
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node node_modules/@playwright/test/cli.js test --config playwright.config.mjs
```

## Trạng thái bàn giao

Implementation và kiểm chứng cục bộ đã hoàn thiện; reviewer tự động không phát
hiện finding quan trọng trong phạm vi reporting/history. Review này chỉ đọc code,
không chạy lại test và không thay approval của Trần Hưng Khánh hoặc leader.
Không tự ký nghiệm thu, sửa trạng thái workbook, merge main hoặc triển khai public.
Push nhánh cá nhân được người dùng yêu cầu rõ trong phiên này; PR/merge không được
suy ra từ yêu cầu push. Bản bàn giao 3.46/3.48 ghi chưa push là ảnh chụp lịch sử
trước bước publish này, không phải trạng thái sau cùng.
