# 07 — Debugging/Change Control

## Phạm vi

Bugfix, lỗi setup/build/integration và quyết định có cần refactor.

## Yêu cầu

1. MUST ghi expected/actual, điều kiện và môi trường.
2. MUST tái hiện hoặc nói rõ bằng chứng chưa đủ; không gắn nhãn confirmed khi chỉ nghi ngờ.
3. Khoanh root cause, liệt kê giả thuyết có evidence và phép kiểm phân biệt chúng.
4. Sửa nhỏ nhất giải quyết nguyên nhân trong phạm vi được giao.
5. Kiểm tra failure path và luồng liên quan; regression test nếu phù hợp [06](06-testing-quality.md).
6. Báo nguyên nhân, file đổi, kết quả và giới hạn kiểm chứng.

- MUST không rewrite module vì chưa hiểu, refactor diện rộng trong bug nhỏ, đổi public
  API để né sửa lỗi nội bộ hoặc hoàn tác cả tree để gỡ một thay đổi của mình.
- MUST không lặp nhiều vòng sửa đoán khi không có evidence mới; dừng phần phụ thuộc,
  thu log/tạo reproduction/đề nghị input cụ thể, tiếp tục phần độc lập nếu có.
- SHOULD giữ refactor lớn thành task/ADR riêng với migration/rollback thích hợp;
  MAY chỉnh tên/helper nhỏ khi cần cho fix và diff vẫn giải thích được.

## Lý do

Giữ cause/effect có thể review và giảm rủi ro bugfix tạo lỗi ngoài scope.

## Ví dụ

Đúng: TS error do generator default semantics, sửa option và sinh types lại.
Sai: xóa contract hoặc cast qua unknown chỉ để compiler im lặng; đổi Vite sang framework
khác khi lỗi thực là sandbox không cho spawn esbuild.

## Kiểm chứng

[Bug report](../templates/bug-report.md) ghi reproduction và mức chắc chắn;
so sánh diff trước/sau và commands đã chạy. Log chỉ chứa dữ liệu đã loại secret.

## Ngoại lệ

Fix cần refactor lớn có thể làm khi user đã giao rõ phạm vi đó; ghi acceptance,
migration/risk trước triển khai. Nếu chưa giao thì đề xuất theo [00](00-governance.md),
không xin phép lại từng sửa cục bộ đã được phép.

## Liên quan

[02 Coding](02-coding-standards.md), [05 Git](05-git-pr.md), [06 Testing](06-testing-quality.md).
