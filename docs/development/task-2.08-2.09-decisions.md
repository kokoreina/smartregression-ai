# Quyết định triển khai 2.08/2.09 — inventory và discovery

## 1. Trạng thái, thẩm quyền và nguồn

**Accepted ngày 2026-11-04.** Nguyễn Tấn Huy (H1) xác nhận: “chốt như những gì
bạn ưu tiên và đưa vào repo … để các thành viên khác làm theo”, sau đề xuất về
candidate, môi trường, PostgreSQL, trạng thái và native test IDs. Đây là quyết định
triển khai do H1 xác nhận; không phải mentor approval hoặc nghiệm thu code.

Tài liệu này là nguồn quyết định chung cho KH/H1 và consumers 2.13/2.16/2.17/2.18.
Đọc cùng [team guide](sprint-2-team-guide.md), [decision register](decision-register.md),
[canonical contracts](../contracts/stage-reports.md) và
[foundation checkpoint](task-2.20-checkpoint.md). Phạm vi domain inventory ở đây
thay đề xuất cũ của checkpoint §6.2; không thay P3 EvidenceBundle/P5 retrieval.

Baseline đối chiếu: main `b50fe8966f6b3da3dbf7a7dfb8216da3bd764a05`, fetch ngày
2026-11-04. Main đã có schema/migrations và run/report adapter qua PR #25;
[handoff adapter](task-2.20-adapter.md) ghi kết quả PostgreSQL 17.11. Phiên chốt
tài liệu này không chạy lại DB tests và không suy ra inventory đã triển khai.
Không cần dựng lại foundation hoặc đợi một adapter run/report chưa có như mô tả cũ.

## 2. Repository và phạm vi nghiệm thu

| Candidate | Vai trò | Target commit cố định |
| --- | --- | --- |
| andialbrecht/sqlparse | Chính cho demo và nghiệm thu | `60cdc649726bf1bc4f1b336050560b336da715ec` |
| msiemens/tinydb | Dự phòng, đồng thời kiểm tra tương thích bổ sung | `edff96aeb2616402e9489d46e90a592c05565621` |

Nghiệm thu collection trên **cả hai candidate**, cộng fixtures do nhóm sở hữu để
kiểm tra empty/partial/errors. Sprint 2 này không nhận tùy ý URL/branch/repository.
Candidate hoặc revision mới phải qua allowlist/profile và kiểm chứng tương thích
riêng, không tự lấy latest. Inventory luôn gắn actual target SHA/snapshot/config;
quyết định này không tự chốt cohort base/target pairs dùng đánh giá phương pháp.

Nguồn: [candidate reproduction Sprint 1](../research/sprint-1/candidate-reproduction.md)
và [harness](../../scripts/candidates/README.md). Hai lần collection lịch sử giữ
509 IDs sqlparse và 228 IDs TinyDB. Đây là số **collected** lịch sử, không phải
số passed và không phải hằng số để producer tự điền. Collector Sprint 2 phải chạy
lại, đối chiếu exact IDs và giải thích mọi khác biệt. Giữ license/provenance và
các exclusions/skip; TinyDB có optional PyYAML test skip trong baseline.

Các candidate này phục vụ correctness/reproducibility của discovery. Chúng không
tự chứng minh fault retention, impact accuracy hay time savings; dataset/cohort/
labels và end-to-end evaluation vẫn theo [protocol](../research/evaluation-protocol.md).

## 3. Môi trường và collection profile

| Thành phần | Baseline accepted |
| --- | --- |
| Python input container | 3.14.3; độc lập patch version của backend host |
| pytest | 9.1.1 |
| pytest-cov | 7.0.0; chỉ nạp explicit trong profile cần, hiện TinyDB |
| coverage | 7.17.0 theo baseline đã quan sát |
| Build tooling nếu cần | build 1.3.0, hatchling 1.27.0 |
| Test paths | `tests/` trong target snapshot |
| Plugin policy | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; allowlist explicit, giữ plugin observer tin cậy |
| Source/root | Snapshot read-only tại `/repo`, pytest rootdir `/repo` |

