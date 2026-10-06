# Dùng Agent Profiles và Project Rules với Codex

## 1. Bắt đầu đúng workspace

Mở thư mục có [AGENTS.md](../../AGENTS.md), [pyproject.toml](../../pyproject.toml) và
frontend/ trong IDE; máy hiện tại là D:\smart-regression-ai. Không mở riêng frontend/
rồi cho rằng toàn bộ hướng dẫn root đã có. Kiểm tra cwd và git status; workspace
này chưa có .git, nên không bịa branch/commit hoặc tự khởi tạo Git ngoài task.

Trong Codex, gửi prompt khởi đầu sau; thay task và paths theo việc được giao:

> Làm việc tại root SmartRegression AI. Trước khi sửa, xác định cwd/root và git status;
> nếu không có Git, báo giới hạn. Đọc AGENTS.md, tìm hướng dẫn áp dụng theo thư mục và
> mở profile/rule được định tuyến cho task này. Liệt kê đường dẫn file thực sự đã đọc,
> file chỉ thấy link nhưng chưa đọc và xung đột nếu có. Giữ thay đổi có sẵn. Task:
> kiểm tra docs/development/agent-rules-setup.md có links hợp lệ; chỉ sửa Markdown liên
> quan nếu cần, không đổi source, dependency, CI, không commit/push/deploy.

## 2. File nào được nạp

