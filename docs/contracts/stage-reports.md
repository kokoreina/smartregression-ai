# Stage reports v2.0.0

Nguồn chuẩn: [stages.py](../../backend/src/smartregression/contracts/stages.py).
Compatibility/handoff: [task 2.14](../development/task-2.14.md).
Report phân tích theo stage không có selection, execution hoặc fault labels.

## Version và consumers

`StageAnalysisReport.schema_version` bắt buộc là `2.0.0`. Nested v2 values thuộc
version của root; không có `schema_version` riêng. Unknown fields bị từ chối.
Các field không có default là required; nullable không đồng nghĩa optional.
`data/reason/error_code`, measurements, symbol/locations và verification fields
có defaults thể hiện trong schema. Missing measurements là null, không phải zero.

`application.reports.validate_report_json` nhận v1 hoặc v2 qua typed union, không
coerce report này thành report kia. Omitted version vẫn được nhận cho legacy v1
theo behavior cũ, nhưng không cho v2. Unsupported versions bị từ chối.
Readers v1 tiếp tục chỉ dùng v1; không gửi v2 tới chúng. `validate-report` nhận cả
hai và exit 0 chỉ nghĩa tài liệu hợp contract, kể cả analysis failed.

Legacy schemas, API paths và fixture demo không đổi. Exporter đưa public v2
models và EvidenceBundle vào OpenAPI mà không thêm route. TypeScript được sinh
từ OpenAPI; frontend demo vẫn chỉ dùng v1. Runtime real-report UI thuộc 2.18 và
phải dùng boundary validation trước render; TS types không xác thực dữ liệu ngoài.

## Identity

- `repository_id`: opaque application ID, 1–128 ASCII letters/digits/dot/underscore/
  hyphen, bắt đầu bằng letter/digit. Không tự dùng local path/URL làm ID. Mapping
  từ source repository sang ID do authorized acquisition boundary thực hiện.
- `run_id`: application cấp khi bắt đầu một run; `report_id` định danh tài liệu.
  Đây không phải framework-native test IDs. Không tự dùng lại run ID cho identity khác.
- `identity.base/target`: repository ID, full lowercase SHA-1/SHA-256 commit,
  `snapshot_id` từ manifest `snapshot/1`. Comparison mode hiện `direct_two_tree`.
- `snapshot_id` required nhưng nullable khi chưa materialize được. Failure report
  vẫn mô tả hai commit đã resolve mà không bịa hash. Nếu chưa resolve commits thì
  trả acquisition/request error; chưa có identity đủ để tạo report này.
- Graph/inventory/evidence/retrieval/review payloads và snapshots payload yêu cầu
  hash không null. Changes và EvidenceBundle yêu cầu cả hai revision có hash.
- Base=target được phép; nếu cả hai hash đã biết thì phải cùng snapshot identity.

Stage dữ liệu kế thừa repository/run từ report, không tự mang run khác. Boundary
converters kiểm declared repo/commit với identity được caller cung cấp. Producer
dataclasses không có run ID hoặc manifest hash thì không chứng minh được input
đã được đọc từ trusted snapshot; acquisition/workflow 2.13 phải bảo đảm điều đó.
Authorization, source acquisition và quyền đọc persisted reports vẫn là trách
nhiệm backend boundary; JSON hợp lệ không cấp quyền.

## Stage envelope và aggregation

Tám stage explicit: snapshots, changes, graph, impact, inventory, retrieval,
evidence, review_ordering. Không mặc định stage thiếu thành completed.

| status | data | reason | error_code | limitations |
| --- | --- | --- | --- | --- |
| not_implemented | null | Required stable code | null | Có thể có |
| not_run | null | Required stable code | null | Có thể có |
| completed | Required typed payload, có thể empty | null | null | Rỗng |
| partial | Required typed payload, có thể empty | null | null | Ít nhất một structured issue |
| failed | null | null | Required stable code | Có thể có |

Error/limitation codes dùng lowercase ASCII snake_case. Issue có path tùy chọn
trong repository-relative namespace. Không thêm raw exception/DSN/source vào code.
Partial results còn dùng được nằm ở partial stage, không giấu trong failed payload.

Root `analysis_status` phải khớp:
1. Tất cả completed → completed.
2. Có completed/partial, nhưng không phải tất cả completed → partial.
3. Không có completed/partial, có failed → failed.
4. Còn lại có not_run → not_run; tất cả not_implemented → not_implemented.

Đây là completeness của report tám stage, không phải đánh giá repository an toàn,
chất lượng retrieval hay bằng chứng đã chạy tests. 2.13 tạo trạng thái; validator
2.14 chỉ kiểm consistency. Các partial file/graph/inventory/evidence phải làm
stage tương ứng partial; impact/review không được completed khi prerequisites
changes/graph partial. Detail limitations vẫn phải được workflow bảo toàn.

## Domain payloads

**Changes:** file/module/class/function/method, change kind, reason, symbol,
previous_path và base/target ranges 1-based inclusive. Decorator thuộc span mà
producer cung cấp. `contains_changed_symbol` khác direct `content_changed`.
File records chỉ là Git metadata, không tự có source spans. Empty modules có thể
không có span. Added không có base span; deleted không có target span. Rename
cần previous_path; symbols trong renamed file vẫn có thể added/deleted/modified.
Files và component paths phải cùng coverage; IDs và component keys duy nhất.

**Graph:** một frozen revision, importer → importee, nodes theo repository paths;
edge endpoints và unresolved source phải tồn tại trong graph. Unresolved imports
giữ reference/kind/reason, bắt buộc partial. Graph không phải call graph hoặc bằng
chứng chắc chắn behavior đổi. Graph target không tự chứa deleted base component.

