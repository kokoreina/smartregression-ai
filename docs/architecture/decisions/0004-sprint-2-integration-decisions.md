# ADR 0004 — Quyết định và kế hoạch hoàn tất Sprint 2

- Status: **accepted**, ngày **2026-11-05**; phạm vi 11 mục dưới đây.
- Nguồn quyết định: Nguyễn Tấn Huy (H1) truyền đạt sự đồng ý **của cả nhóm**:
  “Tôi và nhóm đã đọc qua toàn bộ các plan của bạn và cả nhóm đã quyết định chốt
  sẽ làm như bạn, đây là ý cả nhóm k phải mình tôi.” User giao chính thức hóa bằng
  brief tiếp theo; đây không phải suy đoán đồng thuận từ code, merge hoặc CI.
- Baseline: fetch `origin/main` thành công trong lượt này, SHA
  `07452660ab37699b0fbc28864601ea9e653f1bd3`. Checkout tài liệu còn có commit P5
  `0c9ec43ea30b014b14f32192fff82f792fac51e5`; P5 chưa nằm trong main tại mốc fetch.
- Bổ sung [ADR 0003/P5](0003-local-lexical-retrieval.md), thay các pending Sprint 2
  tương ứng trong ordering/UI/checkpoint/guide. Không thay mục tiêu MVP hoặc estimate.

Accepted design, phân công review, implementation và acceptance là các trạng thái
riêng. Lượt này chỉ đổi tài liệu; không thay runtime/contract/migration/generated
types, không đánh task Done hoặc xác nhận review/mentor approval chưa xảy ra.
LLM provider/model, production selector/runner, durable jobs, retention/ACL và
research campaign thuộc các mục 12 trở đi của audit, **ngoài scope**.

## Bối cảnh và cách chọn

Main có snapshot/diff/graph, các module impact/ordering, inventory/mapping và
manifest/context validation riêng. `application/analysis.py` còn để impact/evidence/
retrieval `not_implemented`, inventory mặc định `not_run` nếu thiếu collector,
ordering chưa nối. `core/retrieval/index_manifest.py` vẫn chặn `ready()` bằng
`trusted_snapshot_acquisition_required`. UI mở report JSON, API chỉ health.

Hướng được chọn là giữ module/quy tắc hiện có, xác định interface và nối một luồng
thật có bằng chứng. Đổi sorting, thêm public fields/dashboard hoặc framework storage
trước khi có consumer sẽ tăng số điểm tích hợp và công việc sửa lại. Chưa có benchmark
chứng minh các lựa chọn dưới đây tối ưu chất lượng retrieval hoặc tốc độ sản phẩm.

## 1. Graph completeness

Completeness lấy từ producer status, evidence và limitations. Không suy `partial_graph`
chỉ vì edges rỗng. Producer thành công nhưng không quan sát dependency dùng
`no_dependency_edges_observed` khi phù hợp. Parse failure, unresolved hoặc cap làm
thiếu dữ liệu giữ partial và nguyên nhân. `not_run`/`failed` không thành successful
empty. Caller chỉ có edges phải thể hiện thiếu completeness metadata, không tuyên bố
đầy đủ; mã/shape cụ thể được owner ghi trong implementation contract.

Giữ giới hạn static analysis ngay cả khi không có runtime error. Gap hiện tại:
`order_for_review` tự thêm partial khi edges rỗng; `order_from_stage_changes` vẫn đi
qua nó; `order_from_impact_payload` phân biệt producer partial và no-edges. Phải đồng
nhất các đường gọi và cập nhật expected fixtures cũ, không xóa kiểm tra lỗi.

H2 producer semantics; H1 application; AN propagation; VI ordering/UI. Acceptance:
cùng inputs/evidence cho cùng semantics qua các entrypoints; no-edges, unresolved,
parse/budget, failed/not_run và thiếu metadata không bị gộp thành safe empty.

## 2. Review ordering 2.07

