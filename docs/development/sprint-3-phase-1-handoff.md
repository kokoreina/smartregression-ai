# Sprint 3 đợt 1 — Bàn giao và nghiệm thu

Ngày: **15/11/2026, UTC+7**. Người thực hiện theo ủy quyền nhóm: Nguyễn Tấn Huy,
có coding agent hỗ trợ khảo sát, code, tests và tài liệu. Đây là self-verification;
chưa có review độc lập, commit/push/PR/merge mới hoặc phê duyệt mentor.

## 1. Trạng thái

**Phần code, audit, tài liệu và Excel đã hoàn thành trong scope đợt 1. Gate nghiệm
thu trình duyệt và hai lượt diễn tập còn chờ kết quả thực tế của Huy.** Đợt 2 có
thể bắt đầu từ [auth brief](sprint-3-web-contracts.md); không ghi toàn đợt 1 Done.

Worktree `D:/smart-regression-ai/var/main-preview`, branch
`feat/web-repository-analysis`; fetch thực tế xác nhận HEAD và origin/main đều
`5a30a7ac5a1e2ad87a45120fe7c043bae49be5d4`. Toàn bộ web changes vẫn local. Root
workspace dùng branch nghiên cứu cũ; không chạy nhầm frontend ở root.

Đã đọc Coordinator/Backend/Frontend/RAG profiles; rules 00/01/02/03/06/07/08/13;
skills api-contracts, test-driven-development, systematic-debugging,
security-review, ui-design, accessibility-review, webapp-testing và spreadsheets.
AI disclosure/giới hạn trách nhiệm được đối chiếu Appendix C/D của Proposal v1.4;
không sửa chữ ký, tỷ lệ đóng góp hoặc nội dung Proposal.

## 2. Đầu ra và thay đổi

- [Audit](sprint-3-phase-1-audit.md): đủ 75 task không trùng ID, dependency, tám đợt
  nghiệm thu chính và 20 task nghiên cứu tái sử dụng. 1 task đạt AC khảo sát
  (3.01), 30 implementation một phần, 44 chưa có feature web.
- [Team guide hiện hành](sprint-3-team-guide.md) theo bộ 75 task. Guide nghiên cứu
  được lưu [nguyên bản](archive/sprint-3-research-team-guide.md); không đổi trạng
  thái hoặc ý nghĩa 20 task cũ.
- [Contracts/auth brief](sprint-3-web-contracts.md): routes hiện có và API `/api/v1`
  tương lai, session/CSRF/email/owner/quota invariants và negative cases. Chưa có
  auth endpoints, web migrations hoặc owner enforcement runtime mới.
- Real reports trước đây có thể đổi overview repo nhưng giữ identity repo cũ.
  Backend validator và offline reader nay ràng buộc GitHub slug/hash. Test tái
  hiện đã fail trước sửa rồi pass; demo fixture vẫn giữ nhãn demo.
- AI state trước đây chấp nhận completed+reason/not_run+error. Backend/frontend
  nay từ chối trạng thái mâu thuẫn; consumer kiểm enum canonical và integer token
  usage/unknown keys. Shape export/schema version không thay đổi.
- Câu hỏi có mẫu credential nhận diện được nay bị chặn trước source acquisition/
  provider; tái sử dụng filter retrieval, không echo dữ liệu nhạy cảm. Đây không
  phải bảo đảm DLP toàn diện. Unit test synthetic secret fail trước rồi pass sau.
- UI mặc định static, ghi rõ excerpt chưa hỗ trợ và lỗi kết nối API có hướng phục
  hồi/mở saved report. Giữ request guards, tree identity,
  evidence navigation, full export/import, saved labels và JSON error recovery.
- Fix cache SSR đã có từ lượt trước được kiểm chứng lại: runtime React vẫn tải
  được sau cả hai SSR suites; không cần reset cache mỗi lần chạy tests.

Canonical models là nguồn; OpenAPI/types đã sinh từ lượt trước và exporter/types
checks hiện pass. Validation bổ sung không đổi wire fields hoặc endpoint. Các
report thật đã lưu và stage-v2 reader cũ vẫn được consumer checks chấp nhận.

## 3. Kiểm chứng thực tế

Môi trường dùng lại: Python 3.14.3 từ `../s3-gemini/.venv/Scripts/python.exe`,
Ruff cùng venv, Node 22.14.0/npm hiện có, Git portable
`../task-2.13-tools/mingit/cmd`. Không clean install, thêm dependency, chạy input
repo, Docker/app DB migration hoặc paid Gemini call.

PowerShell tại worktree, đặt `PYTHONPATH=backend/src` và portable Git trên PATH:

