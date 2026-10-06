# 00 — Governance

## Phạm vi

Mọi task và quyết định nhóm. Nguồn hiện trạng ở [decision register](../development/decision-register.md).

## Yêu cầu

- MUST ghi nguồn và trạng thái accepted/proposed/pending/superseded. Có code không
  chứng minh mentor đã duyệt; prompt gợi ý cũ không tự thành accepted.
- Khi code/docs mâu thuẫn, MUST đọc ADR/lịch sử nếu có, nêu bằng chứng và phương án.
  Không có Git/proposal thì ghi thiếu nguồn, không tự kết luận bên nào luôn đúng.
- MUST giữ công việc có sẵn; quy tắc module bổ sung chi tiết, không âm thầm nới rule gốc.
- Thay phạm vi, contract breaking, mô hình lưu trữ hoặc security boundary MUST có
  quyết định rõ trong task/ADR. Nếu user đã giao hợp lệ thì thực hiện và ghi quyết định,
  không hỏi lại máy móc; phần còn mơ hồ ảnh hưởng phạm vi mới cần làm rõ.
- SHOULD chọn thay đổi nhỏ và reversible; MAY tự quyết cách diễn đạt, tên helper,
  test cục bộ trong scope. Không biến mọi lựa chọn kỹ thuật nhỏ thành ADR.
- MUST ghi ngoại lệ có phạm vi, lý do, biện pháp thay thế, người quyết định thực tế,
  ngày và mốc xem xét lại. Chưa duyệt ghi pending, không tự duyệt ngoại lệ của mình.
- SHOULD rà soát rules mỗi sprint, gộp trùng/bỏ lỗi thời bằng thay đổi có truy vết.

## Lý do

Cho phép tiến độ trong phạm vi được giao, đồng thời ngăn kiến trúc/policy bị đổi ngầm.

## Ví dụ

Đúng: task giao đổi schema, agent lập danh sách consumers và migration rồi cập nhật.
Sai: thấy test lỗi nên tự bỏ validation, ghi ADR accepted mà không có quyết định.

## Kiểm chứng

Review task brief/ADR/diff đối chiếu [register](../development/decision-register.md);
kiểm tra người và thời điểm là có thật. Không có diff Git dùng snapshot file trước/sau.

## Ngoại lệ

Dùng [rule-exception](../templates/rule-exception.md) cho ngoại lệ MUST. Ngoại lệ không
vượt chỉ dẫn cấp cao hơn, permission/sandbox hoặc quyền GitHub. SHOULD khác mặc định
chỉ cần ghi lý do trong task/PR nếu không chạm MUST.

## Liên quan

[05 Git](05-git-pr.md), [07 Change control](07-debugging-change-control.md),
[13 Documentation](13-documentation-ai-use.md), [14 Enforcement](14-enforcement.md).
