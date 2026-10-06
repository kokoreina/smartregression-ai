# 10 — Runner/Security

## Phạm vi

Ingest/clone/archive/checkout và thực thi test đầu vào khi các tính năng được triển khai.
Hiện chỉ có [runner Protocol](../../backend/src/smartregression/core/execution/ports.py);
quy tắc này không tuyên bố isolation đã tồn tại.

## Yêu cầu

- MUST coi repo đầu vào có thể chứa code không tin cậy. Không thực thi trong web API,
  dashboard hoặc môi trường có quyền deploy/production credentials.
- Test ID đã validate MUST không được coi là bằng chứng test code an toàn. Worker
  phải cô lập với giới hạn CPU/RAM/time/output, cleanup cả success/error/cancel.
- MUST không privileged mode, mount Docker socket hoặc gắn production secrets vào
  workload không tin cậy. Container đơn thuần không là bảo đảm cách ly tuyệt đối.
- MUST có network policy và dependency-install policy; install hooks cũng là code.
  Timeout/cancellation phải xử lý tiến trình con và tài nguyên, không chỉ đổi nhãn UI.
- MUST dùng argument list, không ghép input vào shell. Validate đường dẫn, scope
  workspace, symlinks và destination trước đọc/ghi/dọn artifacts.
- Khi có URL/redirect/archive ingestion, MUST xét SSRF/private destinations,
  path traversal, symlink escape và redirect policy; không coi validate URL ban đầu là đủ.
- GitHub events MUST gắn đúng commit/trust/permissions; fork PR không tự được cấp
  secret hoặc dùng workflow đặc quyền để chạy code không tin cậy.
- MUST phân biệt test failure, build failure, timeout, cancellation, infrastructure
  failure; không gộp thành fault detected. Contract cần mở rộng thì theo rule 03.
- SHOULD giữ artifacts tối thiểu và redact logs. MAY giới hạn MVP vào repo thử nghiệm
  nhóm đã duyệt nếu ghi rõ threat model/giới hạn, không quảng cáo hỗ trợ arbitrary repos.

## Lý do

Execution là boundary riêng có thể gây tác động ngoài ứng dụng; validation danh tính
không ngăn nội dung test phá môi trường.

## Ví dụ

Đúng: worker đã duyệt nhận danh sách IDs/commit, áp quota và trả lỗi timeout rõ.
Sai: API nối test ID vào shell command, mount host socket để “container chạy nhanh hơn”.

## Kiểm chứng

Trước triển khai runner: threat model và integration cases cho timeout/cancel/output
flood/path escape/cleanup/network. Test trên fixture an toàn trong môi trường được
giao quyền; chưa có worker thì ghi planned, không chạy exploit hay repo lạ để minh họa.

## Ngoại lệ

Repo đã duyệt có thể giảm bề mặt hỗ trợ, không tự cấp privileged mode/secrets.
Đổi security boundary cần quyết định rõ theo [00](00-governance.md); Markdown không
vượt sandbox/approval hoặc cấu hình quyền công cụ.

## Liên quan

[01 Architecture](01-architecture.md), [04 Storage](04-data-storage.md),
[09 Selection](09-impact-selection.md), [12 CI](12-ci-dependencies.md).
