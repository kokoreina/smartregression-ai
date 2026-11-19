# Task 3.46 — Biên bản kiểm chứng cục bộ

Ngày: 18/11/2026. Người thao tác browser: Hà An. Codex hỗ trợ chuẩn bị ma trận,
chạy checks và ghi nhận bằng chứng. Nhánh `feat/an-task-3.46-ownership`, baseline
`effd115`; workspace còn có bản sửa import impact riêng được ghi trong
[handoff parser](python-submodule-impact-fix.md). Không gán bản sửa parser cho 3.46.

## Đầu ra task

Workbook `Sprint 3 Backlog!B518:G524` yêu cầu **định nghĩa** negative cases A/B cho
mọi API đọc/sửa/export, review contracts, owner spoof và ID guessing. Đầu ra này gồm
[ma trận](task-3.46-ownership-matrix.md), [48 ca chi tiết](task-3.46-endpoint-cases.md)
và `backend/tests/unit/test_product_ownership_matrix.py`.

**Trạng thái: đầu ra đã hoàn thiện cục bộ, sẵn sàng review; chưa có approval hoặc PR.**
Việc chạy hết ca nghiệm thu bảo mật toàn sản phẩm là phạm vi riêng, không được ghi
Pass chỉ vì đã có tài liệu và guard tests.

## A/B trên browser do người dùng thực hiện

Môi trường local product mode tại `http://127.0.0.1:5173`. A dùng cửa sổ Opera
thường, B dùng cửa sổ Private; cả hai hiển thị email đã xác thực. Định danh bằng
actor A/B để không ghi email cá nhân vào repo.

Project P-A: `7f4a7c29-9943-407a-b679-b1bd90f37712` — Test SQLParse.

| ID | Thao tác | Quan sát thực tế | Kết luận |
| --- | --- | --- | --- |
| UI-01 | B mở danh sách dự án | Danh sách trống; dự án A không xuất hiện | Pass cho list isolation được quan sát |
| UI-02 | B dán URL trực tiếp của P-A | Hiện “Dự án không tồn tại hoặc bạn không có quyền truy cập”; không hiện nội dung dự án | Pass ở giao diện |
| UI-03 | A mở cùng URL P-A | Hiện Test SQLParse, repository và snapshot | Pass cho positive owner control |

Nguồn: các ảnh người dùng cung cấp trong cuộc trò chuyện lúc khoảng 22:24–22:26.
Không có Network trace kèm ảnh nên không suy mã HTTP từ ảnh. Ảnh gốc chưa được
sao chép vào repo; khi bàn giao cần lưu bản đã che email, tab và thông tin cá nhân.
Biên bản không tuyên bố đã đóng gói ảnh đính kèm.

## PostgreSQL local thật: tám ca kiểm tra ProjectService

Sử dụng cùng P-A và hai owner A/B đã verified có sẵn. Không tạo tài khoản, không
thay mật khẩu hoặc session. Gọi ProjectService và BoundProjectStore thật; test
adapter chỉ thay ownership transaction thành **luôn rollback trong finally**.
Positive mutation được thực hiện trong transaction rồi hoàn tác; denied mutation
cũng được hoàn tác kể cả khi bất ngờ cho phép, và sẽ làm phép kiểm thất bại.

| Ca | Expected và actual | Kết quả |
| --- | --- | --- |
| A get P-A | Trả đúng project | Pass |
| B list | Không chứa P-A | Pass |
| B get P-A | AuthFailure 404 | Pass |
| A update P-A | Sửa title và tăng version trong transaction | Pass, đã rollback |
| B update P-A | AuthFailure 404 | Pass |
| A archive P-A | archived=True trong transaction | Pass, đã rollback |
| B archive P-A | AuthFailure 404 | Pass |
| A get UUID chưa tồn tại | AuthFailure 404 | Pass |

Readback sau cùng: project bằng nguyên trạng trước kiểm tra; số activity không
đổi. Evidence runtime: `var/task-3.46/postgres-project-probe.json` (ignored).
Lần probe đầu dùng sai tên bảng activity và dừng trước mutations; đã đối chiếu
storage code, sửa truy vấn sang `web_activity` và chạy lại đủ tám ca.

Phạm vi chứng minh: domain/storage project isolation trên PostgreSQL. Không phải
bằng chứng HTTP, toàn bộ schema, export, row isolation ở các module còn lại hoặc
test bằng hai phiên browser cho mutation.

## Kiểm tra tự động API guards

Lần chạy cuối: **426 passed** trong 8,24 giây: 411 matrix cases và 15 ca auth,
project, run, AI, API liên quan. Ruff lint/format đạt. Lệnh đầy đủ trong handoff;
log `var/task-3.46/final-targeted.txt`.

- 48 data endpoints đều kiểm tra guest, invalid, expired, disabled và unverified.
- 48 endpoints đều chuyển đúng owner từ phiên A/B dù query/header giả owner.
- 19 mutation/export endpoints kiểm tra thiếu CSRF, CSRF của phiên khác và Origin sai.
- 16 body models từ chối client owner_id; inventory giữ đúng 48 data + 13 account/public.

Services được recording boundary thay thế trong suite matrix. Không gọi provider,
không chạy mã repo đầu vào, không lấy kết quả marker 409 làm CRUD/export thành công.

## Chưa nghiệm thu và bước bàn giao

- Toàn bộ row isolation/read/edit/export cho runs, AI, explorer, notes, scenarios,
  JSON và reporting CSV còn phải chạy theo ma trận với object hợp lệ và positive controls.
- Ca browser guest/unverified, mutation, export và chiều A dùng object B chưa được
  người dùng xác nhận; ghi Not run thay vì Pass. Guard tests không thay các ca đó.
- Disposable PostgreSQL Docker harness chưa khả dụng; không sửa fixture để vượt gate.
- Reviewer đề xuất Trần Hưng Khánh chưa phê duyệt. Không có commit/push/PR/merge.

Để review 3.46: kiểm tra đủ negative cases ở 48 hàng, điều kiện ID guessing/owner
spoof và phân biệt bằng chứng guard/SQL/browser. Review và quyết định nghiệm thu
phải do người được giao ghi nhận; tài liệu này không tự cấp approval.