Giữ `(tier, path, symbol or "")` tăng dần: changed executable → direct → indirect.
Distance chỉ giải thích, unknown giữ `None` cùng reason; không bịa distance hoặc
đổi sang distance-first. Input permutation, duplicates và cycles phải deterministic.
2.12 context ranking có lexical score **trong tier** và tie-break riêng; không đổi
rule 2.07. VI owner; H2 review semantics; H1 kiểm consumer. Đóng câu hỏi distance-first.

## 3. Executable, docs và config projection

Giữ mọi changed files; UI phân biệt executable/dependency impact với docs/config/
unsupported changes. README không thành executable. Config chưa được analyzer hỗ
trợ không thành “không ảnh hưởng”; Python parse failure hiện đúng partial/unsupported.
Authorized docs vẫn có thể là context bổ sung. Deleted evidence dùng base, context
hiện hành dùng target với identity riêng.

Ưu tiên projection từ contract hiện có; chỉ đề xuất public extension khi thiếu thông
tin cụ thể. AN classification/evidence; H1 projection; VI UI. Acceptance: docs-only,
config-only, mixed, deleted, parse failure không mất paths hoặc limitations.

## 4. Mapping 2.16 integration

Dùng application API hiện có với authorized snapshot, actual stages, inventory và
trusted collection receipt. Xuất versioned mapping artifact đi kèm report, gắn đúng
run/report/identity và digest; giữ exact native IDs, relationships, provenance,
unresolved. Mapping chỉ ở mức `test_file_to_component_module`, không là function
coverage, selector hoặc safe exclusion. Serialized artifact không cấp quyền dispatch;
consumer phải validate/recompute trong authorized boundary.

KH mapping API; H1 wiring/artifact; H2 semantics; VI chỉ tham gia nếu có UI consumer.
Không tự thêm mapping dashboard/public field. Acceptance: real workflow tạo artifact
đúng inventory, wrong identity/receipt/IDs bị reject hoặc expose đúng unresolved;
failed/partial inventory không thành completed empty.

## 5. Ownership và review responsibility

Phân công review dưới đây **đã accepted**, không có nghĩa review đã thực hiện.
Giữ accountable/effort task gốc; reviewer phải khác tác giả phần được review.

| Boundary | Chủ trì/writer | Reviewer được phân công |
| --- | --- | --- |
| Graph/impact semantics | H2 — Phạm Phan Hoàng Huy | AN — Đỗ Hà An |
| Ordering/UI states | VI — Đặng Đại Việt | H1 — Nguyễn Tấn Huy; H2 kiểm ordering semantics |
| Acquisition/base-target | AN | H1 |
| Mapping 2.16 | KH — Trần Hưng Khánh | H2 |
| Chunk/query/retrieval | H2 | VI; AN kiểm identity, KH kiểm exclusions/storage budgets |
| PostgreSQL domain metadata/recovery | KH | H1 |
| Shared contracts/workflow | H1 | AN; VI kiểm consumer compatibility |
| Cross-module 2.19 | KH accountable; AN identity/evidence, KH inventory/runner | VI |

H1 tổng hợp acceptance, owner xác nhận deliverable của mình. Giữ reviewer gốc cho
các task không có phân công thay thế ở bảng này; chưa gán thì ghi chưa gán. Foundation
2.20 vẫn H1 accountable và AN review; domain index migrations do KH viết/H1 review.
Nếu reviewer là đồng tác giả, bố trí người khác đủ hiểu boundary và ghi nhận việc
đổi reviewer, không dùng self-review để thay independent review.

Một writer cho cùng contract/schema/migration tại một thời điểm. Mỗi PR bàn giao
behavior, file/contract impact, commands/results, limits và reviewer thực tế.
Trạng thái `assigned`, `review completed`, `acceptance recorded` phải tách biệt.

## 6. Demo và acceptance

Luồng chung: authorized frozen base/target → changes/graph/impact → evidence và
target inventory/mapping → verified index/retrieval → report/artifacts → UI mở file.
File-based inspection đáp ứng 2.18; không thêm API service chỉ để demo. Thiết kế
expected trước khi chạy, không chép observed output thành oracle. Fixture/demo gắn
nhãn riêng với actual authorized candidate integration.

