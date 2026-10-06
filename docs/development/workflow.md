# Workflow nhóm

1. Chọn task trong backlog, ghi acceptance criteria và phần không thuộc scope.
2. Kiểm tra trạng thái working tree; tạo branch theo task, giữ thay đổi của người khác.
3. Sửa lớp có trách nhiệm phù hợp, cập nhật docs/test cần thiết.
4. Đổi contract thì tái sinh OpenAPI/types; không sửa generated file riêng lẻ.
5. Chọn checks theo [verified-commands](verified-commands.md); mở PR nhỏ bằng template,
   ghi kết quả và giới hạn thực tế. Định tuyến profile/rule ở [AGENTS](../../AGENTS.md).
6. Một thành viên khác review thiết kế, bằng chứng kiểm chứng và phần AI hỗ trợ.

CI .github/workflows kiểm tra chính SmartRegression. integrations/github-actions là
thiết kế tích hợp với repo được phân tích, chưa chạy và không phải CI của dự án này.
Chưa tạo Git repository/remote hoặc cấu hình quyền; maintainer thực hiện khi sẵn sàng.

Khi dùng Codex, bắt đầu từ [agent-rules-setup](agent-rules-setup.md), giao task bằng
[brief](../templates/task-brief.md) và chuyển phiên bằng [handoff](../templates/handoff.md).
