# 05 — Git/PR

## Phạm vi

Working tree, branches, PR và hợp tác. Workspace hiện chưa có .git; quy trình áp dụng
khi maintainer tạo repo, không giả history/remote hoặc tự git init trong task khác.

## Yêu cầu

- MUST xem git status/diff trước sửa; nếu thiếu Git báo giới hạn và dùng snapshot
  để bảo toàn files. Không ghi đè thay đổi người khác vì tưởng là code lỗi của mình.
- SHOULD branch theo task và PR tập trung theo [CONTRIBUTING](../../CONTRIBUTING.md).
  MUST không dùng reset --hard/clean -fd/force push hoặc xóa working tree như cách sửa lỗi mặc định.
- MUST không tự commit/push/merge/deploy khi chưa được giao. Leader/người được nhóm
  giao merge theo quyền GitHub thật; vai trò trong Markdown không tạo quyền merge.
- PR MUST có mục đích, behavior trước/sau, kiểm chứng, rủi ro và contract impact;
  dùng [PR template](../../.github/pull_request_template.md), bổ sung risk ở mô tả khi cần.
- Khi làm song song, MUST phân công writer cho shared schema/lockfile/AGENTS rõ;
  không dùng chung working tree cho nhiều writer không phối hợp. MAY dùng worktree
  riêng khi task cho phép và Git có sẵn; không tự bật parallel agents chỉ nhờ profile.
- CODEOWNERS chỉ tạo khi biết username thật; required review không đồng nghĩa độc
  quyền merge. Markdown không cấu hình branch protection hoặc ruleset.

## Lý do

Giữ thay đổi truy vết được và tránh mất công việc/merge conflict do ghi chồng shared files.

## Ví dụ

Đúng: bàn giao models trước, người thứ hai tái sinh types sau khi tích hợp. Sai:
hai agent cùng sửa lockfile, sau đó reset cả repo để giải quyết conflict.

## Kiểm chứng

Review diff/staged paths, PR checklist và actual checks. Quyền/required checks chỉ
xác nhận bằng GitHub settings/run evidence khi được truy cập, không suy ra từ YAML.

## Ngoại lệ

Task tài liệu cục bộ chưa có Git không bị ép tạo branch; ghi rõ cách kiểm tra trước/sau.
Hoạt động phá hủy/chỉnh quyền cần authorization cụ thể và [00](00-governance.md),
không diễn giải quyền sửa bug thành quyền xóa thay đổi người khác.

## Liên quan

[07](07-debugging-change-control.md), [12](12-ci-dependencies.md), [14](14-enforcement.md).