**Impact:** candidate và supported paths tham chiếu changed component ID. Path
có hướng **candidate → ... → changed component**, đi theo importer → importee
edges. Producer 2.04 dùng reverse traversal để tìm candidate nhưng serialize path
theo hướng trên. Nodes trong một path không lặp; nhiều paths/cycles trong graph
vẫn được phép. Direct candidate phải có direct edge/path; indirect có đường dài
hơn và không có direct edge tới origin. Direct candidate có thể có thêm path dài.
Changed candidate không cần dependency path. Base graph dùng previous_path khi
rename; target graph dùng path mới. Added không seed base, deleted không seed target.
Contract validation kiểm references/path structure, không triển khai thuật toán.

**Inventory:** chỉ target snapshot, framework pytest, native test IDs duy nhất,
complete/partial riêng. Empty completed inventory khác discovery chưa chạy. IDs
hợp schema chưa chứng minh framework đã discover hoặc có thể thực thi an toàn.

**Retrieval:** sources giữ snapshot/index/config identity, kể cả kết quả rỗng;
có thể truy vấn cả base và target bằng sources riêng. Mỗi item khai cùng provenance
của một source được khai báo, path/range/content hash/rank và optional finite score.
IDs/ranks duy nhất. Configuration identity phải pin các cấu hình ảnh hưởng kết
quả ở producer; không chọn lexical/embedding backend hoặc bịa embedding model tại
contract. Query execution, content verification và dedup algorithm thuộc 2.10–12.

**Review ordering:** giữ snapshot, rule_version, path/symbol/tier/reason. Graph và
changes phải có data; candidate paths thuộc graph. `ordering_inputs` là projection
cho legacy 2.07: bỏ non-Python file metadata, file-only parse failures và class
container-only records khỏi executable seeds; giữ original changes ở report.
Omissions có code khi ảnh hưởng phạm vi. Tuple edges giữ importer → importee.
Không dùng review tiers làm test selection hoặc xác suất fault. Producer raw 2.07
vẫn có gap nếu gọi trực tiếp với README; adapter không sửa thuật toán của VI.

**Evidence:** location thuộc một trong hai report revisions; có thể dùng base và
target cùng report. `resolution` là unverified/resolved/missing/mismatched;
`support` riêng là unverified/supported/unsupported. Defaults là unverified.
Non-default resolution cần verification_reason; support đã xác định yêu cầu
resolved source. Còn item chưa resolved+supported thì evidence stage partial.
Các field này là **khai báo của producer**, không phải attestation do JSON validator
tạo ra. 2.06 phải đọc trusted snapshot và xác minh source/support; untrusted upload
khai supported không thay thế việc đó. Không thêm source resolver trong 2.14.

## Persistence checkpoint

[EvidenceStore](../../backend/src/smartregression/application/evidence_store.py)
nhận/đọc atomic `EvidenceBundle`: identity + changes/graph/impact/evidence. Các
reference giữ đủ context để reload không mất provenance. Đây là domain boundary,
không chốt normalized SQL tables hoặc thay toàn bộ PostgreSQL design.

- Key: repository_id + run_id. Identity/payload immutable sau successful save.
- Identical canonical JSON retry là no-op; cùng key khác payload là EvidenceConflict.
  Array order có ý nghĩa. Canonicalization dùng core.git.snapshots.canonical_json.
- Save phải atomic, gồm constraint/concurrency trong adapter transaction.
- Load absent trả None; infrastructure failure dùng EvidenceStorageError.
- Application revalidate serialization và so toàn bộ identity khi reload để
  không trả bundle sai run/revision. Không catch storage failure thành not found.
- Bundle là domain data, không phải toàn bộ StageAnalysisReport. 2.20/2.13 phải
  lưu stage statuses/limitations và run/config metadata cùng run/report riêng;
  không dựng report completed chỉ vì bundle load thành công. File limitations,
  unresolved imports và evidence verification fields vẫn nằm trong bundle.
- Models frozen ở attribute level; nested lists không immutable. Application store
  helpers revalidate/deep-copy qua JSON trước crossing adapter boundary.
- 2.20/KH phải kiểm atomicity, unique/FK/foreign identity và concurrency trên
  PostgreSQL thật. Fake tests ở 2.14 không chứng minh các tính chất DB đó.

## Examples và kiểm tra

Tất cả `examples/reports/stage-report.*.json` đều DEMO:

| File suffix | Nguồn / giới hạn |
| --- | --- |
| partial | Snapshots/changes/graph/ordering dùng pure producers trên tiny Python fixture; impact paths/evidence là contract examples cho producer chưa có. Evidence unverified |
| empty | Contract-only success-empty example, không phải một actual pipeline run |
| failed | Contract-only snapshot failure; manifest hashes unknown/null |
| not-implemented | Contract-only report cho stages chưa triển khai |

Legacy `demo.json` giữ nguyên. Exporter validate các example v2 và label DEMO.

```powershell
uv run python scripts/export_contracts.py
npm.cmd --prefix frontend run contracts:generate
uv run python scripts/export_contracts.py --check
npm.cmd --prefix frontend run contracts:check
npm.cmd --prefix frontend run typecheck
uv run smartregression validate-report examples/reports/stage-report.partial.json
```

Commands yêu cầu đúng checkout/environment; kết quả thực và giới hạn ở handoff.
Runtime cross-field validation không được diễn đạt đầy đủ bởi OpenAPI/TypeScript.