KH phải tạo dependency lock đầy đủ cho candidate image, gồm transitives, ghi image
digest và kiểm chứng build/run. Không dùng lock backend làm lock của input runner.
Dockerfile spike hiện pin direct packages; chưa là bằng chứng rebuild tái lập mọi
dependency. Image identity cũ chỉ là lịch sử, không giả image hiện đã sẵn trên máy
thành viên. Pin collector/config version và hash cùng image/environment identity.
Nếu không tái tạo được baseline, ghi nguyên nhân và đề xuất thay đổi trước khi đổi
profile; không âm thầm upgrade hoặc bỏ dependency/config để qua kiểm tra.

Giữ pytest configuration của candidate, gồm coverage khi TinyDB yêu cầu. Không
bật lint/type/docs plugins ngoài allowlist; không tự cài packages lúc collection.
Install/build hooks chạy trong boundary được duyệt; image build dependencies tách
khỏi candidate runtime và không mang input source vào online dependency build.

Collector dùng argument list với `--collect-only`, `tests`, explicit rootdir và
bounded temp directory theo profile. Không dùng `-k`, `-m` hoặc selected-ID subset
để tạo inventory toàn bộ phạm vi đã chốt. Config-derived exclusions/collection skips
phải được ghi lại; không suy “complete” là mọi test có thể tồn tại ngoài profile.
Lấy `item.nodeid` từ pytest hooks và kết quả có cấu trúc; không parse console text
làm nguồn chuẩn. Script spike chỉ là nguồn tham chiếu, không tự trở thành product runner.

## 4. Isolation và resource budget

Giữ baseline hiện có: mỗi collection một Linux container riêng; không collection,
import test/conftest hoặc chạy install hook trong API/dashboard/host Python.

| Giới hạn | Giá trị accepted |
| --- | --- |
| Collection timeout | 60 giây |
| CPU | 1 CPU |
| Memory / memory-swap cap | 512 MiB / 512 MiB; không thêm swap vượt cap |
| PIDs | 64 |
| Tmpfs | 64 MiB; noexec/nosuid/nodev |
| Captured output budget | 512 KiB; tính cả structured output/logs theo transport, không cắt IDs để báo complete |
| Network | none trong candidate build/collection/execution |
| Quyền | UID/GID 65534, read-only root/source, cap-drop ALL, no-new-privileges, seccomp |

Không mount Docker socket, credentials hoặc writable workspace vào workload.
Docker orchestration chạy ngoài web process, trên worker do nhóm kiểm soát.
Cleanup phải bounded và xử lý success/error/timeout; không chỉ đổi nhãn UI trong khi
process/container vẫn chạy. Không automatic retry/nới quota/bật network/fallback host
khi lỗi; giữ failed attempt và nguyên nhân. Thiếu dependency là setup failure,
không phải test failure hoặc confirmed fault. Không nhận arbitrary hostile repos
chỉ vì có container. Theo [rule 10](../rules/10-runner-security.md).

## 5. Native IDs và thay đổi contract cần triển khai

Chốt **giữ nguyên pytest node ID**: không trim, lowercase, Unicode-normalize,
thay separator hoặc đổi thành UUID/hash khi selection/dispatch. UI display label
nếu có là trường riêng; execution dùng đúng ID quan sát trong đúng inventory.
Exact duplicates phải được báo rõ, không âm thầm deduplicate rồi báo complete.
Hai IDs khác nhau dù chỉ ở whitespace vẫn không được gộp.

Hiện `InventoryPayload.test_ids` dùng `Text`, còn `Text` bật strip_whitespace.
H1 là writer của contract dùng chung: tạo kiểu riêng `NativeTestId` không trim,
kiểm tra producer/consumer, regression cases và export schema/types bằng công cụ.
Không sửa global Text. KH cung cấp ID fixtures và collector requirements; nếu cần
chuyển writer cho KH phải ghi phối hợp cụ thể, tránh hai người cùng sửa contract.

Đây là thay đổi semantics đã được chấp nhận, **chưa là thay đổi code trong phiên
tài liệu này**. Trước merge code phải ghi compatibility/version strategy theo
[rule 03](../rules/03-contracts-api.md), không tự coi additive là luôn tương thích.
Không bịa hồi phục IDs đã bị trim trong dữ liệu cũ; recollect từ snapshot/profile
nếu cần dữ liệu native chính xác. Public schema version cụ thể phụ thuộc rà consumers.

