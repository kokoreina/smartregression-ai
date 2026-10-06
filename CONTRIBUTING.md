# Đóng góp

Đọc [AGENTS.md](AGENTS.md), [setup](docs/development/setup.md) và
[workflow](docs/development/workflow.md). Tạo branch theo task: `feat/<task>`,
`fix/<task>` hoặc `docs/<task>`. Không làm trực tiếp trên nhánh chính.

PR nhỏ giải quyết một việc; trình bày đầu ra, giới hạn, cách kiểm chứng và schema impact.
Nhờ một thành viên khác review; đây là quy ước nhóm, chưa cấu hình branch protection.

Hoàn thành khi acceptance criteria được đáp ứng, checks liên quan pass, docs cập nhật,
không có secrets/generated runtime artifacts, và người viết hiểu phần AI hỗ trợ.
Schema thay đổi phải tái sinh artifacts, cập nhật fixture/test và giải thích compatibility.
Không merge khi chưa giải quyết review; không khẳng định một check pass nếu chưa chạy.
