# ADR 0002 — Python và pytest cho repository đầu vào

- Status: accepted theo yêu cầu trực tiếp của người dùng.
- Ngày: 2026-10-24.
- Người quyết định: Nguyễn Tấn Huy (kokoreina).
- Nguồn: yêu cầu “hãy chốt python và pytest cho dự án này”.
- Thay thế phần lựa chọn ngôn ngữ/framework đầu vào còn pending trong ADR 0001;
  các quyết định bootstrap khác giữ nguyên. Không tuyên bố mentor phê duyệt.

## Context và phương án

MVP cần đúng một ngôn ngữ và một framework của repository được phân tích.
Đây là phạm vi đầu vào, khác với stack Python/FastAPI và React của SmartRegression.
Draft repository candidates hiện tập trung Python/pytest; chưa có bằng chứng chạy
candidate trong worker cô lập hoặc benchmark so sánh các stack.

| Phương án | Lợi ích | Tradeoff và giới hạn bằng chứng |
| --- | --- | --- |
| Python + pytest | Phù hợp hướng candidate và toolchain nhóm hiện có | Discovery có thể import code; cần isolation; chưa chứng minh G1 |
| Java + JUnit | Phương án mở rộng sau MVP | Cần parser/build/discovery khác, chưa có spike so sánh |
| JavaScript + Jest | Phương án mở rộng sau MVP | Cần adapter và môi trường riêng, chưa có spike so sánh |

Không khẳng định Python/pytest tốt hơn bằng benchmark. Lựa chọn được chốt theo
chỉ đạo scope của Huy, không dựa vào kết quả thực nghiệm chưa có.

## Decision

MVP hỗ trợ repository đầu vào dùng **Python và pytest**, chọn/chạy test hiện có
bằng framework-native IDs tại target SHA. Không sinh test, sửa repo đầu vào hoặc
thêm hỗ trợ Java/JUnit, JavaScript/Jest trong quyết định này.

Phiên bản Python/pytest hỗ trợ cho input, plugin, dependency policy, parser,
PR diff semantics và discovery implementation còn pending theo spike.
Python 3.14 của chính SmartRegression không tự thành yêu cầu phiên bản cho input.

## Consequences và kiểm chứng

- An triển khai/kiểm chứng diff, symbol và dependency cho Python theo brief.
- Khánh triển khai/kiểm chứng pytest discovery và single-test execution cô lập.
- Việt kiểm chứng candidate/license và khả năng tái lập; candidate chưa tự được chọn.
- Huy tổng hợp G1: checkout → diff → discovery → single-test execution và dependency.
- Discovery cũng chạy code không tin cậy; không chạy trong API/dashboard hoặc host
  có credentials. Cần policy cô lập trước thực thi.
- Không đổi public contracts, dependencies, DB, runner hoặc CI trong task tài liệu này.

**G1 vẫn chưa được chứng minh bởi quyết định này.** Gate kỹ thuật, review độc lập
và các quyết định D06–D09 không tự hoàn thành khi D05 được chốt một phần.

## Migration, rollback và review

Không có migration dữ liệu/runtime. Decision register là chỉ mục trạng thái hiện tại;
các draft/handoff cũ là snapshot lịch sử, câu “framework pending” ở đó được thay thế
bởi ADR này cho riêng lựa chọn Python/pytest. Backlog spike nay kiểm chứng cặp đã chọn.
Xem lại sau G1 nếu candidate/plugin/runtime không tái lập được; thay đổi quyết định
cần ADR mới, giữ lịch sử và bằng chứng. Không rollback bằng xóa quyết định cũ.

Codex hỗ trợ soạn và kiểm tra tài liệu; Huy cần đọc/hiểu, thành viên khác review PR.
Không giả chữ ký, tỷ lệ đóng góp hoặc phê duyệt độc lập.
