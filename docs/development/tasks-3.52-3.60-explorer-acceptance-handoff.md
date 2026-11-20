# Hà An — task 3.52–3.60, bàn giao kiểm chứng

Cập nhật 20/11/2026. Nhánh `feat/an-task-3.46-ownership`, baseline của đợt này
`dddaee6`. Đây là kiểm chứng và sửa các khoảng trống của implementation hiện có,
không phải tuyên bố toàn bộ tính năng được viết mới trong đợt này.

## Đầu ra và phạm vi

| Task | Đầu ra kiểm chứng/sửa | Bằng chứng có thể chạy lại |
| --- | --- | --- |
| 3.52 A/B | Cùng repo/base/config/type; hypothesis không có measured delta; không chọn phương án an toàn theo count | `test_scenarios_unit.py`; native `test_remaining.py`: equal alternatives, sai baseline/type/project/owner; proof bị xóa giữ SHA base |
| 3.53 Comparison UI | Xóa kết quả cũ khi bắt đầu so sánh mới; chỉ hiện summary/delta sau khi đọc được cả hai graph; node chỉ có ở A giữ nhãn overlay A | `comparison-acceptance.spec.mjs`: lỗi đổi mode, hai panel/base-target, provenance của overlay bị bỏ, deleted evidence, graph đọc lỗi không để lại success |
| 3.54 Guides/search/AI | Guide/search tĩnh chọn đúng file/SHA; consent metadata riêng với excerpt; quota error giữ kết quả tĩnh; text không thực thi HTML | `project-workspace.spec.mjs`: keyboard citation, no-match, consent, lỗi quota/no-retry, hostile text và citation sai SHA; `test_assistance.py` |
| 3.55 Notes/pins/resume | Lưu note theo owner/SHA, optimistic version, stale path rõ; resume debounce 1 giây, URL trực tiếp ưu tiên; không autosave AI draft | Native notes/version/owner tests; browser resume/escaping; real browser note → restart → đăng nhập lại → mở lại |
| 3.56 Hotspots | Hiện số file của toàn snapshot và SHA; bấm cycle/hub bật focus vào file; không đổi mẫu số theo viewport | `test_explorer_graph.py`; browser cycle fixture + scope giữ 2 file; unknown không ghi thành 0 |
| 3.57 Print/PDF | A4 ngang, bảng run và usage tải hết các trang của snapshot, bỏ sidebar và trang trắng thừa; giữ filter/time/limitations | `print-acceptance.spec.mjs` với 105 run và 126 usage; `verify_print_pdf.py`; PDF real-browser từ API/DB thật và PDF fixture nhiều trang |
| 3.58 Security | Owner cho snapshot/source/notes/view-state/run/report/download; CSRF; XSS/CSV escaping và nguồn nhập không được chạy | Native auth/explorer/notes/scenario/reporting; hai account qua browser; targeted auth/export tests và các fixture hostile |
| 3.59 Durable workflow | Browser gọi product HTTP/API/PostgreSQL thật: signup, verify, login, project, snapshot, note, run, JSON/CSV/PDF, restart/reopen, mobile/keyboard | `native_reporting/test_browser.py` + `scripts/e2e-an-remaining.mjs`; không `page.route` data endpoints; count dashboard khớp CSV; theo dõi đúng POST run và hai endpoint AI để phát hiện gọi lại khi reopen |
| 3.60 Coverage/handoff | Ma trận này, plan, commands và giới hạn để người khác review | **Ready for review sau checks; chưa phải quyết định nghiệm thu độc lập** |

Các sửa production của đợt này giới hạn ở `Scenarios.tsx`, `Explorer.tsx`,
`Dashboard.tsx`, `styles.css`, `dashboard.css`. Không đổi API/schema, generated types, lockfile,
provider hoặc database migration.

## Các lỗi đã tái hiện trước khi sửa

- So sánh phiên bản thất bại vẫn giữ heading A/B thành công cũ. Summary/delta được
  công bố trước khi graph tải xong cũng có thể gây hiểu nhầm. Đã xóa kết quả cũ và
  chỉ công bố kết quả hoàn chỉnh sau các read cần thiết.
- Hotspot không ghi scope và bấm cycle chưa bật focus. Đã hiện full-snapshot file
  count/SHA và đưa graph vào focus khi chọn hotspot.
- Báo cáo thật trên màn hình 390px tràn ngang bởi evidence ID dài. Đã cho ID xuống
  dòng trong flex container, vẫn giữ nguyên ID và khả năng đọc bằng chứng.
- PDF 105 dòng có trang trắng cuối do min-height/border của workspace màn hình
  tiếp tục được in. Reset các thuộc tính này riêng trong print; PDF kiểm cuối
  gồm 105 run và 126 usage trên 20 trang A4 ngang, đủ dòng cuối và không có trang rỗng.
