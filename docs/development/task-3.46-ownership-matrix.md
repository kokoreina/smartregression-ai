# Task 3.46 — Ma trận quyền sở hữu và nghiệm thu của Hà An

Ngày đối chiếu: 18/11/2026. Baseline `effd115747a1260a8ebb7ef0f9d3ff9c0f88f1b1`, sau PR #70.
Nhánh làm việc: `feat/an-task-3.46-ownership`.

Nguồn phân công: workbook `C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned.xlsx`,
`Sprint 3 Backlog!B53:G53`, brief dòng 518–524. Owner gốc Đỗ Hà An, estimate 4h,
dependency 3.02, reviewer đề xuất Trần Hưng Khánh.

## Đầu ra và hiện trạng

**Đầu ra của 3.46 đã sẵn sàng để review cục bộ:** ma trận, 411 ca guard tests,
danh sách nghiệm thu theo từng endpoint và biên bản bằng chứng. Chưa có phê duyệt
của reviewer, chưa commit/push/PR. Không đồng nhất task thiết kế ma trận 3.46 với
nghiệm thu bảo mật toàn sản phẩm ở 3.58/3.59/3.60. Workbook baseline đã ghi Done;
đó là trạng thái có sẵn, không phải bằng chứng của lần kiểm tra này.

- [48 ca nghiệm thu cụ thể](task-3.46-endpoint-cases.md).
- [Biên bản kiểm chứng và giới hạn](task-3.46-acceptance-record.md).

Đầu ra là ma trận negative cases A/B cho các API đọc/sửa/export, cùng quy tắc
nghiệm thu và liên kết kiểm chứng. Implementation quyền sở hữu hiện có sử dụng
session ở backend, account verified, CSRF cho mutation và owner predicate ở storage.

Phần tiếp nhận này bổ sung `backend/tests/unit/test_product_ownership_matrix.py`
để tự động đối chiếu **48 data endpoints** với toàn bộ OpenAPI product mode, cùng
danh sách tường minh 13 thao tác account/public. Khi có endpoint mới ở bất kỳ
namespace nào, inventory test yêu cầu phân loại và thêm case. Không có đường dẫn members/roles/assignments/invites
trong inventory hiện hành.

## Tài khoản và dữ liệu kiểm tra

| Actor | Dữ liệu cần chuẩn bị | Quyền dự kiến |
| --- | --- | --- |
| Guest / session sai, hết hạn hoặc disabled | Không có phiên hợp lệ | Data API từ chối 401 |
| U chưa xác minh email | Session U hợp lệ | Data API từ chối 403 email_verification_required |
| A đã xác minh | Project P-A, run R-A, scenario S-A, note N-A, dashboard view V-A | Đọc/sửa/export dữ liệu của A theo trạng thái nghiệp vụ |
| B đã xác minh | Project P-B cùng các object hợp lệ của B | Đọc/sửa/export dữ liệu của B theo trạng thái nghiệp vụ |

Các ca kiểm tra session gửi Origin/CSRF hợp lệ để quan sát riêng điều kiện đăng nhập.
Mutation với CSRF thiếu/sai hoặc Origin sai được kiểm tra riêng, kết quả 403.

## Ma trận nghiệm thu A/B

Các thao tác hợp lệ của chủ sở hữu cần dùng object thực và body hợp lệ. Với ID lạ,
404 dự kiến giữ cùng cách xử lý như object không thuộc chủ sở hữu.

