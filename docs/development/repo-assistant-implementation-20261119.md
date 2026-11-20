# Repository assistant: kế hoạch thực thi

Người dùng đã đọc và duyệt [proposal](repo-assistant-change-notifications-proposal-20261119.md),
giao lập kế hoạch chi tiết và thực thi ngày 19/11/2026. Đây là nguồn authorization
cho implementation local; không tự suy nghiệm thu nhóm hoặc mentor approval.

Baseline main `effd115`; branch `feat/repository-assistant-gemini-recovery-20261119`.
Source trước khi làm sạch, chỉ có file proposal mới; không reset/ghi đè công việc.

## Phạm vi và thứ tự

| Gói | Thiết kế thực thi | Gate trước khi hoàn tất |
| --- | --- | --- |
| 1. Contracts | Overview, thread/message, watch, notification, signed receipt; API mới additive | Pydantic, export OpenAPI/TS, consumer build và contract drift |
| 2. Grounding | Reading guide và lexical retrieval; lời hỏi nối tiếp dùng tối đa ba câu hỏi cũ; facts có SHA/path/range | Known-edge/non-edge, no-evidence, base deletion, scope boundary, parser identity |
| 3. Persistence | Migration `20261119_16`, năm bảng; snapshot FK cho thread; không lưu source excerpt trong message | PostgreSQL thật: upgrade, schema diff, owner isolation, lost-ack/replay, backup/restore |
| 4. Conversations | Static-first; AI metadata consent, source excerpt preview/consent riêng; quota dùng hạ tầng hiện có | Sai SHA/config, secret, invalid excerpt, busy/quota/provider error, retry |
| 5. Change monitoring | Một ref/watch mỗi project; paths người dùng chọn; manual check và polling worker; GitHub webhook đã ký đánh thức hàng đợi | Dedupe, force-push/out-of-order reconciliation, leased-job crash recovery, edit/archive races |
| 6. UI | Tab Trợ lý & thay đổi; onboarding tạo project mở trợ lý; Light/Dark, citation, diff, impact chain, read/unread | Browser desktop/mobile, keyboard/focus, stale requests, loading/error/empty/quota |
| 7. Acceptance | Unit/integration/contracts/build/browser; local migration có backup; worker riêng | Ghi số liệu và pending thực; không lấy mock thay live GitHub/provider |

## Những lựa chọn cụ thể

- Giữ public GitHub và Python impact; hỗ trợ JS Explorer hiện có không thành
  TypeScript hoặc quan hệ Python–frontend xuyên API.
- Watch lưu baseline SHA, branch, scope, optimistic version, next-check và lease.
  Polling mỗi 5–1.440 phút, mặc định 10 phút. Claim bằng row lock/skip locked;
  crash mất tiến trình được reclaim khi lease 10 phút hết hạn, kể cả manual job.
- Gộp sự kiện theo ref, resolve head hiện tại thay vì tin thứ tự webhook. Không
  cam kết lưu đủ lịch sử sự kiện hoặc quan sát branch tồn tại giữa hai lượt poll.
- Report đọc cả base và target; rename giữ dạng delete/add. Publish notification
  và advance baseline trong cùng transaction; version/lease guards chặn worker cũ.
- Webhook lưu delivery hash và projection giới hạn; raw source/payload không ghi
  log. Receiver dùng HMAC-SHA256, delivery UUID, repo/ref binding, không dùng CSRF.
- Notification không tự chạy source hoặc tự gọi AI cho mọi event. Người dùng mở
  kết quả và yêu cầu giải thích bằng quota; watcher không tiêu lượt AI ngầm.
- Thread giới hạn 100/project, 100 message/thread; list trả 30 thread mới nhất.
  Source snippets tái tạo theo SHA khi đọc; không lưu prompt/source bản sao trong
  chat. Có API xóa thread và message của chính owner. AI attempt/audit vẫn giữ.
- Retention snapshot phải bảo toàn tham chiếu từ thread/watch/notification; không
  xóa báo cáo nghiệp vụ để giải phóng cache.