Tài liệu OpenAI mô tả Codex tìm hướng dẫn theo đường từ project root tới cwd; nếu
không tìm được root thì chỉ kiểm cwd. Điều này không có nghĩa mọi AGENTS ở thư mục
con đều được nạp. Hãy yêu cầu đọc tường minh file liên quan và bắt đầu phiên mới
khi cần kiểm lại hướng dẫn đã đổi. [Nguồn OpenAI về AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Quy ước của nhóm: docs/agents là role profiles, docs/rules là tài liệu phải mở theo
task, không auto-run hay quyền công cụ. Không tạo AGENTS.override.md để vô hiệu hóa
rule. Không chỉnh approval/sandbox hoặc tăng quyền toàn cục để tiện làm việc.
Nếu gặp chặn, báo action/lý do và phương án trong quyền hiện có.

Giới hạn xác minh: đã đọc nguồn official ngày 2026-10-06; chưa kiểm mọi IDE/client,
cấu hình global hoặc phiên bản Codex của thành viên. Câu trả lời “đã đọc” cần chỉ rõ
paths/nội dung liên quan, không tự chứng minh client nạp tất cả file.

## 3. Chọn profile và model

Chọn một profile chính từ [danh mục](../agents/README.md), rồi đọc rule theo bảng
AGENTS. Bugfix thêm rule 07; thay contract đọc rule 03 và các consumers; không đọc
toàn bộ 30 file cho một typo. Chín vai trò không yêu cầu chín người hoặc chín agents.

Nếu muốn dùng **GPT-6 Astra**, chọn model tương ứng trong giao diện/client của bạn
nếu tài khoản hiển thị; kiểm tra model đang chọn trước task. Tên file/profile/Markdown
không đổi model. Trang model chính thức xác nhận GPT-6 Astra, nhưng không chứng minh
quyền truy cập của tài khoản hay UI cụ thể của thành viên.
[Nguồn OpenAI về GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).

Không cần ghi model ID API hoặc sửa config để dùng bộ tài liệu này. Coding model
khác LLM provider/model của sản phẩm đang pending. Giao diện tích hợp giữa IDE có
thể khác nhau; tham khảo [hướng dẫn IDE chính thức](https://learn.chatgpt.com/docs/codex/ide)
và kiểm tra trực tiếp client đang dùng, không áp cách nạp file của client này cho mọi client.

## 4. Prompt mẫu có thể giao việc

Các ví dụ dưới đây là task mẫu, không phải lệnh yêu cầu triển khai toàn bộ ngay.
Điền [task brief](../templates/task-brief.md) nếu scope phức tạp hơn.

### Phát triển một chức năng nhỏ

> Dùng Frontend/Dashboard. Đọc AGENTS.md, profile và rules 02, 03, 06. Thêm vào
> ReportView khả năng hiển thị report_id và schema_version từ generated contract;
> thiếu version thì ghi chưa xác định. Chỉ sửa frontend/src và docs liên quan, không
> thêm API/dependency, không tự sinh dữ liệu. Giữ DEMO label, null semantics và layout
> hiện có. Acceptance: hai trường hiển thị đúng fixture, lint/typecheck pass; chạy
> build/smoke nếu được phép và báo chính xác phần bị chặn. Không commit/push/deploy.

### Sửa bug phạm vi nhỏ

> Dùng Backend/Contracts, đọc rules 03, 06, 07. Expected: CLI validate-report trả exit
> 1 với JSON sai contract và không echo input nhạy cảm. Xem code/tests, tái hiện trước;
> nếu đã đúng thì chỉ báo evidence. Nếu lỗi, sửa nhỏ trong CLI/application hoặc tests
> liên quan, không đổi public schema/exit code hoặc refactor toàn bộ. Chạy regression
> test phù hợp, ghi root cause/command/result/limits. Không commit/push/deploy.

### Review PR không sửa code

> Dùng Reviewer, read-only. Với diff/paths trong handoff tôi đính kèm, đọc AGENTS.md
> và rules của module. Kiểm contract consumers, demo/real, evidence/IDs, leakage và
> CI claims. Không sửa file, không approve/merge thay người. Findings P0–P3 phải có
> file/vị trí, trigger, tác động và confirmed/suspected; báo checks đã chạy và phần
> chưa review. Nếu không có Git/diff thật, nêu giới hạn thay vì giả lịch sử PR.

### Thay contract có consumers

> Dùng Backend/Contracts; đọc rule 03, 06 và consumer frontend. Task mẫu này cho phép
> thêm trường tùy chọn description vào AnalysisReport, không đổi meaning trường cũ.
> Trước khi sửa, liệt kê compatibility với extra=forbid, schema version và consumers.
> Nếu đây là breaking change cần version policy chưa quyết, trình bày phương án và
> làm phần khảo sát độc lập; không tự gán version mới. Trong phạm vi tương thích được
> xác định, sửa models, fixtures/tests cần thiết, tái sinh OpenAPI/types bằng công cụ
> rồi cập nhật consumer nếu cần. Không sửa generated file tay hoặc thêm dependency.
> Chạy schema/types và consumer checks, bàn giao migration/limits; không commit/deploy.

### Tiếp tục sau đổi phiên

> Tiếp tục task trong handoff tôi cung cấp, không bắt đầu lại dự án. Đọc AGENTS.md,
> profile/rules ghi trong handoff và actual files/diff; liệt kê đã đọc. Xác minh quyền
> đã giao, việc hoàn tất, pending và thay đổi người khác; đừng dựa chỉ vào summary cũ.
> Tiếp tục các bước còn lại trong paths đã giao, kiểm tra phần vừa sửa; không lặp tests
> toàn bộ nếu không có lý do mới. Nếu handoff thiếu input chặn task, nêu đúng phần thiếu
> và tiếp tục phần độc lập. Không tự commit/push/merge/deploy.

## 5. Bàn giao giữa thành viên

Tóm tắt bằng [handoff](../templates/handoff.md): task/branch/commit nếu có, file và
contract impact, commands/result thật, known issues/pending/next step và quyền còn
áp dụng. Không gửi transcript có secrets hoặc chép source riêng tư sang prompt khi
chưa có policy cho phép. Ghi self-review đúng tên; đổi profile không tạo reviewer độc lập.

Nhóm 5 người dùng [module ownership](module-ownership.md) làm đề xuất phân vùng, tự
gán người thực hiện/reviewer. Shared schema/lockfile cần một writer tại một thời điểm
hoặc phối hợp rõ; profile không tự bật agent song song.

## 6. Cập nhật rules và hướng dẫn cũ

Khi có ADR mới, link vào [decision register](decision-register.md), cập nhật đúng
rule chuyên đề và routing nếu cần; đánh dấu superseded ở nguồn cũ thay vì xóa dấu vết.
Không làm thêm bản contract hoặc danh sách commands độc lập. Cùng sprint nên rà file
trùng/lỗi thời; thay đổi đã giao hợp lệ không cần hỏi lại chỉ vì có docs impact.

Nếu hướng dẫn cũ mâu thuẫn: ghi paths/nguồn/điểm mâu thuẫn, đọc ADR/history nếu có,
giữ phần không phụ thuộc tiếp tục được. Với scope/security decision chưa rõ, đề xuất
phương án để người có trách nhiệm quyết; không coi code hoặc docs luôn đúng. Root
AGENTS đã định tuyến thay cho danh sách checks cũ; [commands](verified-commands.md)
là nguồn lệnh, [verification](verification.md) giữ lịch sử review trước.

## 7. Leader kiểm tra trước merge

- Scope/acceptance và quyền thực đã giao; không có rewrite/dependency/CI đổi ngoài task.
- Diff giữ công việc có sẵn; contract/consumers/fixture/generated artifacts đồng bộ.
- Người viết giải thích được phần AI hỗ trợ; review độc lập do người khác nếu nhóm yêu cầu.
- Checks thực và blockers, phân biệt CI configured với run pass/required checks.
- Không secrets/runtime artifacts/checkout bị stage; `.gitignore` không xóa file đã tracked.
- Research labels/cohort/mẫu số đúng, không demo thành result hoặc full-suite leakage.
- Quyền GitHub/settings được xác minh thật trước claim protected; merge bởi người được giao.

Các bước này là quy ước review, không tự thiết lập branch protection.
Gate còn thiếu và vai trò theo dõi ở [enforcement](../rules/14-enforcement.md).
