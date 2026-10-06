# Project Rules

Quy ước làm việc được tạo theo yêu cầu nhóm; không tự bật gate CI/GitHub. MUST là
yêu cầu trong phạm vi áp dụng; SHOULD là mặc định có thể khác khi ghi lý do trong
task/PR; MAY là tùy chọn. MUST không biến quyền của công cụ thành quyền của tài liệu.
Ngoại lệ MUST dùng [rule exception](../templates/rule-exception.md) và cơ chế
[governance](00-governance.md), không tự nới rule chỉ để báo pass.

Đọc theo bảng định tuyến ở [AGENTS](../../AGENTS.md). Mỗi file chuyên đề là nguồn
quy tắc của mình; [contracts](../contracts/README.md) giữ chi tiết schema hiện hành,
[ADR](../architecture/decisions/0001-bootstrap.md) giữ quyết định thiết kế và
[evaluation protocol](../research/evaluation-protocol.md) giữ kế hoạch thực nghiệm.

| ID | Nội dung | Khi đọc thêm |
| --- | --- | --- |
| [00](00-governance.md) | Quyết định, ngoại lệ, phạm vi | Xung đột hoặc thay đổi policy |
| [01](01-architecture.md) | Dependency và boundary | Thêm/move module hoặc orchestration |
| [02](02-coding-standards.md) | Style, type, lỗi, retry | Sửa source |
| [03](03-contracts-api.md) | Contract/API/compatibility | Sửa producer/consumer |
| [04](04-data-storage.md) | Snapshot, artifacts, migration | Lưu/index/cache dữ liệu |
| [05](05-git-pr.md) | Working tree, PR, shared files | Branch/PR/tích hợp |
| [06](06-testing-quality.md) | Kiểm tra theo rủi ro | Sửa behavior/test |
| [07](07-debugging-change-control.md) | Debug có bằng chứng | Bugfix/refactor |
| [08](08-llm-rag.md) | Retrieval, model, budget, data | Tính năng LLM/RAG |
| [09](09-impact-selection.md) | Diff/impact/inventory/fallback | Phân tích và chọn test |
| [10](10-runner-security.md) | Isolation/threat boundary | Ingest/checkout/execution |
| [11](11-research-evaluation.md) | Fault/metrics/leakage | Dataset/benchmark/kết quả |
| [12](12-ci-dependencies.md) | CI và dependency | Workflow/runtime/packages |
| [13](13-documentation-ai-use.md) | Tài liệu và AI disclosure | Tài liệu/handoff/ADR |
| [14](14-enforcement.md) | Ma trận cơ chế kiểm tra | Review gates/readiness |

Trạng thái kỹ thuật không suy ra từ MUST: quy tắc runner có thể bắt buộc khi runner
được xây nhưng runner hiện chưa có. [Enforcement](14-enforcement.md) phân biệt
Markdown, local checks, CI cấu hình, human review và GitHub settings chưa xác minh.
