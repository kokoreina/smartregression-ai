# Chạy SmartRegression trên máy thành viên

Hướng dẫn cho checkout có tính năng Repository Assistant, ngày 19/11/2026.
Mỗi máy có database, tài khoản, API key và quota riêng; clone Git không sao chép
cấu hình hoặc dữ liệu trên máy Khánh. Chạy các lệnh tại thư mục gốc repository.

## 1. Lấy source và cài dependencies

Cần Git, Python 3.14.x, uv, Node.js 22.14+ thuộc dòng 22, npm 10+ và Docker Desktop
đang chạy Linux containers. Trước khi PR được merge:

```powershell
git clone --branch feat/repository-assistant-gemini-recovery-20261119 https://github.com/kokoreina/smartregression-ai.git
Set-Location smartregression-ai
uv sync --locked
npm --prefix frontend ci
```

Sau khi nhóm merge PR, thay tên nhánh ở lệnh clone bằng `main`. Nếu đã có clone,
kiểm tra `git status`, lưu công việc của mình trước khi đổi nhánh; không xóa repo
hoặc reset thay đổi local để cập nhật. Không dùng đường dẫn `D:\C1.SE26\Repo` của
máy Khánh nếu máy mình clone ở vị trí khác.

## 2. Điền Gemini API key ở đâu?

