# 14 — Enforcement

## Phạm vi và yêu cầu

MUST phân biệt rule được viết với cơ chế đang hoạt động. Markdown không bảo đảm
tuân thủ; local hook có thể bị bỏ qua; CI chỉ chặn merge khi required checks được
cấu hình phù hợp trên branch/ruleset. Profile Reviewer không phải human review độc lập.

Trạng thái tại lần lập bộ tài liệu: chưa có .git/remote để kiểm repository settings;
source CI YAML có thật nhưng chưa có bằng chứng run. Bộ tài liệu này **không tự bật gate**.
SHOULD kiểm tra lại bảng mỗi sprint; MAY triển khai gate theo task riêng đã được giao.

## Ma trận

Người chịu trách nhiệm dưới đây là vai trò đề xuất, chưa gán tên/quyền GitHub thật.
`observed local` chỉ là evidence cục bộ; `configured` là có cấu hình; `planned` là chưa có.

| Rule | Cơ chế kiểm tra | Nơi cấu hình/nguồn | Chịu trách nhiệm | Trạng thái |
| --- | --- | --- | --- | --- |
| 00 Quyết định/ngoại lệ | Markdown + human review task/ADR | [register](../development/decision-register.md), [exception](../templates/rule-exception.md) | Coordinator + người giao task | Quy ước; chưa có máy tự phê duyệt |
| 01 Dependency direction | Review imports/boundaries | [architecture](../architecture/overview.md) | Backend + reviewer | Human review; architecture lint planned |
| 02 Python style | Ruff local + source CI | [pyproject](../../pyproject.toml), [CI](../../.github/workflows/ci.yml) | Người sửa + DevOps | Observed local; CI configured, run chưa xác minh |
| 02 Frontend style/types | ESLint/tsc local + CI | [package](../../frontend/package.json), [tsconfig](../../frontend/tsconfig.json), [CI](../../.github/workflows/ci.yml) | Frontend + DevOps | Observed local; CI configured |
| 03 Schema/fixture | Pydantic tests/CLI/exporter --check | [models](../../backend/src/smartregression/contracts/models.py), [exporter](../../scripts/export_contracts.py), CI | Backend + QA | Một số checks observed local; full suite còn thiếu |
| 03 Generated types drift | Generator --check | [generator](../../frontend/scripts/contracts.mjs), package, CI | Backend + Frontend | Observed local; CI configured |
| 04 Artifacts/cache | .gitignore + staged review | [.gitignore](../../.gitignore), [storage pending](../../backend/src/smartregression/adapters/storage/README.md) | Người sửa + DevOps | Patterns có; chưa có Git index để audit; cache isolation tests planned |
| 05 PR/merge | Human review + repository settings | [CONTRIBUTING](../../CONTRIBUTING.md), [PR template](../../.github/pull_request_template.md) | Tác giả, reviewer, leader có quyền thật | Template có; required reviewers/checks/branch protection chưa xác minh |
| 06 Product tests | pytest local/CI | [tests](../../backend/tests), pyproject, CI | QA + người sửa | CI configured; review trước 14 pass, 2 temp errors |
| 06 Browser/e2e | Manual smoke; future harness | [verification](../development/verification.md) | Frontend + QA | HTTP smoke có; browser e2e chưa xác minh/harness planned |
| 07 Small bugfix | Reproduction + diff review | [bug template](../templates/bug-report.md) | Tác giả + reviewer | Quy ước human review |
| 08 LLM/RAG integrity | Mock/budget/provenance tests khi có module | [LLM pending](../../backend/src/smartregression/adapters/llm/README.md) | RAG/LLM + QA | Planned; chưa provider/live checks |
| 09 Selection validity | Contract validators + inventory tests tương lai | models, [selection pending](../../backend/src/smartregression/core/selection/README.md) | Selection + QA | Overlap/reference checks có; membership/fallback tests planned |
| 10 Runner isolation | Threat model + isolated integration tests | [port](../../backend/src/smartregression/core/execution/ports.py) | DevOps + reviewer | Planned; không có runner thực |
| 11 No leakage/metrics | Dataset/protocol review + metric tests tương lai | [protocol](../research/evaluation-protocol.md) | QA/Research + reviewer khác người viết | Outline có; benchmark/gates planned |
| 12 Reproducible install/build | uv locked/npm ci/build trong CI | manifests/locks, CI | DevOps + người cập nhật | Configured; clean setup/build/CI xanh chưa xác minh |
| 13 AI/documentation | PR checklist + đọc code/link check | PR template, [setup](../development/agent-rules-setup.md) | Tác giả + human reviewer | Quy ước; link check chỉ chạy tạm cho task docs |
| 10/13 Secrets | Source/staged review; scanner tương lai | .gitignore, Code Review Rules | Tác giả + reviewer | Review thủ công; secret scanner/hook chưa triển khai |

Không có local Git hook đã được xác minh. Bằng chứng lệnh và cập nhật HTTP smoke nằm
ở [verified commands](../development/verified-commands.md); không sao chép kết quả cũ thành pass mới.

## Lý do và ví dụ

Đúng: “schema drift check có trong workflow, chưa biết có required trên branch”.
Sai: “có AGENTS.md nên agent không thể sửa ngoài scope” hoặc “Reviewer profile đã approve PR”.

## Kiểm chứng

Đọc config/run/settings có quyền truy cập, ghi nơi và thời điểm quan sát. Nếu thiếu
quyền/settings thì giữ chưa xác minh; không tự thay quyền GitHub trong task tài liệu.

## Ngoại lệ

Task docs không cần dựng CI gate còn thiếu. Ngoại lệ với gate đã có cần quyết định
theo [00](00-governance.md), không tự vô hiệu hóa để merge. Quyền hệ thống không thể miễn bằng template.

## Backlog gate đề xuất (không triển khai trong nhiệm vụ này)

| Task | Đầu ra | Tiêu chí chấp nhận |
| --- | --- | --- |
| Xác minh source CI | Run link/log trên PR thật | Các lệnh configured chạy thành công, failure chặn job |
| Required checks/reviews | Leader đối chiếu settings và đề xuất policy | Quyết định thật, chỉ chỉnh khi được giao; chứng minh branch mục tiêu yêu cầu checks |
| Architecture/secret checks | Thiết kế gate nhỏ theo risk | Fixture vi phạm bị phát hiện, không log secret; task dependency riêng nếu cần |
| Inventory/runner gates | Tests khi module có thật | Unknown ID bị reject, timeout/cancel/cleanup/isolation có evidence |
| Research reproducibility | Manifest/leakage/metric checks | Cohort/denominator traceable, zero denominator/failed run xử lý rõ |

## Liên quan

[05](05-git-pr.md), [06](06-testing-quality.md), [12](12-ci-dependencies.md),
[13](13-documentation-ai-use.md).
