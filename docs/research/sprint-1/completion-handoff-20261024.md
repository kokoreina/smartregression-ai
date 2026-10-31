# Bàn giao bổ sung task 1.01–1.11 — 2026-10-24

Nguyễn Tấn Huy giao thực hiện phần độc lập còn thiếu của Sprint 1. Đây là handoff
cho đợt tích hợp mới, **không phải task 1.12 hoặc quyết định nghiệm thu sprint**.
`review.md`, handoff cũ và tên owner được giữ nguyên. Chưa có human review độc lập.

Baseline main `7989209`, working tree ban đầu sạch; PR nghiên cứu phụ thuộc branch
`feat/s1-git-discovery-spike`. Merge PR kỹ thuật trước PR nghiên cứu, không tự merge.
PR kỹ thuật: [#9](https://github.com/kokoreina/smartregression-ai/pull/9), commit
`23bc998`; branch tài liệu `docs/s1-research-rag-completion` dùng nhánh kỹ thuật làm
base. Sau khi #9 merge, xác nhận/retarget base PR tài liệu về main trước merge.
Các thay đổi được Codex hỗ trợ Huy theo brief, không gán đóng góp này cho thành viên
khác. Các draft đã có được tái sử dụng, không tạo pipeline/framework song song.

## Ma trận AC và đầu vào tiếp theo

| Task / owner guide | Đầu ra và bằng chứng hiện có | Trạng thái / phần chưa đủ |
| --- | --- | --- |
| 1.01 Huy | [RQ](research-questions.md), năm baseline/ablation, metrics/N/A/overhead/split; [source audit](research-sources-20261024.md) kiểm nguồn primary; bổ sung impact precision/recall | Draft đủ review; Việt review và nhóm chốt protocol trước held-out |
| 1.02 Việt | Checklist giữ nguyên cấu trúc, [note bổ sung](candidate-evidence-20261024.md) cập nhật D05/nguồn target và giới hạn phép đo | Draft có evidence bổ sung; Huy cần review thật, không dùng stars để suy contamination |
| 1.03 Việt | Hai SHA/license và test/config source được đọc lại qua GitHub; đề xuất sqlparse chính/TinyDB dự phòng | Candidate chưa được chọn; chưa đo candidate build/discovery/suite size; thiếu dependency/plugin/environment review |
| 1.04 Huy | Mock access phân biệt 200/401/403/404/service error, invalid input không gọi transport, timeout; tests cũ vẫn qua | Locally verified ở mức double được guide cho phép; live access/auth chưa làm; An review |
| 1.05 Khánh | [Environment](test-environment.md), Limits validation, Docker fixture guard/quota/failure cases; Python 3.14.3/pytest 9.1.1 đã chạy | Locally verified fixture; production limits, plugin/version matrix còn proposed; An review |
| 1.06 An | Draft immutable SHA/direct two-tree/PR merge-base/PR-head changes và failure semantics | Thiết kế đủ để review; Q01–Q09 PR policy chưa accepted; spike chỉ dùng hai full SHA, không tự chốt thay nhóm |
| 1.07 An | [Git spike](git-diff-spike.md), code/tests diff/rename/delete/missing SHA; AST symbol/import edges; [technical handoff](implementation-handoff-20261024.md) | Locally verified fixture; Phạm Phan Hoàng Huy review; SHA-256 Git repo và dynamic imports chưa kiểm chứng/không hỗ trợ đầy đủ |
| 1.08 Huy | In-memory UUID/state machine, timestamps/error codes, duplicate/retry giới hạn; tests cũ vẫn qua | Locally verified prototype; Khánh review; không có durable job/production concurrency/cancellation |
| 1.09 Phạm Phan Hoàng Huy | [RAG scope](rag-scope.md): nguồn index, metadata/SHA/path/symbol, secret/provenance/labels exclusion, injection/budgets và cases | Draft đủ review thiết kế; An review; không index/provider/egress implementation |
| 1.10 Khánh | [Selection policy](selection-policy.md) giữ decision table và invariants; nối dependency RAG mới; fixture chỉ kiểm ID/snapshot guards | Draft đủ review thiết kế; Phạm Phan Hoàng Huy review; không selector production/recall claim |
| 1.11 Huy | [Protocol](../evaluation-protocol.md) và [report template](evaluation-report-template.md): cohorts, independent impact/fault labels, baselines, N/A, failures/exclusions và leakage | Draft đủ review; Việt/Khánh cung cấp environment/cohort; sample/budget/repeats cần quyết trước experiment |

Có thể dùng mocks cho 1.04/1.08 theo guide; không ép triển khai auth/job platform
production để đóng spike. Không coi thiếu human review là lý do dừng implementation
đã giao, nhưng không tự điền người đã review/approved.

## G1 và giới hạn bằng chứng

Technical handoff ghi exact commands, runtime/image ID, SHA, observations và artifact
local. Hai full SHA → đọc diff → materialize immutable fixture blobs → discover native
IDs trong Docker → freeze selection → chạy một test đã được kiểm chứng thật. Có
symbol/dependency prototype và failure/timeout/output/cleanup evidence.

Không chạy `git checkout` trong repo ngoài; materialization từ `cat-file` tránh hooks,
filters và thay đổi working tree. Đây là fixture-only equivalent cho snapshot checkout
trong spike, cần nhóm review chấp nhận phạm vi gate. Chưa chứng minh end-to-end trên
candidate hoặc arbitrary repository; không dùng synthetic cases làm real faults.
Các ảnh/container đã build chỉ phục vụ spike; không deploy dịch vụ sản phẩm.

## Quyết định còn cần người thật

| Quyết định | Đề xuất / tác động | Người phối hợp |
| --- | --- | --- |
| Dataset target | Proposal v1.4: >=2 repo, >=30 pairs, >=15 verified fault-bearing cases; Project Plan v1.1: 50 pairs. Dùng target Proposal làm cơ sở thảo luận, không tự chốt 50 hoặc giả đã thu thập | Huy tổng hợp, nhóm/mentor xác nhận trước held-out |
| Repeat/budget/split | Proposal nêu ba model runs nếu budget cho phép; phải ghi budget và deviations, giữ cùng source case trong một split | Huy/Việt và nhóm |
| Candidate | sqlparse chính và TinyDB dự phòng là đề xuất sau source/license inspection; chưa nhận dataset | Việt + An/Khánh kiểm reproducibility |
| PR semantics | Giữ Q01–Q09 của An là proposed; fixture direct SHA không quyết policy PR production | An/Huy và affected consumers |
| Input support/isolation | Python/pytest accepted ở ADR 0002; version/plugin/general worker policy chưa được mở rộng từ fixture | Khánh/An và nhóm |
| RAG/provider | Scope thiết kế đã có; provider/index/storage/retention/egress cần decision riêng | Phạm Phan Hoàng Huy/Huy |

Không có câu trả lời của nhóm không được coi là approval. Những việc này không
chặn các docs/spike đã hoàn thiện; chúng chặn nghiệm thu hoặc experiment tương ứng.

## Kiểm chứng, bảo toàn và AI use

Xem technical handoff cho test/lint/schema/G1 results. Đợt nghiên cứu chỉ thay docs;
kiểm local links/fences/UTF-8 trên 20 docs thay đổi/mới, diff và credential-pattern
check đạt (không là general secret scanner). Full backend cuối: **49 passed**;
Ruff lint/format và exporter --check đạt. PR kỹ thuật ghi exact G1 command và
artifacts mới. Candidate evidence đọc đúng sáu file/đoạn từ hai repo và metadata commit, không
kiểm toàn candidate history. Primary paper audit chỉ đọc các phần được chỉ rõ.
Proposal/Project Plan được trích XML text/table liên quan, không audit sơ đồ/objects;
Appendix C/D AI policy đã đọc, chữ ký cũ không duyệt phần mới.

Không đọc .env, không gọi LLM trả phí/benchmark, không sửa credentials, DB hoặc CI;
không gửi source riêng tư ra ngoài. Huy cần đọc/hiểu/chỉnh phần AI hỗ trợ, thành viên
thật review theo task; không có tỷ lệ AI/đóng góp, chữ ký hoặc mentor approval giả.
Không commit artifacts `var/`, không sửa tác giả cũ; identity mới kokoreina với email
đã xác nhận phải được kiểm trước commit. Không tự push main/merge/deploy.

Phần tiếp theo: review hai PR, nhận quyết định ở bảng trên, chuẩn bị candidate
environment nếu được giao, sau đó Huy thực hiện 1.12 trong task riêng.
