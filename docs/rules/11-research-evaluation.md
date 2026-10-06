# 11 — Research/Evaluation

## Phạm vi

Dataset, baselines, fault labels, metrics và báo cáo thực nghiệm. Protocol nguồn ở
[evaluation outline](../research/evaluation-protocol.md); dataset/cohort/ngưỡng vẫn pending.

## Yêu cầu

- MUST khóa selection trước join full-suite outcomes/ground truth. Selector không
  thấy labels hoặc future information dùng đánh giá. Failed tests không là nhãn cho
  toàn bộ affected components; một fault gây nhiều test fail chỉ là một fault ID.
- MUST dùng inventory/cohort chung khi so phương pháp, cùng commit pairs/điều kiện
  chạy và ngân sách phù hợp. Record khác biệt thay vì giấu overhead của phương pháp.
- MUST đóng băng split trước tuning, không tune trên evaluation set; ghi dataset
  provenance/license, tiêu chí lấy mẫu, seed/config/model/prompt/tool versions.
- MUST tách real fault, mutation, flaky tests và infrastructure failures; định nghĩa
  cách adjudicate fault và xử lý failed/excluded runs trước báo metric.
- MUST báo end-to-end time gồm preprocessing/retrieval/LLM/validation/execution/
  report theo boundary đã định. Tách initial indexing khỏi per-change cost; nếu
  amortize, ghi số lần sử dụng và giả định. Time saving có thể âm.
- MUST không bịa nguồn/metrics hoặc biến ngưỡng mục tiêu, giải thưởng, sample minh họa
  thành kết quả thật. SHOULD báo distribution/uncertainty và threats to validity.
- MAY dùng bảng tính tay minh họa để kiểm công thức; gắn nhãn demo, không coi là benchmark.

## Mẫu số và định nghĩa

Các định nghĩa dưới đây là quy ước tính toán cho protocol tương lai, chưa phải kết
quả hoặc cam kết chất lượng. Một cohort chỉ gồm các run so sánh được theo protocol.

- Gọi I là tập test IDs inventory chung và S là selected IDs hợp lệ trong I.
  Test Reduction = 1 − |S| / |I|. |I|=0 → N/A; chạy full suite fallback phải báo tập
  thực tế đã dispatch riêng để không nhầm planned reduction với savings đã đạt.
- F là tập **fault IDs có ground truth** mà full suite phát hiện được trong cohort.
  F_S là tập fault trong F được selected suite phát hiện theo cùng tiêu chí.
  Fault Detection Retention = |F_S| / |F|, |F|=0 → N/A, không tự thành 100%.
- Nếu gọi Missed Fault Rate là phần bù: |F \ F_S| / |F|, cùng F, cohort, eligibility
  và policy loại run. Dùng mẫu số khác phải đổi cách diễn giải, không claim 1−retention.
- Time Saving = (T_full − T_method) / T_full với boundary thời gian đã khai báo;
  T_full=0 → N/A. Không cắt số âm về 0. Unknown cost/time là null/NA, không gán 0.
- SHOULD ghi rõ macro/micro aggregation, exclusions và zero-denominator policy;
  protocol MAY chọn convention khác nếu quyết trước, báo cả numerator/denominator
  và không đánh đồng với định nghĩa trên.

## Lý do và ví dụ

Minh họa: full suite bắt fault A gây 3 tests fail và fault B gây 1 test fail;
selected chỉ bắt A thì retention=1/2, không phải 3/4. Đúng: fault labels có provenance.
Sai: lấy số tests fail làm số faults rồi so cohort khác để tuyên bố không bỏ sót.

## Kiểm chứng

Review leakage/data split; kiểm công thức với empty denominator, duplicate test
fail cùng fault, excluded/timeout run và negative savings. Khi có implementation,
thêm unit tests metrics và replication manifest; chưa có benchmark command thì ghi pending.

## Ngoại lệ

Thay cohort/metric/baseline cần cập nhật protocol và decision trước run, giữ kết quả
cũ có nhãn; không hậu kiểm đổi tiêu chí để làm kết quả đẹp. Theo [00](00-governance.md).

## Liên quan

[06 Testing](06-testing-quality.md), [08 LLM/RAG](08-llm-rag.md),
[09 Selection](09-impact-selection.md), [13 AI use](13-documentation-ai-use.md).
