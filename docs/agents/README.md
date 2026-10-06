# Agent Profiles

Đây là hồ sơ **vai trò coding agent hỗ trợ nhóm phát triển**, không phải agents của
sản phẩm SmartRegression, cấu hình model, hoặc cấu hình tự khởi chạy sub-agent.
Nhóm có 5 thành viên (4 software, 1 DevOps có khả năng software); một người dùng
nhiều profile theo task. Phân công người thật theo [module ownership](../development/module-ownership.md).

Đọc [AGENTS gốc](../../AGENTS.md), chọn một profile chính và mở các rule được định
tuyến; chỉ thêm profile khác khi task chạm boundary của họ. Mẫu dùng chung ở
[task brief](../templates/task-brief.md) và [handoff](../templates/handoff.md).

| Profile | Dùng cho | Đầu ra chính |
| --- | --- | --- |
| [Coordinator](coordinator.md) | Task/dependency/phạm vi | Task nhỏ, thứ tự tích hợp, pending rõ |
| [Backend/Contracts](backend-contracts.md) | API/application/CLI/schema | Contract nhất quán producer–consumer |
| [Change Impact](change-impact.md) | Git/symbol/dependency/provenance | Changed/possibly impacted/verified được phân biệt |
| [RAG/LLM](rag-llm.md) | Index/retrieval/prompt/adapter | Context đúng snapshot, output đã validate |
| [Regression Selection](regression-selection.md) | Inventory/validation/fallback | Selected/skipped đúng inventory, lý do rõ |
| [Frontend/Dashboard](frontend-dashboard.md) | Hiển thị report/trạng thái | UI trung thực với dữ liệu nguồn |
| [DevOps/Runner](devops-runner.md) | CI/isolation/artifacts | Thực thi có giới hạn, gate có bằng chứng |
| [QA/Research](qa-research.md) | Product tests/evaluation | Hai luồng kiểm chứng tách biệt, tái lập được |
| [Reviewer](reviewer.md) | Review đọc code/diff | Findings có bằng chứng, không sửa mặc định |

Profile mô tả quyền tự xử lý **trong task đã giao**, không cấp quyền công cụ hay
phê duyệt thiết kế. Các bước tương lai chỉ áp dụng khi module được triển khai;
đọc [decision register](../development/decision-register.md) trước khi coi feature là có thật.
Không chạy song song nếu chưa giao paths/shared files rõ; không giả lập review độc lập
bằng việc đổi tên profile trong cùng phiên.