## Model và ngân sách

User yêu cầu chuyển Gemini 3.8 Flash trong cùng phiên. Google Docs đã xác nhận
model ID `gemini-3.8-flash`, structured output và thinking `LOW`; `MINIMAL` không
được hỗ trợ. Web narrative/chat dùng 3.8; CLI/research policy lịch sử giữ model
3.5 Flash-Lite và không trộn cohort/ledger cũ.

Google công bố standard input/output của model 3.8 có Free Tier ngày 19/11/2026:
[model](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash),
[pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash),
[billing](https://ai.google.dev/gemini-api/docs/billing).
Account/project API tier thực tế chưa được xác minh. Gói Google AI Pro không tự
chứng minh API key thuộc Free Tier. Không bật billing hoặc đổi project Cloud.

User giao quyết định giới hạn kiểm chứng; chọn campaign mới tối đa 3 generation,
dự phòng tổng USD 0.06; không nới campaign cũ. USD reservation không phải invoice.
Ưu tiên synthetic/public data; không gửi thông tin cá nhân/source private. Chưa
gọi provider trong bước lập kế hoạch. Free tier vẫn cần cap token/lượt/time.

Narrator cap 8.192 input + 2.048 output/thinking, một generation mỗi admitted attempt. Bound
3.8 standard hiện tại là 13.824 micro-USD/lượt theo giá công bố tới 31/12/2026;
actual cost vẫn unknown. Chặn sau ngày này tới khi cập nhật bound/giá được kiểm
chứng. Không thêm Google Search/Maps/tools phát sinh chi phí.

Sau yêu cầu sửa 503, đã xác nhận phản hồi high-demand từ Google. ADR 0005 bổ sung
backoff 2s/4s + jitter, tối đa 3 attempt, mỗi attempt phải reserve riêng trong cùng
campaign. Tùy chọn fallback mặc định tắt, dùng 3.5 Flash-Lite ở lượt cuối khi được
cho phép. Một recovery campaign riêng có cap 3 / USD .06 được thông báo trước theo
quyền chọn budget user đã giao; không reset campaign cũ. Live recovery thành công
qua fallback, không chứng minh 3.8 đã hết quá tải. Tổng cap hai đợt 6 / USD .12;
actual billing unknown. Xem handoff cho evidence và checks cuối.

## UI direction và giới hạn vận hành

Theo [DESIGN](../../DESIGN.md): inset workspace, neutral/teal, system font, flat
panels và shared controls; ENERGY 1 / RHYTHM 2 / MOTION 1. Reading/conversation là
trọng tâm; watch và notifications hỗ trợ nhiệm vụ. Người dùng chọn áp dụng
antislop trong khi xây dựng. Không thêm UI library hoặc marketing charts.

Worker là process riêng: `python scripts/assistant/worker.py`, cùng cấu hình DB
runtime của backend. API tạo job bền vững, manual check có thể xử lý ngay bằng
background task; worker riêng tiếp tục các job tồn đọng và polling. Không chạy
migration trong startup. Máy tắt/worker dừng thì monitoring gián đoạn.

Local không tự nhận được webhook từ GitHub qua loopback. Receiver được kiểm chứng
synthetic trước; cài GitHub App/repository webhook và public HTTPS là bước vận hành
cần quyền thực tế. Không đăng ký hook, mua hạ tầng hoặc public deploy trong task này.

## Trạng thái kiểm chứng

Đã triển khai local và kiểm chứng theo [handoff](repo-assistant-handoff-20261119.md).
Live recovery qua model dự phòng đã thành công; 3.8 vẫn có trạng thái quá tải từ
Google. Webhook public chưa cài, GitHub anonymous quota đang hết. Checklist này
không thay nghiệm thu nhóm hoặc independent review.

Codex hỗ trợ thiết kế/code/tests/tài liệu. Nhóm chịu trách nhiệm review và hiểu
implementation theo Appendix C/D của Proposal; không giả review độc lập.
