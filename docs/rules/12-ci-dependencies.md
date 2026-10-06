# 12 — CI/Dependencies

## Phạm vi

Manifest/lockfiles, runtime/tooling và workflow. Phân biệt
[source CI](../../.github/workflows/ci.yml) với [input-repo integration](../../integrations/github-actions/README.md).

## Yêu cầu

- MUST giữ manifest/lockfile nhất quán; uv/npm sinh lock, không viết tay. Chỉ đổi
  dependency theo task, không tự nâng major hoặc đổi stack để khớp tài liệu.
- MUST dùng CI quyền tối thiểu; source tests thông thường không yêu cầu API key thật.
  Cache phải phù hợp runtime/lockfile, không chứa secrets hoặc checkout repo đầu vào.
- MUST không vô hiệu hóa gate để merge nhanh. Diagnostic command khác full CI phải
  ghi là diagnostic, không thay bằng chứng full check.
- MUST chỉ ghi command đã đối chiếu implementation/tool vào
  [verified commands](../development/verified-commands.md); phân biệt xác minh định nghĩa
  với chạy pass. Không có script frontend test/e2e thì không invent npm test.
- Gate chưa triển khai ghi planned; workflow đã cấu hình chưa có run thì ghi configured,
  không active enforcement. Không khẳng định branch protection bật nếu chưa kiểm GitHub.
- SHOULD review package purpose, engines, transitive impact và warning khi cập nhật;
  MAY pin runtime phục vụ reproducibility theo ADR, không suy ra toàn bộ OS đã test.
- Bộ tài liệu này không tự tạo workflow/hook/settings. Gate còn thiếu chỉ ghi backlog
  ở [14](14-enforcement.md) cho task implementation sau.

## Lý do

Build tái lập được và CI chứng minh điều nó thực chạy, tránh “có YAML tức đã bảo vệ merge”.

## Ví dụ

Đúng: schema/types check có lệnh thật trong CI, vẫn ghi chưa có GitHub run.
Sai: docs ghi lint pass vì script tồn tại; giảm checks sau lỗi quyền local hoặc tự sửa lockfile.

## Kiểm chứng

Review engines/manifests/locks, scripts và CI run evidence; khi đổi dependency chạy
install locked và checks liên quan trên môi trường cho phép. Docs-only chỉ đối chiếu,
không reinstall hoặc nâng package.

## Ngoại lệ

Emergency dependency update đã được giao có thể thực hiện, phải ghi risk và checks
thiếu. Không dùng ngoại lệ để giả gate pass hoặc vượt GitHub permissions; theo [00](00-governance.md).

## Liên quan

[05 Git](05-git-pr.md), [06 Testing](06-testing-quality.md),
[10 Runner](10-runner-security.md), [14 Enforcement](14-enforcement.md).
