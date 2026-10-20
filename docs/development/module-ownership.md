# Đề xuất 5 vùng trách nhiệm

Chưa gán tên người và không tạo CODEOWNERS giả. Nhóm tự thống nhất và luân phiên review.

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
