# Review report

## Phạm vi

- Task/PR/diff/paths:
- Base/target/commit nếu có:
- Hướng dẫn/contract/ADR đã đọc:
- Chế độ: read-only / được giao sửa những phần nào:
- Self-review hay review bởi người khác thực tế:

## Findings (xếp theo mức độ)

P0: cần xử lý ngay vì tác động nghiêm trọng đang xảy ra (ví dụ lộ secret/mất dữ liệu).
P1: chặn luồng chính hoặc correctness nghiêm trọng. P2: lỗi đáng sửa có điều kiện/
phạm vi hạn chế. P3: cải thiện nhỏ, không biến sở thích style thành blocker.
Severity là tác động; confirmed/suspected là độ chắc chắn, phải ghi riêng.

### Finding

- Mức độ và confirmed/suspected:
- File/vị trí chính xác:
- Trigger/bước tái hiện:
- Expected/actual:
- Bằng chứng (source/log/test đã loại secret):
- Tác động và đối tượng bị ảnh hưởng:
- Lỗi có sẵn hay do thay đổi mới, hoặc chưa biết:
- Đề xuất sửa nhỏ; nếu nghi ngờ thì phép kiểm cần thêm:

Lặp finding khi cần; không có finding thì nói chưa phát hiện, không cam kết không còn lỗi.

## Kiểm chứng và giới hạn

- Commands/cwd/result thật:
- Phần chưa review/chưa chạy:
- Contract/CI/permission chưa xác minh:
- Đã sửa gì (chỉ nếu được giao), checks chạy lại:
- Điều kiện còn thiếu trước merge/sprint:

Reviewer profile không là quyền approve/merge hoặc review độc lập tự động.
