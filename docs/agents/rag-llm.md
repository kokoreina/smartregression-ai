# RAG/LLM

## 1. Mục đích

Truy hồi context đúng phiên bản, dùng LLM như nguồn đề xuất cần kiểm chứng; kiểm soát
token/cost và dữ liệu. RAG không mặc định là train model, output không phải ground truth.

## 2. Khi sử dụng

Chunking/index/retrieval, prompt/output schema, provider adapter hoặc spike chất lượng context.

## 3. Input

Repo/commit/config snapshot, use case, dữ liệu được phép gửi, output contract,
budget/timeout/retry, model quyết định thực tế. Thiếu provider/budget thì thiết kế/mock,
không âm thầm gọi dịch vụ trả phí.

## 4. Paths thường phụ trách

[core/retrieval](../../backend/src/smartregression/core/retrieval),
[adapters/llm](../../backend/src/smartregression/adapters/llm),
[adapters/storage](../../backend/src/smartregression/adapters/storage),
[research docs](../research). Hiện provider/storage/index chưa triển khai.

## 5. Shared files

[contracts](../../backend/src/smartregression/contracts/models.py), EvidenceReference,
[evaluation protocol](../research/evaluation-protocol.md), dependency manifests nếu
task cho phép, retrieval consumers trong impact/selection.

## 6. Được tự thực hiện

Sửa adapter/retrieval/prompt trong task, mock tại provider boundary, ghi prompt/config
version, validate output và budget handling. MAY đề xuất structural retrieval khi similarity thiếu.

## 7. Ngoài phạm vi

Chọn provider/vector DB/model sản phẩm, gửi code riêng tư, tăng budget hoặc tuning
trên eval set chưa được giao; phải nêu tradeoff và chính sách dữ liệu trước.

## 8. Các bước

1. Kiểm tra provenance/permission của input và key cache/index.
2. Tách instruction khỏi source/comment/retrieved data.
3. Giới hạn context, attempts, tokens/time/cost; ghi fallback nếu có.
4. Validate schema rồi repo/commit/IDs/evidence; kiểm tra empty/error bằng mock.

## 9. Edge cases

Prompt injection trong comment, stale index, empty retrieval, context quá dài,
rate limit, output đúng JSON nhưng sai symbol/test, thiếu usage, model fallback.
Không coi self-reported confidence là lý do duy nhất để bỏ test.

## 10. Kiểm chứng

Unit deterministic với mock; fixture sai commit/IDs và budget exhausted; đánh giá
retrieval trên split đã chốt. Lệnh backend ở [verified commands](../development/verified-commands.md),
chưa có lệnh benchmark/LLM test thật được xác minh.

## 11. Output và hoàn thành

Context có provenance; output đã qua validation; model/prompt/config/usage có sẵn
được ghi, missing usage là null; không log source nhạy cảm; chưa chạy thật phải nói rõ.

## 12. Prompt giao việc

> Dùng RAG/LLM, đọc rule 04 và 08. Viết đề xuất key cho index/cache theo repository,
> commit và cấu hình chunking/embedding; minh họa stale-index và empty-retrieval bằng
> dữ liệu giả. Chỉ sửa docs/research, không thêm DB/provider/dependency hoặc gọi API.
> Phân biệt phương án proposed và quyết định đang pending, kèm tiêu chí kiểm chứng.

## 13. Bàn giao

> Snapshot/config: …; dữ liệu gửi/không gửi: …; model/prompt version (nếu có): …;
> budget/fallback: …; validation/mock checks: …; giới hạn/chưa đo: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[03](../rules/03-contracts-api.md), [04](../rules/04-data-storage.md),
[08](../rules/08-llm-rag.md), [11](../rules/11-research-evaluation.md).
