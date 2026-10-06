# Contract v1.0.0

Nguồn chuẩn: backend/src/smartregression/contracts/models.py. Mỗi model có
schema_version mặc định 1.0.0, từ chối phiên bản khác và unknown fields. Demo root ghi
schema_version rõ ràng. Khi serialize, backend xuất version cho cả nested objects.

- AnalysisRequest: repository và CommitPair, không có outcomes/fault labels.
- CommitPair: full lowercase SHA-1 hoặc SHA-256; refs cần resolve ở Git adapter tương lai.
- ChangedComponent: file, symbol tùy chọn, loại đổi và previous_path tùy chọn.
- EvidenceReference: ID, commit thuộc cặp report, file, khoảng dòng 1-based inclusive,
  symbol/excerpt tùy chọn. Đổi/xóa có thể tham chiếu base commit.
- ImpactFinding: giải thích và ít nhất một evidence ID tồn tại trong report.
- TestSelection: framework, selected/skipped kèm reason; test IDs duy nhất và hai tập
  không giao nhau. fallback_reason null nếu không fallback. Native test ID phải do
  framework discovery tạo; bootstrap chỉ kiểm tra cấu trúc/không trùng, chưa xác thực
  ID có tồn tại trong một repo/framework thật.
- ExecutionResult: outcome, duration chưa đo null. Không có thuộc tính fault_detected.
- AnalysisReport: repository/commit pair, data_kind demo/real, analysis_status độc lập
  execution_status. not_run có results rỗng; completed có outcome cho mỗi test đã chọn.
- ErrorResponse: code/message có version, không echo code nguồn đầu vào.

analysis_status=not_implemented trong fixture để không giả mạo phân tích hoàn tất.
Chi phí USD và thời gian giây không âm, chưa đo null, không dùng số 0 giả định.
Report ID/evidence IDs chỉ định danh trong report, chưa có persistence policy.
Validator chưa xác minh đường dẫn, commit hay symbol tồn tại; đó là việc adapter sau spike.

```sh
uv run python scripts/export_contracts.py
npm --prefix frontend run contracts:generate
uv run python scripts/export_contracts.py --check
npm --prefix frontend run contracts:check
```

Export chứa API paths thật và schema của contract chưa có route. Không sửa tay
contracts/generated/openapi.json hoặc frontend/src/types/generated.ts. Cả hai được
đưa vào version control, so sánh deterministic ngay cả khi chưa git init.
Breaking change phải tăng schema version và mô tả migration; additive change cũng
review consumer do extra fields bị từ chối. Chưa có chính sách hỗ trợ nhiều version.
TypeScript không thay thế runtime validation: fixture tin cậy nhờ exporter/CI;
khi thêm upload/API report thật phải validate đầu vào trước khi hiển thị.

Generator đặt `defaultNonNullable: false` để các trường có default nhưng không có
trong `required` của schema vẫn optional, phù hợp với JSON đầu vào Pydantic chấp nhận.
Không dùng ép kiểu qua unknown để che lỗi contract. Cross-field validators (dòng,
commit, evidence/test references) do backend thực hiện, không được diễn đạt đầy đủ
bằng OpenAPI hoặc TypeScript.
