# Sprint 3 — Contracts nền và bàn giao auth cho đợt 2

**Cập nhật đợt 2, 15/11/2026:** contracts bên dưới đã có implementation local;
xem [auth design](sprint-3-auth-design.md) và [handoff](sprint-3-phase-2-handoff.md).
Các câu “sẽ triển khai” là thời điểm chốt brief đợt 1; owner/project/run/quota vẫn
thuộc các đợt sau. Auth backend pass không thay Gmail/browser/staging acceptance.

Ngày: 15/11/2026, UTC+7. Theo phạm vi tám đợt Huy đã giao; đây là quyết định thiết kế
để triển khai tiếp, không phải bằng chứng auth/project đã có. Task 3.02/3.04/3.46
mới hoàn thành phần nền; trạng thái từng task nằm trong [audit 75 task](sprint-3-phase-1-audit.md).

## 1. Luồng đang triển khai ở đợt 1

| Interface thật | Input / output | Ranh giới |
| --- | --- | --- |
| POST `/repositories/inspect` | Public HTTPS GitHub URL → overview và tối đa 10 commit | Loopback Host/Origin, JSON body cap; không code execution |
| POST `/repositories/tree` | URL + full target SHA → cây có tree SHA và loại entry | Tối đa 5.000 entry/2 MB metadata; truncated là lỗi rõ |
| POST `/repository-analyses` | URL + base/target SHA + AI opt-in/consent/question → full response | Snapshot read-only, static Python; selection/execution luôn not_run |
| JSON local `RepositoryReportExport` | `report_kind=repository-analysis`, `schema_version=1.0.0`, timezone-aware `exported_at`, full `payload` | Không phải API download owner-protected; không phải PostgreSQL history |

Vite `/api` chỉ là proxy development: `/api/repository-analyses` được rewrite về
`/repository-analyses`. Không nhầm với namespace API sản phẩm `/api/v1` ở đợt 2.
Giữ các routes cũ để tương thích local. Không public backend này ra Internet.

Backend `contracts/repository.py` là nguồn canonical, OpenAPI và TypeScript sinh
bằng exporter. Thay validator liên trường vẫn phải chạy consumer tests; schema
shape không thay thế checks. `real` response phải có repo URL/full_name khớp và
repository_id = `github-` + SHA256(lowercase owner/repo). V2 report kiểm tra các
snapshot/evidence references nội bộ. Điều này phát hiện ghép nhầm repo; file local
không có chữ ký và không được coi là dữ liệu đã xác thực từ một server tin cậy.

Repo, base/target SHA, snapshot, run_id và report_id là các định danh khác nhau.
Giữ identity từ báo cáo đã chạy, không lấy từ form đang chỉnh. Metadata citations
được giải nghĩa trong phạm vi run có SHA rõ; không biến citation membership thành
bằng chứng correctness của toàn bộ nhận định. Import hỗ trợ export envelope mới
và legacy full response hợp lệ. Canonical stage-v2 import cũ giữ reader riêng.

Trạng thái `narrative`: completed có data và không có error/reason; failed có
error_code và không có data/reason; not_run không có data/error. Usage token phải
là integer không âm; duration/cost hữu hạn không âm. Unknown là null/absent,
không tự thành 0. Từ chối usage keys/error enums ngoài contract. AI failure vẫn
hiển thị static report, không suy ra tests pass hoặc không có rủi ro.

## 2. Chính sách AI được chốt cho đợt 1

- Mặc định UI là phân tích tĩnh; bật AI là thao tác chủ động riêng.
- Metadata gồm repo, SHA/snapshot, paths, symbols, import/impact observations và
  câu hỏi. Không tự gửi source/comments/excerpts; chưa hỗ trợ excerpt consent.
- Câu hỏi cũng là dữ liệu được gửi: người dùng không nhập key/secret hoặc source
  riêng tư. Backend chặn các mẫu credential đã nhận diện trước khi tải repo/gọi
  provider bằng bộ lọc đang dùng cho retrieval; không echo câu hỏi. Đây không phải
  hệ thống DLP phát hiện mọi secret.
- Nội dung repo/câu hỏi là dữ liệu không tin cậy, không có quyền thay system
  instruction, budget, tools hoặc evidence validation. Provider không được chạy
  tool/call code và không tự retry generation.
- Giữ 8.192 input tokens, 2.048 output/thinking, count timeout 5s,
  generation 15s và outer deadline 25s. Repo acquisition có deadline riêng.
- Giữ session tối đa 5 runs, 0,02 USD/run, 0,10 USD/session; reservation unknown
  không phải invoice. Không reset hoặc đổi session ID để né giới hạn.
- Ledger hiện 5/5: đợt 1 không gọi mới. Dùng report thật đã lưu, ghi thời điểm
  xuất riêng, thời điểm phân tích thiếu thì unknown. Live smoke 3.13 vẫn pending.
- Các feature AI tiếp theo dùng cùng chính sách, thêm consent theo loại dữ liệu
  nếu được triển khai. Tài khoản mới quota=0; operator cấp qua cấu hình server,
  không có public admin role hoặc tự cấp quota từ frontend.

## 3. Đặc tả auth để bắt đầu đợt 2

Giữ FastAPI/application/adapters/PostgreSQL và React hiện có. Chưa thêm bảng,
dependency hoặc endpoint auth trong đợt 1. Đợt 2 thêm migration additive cho users,
sessions và purpose-scoped verification/recovery tokens; giữ schema nghiên cứu.
Email chuẩn hóa strip/lower và unique. Không lưu hoặc log mật khẩu/token thô.

