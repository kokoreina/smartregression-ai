# Sprint 3 — Team guide cho 75 task web

Ngày đối chiếu **15/11/2026, UTC+7**. Backlog: [workbook](../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned.xlsx),
`Sprint 3 Backlog!B8:G82` và briefs `B113:K786`. Scope hiện hành: phần mềm giúp
người dùng hiểu repo GitHub, quan hệ giữa file/folder và ảnh hưởng khi thay đổi.

**Nguồn trạng thái/task/dependency duy nhất:** [audit 75 task](sprint-3-phase-1-audit.md).
Đầu ra và AC gốc vẫn ở workbook; không suy Done từ số tests hoặc trạng thái Git.
Hướng dẫn 20 task Gemini/selection/execution trước đây được bảo toàn tại
[guide nghiên cứu lịch sử](archive/sprint-3-research-team-guide.md). Cùng ID 3.xx
trong tài liệu lịch sử không mang ý nghĩa task mới. Các sheet `S3 Backlog trước
14-11`/`S3 Reports trước 14-11` giữ nguyên lịch sử, không đánh Done bằng đổi scope.

## 1. Bắt đầu đúng workspace

Đợt 3–8 có implementation local. Dùng [operations](sprint-3-local-operations.md)
để khởi động đúng product mode, mở báo cáo offline hoặc chạy Compose HTTPS riêng.
Kết quả mới ở [handoff](sprint-3-phase-3-8-handoff.md); các mục "chưa có" trong
handoff đợt1/2 là lịch sử. Audit75 vẫn là nguồn trạng thái task duy nhất.

- Code web: `D:/smart-regression-ai/var/main-preview`, branch
  `feat/web-repository-analysis`. HEAD/main sau fetch: `5a30a7a`; web vẫn local.
- Workspace gốc đang ở branch nghiên cứu cũ; không chạy nhầm frontend ở đó.
- Đọc AGENTS và profile/rule đúng task; kiểm tra status và hướng dẫn thư mục con.
  Giữ local changes; không reset, tự init Git hoặc sửa generated files bằng tay.
- Nhóm đã giao Huy thực hiện toàn bộ phần còn lại. Owner gốc trong workbook vẫn
  được giữ để truy vết; ghi Huy là người thực hiện thực tế trong handoff.
- Review/approve của người khác chỉ ghi khi thực sự xảy ra; self-review không thay
  independent review. Không tự commit/push/merge/deploy khi chưa được giao.

## 2. Tám đợt và cách nhận task

| Đợt | Luồng sử dụng cần hoàn thành |
| --- | --- |
| 1 | Baseline/audit → demo tree/commit/impact → saved Gemini → export/import |
| 2 | Register → email verification → login/session/logout/recovery + app shell |
| 3 | Personal projects → durable runs/history/AI/quota → HTTPS staging |
| 4 | Explorer/tree → Python/JS dependencies → static calls/hotspots → resume |
| 5 | Description hypothesis/code-diff overlay → impact/A-B/version comparison |
| 6 | Reading guide → bounded feature retrieval → explain file/folder → AI smoke |
| 7 | Filtered dashboards → CSV/JSON/print → responsive/motion/performance |
| 8 | Cross-module security/browser/restore → final 18-feature acceptance |

Đợt nghiệm thu của từng task đã ghi trong audit. Trước khi implement: mở đúng
task → đọc dependency và AC → kiểm tra output đã có → chọn lát hành vi nhỏ có
producer/consumer thật → viết regression cho lỗi có thể tái hiện → implement →
checks → evidence/handoff. Contract readiness không yêu cầu task cha đã hoàn tất
mọi module; ghi rõ slice đã chốt để tránh vòng chờ.

## 3. Profile, rule và skill

| Công việc | Profile/rules | Skill khi có trigger |
| --- | --- | --- |
| Chia task, quyết định, tích hợp | Coordinator; 00/01/13 | api-contracts khi chạm schema |
| API/DTO/application/storage | Backend/Contracts; 01/02/03/04/06 | api-contracts, test-driven-development |
| Python/JS diff/graph/impact | Change Impact; 01/06/09 | test-driven-development; evaluation-integrity khi có nghiên cứu |
| Gemini/retrieval/context | RAG/LLM; 03/04/06/08 | security-review; TDD cho boundary |
| UI/tree/graph/report | Frontend; 02/03/06 | ui-design, accessibility-review, webapp-testing |
| Debugging | Profile module + 07 | systematic-debugging, regression test phù hợp |
| CI/dependency/staging/backup | DevOps/Runner; 06/10/12 | security-review; github-actions-hardening khi đổi workflow |
| Security/acceptance/review | Reviewer, QA; 05/06/14 | security-review; browser kiểm tra thật |
| Excel trạng thái | Coordinator + 13 | spreadsheets; giữ layout/validation/formulas và actual hours thật |

