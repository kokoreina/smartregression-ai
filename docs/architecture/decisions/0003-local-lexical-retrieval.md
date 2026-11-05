# ADR 0003 — P5: local structural và lexical retrieval cho Sprint 2

- Status: **accepted** ngày **2026-11-05**.
- Người quyết định: Nguyễn Tấn Huy (H1), truyền đạt sự đồng ý của cả nhóm.
- Nguồn: user xác nhận “Vậy hãy chốt những thông tin này đi tôi và cả nhóm đều đã
  đồng ý với các ý này”, trả lời danh sách 12 quyết định P5, base/target semantics,
  phân công và tiêu chí nghiệm thu trong phiên hiện hành.
- Thay phần retrieval/index còn pending của D06 và P5 trong
  [checkpoint 2.20](../../development/task-2.20-checkpoint.md#11-decision-register-cho-checkpoint).
  Provider/model LLM, production retention và các quyết định khác không tự được chốt.
- Phạm vi: thiết kế cho 2.10/2.11/2.12 và tích hợp 2.13/2.17/2.18;
  không thay estimate, lịch sprint hoặc ghi task Done.

## Context và phương án

Baseline đã kiểm tra: main `07452660ab37699b0fbc28864601ea9e653f1bd3`.
Snapshot acquisition, graph/impact, provisional index/chunk manifest, context
metadata builder và ranking/validation đã có implementation riêng. Workflow vẫn
ghi retrieval `not_implemented`; `IndexBuild.ready()` luôn từ chối với
`trusted_snapshot_acquisition_required`. Chưa có index metadata migration hoặc
LLM provider call. Accepted design không tự thay những implementation blockers này.

| Phương án | Lợi ích | Chi phí và giới hạn |
| --- | --- | --- |
| Local structural + lexical, được chọn | Tận dụng graph/impact và 2.12; tái lập được; không gửi source tới provider | Phụ thuộc identifiers và graph; không cung cấp semantic embedding search |
| Embedding/vector retrieval | Có thể hỗ trợ truy vấn khác từ vựng | Cần model, backend, data/budget policy và kiểm chứng thêm |
| Hybrid lexical + embedding | Có thể kết hợp hai nguồn tín hiệu | Tăng công việc tích hợp trước khi có bằng chứng cần thiết |

Lựa chọn theo code/phạm vi Sprint 2, không phải benchmark chứng minh lexical tốt
hơn. Xem lại sau nghiệm thu retrieval hoặc khi đánh giá tái lập được cho thấy thiếu
context cần thiết.

## Decision

### Retrieval và dữ liệu

1. Retrieval chạy **local**, kết hợp changed components, potential-impact candidates
   và lexical search. Không thêm embedding provider, pgvector/vector database hoặc
   dịch vụ ngoài máy trong slice Sprint 2 này.
2. Chỉ index source/tests/docs được phép từ **authorized frozen snapshots**.
   Không dùng dirty working tree; không chạy/import input source, collection/hooks.
3. Context hiện hành mặc định thuộc **target**. Deleted code hoặc đối chiếu thuộc
   **base**, có index/source identity riêng. Không trộn hai revision thành một
   snapshot, gán base bytes cho target, hoặc đổi target graph/mapping semantics.
4. Loại đường dẫn bị cấm, secrets đã nhận diện, reference full-suite outcomes và
   fault labels trước tạo chunk/artifact/index. Hash/local-only không thay exclusion;
   không hứa phát hiện mọi secret. Retrieved source/comment/docs là dữ liệu không
   tin cậy, không đổi policy hoặc tool permissions.

### Chunk, query và ranking

5. Python ưu tiên class/function AST boundaries, tái sử dụng parser hiện có. Phần
   module còn lại và tests/docs dùng đoạn có giới hạn. Oversized symbol/chunk xử lý
   theo policy đã version hóa, giữ đúng physical range. Không viết parser cạnh tranh
   hoặc che parse failure bằng completed index. Giữ CR/LF/CRLF boundaries và exact
   byte hashes của 2.10/2.12; không normalize bytes để verify.
6. Query deterministic từ path, module/symbol và identifiers liên quan thay đổi;
   không dùng LLM sinh query. H2 bàn giao tokenizer, lexical scoring, query policy
   và tie-break có version/expected fixtures. Công thức cụ thể là implementation
   detail, không cần hỏi chọn backend lại; không tuning bằng outcomes/fault labels.
7. Giữ rule 2.12: changed → direct dependents → indirect dependents → context bổ
   sung; lexical score xếp **trong từng nhóm**, rồi tie-break deterministic hiện
   hành. Dedup giữ provenance. Score không là confidence/fault probability hoặc
   bằng chứng safe exclusion.
8. Bắt buộc giới hạn chunk size, tổng dữ liệu/chunks index, query work/time và
   context output. H2 ghi đơn vị/default hữu hạn trong config và boundary tests;
   không nới cap snapshot/runner. Vượt budget phải reject hoặc expose partial/reason;
   top-k output phải ghi rõ, không silently truncate rồi báo đầy đủ ảnh hưởng.

### Persistence và lifecycle

9. PostgreSQL lưu metadata index/chunk, state, configuration và artifact references.
   Chunk content/manifest ở artifact local có hash. Tái sử dụng connection,
   transaction, migration và guarded artifact publication patterns hiện có;
   không xây storage service mới hoặc đưa source lớn/vector vào metadata tables.
10. Key phân biệt repo, frozen commit/snapshot, index version và canonical config
    hash. Config gồm parser/chunking/tokenizer/query/scoring/ranking/exclusions và
    limits ảnh hưởng kết quả. Backend thể hiện lexical; **`embedding_model = NULL`**,
    không model giả. Config/version đổi không được reuse index như cùng identity.
11. Lifecycle riêng `building / ready / failed`, không đổi canonical StageStatus.
    Ready chỉ sau trusted acquisition verification, xác minh manifest/chunks/bytes/
    hash/config cùng snapshot, artifact publish và metadata commit. AN/H1/H2 phải
    nối boundary thực từ 2.15; bỏ guard hoặc nhận boolean/caller-supplied manifest
    làm trust proof không đáp ứng quyết định này.
12. H2/KH định nghĩa lookup ready index theo repo/snapshot/config/version, load
    chunks/provenance theo index/path/range và stale-build checks. Scoped FKs,
    uniqueness, nullable model vào migration từ head thật, không dùng slot cũ.
    Incomplete publication không query như ready. SQL/filesystem không có distributed
    transaction: DB fail sau publish giữ orphan và báo lỗi; commit outcome không rõ
    không tự delete/replay. Recovery kiểm cả metadata và artifact bytes.

### Output và LLM

13. Tái sử dụng `RetrievalPayload`, `RetrievalSource`, `StageResult`; giữ repo/commit/
    snapshot/index/config/path/range/hash và limitations. Resolver riêng lấy bounded
    bytes từ verified artifact cho authorized consumer; không nhét source vào
    metadata hoặc tự mở rộng public contract. Base/target sources giữ identity riêng;
    H1/AN/VI kiểm consumer compatibility trước wiring.
14. Successful empty khác unavailable/failed/partial. Sai repo/SHA/config hoặc hash
    phải reject/expose đúng limitations, không thành safe empty. Graph/impact limits
    không được mất khi tổng hợp retrieval/report/UI.
15. P5 không chọn LLM provider/model, gọi dịch vụ trả phí, tạo selector hoặc chạy
    test input. LLM sau này có adapter và data/budget decision riêng.

## Phân công và thứ tự bàn giao

Theo phân công nhóm đã đồng ý; không cộng estimate hoặc đổi accountable:

| Thành viên | Phạm vi |
| --- | --- |
| H2 — Phạm Phan Hoàng Huy | 2.10/2.11 chunking/config/local lexical index/search và producer; giữ graph/impact semantics |
| AN — Đỗ Hà An | Acquisition evidence 2.15, base/target identity, limitations 2.17 và identity slice 2.19 |
| H1 — Nguyễn Tấn Huy | Điều phối interface/compatibility 2.14, composition/wiring 2.13 và storage consumer boundaries |
| KH — Trần Hưng Khánh | Shared migration chain, metadata transaction/recovery, exclusions support 2.10 và cross-module 2.19 |
| VI — Đặng Đại Việt | Tái sử dụng 2.12 rank/dedup/verify, context/provenance/limitations consumer và UI 2.18 |

Thứ tự: H2/AN/H1 interface/config → KH/H2 metadata/artifact boundary → H2 index
ready/retrieval + VI validation → H1 workflow → AN/KH cross-module và VI browser.
Phần độc lập làm trước; một writer cho cùng contract/schema/migration. Profiles
không tự khởi chạy sub-agents.

## Acceptance cần thực hiện

- Cùng snapshot/config tạo cùng chunks/identities/ordering; đổi config không reuse
  sai index. Có expected relevance/tie/dedup fixtures, không outcomes/fault labels.
- Wrong repo/SHA/snapshot/config, stale/incomplete index, tampered artifact/hash và
  sai range bị reject. Deleted/base context không bị gán target provenance.
- Index ready cần acquisition proof thực; lỗi build/artifact/SQL không tạo ready.
  Có concurrency/retry, rollback và lost-ack checks theo data impact.
- Boundary limits/exclusions và empty/partial/failed/budget-exhausted rõ; không
  execute input hoặc đưa partial thành safe exclusion.
- PostgreSQL + artifact round-trip và backup/restore thực; fake/SQLite không thay
  acceptance. Contract/generated consumers không drift.
- CLI dùng producer thật; report/UI giữ provenance/limitations, có smoke artifacts,
  commands/results và handoff. Browser checks không thay bằng typecheck.

## Migration, khôi phục và trạng thái bàn giao

Task hiện hành chỉ cập nhật Markdown, không đổi runtime/contracts/generated types,
dependencies, migrations, workbook hoặc DOCX. DB Design v1.5 `embedding_model NOT NULL`
được supersede ở mức **thiết kế** cho lexical backend; DOCX/SQL reconciliation làm
trong slice triển khai. Numeric config defaults và schema chi tiết là implementation
deliverables có review/tests, không còn là blocker chọn backend.

Production retention period/automatic deletion và quyền multi-user chưa được chốt.
Không xóa artifacts sẵn có; implementation ghi lifecycle/recovery limits và giữ
evidence cần review. Migration rollback không được coi là data recovery.
Accepted design không phải implementation acceptance, CI pass hoặc Sprint 2 Done.

OpenAI Codex hỗ trợ đối chiếu source, soạn ADR, đồng bộ docs và self-review; đã đọc
Proposal v1.4 Appendix C/D. Nhóm chịu trách nhiệm đọc/hiểu/kiểm chứng. Nguồn xác nhận
H1 ở đầu ADR không suy independent code review, mentor approval hoặc tỉ lệ đóng góp.
