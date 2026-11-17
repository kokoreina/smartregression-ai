# Sprint 3 đợt 2 — Bàn giao tài khoản và app shell

Ngày 15/11/2026, UTC+7. Huy thực hiện theo phạm vi nhóm đã bàn giao, coding agent hỗ
trợ implementation/tests/tài liệu. Self-verification, chưa có independent review,
commit/push/PR/merge hoặc public deployment trong task này.

## 1. Trạng thái và baseline

Worktree `D:/smart-regression-ai/var/main-preview`, branch
`feat/web-repository-analysis`, HEAD baseline `5a30a7ac5a1e2ad87a45120fe7c043bae49be5d4`
cùng local changes đợt 1/2. Fetch thực tế đợt 2 xác nhận origin/main vẫn cùng SHA;
main chưa có local auth này. Các file dirty được snapshot vào ignored `var/phase2/before` trước
khi thay đổi; root database/Office files khác không bị sửa.

**Có implementation local** cho auth, PostgreSQL migration và app shell. **Chưa
nghiệm thu toàn bộ đợt 2**: Huy đã xác nhận nhận thư và xác thực Gmail thành công;
server ghi verify 200 và verified=True. Server cũng ghi reset-password 200. Huy xác
nhận nhận email recovery, đăng nhập bằng mật khẩu mới, sửa tên, đổi mật khẩu, đăng
nhập lại và đăng xuất đều thành công. Các kiểm tra browser còn lại chưa nghiệm thu;
HTTPS staging thuộc đợt 3. Không đánh feature Done bằng SSR/mock.

Thiết kế, dữ liệu, wireframes và semantics:
[auth design](sprint-3-auth-design.md). Nguồn task hiện hành:
[audit 75 task](sprint-3-phase-1-audit.md). Brief dự án/ownership ở đợt 3 vẫn giữ
trong [web contracts](sprint-3-web-contracts.md).

## 2. Thay đổi và contract impact

- Migration additive `20261115_07`: web_users/sessions/account_tokens/rate_limits,
  frozen DDL, drift metadata và upgrade tests. Dữ liệu nghiên cứu giữ nguyên.
- Auth application + bound PostgreSQL adapter, Argon2id, hashed session/token,
  transactional revoke/consume, atomic throttling và khóa user cho login/reset/disable.
- `/api/v1/auth/*` theo brief, cùng safe capability `/api/v1/capabilities`.
  Backend models → exporter → generated TS; không sửa generated bằng tay.
- Signed CSRF + exact Origin + session rotation; cookie dev/production riêng;
  generic validation/errors, no-store, safe DB failures và SMTP diagnostics.
- Gmail STARTTLS adapter, không auto retry, link fragment không consume bằng GET.
  Password/token không vào log. Phản hồi 202 chỉ là nhận yêu cầu, không xác nhận mail đến.
- Operator `smartregression disable-account --user-id UUID`, không public admin API.
- React Router, protected shell, auth/account views, form/double-submit guards,
  dialog logout, keyboard semantics, reduced-motion và sidebar responsive.
- Vite giữ `/api/v1`, rewrite legacy paths riêng. Product mode không mount demo
  POSTs; local demo `/demo` vẫn mở saved report không cần session. No project CRUD,
  personal history hoặc account AI calls được dựng giả.
- Dependencies sinh bằng uv/npm: pwdlib/Argon2, email-validator, React Router.
  Existing Python lock versions giữ nguyên; 5 transitive/direct packages bổ sung.
  Zod dev dependency đã vá tương thích; npm còn cảnh báo moderate ở chuỗi ESLint/
  minimatch. Không ép downgrade/upgrade major công cụ để làm audit bằng 0.

## 3. Cách chạy local và cấu hình riêng

Auth development dùng container riêng do `scripts/auth/prepare_local.py` tạo,
bind loopback và runtime DB user không có DDL. Không tái sử dụng hoặc migrate
database gốc. Container có nhãn `smartregression.auth-local`; định danh nằm trong
ignored `var/auth/local-context.json`. Không xóa tùy tiện container khác.

