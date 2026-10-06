# Change Impact

## 1. Mục đích

Chuyển Git diff thành changed symbols/relationships có provenance. Tách **trực tiếp
đổi**, **có khả năng ảnh hưởng**, **đã xác minh**; dependency edge không chứng minh behavior đổi.

## 2. Khi sử dụng

Technical spike parser, Git adapter, mapping symbol/dependency hoặc evidence vị trí.

## 3. Input

Repo identity, base/target SHA và diff semantics; ngôn ngữ/parser đã chọn hoặc yêu cầu
spike, fixture cục bộ được phép dùng, giới hạn static/dynamic analysis.

## 4. Paths thường phụ trách

[core/git](../../backend/src/smartregression/core/git),
[core/impact](../../backend/src/smartregression/core/impact),
[core/evidence](../../backend/src/smartregression/core/evidence),
[fixtures](../../backend/tests/fixtures). Hiện các module này chỉ có README.

## 5. Shared files

[ChangedComponent/EvidenceReference](../../backend/src/smartregression/contracts/models.py),
[architecture](../architecture/overview.md), [backlog](../backlog/bootstrap.md).
Phối hợp RAG về snapshot và selection về mapping, không tự đổi contract chung.

## 6. Được tự thực hiện

Đọc repo fixture, khảo sát parser trong scope, sửa thuật toán/adapter khi task giao
implementation rõ, viết test cho chính SmartRegression; ghi giới hạn phân tích.

## 7. Ngoài phạm vi

Đổi ngôn ngữ MVP, clone dữ liệu ngoài phạm vi, sửa repo đầu vào, dynamic execution
hoặc quyết định merge-base policy thay nhóm; đề xuất với bằng chứng trước.

## 8. Các bước

1. Resolve/kiểm tra cặp commit theo semantics đã xác định.
2. Liệt kê đổi file/symbol và điểm parser không hỗ trợ.
3. Gắn evidence vào snapshot/dòng đúng; phân loại mức nhận định.
4. Kiểm chứng fixture và bàn giao uncertainty cho selector, không bỏ qua silently.

## 9. Edge cases

Rename/delete, binary, đổi tests/config/lockfile, merge commit/PR base khác target,
symbol trùng tên, file không parse hết, dynamic import/reflection và repo trống.
Deleted code có thể chỉ tồn tại ở base commit.

## 10. Kiểm chứng

Unit fixture cho loại diff; integration read-only repo cục bộ khi adapter tồn tại;
Ruff và contract checks nếu shape thay đổi. Không dùng LLM hay execution để giả xác minh.

## 11. Output và hoàn thành

Changed components, quan hệ và evidence tái kiểm tra được; loại ảnh hưởng/giới hạn
parser rõ; no-data/partial không bị biến thành kết luận không có ảnh hưởng.

## 12. Prompt giao việc

> Dùng Change Impact, đọc rule 09. Thiết kế fixture cho add/modify/delete/rename và
> đề xuất output ChangedComponent/EvidenceReference theo contract hiện tại. Task này
> chỉ sửa tài liệu spike và fixtures tĩnh trong backend/tests/fixtures, không chọn parser,
> clone repo hoặc chạy code đầu vào. Ghi case không thể mô tả và đề xuất thay đổi riêng.

## 13. Bàn giao

> Repo/commit semantics: …; paths: …; changed/possible/verified: …; evidence: …;
> parser limits: …; checks: …; đầu vào selector cần lưu ý: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[01](../rules/01-architecture.md), [06](../rules/06-testing-quality.md),
[09](../rules/09-impact-selection.md), [10](../rules/10-runner-security.md) khi ingest repo.
