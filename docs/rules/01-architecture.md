# 01 — Architecture

## Phạm vi

Thay code/module boundary hoặc orchestration; nguồn kiến trúc ở
[overview](../architecture/overview.md) và [ADR 0001](../architecture/decisions/0001-bootstrap.md).

## Yêu cầu

- MUST giữ hướng entrypoints/API/CLI → application → core/interfaces; adapters
  triển khai interfaces. Contracts dùng chung không import entrypoint.
- Core MUST NOT import FastAPI, React hoặc SDK LLM. Pydantic ở contracts hiện là
  lựa chọn có sẵn; không tự tách framework model thành kiến trúc mới ngoài task.
- API/CLI MUST dùng chung logic nghiệp vụ trong application; parsing HTTP/arguments
  nằm ở entrypoint. Composition root chịu trách nhiệm nối implementation/config.
- MUST giữ runner ngoài tiến trình web; một repo code không đồng nghĩa một process.
- SHOULD thêm interface khi có boundary/consumer thật; không tạo hàng loạt lớp rỗng,
  microservices, broker hoặc plugin framework cho nhu cầu chưa chứng minh.
- MAY giữ README-only cho module pending; MUST phân biệt thiết kế proposed với
  implementation đã tồn tại và quyết định đã accepted.

## Lý do

Nhóm fresher có thể hiểu và test từng lớp, thay adapter mà không gắn core vào provider.

## Ví dụ

Đúng: route gọi application use case, adapter implement port được inject ở root.
Sai: core/selection import app FastAPI hoặc gọi SDK trực tiếp; route dùng shell chạy repo test.

## Kiểm chứng

Review imports/call graph và tests boundary; [runner port](../../backend/src/smartregression/core/execution/ports.py)
hiện chỉ Protocol. Chưa có architecture lint tự động; không tuyên bố CI kiểm tra dependency direction.

## Ngoại lệ

Thay boundary cần ADR với consumer/migration impact và quyết định theo
[00](00-governance.md); không dùng refactor nhỏ để hợp thức hóa execution trong API.

## Liên quan

[02 Coding](02-coding-standards.md), [03 Contracts](03-contracts-api.md), [10 Runner](10-runner-security.md).
