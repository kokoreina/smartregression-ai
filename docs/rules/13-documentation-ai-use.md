# 13 — Documentation/AI Use

## Phạm vi

README, setup, schema/architecture docs, ADR, task/handoff và AI disclosure.

## Yêu cầu

- Behavior/setup/schema/architecture đổi MUST cập nhật tài liệu nguồn và link, không
  tạo bản sao tự mâu thuẫn. Ghi giới hạn, demo/mock và phần chưa triển khai.
- MUST ghi lệnh/kết quả thật; không bịa nguồn, phiên bản, username, contribution ratio
  hoặc mức AI hỗ trợ. Người viết phải hiểu và giải thích được code AI tạo/sửa.
- Proposal C1.SE26 v1.4 có Appendix C về AI disclosure và Appendix D về chính sách
  AI của trường. Khi task liên quan AI use, disclosure, báo cáo học thuật hoặc quyền
  dùng nội dung, MUST đọc đúng appendix và đối chiếu bản hiện hành; không suy ra chữ ký
  cũ phê duyệt nội dung mới hoặc việc nhóm đã tuân thủ.
- Appendix D cho phép AI hỗ trợ học tập, thiết kế, code, debug, test và tài liệu khi
  sinh viên review/hiểu/xác minh; cấm nộp nội dung AI không hiểu, tài liệu không kiểm
  chứng và nguồn nghiên cứu bịa đặt. MUST bảo toàn trách nhiệm tác giả và disclosure
  tool/mục đích/giai đoạn/phạm vi khi sửa tài liệu thuộc dự án.
- MUST không lưu key hoặc toàn prompt chứa source nhạy cảm vào nhật ký chia sẻ.
  Handoff tóm tắt quyết định/evidence đã redacted đủ để tiếp tục, không cần transcript nguyên văn.
- Quyết định quan trọng SHOULD có [ADR](../templates/adr.md) ngắn; lịch sử chỉnh file
  không được dùng giả phê duyệt mentor. Chưa biết người quyết định để trống/pending.
- MUST ghi rõ profile là vai trò, không chọn model hoặc khởi agent; rules là tài liệu,
  không cấp quyền. Hướng dẫn dùng Codex cần nguồn official và giới hạn client chưa xác minh.
- MAY bỏ test sản phẩm cho docs-only; MUST kiểm paths, links, fences, bảng, consistency
  và diff. Không thêm docs tooling dependency chỉ cho một đợt tài liệu.

## Lý do

Người mới và agent dựa trên cùng thông tin thực, có thể biết điều gì chưa được làm.

## Ví dụ

Đúng: “AI hỗ trợ draft tests; tác giả đã đọc và chạy các lệnh sau …”. Sai: “mentor
approved”, “90% do người viết” hoặc “CI active” khi không có evidence.

## Kiểm chứng

Review PR AI section, links đến nguồn quyết định/command và mức chắc chắn;
đối chiếu manifest/code trước cập nhật docs. Tự review cùng phiên phải được gọi self-review.

## Ngoại lệ

Không cần ADR cho typo hoặc sửa link. Nếu tài liệu cũ chứa secret thì xử lý theo
quy trình được giao, không chép secret sang bug report; thay chính sách theo [00](00-governance.md).

## Liên quan

[00 Governance](00-governance.md), [05 Git](05-git-pr.md),
[06 Testing](06-testing-quality.md), [setup agents](../development/agent-rules-setup.md).
