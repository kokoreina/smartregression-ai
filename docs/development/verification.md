# Review bootstrap — 2026-10-06

Review trực tiếp source, contract, tài liệu, dependency manifests/lockfiles và CI.
Không dựa vào báo cáo hoàn thành cũ. Môi trường: Windows PowerShell, Python 3.14.3,
Node 22.14.0, npm 10.9.2; uv 0.12.23 cục bộ. Không có .git hoặc docs/proposal.
Không commit/push/deploy, không thêm stack hoặc thuật toán AI.

## Vấn đề theo mức độ

### P1 — Types không khớp optional/default của backend (đã sửa)

frontend/scripts/contracts.mjs gọi openapi-typescript với mặc định defaultNonNullable.
Kết quả generated.ts bắt buộc nested schema_version và các trường có default dù
OpenAPI không liệt kê chúng trong required. Fixture Pydantic chấp nhận nhưng
frontend/src/features/reports/demo.ts bị TS2352, làm typecheck/build thất bại.
Đặt defaultNonNullable=false và sinh lại types bằng công cụ; typecheck và drift
check pass. Không thêm bộ contract thủ công hoặc ép kiểu qua unknown.

### P2 — Chưa có bằng chứng chạy toàn bộ từ đầu đến cuối (còn mở)

Vite dev/build không khởi tạo được esbuild trong sandbox: spawn EPERM. Pytest có
14 test pass, 2 test lỗi ở setup tmp_path do PermissionError, kể cả khi basetemp ở
workspace. Không khẳng định dashboard đã chạy trên browser hoặc full suite pass.
Đã kiểm tra riêng CLI với file trong var/ và xác nhận exit codes 0/1/2.

Không có Git metadata/remote nên chưa xác minh tracked files hoặc run GitHub Actions.
CI có steps thực, không echo placeholder, nhưng chưa có run chứng minh xanh.
uv lock --check --offline pass; thử sync offline sau thay đổi pyproject bị thiếu
hatchling trong cache. Cần xác nhận setup sạch có mạng trên máy thành viên/CI.

### P2 — Runner contract chưa đủ để triển khai độc lập (giữ pending)

core/execution/ports.py chỉ mô tả một Protocol trả list ExecutionResult.
Không có timeout/cancellation, transport, job ID hay biểu diễn suite-level failure.
Đã làm rõ target commit, repository identity, ID đã validate và ranh giới worker
trong docstring. Không tự thiết kế hệ thống job/worker mới. Trước task runner thật,
nhóm phải chốt các quyết định trên cùng policy cách ly và framework MVP bằng ADR.
Hiện đủ chia vùng trách nhiệm và làm spike, chưa đủ giao 5 người viết module tích
hợp hoàn toàn độc lập mà không thống nhất input/output với nhau.

### P3 — Vệ sinh kiểm tra và tài liệu (đã sửa)

- Ruff không nhận diện src-layout tường minh và vẫn có thể quét runtime/temp artifacts
  khi workspace chưa git init. Thêm src và exclude var/pytest-cache-files-*; chuẩn hóa
  import bằng Ruff. Đã check lại root không còn lỗi.
- .gitignore thiếu thư mục tạm pytest-cache-files-* sinh bởi lần test lỗi; đã bổ sung.
- Làm rõ ignore dist/node_modules trong ESLint, không đổi rule kiểm tra source.
- README liên kết verification.md chưa tồn tại; đã tạo tài liệu này.
- Architecture nói fixture validate trước build nhưng npm build riêng chỉ chạy
  TypeScript/Vite; đã ghi chính xác validation nằm trong CI/exporter/CLI.
- Health client không kiểm tra schema_version; đã thêm kiểm tra trước khi báo kết nối.
- Generated types sinh lại theo contract; không sửa tay generated artifact.

### P3 — Cảnh báo dependency (còn mở, không tự nâng stack)

Starlette TestClient cảnh báo dùng httpx đã deprecated; tests vẫn chạy. Lần npm install
trước review báo ESLint 9 hết hỗ trợ. Chưa đổi dependency trong review; nhóm nên tạo
task cập nhật tương thích, review lockfiles và chạy lại CI thay vì nâng major không kiểm chứng.

## Đối chiếu 10 mục