```powershell
# Chỉ lần đầu; tạo DB riêng + migration và cấu hình, không in secrets:
$env:PYTHONPATH='backend/src'
.venv/Scripts/python.exe scripts/auth/prepare_local.py

# Điền SMTP_USERNAME/SMTP_PASSWORD riêng trong var/auth/web.env.
# Gmail phải bật 2-step verification; dùng App Password 16 ký tự.
$env:SMARTREGRESSION_WEB_ENV_FILE='D:/smart-regression-ai/var/main-preview/var/auth/web.env'
$env:SMARTREGRESSION_WEB_MODE='local-demo'
.venv/Scripts/python.exe -m uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers

# Terminal khác, cùng worktree:
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Mở `/login`, `/register` hoặc `/demo` tại `http://127.0.0.1:5173`. Khi sửa env phải
restart đúng backend process; không kill Python/Node khác. Ctrl+C ở terminal sở
hữu để dừng. Database container được giữ cho local; dùng định danh đã kiểm tra
trong context khi stop/start. Dữ liệu auth tồn tại qua restart; không cam kết giữ
dữ liệu sau khi xóa container. Backup production/local release ở đợt 3.

Mẫu không secret: `config/web-auth.env.example`. Không gửi `.env`, database DSN,
SMTP App Password hoặc CSRF secret vào Git/chat/screenshots. Thư viện cấu hình
không đọc file hoặc kết nối mạng lúc import/export OpenAPI. Runtime dùng
`SMARTREGRESSION_DATABASE_URL`; migration credentials riêng, không fallback.

Product mode dùng `SMARTREGRESSION_WEB_MODE=product`, origin HTTPS/cookie secure,
không bật AUTH_LOCAL_HTTP. Không public deployment này trước các gate đợt 3.

## 4. Kiểm chứng và giới hạn

Các lệnh đã chạy từ worktree; portable Git được prepend vào PATH cho tests có Git:

```powershell
$env:PYTHONPATH='backend/src'
$env:PATH='D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd;' + $env:PATH
.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp var/phase2/full-release-check --junitxml var/phase2/full-release-check.xml
.venv/Scripts/python.exe scripts/storage/run_checks.py
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/python.exe scripts/export_contracts.py --check
npm --prefix frontend run contracts:check
npm --prefix frontend run test:auth
npm --prefix frontend run lint
npm --prefix frontend run build
D:/smart-regression-ai/.tools/bin/uv.exe lock --check --offline
git diff --check
```

| Check | Kết quả thực tế / giới hạn |
| --- | --- |
| First PostgreSQL harness, thiếu portable Git | 111 pass, 4 skip, 7 fail/20 error ở Git fixtures; không coi pass toàn suite |
| PostgreSQL harness sau sửa PATH | 138 pass, 4 skip; exit 0, gồm auth/migration và restart/restore; artifact `var/storage-verification-e9a1aa79654e4ebc828659757ba2384b/evidence.json` |
| Targeted backend lần đầu đúng môi trường | 220 pass, 1 fail: expected OpenAPI route set chưa tính auth; đã cập nhật expected paths đầy đủ, focused test pass |
| Full default backend cuối | **1065 passed / 147 skipped**, exit 0, 699,32s; artifact `var/phase2/full-release-check.xml` |
| Default backend trước cập nhật schema assertions | 1063 pass / 147 skip / 2 fail ở expected table/head cũ; đã sửa expectations và FK RESTRICT, focused schema tests 2 pass; full rerun cuối đã pass |
| PostgreSQL cuối sau FK alignment, revoke/login race và throttle | **142 passed, 4 skipped**, exit 0, 276,85s; `var/storage-verification-29664d963a0c41a0a60fdc0432e640b3/evidence.json`, gồm restart/restore |
| Frontend consumer/report checks | 88 validation + 11 report SSR + 60 repository checks pass |
| Frontend auth | **20 SSR/transport checks pass**; regression sai mật khẩu hiện tại không xóa session, fail trước rồi pass sau sửa; không phải browser |
| Frontend lint/build | Pass trên bản đã chạy; kiểm tra lại nếu có source change sau đó |
| Ruff / exporter / uv lock | Pass; final diff/integrity được ghi khi bàn giao |
| Live Vite regression | Runtime dependencies còn tải HTTP 200 sau cả 3 SSR suites; không phải browser acceptance |
| Design-token contrast | 5 cặp chữ/nền chính >=4.5:1 theo sRGB calculation; không phải chứng nhận rendered WCAG |
| Actual HTTP qua Vite + DB dev | Login/me/logout pass, logout session cũ 401; `var/phase2/live-account-check.json` |
| Gmail và account UI local | Initial register 202 có delivery failure vì credential chưa đúng; sau Huy sửa, **SMTP TLS/login accepted**. Huy xác nhận verify thành công; server verify 200 và verified=True. Server reset 200; Huy xác nhận nhận email recovery, login mới, sửa tên, đổi mật khẩu, login lại và logout thành công. Đây là quan sát thủ công của Huy, không phải browser automation |
| Browser | Browser host unavailable; Windows tool dừng vì không xác minh được URL allowed; chưa nghiệm thu interaction/viewport |

