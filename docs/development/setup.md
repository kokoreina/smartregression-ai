# Cài đặt và chạy

Chạy lệnh ở root của monorepo. Baseline đã kiểm tra môi trường: Windows PowerShell,
Python **3.14.3**, Node **22.14.0**, npm **10.9.2**. Project giới hạn Python 3.14.x
và Node 22.x >=22.14 để tránh mở rộng runtime chưa kiểm chứng. uv được cài cục bộ
trong `.tools` trên máy bootstrap, không đưa vào Git; các thành viên cài uv riêng.

Vite 7 yêu cầu Node ^20.19 hoặc >=22.12; baseline trên đáp ứng yêu cầu
([Vite](https://vite.dev/guide/)). Phiên bản package thực nằm trong uv.lock và
frontend/package-lock.json. pytest là framework test **của SmartRegression**,
không phải quyết định framework repo đầu vào.

## Windows PowerShell

Cài Python 3.14 và Node 22.14+ dòng 22 trước. Cài uv theo
[tài liệu chính thức](https://docs.astral.sh/uv/getting-started/installation/),
ví dụ qua pip:

```powershell
py -m pip install uv
uv --version
uv sync --locked
npm.cmd --prefix frontend ci
uv run uvicorn smartregression.api.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu uv chưa ở PATH, dùng `py -m uv` thay `uv`. Máy bootstrap có thể dùng
`.\.tools\bin\uv.exe` thay `uv`; đây chỉ là công cụ cục bộ, không phải dependency runtime.
Terminal thứ hai ở root:

```powershell
npm.cmd --prefix frontend run dev
```

Dùng npm.cmd nếu PowerShell chặn npm.ps1; không cần đổi execution policy toàn máy.

## Linux/macOS

Cài Python 3.14, uv và Node 22.14+ dòng 22 bằng công cụ quản lý runtime của bạn.
Kiểm tra `python3 --version`, `uv --version`, `node --version`, `npm --version`.

```sh
uv sync --locked
npm --prefix frontend ci
uv run uvicorn smartregression.api.main:app --reload --host 127.0.0.1 --port 8000
# terminal thứ hai tại root
npm --prefix frontend run dev
```

Mở http://localhost:5173, API http://127.0.0.1:8000/health,
API docs http://127.0.0.1:8000/docs. Vite proxy `/api` tới backend nên không cần
CORS rộng. Dev server chỉ bind loopback. Build preview phục vụ UI tĩnh, không có
proxy API được cấu hình cho deployment; API có thể hiện chưa kết nối khi preview.

Không cần `.env` để chạy bootstrap; `.env.example` chỉ ghi placeholder tương lai.
Không đưa API key vào VITE_* hoặc browser. Fixture được bundle vào dashboard.
Không có demo endpoint cần bật, cũng không có endpoint analyze.

## CLI và tái sinh contract

```sh
uv run smartregression --help
uv run smartregression validate-report examples/reports/demo.json
uv run python scripts/export_contracts.py
npm --prefix frontend run contracts:generate
```

Exit code validate-report: 0 hợp lệ, 1 sai JSON/contract, 2 lỗi đọc file hoặc cú pháp CLI.
Các lệnh checks nằm trong README/AGENTS. Khi đổi dependency, dùng `uv lock`
và/hoặc `npm --prefix frontend install`, review lockfile rồi chạy lại checks.
Không sửa tay lockfile. Nếu mất mạng, không coi checks chưa chạy là pass.

## Giới hạn của phiên review bootstrap

Trong sandbox của phiên review, Vite dev/build bị `spawn EPERM` khi khởi tạo esbuild;
hai pytest dùng tmp_path bị PermissionError. Đây không phải kết quả pass, và không
cần thay stack hoặc hạ checks CI để né lỗi. Chạy lại các lệnh chuẩn trên máy thành viên.
`uv sync --locked --offline` chỉ chạy được khi cache đủ cả build dependency hatchling;
lockfile hợp lệ không đồng nghĩa có thể cài hoàn toàn offline. Không dùng offline
cho lần setup mới. Xem verification.md để biết lệnh đã chạy và còn thiếu.
