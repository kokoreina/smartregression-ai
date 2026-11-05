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
| D05 | Python + pytest cho repo đầu vào MVP; revision semantics 1.06; parser/discovery và phiên bản input được theo dõi riêng | accepted cho Python/pytest và baseline thiết kế 1.06; acceptance implementation/G1, parser/discovery và phiên bản input còn riêng/pending | [ADR 0002](../architecture/decisions/0002-python-pytest-input.md), [revision semantics 1.06 — A01](../research/sprint-1/revision-semantics.md#10-quyết-định-và-việc-còn-lại-sau-review), [review PR #5](https://github.com/kokoreina/smartregression-ai/pull/5#pullrequestreview-5637165169), [handoff 1.06](../research/sprint-1/an-revision-handoff.md); user xác nhận task 1.06 đã chốt ngày 2026-10-26, không coi acceptance thiết kế là bằng chứng runtime | Nguyễn Tấn Huy cho Python/pytest; revision semantics được user truyền đạt đã chốt, chưa cung cấp tên người quyết định riêng |
| D06 | LLM provider/model, embedding/index, DB và retention | pending | Proposal/Architecture mô tả LLM/RAG; Architecture nêu PostgreSQL target nhưng cần xác nhận, Database v1.5 ghi PostgreSQL và nhắc Project Plan cho phép SQLite. ADR 0001 là bootstrap hiện hành | Chưa xác định |
| D07 | Runner isolation/transport/timeouts/cancellation/job semantics | Proposed trong tài liệu thiết kế; implementation/decision cụ thể pending | Architecture v1.3/Database v1.5 mô tả worker/sandbox; [runner port](../../backend/src/smartregression/core/execution/ports.py) và adapter README chưa phải runner thật | Chưa xác định |
| D08 | Kết nối repo qua GitHub; một CI/CD platform cho MVP | GitHub repository là scope proposal; CI platform cụ thể pending | Proposal v1.4; [integration](../../integrations/github-actions/README.md) còn future; source CI không đồng nghĩa input-repo workflow đã làm | Chưa xác định |
| D09 | Dataset/license/baselines/cohort/fault adjudication/ngân sách/ngưỡng | Mục tiêu trong proposal; protocol/run evidence pending | Proposal v1.4 và [evaluation outline](../research/evaluation-protocol.md); mục tiêu không phải kết quả thực nghiệm | Chưa xác định |
| D10 | Chia 5 vùng công việc | proposed | [module ownership](module-ownership.md); chín profiles là chín vai trò, chưa gán người | Nhóm cần phân công |
| D11 | Bộ hướng dẫn và định tuyến profile/rule | accepted cho nhiệm vụ tài liệu này | Yêu cầu người dùng; [AGENTS](../../AGENTS.md), [governance](../rules/00-governance.md); không cấp quyền tools hay bật enforcement | Người dùng yêu cầu; chưa có phê duyệt mentor |
| D12 | Hoàn thiện local Sprint 1 theo research foundation + technical spike, task 1.01–1.12/G1; workbook chỉ đọc; không commit/push/merge/deploy | accepted cho scope nhiệm vụ 2026-10-31; không phải sprint acceptance | Brief user hiện hành được tóm tắt ở [closeout decisions](../research/sprint-1/closeout-decisions.md); [review](../research/sprint-1/review.md) là trạng thái bàn giao | Người dùng trong phiên hiện hành; không suy tên/quyền mentor |
| D13 | Engine PostgreSQL cho backend Sprint 2 | accepted theo user; tách khỏi phần DB pending lịch sử ở D06; không chốt provider/index/retention | User xác nhận engine, được nhắc lại trong brief 2.20-A; [team guide 2.20](sprint-2-team-guide.md#task-220), [checkpoint](task-2.20-checkpoint.md#1-trạng-thái-nguồn-và-baseline) | Nguyễn Tấn Huy truyền đạt quyết định nhóm; không suy mentor approval |
| D14 | Tooling, minimum schema và writer boundaries foundation 2.20 | accepted P1/P2/P4 ngày 2026-11-03 theo user xác nhận nhóm thống nhất; H1 independent foundation triển khai cục bộ, DB acceptance pending | [Checkpoint 2.20-A](task-2.20-checkpoint.md#11-decision-register-cho-checkpoint): Core + psycopg3 + Alembic, 5-table foundation và writer boundaries; [handoff 2.20-B](task-2.20-b.md) tách code local khỏi KH schema/migrations/adapter chưa có; P3 bundle/P5 retrieval vẫn cần quyết định riêng | Nguyễn Tấn Huy truyền đạt nhóm đã thống nhất sau danh sách P1/P2/P4; không suy mentor approval/runtime acceptance |
| D15 | Candidate/environment, inventory PostgreSQL và native pytest IDs cho 2.08/2.09 | accepted 2026-11-04; implementation/acceptance riêng | [Quyết định 2.08/2.09](task-2.08-2.09-decisions.md): sqlparse + TinyDB fixed SHA, locked collection profile/isolation, hai bảng, exact native IDs, explicit empty/partial/failed; thay đề xuất inventory checkpoint §6.2, không chốt P3/P5 | Nguyễn Tấn Huy xác nhận áp dụng phương án ưu tiên cho nhóm; không suy mentor approval |
| D16 | P3: EvidenceBundle persistence 2.05 và lifecycle với 2.06/2.13 | accepted 2026-11-04 theo xác nhận nhóm qua H1; implementation/acceptance riêng | [Đặc tả P3 và nguồn xác nhận](task-2.05-p3.md#p3-status): bounded canonical bytea 2 MiB, full identity, immutable retry, verification trước freeze/transient inspection và compound SQL transaction; KH giữ migration chain. Thay trạng thái proposed trước đó | Nguyễn Tấn Huy truyền đạt “vậy hãy chốt như phương án đề xuất đi, cả nhóm đều đã đồng ý rồi”; không suy mentor approval hoặc GitHub approval/merge |
| D17 | P5: local structural + lexical retrieval cho Sprint 2 | accepted 2026-11-05 theo xác nhận cả nhóm qua H1; implementation/acceptance riêng | [ADR 0003](../architecture/decisions/0003-local-lexical-retrieval.md): PostgreSQL metadata + hashed local artifacts, nullable embedding model, frozen base/target provenance, bounded retrieval và trusted ready lifecycle; thay retrieval/index pending của D06/P5, không chọn LLM provider/model | Nguyễn Tấn Huy truyền đạt “tôi và cả nhóm đều đã đồng ý với các ý này”; không suy code review/mentor approval |

D17 là nguồn hiện hành cho P5; ghi chú P5 pending trong các handoff cũ là lịch sử.
Backend retrieval đã được chọn; acquisition-to-ready bridge, domain migrations,
retrieval wiring và acceptance vẫn là việc triển khai. D06 giữ lịch sử; LLM provider/
model và production retention chưa được chốt bởi D17.

D14 cập nhật hiện trạng ngày 2026-11-04: foundation, schema/migrations và run/report
adapter đã merge qua PR #25 vào main `b50fe89`. [Handoff adapter](task-2.20-adapter.md)
ghi kiểm chứng PostgreSQL thật; trạng thái local/pending trong hàng D14 là mốc H1
ban đầu. Không suy acceptance inventory hoặc whole sprint từ foundation.

Baseline P3 ngày 2026-11-04: main fetch `9bcd6a4` đã merge PR #30, nối opt-in
run/report persistence; hai source CI checks của PR SUCCESS. Revision files hiện
có head `20261104_03` cho inventory, không dành sẵn M003 cho evidence. Các dữ kiện
này không chứng minh PostgreSQL EvidenceStore/resolver đã tồn tại. D16 được chấp
thuận bởi xác nhận user riêng nêu trong đặc tả P3, không suy từ các mốc merge/CI này.

D05/D07/D09 giữ lịch sử ở bảng. Evidence mới và các điểm quyết định còn lại được
phân loại theo mốc cần chốt trong [closeout decisions](../research/sprint-1/closeout-decisions.md).
Các PR đã merge có review thực; CI main `e937f66` được quan sát success trên GitHub
ngày 2026-10-31. Không suy CI đó xác minh thay đổi local mới hoặc toàn bộ gate G1.

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
