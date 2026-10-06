# 04 — Data/Storage

## Phạm vi

Repository snapshots, index/cache, report/artifacts, benchmark và migration khi có storage.
DB, vector DB, retention/persistence schema hiện pending; API contract có sẵn không chốt DB schema.

## Yêu cầu

- MUST ghi pending thay vì chọn DB để lấp module. Khi thêm storage trong task đã giao,
  nêu use case, owner/lifecycle và nguồn quyết định.
- Index/cache key MUST chứa repo identity, commit và cấu hình ảnh hưởng kết quả:
  parser/chunking/embedding/prompt/model version tùy cache. Không dùng tên branch mutable làm key duy nhất.
- MUST ngăn trộn artifacts giữa repo/run; giữ provenance khi copy/export, invalidation
  đúng lúc. Không tái sử dụng index sai snapshot vì similarity cao.
- MUST phân biệt user data, fixture, benchmark và demo; checkout/log/index/run artifacts
  không commit mặc định. Dữ liệu sinh local theo [var](../../var/README.md).
- Khi migration tồn tại, MUST ghi tác động dữ liệu, test nâng cấp và phương án backup/
  restore phù hợp. Migration mất dữ liệu không thể mặc định rollback SQL sẽ phục hồi.
- Nếu hỗ trợ nhiều người dùng, MUST kiểm tra quyền đọc report/artifact ở backend,
  không dựa vào việc UI giấu link. Hiện chưa có multi-user/auth storage.
- SHOULD giới hạn retention/output theo nhu cầu; MAY dùng file fixture nhỏ trước
  khi chọn DB nếu phù hợp use case được giao.

## Lý do

Snapshot sai làm bằng chứng và kết quả nghiên cứu sai dù từng bước không báo lỗi.

## Ví dụ

Đúng: cache key phân biệt repo A/commit X/config Y. Sai: dùng cùng thư mục `latest`
cho hai repo hoặc xóa cột rồi coi down migration tạo lại cột là khôi phục dữ liệu.

## Kiểm chứng

Review key/provenance, test collision/wrong commit/config change khi có implementation;
kiểm tra .gitignore/diff. Chưa có DB tests/migration runner thì ghi planned.

## Ngoại lệ

Benchmark fixture đưa vào Git cần provenance/license và kích thước phù hợp trong
task được duyệt; không chứa credential. Thay storage model/retention lớn theo [00](00-governance.md).

## Liên quan

[03](03-contracts-api.md), [08](08-llm-rag.md), [10](10-runner-security.md), [11](11-research-evaluation.md).
