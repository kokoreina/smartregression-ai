# SmartRegression AI

**An LLM- and RAG-Based Change Impact Analysis and Regression Test Selection System.**

Bootstrap cho nhóm 5 sinh viên: contract, health API, CLI kiểm tra report và dashboard
**DEMO**. Mục tiêu tiếp theo là phân tích ảnh hưởng giữa hai Git commit có bằng chứng,
chọn regression test hiện có, xác thực lựa chọn và hỗ trợ thực thi/đánh giá.

Workspace ban đầu trống, chưa có Git metadata, AGENTS.md hoặc docs/proposal.
Phạm vi hiện tại dựa trên yêu cầu bootstrap của người dùng, chưa đối chiếu proposal.

Review bootstrap: lint, typecheck, schema/types và backend smoke checks đã chạy;
frontend dev/build và toàn bộ pytest còn cần xác nhận trên máy không bị giới hạn
sandbox. Chưa có bằng chứng CI xanh. Xem [kết quả và điều kiện vào sprint](docs/development/verification.md).

## Chạy nhanh

Yêu cầu Python 3.14.x, uv, Node.js 22.14+ thuộc dòng 22, npm 10+.
Tại thư mục gốc:

```sh
uv sync --locked
npm --prefix frontend ci
uv run uvicorn smartregression.api.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal thứ hai: `npm --prefix frontend run dev`, mở http://localhost:5173.
Dashboard tải fixture cục bộ, vẫn xem được DEMO khi API ngắt kết nối.

```sh
uv run smartregression --help
uv run smartregression validate-report examples/reports/demo.json
uv run ruff check .
uv run ruff format --check .
uv run pytest
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
uv run python scripts/export_contracts.py --check
npm --prefix frontend run contracts:check
```

Xem [setup Windows/Linux/macOS](docs/development/setup.md),
[kiến trúc](docs/architecture/overview.md), [contract](docs/contracts/README.md),
[backlog](docs/backlog/bootstrap.md) và [kiểm chứng](docs/development/verification.md).

Hướng dẫn làm việc: [Agent Profiles](docs/agents/README.md),
[Project Rules](docs/rules/README.md), [bắt đầu task với Codex](docs/development/agent-rules-setup.md),
[lệnh đã đối chiếu](docs/development/verified-commands.md) và
[sổ quyết định/trạng thái cập nhật](docs/development/decision-register.md).

## Giới hạn

- Chỉ `/health` hoạt động; đây là liveness của API, không kiểm tra dependency.
- Không có endpoint analyze, demo API, LLM call, clone repo hay chạy test đầu vào.
- Đầu vào MVP đã chốt **Python + pytest** theo [ADR 0002](docs/architecture/decisions/0002-python-pytest-input.md); phiên bản hỗ trợ production và nghiệm thu G1 còn pending, đã có evidence fixture.
- Có spike read-only Git/Python và [G1 fixture cô lập](scripts/g1/README.md), chưa nối
  API/dashboard. Retrieval/selection/evaluation và runner production vẫn chưa triển khai.
- Database, vector store, LLM provider và giao thức worker còn pending sau spike.
- Chi phí/thời gian chưa đo là `null`; test fail không đồng nghĩa phát hiện fault.
- Đây không phải sản phẩm production-ready; chưa deploy. Source CI của main
  `e937f66` đã chạy thành công trên GitHub; không xác minh thay đổi local mới.
- Sprint 1 có [candidate reproduction](docs/research/sprint-1/candidate-reproduction.md)
  trên hai snapshot Python/pytest trong Docker; xem [review hiện hành](docs/research/sprint-1/review.md)
  cho phạm vi nghiệm thu local, G1 và phần còn pending.

## Cấu trúc

```text
backend/src/smartregression/   contracts, core, application, adapters, api, cli
backend/tests/               unit, integration, fixtures
frontend/src/                app, features, components, lib, types
contracts/generated/         OpenAPI từ backend, không sửa tay
examples/reports/             fixture DEMO chuẩn
docs/                        architecture, contracts, development, research, backlog
.github/workflows/            CI của SmartRegression
integrations/github-actions/  tích hợp repo đầu vào tương lai
scripts/                     export/check contract
var/                         dữ liệu cục bộ bị Git ignore
```
