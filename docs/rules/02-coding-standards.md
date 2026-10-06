# 02 — Coding Standards

## Phạm vi

Python/TypeScript và scripts của SmartRegression, không áp style sang repo đầu vào.

## Yêu cầu

- MUST theo Ruff và TypeScript strict/ESLint hiện có; dùng [commands](../development/verified-commands.md).
  Không thêm formatter/framework để sửa một file nếu chưa có nhu cầu task.
- MUST có type annotations tại interface/public application boundary; SHOULD dùng
  tên mô tả domain. Comment giải thích quyết định/giới hạn, không kể lại từng dòng.
- MUST validate tại trust boundary: request/file report, provider output, repo paths,
  test inventory; generated TS types không thay runtime validation.
- MUST giữ error context hữu ích nhưng không echo secrets/source nhạy cảm. Không nuốt
  lỗi/return success; except rộng chỉ ở boundary có lý do, phân loại và báo lỗi đúng.
- Khi có network/worker call, MUST timeout/retry hữu hạn; kiểm tra idempotency trước
  retry để không chạy job hoặc tính phí lặp ngoài ý muốn.
- SHOULD chọn thư viện/cấu trúc sẵn có; dependency lớn cho helper nhỏ phải có lợi ích
  cụ thể. Không ép số dòng tối đa hoặc abstraction nếu code khó giải thích hơn.
- MAY để NotImplemented/README pending khi rõ chưa hỗ trợ; MUST không nối placeholder
  vào đường đi hiển thị thành công thật.

## Lý do

Giữ failure có thể chẩn đoán và code đủ rõ để người viết giải thích khi review.

## Ví dụ

Đúng: CLI trả exit 1 khi invalid report, không in input. Sai: `except Exception`
rồi trả report rỗng `completed`; thêm dependency chỉ để nối hai chuỗi.

## Kiểm chứng

Lint/typecheck, review error paths/timeout và test boundary liên quan. Check style
không đủ chứng minh semantics; không giảm rules hoặc cast qua unknown để che lỗi.

## Ngoại lệ

Compatibility với thư viện thiếu types MAY dùng adapter/cast nhỏ có comment và test.
Disable lint cục bộ cần lý do rule cụ thể, không disable cả file để pass. Nếu chạm
MUST hoặc thêm dependency ngoài scope, theo [00](00-governance.md) và [12](12-ci-dependencies.md).

## Liên quan

[03](03-contracts-api.md), [06](06-testing-quality.md), [07](07-debugging-change-control.md).