```powershell
../s3-gemini/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_repository_web.py backend/tests/unit/test_repository_tree.py backend/tests/unit/test_repository_narrative.py backend/tests/unit/test_repository_export.py backend/tests/unit/test_context_retrieval.py backend/tests/unit/test_stage_reports.py backend/tests/unit/test_workflow_contracts.py backend/tests/integration/test_api.py backend/tests/integration/test_analysis_cli.py -q -p no:cacheprovider --basetemp var/phase1/tests-verified --junitxml var/phase1/tests-verified.xml --tb=short
../s3-gemini/.venv/Scripts/python.exe scripts/export_contracts.py --check
../s3-gemini/.venv/Scripts/ruff.exe check .
../s3-gemini/.venv/Scripts/ruff.exe format --check .
npm --prefix frontend run contracts:check
npm --prefix frontend run lint
npm --prefix frontend run build
node frontend/scripts/test-repository-view.mjs var/web-analysis-final-vietnamese.json var/demo-static-20261115.json
node frontend/scripts/test-dev-runtime.mjs http://127.0.0.1:5173
D:/smart-regression-ai/.tools/bin/uv.exe lock --check
git diff --check
```

| Check | Kết quả quan sát |
| --- | --- |
| Final targeted backend/API/CLI/contracts/retrieval tests | **203 passed**, exit 0; 76,90s; XML `var/phase1/tests-verified.xml` |
| Exporter / generated TypeScript | Pass; không chỉnh generated files bằng tay |
| Ruff check / format | Pass; không hạ rule/skip test |
| Frontend contracts gate | **88 validation + 11 report SSR + 60 repository checks** pass |
| Hai report thật qua consumer và JSON round-trip | **62 repository checks** pass |
| Frontend lint/build | Pass; build gồm TypeScript check |
| Live Vite cache regression | Pass; runtime JS còn HTTP 200 sau cả hai SSR suites |
| uv lock --check | Pass; 50 packages resolved, không sync/install |
| Actual HTTP tree/static/no-consent | 200 tree, 200 static, 422 thiếu consent; ledger giữ nguyên |
| Final runtime sau restart | Health 200; câu hỏi chứa credential synthetic trả 422 `sensitive_question`, không echo input; `var/phase1/final-http-guard.json` |
| Saved AI canonical validation | Pass; narrative completed trong report lịch sử, không generation mới |
| Final integrity | 75 ID/PB/briefs khớp nguồn, 127 local file links hợp lệ; 22/33 file dirty ban đầu giữ byte-identical, 11 file sửa đúng scope |
| Recognized credential scan | Không có mẫu khớp trong 148 source/document files; không phải secret audit toàn diện |
| Browser/rehearsal | **Chưa kiểm chứng**: Browser host unavailable; chờ Huy báo thao tác thực tế |

Hai vòng kiểm tra trước thêm guard cuối là 195 pass; kết quả 203 ở trên mới là
vòng cuối. Command `uv` đầu tiên thiếu PATH, sau đó dùng executable rõ ràng đã
pass. Tests mới tái hiện 4 lỗi provenance/state và credential guard trước sửa;
không coi các vòng fail tái hiện là lần nghiệm thu. Full backend suite/CI/real
PostgreSQL acceptance chưa chạy cho task này; không có thay đổi DB cần migration.

Repo HTTP thật: `andialbrecht/sqlparse`, base
`91149dffdf691945dc5e20d9c9623390d9b96ffb`, target
`be3b7a68d07af5a22b49765e26d2541be640999f`. Target tree **106 entries/94 files**;
static response **5 changed files/55 impact candidates**. Chưa chạy test của repo.
Artifact `var/phase1/http-check.json` ghi kết quả; `static-http.json` giữ response.
HTTP check xác nhận byte hash ledger không đổi. Ledger có 5/5 runs trước task;
không reset/increase/đổi session. Cost unknown giữ null/reservation riêng.

### Excel

File gốc `C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned.xlsx` đã cập
nhật status và evidence của 75 task, cùng ghi chú baseline Sprint 3 Reports.
Counts: **1 Done / 30 Ongoing / 44 Not started**. Chỉ 3.01 Done về đầu ra khảo sát;
không đóng feature task bằng lát demo. Layout kiểu Sprint 2, IDs, English
descriptions, PB/owners, estimates, formulas, data validation và actual hours giữ
nguyên. Các cột hours gốc có ý nghĩa input/time-log, không suy giờ từ trạng thái
Done; chưa đo thì không tự điền.

Artifact tool đã author/recalculate/render bản làm việc. Kết quả final xác minh
chỉ hai sheet XML liên quan thay đổi; **68 package parts khác byte-identical**,
formula/shared-formula expressions và layout/validation không đổi. Preview top,
task evidence và baseline đã xem; không thấy lỗi formula trong bản recalculated.
Bản sao trước sửa và kiểm chứng kỹ thuật ở `var/phase1/`, không đưa vào commit.
Workbook mới cũng nằm trong worktree cho review; file gốc ở workspace là file
người dùng sử dụng. Chưa kiểm tra mở bằng Excel native hoặc native recalc engine.