Lấy API key cho Google API project của mình tại
[Google AI Studio](https://aistudio.google.com/api-keys). Dùng file
[`backend/.env.example`](../../backend/.env.example) làm mẫu:

```powershell
Copy-Item -LiteralPath backend/.env.example -Destination backend/.env
notepad backend/.env
```

Chỉ copy lần đầu khi chưa có `backend/.env`; nếu đã có thì mở file hiện có để sửa.
Trong file đó, điền key thật sau dấu `=`:

```dotenv
GEMINI_API_KEY=YOUR_GOOGLE_AI_STUDIO_API_KEY
```

`YOUR_GOOGLE_AI_STUDIO_API_KEY` là placeholder, phải thay bằng key của mình.
Không dán key vào frontend, biến `VITE_*`, source, PR hoặc ảnh chụp. Kiểm tra
`git check-ignore backend/.env` phải trả về `backend/.env`. File mẫu được commit,
file chứa key thật được Git ignore.

Backend không tự tìm `.env`: phần chạy server bên dưới đặt
`SMARTREGRESSION_GEMINI_ENV_FILE` trỏ đúng file này. Nếu shell đang có
`GEMINI_API_KEY` hoặc `GOOGLE_API_KEY` khác với file, loader báo xung đột; chọn
một nguồn key thống nhất rồi khởi động lại backend. Không cần điền API key vào UI.

Web dùng `gemini-3.8-flash`; form cho phép chọn fallback sang
`gemini-3.5-flash-lite` khi gặp 503. Đổi tên model tùy ý trong `.env` không thay
đổi policy trong source. Google AI Pro và Google API billing/quota là hai phần
riêng; kiểm tra API project của mình, không mặc định mọi lời gọi đều miễn phí.

## 3. Chuẩn bị database và email cho đăng ký

```powershell
$env:PYTHONPATH = 'backend/src'
.\.venv\Scripts\python.exe scripts/auth/prepare_local.py
$env:SMARTREGRESSION_WEB_ENV_FILE = (Resolve-Path 'var/auth/web.env').Path
.\.venv\Scripts\python.exe scripts/auth/migrate_local.py
notepad var/auth/web.env
```

`prepare_local.py` tạo PostgreSQL local riêng, ghi cấu hình dưới `var/auth/` được
Git ignore. `migrate_local.py` backup, nâng tới migration `20261119_16` và cấp quyền
runtime cho các bảng sản phẩm. Giữ nguyên URL/password database và CSRF secret
được sinh. Không copy file riêng của thành viên khác hoặc database đang deploy.

Để nhận email xác thực và khôi phục mật khẩu, điền hai dòng sẵn có trong
`var/auth/web.env`:

```dotenv
SMARTREGRESSION_SMTP_USERNAME=YOUR_GMAIL_SENDER_ADDRESS
SMARTREGRESSION_SMTP_PASSWORD=YOUR_GMAIL_APP_PASSWORD
```

Dùng Gmail có xác minh hai bước và App Password, không dùng mật khẩu đăng nhập
Gmail. Không gửi file này vào Git/chat. Tài khoản ở website deploy không tồn tại
sẵn trong database mới: đăng ký và xác thực tài khoản local qua email.

## 4. Chạy frontend, backend và worker

Mỗi terminal mở tại thư mục gốc clone của mình. Terminal backend:

```powershell
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = (Resolve-Path 'var/auth/web.env').Path
$env:SMARTREGRESSION_GEMINI_ENV_FILE = (Resolve-Path 'backend/.env').Path
$env:SMARTREGRESSION_WEB_MODE = 'product'
.\.venv\Scripts\python.exe -m uvicorn smartregression.api.main:app --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

Terminal frontend:

```powershell
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Terminal worker, cần giữ chạy khi bật tự theo dõi GitHub:

```powershell
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = (Resolve-Path 'var/auth/web.env').Path
.\.venv\Scripts\python.exe scripts/assistant/worker.py
```

Mở `http://127.0.0.1:5173`, đăng ký/xác thực email, đăng nhập, tạo dự án bằng URL
GitHub public rồi mở **Trợ lý & thay đổi**. Không thay `127.0.0.1` bằng `localhost`
khi dùng cấu hình origin này. Dừng bằng Ctrl+C; giữ database để bảo toàn dữ liệu.
Khởi động lại backend sau khi đổi cấu hình. Đây là setup loopback, không phải
hướng dẫn public deployment.

## 5. Key hợp lệ nhưng AI vẫn báo hết quota?

Ứng dụng chủ động để quota AI của tài khoản mới bằng 0. Đây là quota nội bộ,
khác quota của Google. Tra cứu tĩnh và xem bằng chứng vẫn dùng được khi không
bật **Dùng Gemini**. Bật key không tự cấp lượt AI hoặc reset ngân sách cũ.

Cho database local mới dùng để kiểm chứng, người vận hành có thể dùng script
đã có, cấp tối đa **10 lượt generation / USD 0.20 dự phòng** cho đúng tài khoản
đã xác thực có email bằng `SMARTREGRESSION_SMTP_USERNAME`:

```powershell
$env:PYTHONPATH = 'backend/src'
$env:SMARTREGRESSION_WEB_ENV_FILE = (Resolve-Path 'var/auth/web.env').Path
.\.venv\Scripts\python.exe scripts/auth/grant_acceptance_ai.py
```

Đây là bước cấp quyền có chủ đích, chỉ chạy khi đã chốt giới hạn kiểm chứng;
script không gọi Google. Nếu muốn dùng script này trên máy mới, đăng ký và xác
thực tài khoản local bằng chính email sender đã cấu hình. Script giữ campaign
nghiệm thu lịch sử, chạy lại không cấp thêm lượt. Không dùng để nới ngân sách
đã tiêu trên máy Khánh, không sửa/xóa ledger hoặc tạo lại DB để lách quota.
Tài khoản khác cần người vận hành cấp grant phù hợp; UI không có chức năng tự cấp.
USD dự phòng là giới hạn ứng dụng, không phải hóa đơn Google và không tự bật billing.

Sau khi có grant, nhập câu hỏi, bật **Dùng Gemini**, xem và đồng ý riêng nếu gửi
trích đoạn source, rồi gửi. Mỗi lượt retry 503 cũng tiêu lượt riêng, tối đa 3 lượt
cho một câu hỏi. UI hiển thị model thực sự trả lời. Fallback mặc định tắt.

## 6. Các lỗi thường gặp

| Hiện tượng | Kiểm tra |
| --- | --- |
| `provider_configuration` | File `backend/.env`, tên `GEMINI_API_KEY`, biến đường dẫn trong terminal backend, xung đột key giữa file và process; restart backend. |
| `provider_auth` / `provider_permission` | Key/API project, quyền và điều kiện truy cập model trên Google AI Studio. |
| Google 429/quota | Quota API project và model; grant nội bộ không thay được giới hạn Google. |
| Gemini 503 | Server model tạm quá tải; có backoff trong quota, hoặc bật fallback. Không bảo đảm 3.8 luôn sẵn sàng. |
| Quota nội bộ bằng 0 | Cần grant của người vận hành ở bước 5; không chỉ điền thêm key. |
| Không nhận email xác thực | Gmail sender/App Password trong `var/auth/web.env`; xem cả spam. |
| GitHub rate limit | Có thể thêm backend-only `SMARTREGRESSION_GITHUB_TOKEN` cho public API reads; không cần cho Gemini. Không cấu hình trong frontend. |
| Không có thông báo GitHub mới | Bật theo dõi, lưu nhánh/vùng mã, giữ worker chạy; thay đổi phải được push lên GitHub. Localhost chưa nhận webhook từ GitHub. |
| DB lỗi sau Docker restart | Kiểm tra port loopback của đúng container có nhãn và config riêng; không xóa DB/volume để sửa. |

Xem [vận hành](repo-assistant-local-operations.md),
[bằng chứng và giới hạn](repo-assistant-handoff-20261119.md),
[contract](../contracts/repository-assistant.md). Hướng dẫn này được đối chiếu với
loader/scripts hiện có, không phải tuyên bố đã thử toàn bộ trên máy của từng thành
viên. Codex hỗ trợ soạn và kiểm tra; nhóm cần đọc/hiểu trước khi sử dụng.
