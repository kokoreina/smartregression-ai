# P3 — EvidenceBundle persistence cho 2.05

> Implementation follow-up: [2.05 handoff](task-2.05.md) records local adapter,
> migration and PostgreSQL verification. Statements below describe the P3 decision
> baseline; source verification and compound workflow remain separate slices.

<a id="p3-status"></a>

## 1. Trạng thái, baseline và phạm vi

**Accepted ngày 2026-11-04 theo xác nhận của Nguyễn Tấn Huy (H1) rằng cả nhóm đã đồng ý.**
Nguồn: user yêu cầu trong phiên này: “vậy hãy chốt như phương án đề xuất đi, cả nhóm
đều đã đồng ý rồi”. Quyết định áp dụng toàn bộ phương án P3 bên dưới: bounded bytea
2 MiB, immutable bundle/run, full identity/codec/retry, verification trước freeze,
transient re-inspection, compound SQL transaction và ownership H1/KH/VI.
Đây là nguồn đặc tả P3 đã chốt, tiếp nối đề xuất trong
[checkpoint 2.20-A §6.1/8](task-2.20-checkpoint.md#61-205--evidence_bundles-theo-existing-port).
P3 trước đó là proposed; xác nhận mới này là nguồn chấp thuận riêng, không suy từ
P1/P2/P4 hoặc D15. Nhóm quyết định theo thông tin H1 truyền đạt; không suy mentor
approval, GitHub review/merge hoặc implementation acceptance. P5/retrieval vẫn riêng.

Các mốc Git/CI và phạm vi dưới đây ghi lần soạn đặc tả ban đầu; cập nhật accepted
chỉ sửa tài liệu, không chạy lại CI/fetch hoặc triển khai code trong lượt chốt.

- `git fetch origin main` thành công; main quan sát được là
  `9bcd6a4372dce3e1c58f8ce5e0f7d233ba5c3c47`.
- [PR #30](https://github.com/kokoreina/smartregression-ai/pull/30) đã merge ngày
  2026-11-04 lúc 08:56:50 UTC; hai source CI checks của PR đều SUCCESS.
  Không coi đó là CI cho tài liệu mới hoặc acceptance 2.05.
- Checkout: `D:\smart-regression-ai\var\main-review-20261103`, branch
  `feat/sprint-2-2.13-report-persistence`, HEAD
  `8eb6995b055341227a09231d982c3321cc8f97c5`; tree trùng main được fetch,
  working tree sạch trước nhiệm vụ. Không merge/rebase hoặc đổi branch.
- Checkout gốc và `outputs/`, `start-cliproxy-management.bat` được giữ nguyên.
- Phiên này chỉ sửa Markdown. Không code, migration, contract/generated artifacts,
  dependencies, DB writes, product tests, commit/push hoặc mở PR.

Đã có [port/helpers EvidenceStore](../../backend/src/smartregression/application/evidence_store.py),
[EvidenceBundle/RunIdentity](../../backend/src/smartregression/contracts/stages.py),
[fake-store tests](../../backend/tests/unit/test_stage_storage.py) và
[run/report persistence](task-2.13.md#persistence-wiring).
Chưa có PostgreSQL EvidenceStore, bảng evidence_bundles hoặc resolver 2.06.
Potential-impact producer đã có trên main nhưng workflow chưa nối impact/evidence;
không dựng bundle bằng payload giả để lấp stage chưa có.

<a id="p3-choice"></a>

## 2. Phương án đã chốt

Một bundle bất biến cho mỗi `(repository_id, run_id)`, canonical JSON bytes trong
PostgreSQL `bytea`, tối đa **2_097_152 bytes sau serialize**. Tái sử dụng Core,
psycopg, Alembic, settings/engine và transaction infrastructure đã có.

| Phương án | Đánh đổi với consumer save/load hiện tại |
| --- | --- |
| Bounded bytea — đã chọn | Giữ exact canonical bytes/array order, một row/transaction; không SQL-query nested paths, có cap phải kiểm bằng dữ liệu đại diện |
| JSONB | Tiện query nhưng không giữ representation; không thay canonical-byte equality và có giới hạn JSON string như U+0000 |
| Artifact-backed bundle | Phù hợp dữ liệu lớn hơn nhưng thêm file/catalog coordination, kiểm root/digest và orphan recovery |
| Normalize toàn bộ | FK/query từng entity nhưng thêm tables/mapping/joins chưa có consumer cần dùng |

Không thêm secondary indexes hoặc normalized tables cho nhu cầu giả định.
Mapping DB Design §3.4.1–5 được chốt cho slice này: changed files,
components/ranges, graph edges, impact paths/candidates và evidence nằm trong bundle;
không gọi đây là implementation normalized design. Không tạo location/rank/explanation
hoặc component IDs để lấp trường thiếu. Nếu dữ liệu đại diện vượt cap, báo explicit
size failure và mở lại P3; không tự truncate, nén hoặc đổi storage backend.

<a id="p3-identity"></a>

## 3. Schema và full identity

KH triển khai trong schema `smartregression`, metadata/migration cùng source convention:

| Cột | Yêu cầu đã chốt, chưa triển khai |
| --- | --- |
| repository_id, run_id — text | Composite PK; composite FK tới analysis_runs(repository_id, run_id), ON UPDATE/DELETE RESTRICT |
| bundle_format — text | NOT NULL, độ dài 1–128; writer dùng `evidence-bundle/1`, reader chỉ nhận codec hỗ trợ |
| payload — bytea | NOT NULL; CHECK octet_length từ 1 đến 2_097_152 |
| payload_sha256 — text | NOT NULL; CHECK 64 lowercase hex; application kiểm digest khớp payload |
| created_at — timestamptz | NOT NULL, server insertion time, không cập nhật khi retry |

PK đã phục vụ exact lookup; không thêm unique/index dư. Không thêm snapshot columns
trùng lặp: trong cùng transaction, adapter so identity trong bundle với immutable run:
repository_id, run_id, base.commit/base.snapshot_id, target.commit/target.snapshot_id,
comparison_mode. Hai snapshot.repository_id phải đúng enclosing repository; cả hai
snapshot_id bắt buộc non-null theo EvidenceBundle. SHA/hash không được suy từ branch.
Các snapshot rows phải tương ứng FK/manifest metadata đã được acquisition tin cậy tạo.

DB bảo vệ key, run existence, size và basic constraints; **không kiểm nested references
trong bytea**. EvidenceBundle validators kiểm cấu trúc, graph/path/component/evidence
references. Source resolver kiểm vị trí/source/support; hai tầng này không thay nhau.
Run/config, statuses/limitations và data_kind vẫn thuộc run/report, không thêm vào
public EvidenceBundle. Metadata repository/run IDs theo giới hạn foundation hiện có;
không áp cap 512 bytes lên nested IDs, excerpts hoặc native test IDs.

Source binding/authorization phải được caller xác minh trước storage. Có repository/run
row không cấp quyền đọc, không có auth service mới; bundle không được tự đăng ký repo.

<a id="p3-codec"></a>

## 4. Codec và validation

Tái sử dụng [canonical_json](../../backend/src/smartregression/core/git/snapshots.py)
trên `checked_bundle.model_dump(mode="json")`: sort_keys=True, ensure_ascii=True,
separators dấu phẩy/dấu hai chấm không khoảng trắng, **một LF cuối**, encode UTF-8.
Giữ array order; không Unicode normalization/case-fold/trim ngoài contract hiện có.
Escaping như `\u0000` là bytes JSON, không đưa NUL thành PostgreSQL text.
Đây là codec nội bộ dựa trên serializer hiện hữu, không claim chuẩn RFC canonical JSON.

Dump đầy đủ defaults/nulls, không dùng exclude_unset/exclude_none; omitted default
được typed validation materialize trước canonicalization. Bundle hiện không có numeric
field cho NaN/Infinity; reject non-finite/invalid types qua typed validation, không
thay global canonical_json để phục vụ riêng task này. Text vẫn theo semantics model
hiện có; không cam kết giữ whitespace mà model Text đã chuẩn hóa trước storage.
EvidenceBundle không chứa inventory; không đổi NativeTestId hoặc legacy v1.

Save revalidate/deep-copy nested lists qua model như helpers hiện có, rồi kiểm identity,
canonical bytes, size và SHA-256 **trước mở connection**. Bounded acquisition/producer
limits vẫn cần thiết; kiểm sau serialize không phải memory isolation trước serialize.

Load: đọc row scoped → kiểm format/size/hash → strict UTF-8/JSON decode → typed bundle
validation → canonical re-encode phải bằng stored bytes → so row/run/expected identity.
Reject invalid JSON/noncanonical encoding/duplicate-key representation thay vì sửa bytes
khi đọc. Hash đúng không làm invalid payload hợp lệ; canonical equality không thay source
verification. Internal codec `evidence-bundle/1` không phải public schema_version 2.0.0.
Contract hiện tại không cần đổi; codec mới sau này cần compatibility/upgrade riêng.

<a id="p3-storage"></a>

## 5. Save/load, concurrency và errors

Giữ `EvidenceStore.save(bundle) -> None`, `load(identity) -> EvidenceBundle | None`.
Standalone save yêu cầu trusted run đã tồn tại; port không nhận config/manifests nên
không tự tạo placeholder run. Adapter revalidate ở boundary kể cả caller bỏ helpers.

1. Chuẩn bị payload hợp lệ; mở transaction, kiểm full identity với run.
2. INSERT scoped key với ON CONFLICT DO NOTHING; không SELECT-then-INSERT đơn thuần.
3. Nếu key đã có, SELECT lại committed row trong READ COMMITTED, kiểm integrity/codec
   rồi so canonical bytes, format và full identity. Giống hoàn toàn là no-op; khác là
   EvidenceConflict. created_at do server tạo không thuộc retry comparison.
4. Không UPDATE để đạt retry success. Unique key serialize concurrent inserts; loser
   chờ trong lock/statement timeout đã cấu hình. Timeout/deadlock/disconnect báo lỗi,
   không tự retry producer/transaction.
5. Transaction owner commit một lần. Bound adapter không commit/rollback bên trong;
   standalone adapter sở hữu transaction. Không dùng bound connection đã đóng hoặc
   không có active transaction. Run/bundle immutable và RESTRICT là precondition;
   maintenance privileged writes không thuộc concurrent runtime protocol.

Load absent key → None; có row phải kiểm cả immutable run và payload trước trả dữ liệu.
Expected identity khác existing row/run → EvidenceConflict, không trả foreign bundle
hoặc None. Có run nhưng chưa có bundle vẫn là absent bundle; load không tạo dữ liệu.

| Trường hợp | Error mapping và trạng thái |
| --- | --- |
| Cùng key khác immutable bytes/identity | Existing EvidenceConflict / `evidence_conflict` |
| DB unavailable/timeout/ambiguous commit, missing prerequisite run khi save | Existing EvidenceStorageError / `evidence_storage_failed` |
| Size vượt cap | Subclass đã chốt, chưa triển khai / `evidence_payload_too_large` |
| Unsupported codec | Subclass đã chốt, chưa triển khai / `evidence_format_unsupported` |
| Payload/hash/validation/canonical encoding hỏng trên load | Subclass đã chốt, chưa triển khai / `evidence_corrupt` |
| Input không hợp lệ trước save | Typed validation rejection như helpers hiện có; caller map safe code, không echo input |

Các mã mới đã chốt cần triển khai/test trong prompt 4; không phải behavior đã có.
Current load_evidence còn guard ValueError `stored_evidence_identity_mismatch` cho port
trả foreign bundle; giữ defense này, không tuyên bố helper hiện đã trả EvidenceConflict.
Adapter thật phải bắt mismatch sớm theo mapping trên.

`database_transaction`/`database_engine` hiện sanitize thành RunStorageError.
Standalone evidence boundary cần chuyển infrastructure RunStorageError thành
EvidenceStorageError an toàn, bao gồm commit/connection failure; không nuốt domain
EvidenceConflict hoặc trả None khi DB lỗi. Compound writer ở §7 phải giữ typed
evidence errors và CLI xử lý trước generic error handler. Không sửa shared transaction
framework rộng hoặc để SQLAlchemy types lọt vào application port.

Mọi diagnostics dùng safe code, không DSN/SQL/source/raw exception. Ambiguous commit
trả failure; exact key+bytes có thể retry khi caller còn giữ captured data, không tự
delete/overwrite. Digest một mình không phải chứng minh equality.

<a id="p3-lifecycle"></a>

## 6. Lifecycle 2.05 ↔ 2.06

Lifecycle đã chốt: producer observations → source resolution → support validation → validate
report/bundle → freeze một execution → persist. 2.06 thực hiện verification trước
freeze; 2.05 chỉ bảo toàn kết quả, không tự nâng trạng thái verification.

- resolution đúng contract: unverified/resolved/missing/mismatched; support tách riêng:
  unverified/supported/unsupported. Non-default resolution cần verification_reason;
  support xác định cần resolved source. Commit/path/range tồn tại chưa chứng minh support.
- Đọc frozen snapshot có identity/hash khớp, không đọc working tree hiện tại hoặc chạy
  input code. Saved verification fields là producer claims; untrusted uploads không
  được coi là trusted verification chỉ vì validator chấp nhận JSON.
- Cho phép lưu evidence chưa verified đúng sự thật. Nếu item chưa resolved+supported,
  evidence stage trong report phải partial kèm limitation theo contract; storage không
  suy stage completed từ empty items hoặc successful load. Bundle không chứa stage envelopes.
- Partial changes/graph/impact có data vẫn có thể tạo bundle hợp lệ; statuses và đầy đủ
  limitations giữ trong report. Nếu thiếu một trong changes/graph/impact/evidence data,
  **không tạo bundle**, không tạo empty data thay not_implemented/not_run/failed.
- Re-inspect sau reload trả inspection riêng trong memory, không sửa persisted bundle,
  report hoặc original verification fields. UI phân biệt saved claim với current
  inspection; API/UI contract cho inspection phải đặc tả ở 2.06, không thêm ở P3.
- Muốn lưu kết quả verification khác: execution mới/run_id mới, giữ source provenance;
  không nhét payload mới vào cùng run key. Report_id mới cùng run chỉ được dùng khi
  domain bundle không đổi. Không cần bundle version table/service trong slice này.

Không đổi public model/port để giải quyết lifecycle này. VI nhận payload/state mapping
và examples từ H1/2.06; VI vẫn sở hữu evidence component, không bị chuyển task UI sang H1.

<a id="p3-integration"></a>

## 7. Report persistence 2.13 và compound transaction

**Đã có:** [persist_report](../../backend/src/smartregression/application/persistence.py)
validate/prepare → publish complete file → store.save; PostgresRunReportStore mở một
transaction và dùng BoundRunReportStore ghi snapshots/run/artifact/report metadata.
`--persist` hiện chỉ lưu report, chưa lưu EvidenceBundle. SQL save tạo run prerequisites
trong transaction, không tạo repository. File/report và metadata vẫn immutable.

**Thiết kế đã chốt, triển khai khi tích hợp ở prompt 6:** dùng cùng prepared execution và optional checked
bundle; validate overlap **trước publication**: full identity và bốn data payloads phải
khớp report, không chỉ digest/IDs. Chỉ tạo optional bundle nếu đủ data như §6.
Report statuses/limitations phải validated, không tự derive từ bundle.

Freeze ở đây là capture detached canonical bytes và identity sau revalidation, không
chỉ giữ tham chiếu Pydantic frozen model: nested lists vẫn mutable. Compound writer
phải dùng đúng captured bundle đã so với report bytes, hoặc reject nếu revalidation
ở SQL boundary cho bytes khác preflight; không serialize lại caller-owned model đã
bị đổi giữa publish/save. Size/digest/codec được kiểm lại ở adapter boundary.

Tái sử dụng RunReportStore.save(write) boundary với compound concrete writer giữ checked
bundle theo execution; writer mở một database_transaction, gọi BoundRunReportStore.save
rồi bound EvidenceStore.save trên cùng connection. Run vừa insert đã thấy trong cùng
transaction. Không gọi hai standalone save liên tiếp để giả atomicity. Application
preparation nhận/validate optional bundle, composition nối writer; không cần public
API/CLI flags, generic UoW hoặc một workflow clone. Mọi chữ ký/helper mới ở đây đều là
thiết kế đã chốt, chưa tồn tại trên main tại baseline §1.

| Bước | Precondition | Đã ghi | Failure/retry |
| --- | --- | --- | --- |
| Prepare/freeze | Authorized source, actual config/manifests; report/bundle hợp lệ và overlap khớp | Chưa file/SQL | Validation/size/mismatch fail trước publish; không retry analysis âm thầm |
| Publish report | Trusted disjoint artifact root, exact IDs/raw bytes/digest | Complete file | Publish failure không gọi SQL; giữ failure nếu cleanup sau publish lỗi |
| SQL prerequisites/catalog | Existing authorized repository; live transaction | Rows chưa commit, run tồn tại cho bundle | BoundRunReportStore lỗi → rollback phần mới, giữ file |
| Optional bundle save | Run identity khớp, checked bundle nếu đủ data | Bundle và metadata cùng transaction | Conflict/evidence failure → rollback toàn bộ phần mới; existing committed rows không bị xóa |
| Commit/ack | Tất cả saves thành công | Cả metadata và bundle nếu supplied | Ack mất → failure/ambiguous, không xóa file hoặc tự replay |
| CLI output | Save và commit ack thành công | JSON/stdout + persisted diagnostic | Giữ analysis exit 0/1/2; persistence failure exit 2, safe stderr, không JSON hoặc success claim |

Existing report-only persistence giữ nguyên khi không có bundle đủ điều kiện; success
chỉ có nghĩa report đã lưu. Khi wiring có bundle, diagnostic phải nói rõ saved hoặc
not included và lý do thiếu data; không thêm unsupported fields vào report contract.
Không đổi analysis_status thành failed chỉ vì storage lỗi; persistence exit/diagnostic
là boundary riêng. CLI bổ sung handling EvidenceStorageError trước generic exception.

Nếu report đã committed từ đường standalone mà save bundle sau đó thất bại: report
vẫn tồn tại, không có rollback xuyên hai calls; báo evidence failure, không báo complete
evidence persistence. Có thể retry exact standalone bundle khi giữ đủ captured data.
Đường này hữu ích cho adapter tests/authorized domain save, không phải compound CLI flow.

Nếu run đã có bundle, compound writer phải đọc/validate nó và reject overlapping
report data khác bundle, kể cả caller không supplied bundle mới. Report thiếu data
không được tự fill từ bundle cũ hoặc nâng success; mismatch không tạo report mới.
Không có row không đồng nghĩa stage data rỗng.

File/SQL không phải distributed transaction. File đầy đủ còn lại sau rollback là
orphan cần reconciliation; commit ambiguous không được auto-delete. Exact retry cần
giữ IDs, bytes, config và manifests của execution; analyze lại sinh IDs mới không
phải retry. Publisher hiện exclusive và có thể reject existing destination: không
claim CLI resume/exact publication retry đã được triển khai. Không thêm GC/outbox/queue.

<a id="p3-handoff"></a>

## 8. Migration, ownership và thứ tự triển khai

Head từ revision files đã kiểm: `20261104_03` (inventory), predecessor `20261103_02`.
Không kết nối DB để xác nhận deployed head trong phiên docs. KH phải kiểm lại head
mới nhất lúc triển khai; nhãn M003 trong checkpoint là kế hoạch cũ, đã được inventory
đi trước, không phải slot/revision dành riêng cho evidence.

| Phần | Writer/phối hợp và đầu ra |
| --- | --- |
| P3 | Nhóm đã chốt qua xác nhận H1 ngày 2026-11-04; H1 domain mapping, KH xác minh migration/grants |
| Schema/migration/shared DB harness | KH: Table metadata + append-only revision một head, runtime grants, upgrade/recovery checks theo §3/9 |
| 2.05 — prompt 4 | H1: PostgreSQL EvidenceStore standalone/bound, codec/errors và focused tests; reuse foundation; phối hợp KH trước sửa shared files |
| 2.06 — prompt 5 | H1: resolver/support validation + handoff inspection/payload cho VI; VI: evidence component |
| 2.13 — prompt 6 | H1: compound writer/preparation và producer wiring, failure/exit checks, actual smoke/demo |
| Prompt 7 | Audit H1 acceptance trên main mới nhất; human review/acceptance riêng |

Prompt 4 có thể kiểm adapter bằng owned typed fixtures khi workflow producers chưa
nối đủ; phải ghi fixture/domain acceptance riêng, không claim actual end-to-end
evidence pipeline từ kết quả đó.

Runtime: schema USAGE và SELECT/INSERT trên evidence_bundles; đọc analysis_runs/snapshots
theo foundation, không UPDATE/DELETE/TRUNCATE/ALTER/DROP/CREATE hoặc owner membership.
Migration owner riêng; kiểm grants thực, kể cả PUBLIC/inherited privileges, không dùng
owner connection để claim least privilege. Không tự migrate/provision lúc CLI/API startup.

Migration additive, không backfill bundle từ historical report: có thể thiếu frozen
sources/verification và không đủ data. Historical report/run vẫn đọc được; absent bundle
không tự thành empty evidence. Nâng cấp phải giữ inventory/foundation rows, PK/FK/grants;
fresh/upgrade/reapply/head consistency kiểm bằng PostgreSQL thật.
Destructive downgrade không chạy trên dữ liệu không disposable; khuyến nghị từ chối drop
evidence có dữ liệu. Down DDL không khôi phục bytes; recovery dùng backup/restore DB và
report artifacts tại quiescent checkpoint vào isolated targets, kiểm bytes/digest/full
identity/reload. Chưa đo RPO/RTO hoặc claim representative 2 MiB fit.

<a id="p3-acceptance"></a>

## 9. Acceptance matrix — kế hoạch, chưa chạy

| Tình huống | Expected | Tầng/bằng chứng cần thu |
| --- | --- | --- |
| Round-trip Unicode/escaped NUL, defaults/null, paths/spans, order/excerpt | Model và canonical bytes giống; created_at giữ khi retry | Unit codec + PostgreSQL rows/reload, fixtures hợp contract |
| Wrong repo/run/base/target/hash/comparison; null snapshot | Reject, không trộn nguồn | Unit validators + DB scoped/run-binding assertions; key khác hợp lệ không tự coi là conflict |
| Unknown components/evidence/path/edge, cross-snapshot | Reject nested inconsistency | Unit actual EvidenceBundle validators, không chỉ fake adapter |
| Cùng key/exact bytes; cùng key khác bytes/identity | No-op một row; EvidenceConflict | Unit chuẩn bị + PostgreSQL count/full bytes/created_at |
| Hai connections writers giống/khác payload | Một immutable winner; loser no-op/conflict đúng | PostgreSQL barrier/concurrent commit và bounded timeout; MemoryStore không đủ |
| Canonical size cap và +1 byte | Cap cho phép khi valid; vượt báo size error, không SQL write | Unit tạo valid serialized boundary fixtures + DB CHECK trực tiếp bằng test owner |
| Digest sai, invalid JSON/UTF-8, noncanonical/duplicate keys | Corrupt error, không sửa khi load | Unit decode + controlled PostgreSQL tamper bằng test owner, restore/cleanup fixture |
| Format không hỗ trợ | Explicit unsupported error | Unit + DB forged row; không fallback codec |
| Absent row, wrong expected identity, DB unavailable | None, conflict, storage error phân biệt | Unit port/helper defense + PostgreSQL adapter/connection failure |
| Missing prerequisite run/FK, failure sau run/report insert hoặc bundle insert | Reject; transaction rollback phần mới | PostgreSQL actual compound transaction; existing rows giữ nguyên |
| Invalid evidence trước publish, publication failure, bundle conflict sau publish | Không SQL ở preflight/publish failure; rollback + complete orphan ở SQL failure | Unit ordering/failure injection + real file/PostgreSQL integration |
| Commit acknowledgement mất | Safe failure, không delete/auto-retry; reconcile exact captured data | Fault injection ở commit boundary, phân biệt với observed server commit/reload |
| Report/bundle overlap khác, kể cả bundle cũ mà optional input absent | Reject trước commit; không dựng stage success | Unit preparation + PostgreSQL existing-run integration |
| Unverified/unsupported/missing source; inspect sau freeze | Report partial đúng contract; persisted bytes không đổi | Unit resolver/report + reload/inspection cases ở 2.06 |
| Runtime privileges | INSERT/SELECT được; UPDATE/DELETE/TRUNCATE/DDL bị chặn | PostgreSQL runtime-role negative assertions, không owner |
| Fresh/upgrade/reapply và backup/restore | Một head; old rows/artifacts nguyên vẹn, bundle load được | KH harness, schema/grant introspection, restored exact bytes/hash/identity |
| Default CLI/help/health không DB | Giữ behavior, không eager DB imports/settings | Existing boundary tests + focused regression khi wiring |

Unit/fakes không thay PostgreSQL acceptance. Tái sử dụng dedicated harness ở
[setup](postgresql-setup.md#dedicated-test-command); mở rộng harness/recovery catalog
cho evidence thuộc KH phối hợp H1. Tests hiện có chưa bao phủ bảng chưa triển khai;
không lấy số pass 2.13 làm bằng chứng P3/2.05.

<a id="p3-next"></a>

## 10. Bàn giao, checks và quyết định còn lại

Hoàn thành phiên docs: đặc tả đã chốt và cross-links; **chưa hoàn thành 2.05/2.06**.
Profiles: Coordinator/Backend; rules 00/01/03/04/06/13 và root AGENTS;
security-review cho source → typed validation → SQL/file → consumer. Không đổi
producer-consumer schema; api-contracts chỉ cần khi slice sau thay boundary/contract.
Self-review cùng phiên, không independent review hoặc security certification.

Gói P3 đã được nhóm chấp thuận qua H1 ngày 2026-11-04, nguồn tại §1 và D16 trong
[decision register](decision-register.md). Không còn pending quyết định P3.
Prompt 4 đủ đầu vào thiết kế để bắt đầu khi được giao triển khai; acceptance DB
chờ migration/harness KH cùng head thống nhất. Human code review/runtime acceptance
vẫn riêng và chưa xảy ra từ việc chốt thiết kế. Không cần đợi P5 hoặc làm lại
Prompt 2 đã merge. Lượt chốt này không commit/push/merge hoặc bắt đầu prompt 4.

Checks thực tế phiên soạn đặc tả ban đầu: Git roots/status/remotes và fetch main; gh pr view 30 xác
minh merge/CI; đọc source, revision files, tests và tài liệu; kiểm Appendix C/D của
[Proposal v1.4](../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx).
Lần fetch/gh ban đầu trong sandbox lỗi proxy 127.0.0.1:9; chạy lại được bằng quyền
network được công cụ cho phép, không phải lỗi code. Không chạy DB/product suite,
browser hoặc CI mới vì chỉ Markdown; link/fence/table/whitespace/scope checks được
kiểm bằng PowerShell + Python inline (không tạo script/dependency mới): **PASS**, 5
file Markdown, 360 local links/anchors, 38 bảng, code fences, UTF-8/EOF/whitespace
và scope; không có broken link mới hoặc cũ trong các file đổi. `git diff --check`
exit 0. Static AST check của revision files xác nhận một head `20261104_03`,
không import/run migration hoặc kiểm deployed DB. `git rev-parse HEAD^{tree}` và
`git rev-parse origin/main^{tree}` cùng `d7540d834a27ce0a0d43d5452040fbfd9302107c`.
Đây là kiểm chứng docs/baseline, không phải product test results.

OpenAI Codex hỗ trợ audit, so sánh phương án, soạn spec/acceptance và self-review.
Nhóm đã xác nhận quyết định thiết kế; vẫn cần đọc/hiểu/review và kiểm chứng implementation.
Chữ ký/tỷ lệ cũ trong
Appendix C/D không phê duyệt nội dung mới. Không tạo service/process, cài dependency
hoặc lưu artifacts/secret trong phiên này.
