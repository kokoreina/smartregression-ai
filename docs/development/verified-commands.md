# Lệnh đã đối chiếu với repository

Đối chiếu ngày 2026-10-06. Cwd của mọi lệnh dưới đây là **root monorepo** chứa
pyproject.toml và frontend/, hiện là D:\smart-regression-ai. Hai mức bằng chứng:

- **Định nghĩa xác minh:** command/script/entrypoint tồn tại trong manifest, script,
  CLI hoặc CI; không đồng nghĩa đã chạy thành công.
- **Kết quả quan sát:** lệnh đã chạy có evidence, ghi môi trường và giới hạn. Kết quả
  từ review trước dẫn [verification](verification.md); không phải chạy lại trong task Markdown.

Không có frontend test/e2e script, runner command, LLM benchmark command hoặc migration
command đã được xác minh; không dùng tên lệnh phỏng đoán cho các module đó.

**Bổ sung 2026-10-24:** đã có command cho **fixture-only G1** trong
[harness README](../../scripts/g1/README.md); đây là spike tách khỏi production runner.
Các kết quả lịch sử bên dưới giữ nguyên. Evidence mới và exact commands nằm ở
[handoff tích hợp](../research/sprint-1/implementation-handoff-20261024.md).

## Runtime và nguồn

[pyproject](../../pyproject.toml) yêu cầu Python >=3.14,<3.15;
[package](../../frontend/package.json) yêu cầu Node >=22.14,<23, npm >=10.
[CI](../../.github/workflows/ci.yml) chọn Python 3.14, Node 22.14.0, uv 0.12.23.
Tool local đã quan sát: Python 3.14.3, Node 22.14.0, npm 10.9.2, uv 0.12.23.
Phiên bản dependency cụ thể lấy từ [uv.lock](../../uv.lock) và
[package-lock](../../frontend/package-lock.json), không chép phiên bản vào nhiều hướng dẫn.

`uv` chưa có trong PATH máy bootstrap: review dùng `.tools/bin/uv.exe` hoặc binary
trong `.venv/Scripts`. Thành viên cài uv theo [setup](setup.md), không phụ thuộc .tools.
`uv run` có thể sync/build package trước khi chạy; chạy executable sẵn có thành công
không chứng minh một clean `uv sync` sẽ thành công offline.

## Setup và chạy

| Lệnh chuẩn | Định nghĩa đã đối chiếu | Kết quả/giới hạn đã quan sát |
| --- | --- | --- |
| `uv sync --locked` | pyproject/uv.lock, CI | Dependencies từng được cài bằng uv; chưa xác nhận setup sạch mới; offline thiếu hatchling ở lần review |
| `npm --prefix frontend ci` | package/lock, CI | Dry-run offline đã pass; chưa coi là clean install/scripts pass |
| `uv run uvicorn smartregression.api.main:app --reload --host 127.0.0.1 --port 8000` | api/main.py, Uvicorn dependency, setup | Uvicorn live health đã pass bằng Python module không reload; chưa xác nhận --reload trong mọi client |
| `npm --prefix frontend run dev` | script dev = Vite bind loopback | Review trước bị EPERM; lần mở web sau đã khởi động Vite bằng node entrypoint, HTTP hiện trả 200; chưa coi là browser e2e |
| `uv run smartregression --help` | project.scripts → cli/main.py | CLI executable/module đã chạy --help thành công trong review |
| `uv run smartregression validate-report examples/reports/demo.json` | CLI subcommand/fixture, CI | Executable/module đã trả exit 0 và nhãn DEMO; invalid/missing file smoke riêng trả 1/2 |

PowerShell dùng `npm.cmd` thay `npm` nếu execution policy chặn npm.ps1; không cần
thay policy toàn máy. Cài lần đầu cần network/dependency access hợp lệ, không tắt sandbox.

## Checks và tái sinh contract

| Lệnh chuẩn | Nguồn xác minh | Kết quả review trước / giới hạn |
| --- | --- | --- |
| `uv run ruff check .` | pyproject Ruff/dev deps, CI | .venv Ruff đã PASS |
| `uv run ruff format --check .` | Ruff formatter, CI | .venv Ruff đã PASS |
| `uv run pytest` | pyproject testpaths, backend/tests, CI | .venv Python pytest: 14 pass, 2 setup errors quyền thư mục tạm; full suite chưa pass |
| `uv run python scripts/export_contracts.py --check` | exporter argparse, CI | .venv Python đã PASS; kiểm cả fixture demo |
| `uv run python scripts/export_contracts.py` | exporter write mode | Đã sinh OpenAPI; chỉ chạy khi cần cập nhật nguồn chuẩn, không dùng thay --check trong CI |
| `npm --prefix frontend run contracts:generate` | package + frontend/scripts/contracts.mjs | Đã sinh types bằng openapi-typescript, không sửa tay |
| `npm --prefix frontend run contracts:check` | package + generator --check, CI | PASS; option defaultNonNullable=false giữ optional fields đúng schema |
| `npm --prefix frontend run lint` | package + eslint.config.js, CI | PASS |
| `npm --prefix frontend run typecheck` | package + tsconfig strict, CI | PASS |
| `npm --prefix frontend run build` | package: tsc --noEmit rồi vite build, CI | Bị spawn EPERM ở esbuild trong review; build chưa được xác nhận sau khi dev chạy |
| `uv lock --check --offline --cache-dir .uv-cache` | uv CLI, manifest/lock | .tools uv đã PASS; không chứng minh cache có đủ packages để sync |

Đổi contract: export rồi generate, sau đó chạy cả hai check và consumer tests. Đổi
fixture cũng phải validate backend; `npm run build` riêng không chạy Pydantic.
Chọn subset pytest theo module khi debug, nhưng không thay full suite của CI bằng
subset rồi tuyên bố tất cả pass. Xem [Testing](../rules/06-testing-quality.md).

## HTTP smoke trong task tài liệu

Dev servers từ yêu cầu mở web trước vẫn chạy, không được khởi động lại hoặc đổi cấu
hình trong task này. Các lệnh PowerShell read-only đã chạy:

```powershell
Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing
Invoke-RestMethod 'http://127.0.0.1:5173/api/health'
```

Kết quả: UI HTTP 200; health có schema_version=1.0.0, status=ok,
service=smartregression-api, scope=service_only. Đây là HTTP/proxy smoke, không xác
nhận browser rendering, full build, LLM, storage hay runner readiness.

## Giới hạn và cập nhật

Không chạy product suite lại cho đợt chỉ sửa Markdown. GitHub CI, Linux/macOS,
browser e2e, required checks/branch protection và setup sạch vẫn chưa xác minh.
Không có .git nên không có git diff/index/history đáng tin để báo; task docs dùng
hash snapshot trước/sau để kiểm source/manifests/CI không đổi.

Khi thêm script, cập nhật bảng từ implementation thật và ghi kết quả riêng. Gate
planned ở [enforcement](../rules/14-enforcement.md), không invent command ở đây.
