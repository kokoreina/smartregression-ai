# Backend/Contracts

## 1. Mục đích

Bảo vệ nguồn contract chuẩn và logic application chung cho API/CLI; producer và
consumer phải hiểu cùng dữ liệu, không tạo DTO frontend riêng mâu thuẫn backend.

## 2. Khi sử dụng

Sửa API, CLI validation, application orchestration hoặc schema/compatibility.

## 3. Input

Behavior mong muốn, contract hiện tại, consumers, fixture, compatibility yêu cầu,
task cho phép sửa những paths nào; job/runner chưa có phải giữ pending.

## 4. Paths thường phụ trách

[contracts](../../backend/src/smartregression/contracts),
[application](../../backend/src/smartregression/application),
[API](../../backend/src/smartregression/api), [CLI](../../backend/src/smartregression/cli),
[tests](../../backend/tests), [exporter](../../scripts/export_contracts.py).

## 5. Shared files

[models](../../backend/src/smartregression/contracts/models.py),
[OpenAPI](../../contracts/generated/openapi.json), [types](../../frontend/src/types/generated.ts),
[fixture](../../examples/reports/demo.json), pyproject/uv.lock. Phối hợp frontend và QA.

## 6. Được tự thực hiện

Sửa validation/route/application trong task, thêm regression test có ý nghĩa, tái
sinh schema/types khi thay đổi contract đã nằm trong scope. Không hỏi lại chỉ vì có consumer.

## 7. Ngoài phạm vi

Breaking change chưa được giao, persistence/job system mới hoặc đổi authentication
boundary cần đề xuất compatibility/migration trước; không đổi API để né bug nội bộ.

## 8. Các bước

1. Đọc model, callers và [quy ước schema](../contracts/README.md).
2. Khoanh behavior thay đổi và consumer bị ảnh hưởng.
3. Sửa nguồn chuẩn, test boundary; tái sinh artifacts bằng công cụ.
4. Kiểm tra types/fixtures/API/CLI liên quan; báo compatibility thực tế.

## 9. Edge cases

Sai version, default/optional/null, unknown fields, SHA sai, evidence dangling,
line range đảo, selected/skipped giao nhau, retry/duplicate/cancellation nếu endpoint có.
Contract hiện chưa có job ID/cancelled; không invent trường chỉ để hoàn thành UI.

## 10. Kiểm chứng

Ruff, pytest mục tiêu; CLI valid/invalid; exporter --check, contracts:check và frontend
typecheck khi đổi schema. Tên lệnh/cwd ở [verified commands](../development/verified-commands.md).

## 11. Output và hoàn thành

Model/consumer/fixture đồng bộ, lỗi trả mã ổn định không lộ input, migration nếu cần,
checks thật cùng giới hạn. Schema xuất hiện trong OpenAPI không có nghĩa endpoint tồn tại.

## 12. Prompt giao việc

> Dùng Backend/Contracts, đọc rule 03 và 06. Kiểm tra một report có evidence_id không
> tồn tại có bị từ chối hay không. Tái hiện trước; nếu lỗi, sửa nhỏ trong models và
> backend/tests, giữ API shape. Nếu đã đúng, báo bằng chứng, không sửa cho có. Chạy test
> liên quan và schema check; không thêm endpoint hoặc dependency.

## 13. Bàn giao

> Behavior trước/sau: …; nguồn model: …; consumers: …; artifacts sinh lại: …;
> compatibility/version: …; lệnh/kết quả: …; chưa kiểm chứng/pending: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[01](../rules/01-architecture.md), [02](../rules/02-coding-standards.md),
[03](../rules/03-contracts-api.md), [06](../rules/06-testing-quality.md).
