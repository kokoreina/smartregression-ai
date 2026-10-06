# 09 — Impact/Selection

## Phạm vi

Git change model, impact/evidence, inventory, selected/skipped và fallback.
Chưa có thuật toán thật; [contract](../contracts/README.md) hiện chỉ validate cấu trúc/liên kết.

## Yêu cầu

- MUST chuẩn hóa base/target full SHA và xác định diff semantics. PR phải nêu merge-base,
  head/base hoặc merge result nào được so; không dùng branch mutable như snapshot đã khóa.
- MUST xét deleted/renamed files, thay đổi tests/config/dependencies; partial parser
  phải ghi giới hạn. Dependency edge không đồng nghĩa behavior chắc chắn đổi.
- MUST tách trực tiếp changed, possibly impacted và verified impact theo bằng chứng.
  Evidence đúng vị trí khác evidence thật sự hỗ trợ kết luận; không tự thêm enum chưa có.
- Inventory MUST thuộc target commit/framework được hỗ trợ; selected/skipped lấy từ
  inventory đó. IDs LLM đề xuất phải tồn tại, loại trùng có ghi nhận khi cần; hai tập không giao.
- MUST xác định inventory có đầy đủ không trước tuyên bố phân loại toàn bộ test.
  Nếu policy phân loại toàn inventory, union hai tập phải bằng inventory; partial inventory
  cần trạng thái/giới hạn rõ, không giả full coverage.
- Không tìm được test MUST không bị diễn giải thành không có rủi ro. Empty selection
  phải có lý do và policy rõ; parsing thiếu/evidence sai/provider lỗi dẫn tới fallback
  có ghi nhận hoặc dừng có lỗi theo policy đã quyết, không silently drop test.
- Full-suite fallback chạy lỗi MUST báo execution/infrastructure failure, không báo an toàn.
- MUST không hứa zero missed faults khi chưa có bằng chứng. Selection khác prioritization;
  MUST không dùng full-suite outcomes/fault labels làm selector input.
- SHOULD ưu tiên giải thích truy vết được; MAY đề xuất conservative fallback trong
  spike nhưng chính sách cuối vẫn cần quyết định, không tự coi đã accepted.

## Lý do

Chọn ít test chỉ có ý nghĩa khi danh tính, snapshot và điều kiện fallback được kiểm soát.

## Ví dụ

Đúng: deleted symbol tham chiếu base, inventory vẫn ở target, thiếu evidence dẫn tới
fallback có lý do. Sai: chọn test đã bị xóa; thấy empty retrieval nên bỏ mọi test và báo safe.

## Kiểm chứng

Tests wrong commit, rename/delete, changed config/test, unknown/duplicate IDs,
empty/partial inventory, fallback reason và lỗi fallback. Review semantics bằng chứng,
không chỉ xem JSON Schema pass.

## Ngoại lệ

Spike dùng inventory nhỏ được gắn nhãn không đại diện full repo; không dùng kết quả
đó để tuyên bố recall. Đổi policy/diff semantics ngoài task theo [00](00-governance.md).

## Liên quan

[03](03-contracts-api.md), [08](08-llm-rag.md), [10](10-runner-security.md),
[11](11-research-evaluation.md).
