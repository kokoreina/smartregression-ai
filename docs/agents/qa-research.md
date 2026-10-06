# QA/Research

## 1. Mục đích

Kiểm thử correctness của SmartRegression và đánh giá phương pháp nghiên cứu là hai
luồng riêng. Tạo bằng chứng tái lập được, không dùng ground truth để trợ giúp selector.

## 2. Khi sử dụng

Regression tests cho sản phẩm, evaluation protocol, dataset/labels/baseline hoặc
review metrics/threats to validity.

## 3. Input

Expected behavior và task scope cho product tests; cohort/split/labels/provenance,
baselines/config/budget và run observations cho nghiên cứu. Thiếu labels không được
đếm test fail thay thế fault.

## 4. Paths thường phụ trách

[backend tests](../../backend/tests), [core/evaluation](../../backend/src/smartregression/core/evaluation),
[research docs](../research), [report examples](../../examples/reports).
Chưa có benchmark dataset/runner hoặc frontend e2e harness.

## 5. Shared files

[contracts](../../backend/src/smartregression/contracts/models.py),
[evaluation protocol](../research/evaluation-protocol.md), fixtures, CI gates.
Selector chỉ nhận input được phép trước chạy test, không nhận data join của evaluator.

## 6. Được tự thực hiện

Viết test có ý nghĩa, chuẩn bị fixtures/mock, kiểm tra metrics bằng dữ liệu minh họa
được gắn nhãn, đề xuất protocol và báo bằng chứng. Không tự đặt ngưỡng chất lượng thành kết quả.

## 7. Ngoài phạm vi

Chọn dataset/license, đổi cohort/metric/budget hoặc chạy benchmark trả phí chưa giao;
không tối ưu prompt/model bằng cách nhìn trước evaluation set.

## 8. Các bước

1. Chọn luồng product test hay research; ghi expected và nguồn ground truth.
2. Khóa input/split/config trước so sánh; tách real/mutation/flaky/infrastructure.
3. Chạy checks được phép, giữ cả failed/excluded runs và lý do.
4. Báo denominator, uncertainty, cost và limits; bàn giao replication instructions.

## 9. Edge cases

Một fault nhiều tests fail; full suite không bắt fault nào; inventory rỗng; baseline
khác commit; timeout chưa có verdict; negative time saving; flaky/non-determinism;
partial parsing; token usage không có.

## 10. Kiểm chứng

Pytest unit/integration theo risk; schema/CLI checks; metric hand calculation theo
[rule 11](../rules/11-research-evaluation.md). Chưa có benchmark command đã xác minh;
không dùng mock outcomes như kết quả phương pháp thật.

## 11. Output và hoàn thành

Test tái hiện failure hoặc nêu không tái hiện; protocol ghi cohort/labels/exclusions,
retention đúng fault denominator, đầy đủ seed/config/version để người khác kiểm lại.

## 12. Prompt giao việc

> Dùng QA/Research, đọc rule 06 và 11. Review evaluation outline hiện tại, đề xuất
> manifest phân biệt real fault, mutation, flaky và infrastructure failure. Chỉ sửa
> tài liệu nghiên cứu; dùng ví dụ giả có nhãn minh họa để kiểm tra mẫu số 0 và một fault
> gây nhiều test fail. Không đưa labels vào selector, không bịa benchmark hoặc nguồn.

## 13. Bàn giao

> Luồng kiểm chứng: …; dataset/cohort/label provenance: …; config/baseline: …;
> denominator/failed runs: …; checks/result thật: …; threats/pending: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[06](../rules/06-testing-quality.md), [11](../rules/11-research-evaluation.md),
[08](../rules/08-llm-rag.md), [13](../rules/13-documentation-ai-use.md).