| Case | Expected/điều kiện đạt | Owner và evidence cần lưu |
| --- | --- | --- |
| A01 Luồng thành công | Actual producers, matching repo/run/base/target/config, paths/hash resolve được, không stage bắt buộc nào còn not_implemented | H1 tổng hợp commands, commit/config, report và manifest artifact digests |
| A02 Docs/config/no edges | Mọi changed paths còn nguyên; không auto partial từ no-edges hoặc báo safe | AN expected/classification; H2 graph; VI browser |
| A03 Partial/unresolved/budget | Nguyên nhân còn tới report/UI; timeout không completed đầy đủ | H2/AN producer cases; H1 report; VI browser |
| A04 Identity và corruption | Wrong repo/SHA/snapshot/config/version, stale/forged index, tampered bytes/hash/range bị reject đúng boundary | AN identity/evidence 2.19; H2 retrieval; KH storage |
| A05 Inventory/mapping | Failed discovery không empty success; unknown ID không trở thành valid relationship; giữ exact native IDs và receipt | KH integration 2.19 và mapping artifacts |
| A06 Persistence/recovery | PostgreSQL thật + artifact round-trip, concurrent build/failure/ambiguous commit, restart và consistent backup/restore được kiểm | KH commands/results, DB/artifact checks; H1 application |
| A07 UI contract/identity | Invalid report bị reject, run ID/revision/path/span đúng; real/demo/loading/empty/partial/error rõ | VI browser artifacts, H1 consumer review |

Khởi tạo execution record mỗi ca: **chưa chạy trong task tài liệu này**. Record thật
cần case → expected → actual → command/cwd/exit → artifact/hash → reviewer/date.
Không dùng typecheck thay browser, SQLite/fake thay PostgreSQL, hoặc unit suite thay
toàn bộ 2.19. Input hooks/pytest chỉ chạy trong runner được phép, không API/dashboard.
Owner xác nhận AC và evidence; H1 tổng hợp human acceptance, không đóng sprint từ merge.

## 7. Capacity và lịch theo remaining work

232h work + 32h reserve là baseline lịch sử, không phải capacity/giờ còn lại.
Nhóm chọn lập lịch từ deliverable còn thiếu; bảo vệ thời gian review/integration/fix.
Không cộng trùng unit/integration vào reserve; thiếu capacity thì xem cải tiến tùy
chọn trước, không bỏ integrity/acceptance hoặc âm thầm đổi task/sprint dates.

| Thành viên | Bằng chứng đã có để đối chiếu | Deliverable còn thiếu ở baseline main | Estimate implement/review/integration | Availability/ngày cam kết |
| --- | --- | --- | --- | --- |
| H1 | Workflow thin; P3/compound/resolver có trên nhánh cũ, chưa trên main | Reconcile code cũ, acquisition/contracts bridge, mapping artifact, full workflow/acceptance | Chưa cung cấp | Chưa cung cấp |
| AN | Snapshot/changes/limitations modules trên main | Trusted bridge, classification/base-target propagation, identity cases 2.19 | Chưa cung cấp | Chưa cung cấp |
| H2 | Graph/impact, provisional manifest và context builder trên main | Semantics convergence, bounded chunk/query/index/search, ready lifecycle | Chưa cung cấp | Chưa cung cấp |
| KH | Foundation/inventory/mapping trên main; task handoffs có checks lịch sử | Index metadata/recovery/exclusions, cross-module inventory/runner acceptance | Chưa cung cấp | Chưa cung cấp |
| VI | Ordering/ranked-context/UI modules trên main | Consumer checks, runtime validator/Run ID fixes, projection và real browser acceptance | Chưa cung cấp | Chưa cung cấp |

Mỗi người bổ sung commit/evidence chính xác, estimate ba phần và availability trước
khi chốt ngày lịch. Đây là **operational inputs**, không mở lại accepted architecture.
Mốc tương đối: M0 semantics/interfaces; M1 verified sources/manifests; M2 storage/index;
M3 retrieval/workflow; M4 cross-module/DB/browser acceptance. Không tự suy số ngày.

