# Sprint 3 đợt 2 — Thiết kế tài khoản, dữ liệu web và giao diện

Ngày 15/11/2026 (UTC+7). Theo kế hoạch Huy giao; đây là thiết kế triển khai,
không phải phê duyệt mentor hoặc bằng chứng nghiệm thu browser. Bộ task web 75
mục dùng [audit](sprint-3-phase-1-audit.md), khác bộ 20 task nghiên cứu lịch sử.

## 1. Phần có implementation trong đợt 2

Auth routes `/api/v1/auth/*`, session PostgreSQL, Argon2id, signed double-submit
CSRF, token email/reset, Gmail SMTP, operator disable-account, React Router và
app shell. Backend models sinh OpenAPI/TypeScript; report schemas cũ giữ nguyên.
`GET /api/v1/capabilities` công bố cờ local demo để UI không trình bày nút demo
như chức năng dữ liệu tài khoản. Chưa có project CRUD hoặc personal report API.

| Bảng mới trong schema `smartregression` | Dữ liệu và constraint chính |
| --- | --- |
| `web_users` | UUID, normalized email unique, display name, Argon2id hash, verified, enabled, created_at |
| `web_sessions` | SHA256 token PK, user FK, expiry 7 ngày, revoked_at; index user |
| `web_account_tokens` | SHA256 token PK, user FK, purpose verify/reset, expiry, used_at; index user |
| `web_rate_limits` | Hash bucket key + window_start PK, attempts; atomic conditional UPSERT |

Migration `20261115_07` nối `20261109_06`; không sửa migration cũ. Users/tokens
không có xóa dây chuyền. Token mới vô hiệu hóa token cũ cùng purpose. Consume token
và cập nhật verified/password cùng transaction. Token reset không tự verified email.
Login recheck password hash/enabled dưới khóa user sau Argon2 verification; reset,
disable và các thao tác phiên dùng cùng thứ tự khóa user → session/token.

Runtime chỉ SELECT/INSERT/UPDATE trên bốn bảng auth, không DDL; migration identity
riêng. Không cấp thêm quyền lên research tables. Tài khoản disabled bị từ chối ngay
kể cả cookie chưa hết hạn. Không có public role/admin API.

CSRF có TTL 1 giờ, ký HMAC với secret server và ràng buộc session hiện tại. Login/
logout/password mutation rotate CSRF. Mọi API ghi yêu cầu Origin chính xác và CSRF.
Không tin forwarded IP khi chạy local; dùng `--no-proxy-headers`. Rate limit fixed
window: login 5/phút trên IP + email; register 5/giờ/IP; resend và forgot mỗi loại
3/giờ trên IP + email. Bucket keys đã hash, không lưu email/IP thô trong bảng limit.

Auth response có `schema_version=1.0.0`; errors có code ổn định, không echo input.
Session sai 401; CSRF/Origin sai 403; token sai/hết hạn 400; throttle 429/Retry-After;
DB/config tạm không khả dụng 503. API responses không cache. SMTP failure không
chuyển verified hoặc báo đã gửi; phản hồi request email vẫn trung tính.

## 2. Thiết kế dữ liệu các đợt sau — chưa tạo bảng

| Entity dự kiến | Quan hệ/ownership | Đợt triển khai |
| --- | --- | --- |
| Personal project | owner_user_id → web_users; URL repo, title, archive/version; tối đa 3 active/owner | 3 |
| Project run/report link | project + owner → project; liên kết compound repository_id/run_id tới catalog nghiên cứu; full SHA/config | 3 |
| Scenario | project/run + owner; input giả thuyết hoặc overlay tách static evidence; version bất biến | 5 |
| Note/reading state | project/run + owner; vị trí file/SHA, ghi chú, version | 4–6 |
| Activity | owner/project + loại thao tác, thời điểm, object reference; không lưu mật khẩu/token/prompt nhạy cảm | 3 trở đi |

Mọi query thực tế ở đợt sau phải lấy owner từ session, ràng buộc owner + parent ở
backend và kiểm tra cả export/download. Object khác owner trả 404 giống không tồn
tại. Run nghiên cứu cũ không tự thuộc một user mới; chỉ liên kết qua use case đã
kiểm quyền. Inventory nghiên cứu không đổi thành test case thủ công hoặc bảng user.
Mỗi migration mới nối head đã tích hợp, một writer; không tạo placeholder tables.

Trước nâng cấp DB có dữ liệu: backup bằng tài khoản vận hành, kiểm tra restore trên
DB riêng, chạy migration bằng migrator và smoke bằng runtime. Không tự migration
trong startup API. Các migration forward-only; phục hồi lỗi bằng backup, không giả
down migration sẽ khôi phục được dữ liệu. Harness kiểm tra populated upgrade và
fresh DB; phiên local đợt này dùng container riêng, không sửa database gốc.