Guide tại workspace gốc hiện là chỉ dẫn cục bộ tới guide/audit trong worktree để
tránh dùng nhầm bộ 20 task. Nội dung guide cũ được lưu byte-identical trong archive.
Các relative links trong bản lịch sử vẫn nguyên như nguồn gốc; khi tra cứu, resolve
theo vị trí `docs/development` cũ. Khi tích hợp, dùng guide đầy đủ trong worktree,
không đưa chỉ dẫn đường dẫn `var/main-preview` của checkout gốc vào PR.

## 4. Browser checklist cần hoàn tất

Huy đã trả lời sẽ kiểm tra và báo kết quả cụ thể. Chưa nhận kết quả thì không điền
pass hay suy từ ảnh/HTTP. Mỗi dòng dưới đây còn pending cho tới quan sát thật:

| Case | Cần quan sát | Trạng thái |
| --- | --- | --- |
| B01 | Mở/reload có UI; không runtime error/trang trắng | Chưa kiểm chứng |
| B02 | Repo/tree đúng SHA, search giữ parent, chọn file/collapse | Chưa kiểm chứng |
| B03 | Enter trong search không submit phân tích | Chưa kiểm chứng |
| B04 | Static analysis đúng base/target; đổi SHA xóa report cũ; tree refresh giữ report | Chưa kiểm chứng |
| B05 | Saved Gemini có nhãn, evidence click mở/focus đúng | Chưa kiểm chứng |
| B06 | Download → reload → reopen giữ narrative/identity, không network AI | Chưa kiểm chứng |
| B07 | JSON hỏng/quá lớn báo lỗi và giữ report hợp lệ trước đó | Chưa kiểm chứng |
| B08 | Backend offline vẫn mở report local; error có đường phục hồi | Chưa kiểm chứng |
| B09 | Keyboard/focus/390-768-1440px/200% zoom | Chưa kiểm chứng |
| B10 | Hai lượt diễn tập xuyên suốt trên bản cố định | Chưa kiểm chứng |

Khi có kết quả Huy, ghi rõ browser/URL, bước, observed result và lỗi. Không cần
đợi thành viên khác để code; vẫn cần bằng chứng để đóng gate browser.

## 5. Chạy demo và tiếp tục

Hai tiến trình local của task: backend uvicorn port 8000, frontend Vite port 5173.
Bind loopback; nhận diện đúng command/port khi dừng, PID có thể đổi sau restart.
Để chạy trên máy có toolchain chuẩn:

```powershell
uv sync --locked
npm --prefix frontend ci
uv run uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000
# Terminal khác, cùng worktree:
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Nếu dùng environment hiện có, đặt `PYTHONPATH=backend/src`, prepend portable Git
và gọi `../s3-gemini/.venv/Scripts/python.exe -m uvicorn ...`. Gemini key chỉ đọc
từ trusted backend env file qua `SMARTREGRESSION_GEMINI_ENV_FILE`; không cần key
để static/import. Không in `.env`. Không chạy `uv sync/npm ci` chỉ để demo trên
environment hiện đã có nếu không cần install.

Mở `http://127.0.0.1:5173/`, đọc sqlparse rồi nhập cặp SHA ở trên, tải tree, chọn
file và chạy static. **Mở báo cáo đã lưu** chọn
`var/demo-20261115/sqlparse-gemini-saved.json` để xem narrative thật lịch sử; không
giới thiệu là vừa gọi Gemini. Thời điểm xuất không phải thời điểm phân tích.
Để dừng: Ctrl+C trong đúng terminal đã khởi động mỗi service; không kill các
Python/Node khác của người dùng. Nếu dev cache cũ hỏng, restart Vite một lần với
`--force`; regression đảm bảo SSR không phá cache nữa.

### Nhóm thay đổi để review khi được giao publish

1. Backend/contracts: GitHub adapter + routes/use case/narrator, contract/exporter
   và generated outputs, credential/provenance/state guards, tests tương ứng.
   `httpx` runtime classification/uv.lock đã có từ trước; lock check pass. Không
   gộp `scripts/llm/smoke.py` vào PR nếu chưa review diff vốn có.
2. Frontend/verification/handoff: repository views/tree/client/full-report reader,
   App/styles, isolated SSR caches/runtime regression, guide/audit/contracts brief
   và workbook. Backend PR phải cung cấp contracts trước consumer nếu tách PR.

Không staging/commit/push/merge trong task này. Root architecture/Office files và
helper ngoài scope được giữ. Các file dirty ban đầu được snapshot để so sánh; các
thay đổi ngoài task không bị hoàn tác. Source artifacts/ledger/keys/preview/build
không đưa vào deliverable source hoặc PR.

Đợt tiếp theo: 3.31 additive auth migration → 3.32 password/session/CSRF → 3.33
verification/SMTP → 3.34 recovery và app shell. API brief đã có, phần browser demo
còn pending không buộc dừng các đầu việc auth độc lập.