| Nhóm / số endpoint | Ca của chủ sở hữu | Ca B dùng dữ liệu A hoặc giả owner | Bằng chứng hiện có ở tầng dữ liệu |
| --- | --- | --- | --- |
| Projects / 9 | List/create/get/update/archive/restore/activity/repository/tree | List của B chỉ có dữ liệu B; get/update/archive/activity/repository/tree của P-A bị từ chối; body owner_id bị từ chối | `storage/test_projects.py::test_project_owner_isolation_and_version_conflicts` |
| Runs / 4 | Tạo/list/get/report trong P-A | B dùng P-A hoặc run của A dưới P-B bị từ chối | `storage/test_web_runs.py::test_publication_readback_owner_and_restart` |
| AI và quota / 6 | Quota của A, tạo/xem AI job trong P-A theo consent/quota | Header/query owner A không đổi actor B; job của A không đọc được bởi B | `storage/test_web_ai.py::test_new_account_has_zero_quota_and_cross_owner_is_404` |
| Snapshots/explorer / 10 | Materialize/tree/graph/nodes/source/impact/hotspots/calls/guide/search trong P-A | B dùng P-A không đọc hoặc materialize được; commit/path không cấp quyền truy cập | `storage/test_explorer.py::test_other_owner_cannot_materialize_read_graph_or_source` |
| Notes và resume / 5 | Tạo/sửa/list note, đọc/lưu view-state của A | B không đọc/sửa N-A; không đọc/ghi view-state P-A | `storage/test_notes.py::test_notes_anchor_versions_and_cross_owner`, `test_view_state_optimistic_conflict_and_owner` |
| Scenarios và comparisons / 7 | Tạo/list/get/graph/source/so sánh trong P-A | B dùng S-A; thay project của request; A so sánh với scenario của B đều phải bị từ chối | `storage/test_scenarios.py::test_overlay_persistence_repeat_and_comparison`; cần đối chiếu từng case với DB/browser thật |
| JSON exports / 2 | Export run/scenario đã lưu của A | B đổi project/run/scenario ID của A bị từ chối, không nhận nội dung file | `frontend/scripts/e2e-auth-security.mjs` ghi các cross-owner exports trong harness PostgreSQL/SMTP |
| Reporting / 5 | Tạo/đọc dashboard snapshot, drilldown/runs, usage và CSV | B đọc/export V-A hoặc tạo view từ P-A bị từ chối; dữ liệu và filter giữ owner | `storage/test_web_reporting.py::test_dashboard_drilldown_csv_and_owner_isolation` |

Các tên rút gọn `storage/...` ở bảng trên nằm trong `backend/tests/integration/storage/`.
Danh sách từng method/path và request mẫu có trong `CASES` của bộ kiểm tra mới.

## Kiểm tra tự động mới chứng minh điều gì

| Kiểm tra | Số case | Kết quả tại baseline |
| --- | ---: | --- |
| Inventory khớp toàn bộ OpenAPI; thêm data namespace mới cần matrix case | 2 | Pass |
| 48 endpoint × guest/invalid/expired/disabled/unverified | 240 | 401/403 và chưa gọi data boundary |
| 48 endpoint × session A/B, kèm owner spoof ở query/header | 96 | Actor truyền xuống data boundary lấy từ session |
| 19 mutation/export × thiếu token/token của phiên khác/Origin sai | 57 | 403 và chưa gọi data boundary |
| 16 request có body model, chèn owner_id của A dưới session B | 16 | 422 invalid_request và chưa gọi data boundary |
| Tổng bộ matrix mới | 411 | Pass |

Harness sử dụng **FastAPI TestClient, AuthService.current và CsrfSigner thật**.
Session records là synthetic in-memory. Services/stores dùng recording boundary,
dừng tại lần truy cập dữ liệu đầu tiên bằng marker `matrix_data_boundary` (409).
Marker này chứng minh route chuyển đúng actor; nó không phải phản hồi thành công
hay kết quả từ PostgreSQL. Row isolation, successful owner CRUD/export và browser
phải được xác minh bằng các harness ở bảng A/B trên.

## Kiểm chứng đã thực hiện

