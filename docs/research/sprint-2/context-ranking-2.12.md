# Ranked, Deduplicated, and Validated Context — Task 2.12

**Module:** `backend/src/smartregression/core/retrieval/ranked_context.py`
**Author:** Dang Dai Viet (VI)
**Sprint:** 2 — Change impact + dependency analysis
**Role:** RAG / Retrieval Context Validation (VI 8h)
**Status:** Implementation & verification completed (16 unit tests passing)

---

## 1. Mục tiêu và phạm vi

Theo kế hoạch Sprint 2 (`docs/development/sprint-2-team-guide.md`, anchor `#task-212`):
- **Nhiệm vụ:** Nhận `RetrievalPayload` từ Task 2.11 (H2), đối chiếu với `FrozenSnapshot` bất biến (Task 2.15), sắp xếp thứ tự ưu tiên (ranking), loại bỏ trùng lặp mà không mất xuất xứ (deduplication preserving provenance), và kiểm tra tính hợp lệ về mặt kỹ thuật (repo, commit, path, line range, content hash).
- **Quy tắc xếp hạng (Rule 2.12-v1):** Xác định thứ tự ưu tiên rõ ràng theo tier thay đổi, độ liên quan (score), thứ tự ban đầu, và tie-break ổn định.
- **Xử lý bất thường:** Phát hiện sai lệch commit/repo thì fail closed; phát hiện chunk hỏng/sai lệch nội dung thì reject ở strict mode hoặc tách vào limitations ở partial mode (Rule 09).
- **Người tiêu thụ (Consumers):** Task 2.13 (Workflow/CLI runner - H1), Task 2.17 (Analysis limitations manifest - AN), và giao diện báo cáo Task 2.18.

---

## 2. Thiết kế giải thuật & Kiến trúc

### 2.1 Thuật toán Ranking & Tie-Break (`Rule 2.12-v1`)

Thứ tự sắp xếp được tính toán hoàn toàn xác định (deterministic) theo các tiêu chí:

1. **Relevance Tier (Độ ưu tiên phân lớp):**
   - **Tier 1 (Directly Changed):** Tệp/module nằm trong danh sách thay đổi trực tiếp (từ Task 2.01 `ChangePayload` hoặc `ImpactCandidate.relationship == "changed"`).
   - **Tier 2 (Direct Dependents):** Tệp là phụ thuộc trực tiếp (từ Task 2.04 `ImpactCandidate.relationship == "direct"`).
   - **Tier 3 (Indirect Dependents):** Tệp là phụ thuộc bắc cầu (từ Task 2.04 `ImpactCandidate.relationship == "indirect"`).
   - **Tier 4 (General / Other Context):** Các ngữ cảnh truy hồi khác không thuộc diện thay đổi hoặc tác động đã biết.
2. **Relevance Score (Điểm tương đồng/relevance):** Sắp xếp giảm dần (`score` cao hơn xếp trước; `None` xếp sau các giá trị số).
3. **Original Retrieval Rank (Thứ tự gốc):** Ưu tiên chunk có thứ tự ban đầu tốt nhất (`min(original_rank)`).
4. **Deterministic Tie-Break:**
   - Thứ tự từ điển đường dẫn (`path` ascending).
   - Dòng bắt đầu (`line_start` ascending).
   - Dòng kết thúc (`line_end` ascending).
   - Chunk ID (`id` ascending).
5. **Gán Rank liên tục:** Gán số thứ tự chuẩn hóa `rank = 1, 2, ..., N` cho các chunk sau deduplication.

### 2.2 Deduplication không làm mất Provenance

Khi nhiều truy vấn hoặc nguồn chỉ mục (index sources) trả về cùng một đoạn mã vật lý `(path, line_start, line_end, content_sha256)`:
- Hợp nhất thành **1** mục đại diện duy nhất trong danh sách xếp hạng.
- Giữ lại toàn bộ vết xuất xứ trong `ContextProvenance`: ghi nhận nguồn `RetrievalSource`, mã chunk ban đầu `original_item_id`, thứ tự ban đầu `original_rank`, và điểm `score`.
- Bảo toàn toàn bộ các nguồn `RetrievalSource` trong `RetrievalPayload.sources`, đảm bảo không mất thông tin xuất xứ đối với hệ thống downstream.

### 2.3 Kiểm chứng nguồn bất biến (`FrozenSnapshot`)

