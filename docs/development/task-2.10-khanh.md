# Task 2.10 — Exclusions và index persistence của Khánh

Ngày 2026-11-05. Trần Hùng Khánh; baseline main `ee1f7db`, nhánh
`feat/khanh-task-2.10-index-storage`. Scope: phần KH trong
[brief 2.10](sprint-2-team-guide.md#task-210) và W04 của
[ADR 0004](../architecture/decisions/0004-sprint-2-integration-decisions.md), theo
[P5](../architecture/decisions/0003-local-lexical-retrieval.md). H2 giữ chunking,
tokenizer/query/scoring/search; H1 giữ composition/CLI integration. Không nhận lại
effort của hai owner đó. Phần này thêm exclusion policy, application publication/
verified load, metadata schema/adapter, artifact/recovery và kiểm chứng tương ứng.

## Exclusions trước artifact/index

[exclusion_reason](../../backend/src/smartregression/core/retrieval/exclusions.py)
version `index-exclusions/1`, chỉ trả reason, không trả excerpt của dữ liệu bị cấm.
Whole-file kiểm tra độc lập với chunk: caller không được đưa một dòng sạch của
file có secret/label ở dòng khác để vượt guard.

- Cho phép Python source/tests `.py/.pyi`; `.md/.rst/.txt` trong docs/doc/documentation
  hoặc README. Mọi phần còn lại là unsupported, không tự coi là code được index.
- Chặn `.env*`, thư mục credentials/secrets, key containers, dependency/generated/
  cache directories; chặn đường dẫn evaluation/labels/outcomes/results/coverage.
- Chặn recognized private-key headers, một số token formats và literal credential
  assignments; chặn reference outcomes/fault-label markers trong nội dung. Đây là
  conservative heuristic có false positives và không phát hiện mọi secret. Unknown
  secret, encoded data hoặc outcome không có marker cần operator review/data policy.
- Chặn NUL/non-UTF-8. Không redact rồi gán hash/range của source gốc. Exclusions làm
  giảm eligible scope; index đầy đủ scope này không có nghĩa phân tích toàn repo an toàn.

Producer H2 gọi policy **trước** tạo chunks. Publisher kiểm lại tất cả source bytes
từ authorized Git, không tin producer đã lọc. Chunk content không vào SQL metadata.

## Internal interface và compatibility

[IndexConfiguration/IndexRecord](../../backend/src/smartregression/application/index_store.py)
là internal storage boundary, không thêm public Pydantic report fields. Giữ nguyên
`index/1`, `chunk/1`, native paths/physical CR/LF/CRLF ranges và content hash. Config
hash SHA-256 của canonical JSON chứa parser/chunker/tokenizer/query/scoring/ranking/
exclusion versions, backend, nullable model và giới hạn ADR. Caller dùng versions
thật của producer; `fixture-*/1` trong test không phải release version của H2.

Manifest `configuration_id` phải bằng `configuration.digest`. Config defaults đúng
ADR: chunk 128 lines/8 KiB; index 10.000 chunks/32 MiB; query 64 terms; context
20 chunks/64 KiB; build 60s/query 5s. Có thể giảm, không tăng cap ở interface này.
Query/context limits là metadata bàn giao cho producer; adapter này không chạy search
hoặc giả enforce query policy thay H2. Build deadline được kiểm ở phase boundaries,
không phải process cancellation/hard CPU timer cho parser do caller chạy.

[publish_index](../../backend/src/smartregression/application/index_publication.py):

```python
result = publish_index(
    source,
    authorization=authorization,
    manifest=manifest,
    configuration=config,
    expected_chunks=producer_completed_count,
    attempt_id=attempt_uuid_hex,
    store=PostgresIndexStore(engine),
    artifacts=index_files,
)
```

Caller dùng actual `SnapshotSource` đã được composition tin cậy, authorization và
full frozen SHA. Application reacquire source, validate identity/config/hash/ranges,
exclusions/count/caps trước bất kỳ publication; union chunk ranges phải bao phủ mọi
dòng của mỗi eligible nonempty file, không silent partial ready. Cho phép overlap
để không tự đổi AST policy của H2; overlap vẫn tính vào total chunk bytes/count.
`expected_chunks` đối chiếu completion count, không thay source coverage verification.
Physical coverage không chứng minh semantic recall. Scope rỗng hợp lệ có zero chunks.

Artifact `index-artifact/1` chứa existing manifest + canonical config + exact chunk
bytes base64 theo thứ tự canonical. File tối đa 48 MiB bao gồm encoding/metadata;
source bytes đồng thời giữ cap 32 MiB và snapshot limits chặt hơn. Artifact key theo
whole-file hash, publication fsync/atomic link/no symlink và authorized sibling root
tái sử dụng `ReportFiles`. Report vẫn giữ cap 16 MiB; chỉ index adapter đổi cap riêng.

`load_ready_index` authorize/reacquire Git trước lookup; match repo/commit/snapshot/
index version/config, check SQL chunk rows, exclusions và regenerate expected bytes,
rồi kiểm artifact size/hash/exact equality. Metadata state hoặc tự dựng frozen
snapshot không đủ để gọi ready. Old `IndexBuild.ready()` guard giữ nguyên; API mới
là đường publication có verification, không mở provisional guard để demo.
Không chạy/import input source hoặc gọi provider/network.

## PostgreSQL lifecycle và recovery

Migration additive [20261105_05](../../migrations/versions/20261105_05_index_metadata.py)
nối head `20261104_04`; forward-only, recovery bằng consistent backup. Thêm:

- `knowledge_indexes`: key repo/commit/snapshot/version/config; deterministic index ID,
  canonical metadata/config, nullable embedding_model, building/ready/failed, attempt/error.
- `index_chunks`: repo/index/chunk key, ordinal/path/range/content hash/size; composite
  FK và uniqueness giữ scope. SQL không chứa source content. Snapshot FK tách base/
  target theo actual commit; không gắn index base vào target hay run sai.

[PostgresIndexStore](../../backend/src/smartregression/adapters/storage/index_store.py)
ghi snapshot metadata trong transaction từ prepared record; repository phải được
operator provision sẵn. Không auto-migrate/provision repository hoặc dùng schema
create_all. `begin` atomically tạo building+chunk metadata; `finish` đổi state theo
đúng attempt. Scoped uniqueness + row locks arbitrate concurrent build; cùng attempt
retry idempotent. Attempt khác gặp building trả `index_build_in_progress`; không
steal timeout build. Operator phải reconcile attempt cũ, không tự hết hạn/xóa dữ liệu.
Failed publication cho phép explicit retry cùng immutable record bằng attempt mới.

Artifact publication lỗi → failed trước ready SQL; SQL fail sau file publication giữ
orphan/building. Lost commit ack trả storage error, không tự delete/retry hoặc đổi
ready thành failed; caller dùng verified load để reconcile trước retry. PostgreSQL
và filesystem không có distributed transaction; tránh mô tả hai bước là atomic.
Artifacts không tự cleanup vì có thể đang được run/index khác dùng.

Runtime role: SELECT/INSERT hai bảng, chỉ UPDATE `(state, attempt_id, error_code)`
trên header; không UPDATE payload/chunks/DELETE/DDL. Grant deployment cần operator:

```sql
GRANT SELECT, INSERT ON smartregression.knowledge_indexes,
    smartregression.index_chunks TO smartregression_runtime;
GRANT UPDATE (state, attempt_id, error_code) ON smartregression.knowledge_indexes
    TO smartregression_runtime;
```

Không đổi permissions DB hiện có tự động. Metadata adapters là trusted application
dependencies, không exposed API hay capability cho untrusted repo content. DB role
có thể ghi state không thay việc loader bắt buộc verify source/artifact.

## Kiểm chứng và bàn giao

```powershell
& scripts/index/verify.ps1 -PythonExe <locked-backend-python>
```

Script chạy full backend/Ruff/contracts và existing dedicated PostgreSQL 17 harness.
`-DatabaseOnly` chỉ dùng rerun DB sau checks. Harness tạo container/password/DB riêng,
chỉ loopback, không dùng DB có sẵn; snapshot all metadata tables, pg_dump/pg_restore,
copy artifact tree và verify restored index qua actual SQL/artifact adapters. Index
recovery seed là synthetic fixed source có nhãn, không candidate benchmark. Input
Git fixtures trong integration tests là bytes test-owned, không input pytest execution.

Focused local: 55 pass qua external temp fixture chẩn đoán; SQL opt-in chưa tính vào
kết quả này. Đo pinned candidate phát hiện PASSWORD keyword map bị nhận nhầm thành
credential; sau thêm regression/sửa literal pattern, subset exclusions/publication
**50 pass** (22 policy + 28 application). Full suite/real PostgreSQL đang kiểm chứng;
kết quả cuối ghi tại
[verification record](../research/sprint-2/index-verification-20261105.md).

Dedicated PostgreSQL cuối: **110 passed, 2 existing candidate-specific skips**,
không failures/errors; cả 19 index cases pass. Fresh/upgrade head `20261105_05`,
exact-row backup/restore, index chunks/metadata/artifact restore và cleanup đạt.
Code/verification phần KH đã hoàn tất, sẵn sàng review. Không đánh đồng trạng thái
này với task chunker/search của H2 hoặc actual approval/merge.

Static measurement trên cached pinned trees đã được đối chiếu blob/tree/snapshot:
sqlparse có 46/93 eligible files, 299.219 bytes; TinyDB 32/65, 228.909 bytes.
Largest physical line content 177/137 bytes, dưới chunk byte cap; tổng eligible bytes
dưới index cap. Đây là phép đo source exclusions, không chunker/search/quality
benchmark; thời gian một lượt không là performance SLA. Reproduce trên dữ liệu
đã thu bằng inventory harness, không download/execute code mới:

```powershell
python scripts/index/measure_exclusions.py --candidate-root <candidate-inventory-verification-directory>
```

H2 tiếp tục chunking/scoring/search và dùng cổng này; H1 nối actual CLI/report.
Đây là bàn giao hoàn tất phần KH khi checks đạt, không tự đóng task index của H2
hay whole-sprint A01–A07. H1 review storage, H2 kiểm manifest/query compatibility;
human review chưa xác nhận. Không đổi public schema/OpenAPI/types, dependency/
lockfiles, provider/model hoặc CI. Metadata retention/ACL đa người dùng ngoài scope.

OpenAI Codex hỗ trợ thiết kế/implementation/tests/debug/docs; đã đối chiếu Proposal
v1.4 Appendix C/D. Self-review không thay review độc lập; nhóm cần hiểu/kiểm chứng
phần AI hỗ trợ, không thêm chữ ký hoặc tỷ lệ đóng góp giả.