Tại worktree task 3.46, Python 3.14.10, dependencies từ `uv sync --locked`:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_product_ownership_matrix.py backend/tests/unit/test_auth_security.py backend/tests/unit/test_projects_unit.py -q --tb=short
.venv/Scripts/ruff.exe check backend/tests/unit/test_product_ownership_matrix.py
.venv/Scripts/ruff.exe format --check backend/tests/unit/test_product_ownership_matrix.py
```

Kết quả targeted suite sau review: **426 passed**, gồm 411 ca matrix, 11 ca auth/project
và 4 ca run/AI/API. Lệnh final thêm `backend/tests/unit/test_web_runs_unit.py`,
`backend/tests/unit/test_web_ai_unit.py` và `backend/tests/integration/test_api.py`
vào danh sách trên. Ruff lint/format đạt. Logs lưu tại
`var/task-3.46/final-targeted.txt` trong worktree, không đưa runtime logs vào Git.

Đã kiểm tra độ nhạy bằng hai mutation chỉ tồn tại trong process riêng:

- Bỏ điều kiện verified trong AuthService: cả 48 ca unverified phát hiện lỗi.
- Ép actor B thành A: cả 48 ca owner-forwarding của B phát hiện lỗi.

Mỗi mutation kết thúc khi process thoát. Suite chuẩn được chạy lại sau kiểm tra
độ nhạy. Lần chạy đầu gặp hai lỗi ở recording fixture do tên biến `calls` trùng
method explorer.calls; đã đổi sang private `_events`, sau đó suite đạt.

Reviewer tự động phát hiện inventory ban đầu chỉ quét các prefix đã biết. Đã tái
hiện bằng cách thêm `/api/v1/exports` trong app fixture: test mới thất bại vì chưa
phát hiện endpoint này. Sau khi đối chiếu toàn bộ OpenAPI với matrix cộng danh sách
account/public tường minh, regression và suite đạt. Reviewer tự động là hỗ trợ kỹ
thuật, không phải approval của Khánh.

Lần đầu, sáu ca PostgreSQL trong disposable DB harness bị skip vì thiếu context
và Docker. Không tính các skip là Pass. Sau đó đã bổ sung tám ca ProjectService
với PostgreSQL local thật, mọi transaction luôn rollback; readback xác nhận project
và số activity không đổi. Chi tiết trong biên bản. Phép thử này không thay toàn bộ
SQL harness hoặc kiểm tra HTTP/export.

Hà An đã cung cấp ảnh browser hai phiên A/B riêng: B không thấy dự án A trong
danh sách và bị chặn khi mở URL P-A; A mở cùng URL và xem được. Đây là bằng chứng
manual của các ca đó, không phải kết quả browser automation hoặc toàn bộ 48 API.

## Checklist dùng khi nghiệm thu thực tế

1. Khởi động product mode trên môi trường kiểm tra theo operations của dự án.
2. Tạo A/B và U qua flow account được phép; mỗi A/B có project, run, scenario,
   note và dashboard view hợp lệ riêng. Dùng fixture có nhãn nếu cần dữ liệu mẫu.
3. Xác nhận A và B đều thực hiện được thao tác hợp lệ trên dữ liệu mình sở hữu.
4. Với từng endpoint trong CASES, giữ session B, dùng ID A và body hợp lệ. Ghi
   status/body, xác minh dữ liệu A không thay đổi sau mutation bị từ chối.
5. Đổi sang ID chưa tồn tại, thử request trộn project B/object A và project A/object B.
6. Kiểm lại Guest/U, Origin/CSRF và owner spoof. Với account routes, dùng
   `storage/test_auth.py::test_http_csrf_origin_session_and_cross_account_profile`.
7. Chạy reviewer khác đối chiếu kết quả; lưu revision, môi trường và quyết định thật.

`/health`, capabilities và các bước đăng ký/đăng nhập/khôi phục tài khoản có chính
sách public/session riêng, được xác định trong auth contracts và tests. Inventory
48 endpoint ở đây là các data API project/usage/reporting, không phải toàn bộ API
công khai của ứng dụng. Offline report reader sử dụng file do người dùng mở; source
report không tự trở thành dữ liệu account trên server.

## Bàn giao

Task bổ sung ma trận và khả năng phát hiện thiếu guard trên route mới. Public
contracts, generated files và migrations không đổi. Phần kiểm tra SQL/browser
thực tế và review độc lập cần được ghi nhận riêng trước khi dùng để chốt nghiệm thu
bảo mật toàn sản phẩm (3.58/3.59/3.60).

Codex hỗ trợ đọc source, viết ma trận/tests và kiểm chứng theo yêu cầu Hà An.
Hà An cần đọc và giải thích được phần tiếp nhận. Review tự động và self-review
không thay quyết định nghiệm thu của người được giao review.
