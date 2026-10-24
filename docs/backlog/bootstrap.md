# Bootstrap và bước tiếp theo

Đã tạo: src package và ranh giới lớp; 9 contract yêu cầu cùng model hỗ trợ; health API;
CLI validate-report; fixture/dashboard DEMO; export schema/types; CI; docs nhóm và
evaluation outline. Kết quả checks thực tế ở docs/development/verification.md.
Không có thuật toán phân tích, provider, storage hay runner implementation.

| Task nhỏ tiếp theo | Đầu ra | Tiêu chí chấp nhận |
| --- | --- | --- |
| 1. Technical spike Python/pytest | Fixture repo nhỏ và evidence cho cặp đã chọn theo [ADR 0002](../architecture/decisions/0002-python-pytest-input.md) | Chứng minh diff, symbol/dependency mapping, discovery và single-test execution cô lập; xác định phiên bản/plugin hỗ trợ, ghi giới hạn và trạng thái G1 |
| 2. Git change adapter tối thiểu | Đọc hai commit từ repo cục bộ tạo ChangedComponent | Tests cho add/modify/delete/rename, commit không tồn tại; chỉ read-only, không clone hay execute |
| 3. Validator test inventory | Interface discovery + kiểm tra stable IDs và fallback policy | Phát hiện ID không tồn tại/trùng, selected/skipped không giao; tests từ inventory cố định, không dùng outcomes |
| 4. Evidence provenance | Resolver kiểm tra commit/file/line/symbol với fixture | Từ chối bằng chứng ngoài commit pair hoặc dòng không tồn tại; xử lý deleted file theo base commit |
| 5. Evaluation manifest | Schema manifest và 3 ví dụ real/mutation/infrastructure | Provenance/label tách khỏi selector, reviewer xác nhận không leakage; unknown metrics null; chưa chạy code đầu vào |