Profiles là hướng dẫn vai trò, không tự khởi agent song song. Đọc skill khi phù
hợp, không cài tooling hoặc sinh tài liệu chỉ để làm đủ quy trình.

## 4. Quy tắc sản phẩm bắt buộc

- React/FastAPI/PostgreSQL, application/core/adapters hiện có; không microservice,
  queue/vector DB hoặc chạy code repo đầu vào từ web.
- Tree liệt kê file Git nhiều ngôn ngữ; phân tích ảnh hưởng hiện chỉ Python.
  JavaScript parser/what-if/call graph chưa có thì ghi chưa triển khai.
- Containment/import/static call là ba quan hệ khác nhau. Không giả runtime trace,
  lỗi, xác suất ảnh hưởng hoặc số liệu nghiên cứu từ một graph.
- Full SHA/config/snapshot theo report; code/diff what-if là overlay bất biến, không
  commit hoặc execute. Natural-language what-if là hypothesis, không static fact.
- Owner là session ở backend; không membership/roles/invite trong scope hiện hành.
  Auth/project chưa triển khai, local Host/Origin không phải authentication.
- AI explicit action + consent; key backend, không VITE/log/prompt. Metadata
  mặc định; excerpt riêng chưa triển khai. Giữ budget và unknown charges.
- UI default static; mở saved report không gọi provider. Ledger local 5/5 nên
  đợt 1 chỉ dùng report thật đã lưu. Không tự reset để gọi mới.
- Saved/DEMO/mock/real và analysis/test execution hiển thị khác nhau. Narrative
  là giải thích cần đối chiếu evidence. Unknown cost/metric không thành zero.
- Dữ liệu nghiên cứu/test inventory không đổi nghĩa thành dữ liệu tài khoản web.

## 5. Bắt đầu đợt 2

**Cập nhật triển khai 15/11/2026:** auth/app shell đã có local code. Xem
[thiết kế và wireframes](sprint-3-auth-design.md),
[lệnh/kết quả/pending đợt 2](sprint-3-phase-2-handoff.md). PostgreSQL tests đạt;
Gmail receipt và browser vẫn là gate riêng. Không đọc các bước dưới đây như trạng
thái “chưa có code” hoặc suy đã merge từ việc implementation local tồn tại.

Đọc [contracts/ownership/auth brief](sprint-3-web-contracts.md). Thứ tự:
3.31 auth migration → 3.32 session/password/CSRF → 3.33 email → 3.34 recovery →
3.61/3.62 shell và auth slice của 3.63. Project slice 3.35/3.63 ở đợt 3.
Owner/quota contracts được chuẩn bị trước; quota thật còn phụ thuộc durable runs.

Routes mới `/api/v1`; production disable legacy local POSTs trước public staging.
Backend checks session/verified/owner trên mọi object/export. New account AI quota
0; không có đường public tự cấp quota. SMTP/domain/HTTPS chưa cấu hình thì ghi
prerequisite, không giả email sent hoặc delivery/verification thành công.

Đợt 1 không bị coi Done khi browser còn thiếu; phần auth độc lập vẫn có thể bắt
đầu sau khi contracts đã khóa. Không tăng phạm vi bằng việc đóng task chưa làm.

## 6. Checks và bàn giao

Lệnh và kết quả đợt này: [handoff](sprint-3-phase-1-handoff.md). Backend unit/API
tests không gọi Gemini thật. Browser phải kiểm thao tác/keyboard/viewport;
HTTP 200/SSR/build không thay browser pass. PostgreSQL tests chỉ cần khi task
thực sự chạm schema/persistence; chưa làm auth DB thì không báo đã kiểm chứng.

Handoff luôn có: behavior trước/sau → files/contracts → commands/results →
unverified/pending → bước tiếp theo. Ghi baseline cùng hash/artifact cho kết quả
quan trọng. Excel dùng Done/Ongoing/Blocked/Not started đúng validation; actual
hours không lấy từ estimate, không điền tỷ lệ phần trăm không đo được.

AI được dùng để hỗ trợ khảo sát/code/tests/tài liệu. Thành viên nhận task phải
đọc/hiểu thay đổi và chạy kiểm chứng phù hợp; không ghi approval/đóng góp giả.