## 8. Trusted acquisition tới ready

AN/H1 boundary xác minh authorized repo/full frozen SHA và actual snapshot/manifest
bytes; H2 builder tiêu thụ qua interface. Wrapper/DTO/`trusted=True` không tự tạo
trust. Ready chỉ sau verification → staging/publish artifacts → metadata commit.
Không gỡ guard hiện có để demo; load persisted index phải verify metadata/artifacts.
Base/target provenance riêng. Wrong SHA/dirty/stale source, forged manifest và
tampered bytes không tạo ready hợp lệ.

Trước khi viết code mới, H1/AN đối chiếu nhánh implementation cũ:
`e03312a` EvidenceStore, `1c2e011` resolver, `f88e823` compound workflow,
`b7ac7a2` impact bounds; chúng chưa là ancestors của baseline main. Reuse/reconcile
trong task code riêng, không cherry-pick ở task này. Không coi resolver evidence
đã tồn tại là acquisition-to-index bridge đã hoàn tất.

## 9. Chunking, query, scoring và budgets

Local structural + lexical theo P5, không embeddings/egress. Tái sử dụng AST parser,
hạn chế duplication class/method. Remainder/docs chia bounded physical lines.
Oversized symbol chia đoạn liên tiếp, giữ symbol identity/span và policy version.
Nếu một physical line vượt byte cap, không cắt byte rồi bịa line-range/hash hợp lệ;
reject/expose reason theo policy, không publish index thiếu như ready đầy đủ.

Tokenizer tách snake_case/camelCase/path/module identifiers. Normalize tokens phục
vụ search, không normalize source bytes/hash. Query deterministic từ changed paths/
modules/symbols/identifiers; không LLM, fault labels hoặc reference outcomes.
Score ưu tiên distinct query-term matches và exact symbol/module matches, không
thưởng vô hạn repetition. H2 chốt công thức/weights có version và expected fixtures.
Giữ tier 2.12, score trong tier, stable tie-break và dedup có provenance.
Áp dụng exclusions trước chunk/artifact/index; local/hash không thay secret exclusion.

| Giới hạn khởi đầu đã chọn | Default và đơn vị |
| --- | --- |
| Chunk | Đồng thời ≤128 physical lines và ≤8 KiB exact content bytes |
| Index | Đồng thời ≤10.000 chunks và ≤32 MiB tổng chunk content bytes |
| Query | ≤64 distinct terms sau dedup |
| Context | Đồng thời ≤20 chunks và ≤64 KiB content bytes |
| Timeout | Build 60s; query 5s |

KiB=1024 bytes; MiB=1024² bytes. Đây là **initial operational defaults chưa benchmark**.
Giới hạn snapshot/runner hiện có chặt hơn vẫn áp dụng, không tự nới chúng.
H2/KH đo trên authorized candidates trước freeze config; thay default cần lý do,
version/config hash và boundary tests, không hỏi chọn backend lại. Cùng completed
inputs/config cho deterministic output; timeout phụ thuộc môi trường phải được ghi.
Build thiếu không ready đầy đủ; timeout/incomplete expose partial/reason. Top-k
công khai bounded scope, không chứng minh toàn bộ impact/safe exclusion.

## 10. PostgreSQL publication và recovery

PostgreSQL lưu index/chunk metadata (identity/config/version/state/backend,
artifact refs/hashes, path/range/hash, attempt/error chẩn đoán); content ở hashed
local artifacts. `embedding_model = NULL` cho lexical. Tái sử dụng connection,
transaction và guarded publication patterns, không thêm storage framework rỗng.
KH giữ shared migration chain từ head thật; H2 query requirements; H1 application review.

