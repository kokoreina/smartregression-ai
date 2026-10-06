# Frontend/Dashboard

## 1. Mục đích

Hiển thị report/trạng thái/evidence/selection/execution đúng contract, không tự suy
ra metric nghiệp vụ hoặc nhãn an toàn từ số test pass.

## 2. Khi sử dụng

Sửa UI report, health connection, loading/error hoặc nối consumer vào API đã có.

## 3. Input

Behavior UX, generated types, endpoint thật/fixture hợp lệ, trạng thái backend hỗ trợ,
ảnh hoặc bước tái hiện nếu có. Không biến mock thành response production.

## 4. Paths thường phụ trách

[app](../../frontend/src/app), [features](../../frontend/src/features),
[components](../../frontend/src/components), [lib](../../frontend/src/lib).
Repositories/analyses hiện chỉ có README; dashboard chỉ hiển thị DEMO và health.

## 5. Shared files

[generated types](../../frontend/src/types/generated.ts),
[demo fixture](../../examples/reports/demo.json), [generator](../../frontend/scripts/contracts.mjs),
backend models, package/lockfile nếu task dependency cho phép.

## 6. Được tự thực hiện

Sửa component/style/data handling trong scope, giữ accessibility và responsive;
thêm test phù hợp bằng công cụ sẵn có. Đổi fixture phải qua backend validation.

## 7. Ngoài phạm vi

Thêm endpoint/job, tự tính fault retention, đặt enum mới hoặc nhúng API key; đề xuất
contract với backend trước. Không cài UI/test framework mới chỉ để sửa lỗi nhỏ.

## 8. Các bước

1. Đọc type và actual response; phân biệt dữ liệu demo/mock/real.
2. Map trạng thái có thật, unknown/null hiển thị chưa đo/chưa biết.
3. Thiết kế loading, empty, partial, error, cancelled và demo cho feature phù hợp.
4. Typecheck/build và smoke luồng liên quan; ghi trạng thái chưa được backend hỗ trợ.

## 9. Edge cases

API offline nhưng DEMO vẫn đọc được; response sai version; long paths; no findings;
partial report; null cost; empty selection khác no risk; stale requests khi unmount.
`cancelled` chưa có trong contract: ghi pending, không cast để giả hỗ trợ.

## 10. Kiểm chứng

Frontend lint/typecheck/build, contracts:check khi dùng schema; CLI validate nếu đổi
fixture; smoke UI loading/error/empty và keyboard khi chạy được. Không coi typecheck là e2e.

## 11. Output và hoàn thành

UI khớp backend, DEMO rõ, evidence đúng commit/range, trạng thái test tách analysis,
không rò secret; báo chính xác browser/build nào chưa chạy.

## 12. Prompt giao việc

> Dùng Frontend/Dashboard, đọc rule 03 và 06. Kiểm tra health offline trong App.tsx:
> DEMO phải vẫn hiển thị và nút thử lại phản ánh kết nối thật. Chỉ sửa frontend/src nếu
> tái hiện lỗi; giữ fixture/schema/dependency. Chạy lint/typecheck, smoke nếu môi trường
> cho phép; báo không chạy được thay vì khẳng định pass.

## 13. Bàn giao

> Component/behavior: …; contract/fixture: …; states đã kiểm: …; browser/checks: …;
> states pending: …; screenshot nếu có (không bắt buộc): …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[02](../rules/02-coding-standards.md), [03](../rules/03-contracts-api.md),
[06](../rules/06-testing-quality.md), [13](../rules/13-documentation-ai-use.md).
