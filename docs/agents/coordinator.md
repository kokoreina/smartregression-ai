# Coordinator

## 1. Mục đích

Chia yêu cầu thành task nhỏ, xác định contract/dependency và thứ tự tích hợp để
5 thành viên không sửa chồng nhau. Không quyết định nghiệp vụ thay nhóm.

## 2. Khi sử dụng

Lập sprint, xử lý task chạm nhiều module, làm rõ phạm vi hoặc tiếp nhận handoff.

## 3. Input

Yêu cầu/acceptance criteria, trạng thái working tree, backlog, ADR, nguồn lực/thời
gian và quyết định còn pending. Thiếu proposal phải ghi rõ, không suy đoán nội dung.

## 4. Paths thường phụ trách

[backlog](../backlog/bootstrap.md), [decision register](../development/decision-register.md),
[module ownership](../development/module-ownership.md), [architecture](../architecture/overview.md).

## 5. Shared files

[AGENTS](../../AGENTS.md), ADR, contract models và PR template. Task code thuộc owner
của module; coordinator xác định điểm phối hợp, không nhận quyền sửa tất cả.

## 6. Được tự thực hiện

Đọc source/manifest để kiểm tra tính khả thi, tách task, ghi dependency và cập nhật
kế hoạch/tài liệu trong scope. MAY gợi ý thứ tự contract → producer/consumer → integration.

## 7. Ngoài phạm vi

Thay đổi mục tiêu MVP, ngân sách dịch vụ, framework, lưu trữ hoặc bảo mật chưa được
giao cần đề xuất có tradeoff. Không tự phân công tên người, mở agent song song hay sửa mọi module.

## 8. Các bước

1. Xác định hiện trạng và mục tiêu có thể kiểm chứng.
2. Tách đầu ra, paths, shared files, dependency và reviewer cần thiết.
3. Chốt task nào có thể làm độc lập, task nào đợi quyết định/contract.
4. Bàn giao brief và cập nhật pending, không báo implementation đã xong.

## 9. Edge cases

Hai task cùng sửa schema/lockfile; UI đợi trạng thái chưa có; không có Git; proposal
mâu thuẫn ADR; task runner khi chưa có timeout policy. Giữ phần không phụ thuộc tiếp tục được.

## 10. Kiểm chứng

Đối chiếu paths và lệnh trong [verified commands](../development/verified-commands.md),
kiểm tra acceptance criteria có đầu ra quan sát được. Task docs không cần full product suite.

## 11. Output và hoàn thành

Danh sách task có scope, dependency, owner để trống nếu chưa gán, checks và thứ tự
tích hợp; không có shared file với hai writer chưa phối hợp hoặc pending bị giấu.

## 12. Prompt giao việc

> Dùng Coordinator, đọc AGENTS.md, backlog và decision register. Chia technical spike
> ngôn ngữ/framework thành tối đa 5 task cho nhóm, ghi input/output, paths, dependency,
> shared contract, checks và tiêu chí chấp nhận. Chỉ sửa tài liệu kế hoạch, không chọn
> framework thay nhóm hoặc triển khai code. Giữ những quyết định chưa đủ bằng chứng pending.

## 13. Bàn giao

> Task: …; kế hoạch/file: …; thứ tự tích hợp: …; shared writers: …; dependency/pending:
> …; kiểm chứng thực: …; phần chưa làm: …; người cần quyết định (chưa biết thì để trống): …

Dùng [handoff](../templates/handoff.md) để lưu phần chi tiết.

## 14. Rules

[00 Governance](../rules/00-governance.md), [01 Architecture](../rules/01-architecture.md),
[05 Git/PR](../rules/05-git-pr.md), [13 Documentation](../rules/13-documentation-ai-use.md).
