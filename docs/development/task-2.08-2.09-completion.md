# 2.08/2.09 — candidate collection và PostgreSQL

Ngày 2026-11-04, nhánh `feat/khanh-task-2.08-2.09-inventory` tích hợp main
`f1dbe2da629da9b008f76cac43fdcf3882f46109`, đã gồm native-ID fix của H1
`9ace693b5225886f9d9be15c257a1f379bb7d4a5` qua PR #27. Giữ nguyên authorship của H1;
KH không viết lại contract hoặc backend lock. Quyết định áp dụng:
[accepted 2.08/2.09](task-2.08-2.09-decisions.md). Implementation và local runtime
verification đã hoàn tất; independent review/merge/đánh dấu Done do nhóm xác nhận.

## Đã triển khai

- `CandidateInventoryCollector`: chỉ nhận hai repository ID/commit/full Git tree
  đã chốt. Commit label giả, file/mode bị sửa hoặc tree thiếu bị từ chối trước
  Docker. Download/materialize chỉ xử lý bytes, không import/build source trên host.
- `scripts/inventory/requirements.lock`: uv sinh lock Linux/Python 3.14 gồm mọi
  dependency bắc cầu và hashes. Image online chỉ nhận dependencies; build hook của
  candidate và collection chạy trong container offline riêng. Python/pytest/plugin
  giữ baseline accepted; không dùng backend lock cho input image.
- Observer lấy `item.nodeid`, finish/errors, config exclusions/skips và environment.
  Chỉ một structured frame hợp lệ mới là nguồn inventory; console là diagnostics.
  Mỗi candidate build offline và collect hai lần cùng image/profile, so exact IDs
  và thứ tự. Counts lịch sử dùng đối chiếu, không điền vào output producer.
- Giữ whitespace/Unicode/order qua native-ID fix của H1; xem
  [compatibility](../contracts/stage-reports.md#native-test-ids). Internal/plugin
  exits 1/3/4 vẫn failed dù có IDs. Successful empty cần finish, không lỗi và exit 5.
  Partial cần trusted structured observations; explicit empty checkpoint có thể
  partial/count=0. Timeout/overflow không có checkpoint vẫn failed; diagnostics
  của failed attempt không biến thành eligible test rows.
- `InventoryWrite` freeze/revalidate identity, stage/config, IDs và measurements.
  Consumer `require_complete_inventory_ids` chặn partial/failed/inactive trước
  selection/dispatch. Bỏ cap 8,192 bytes/ID cũ, vẫn có tổng byte/output budget.
  PostgreSQL U+0000 và unpaired surrogate bị từ chối rõ, không truncate/replace.
- Migration `20261104_03` nối actual head `20261103_02`, không sửa foundation
  revisions. Thêm `test_inventories`, `test_cases`, run-target uniqueness, scoped
  FKs, status/presence checks, exact UTF-8 digest và deferred count/order/byte checks.
  Native ID lưu nguyên text; SHA-256 chỉ làm technical B-tree key. Không bịa mapping
  hoặc source location cho 2.16.
- `PostgresInventoryStore`/`BoundInventoryStore` dùng engine/transaction hiện có.
  Một frozen inventory/run: exact retry no-op; payload/config/ID khác conflict.
  Header/cases commit chung; load kiểm scope/config/status/count/order/digest.
  Repository/run/snapshots phải được provision trước, không tạo snapshot giả.

## Boundary và kiểm chứng

Candidate containers: UID/GID 65534, read-only root/source, network none, cap-drop,
seccomp, no-new-privileges, 60s, 1 CPU, 512 MiB RAM/swap cap, 64 PIDs, 64 MiB noexec
tmpfs, 512 KiB tổng captured output. Kiểm Docker inspect và runtime probes; cleanup
lỗi làm invocation fail. Không mount credentials/socket/writable workspace. Không
quảng cáo hỗ trợ arbitrary hostile repos.

Khánh chạy script dưới đây trong PowerShell thường ngày 2026-11-04; agent đọc lại
ba evidence files và PostgreSQL JUnit. **521 passed, 72 skipped**, một warning
Starlette/httpx có sẵn, 59.08s; 71 skip là DB opt-in được chạy thật sau đó, một skip
là POSIX FIFO trên Windows. Ruff check/format (213 files) và contract export pass.
Hai candidate build offline/collection hai lần pass; 12/12 fixture Docker pass;
**71/71 PostgreSQL tests pass**, không skip, CLI report 6.72s. Fresh/upgrade/reapply,
backup/restore exact rows, artifact digest/catalog và cleanup đều pass. Bằng chứng
chi tiết ở [verification record](../research/sprint-2/inventory-verification-20261104.md).
Full suite trong sandbox trước đó vướng ACL; không dùng diagnostic runs thay kết quả
PowerShell thường này. Không cần nới sandbox hoặc đổi Docker security settings.

Từ root checkout, PowerShell thường, Linux Docker đang chạy:

```powershell
& scripts/inventory/verify_complete.ps1 -PythonExe '<existing locked backend Python executable>'
```

`-RuntimeOnly` phục vụ điều tra lỗi runtime mà không lặp source checks; không thay
full default gate. Mỗi lượt tạo thư mục evidence mới dưới `var/`, không commit
source candidate, logs, reports, DB dumps hoặc credentials.

Acceptance gồm hai collection/candidate, fixture success/empty/partial/import/plugin
error/duplicate/timeout/overflow/malformed/missing/unsupported/native IDs; PostgreSQL
thật kiểm năm states, partial/complete empty, scope/count/order/config, long/Unicode/
whitespace IDs, collision, retry/conflict/concurrency/rollback và runtime permissions.
Hai inventory candidate thật được đưa qua canonical contract → DB adapter → consumer.
Migration fresh/upgrade/reapply và backup/restore gồm cả inventory rows.

Committed Sprint 1 evidence chỉ có counts, không có complete ID arrays lịch sử.
Harness ghi giới hạn này: exact/order equality giữa hai lượt mới, đối chiếu counts
lịch sử riêng. Không tuyên bố exact equality với artifact cũ không có để kiểm tra.

## Permissions và consumers

Sau migration bằng migration role, cấp thêm quyền domain cho runtime role đã cấu hình:

```sql
GRANT SELECT, INSERT ON smartregression.test_inventories,
    smartregression.test_cases TO smartregression_runtime;
```

Không cần UPDATE/DELETE/DDL hoặc đọc Alembic version. Dedicated fixture cấp grants
domain riêng, kiểm các thao tác bị cấm. Recovery dùng quiescent backup/restore metadata
và artifacts; destructive downgrade từ chối, không giả rollback dữ liệu đã xóa.

H1/2.13 nhận injected collector/store ngoài web process. 2.16 nhận đúng target IDs và
states nhưng vẫn cần producer impact/mapping riêng; 2.17/2.18 propagate limitations.
Persist được row hoặc successful empty không là kết luận an toàn. Default API/CLI
không tự start Docker/kết nối DB. Không làm selector/retrieval/2.16 thay người khác.

OpenAI Codex hỗ trợ code, tests và self-review. Human review/acceptance còn pending;
không bịa mentor approval, tỷ lệ đóng góp hoặc benchmark results.