| Mục | Kết luận từ source/thực nghiệm |
| --- | --- |
| 1. Setup | Root pyproject, src package, CLI entrypoint và frontend prefix khớp tài liệu; Python 3.14.x/Node 22.x được ghi đúng; uv cần cài riêng |
| 2. Chạy ứng dụng | Uvicorn live health và CLI pass; frontend typecheck pass, dev/build bị EPERM; chưa kiểm tra browser |
| 3. Dependency core | Core chỉ có runner Protocol import typing/contracts; không API/SDK provider; Pydantic nằm ở contracts |
| 4. Contract | Backend là nguồn chuẩn, exporter và openapi-typescript có drift checks; optional/default mismatch đã sửa; validators liên trường chỉ ở backend |
| 5. Demo | Fixture data_kind=demo, analysis_status=not_implemented, execution_status=not_run; loader từ chối data_kind khác; UI có nhãn DEMO rõ |
| 6. Thành công/metric giả | Không endpoint analyze; health scope=service_only; costs/durations null; không fault_detected từ test fail |
| 7. CI | Có uv sync locked, Ruff lint/format, pytest, CLI, npm ci, schema/types drift, lint/typecheck/build; không continue-on-error; chưa chạy trên GitHub |
| 8. Git/secrets/artifacts | Không có .git nên không thể audit index/history. Không thấy secret trong source/docs/fixture được xem và scan pattern phổ biến; .env.example chỉ placeholder. Runtime bị ignore; OpenAPI/types/lockfiles phải version control có chủ đích |
| 9. Thừa phạm vi | Không DB/vector DB/provider SDK, runner thật hoặc lớp rỗng hàng loạt. README-only module giữ pending hợp lý. Một số dependency dev có cảnh báo cần theo dõi |
| 10. Chia việc | module-ownership có 5 vùng và backlog có đầu ra/acceptance criteria; chưa gán tên. Cần chốt framework, interface đầu vào và runner trước implementation tương ứng |

## Kết quả kiểm chứng thực tế

Lệnh Python dùng .venv/Scripts hoặc .tools/bin/uv.exe vì uv chưa có trên PATH của
máy này. Đây là executables đã cài trước review, không phải setup sạch mới.

| Kiểm tra | Kết quả |
| --- | --- |
| Ruff check . / format --check . | PASS sau sửa exclude và src-layout |
| python scripts/export_contracts.py --check | PASS, bao gồm validate fixture DEMO |
| uv lock --check --offline --cache-dir .uv-cache | PASS, manifest/lockfile khớp |
| npm --prefix frontend ci --dry-run --ignore-scripts --offline --cache D:\smart-regression-ai\.npm-cache | PASS dry-run; không chứng minh clean install hoặc lifecycle scripts |
| npm --prefix frontend run lint | PASS |
| npm --prefix frontend run typecheck | PASS sau sửa types |
| npm --prefix frontend run contracts:check | PASS |
| pytest đầy đủ | 14 pass, 2 setup errors do quyền tmp_path; không pass toàn bộ |
| pytest -p no:cacheprovider -k 'not rejects_invalid_report and not reports_unreadable_file' | 14 pass, 2 deselected; một deprecation warning |
| CLI --help / validate report hợp lệ | PASS |
| CLI smoke riêng: hợp lệ / sai contract / file không tồn tại | PASS exit 0 / 1 / 2; không echo private_source trong stderr |
| Live Uvicorn GET /health trên loopback | PASS; tiến trình đã dừng sau kiểm tra |
| npm --prefix frontend run dev / run build | FAIL môi trường spawn EPERM ở esbuild; chưa xác minh runtime/bundle |
| uv sync --locked --offline --cache-dir .uv-cache | Không hoàn tất: thiếu hatchling trong cache; setup chuẩn cần mạng |
| Git status / tracked secrets audit | Không chạy được: chưa là Git repository |
| GitHub Actions, Linux/macOS, browser UI | Chưa chạy |

Hệ thống duyệt tự động không xét được yêu cầu chạy pytest ngoài sandbox do giới hạn
sử dụng; lệnh escalation chưa được thực thi. Đây là lỗi duyệt, không phải kết luận
hành động không an toàn. Không hạ hoặc bỏ tests CI để che hạn chế của môi trường.

## Điều kiện trước sprint đầu tiên

1. Một thành viên chạy setup sạch có mạng và toàn bộ checks bên dưới; smoke dashboard
   với API bật/tắt, xác nhận DEMO/commit/evidence/selected/skipped và loading/error.
2. Maintainer khởi tạo/kết nối Git theo quy trình nhóm; review staged files, giữ runtime
   artifacts/credentials ngoài Git; chạy workflow trên một PR và xác nhận CI xanh.
3. Nhóm gán người thực hiện/reviewer cho 5 vùng, chốt acceptance criteria task nhỏ.
4. Technical spike chốt một ngôn ngữ/framework MVP; thống nhất test inventory,
   evidence provenance và fallback policy trước nối các module thật.
5. Chốt runner/evaluation contracts trước task execution; DB/provider vẫn pending
   đến khi có use case và chính sách dữ liệu. Không cần viết lại kiến trúc bootstrap.

```sh
uv sync --locked
npm --prefix frontend ci
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run smartregression validate-report examples/reports/demo.json
uv run python scripts/export_contracts.py --check
npm --prefix frontend run contracts:check
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```
