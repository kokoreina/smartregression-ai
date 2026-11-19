# Task 3.46 — Danh sách ca nghiệm thu theo endpoint

Baseline `effd115`, product mode; 48 thao tác dữ liệu. Đối chiếu từ `CASES` của test matrix.

## Quy tắc chung

- A/B dùng phiên verified riêng và object thực riêng. A phải thao tác hợp lệ được trên dữ liệu mình trước khi dùng cùng object để thử B.
- B dùng ID thật của A, ID chưa tồn tại, P-A/object B và P-B/object A: đều phải bị chặn 404; không lộ dữ liệu hoặc attachment.
- Body owner_id bị từ chối 422. Spoof owner bằng query/header không thay actor phiên.
- Guest/invalid/expired/disabled: 401. Chưa verified: 403. Mutation/export thiếu/sai CSRF hoặc Origin sai: 403 trước dữ liệu.
- Sau mutation bị từ chối, dữ liệu/version/activity phải giữ nguyên. Bộ matrix hiện kiểm tra guards và owner forwarding bằng recording boundary, không thay nghiệm thu SQL/browser cho mọi endpoint.

| ID | Method và path | Ca negative A/B | Bằng chứng runtime hiện có |
| --- | --- | --- | --- |
| OWN-01 | `GET /api/v1/projects` | B list chỉ thấy dự án B. | SQL B list không thấy P-A; ảnh user có danh sách riêng. |
| OWN-02 | `POST /api/v1/projects` | Dự án tạo dưới B thuộc B; owner_id A bị từ chối. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-03 | `GET /api/v1/projects/{project_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Browser A xem được/B bị chặn; SQL xác nhận. |
| OWN-04 | `PATCH /api/v1/projects/{project_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | SQL A sửa được trong rollback/B 404; dữ liệu giữ nguyên. |
| OWN-05 | `POST /api/v1/projects/{project_id}/archive` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | SQL A archive được trong rollback/B 404; dữ liệu giữ nguyên. |
| OWN-06 | `POST /api/v1/projects/{project_id}/restore` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-07 | `GET /api/v1/projects/{project_id}/activity` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-08 | `GET /api/v1/projects/{project_id}/repository` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-09 | `GET /api/v1/projects/{project_id}/tree` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-10 | `POST /api/v1/projects/{project_id}/runs` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-11 | `GET /api/v1/projects/{project_id}/runs` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-12 | `GET /api/v1/projects/{project_id}/runs/{run_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-13 | `GET /api/v1/projects/{project_id}/runs/{run_id}/report` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-14 | `GET /api/v1/usage` | B chỉ xem usage/quota B, kể cả spoof owner A. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-15 | `POST /api/v1/projects/{project_id}/runs/{run_id}/ai` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-16 | `GET /api/v1/projects/{project_id}/runs/{run_id}/ai/{request_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-17 | `POST /api/v1/projects/{project_id}/assistance/ai` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-18 | `GET /api/v1/projects/{project_id}/assistance/ai` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-19 | `GET /api/v1/projects/{project_id}/assistance/ai/{request_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-20 | `POST /api/v1/projects/{project_id}/snapshots` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-21 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/tree` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-22 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/graph` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-23 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/nodes` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-24 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/source` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-25 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/impact` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-26 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/hotspots` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-27 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/calls` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-28 | `GET /api/v1/projects/{project_id}/snapshots/{commit}/reading-guide` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-29 | `POST /api/v1/projects/{project_id}/snapshots/{commit}/search` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-30 | `POST /api/v1/projects/{project_id}/notes` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-31 | `PATCH /api/v1/projects/{project_id}/notes/{note_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-32 | `GET /api/v1/projects/{project_id}/notes` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-33 | `GET /api/v1/projects/{project_id}/view-state` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-34 | `PUT /api/v1/projects/{project_id}/view-state` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-35 | `POST /api/v1/projects/{project_id}/scenarios` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-36 | `GET /api/v1/projects/{project_id}/scenarios` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-37 | `GET /api/v1/projects/{project_id}/scenarios/{scenario_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-38 | `GET /api/v1/projects/{project_id}/scenarios/{scenario_id}/graph` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-39 | `GET /api/v1/projects/{project_id}/scenarios/{scenario_id}/source` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-40 | `POST /api/v1/projects/{project_id}/scenario-comparisons` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-41 | `POST /api/v1/projects/{project_id}/graph-comparisons` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-42 | `POST /api/v1/projects/{project_id}/runs/{run_id}/export` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-43 | `POST /api/v1/projects/{project_id}/scenarios/{scenario_id}/export` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-44 | `POST /api/v1/reporting/views` | B dùng filter project_id P-A bị chặn; bỏ filter vẫn chỉ dữ liệu B. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-45 | `GET /api/v1/reporting/views/{view_id}` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-46 | `GET /api/v1/reporting/views/{view_id}/runs` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-47 | `POST /api/v1/reporting/views/{view_id}/csv` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. CSRF hợp lệ mới được xét quyền; request bị chặn không đổi dữ liệu. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |
| OWN-48 | `GET /api/v1/reporting/views/{view_id}/usage` | B dùng ID thật A/ID chưa tồn tại đều 404; thử ID object trộn khi có object con. | Chưa nghiệm thu SQL/browser đầy đủ; có guard tests. |

13 thao tác account/public có chính sách riêng trong `ACCOUNT_AND_PUBLIC_OPERATIONS`. Không có API members/roles/assignment/invite.

## Cách ghi nhận

Mỗi ca ghi revision, môi trường, object fixture, expected/actual, status/code, kiểm tra dữ liệu không đổi, bằng chứng và người review. Chưa chạy ghi Not run. Không lưu password, cookie hoặc token.