Lifecycle: building → write/verify staging → publish complete artifacts → transaction
ghi metadata/chunks/ready. Runtime query chỉ dùng committed verified ready index.
SQL rollback không tạo ready của attempt thất bại. Published artifact + DB fail
giữ orphan có truy vết. Ambiguous commit phải reconcile theo identity/digest, không
delete/replay mù. Concurrent builds dùng scoped uniqueness/transaction; reuse chỉ
sau verification. Backup/restore phải bao gồm metadata và bytes nhất quán.
PostgreSQL thật, concurrency/failure/restart/lost-ack/recovery thuộc acceptance A06.

## 11. Manifest và compatibility

Freeze minimal **internal** `index/1`, `chunk/1` sau producer/consumer review:
repo/commit/snapshot/index/config identity, version, physical CR/LF/CRLF ranges,
exact-byte hash, canonical config hash, bounds, unsupported-version behavior.
Giữ base/target source identity riêng cả khi dedup. H1 điều phối; H2 producer;
AN identity; VI consumer. Freeze shape là implementation review deliverable,
không có nghĩa mọi provisional fields đã được review ở task tài liệu này.

Tái sử dụng `RetrievalPayload`, `RetrievalSource`, `StageResult`. Không tự đưa
internal manifest/source bytes vào public API. Nếu consumer cần extension: nêu
use case, liệt kê consumers/fixtures, compatibility/version/migration, sửa models
nguồn → export schema/types → consumer checks. Additive field có thể breaking với
strict unknown-field rejection. Không sửa generated tay hoặc cast để qua validator.

## Work packages và thứ tự PR

Các PR dưới đây là kế hoạch, chưa tạo. Mỗi PR phải là deliverable review được;
không mở stack thiếu dependency mà mô tả như đã ready merge. Chốt interfaces trước
khi các owner triển khai song song trong các working trees riêng.

| WP / mục | Owner; reviewer | Input → output và paths/shared writer | Dependency; bắt đầu → hoàn tất | Acceptance/evidence |
| --- | --- | --- | --- | --- |
| W01 Semantics, mục 1–2 | H2 graph/VI ordering; AN/H1 review theo boundary | Actual producer status + graph → thống nhất ordering limitations; `core/impact/`, `application/`; H1 giữ shared analysis writer | Bắt đầu được với main; xong khi entrypoints hội tụ | No-edges/unresolved/failed/budget fixtures, permutation/cycle checks, docs version |
| W02 Acquisition/manifests, mục 8/11 | AN/H1 interfaces, H2 producer; reviewer theo §5 | Authorized snapshot → verified boundary + internal manifest; `application/`, `core/retrieval/`; H1 contract writer | Reconcile old code trước; xong khi forged/stale input bị chặn, consumers review shape | Identity/exact bytes/version cases, interface handoff; guard chưa gỡ khi chưa đủ readiness |
| W03 Chunk/config, mục 9 | H2; VI, AN/KH theo §5 | W02 sources/config → bounded chunks/query/scoring fixtures; `core/retrieval/`; H2 config writer | Sau W02 interface; xong khi deterministic/budget/exclusion boundaries kiểm được | Defaults/canonical hash, CR/LF/CRLF/oversized cases, authorized candidate measurements |
| W04 Index metadata, mục 10 | KH; H1 review, H2 query review | W02 identity + W03 shape → migration/lookup/publication/recovery adapter; `adapters/storage/`, migration head; KH sole migration writer | Sau interface/config agreement; xong khi PostgreSQL/artifact checks pass | Upgrade/round-trip, concurrent/failure/lost-ack/restart/restore evidence |
| W05 Ready/retrieval/rank, mục 8–11 | H2/VI theo module; AN identity review | W02/03/04 → verified ready search + existing rank/validate producer; `core/retrieval/`, application composition H1 | Sau metadata + trusted boundary; xong khi A03/A04 và bounded context đạt | No ready bypass, wrong config/hash/base-target tests, relevance/tie/dedup fixtures |
| W06 Mapping artifact, mục 4 | H1 integration, KH API; H2/AN review | Actual inventory/receipt/stages → versioned run-bound sidecar; `application/test_mapping.py`, workflow/artifact publisher H1 | Có interface/stages thì bắt đầu, fixture gắn nhãn; xong khi integrated artifact verify được | Exact IDs/receipt/partial/failed/wrong run cases, artifact/hash; không public field mới |
| W07 Projection/UI, mục 3/6 | AN classification, VI UI; H1 review | W01 + contracts + reports → visible docs/config/unsupported và valid identity; `frontend/src/features/reports/`, application projection H1 | Có interface thì làm fixture trước; xong chỉ sau actual report browser run | Validator malformed-report rejection, correct run_id, A02/A07 keyboard/responsive/states evidence |
| W08 Workflow, mục 4/6/8–11 | H1; AN/VI review | W01/02/05/06 và P3 reconcile → actual CLI/application report/artifacts; `application/analysis.py`, composition/entrypoints H1 | Một writer analysis; xong khi actual required producers chạy | Reproduction with commands/config/SHA/hashes, A01/A03, DB integration theo impact |
| W09 Acceptance, mục 6 | KH accountable, AN identity, VI browser, H1 tổng hợp; VI review 2.19 | W04/07/08 → case execution record và human acceptance; `backend/tests/integration/`, browser/evidence handoff | Expected soạn trước, chạy sau boundaries tích hợp; xong khi AC/evidence/actual review đầy đủ | A01–A07; blockers còn lại ghi rõ; không cộng unit tests thành toàn bộ campaign |

