# Regression Selection

## 1. Mục đích

Chọn tập con từ test inventory đúng target commit, validate IDs và giải thích
selected/skipped/fallback. Selection là chọn tập; prioritization chỉ đổi thứ tự chạy.

## 2. Khi sử dụng

Inventory mapping, selection policy, validator hoặc fallback khi thiếu bằng chứng.

## 3. Input

Commit pair, inventory/framework được xác định, findings/evidence và policy. Không
nhận full-suite outcomes/fault labels. Framework của repo đầu vào hiện pending.

## 4. Paths thường phụ trách

[core/selection](../../backend/src/smartregression/core/selection),
[application](../../backend/src/smartregression/application) khi có use case,
[unit tests](../../backend/tests/unit). Selection thật chưa triển khai.

## 5. Shared files

TestSelection/TestDecision trong [models](../../backend/src/smartregression/contracts/models.py),
[runner port](../../backend/src/smartregression/core/execution/ports.py), inventory do
discovery cung cấp và report frontend. Không dùng evaluation labels làm shared input.

## 6. Được tự thực hiện

Sửa validator/policy trong task, kiểm tra tồn tại/loại trùng IDs có lý do, viết tests
trên inventory cố định; giữ decision log và fallback reason.

## 7. Ngoài phạm vi

Đổi framework, chạy test, sinh test mới cho repo đầu vào, hứa zero missed faults,
hoặc đổi safety/fallback policy chưa được giao; cần đề xuất và quyết định thực tế.

## 8. Các bước

1. Chốt inventory thuộc target commit và định dạng stable ID.
2. Tạo candidate từ evidence, kiểm tra membership và bất biến hai tập.
3. Áp dụng empty/error/partial policy đã quyết định; lưu fallback reason.
4. Bàn giao chỉ IDs đã validate cho runner; không tự thực thi LLM output.

## 9. Edge cases

Unknown/duplicate/parameterized/renamed test IDs, selected/skipped overlap, inventory
rỗng hoặc chưa đầy đủ, config/dependency đổi, parser/LLM lỗi, fallback full suite chạy thất bại.

## 10. Kiểm chứng

Unit theo inventory và policy, contract invalid cases, integration discovery khi có
framework. Giữ outcomes ngoài test input selector; xem [commands](../development/verified-commands.md).

## 11. Output và hoàn thành

Mỗi ID nằm đúng inventory, selected/skipped không giao, lý do có bằng chứng hoặc
uncertainty rõ; empty selection không bị báo an toàn; không có execution side effect.

## 12. Prompt giao việc

> Dùng Regression Selection, đọc rule 03 và 09. Review TestSelection hiện có với
> inventory giả định: phát hiện overlap/duplicate/unknown IDs. Chỉ sửa validation và
> tests đã có nếu lỗi thuộc contract hiện hành; membership thực chưa có interface thì
> đề xuất riêng, không chốt framework hay chạy test đầu vào. Báo limits và checks thực.

## 13. Bàn giao

> Inventory/framework/target: …; selected/skipped invariant: …; fallback policy: …;
> validation đã làm: …; trường hợp chưa hỗ trợ: …; lệnh/kết quả: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[03](../rules/03-contracts-api.md), [06](../rules/06-testing-quality.md),
[09](../rules/09-impact-selection.md), [11](../rules/11-research-evaluation.md).