- Rà soát độc lập phát hiện nhãn evidence của node overlay chỉ có ở phương án A
  bị gọi là base; đã dùng `source_kind` để hiển thị nguồn đúng. Bản in usage trước
  chỉ lấy 25 dòng đầu; đã tải tiếp từ frozen snapshot trước khi in. Bộ đếm API
  khi mở lại trước đó bỏ sót endpoint AI thực; đã sửa để kiểm tra đúng URL.

## Chạy lại kiểm tra

Từ repo root, PowerShell; Python trong `.venv`, Node 22 theo manifest:

```powershell
$env:PYTHONPATH = 'backend/src'
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_scenarios_unit.py backend/tests/unit/test_explorer_graph.py backend/tests/unit/test_assistance.py backend/tests/unit/test_repository_export.py backend/tests/unit/test_auth_security.py -q
.venv/Scripts/ruff.exe check backend/tests/integration/native_reporting backend/tests/unit/test_scenarios_unit.py scripts/qa/verify_print_pdf.py
.venv/Scripts/python.exe scripts/export_contracts.py --check

# Opt-in: cluster riêng, không dùng URL hoặc DB account đang chạy.
$env:SMARTREGRESSION_NATIVE_PG_BIN = 'C:/Program Files/PostgreSQL/18/bin'
$env:SMARTREGRESSION_TEST_NODE = 'C:/path/to/node-v22/node.exe'
.venv/Scripts/python.exe -m pytest backend/tests/integration/native_reporting -q --tb=short
Remove-Item Env:SMARTREGRESSION_NATIVE_PG_BIN
Remove-Item Env:SMARTREGRESSION_TEST_NODE
.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short
```

Tại `frontend`:

```powershell
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node node_modules/@playwright/test/cli.js test --config playwright.config.mjs
node scripts/contracts.mjs --check
npm run test:reports
npm run test:auth
```

QA PDF tùy chọn: cài PyMuPDF trong môi trường QA riêng rồi chạy
`python scripts/qa/verify_print_pdf.py <dashboard-105-rows-a4.pdf> --expected-runs 105 --expected-usage 126`.
Không thêm thư viện QA này vào dependency của ứng dụng.

Evidence local ở ignored `var/tasks-352-360/`: logs, `browser-*/result.json`,
JSON/CSV/PDF và screenshot. Token verify synthetic được xóa sau campaign. Không
commit credential, database, browser session hay runtime artifacts.

## Kết quả và giới hạn

- Targeted backend: **42 passed**. Browser suite: **65 passed**.
- Native SQL/HTTP/browser: **19 passed** ở lượt đầy đủ; luồng browser riêng
  chạy lại sau sửa bộ đếm POST: **1 passed**. Full backend: **1559 passed,
  191 skipped** ở lượt trước;
  các sửa sau lượt đó chỉ ở frontend và script QA.
- Typecheck, build, generated contract checks, scoped ESLint/Ruff đã chạy qua.
  Build còn cảnh báo bundle trên 500 KiB; không coi là build failure.
- Report validator **88**, SSR report **11**, repository consumer **60**, auth
  transport/SSR **20** checks đã qua. SSR không thay kiểm tra browser.
- PDF QA dùng Chromium thật, đọc text và render bằng PyMuPDF; kiểm 105 run và 126 usage,
  timezone, tiếng Việt, landscape và trang trắng; không phải PDF server.
  Fixture 20 trang và PDF từ DB thật 3 trang, đều không có trang trắng.

Native PostgreSQL 18 bổ sung bằng chứng local; không thay Docker PostgreSQL 17
hoặc staging. GitHub là transport fixture, email là captured synthetic mailbox,
không xác nhận Gmail/public SMTP delivery. Auth/session, SQL, HTTP, parser,
publication và browser là thật. Không dùng database của người dùng. Có restart
HTTP backend và dựng lại app cùng database; không tuyên bố đây là thử nghiệm
khởi động lại máy hoặc phục hồi hạ tầng production.

Không gọi Gemini trả phí trong campaign. Consent/quota/error/citation có fixture
và test application; không suy từ đó rằng mọi câu trả lời live model đều chính
xác. Phân tích tĩnh không chạy code repo đầu vào hoặc regression tests.

Reviewer/người nghiệm thu độc lập của nhóm còn phải đưa quyết định thực tế.
Review tự động chỉ hỗ trợ phát hiện lỗi, không thay leader approve. Không tự sửa
workbook thành Accepted, tạo PR, merge main hoặc deploy.

AI disclosure: Codex hỗ trợ audit code, viết regression tests, sửa lỗi và soạn
bàn giao. Người nộp cần đọc/hiểu các thay đổi và tự giải thích được luồng xử lý;
không ghi tỷ lệ đóng góp hoặc chữ ký phê duyệt không có bằng chứng.