## 6. PostgreSQL domain design

KH sở hữu hai bảng `test_inventories`, `test_cases` và migration tiếp nối Alembic
head thực trên main. Không sửa revision foundation đã merge, không dựng schema/
engine song song hoặc lấy M003/M004 trong plan làm revision ID thật.

`test_inventories`:

- PK `(repository_id, run_id, inventory_id)`, unique `(repository_id, run_id)`:
  một frozen inventory/run. Retry ghi cùng nội dung là no-op; khác nội dung conflict.
- Scoped FK tới run và target snapshot; application kiểm đúng target của run,
  không chỉ kiểm snapshot tồn tại. Completed/partial bắt buộc target materialized.
  Not-run/failed trước acquisition có thể giữ target hash NULL theo identity thực;
  không tạo snapshot row giả. Nullable FK phải có CHECK/presence rules tương ứng.
- Framework, actual collector version, collection profile/config hash và image/
  environment identity. Có thể reference immutable config/artifact đã được kiểm
  chứng; không lưu DSN/source/fault labels trong config.
- Stage status, nullable completeness/count, reason/error_code, limitations;
  actual exit code/duration/diagnostic artifact reference khi có, unknown là NULL.
  Không dùng job lifecycle pending/running thay analysis stage states.

`test_cases`:

- Scoped FK tới inventory; native node ID lưu đầy đủ trong `text`.
- Dùng digest SHA-256 của exact UTF-8 ID làm technical key trong scoped composite
  key, tránh đưa native ID không giới hạn độ dài trực tiếp vào B-tree PK. Digest
  không thay ID public. Khi cùng digest phải so exact text/bytes; khác ID báo
  conflict/integrity error, không gộp. Không normalize trước hash/compare.
- Giữ ordinal để tái hiện collection order. Không đặt NOT NULL cho display_name,
  source_location hoặc component mapping chưa có producer; mapping thuộc 2.16.
- Không áp cap 512 UTF-8 bytes của run/report/artifact IDs cho node IDs. Resource/
  output budget vẫn áp dụng. PostgreSQL text không hỗ trợ U+0000: reject rõ bằng
  unsupported/persistence error, không truncate/replace; không claim mọi ID tùy ý
  đều persist được.

Ghi inventory và test rows trong cùng transaction. Count của complete/partial
phải khớp số exact unique rows. Không cascade xóa history hoặc thêm retention service.
Sau load phải revalidate scope/status/config/count, không tin JSON đúng là dữ liệu
đúng. Runtime quyền tối thiểu theo foundation; KH bổ sung grants riêng cho domain,
không dùng migration owner để giả kiểm chứng runtime role.

## 7. Trạng thái chung cho collector, DB và consumers

| Trường hợp | stage_status | completeness | test_count | Dữ liệu và lý do |
| --- | --- | --- | --- | --- |
| Chưa có collector | not_implemented | NULL | NULL | reason bắt buộc |
| Chưa chạy | not_run | NULL | NULL | reason bắt buộc |
| Không có kết quả collection tin cậy | failed | NULL | NULL | error_code; diagnostics riêng |
| Có một phần kết quả hợp lệ | partial | partial | Số IDs hợp lệ, có thể 0 | Giữ IDs, limitations bắt buộc |
| Hoàn tất, không có test | completed | complete | 0 | Successful empty |
| Hoàn tất, có test | completed | complete | >0 | Inventory đầy đủ trong profile |

Giữ canonical StageResult: failed không chứa successful data payload; partial có
data + limitations, không ép error_code vào success envelope trái contract. Không
thêm enum success_empty vào public report: đó là completed + complete + count=0.

Chỉ gọi partial khi có trusted structured result/checkpoint đúng snapshot/profile
và có thể kiểm integrity, duplicate và scope. Nếu protocol malformed, snapshot sai,
worker output không tin cậy hoặc không có checkpoint hợp lệ thì failed. IDs thấy
trong log của failed attempt chỉ là diagnostics; không đưa thành eligible test_cases
hoặc test_count=0. Giữ bounded diagnostic artifact nếu cần điều tra.

