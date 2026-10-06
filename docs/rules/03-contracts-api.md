# 03 — Contracts/API

## Phạm vi

Data models, API, CLI reports, provider/runner boundaries và frontend consumers.
Chi tiết schema hiện có giữ tại [contract docs](../contracts/README.md), không sao chép model ở đây.

## Yêu cầu

- MUST dùng [backend models](../../backend/src/smartregression/contracts/models.py)
  làm nguồn chuẩn, có schema_version; export/types bằng công cụ, không sửa generated file tay.
- MUST phân biệt repository identity, base/target commit, report/job/run ID và
  framework-native test ID. Hiện có report_id, **chưa có job/run model riêng**.
- Evidence MUST gắn commit/file/range/symbol khi có; schema pass chưa chứng minh vị trí
  tồn tại hoặc evidence hỗ trợ kết luận. Xem [09](09-impact-selection.md).
- Error MUST có mã ổn định và thông báo đã loại dữ liệu nhạy cảm. Unknown duration/cost
  là null/absent, không tự gán 0. Job/analysis status tách test outcome.
- Sửa schema MUST rà consumers/fixtures/exported types, optional/default/null và
  unknown-field behavior. Breaking change cần compatibility/version/migration rõ
  theo [00](00-governance.md); không mặc định additive là tương thích khi extra=forbid.
- Endpoint có job/retry/duplicate/cancel khi triển khai MUST định nghĩa semantics,
  idempotency và error state trước nối UI. Không thêm cancelled chỉ bằng cast frontend.
- SHOULD chọn shape tối thiểu phục vụ use case; MAY đề xuất extension trong ADR,
  không coi schema chưa có route là endpoint đã làm.

## Lý do

Ngăn producer/consumer lệch nhau và report làm người dùng hiểu sai mức đã phân tích/thực thi.

## Ví dụ

Đúng: đổi models → export → types → consumers/fixtures → checks. Sai: sửa generated.ts
để hết TypeScript error; gán runtime=0 khi worker chưa chạy hoặc report_id làm test ID.

## Kiểm chứng

CLI validation, pytest invalid cases, exporter --check, contracts:check và typecheck;
chạy consumer checks theo [verified commands](../development/verified-commands.md).
API smoke khi route thay đổi; ghi rõ validation runtime nào chưa tồn tại.

## Ngoại lệ

Prototype format khác chỉ dùng trong spike có nhãn, không xuất qua API/report chuẩn.
Đổi nguồn contract hoặc breaking migration ngoài task cần quyết định [00](00-governance.md).

## Liên quan

[04 Storage](04-data-storage.md), [06 Testing](06-testing-quality.md), [09 Selection](09-impact-selection.md).
