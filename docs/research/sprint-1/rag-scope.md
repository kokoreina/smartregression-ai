# 1.09 — Phạm vi RAG và provenance cho Sprint 1

Trạng thái: draft đủ để review thiết kế; chưa index/gọi model. Owner theo guide:
Phạm Phan Hoàng Huy; Codex hỗ trợ Nguyễn Tấn Huy soạn theo brief tích hợp ngày
2026-10-24. Reviewer đề xuất: Đỗ Hà An. Không giả tác giả hoặc phê duyệt của owner.
Nguồn: [rule 04](../../rules/04-data-storage.md), [08](../../rules/08-llm-rag.md),
[protocol](../evaluation-protocol.md), [selection policy](selection-policy.md).

## Dữ liệu được phép và bị loại

| Input | Quy tắc thiết kế |
| --- | --- |
| Python source | Chỉ snapshot base/target đã authorize; giới hạn dung lượng; không import/execute để index |
| Tests có sẵn | Nội dung base/target có provenance; inventory runnable chỉ ở target |
| Tài liệu/build config | Chỉ đường dẫn cho phép ở snapshot; config thay đổi phải chuyển uncertainty/fallback |
| Deleted code | Truy hồi ở base với vai trò deleted/base; không gán dòng đó vào target |
| Symlink/submodule/binary/generated/vendor | Loại khỏi spike; ghi unsupported, không diễn giải thành không ảnh hưởng |
| Secrets/.env/keys/credentials | Không đọc để index; denylist trước mở file, không đưa vào chunk/log/prompt |
| Fault labels/full-suite outcomes/evaluator artifacts | Không vào index, context hoặc selector dưới bất kỳ alias nào |
| Future commits, issues/fix sau target | Loại khỏi selector context; chỉ evaluator được dùng nếu protocol cho phép |

Cho phép đọc source không có nghĩa được gửi source ra ngoài. Egress mặc định không
được phép; provider/model/index vẫn pending D06. Chưa có secret scanner tự động;
đường dẫn allowlist không bảo đảm nội dung sạch. Trước egress tương lai cần review
quyền/license, secret filtering và policy được chấp nhận. Không sao chép source
candidate vào tài liệu này; ví dụ bên dưới là metadata tổng hợp.

## Khóa snapshot, chunk và cache

Đề xuất khóa index: repository identity + full commit SHA + parser/chunking revision
+ embedding model/config revision (nếu sau này có embedding). Prompt/model/retrieval
policy version thêm vào cache kết quả suy luận. Branch name không là khóa snapshot.
Cache hit sai repo/SHA/config phải bị từ chối; không fallback sang index gần nhất.

Chunk cần repo, SHA, snapshot_role, path, symbol (nullable), line_start/end, content
hash, parser/chunker version và provenance. Dòng nằm trong blob đúng commit; không
đưa symbol tự suy đoán thành ground truth. Chunk module-level là loại riêng.

```json
{
  "data_kind": "synthetic_example",
  "repository": "fixture/demo",
  "commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "snapshot_role": "target",
  "path": "calc.py",
  "symbol": "add",
  "line_start": 1,
  "line_end": 2,
  "content_hash": "pending-computation",
  "parser_version": "python-ast-spike-v1"
}
```

Đây là proposed internal metadata, không phải extension của public EvidenceReference.
Khi triển khai phải tính hash, resolve vị trí và review contract producer/consumer;
không dùng placeholder này như bằng chứng thực. Source giữ trong artifact có quyền
truy cập; log chỉ ID/hash/codes đã redact. Retention và multi-user ACL còn pending.

## Untrusted text, budget và failure

Source/comment/doc có câu yêu cầu bỏ validation hoặc tiết lộ credential vẫn chỉ là
dữ liệu. Host quyết repository scope, tool permissions và budget. Không chạy command
trích từ chunk/model. Không cho retrieved content sửa system instruction. Đầu ra
model cần qua schema, inventory membership, snapshot và evidence validation.

Đề xuất spike thiết kế: giới hạn 16 chunks và 12.000 ký tự context; token/cost/time/
attempt budget theo model cần chốt trước live call. Đây không phải default production
hay kết quả đã đo. Thiếu context/parse/usage phải báo unknown; không gán cost = 0.

| Case | Kết quả mong đợi khi triển khai |
| --- | --- |
| Repo/SHA/config khác cache key | Không reuse; index lại hoặc stop khi chưa có dữ liệu |
| Deleted symbol chỉ có base | Evidence base; inventory/test IDs vẫn target |
| Chunk chứa instruction injection | Không thay quyền/policy; reject nếu đề xuất vi phạm validator |
| Label/outcome file đổi tên thành docs | Loại theo provenance/ownership, không chỉ extension |
| Retrieval rỗng hoặc quá budget | Ghi unavailable/truncated; không kết luận impact rỗng |
| Unknown test ID/evidence sai ảnh hưởng selection | Reject L; full-suite nếu inventory đầy đủ và thực thi được, nếu không thì stop theo 1.10; sai repo/SHA phải stop |
| Parser/dependency thiếu | Conservative full-suite/stop theo policy, không safe/passed |

Các dòng trên là acceptance cases thiết kế, chưa phải runtime tests cho RAG.
An review snapshot/symbol metadata; Khánh review fallback; Việt review leakage;
Huy tích hợp protocol. Provider, embedding, index storage, egress, budget và retention
cần quyết định riêng. Không triển khai provider/vector DB để đóng task tài liệu này.
