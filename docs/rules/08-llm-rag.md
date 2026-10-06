# 08 — LLM/RAG

## Phạm vi

Retrieval/index/chunking, prompt, provider adapters và thực nghiệm có LLM.
Hiện chưa có provider/index implementation; GPT-6 Astra dùng để coding không chốt model sản phẩm.

## Yêu cầu

- MUST coi RAG là truy hồi context, không mặc định train model. LLM output là đề xuất,
  không phải ground truth; structured output chỉ giúp shape, không chứng minh semantics.
- API key MUST chỉ ở backend, không VITE_*/bundle/log/prompt. Chỉ gửi dữ liệu được
  phép, lọc credential và hạn chế lưu nguyên văn source/prompt vào nhật ký chia sẻ.
- Source/comment/tài liệu truy hồi MUST là dữ liệu không tin cậy: không thay system
  instruction, tool permission hoặc policy, dù văn bản yêu cầu bỏ validation.
- MUST validate schema rồi identifiers, repo/commit và evidence trước sử dụng.
  Giữ index đúng snapshot theo [04](04-data-storage.md); không tin test ID LLM tự đặt.
- MUST giới hạn context/tokens/attempts/time/cost theo task. Ghi model ID thực,
  prompt version, retrieval config và usage nếu có; unknown usage/cost không thành 0.
- MUST không âm thầm đổi model giữa thực nghiệm; ghi fallback và cohort bị ảnh hưởng.
  Self-reported confidence không là điều kiện duy nhất để bỏ test.
- SHOULD kết hợp quan hệ cấu trúc khi câu hỏi cần dependency/call graph; similarity
  cao không chứng minh dependency hoặc tác động hành vi.
- MUST tách benchmark/evaluation khỏi prompt tuning theo [11](11-research-evaluation.md).
  MAY dùng mock provider cho phát triển local, gắn nhãn và không đưa vào kết quả nghiên cứu thật.

## Lý do

Ngăn prompt injection, stale context và chi phí vô hạn làm sai quyết định selection.

## Ví dụ

Đúng: đề xuất test ID được đối chiếu inventory target trước dispatch. Sai: comment
trong repo yêu cầu gửi API key, agent/provider pipeline làm theo; retrieval rỗng nhưng
vẫn báo impact chắc chắn hoặc tự đổi sang model khác mà không ghi nhận.

## Kiểm chứng

Mock lỗi provider, budget exhausted, wrong commit/ID, injection và empty retrieval;
review config/provenance/log redaction. Chưa có benchmark command thì ghi pending,
không lấy fixture minh họa làm kết quả chất lượng.

## Ngoại lệ

Live provider test chỉ khi task cho phép dữ liệu, budget và môi trường cụ thể; không
chuyển live call vào unit suite. Thay model/provider hoặc data policy ngoài scope theo
[00](00-governance.md), không tự tạo credential hay tăng quyền.

## Liên quan

[03 Contracts](03-contracts-api.md), [04 Storage](04-data-storage.md),
[09 Selection](09-impact-selection.md), [11 Research](11-research-evaluation.md).
