# Bàn giao quyết định Sprint 2, mục 1–11

Ngày 2026-11-05. [ADR 0004](../architecture/decisions/0004-sprint-2-integration-decisions.md)
là nguồn chuẩn; H1 truyền đạt đồng ý cả nhóm và giao chính thức hóa. Bản này chỉ
ghi kết quả task tài liệu, không thay ADR hoặc xác nhận runtime/human acceptance.

## Git và phạm vi

- Root IDE `D:\smart-regression-ai` ở nhánh lịch sử, có untracked `outputs/` và
  `start-cliproxy-management.bat`; giữ nguyên, không checkout/reset/clean.
- Sửa ở checkout `D:\smart-regression-ai\var\main-audit-20261105`, branch
  `docs/sprint-2-p5-local-retrieval`, HEAD `0c9ec43ea30b014b14f32192fff82f792fac51e5`.
  Working tree sạch trước task. Không tạo nhánh/commit/push/PR/merge/deploy.
- Fetch sandbox fail proxy connection; fetch được cấp quyền thành công, main
  `07452660ab37699b0fbc28864601ea9e653f1bd3`. Không xem unrelated open PRs.
- Bốn commits H1 `e03312a`, `1c2e011`, `f88e823`, `b7ac7a2` không là ancestors
  của main ở mốc này; không cherry-pick hoặc viết lại implementation trong task.

Publication follow-up theo yêu cầu user: cho phép commit/push tài liệu trên nhánh
hiện tại; không tạo PR/merge. Fetch trước publication thấy main tiến tới `b3b251a`
(merge identity/evidence regressions 2.19), thêm `test_identity_evidence_flow.py`
và `task-2.19-an.md`, không sửa các file của nhánh tài liệu. Audit/AC trong ADR
vẫn được pin ở baseline trước; không suy toàn bộ W09 đã xong hoặc tests mới đã
được chạy lại trong lượt publication này.

## Đã đổi và contract impact

Ghi accepted 11 mục, initial budgets chưa benchmark, review assignments, A01–A07,
remaining-capacity template và W01–W09/PR sequence trong một ADR tổng hợp. Register
thêm D18, D06 phân biệt pending lịch sử; guide/checkpoint/ADR P5/mapping/ordering/UI/
retrieval README và ownership/storage/RAG status notes dẫn cùng nguồn.

Workbook chỉ sửa text hai sheet Sprint 2: accepted decisions, reviewers và các
dependencies liên quan. Không đổi số giờ, 20 task/status, daily entries, dates,
formulas, allocations, chart data hoặc sheets Sprint 1/3/4. Không đổi Python/TS/
contracts/schema/generated types/migrations/dependencies. Source checks và tests
sản phẩm không được chạy lại cho task tài liệu này.

## Office integrity và giới hạn

File đã sửa: `C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx`.
Các vùng: `Sprint 2 Reports!B8:Z51` (chỉ ô text thuộc quyết định), `Sprint 2 Backlog`
review rows 71/77/95/113/119/131/137/143/149/155/161/167/173 và dependency row 110.
Các ô duplicate ẩn trong merged ranges được đồng bộ theo anchor, không unmerge.

Artifact Tool đã author giá trị. Full export thay nhiều native parts ngoài scope,
nên chỉ đóng gói các text cells đã author vào original OOXML. Independent checks
xác nhận chỉ `xl/worksheets/sheet5.xml` và `sheet6.xml` đổi; mọi ZIP parts khác,
mọi cell ngoài danh sách, style/formula/merge/layout trong hai sheets giữ nguyên.
ZIP integrity pass. Đã reimport file cuối và xem 10 vùng PNG tương ứng phần thay đổi.
Không suy verified native Excel behavior hoặc mới đo burn-down từ PNG.

Backup và integrity record ở ignored `var/decision-closeout/` của checkout sửa:
`backup/`, `workbook-integrity.json`, scripts và previews phục vụ reproduction.
Không commit các artifacts này. Runtime Node wrapper trả exit 1 dù scripts ghi đủ
authored export/previews; không ghi command đó exit 0. Python integrity packaging
trả exit 0; final file được reimport/render và kiểm tra độc lập, không lấy exit code
wrapper thay bằng chứng workbook preservation.

**Database DOCX chưa sửa:** `C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx`, §3.4.8,
bảng `knowledge_indexes`, row `embedding_model`, Nullable = `Not`. Cần đổi thành
nullable cho lexical và ghi design note đúng P5/ADR §10; migration code vẫn task riêng.
Runtime manifest ghi `libreOfficeVersion: null`, không có bundled renderer engine.
Skill [Documents](C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/documents/26.1030.10813/skills/documents/SKILL.md)
yêu cầu “Run `render_docx.py` to produce `page-<N>.png` images” và kiểm mọi trang,
đồng thời không dùng LibreOffice desktop của user thay bundled engine. Vì không
đáp ứng visual gate trong môi trường này, giữ nguyên DOCX; không xuất bản sửa chưa
kiểm. Quyết định NULL đã accepted và ghi trong ADR/workbook, không cần duyệt lại.

## Follow-up và bước tiếp theo

Checks task tài liệu (cwd checkout sửa): `git diff --check` exit 0;
`var/decision-closeout/verify_docs.py` chạy bằng bundled Python exit 0:
389 local links/anchors, 44 tables, balanced fences, đủ 11 decision sections,
20 task allocations giữ nguyên, không runtime/contract/migration changes.
`preserve_workbook.py` exit 0: 648 text cells (gồm duplicate merged cells),
chỉ hai sheet XML đổi và mọi cell/ZIP part ngoài scope giữ nguyên.
DOCX source giữ nguyên. Không chạy product suite/DB/browser trong task này.

- Implementation: W01–W08; chọn một slice, đọc routing/rules/skill tương ứng rồi code.
- Verification: W09/A01–A07, actual reviewer records và human acceptance.
- Operational inputs: remaining estimates, availability và calendar commitments;
  reviewer độc lập cho các task chưa được gán trong kế hoạch gốc (2.01/02/05/06/08/09/12).
  Không coi các ô reviewer cũ này là mở lại quyết định thiết kế 1–11.
- Office follow-up: sửa/render/verify DB Design tại môi trường hỗ trợ; không chờ
  chọn backend. Các pending LLM/production/research ngoài 1–11 giữ nguyên.

H1 bắt đầu **W02**: đối chiếu resolver/compound implementation cũ với main và AN/H2,
viết interface acquisition/manifest có negative fixtures, giữ guard đến khi đủ
verification/publication. W01 và thiết kế UI/acceptance làm độc lập khi interface rõ.
Contracts/analysis writer H1, shared migration chain KH; không sửa chồng.

Windows được giữ thức tạm thời bằng process `SetThreadExecutionState` riêng, không
đổi power plan; process phải được dừng trước bàn giao, tự hết hạn tối đa hai giờ.

## AI disclosure

OpenAI Codex hỗ trợ đọc/diff, soạn docs, author/verify workbook và self-review.
Đã đọc Proposal v1.4 Appendix C/D. Không tạo chữ ký, tỉ lệ đóng góp, completed review
hoặc kết quả tests chưa chạy. Nhóm giữ trách nhiệm đọc, hiểu và kiểm chứng.
