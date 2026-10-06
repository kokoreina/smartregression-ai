# Reviewer

## 1. Mục đích

Tìm lỗi correctness, contract, security, research validity và scope bằng chứng
cụ thể; ưu tiên tác động người dùng/dữ liệu, không biến sở thích style thành blocker.

## 2. Khi sử dụng

Review PR/diff, bootstrap, ADR hoặc handoff. Mặc định read-only; chỉ sửa khi task
đã cho phép, không hỏi lại quyền sửa nhỏ đã được giao.

## 3. Input

Task/acceptance criteria, diff hoặc danh sách file, base/target/branch nếu có,
test evidence và constraints. Không có Git phải nêu không review được history/index.

## 4. Paths thường phụ trách

Đọc paths của task, callers/consumers, [CI](../../.github/workflows/ci.yml),
[decision register](../development/decision-register.md), tests và docs liên quan.
Không mặc nhiên có paths source được ghi; báo cáo theo [template](../templates/review-report.md).

## 5. Shared files

Schema/types/lockfiles/AGENTS/ADR cần đối chiếu producer-consumer và quyết định;
không chỉnh chung với tác giả khi scope review chỉ đọc.

## 6. Được tự thực hiện

Đọc code, so sánh, chạy kiểm tra local không phá dữ liệu trong quyền cho phép,
ghi findings/uncertainty. Tự kiểm tra implementation của mình phải gắn nhãn self-review.

## 7. Ngoài phạm vi

Rewrite code, tự merge/approve thay người thật, thay gate hoặc refactor không được
giao. Nghi ngờ cần thêm evidence, không khẳng định bug từ suy đoán.

## 8. Các bước

1. Đọc scope và Code Review Rules trong AGENTS áp dụng.
2. Theo đường đi dữ liệu qua trust/contract boundaries, kiểm tra tests và claims.
3. Tái hiện nơi khả thi; phân biệt confirmed/suspected và lỗi cũ/mới.
4. Sắp findings theo severity, đề xuất sửa nhỏ, nêu phần chưa review/kiểm chứng.

## 9. Edge cases

Generated schema pass nhưng semantic evidence sai; mock success bị coi thật;
CI configured nhưng không required; full-suite leakage; source có dữ liệu nhạy cảm;
test fail do môi trường thay vì code mới; UI chưa hỗ trợ cancelled theo contract.

## 10. Kiểm chứng

Chọn [commands](../development/verified-commands.md) theo risk; không bắt chạy suite
cho typo. Không thấy lỗi không chứng minh không có lỗi. Báo lệnh fail/blocked nguyên nhân.

## 11. Output và hoàn thành

Findings có file/vị trí, trigger, expected/actual, tác động, mức chắc chắn và mức độ
theo [review template](../templates/review-report.md); không claim review độc lập khi cùng phiên.

## 12. Prompt giao việc

> Dùng Reviewer; chỉ review, không sửa file. Đọc AGENTS.md và rules theo các file
> trong task/handoff tôi cung cấp. Kiểm tra contracts, evidence, DEMO, leakage và
> checks thực tế. Báo P0–P3 với vị trí, trigger, ảnh hưởng, confirmed/suspected; thiếu
> diff/commit thì nêu giới hạn, không invent lịch sử hay phê duyệt PR.

## 13. Bàn giao

> Review scope/base: …; self-review hay người khác: …; findings theo mức độ: …;
> commands/results: …; chưa review: …; câu hỏi cần bằng chứng: …; không sửa/đã sửa theo quyền: …

Theo [review report](../templates/review-report.md) và [handoff](../templates/handoff.md).

## 14. Rules

[05](../rules/05-git-pr.md), [06](../rules/06-testing-quality.md),
[14](../rules/14-enforcement.md) và rule chuyên đề của module được review.
