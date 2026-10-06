# Phác thảo evaluation protocol — chưa có kết quả

Câu hỏi: selection giảm số test/thời gian như thế nào so với full suite mà vẫn giữ
khả năng phát hiện fault có ground truth độc lập? Impact explanations có bằng chứng
đúng commit/file/symbol và có ích cho reviewer không?

Đơn vị thực nghiệm: repository + base/target commit + môi trường + test inventory.
Đóng băng dataset split theo thời gian/repository trước tuning để tránh leakage.
Lưu seed/config/version/schema, tool/model version nếu sau này sử dụng LLM.

Pipeline tách biệt:
1. Selector chỉ thấy change, code/evidence và test inventory được phép tại thời điểm chọn.
2. Lưu selection cùng explanation/fallback trước khi chạy test.
3. Worker tương lai chạy selected và full suite với cùng điều kiện, timeout có ghi nhận.
4. Evaluator join outcomes với fault labels có provenance độc lập. Selector không được
   xem outcome full suite, nhãn fault hoặc future commit khi suy luận.

Phân loại: real fault cần ground truth được review; mutation fault cần operator/seed;
infrastructure failure (timeout, setup, runner crash) không gộp thành real fault.
Flaky test cần protocol chạy lại và báo riêng. Test fail không đủ để khẳng định fault.

Metrics dự kiến: tỷ lệ test được chọn, wall-clock cost (gồm overhead), fallback rate,
valid-ID rate, evidence correctness và fault recall chỉ khi có ground truth/denominator
hợp lệ. Chưa đo ghi null/NA; không gán 0. Báo phân bố, uncertainty và exclusions.

Pending: dataset/license, ngôn ngữ/framework, full-suite baseline và heuristic baseline,
budget, số lần lặp, sample size, fault adjudication, flaky handling, leakage audit,
review rubric cho giải thích, thống kê/CI và cách xử lý suite không chạy được.
Chưa chạy thực nghiệm, chưa có kết quả hoặc nguồn nghiên cứu được xác minh để trích dẫn.