Bốn PostgreSQL skip thuộc các ca inventory/candidate CLI cần harness riêng, không
phải skip auth để che lỗi. Default backend skip DB vì harness riêng là thiết kế
hiện có. Lượt sandbox khác từng lỗi pytest/Git WinError 5; được phân biệt với code
fail. SSR harness auth ban đầu lỗi nạp CJS router, đã sửa harness; consumer checks
cũ vẫn giữ cache riêng, không reset cache web để che trang trắng.

Không có Gemini generation mới; ledger đợt trước giữ nguyên 5/5, không reset/increase.
Live scripts auth chỉ dùng Gmail đã cấu hình, không gọi GitHub hoặc provider LLM.
Không lưu mật khẩu test trong handoff/artifact. File mật khẩu smoke tạm ban đầu
đã xóa; smoke helper hiện chỉ giữ mật khẩu ngẫu nhiên trong memory.

Excel gốc và bản review worktree đã cập nhật 7 task liên quan: tổng **3 Done /
32 Ongoing / 40 Not started**. Done chỉ cho khảo sát/thiết kế 3.01/3.31/3.61;
3.32/3.33/3.34/3.62/3.63 vẫn Ongoing theo gates. Artifact-tool author/recalculate/
render được dùng, kiểm tra ảnh auth/UI/evidence/baseline; chỉ 2 sheet XML đổi,
68 package parts khác byte-identical, formulas/layout/validation/actual hours giữ
nguyên. Workbook chưa native Excel recalc; không suy actual hours từ Done.
SHA256 final `6867eab6890e37a0f3f73bb9541229cdb13dcfc0cb9de6576360974beb44f721`.

Migration auth mới đang local chưa publish; trong vòng test đã làm rõ hai FK
ON UPDATE RESTRICT. DB dev riêng đã backup `var/auth/before-fk-alignment.dump`
trước khi đồng bộ constraints, không đổi account/history hoặc DB gốc. Các revision
đã có trên main không bị sửa.

## 5. Checklist Gmail/browser còn lại

| Case | Cần quan sát | Trạng thái |
| --- | --- | --- |
| A01 | Gmail App Password hợp lệ; SMTP TLS/login được chấp nhận | Pass qua SMTP diagnostic; không chứng minh inbox delivery |
| A02 | Nhận email verify thật, mở link → URL fragment bị xóa, chưa verified trước click xác nhận | Huy xác nhận verify thành công từ email; chưa quan sát riêng fragment và trạng thái trước click |
| A03 | Xác nhận verify → backend verified, login vào account | Đạt theo xác nhận thủ công của Huy; server verify 200/verified=True |
| A04 | Forgot → nhận mail reset → đặt password mới → login cũ fail, login mới pass | Server reset-password 200; Huy xác nhận nhận mail, login mới, sửa tên, đổi mật khẩu, login lại/logout thành công. Login bằng mật khẩu cũ chưa được quan sát riêng trên browser; backend có tests |
| A05 | Hai phiên/browser; đổi/reset/disable làm phiên cũ hết hiệu lực trên UI | Chưa kiểm chứng browser; backend đã có tests |
| A06 | Reload/deep link/back/forward, CSRF retry thủ công, mạng lỗi không gửi POST trùng | Chưa kiểm chứng browser |
| A07 | Keyboard, dialog cancel/Escape/return focus, form errors, 390/768/1440px + 200% | Chưa kiểm chứng |
| A08 | `/demo` tree/static/export/import; saved report không gọi AI; backend offline vẫn đọc file | Chưa kiểm chứng browser đợt 2 |

SMTP tự kiểm tra: `scripts/auth/smoke_local.py --action smtp-check`; gửi lại verify
bằng `--action resend`, recovery bằng `--action request-reset` (explicit email gửi
về sender). `--action check` kiểm account state server, không chứng minh inbox hoặc
browser. Huy có thể dùng UI forgot để chọn mật khẩu riêng cho tài khoản smoke.
Không lấy token từ DB/API/log thay cho luồng email thật.

Trạng thái task tuân AC: 3.31/3.61 chỉ đạt đầu ra thiết kế khi tài liệu/migration
đủ; auth/UI tasks vẫn Ongoing khi checklist browser đầy đủ chưa xong; 3.63 còn projects
ở đợt 3. Không cập nhật actual effort bằng estimate. Bước tiếp theo: xử lý gate
email/browser, rồi bắt đầu owner-scoped projects và durable history ở đợt 3.
