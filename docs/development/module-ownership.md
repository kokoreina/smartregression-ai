# Đề xuất 5 vùng trách nhiệm

Đề xuất vùng công việc bên dưới là lịch sử bootstrap; không tạo CODEOWNERS giả.
Phân công Sprint 2 theo [ADR 0004 §5](../architecture/decisions/0004-sprint-2-integration-decisions.md)
đã accepted ngày 2026-11-05 qua H1 truyền đạt cả nhóm. Assigned khác review completed;
contract/analysis writer H1, migration writer KH, module owners theo team guide.

Phân công theo tên, task và dependency cho Sprint 1 được đề xuất trong
[hướng dẫn phối hợp Sprint 1](sprint-1-team-guide.md); chưa phải quyết định nhóm đã duyệt.

| Vùng | Trách nhiệm/đầu ra | Phối hợp |
| --- | --- | --- |
| 1. Git & code model | commit/diff, changed components, spike parser | 2, 3 |
| 2. Evidence & retrieval | evidence provenance, retrieval interfaces, RAG data policy | 1, 3 |
| 3. Impact & selection | findings, validate test IDs, fallback policy | 1, 2, 5 |
| 4. Application & UI | contracts, API/CLI, dashboard, schema generation | mọi vùng |
| 5. Execution & evaluation | worker boundary, CI, evaluation protocol/dataset | 3, 4 |

Contract là tài sản chung: mọi thay đổi cần review từ bên producer và consumer.
Mỗi task có một người thực hiện, một người review; không coi ownership là độc quyền.