Đối chiếu từng chunk với `FrozenSnapshot`:
1. **Danh tính Repository & Commit:** Kiểm tra `repository_id`, `commit`, và `snapshot_id`. Nếu phát hiện khác biệt revision/repository -> lập tức báo lỗi `retrieval_repository_mismatch`, `retrieval_commit_mismatch`, hoặc `retrieval_snapshot_mismatch` (bảo vệ ranh giới bảo mật theo Rule 08/09).
2. **Sự tồn tại của tệp:** Tệp `path` phải tồn tại trong snapshot. Nếu không có -> mã lỗi `unknown_snapshot_path`.
3. **Phạm vi dòng (Source Range):** Kiểm tra `1 <= line_start <= line_end <= tổng số dòng vật lý`. Định dạng dòng hỗ trợ cả LF, CR, CRLF không làm biến dạng byte gốc. Nếu vượt quá phạm vi -> mã lỗi `invalid_source_range`.
4. **Content Hash:** Trích xuất chính xác byte vật lý từ dòng `line_start` đến `line_end`, băm SHA-256 và so khớp với `content_sha256`. Nếu không trùng khớp -> mã lỗi `chunk_content_mismatch`.

### 2.4 Hỗ trợ Strict Mode và Partial Stage

- **`strict=True`:** Phát hiện bất kỳ chunk nào không hợp lệ sẽ kích hoạt `raise ValueError(error_code)`.
- **`strict=False` (Mặc định cho pipeline):** Loại trừ các chunk lỗi khỏi danh sách ngữ cảnh hợp lệ, ghi nhận vào `limitations: tuple[StageIssue, ...]`, và trả về `status="partial"`.
- Phương thức `to_stage_result()` tạo đối tượng `StageResult[RetrievalPayload]` tuân thủ nghiêm ngặt validator của canonical contract (hỗ trợ cả `completed` khi sạch lỗi và `partial` khi có limitations).

---

## 3. Cấu trúc dữ liệu

Được định nghĩa tại [`backend/src/smartregression/core/retrieval/ranked_context.py`](../../../backend/src/smartregression/core/retrieval/ranked_context.py):

- **`ContextProvenance`:**
  - `source: RetrievalSource`
  - `original_item_id: str`
  - `original_rank: int`
  - `score: float | None`
- **`ValidatedContextItem`:**
  - `id: str`
  - `path: str`
  - `line_start: int`, `line_end: int`
  - `content_sha256: str`
  - `rank: int`
  - `tier: int` (1..4)
  - `score: float | None`
  - `primary_source: RetrievalSource`
  - `provenance: tuple[ContextProvenance, ...]`
- **`ValidatedContextResult`:**
  - `status: Literal["completed", "partial"]`
  - `payload: RetrievalPayload`
  - `items: tuple[ValidatedContextItem, ...]`
  - `limitations: tuple[StageIssue, ...]`
  - `rule_version: str` (`"2.12-v1"`)
  - `to_stage_result() -> StageResult[RetrievalPayload]`

---

## 4. Kết quả kiểm chứng kỹ thuật

Suite test tại [`backend/tests/unit/test_ranked_context.py`](../../../backend/tests/unit/test_ranked_context.py):

| Test Case | Mục đích kiểm tra | Kết quả |
|---|---|---|
| `test_happy_path_single_payload_ranked_and_validated` | Payload hợp lệ, rank 1..N, status completed | **PASSED** |
| `test_ranking_priority_tiers` | Ưu tiên Tier 1 (changed) > Tier 2 (direct) | **PASSED** |
| `test_ranking_tie_breaks_scores_and_positions` | Tie-break theo score và vị trí ổn định | **PASSED** |
| `test_deduplication_preserves_provenance` | Hợp nhất 2 chunk trùng lặp, giữ đủ 2 provenance | **PASSED** |
| `test_deduplication_across_multiple_payloads` | Hợp nhất chunk trùng lặp giữa 2 payloads | **PASSED** |
| `test_empty_retrieval_payload_valid` | Payload rỗng hợp lệ (retains sources provenance) | **PASSED** |
| `test_content_hash_mismatch_strict_and_partial` | Hash sai lệch: strict reject, non-strict partial | **PASSED** |
| `test_unknown_snapshot_path_strict_and_partial` | Tệp không tồn tại: strict reject, non-strict partial | **PASSED** |
| `test_invalid_source_range_strict_and_partial` | Dòng vượt quá tệp: strict reject, non-strict partial | **PASSED** |
| `test_identity_mismatch_fails_closed` | Sai repository/commit/snapshot: luôn fail closed | **PASSED** |
| `test_partial_stage_with_mixed_valid_and_invalid_items` | Một chunk lỗi, một chunk chuẩn: partial + limitations | **PASSED** |
| `test_validate_retrieval_stage_helper` | Helper trả về StageResult hợp lệ | **PASSED** |
| `test_integration_with_change_payload` | Tích hợp ChangePayload từ Task 2.01 | **PASSED** |
| `test_no_execution_or_outcome_leakage` | Không để lộ outcome/fault label/mã thực thi | **PASSED** |

**Tổng kiểm chứng:**
- `pytest backend/tests/unit/test_ranked_context.py`: **16 passed in 0.70s**
- `pytest backend/tests/unit`: **587 passed in 12.49s**
- `ruff check .` & `ruff format --check .`: **All passed cleanly**
- `scripts/export_contracts.py --check`: **All passed cleanly**