### API tối thiểu sẽ triển khai

| Method / path dưới `/api/v1` | Hành vi / quyền |
| --- | --- |
| GET `/auth/csrf` | Cấp signed CSRF token cho form; không cấp user session đăng nhập |
| POST `/auth/register` | Email/password/display_name, tạo unverified; phản hồi 202 trung tính cả email đã tồn tại |
| POST `/auth/login` | Credentials đúng → rotate opaque session và CSRF; trả safe current-user view |
| POST `/auth/logout` | Thu hồi session hiện tại, xóa cookies và client state |
| GET `/auth/me` | 401 nếu chưa đăng nhập, trả id/email/display_name/verified của chính session |
| PATCH `/auth/me` | Chỉ sửa display_name; email change và roles ngoài phạm vi |
| POST `/auth/verify-email` | Purpose-scoped token TTL 24h, single-use, không echo token |
| POST `/auth/resend-verification` | 202 trung tính; rate-limit, không giả verified khi gửi email thất bại |
| POST `/auth/forgot-password` | 202 trung tính, không tiết lộ email; recovery token TTL 1h |
| POST `/auth/reset-password` | Token đúng purpose/single-use; đổi password và revoke mọi session cũ |
| POST `/auth/change-password` | Session + current password, đổi hash; revoke sessions và yêu cầu login lại |

Mật khẩu 12–128 ký tự, không trim; Argon2id qua thư viện chuẩn
`pwdlib[argon2]` khi triển khai đợt 2, pin/lock bằng công cụ theo rule 12. Không
tự viết password hashing. Sessions dùng random opaque token >=256 bit; DB chỉ lưu
hash, user FK, created/expiry/revoked. Expiry tuyệt đối 7 ngày; logout, disable và
password reset/change thu hồi. Username/password không đưa vào log/error response.

Cookie HTTPS: `__Host-sr_session`, HttpOnly, Secure, SameSite=Lax, Path=/,
không Domain. Local HTTP chỉ dùng tên development riêng, Secure=false theo cấu
hình loopback rõ ràng; không áp ngoại lệ đó cho staging.

CSRF: signed double-submit token trong cookie riêng và `X-CSRF-Token`, bound vào
session khi có; ký HMAC bằng server secret, so sánh constant-time, rotate khi
login/logout. Mọi thao tác ghi kể cả login/register yêu cầu token + Origin chính
xác. Không dùng token làm bearer auth và không bật credentialed CORS wildcard.

Giới hạn backend ban đầu: login 5 lần/phút trên cả IP và normalized account;
register 5 lần/giờ/IP; resend/reset request 3 lần/giờ trên IP và email; trả 429
cùng Retry-After. Lưu/thực thi atomically trong PostgreSQL; không thêm Redis.
Lỗi login/forgot dùng thông báo trung tính. Session sai/hết hạn 401, CSRF sai 403,
unverified truy cập nghiệp vụ 403 `email_verification_required`.

Đăng nhập unverified được phép chỉ để xem account, verify/resend/logout. Chưa
verified không tạo project hoặc chạy AI. Token email là random >=256 bit, DB
lưu hash/purpose/expiry/used_at; consume transactionally. SMTP/config secrets ở
server; gửi lỗi không đánh dấu sent/verified. UI chỉ khẳng định đã nhận yêu cầu,
trạng thái delivery thật phải tách riêng; SMTP/staging thiếu là prerequisite còn
thiếu, không đưa token ra API/log để giả email thành công.

## 4. Owner isolation và chuyển tiếp sang đợt 3

Các routes `/projects`, project runs/history, scenarios/notes/dashboard/export mới
đều dưới `/api/v1`, lấy owner từ session. Input owner_id/user_id không cấp quyền.
Không có membership/invite/role quản trị công khai. Tối đa 3 active projects/owner;
project có lịch sử dùng archive, archived không tạo run mới. Lookup object khác
owner hoặc không tồn tại cùng trả 404; chưa login trả 401 trước truy vấn dữ liệu.

Mọi nested lookup gắn owner + parent project. Download/export kiểm quyền như read.
Ngăn client gắn run của project B vào project A. Khi auth/staging được bật, legacy
local POST routes phải disabled trên public deployment (404), không làm alias
bypass session/quota. Đây là gate bắt buộc của 3.43, không phải đã triển khai.

Ownership ma trận theo [audit](sprint-3-phase-1-audit.md): với **mỗi task tạo API**,
ghi object/parent và user A/B, chưa login, unverified, owner spoof, guessed ID,
archived project, wrong SHA/config, stale version, export scope. Auth có token
expiry/wrong purpose/replay/revoke/concurrent consume; quota có reserve race và
unknown charges; report reader có wrong repo/SHA/citation. Đây là cases phải thực
thi ở đợt tương ứng; hiện tại không báo owner enforcement đã pass.

## 5. Điều kiện bàn giao

Auth DTO chỉ sinh khi bắt đầu implementation với consumer thật; cập nhật exporter,
generated TS và valid/invalid fixtures cùng PR. Test bằng PostgreSQL thật cho
session/token/uniqueness/transactions; mock SMTP cho deterministic cases và tách
SMTP thật khỏi unit suite. Browser kiểm tra đăng ký → email thật khi cấu hình có →
verify → login → logout; không dùng cookie trong localStorage.

Đợt 2 có thể bắt đầu từ đặc tả này dù browser acceptance của demo đợt 1 còn chặn;
không đồng nghĩa task đợt 1 hay toàn Sprint 3 đã Done.