Timeout/output overflow không tự thành empty. Nếu transport hỗ trợ checkpoint hợp
lệ trong giới hạn, có thể giữ partial kèm reason/limitation đúng; nếu chưa có cơ chế
đó thì failed. Không yêu cầu dựng streaming protocol chỉ để gọi mọi timeout partial.
pytest exit 5 chỉ được map empty khi collection thực sự hoàn tất bình thường,
không collection errors, có structured result đầy đủ và đúng scope. Exit code một
mình không đủ; internal/plugin errors phải giữ failure dù có IDs quan sát được.

Consumers 2.13/2.16/2.17/2.18 phải propagate states và limitations. Partial/failed
không đủ để kết luận selection an toàn; successful empty cũng không chứng minh
repo không có bug. Full-suite fallback chỉ khi môi trường/policy thực thi cho phép;
lỗi dependency/discovery không được che bằng một fallback thành công giả.

## 8. Writer, thứ tự và acceptance

Giữ allocation/task ownership của team guide, không tự đổi giờ hoặc thêm task mới.

| Thứ tự | Writer / phối hợp | Đầu ra |
| --- | --- | --- |
| 1 | H1 contract, KH cung cấp fixtures | Native ID semantics, compatibility/version note, generated artifacts và consumer checks |
| 2 | KH | Candidate dependency lock/image/profile, isolated collector + 2.09 state mapping |
| 3 | KH | Hai bảng, migrations, persistence adapter dùng foundation, DB tests |
| 4 | KH bàn giao H1/H2/VI và consumers | Inventory/report examples, exact reproduction evidence, limitations và integration inputs |

Nếu thay backend manifest/uv.lock, H1 giữ writer theo P4; candidate-image dependency
lock riêng thuộc KH. KH có thể chuẩn bị collector/schema độc lập trong khi contract
đang phối hợp, nhưng không merge contract drift. Reviewer độc lập chưa xác nhận;
không ghi receipt/approval thay thành viên.

Acceptance bắt buộc trước khi đóng 2.08/2.09:

1. Cả hai candidate thu thập hai lần cùng target/profile/image; so exact IDs và
   order, giữ environment identity và giải thích khác biệt với baseline lịch sử.
2. Fixtures: complete có test, successful empty, trusted partial có/không có IDs,
   import/plugin failure, timeout, output overflow, duplicate, wrong repo/snapshot,
   unsupported ID và malformed/missing structured result.
3. Native IDs, gồm Unicode/parametrized/whitespace cases, qua contract → DB →
   consumer giữ exact value; invalid/duplicate không bị đổi thành success.
4. PostgreSQL thật: round-trip statuses/IDs/config, scoped constraints, count-row
   consistency, late-error rollback, same-payload retry, changed-payload conflict,
   concurrent writes và runtime permissions. Giả lập digest collision phải reject.
5. Migration fresh/upgrade/reapply phù hợp trên dedicated test DB; không stamp/drop
   để che lỗi. Xác minh isolation/resource settings và cleanup success/failure.
6. Tests/lint/export/generated consumer checks theo thay đổi; exact commands,
   versions, result và pending trong handoff. Không dùng doubles thay DB/runner
   acceptance hoặc coi tự review là independent review.

## 9. Kiểm chứng tài liệu và AI disclosure

Phiên này chỉ cập nhật Markdown theo quyết định H1. Đã fetch main, đọc source/
handoffs liên quan; không chạy candidate, pytest, PostgreSQL hoặc benchmark mới.
Kiểm tra diff scope, links/anchors, Markdown fences/whitespace và consistency của
SHA/version/status/ownership trước bàn giao. Workbook/DOCX và code không đổi trong
diff này; tài liệu nhị phân legacy chưa được sửa, dùng quyết định này khi reconcile.

OpenAI Codex hỗ trợ đối chiếu nguồn, soạn quyết định và self-review; dùng các nguyên
tắc evaluation-integrity, security-review và api-contracts đã đọc. Nhóm cần hiểu và
kiểm chứng implementation theo Proposal Appendix C/D; không bịa tỷ lệ đóng góp,
mentor approval hoặc claim runtime pass. Sau bàn giao local, H1 giao commit/push
bản quyết định này để nhóm review và merge; không tự approve/merge hoặc đóng task.
