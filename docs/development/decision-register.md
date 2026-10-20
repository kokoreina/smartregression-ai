# Sổ quyết định và hiện trạng

Mốc nội dung ban đầu: 2026-10-06; workspace D:\smart-regression-ai hiện có Git.
Các tài liệu C1.SE26 trong `C1.SE26_DOCUMENTS/` được bổ sung sau mốc bootstrap.
Proposal v1.4, Architecture v1.3, Database v1.5, Project Plan v1.1 và Scrum workbook
v1.4 đã được trích xuất để đối chiếu phạm vi/kiến trúc/backlog; revision history ghi
pending review nên không xem đây là mentor-approved. Git không xác định người duyệt.

Đây là chỉ mục tới nguồn quyết định, không phải ADR thứ hai. `accepted` nghĩa nguồn
được dẫn đã ghi accepted hoặc là phạm vi user giao rõ; không giả xác nhận mentor.
`proposed`: phương án đang đề xuất; `pending`: chưa quyết; `superseded`: đã có nguồn
thay thế, phải giữ liên kết cũ/mới. Không xóa lịch sử để làm như mọi quyết định đã có sẵn.

| ID | Quyết định/phạm vi | Trạng thái | Nguồn và giới hạn | Người quyết định |
| --- | --- | --- | --- | --- |
| D01 | Monorepo, Python src package, React frontend; hướng phụ thuộc core/application/adapters | accepted cho bootstrap | [ADR 0001](../architecture/decisions/0001-bootstrap.md), [architecture](../architecture/overview.md); không suy ra kiến trúc worker đã chốt | Chưa ghi người cụ thể trong ADR |
| D02 | Python 3.14.x, FastAPI/Pydantic/uv/pytest/Ruff; React 19/TS strict/Vite 7/npm/ESLint; source CI GitHub Actions | accepted cho bootstrap, có implementation | [pyproject](../../pyproject.toml), [package](../../frontend/package.json), [uv lock](../../uv.lock), [npm lock](../../frontend/package-lock.json), [CI](../../.github/workflows/ci.yml); Node dòng 22 >=22.14 | Theo ADR D01, chưa ghi tên |
| D03 | Backend models là nguồn chuẩn; export OpenAPI/types; demo tĩnh, API health | accepted cho bootstrap | [contract](../contracts/README.md), [models](../../backend/src/smartregression/contracts/models.py); không có analyze endpoint | Theo ADR D01 |
| D04 | MVP một ngôn ngữ/framework, dùng test có sẵn; không sửa/sinh test repo đầu vào, không cross-repo | Mục tiêu dự án nêu trong Proposal v1.4; cặp công nghệ cụ thể pending | [Proposal v1.4](../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx); không suy ra implementation đã xong hoặc proposal đã duyệt | Revision ghi pending review |
| D05 | Một ngôn ngữ/framework repo đầu vào; semantics PR diff, parser/discovery | pending | Proposal v1.4 yêu cầu một cặp; [spike backlog](../backlog/bootstrap.md) vẫn cần chọn bằng evidence. Pytest fixture của repo này không chốt framework đầu vào | Chưa xác định |
| D06 | LLM provider/model, embedding/index, DB và retention | pending | Proposal/Architecture mô tả LLM/RAG; Architecture nêu PostgreSQL target nhưng cần xác nhận, Database v1.5 ghi PostgreSQL và nhắc Project Plan cho phép SQLite. ADR 0001 là bootstrap hiện hành | Chưa xác định |
| D07 | Runner isolation/transport/timeouts/cancellation/job semantics | Proposed trong tài liệu thiết kế; implementation/decision cụ thể pending | Architecture v1.3/Database v1.5 mô tả worker/sandbox; [runner port](../../backend/src/smartregression/core/execution/ports.py) và adapter README chưa phải runner thật | Chưa xác định |
| D08 | Kết nối repo qua GitHub; một CI/CD platform cho MVP | GitHub repository là scope proposal; CI platform cụ thể pending | Proposal v1.4; [integration](../../integrations/github-actions/README.md) còn future; source CI không đồng nghĩa input-repo workflow đã làm | Chưa xác định |
| D09 | Dataset/license/baselines/cohort/fault adjudication/ngân sách/ngưỡng | Mục tiêu trong proposal; protocol/run evidence pending | Proposal v1.4 và [evaluation outline](../research/evaluation-protocol.md); mục tiêu không phải kết quả thực nghiệm | Chưa xác định |
| D10 | Chia 5 vùng công việc | proposed | [module ownership](module-ownership.md); chín profiles là chín vai trò, chưa gán người | Nhóm cần phân công |
| D11 | Bộ hướng dẫn và định tuyến profile/rule | accepted cho nhiệm vụ tài liệu này | Yêu cầu người dùng; [AGENTS](../../AGENTS.md), [governance](../rules/00-governance.md); không cấp quyền tools hay bật enforcement | Người dùng yêu cầu; chưa có phê duyệt mentor |

## Mâu thuẫn/điểm cần phân biệt

- Báo cáo [review](verification.md) là ảnh chụp lần kiểm tra trước: Vite dev bị EPERM.
  Sau đó user yêu cầu mở web; dev server đã được chạy. Lần đối chiếu tài liệu này
  nhận HTTP 200 tại UI và health qua proxy; không suy ra browser e2e/build/full suite pass.
  Giữ lịch sử, cập nhật bằng chứng ở [verified commands](verified-commands.md).
- Yêu cầu UI tương lai có `cancelled`, nhưng enum contract hiện **chưa có** trạng thái
  đó hoặc job ID. Profile yêu cầu thiết kế khi triển khai, không tự thêm enum/endpoint.
- Scope PR, selection thật, DB và runner trong prompt là mục tiêu tương lai; README-only
  hiện hành là chưa triển khai. Không biến chúng thành tính năng đã chạy nhờ tài liệu.
- Không thấy mâu thuẫn cần đổi stack. Nếu xuất hiện proposal/ADR mới, đối chiếu nguồn,
  ghi phương án và người quyết định; không mặc định code hay docs luôn thắng.

## Cập nhật

Task đã giao rõ có thể cập nhật quyết định trong phạm vi đó mà không xin phép lại.
Quyết định kiến trúc mới dùng [ADR template](../templates/adr.md), liên kết vào bảng;
đánh dấu nguồn cũ superseded khi có quyết định thay thế thực tế. Review mỗi sprint,
không tự điền tên người duyệt hay ngày duyệt chưa xảy ra.
