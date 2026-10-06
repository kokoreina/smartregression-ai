# 06 — Testing/Quality

## Phạm vi

Kiểm tra source SmartRegression; không nhầm với tính năng chọn/chạy test của repo đầu vào.

## Yêu cầu

- MUST chọn checks theo risk: unit cho logic, integration cho boundary, e2e cho luồng
  quan trọng khi có harness. Bug logic SHOULD có regression test tái hiện nếu khả thi;
  nếu không, ghi reproduction evidence/giới hạn và bước cần làm.
- MUST giữ lỗi cũ tách lỗi mới, environment failure tách code failure. Không xóa/skip
  test, hạ threshold hoặc bỏ gate để che lỗi. Diagnostic subset không thay full gate.
- Unit tests MUST không gọi dịch vụ trả phí thật; mock tại provider/network/runner
  boundary. Không mock hết nghiệp vụ để chỉ assert implementation tự gọi chính nó.
- MUST kiểm tra lỗi liên quan: invalid schema, unknown IDs, wrong commit, empty
  retrieval, timeout, partial parsing. Chỉ thêm case cho module/task có thật.
- MUST báo command/cwd/result thật, coverage chỉ khi đã đo. Build/typecheck không
  chứng minh browser behavior hoặc thuật toán đúng; integration không tự chứng minh isolation.
- MAY không chạy product suite cho typo/docs-only; kiểm tra links/fences/diff là đủ
  nếu không đổi source/config. Không thêm test hình thức chỉ để đạt số lượng.

## Lý do

Tập trung công sức kiểm chứng vào failure có tác động và không tạo cảm giác an toàn giả.

## Ví dụ

Đúng: unknown evidence test chứng minh reject rồi kiểm tra đường happy path.
Sai: skip hai tests lỗi PermissionError và báo toàn bộ suite pass; mock selector để
assert kết quả đã hard-code rồi gọi đó là bằng chứng chất lượng selection.

## Kiểm chứng

Chọn lệnh từ [verified commands](../development/verified-commands.md), lưu exit/result
và checks không chạy. [Review snapshot](../development/verification.md) không thay lần chạy mới.

## Ngoại lệ

Không tái hiện được do môi trường thì báo blocked/uncertain và cung cấp bước chạy lại;
không đổi assertion để né lỗi. Quyết định bỏ test lỗi thời có task và rationale rõ,
không tự biến thành ngoại lệ quality; theo [00](00-governance.md).

## Liên quan

[07 Debugging](07-debugging-change-control.md), [11 Research](11-research-evaluation.md),
[12 CI](12-ci-dependencies.md).
