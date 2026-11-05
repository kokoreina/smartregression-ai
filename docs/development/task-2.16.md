# Task 2.16 — component-to-existing-test mapping

Mốc implementation 2026-11-04. Khánh, estimate 8h; H2 reviewer **assigned**
ngày 2026-11-05 theo [ADR 0004 §4–5](../architecture/decisions/0004-sprint-2-integration-decisions.md), chưa xác nhận review completed. Theo
[team guide](sprint-2-team-guide.md#task-216). User giao bắt đầu 2.16 sau khi kiểm
dependencies; nhánh `feat/khanh-task-2.16-test-mapping` từ main
`53356e6ada1a145a3cb988a926928e838136e152`. Baseline đã merge 2.04, inventory
2.08/09, PostgreSQL foundation, native IDs và 2.17. Không nhận thay 2.19 hoặc đổi
task ownership. KH là writer của mapping và observer metadata phục vụ nó; H1 vẫn
giữ shared canonical contracts/workflow, H2 sở hữu graph/impact algorithms.

## Behavior và phạm vi

1. Nhận run identity, authorized frozen target, canonical changes/graph/impact stages,
   inventory stage/ID/config và optional trusted test-source receipt.
2. Validate lại models dù caller có thể dùng model_copy/mutable lists để vượt
   constructor validation. Chặn wrong repo/run/SHA/snapshot/config/inventory digest,
   unknown/duplicate IDs, unsupported impact paths và graph endpoints.
3. Application kiểm graph nodes/edges/unresolved với actual 2.03 producer trên
   frozen source; JSON schema alone không xác nhận import edge có trong source.
   Caller vẫn phải cung cấp genuine authorized changes/impact của đúng run.
4. Chỉ nối exact native test ID đã có trong inventory với file do pytest observer
   ghi từ `item.path`, relative to root. Không split nodeid theo `::`, không trim,
   lowercase, Unicode-normalize hoặc suy test file từ tên/hint/param text.
5. Join file đó với actual 2.04 candidate/path cho changed component. Ghi candidate
   ID, path ID và toàn bộ importer → importee route; self-file change dùng route
   một node, không bịa import edge. Giữ nhiều supported routes thay vì chỉ shortest.
6. Granularity duy nhất hiện có: `test_file_to_component_module`. Function component
   được map qua module chứa nó, không chứng minh từng test function gọi symbol,
   fixture hoặc behavior cụ thể. Không coi static reachability là verified fault.
7. Mỗi existing ID không có supported relationship có unresolved reason; mỗi
   changed component không có test được map cũng có reason. Deleted component
   chỉ ở base là `component_deleted_no_target`; rename dùng new target path.
8. Partial/inactive/failure và upstream limitations được bảo toàn. Partial inventory
   vẫn có thể cung cấp positive relationships đã quan sát nhưng toàn output partial;
   failed/not_run inventory không thành successful empty mapping. Complete empty
   không chứng minh component không có test/rủi ro. `safe_to_exclude` luôn false.

Không có selected/skipped lists, execution, full-suite fallback, LLM/RAG, outcomes/
fault labels, production selector hoặc runtime test coverage. Rule dùng được ở Sprint 2
nhưng không thay selector policy Sprint 3. Resource bound 50,000 relationships trả
`mapping_relationship_limit` thay vì truncate và báo completed.

## Files và cách gọi

- `core/selection/mapping.py`: immutable internal result, provenance, relationships,
  unresolved records và pure structural mapper.
- `application/test_mapping.py`: validate inventory write/collector receipt và
  use case kiểm graph against frozen sources, không tự thu thập input.
- `scripts/inventory/collect.py`: trusted observer ghi item.path cho mỗi node ID.
- `adapters/runners/candidate_inventory.py`: validate metadata frame/ordered ID set,
  path safety, isolation và fixed candidate scope trước publish observation.
- Tests: known direct/indirect/self-file relationships, opaque/Unicode/param IDs,
  wrong identity/config/version, unknown/duplicate/source unavailable, forged graph,
  partial/failed/empty, deletion/rename, bounds, JSON và real Git/static producers.

Consumer ở H1/2.13 hoặc Sprint 3 gọi explicit application API:

```python
receipt = sources_from_collection(inventory_write, collector.last_observation)
mapping = map_inventory_components(
    inventory_write,
    snapshot=authorized_pair.target,
    changes=changes_stage,
    graph=graph_stage,
    impact=impact_stage,
    test_sources=receipt,
    evidence=evidence_payload_if_referenced,
)
```

`InventoryWrite` lấy từ validated preparation hoặc actual PostgreSQL load; collector
observation phải của cùng attempt/stage/config. API không có quyền authorization
chỉ từ JSON. Nếu chỉ có inventory legacy không có source metadata, bỏ receipt để
nhận explicit unresolved; không bịa item.path từ nodeid. Canonical InventoryPayload
và DB inventory rows không thay đổi, không nhét metadata mới vào schema dùng chung.
Quyết định tích hợp đã accepted ADR 0004 §4: H1 nối API và xuất versioned,
run/report-bound mapping artifact đi kèm report; KH giữ API, H2 review semantics.
Task implementation gốc mới xuất sidecar qua harness, workflow chưa tích hợp.
Public report field/UI chỉ khi có consumer cụ thể và compatibility review; không
mở rộng contract hoặc thêm mapping dashboard trong task tài liệu này.

Result provenance: repository/run/full target SHA/snapshot, inventory ID, collector
config digest, inventory-stage content hash, changes/graph/impact stage hashes,
receipt content hash và rule `pytest-import-file/1`. These hashes bind supplied data;
không xác thực một caller cố tình forge mọi inputs. Serialized sidecar không được
tin để dispatch; phải revalidate/recompute trong authorized application boundary.

## Observer compatibility và security

Private worker frame đổi từ `inventory/1` sang `inventory/2`, thêm `test_sources`
(`pytest-item-path/1`). Host và worker deploy cùng nhau; strict parser reject version
cũ/unknown/missing fields. Collector version tăng `candidate-inventory/2`, worker/
adapter hashes làm config mới, không tái sử dụng receipt/version cũ để suy file.
`InventoryPayload`, public root `2.0.0`, global Text, OpenAPI/types và DB migrations
không đổi. Existing reports/inventory không bị rewrite hoặc giả hồi phục metadata.

Frame vẫn chịu cap 512 KiB gồm logs + structured metadata. Thêm metadata có thể làm
output-limit sớm hơn; không nới cap, bỏ IDs hoặc cắt metadata để qua kiểm tra.
Dependency image/lock, approved candidate SHA/tree và resource/isolation policy giữ
nguyên. Candidate code/conftest/import/build hook chỉ chạy trong Docker worker,
không có host/web fallback. Existing reviewed-candidate threat model áp dụng; không
quảng cáo arbitrary hostile-code protection hoặc metadata không thể bị input code
trong cùng pytest process ảnh hưởng.

## Kiểm chứng hiện tại

Test-first run fail do module chưa tồn tại. Sau implementation: 45 focused tests
pass, gồm real Git acquisition/diff/graph/impact mapping và receipt fixtures. Sandbox
integration run dùng temporary-fixture diagnostic bên ngoài Git vì Windows ACL;
không thay ordinary-terminal default suite. Ruff lint/format và export --check pass;
PowerShell parser check pass. Không sửa schema/TS/DB nên không tự chạy lại DB acceptance.

**Operator run đã pass:** Khánh chạy script trong PowerShell thường, backend host
Python 3.14.5/pytest 9.1.1: **609 passed, 75 skipped, 1 warning cũ**, 63.67s.
Skips: 74 PostgreSQL opt-in tests và một POSIX FIFO trên Windows; task này không
đổi SQL/DB boundary nên không tuyên bố chạy lại DB acceptance. Ruff lint/format
(230 files), exporter --check pass. Hai candidate collect hai lần giữ exact IDs,
order và item.path metadata; mapping probes pass với explicit partial/unresolved
và stale receipt rejection. [Evidence record](../research/sprint-2/mapping-verification-20261104.md)
ghi hashes/giới hạn. Implementation và local verification sẵn sàng cho independent
review, không tự đánh dấu nhóm đã nghiệm thu. Follow-up console pytest của CI phát
hiện helper import phụ thuộc working directory; đã sửa fixture loader (không đổi
production behavior), console subset 44 tests và real-Git diagnostic case pass.
Final Ruff pass với 231 files; publication CI vẫn cần đối chiếu riêng.

Từ root checkout trong PowerShell thường:

```powershell
& scripts/mapping/verify.ps1 -PythonExe '<existing locked backend Python executable>'
```

Script chạy default pytest, Ruff, exporter, build locked dependency image; collect
hai lần mỗi candidate và so exact IDs/order/source metadata; xuất mapping examples.
`-RuntimeOnly` chỉ dành debug khi source checks đã pass. Evidence mỗi lượt ở UUID
mới dưới ignored `var/`; giữ failed attempts, không commit source/logs/dumps.

Candidate probes có label `mapping_probe_with_synthetic_component_seeds`:
sqlparse/lexer.py → tests/test_keywords.py, tests/test_parse.py;
tinydb/operations.py → tests/test_operations.py, tests/test_tinydb.py.
Seeds là fixture giả lập thay đổi để kiểm structural joins với actual collected
IDs/files và source/graph thật, **không phải actual commit diff, benchmark hoặc
khuyến nghị test selection**. Actual changed-component integration có fixture Git
riêng trong tests. Probe giữ unresolved/partial cho test files không có supported
relationship và kiểm stale receipt bị từ chối. Không dùng output đã quan sát để
tự điền expected native IDs; expected là file sets định trước, IDs lấy từ actual
inventory/observed paths rồi so exact membership.

## Bàn giao và AI disclosure

- H2 review granularity/import paths và limits của 2.16, không suy call graph.
- H1/2.13 consume explicit API khi nối stage, chưa sửa shared analysis.py trong task.
- AN/2.17, VI/2.18 giữ unresolved/partial và native ID; UI integration là việc riêng.
- 2.19 có thể tái dùng boundaries/evidence nhưng không đếm unit tests task này thành
  đã hoàn tất toàn bộ cross-module regression campaign.

OpenAI Codex hỗ trợ implementation/tests/self-review/tài liệu. Khánh cần đọc, hiểu
và kiểm chứng trước submission. Independent team review/approval còn pending;
không giả mentor approval, phần trăm đóng góp hoặc outcomes/metrics đã đo.
