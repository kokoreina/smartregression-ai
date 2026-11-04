# Test mapping 2.16; selector chưa triển khai

`mapping.build_component_test_mapping` ghi positive relationships giữa changed
component và existing target test IDs qua graph/impact paths. Native ID không bị
parse/trim để đoán file; file provenance đến từ trusted pytest `item.path` receipt.
Granularity là test-file → component-module, không phải function-call coverage.
Receipt gắn repository/run/target snapshot/inventory/config và inventory content.
Missing/partial/failed/unknown/unresolved giữ lý do, không suy safe exclusion.

Consumer nên dùng `application.test_mapping.map_inventory_components`, tái kiểm
graph với source bytes từ frozen snapshot. Pure core API chỉ kiểm structural
references, không attestation source acquisition. Không tự tin JSON/hash do caller
bất kỳ cung cấp là bằng chứng đã chạy collector hoặc đã xác thực repository.

Đây là internal handoff `component-test-mapping/1`, chưa thêm field vào public
report, endpoint, migration hoặc selector/dispatch. Chi tiết và giới hạn:
[task 2.16](../../../../../docs/development/task-2.16.md).
Full-suite outcomes/fault labels không là mapping input.