W00 là publication tài liệu hiện tại, chưa commit/push. PR order đề xuất:
W00 → W01/W02 → W03/W04 theo interface → W05; W06 và W07 làm độc lập khi có
inputs → W08 → W09. W01 có hai owners thì tách graph/ordering commits hoặc PR theo
writer, tránh cùng sửa một file. W03/W04 chỉ song song sau shape đã bàn giao.
W07 không sửa shared backend models; request H1 theo §11 nếu thiếu contract.

TDD cho behavior/bugfix có regression test; `api-contracts` khi thực sự đổi
producer-consumer contract; security-review cho trust/artifact boundaries;
UI/accessibility/webapp-testing cho W07; systematic-debugging khi có failure chưa
rõ nguyên nhân. Đọc AGENTS/profile/module rules trước code, không bật skills/agents
chỉ vì có tên trong tài liệu. Lệnh từ [verified commands](../../development/verified-commands.md).

## Đồng bộ Office và pending còn lại

Các vị trí Office cần kiểm tra là workbook `Sprint 2 Reports!E8:E55`, các reviewer/
dependency trong `Sprint 2 Backlog` task briefs, và Database v1.5 §3.4.8
`knowledge_indexes.embedding_model` (Nullable đang ghi `Not`). P5/mục 10 thay
NOT NULL này ở mức thiết kế bằng nullable cho lexical. Không dùng model giả.
Workbook đã đồng bộ các text cells liên quan trong hai sheet Sprint 2, giữ nguyên
formulas/native parts/statuses/estimates; bản gốc có backup local. Database DOCX
chưa sửa do runtime Windows không có bundled LibreOffice để đáp ứng render/PNG
verification. Chính xác ô Nullable của `embedding_model` trong §3.4.8 vẫn ghi `Not`;
quyết định hiện hành ở §10/P5 thay nó bằng NULL cho lexical. Không phải pending
chọn backend. Xem [handoff](../../development/sprint-2-decisions-handoff.md).

Phân loại follow-up: W01–W08 là **implementation**; W09/actual review là
**verification**; availability, remaining estimates, calendar dates là
**operational inputs**; provider/model/production/evaluation là **ngoài scope**.
Không còn pending chọn hướng 1–11. Không đánh đồng missing inputs với task Done.

## AI disclosure

OpenAI Codex hỗ trợ đối chiếu main/docs/Office, ghi quyết định nhóm đã chấp nhận,
soạn kế hoạch và self-review. Đã đối chiếu Proposal v1.4 Appendix C/D. Nhóm giữ
trách nhiệm đọc, hiểu và kiểm chứng; không tạo chữ ký, tỷ lệ đóng góp hoặc approval.