## 3. Wireframe và design tokens

Tokens được triển khai bằng CSS variables trong `frontend/src/app/account.css`:
ink `#173b37`, sidebar `#102b29`, surface `#ffffff`, accent `#c5f3aa`, action
`#255c42`, border `#dce5dc`, muted `#536860`; base spacing 8px, card radius 16px.
Dùng font system hiện có, không tải font từ dịch vụ ngoài. Chữ/nền có phân cấp;
không chỉ dùng màu để biểu đạt verified/error/loading. Contrast thực tế/keyboard
vẫn cần browser inspection, không tự tuyên bố WCAG compliance.

| Màn hình | Bố cục thấp chi tiết, trạng thái và hành động |
| --- | --- |
| Auth desktop | Trái: brand + mô tả; phải: card form, label/error/hint, CTA, link chuyển form |
| Auth mobile | Brand gọn phía trên; một cột form; không ẩn field/hành động thiết yếu |
| Account | Sidebar đậm → header → email/verified badge → profile form → đổi mật khẩu khi verified |
| Projects, đợt 3 | Sidebar/header chung → title + tạo mới → project cards → empty/error/loading; chưa có CRUD trong đợt 2 |
| Explorer, đợt 4 | Sidebar → repo/SHA toolbar → tree / graph / inspector; mobile chuyển tabs thay vì ép ba cột |
| Dashboard, đợt 7 | Sidebar → bộ lọc repo/run/thời gian → counts có mẫu số → bảng drill-down → export; unknown không thành 0 |

Auth routes: `/login`, `/register`, `/check-email`, `/verify-email`,
`/forgot-password`, `/reset-password`; protected shell `/app`, `/app/account`.
`/app` chưa verified chuyển check-email. `/app/account` cho unverified xem/cập nhật
tên; đổi mật khẩu yêu cầu verified. Projects/dashboard chưa có: chỉ thông báo
phạm vi đợt 3, không hiển thị số liệu hoặc nút CRUD giả.

Các thành phần dùng lại: form fields/password reveal, FormNotice role status/alert,
cookie-session provider, route gate, native dialog xác nhận logout và style tokens.
Dialog có nhãn, Hủy là focus ban đầu và Escape đóng; native modal quản lý focus.
Link skip-to-content và focus heading sau navigation; error form không chép lỗi
raw server. Hỗ trợ password manager/paste, form busy/double-submit guard, reduced
motion. Bảng report hiện có giữ nguyên; không dựng một bộ component rỗng mới.

## 4. Email và các boundary cần kiểm chứng

Gmail SMTP cố định `smtp.gmail.com:587`, STARTTLS với certificate validation,
timeout 10s; không tự retry. Sender dùng App Password; recipient smoke mặc định
chính Gmail nhóm được cấu hình. Không có token hoặc mật khẩu trong log/bằng chứng.
SMTP acceptance không chứng minh thư đã đến Inbox.

Link dựng từ frontend origin tin cậy, không từ Host. Token ở URL fragment, frontend
đọc vào memory và xóa fragment; GET không consume. Người dùng xác nhận mới gửi POST.
Refresh sau khi xóa fragment cần mở lại link email; không cất token vào storage.
Resend có throttle và token cũ cùng purpose không còn dùng được.

Hai chế độ: `SMARTREGRESSION_WEB_MODE=local-demo` giữ các demo POST có Host/Origin
loopback; `product` không mount chúng. Vite giữ nguyên `/api/v1/*`, rewrite prefix
chỉ cho routes cũ. Khi backend offline, dev loopback vẫn mở `/demo` để đọc saved
report; bản production không tự bật demo do network failure. Logout không xóa
file report người dùng đã lưu nhưng xóa state tài khoản và unmount protected views.

Local cookies khác tên production. HTTPS cookies dùng prefix `__Host-`, Secure,
HttpOnly, SameSite=Lax, Path=/ và không Domain. Không dùng JWT/localStorage session.
Tài khoản mới không được gọi AI qua auth API; project/run/quota ở đợt 3.

## 5. Tính tương thích và kiểm chứng

Kiểm tra auth unit/API + PostgreSQL concurrency, migration metadata drift, quyền
runtime, fresh/populated upgrade, restart/restore; browser và Gmail thật ghi riêng.
Report consumers cũ và demo/import/export là regression bắt buộc khi đổi app shell.
Các dependency chỉ thêm pwdlib/Argon2, email-validator và React Router; lock bằng
công cụ. Zod dependency dev đã được vá tương thích, không ép nâng major minimatch.

Kết quả và pending thực tế: [bàn giao đợt 2](sprint-3-phase-2-handoff.md). Self-review
không thay independent approval. Không commit/push/merge/deploy trong task này.
