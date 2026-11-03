# Task 2.20-A — Checkpoint PostgreSQL foundation

> Tiếp nối implementation 2.20-B ngày 2026-11-03: H1 đã triển khai cục bộ
> dependencies/config/connection/application metadata boundary; xem
> [handoff 2.20-B](task-2.20-b.md). Schema/migrations KH, durable adapter và
> PostgreSQL acceptance vẫn pending. Các mô tả checkpoint bên dưới giữ mốc lịch sử;
> không coi code local đã có trên main hoặc task 2.20 đã Done.

## 1. Trạng thái, nguồn và baseline

**Checkpoint thiết kế để review; chưa triển khai database.** PostgreSQL engine đã
accepted theo người dùng và [team guide 2.20](sprint-2-team-guide.md#task-220).
P1/P2/P4 (tooling, foundation schema và writer boundaries) đã **accepted** theo
xác nhận của Nguyễn Tấn Huy ngày 2026-11-03: “nhóm đã thống chất toàn bộ các điểm
này”, trả lời danh sách P1/P2/P4 ngay trước đó. Đây là quyết định nhóm do H1 truyền
đạt, không phải mentor approval hoặc bằng chứng implementation. P3/P5 vẫn riêng,
không suy xác nhận này chốt bundle policy/retrieval backend. Không đóng task 2.20
hoặc thay allocation backlog.

- Main được fetch: `d30388fae09a8fb413c20b8afc7d7c38c5e361c4`, merge thin workflow 2.13.
- Ngày đối chiếu: 2026-11-03. Không mặc định remote không đổi sau lúc fetch.
- Checkout: `D:\smart-regression-ai\var\main-review-20261103`;
  nhánh local `docs/sprint-2-2.20-checkpoint`, xuất phát từ origin/main sạch.
- Scope phiên: đọc code/history/nguồn chính thức, viết Markdown. Không code, cài
  packages, tạo/chạy migrations, kết nối/thay dữ liệu PostgreSQL, commit/push/merge.
- Sau bàn giao, user giao commit/push và mở PR để review/merge checkpoint này.
  Quyền publish mới không tự chốt tooling/schema, không tự approve hoặc merge.
- Checkout gốc `D:\smart-regression-ai` và untracked files có sẵn được giữ nguyên.
  Không đọc open PR, gửi tin nhắn hoặc khởi chạy sub-agent.

Nguồn yêu cầu: [Scrum workbook v1.4](../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx),
`Sprint 2 Backlog!B169:Z173`; consumers `B79:Z89`, `B97:Z113`, `B127:Z137`.
Đọc cả inline strings và shared strings trong workbook, không sửa file. H1 12h
contracts/connection + KH 12h migrations/integration checks; 24h là preliminary
estimate. AN là reviewer đề xuất, chưa nhận/approve trong phiên này.

Nguồn thiết kế: [DB Design v1.5](../../C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx)
§2.4 (prerequisites) và §3.4 (domain). Revision history của tài liệu ghi pending;
không suy ra mentor-approved hoặc tables đã tồn tại. [D06](decision-register.md)
và storage README là mô tả bootstrap cũ; engine đã được user chốt sau đó, các
quyết định provider/index/retention khác vẫn pending.

Nguồn runtime: [contracts v2](../contracts/stage-reports.md), [stages.py](../../backend/src/smartregression/contracts/stages.py),
[handoff 2.14](task-2.14.md), [handoff 2.13](task-2.13.md),
[architecture](../architecture/overview.md), ADR [0001](../architecture/decisions/0001-bootstrap.md)
và [0002](../architecture/decisions/0002-python-pytest-input.md).
Contracts mô tả runtime hiện hành; DB Design cần mapping/reconciliation, không
được chép nguyên SQL types/semantics rồi đổi public contract để khớp.

## 2. Audit merged code

| Hạng mục | Có trên main / bằng chứng | Gap 2.20 và consumer |
| --- | --- | --- |
| DB dependency/config | [pyproject](../../pyproject.toml), [uv.lock](../../uv.lock) chưa có psycopg/SQLAlchemy/Alembic; [.env.example](../../.env.example) chỉ provider comment | Chưa có PostgreSQL config/connection; H1 |
| Migrations | [storage](../../backend/src/smartregression/adapters/storage/README.md) README-only; chưa có migration files/config/runner | KH cần triển khai mechanism sau quyết định |
| Transactions | Không có DB adapter/transaction boundary | KH/H1 kiểm rollback, connection lifecycle thật |
| Identity | `RunIdentity`, `SnapshotIdentity`; `application.snapshots.prepare_snapshots`, `stage_conversion.identity_from_snapshots` | Có frozen identity/hash; chưa có PK/FK persisted |
| Evidence persistence | [EvidenceStore/save_evidence/load_evidence](../../backend/src/smartregression/application/evidence_store.py) và `EvidenceBundle` | Protocol + application checks, chưa có durable adapter; 2.05 |
| Storage tests | [test_stage_storage.py](../../backend/tests/unit/test_stage_storage.py) dùng MemoryStore | Không chứng minh PostgreSQL atomicity/concurrency/FKs |
| Run/status/config | [analysis.py](../../backend/src/smartregression/application/analysis.py) trả report v2; run/report IDs do application sinh | Chưa lưu run/config/status/limitations; 2.13 tích hợp sau |
| Artifact output | [report_output.py](../../backend/src/smartregression/adapters/report_output.py) publish JSON file hoàn chỉnh | Chưa có artifact catalog, digest lookup/reload hoặc DB/file coordination |
| Composition | [composition.py](../../backend/src/smartregression/composition.py) nối LocalGit → application | Chưa inject DB; giữ read-only analyze hoạt động không cần DB |
| DB setup/recovery | [verified commands](verified-commands.md) chưa có migration/DB acceptance commands | Chưa có real PostgreSQL evidence, backup/restore instructions |

Có schema/JSON/fake store không có nghĩa đã persistence. Trong thin flow hiện tại,
impact/inventory/retrieval/evidence chưa triển khai; không cần đợi chúng để làm
foundation, nhưng fixtures không thay acceptance của actual producers.

## 3. Tooling recommendation

**Phương án A đã chốt (P1): synchronous SQLAlchemy Core + psycopg 3 binary + Alembic.** Dùng Core
Table/statement, chưa dùng ORM Session/relationships hoặc async stack. CLI/use case
hiện synchronous; không có analyze endpoint cần async DB. Core/adapters boundary
giữ nguyên, SQLAlchemy/driver chỉ trong storage adapter và migration layer.

| Phương án | Ưu điểm | Chi phí/rủi ro trong slice 24h | Kết luận |
| --- | --- | --- | --- |
| A. Core + psycopg + Alembic | Connection/transaction/pool và versioned migrations có công cụ sẵn; cùng metadata cho schema | Ba direct dependencies, cần hiểu Core/Alembic và review migration; transitive packages cần lock | Khuyến nghị; tránh tự viết migration runner |
| B. psycopg + Yoyo migrations | SQL trực tiếp, ít lớp runtime; Yoyo có psycopg3 backend và per-file transaction | PyPI Yoyo chưa công bố classifier 3.14 trong metadata đã đọc; phải kiểm compatibility thực; riêng SQL/schema mapping | Có thể dùng nếu nhóm đã quen SQL và chấp nhận spike compatibility, không ưu tiên lúc này |
| C. ORM + psycopg + Alembic | Thuận lợi khi entity CRUD/relationship lớn | Session, identity-map/lazy loading tăng khái niệm chưa cần cho save/load immutable bundle | Deferred; không cần ORM để dùng Alembic |

### 3.1. Compatibility đã kiểm và giới hạn

Metadata PyPI đọc ngày nêu trên (không phải packages đã install):

| Package | Version quan sát | Python metadata và artifacts |
| --- | --- | --- |
| [SQLAlchemy](https://pypi.org/project/SQLAlchemy/2.1.6/) | 2.1.6 | Requires-Python >=3.11; classifier 3.14; cp314 Windows amd64/Linux x86_64 và pure wheel |
| [psycopg](https://pypi.org/project/psycopg/3.3.7/) | 3.3.7 | >=3.10; classifier 3.14; pure wheel; binary extra pin cùng version |
| [psycopg-binary](https://pypi.org/project/psycopg-binary/3.3.7/) | 3.3.7 | cp314-cp314 win_amd64 và manylinux x86_64 quan sát được |
| [Alembic](https://pypi.org/project/alembic/1.20.1/) | 1.20.1 | >=3.10; classifier 3.14; py3-none-any wheel; requires SQLAlchemy >=2.0 |
| [Yoyo](https://pypi.org/project/yoyo-migrations/9.0.0/) | 9.0.0 | Metadata không xác lập hỗ trợ 3.14; không kết luận incompatible chỉ vì thiếu classifier |

Candidate ranges để H1 resolve/lock trong implementation: SQLAlchemy >=2.1.6,<2.2;
psycopg[binary] >=3.3.7,<3.4; Alembic >=1.20.1,<1.21. Runtime Core/driver ở project
dependencies; Alembic ở dev group cho local operator migration trong sprint này.
Deploy/migration image tương lai phải cài migration dependencies riêng, không
giả runtime-only environment có Alembic. Revalidate metadata khi implementation;
không downgrade/nâng runtime Python để né failure. uv sinh lock, không sửa tay.

SQLAlchemy sync không cần thêm asyncio extra/greenlet theo metadata quan sát.
Alembic có Mako/typing-extensions, psycopg trên Windows có tzdata; uv resolve cả
transitive dependencies. Không thêm psycopg_pool song song với SQLAlchemy pool.
Binary extra giúp local Windows không cần build libpq; upgrade package để nhận
binary fixes vẫn là trách nhiệm nhóm, chưa phải deployment policy lâu dài.

Nguồn chính thức đã đọc: [psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html)
(tài liệu nêu Python 3.10–3.15, PostgreSQL 10–18),
[SQLAlchemy psycopg dialect](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg),
[Core transactions](https://docs.sqlalchemy.org/en/21/core/connections.html),
[Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
[autogenerate limitations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html),
[Yoyo official docs](https://ollycope.com/software/yoyo/latest/).
Metadata/docs chứng minh declared support, không chứng minh stack chạy cùng repo.
Clean locked install + PostgreSQL smoke là gate implementation, chưa chạy ở đây.

Đề xuất server baseline **PostgreSQL 17.x** local/test; KH pin exact patch/image
digest trong setup evidence khi triển khai. Chưa khẳng định đã có server/container
này; không thêm pgvector hoặc chọn vector backend. Nếu nhóm đã provision bản khác,
ghi và kiểm compatible trước thay baseline, không âm thầm đổi.

## 4. Scope và migration sequence

Foundation 2.20 đã chốt (P2) chỉ **5 application tables** + bảng version do Alembic quản
lý. Không tạo full DB Design. Naming/fields dưới đây là schema dự kiến, không phải
DDL đã tạo. Schema qualification cố định `smartregression`; không lấy schema/table
name từ input. Một Alembic head, KH là migration writer duy nhất.

| Phase/migration dự kiến | Phạm vi | Writer / input |
| --- | --- | --- |
| M001 | repositories → snapshots → analysis_runs | KH dùng mapping H1 đã review |
| M002 | artifacts → run_reports và indexes/constraints tương ứng | KH; H1 report/config contract |
| M003 | Bounded evidence_bundles của 2.05 | KH migration; H1 domain design/adapter, ngoài giờ foundation |
| M004+ | inventory/test cases và index/chunks khi contracts/producer decisions đủ | KH điều phối thứ tự; domain owner gửi mapping, không tự thêm migrations |

M001/M002 làm trong 2.20; có thể cùng một implementation PR để KH/H1 test chung,
không bắt merge skeleton chưa hoạt động. Tên revision ID thực do Alembic sinh khi
implementation, không coi M001 là command/revision đã tồn tại.

Deferred: app_users/repository_access/auth, full test_configurations service,
run_events/history UI, queue/jobs/retry orchestration, test selection/execution,
LLM calls, CI integration, evaluation tables; vector embeddings ngoài metadata DB.

## 5. Common identity và constraints

- RepositoryId: `text`, application theo regex canonical 1–128 ASCII; DB CHECK cùng
  pattern và PK, không đổi thành UUID/GitHub ID/path. External provider mapping đến
  sau; local authorized fixture không cần fake GitHub repository ID.
- Run/report/component/test IDs: canonical `Text` hoặc native ID, không ép UUID;
  store giá trị đã normalize/validate, không truncate/cast. CLI đang sinh UUID là
  implementation detail. Run key `(repository_id, run_id)` đúng EvidenceStore.
- Giới hạn storage thuộc P2 đã chốt: PostgreSQL text không chứa U+0000, B-tree keys
  có byte-size limit trong khi canonical Text chưa có max length. Đề xuất kiểm
  run_id/report_id/artifact_id metadata <=512 UTF-8 bytes, không U+0000 trước SQL;
  unsupported input báo persistence error, không truncate/đổi ID hoặc đổi validator
  public. Đây là giới hạn persistence cần kiểm chứng implementation, không claim mọi JSON-valid
  Text đều lưu được. Component IDs/excerpts trong bundle bytea vẫn giữ bytes đầy đủ;
  native test ID limits chốt riêng với KH trước domain schema, không áp cap 512 giả.
- SHA: `text`, CHECK full lowercase 40 hoặc 64 hex; digest: `text`, 64 lowercase hex.
  Không dùng fixed char padding. Timestamp `timestamptz`, UTC; unknown measurement
  SQL NULL, không default 0. IDs không rỗng; Unicode whitespace normalization ở app.
- Scope FK luôn có repository/run khi cần. FK ON UPDATE/DELETE RESTRICT; không
  cascade xóa domain/history. Retention/purge có task/decision riêng.
- Optional composite FK dùng MATCH SIMPLE khi null hash/run là hợp lệ, thêm CHECK
  presence cần thiết; không dùng nullable field để bypass invariant ngoài ý muốn.
  PostgreSQL CHECK coi NULL là không vi phạm: cần NOT NULL riêng cho required fields.
  Xem [official constraints](https://www.postgresql.org/docs/current/ddl-constraints.html).
- DB giữ keys/basic field consistency; application revalidate canonical schema,
  all identity, edge/path references và status aggregation. SQL CHECK không đọc
  bảng khác để giả cross-row/graph validation; source resolver kiểm source/support.

### 5.1. A — repositories

Use case: root identity cho mọi persisted run, provision tại trusted local boundary.

| Fields dự kiến | Null/key/check |
| --- | --- |
| repository_id text | NOT NULL PK; RepositoryId pattern |
| source_kind text | NOT NULL; local hoặc github; giá trị từ acquisition thật |
| created_at timestamptz | NOT NULL, insertion time |

Không lưu raw credentials/DSN/local checkout path vào report/config này. Mapping
ID → authorized source do composition/integration giữ; row tồn tại không cấp quyền.
Không dùng bundle upload để tự đăng ký repository. Không có created_by FK giả.
Index PK phục vụ exact repository lookup; lifecycle giữ identity sau mỗi run.
Owner schema KH, source binding contract H1; DB Design §2.4.2 được thu hẹp rõ ràng.

### 5.2. A — snapshots

Use case: frozen content identity, không chứa source bytes/whole manifest.

| Fields dự kiến | Null/key/check |
| --- | --- |
| repository_id text, commit_sha text, snapshot_id text | NOT NULL; PK cả ba; repo FK; SHA/digest CHECK |
| manifest_version text, materializer_version text | NOT NULL; từ actual SnapshotManifest, không placeholder |
| created_at timestamptz | NOT NULL |

Không UNIQUE(repo, commit) vì materializer/version khác có thể cho hash khác;
một run vẫn pin đúng hash cụ thể. Prefix PK phục vụ repo/commit/hash lookup, không
thêm indexes trùng. App kiểm hash với trusted frozen bytes trước insert; row không
tự chứng minh files đúng. Snapshot artifact/catalog có thể thêm ở domain phase,
không cần circular FK vào artifacts để lưu minimum identity.

### 5.3. A — analysis_runs

Use case: immutable comparison/config binding, không thay report completeness.

| Fields dự kiến | Null/key/check |
| --- | --- |
| repository_id text, run_id text | NOT NULL composite PK; repository FK |
| base_sha text, target_sha text | NOT NULL full SHA |
| base_snapshot_id text, target_snapshot_id text | Nullable digest; riêng từng side |
| comparison_mode text | NOT NULL, direct_two_tree |
| data_kind text | NOT NULL demo/real, từ validated caller declaration |
| configuration jsonb, configuration_sha256 text | NOT NULL object/hash; canonicalized actual config |
| created_at timestamptz | NOT NULL |

FK `(repository_id, base_sha, base_snapshot_id)` → snapshots PK; tương tự target.
Null hash giữ failure identity chưa materialize, không tạo snapshot row giả.
Khi cả hai hashes non-null và base=target, CHECK yêu cầu hashes bằng nhau. App
còn kiểm stage data có yêu cầu materialized hash hay không theo v2 validators.

Freeze repo/run/commits/hashes/config/data_kind sau insert trong scope này. Nếu
retry acquisition để bổ sung hash sau failure, tạo run mới; không update identity
âm thầm. Report bổ sung trong cùng run chỉ khi giữ nguyên identity/config.
Không thêm `queued/running/completed` job lifecycle hay fake request_key/attempts.

Configuration object allowlist, dự kiến: application/build version có nguồn,
comparison mode, snapshot limits, Python source limit, graph target-side policy,
producer versions khi có. Unknown producer version là null/explicit limitation,
không invent version. DSN/password/input source/outcomes/fault labels không nằm
trong config. Hash cấu hình derive từ canonical_json ở app; DB CHECK format,
không giả kiểm content hash bằng một regex. Đề xuất config cap 64 KiB, báo lỗi
trước insert nếu vượt; giữ nguyên canonical contract, không silently truncate.

PK phục vụ exact get(repo,run); chưa có history listing nên chưa thêm date index.
Schema KH, metadata contract và capture actual config H1/consumer 2.13.

### 5.4. A — artifacts

Use case: protected file metadata, không chứa snapshot/log/report bytes.

| Fields dự kiến | Null/key/check |
| --- | --- |
| repository_id text, artifact_id text | NOT NULL composite PK; repo FK |
| run_id text | Nullable; nếu có thì composite FK(repo,run) → analysis_runs |
| storage_key text | NOT NULL unique; opaque backend-relative locator |
| kind text | NOT NULL; snapshot, manifest, report_json, log hoặc index khi actual writer có |
| sha256 text, size_bytes bigint, media_type text | NOT NULL; digest, size >=0 |
| schema_version text | Nullable; khi kind report_json thì NOT NULL và supported version |
| access_class text | NOT NULL; repository hoặc service_only cho scope hiện tại |
| created_at timestamptz | NOT NULL |

UQ `(repository_id, run_id, artifact_id)` để report FK scope đủ; FK run nullable
cho snapshot/index repo-level, nhưng report artifacts bắt buộc run_id. Cùng
artifact ID không được đổi bytes/hash/kind/scope. storage_key không chứa secret
hoặc external arbitrary URL; app resolve dưới artifact root, chặn traversal,
symlink/junction và verify digest/size khi đọc. Index(repo,run) chỉ thêm nếu run
artifact listing thực sự được dùng; report lookup dùng FK/UQ hiện có.

### 5.5. A — run_reports

Use case: immutable report publication metadata, trạng thái không suy từ bundle.

| Fields dự kiến | Null/key/check |
| --- | --- |
| repository_id text, run_id text, report_id text | NOT NULL composite PK; FK(repo,run) |
| artifact_id text | NOT NULL; scoped FK(repo,run,artifact_id) → artifacts UQ |
| schema_version text | NOT NULL, 2.0.0 cho new persistence use case |
| analysis_status text | NOT NULL, đúng năm StageStatus hiện hành |
| stage_summary jsonb | NOT NULL object; tám explicit stage keys |
| analysis_duration_seconds double precision, llm_cost_usd double precision | Nullable, finite và >=0 khi có, không default zero |
| created_at timestamptz | NOT NULL |

Summary chỉ chứa status/reason/error_code/limitations của từng stage, không có
full payload/source/excerpt. CHECK đủ tám keys, object shape tối thiểu; app validate
envelopes và aggregate, so summary/measurements với report bytes và RunIdentity
trước save + sau load. Cap summary đề xuất 256 KiB; oversized báo lỗi, không drop
limitations. Full report ở immutable artifact để giữ nested payload/version chính
xác; catalogue row không thay runtime validation hoặc source verification.

Không chọn report “mới nhất” theo timestamp để overwrite domain data. Consumer
đọc explicit repo/run/report ID. Nhiều reports cùng run phải có report_id khác;
same key cùng digest/metadata là no-op, khác nội dung là conflict. Không tự migrate
legacy v1 files; v1 validator/CLI vẫn giữ nguyên, persistence use case này typed v2.
Report reference phải đúng artifact kind/schema/scope qua application transaction.

## 6. B — Domain consumers, không triển khai trong foundation

### 6.1. 2.05 — evidence_bundles theo existing port

Minimum consumer hiện có chỉ là save/load bằng `(repo,run)`, chưa có SQL query theo
symbol/path. **Đề xuất M003 lưu bounded canonical bundle bytes trong PostgreSQL**,
giữ whole report/log/snapshots ở artifacts. Đây là domain record có giới hạn,
không biến metadata DB thành source-code/artifact store.

Fields dự kiến: `repository_id text`, `run_id text` (PK/FK analysis_runs);
`bundle_format text NOT NULL` (internal storage codec, ví dụ evidence-bundle/1,
không thêm schema_version vào public model); `payload bytea NOT NULL`,
`payload_sha256 text NOT NULL`, `created_at timestamptz NOT NULL`.
DB CHECK digest format và `octet_length(payload) <= 2_097_152`; application cap
đề xuất cùng 2 MiB và validate trước transaction. Vượt cap: explicit
EvidenceStorageError với safe diagnostic, không truncate/fallback/file success
âm thầm. Nếu representative data vượt cap, mở scope review về artifact-backed
bundle/normalization; không tự mở rộng storage policy trong 2.05.

`payload` là `canonical_json(bundle.model_dump(mode="json"))`, UTF-8 bytes, không
compression/custom pickle. Byte equality là chuẩn retry; digest chỉ hỗ trợ integrity,
không dùng digest một mình để kết luận nội dung giống. Decode + EvidenceBundle
validation + expected identity check khi load. Composite FK buộc run tồn tại;
app so cả hai snapshot hashes/SHAs với immutable run trước khi write/read.

| Representation đã cân nhắc | Trade-off / quyết định proposed |
| --- | --- |
| JSONB toàn bundle | Dễ inspect/query, giữ array order nhưng không giữ byte representation/object key order; SQL equality không thay canonical byte comparison; JSONB không biểu diễn mọi JSON string như U+0000 |
| Bounded canonical bytea + relational run binding | Exact bytes/array order, phù hợp port immutable save/load, không lỗi codec text JSONB; không SQL-query nested paths; chọn cho M003 |
| Normalize toàn DB §3.4.1–5 ngay | Tốt cho query/FKs từng edge, nhưng producer shape chưa khớp và nhiều tables/joins ngoài consumer hiện có; deferred tới khi có nhu cầu query cụ thể |

Không claim DB FK bên trong bytea: unknown component/path/evidence và cùng snapshot
edge support do typed validators/application kiểm transactionally, resolver 2.06
kiểm source/support. DB chỉ bảo vệ key/run/size/basic constraints. Storage runtime
role không UPDATE/DELETE bundle; migration owner có quyền bảo trì riêng. Tests
tampered/corrupt payload vẫn bắt buộc, dù database không tự decode bundle.

Mapping DB Design §3.4.1–5: changed files/components/ranges, graph nodes/edges,
impact candidates/paths và evidence đều giữ lossless trong canonical domain bundle;
chưa tạo tables cùng tên nên không được gọi là implementation normalized design.
Reconciliation này cần nhóm chốt trong §11. Không tự điền missing source_location,
review_rank/explanation hoặc tạo component IDs mới cho graph module nodes.

### 6.2. 2.08/09 — inventory metadata checkpoint

Future `test_inventories`: PK `(repo,run,inventory_id text)`, FK run + target snapshot;
one frozen inventory/run bằng UQ(repo,run); stage_status năm giá trị canonical,
completeness nullable (complete/partial), test_count nullable >=0, reason/error và
limitations; schema/config/adapter identity chỉ từ actual producer. `test_cases`:
PK(repo,run,inventory_id,test_id text), composite FK inventory; framework-native
IDs không bị chuyển UUID. Payload hiện chưa có file/display_name/component mapping,
nên không đặt NOT NULL các field DB Design đó khi chưa có nguồn. Optional mapping
2.16 chỉ được thêm khi producer có target component identity đáng tin.

| Report inventory | Persistence semantics đề xuất thay DB Design legacy status |
| --- | --- |
| not_implemented / not_run | Giữ status + reason; completeness/count NULL, không success_empty |
| failed | Error code, count NULL; không coi rows của collection dở dang là inventory hoàn chỉnh |
| partial | Data/completeness=partial, count là số IDs quan sát, kể cả 0; limitations bắt buộc |
| completed, count=0 | completeness=complete, count=0; đây mới là successful empty |
| completed, count>0 | completeness=complete, count>0 |

DB Design pending không map 1–1 sang mọi inactive stage; không giữ enum cũ rồi
ép partial thành success. Sửa design được chấp nhận trước M004; KH sở hữu producer
metadata và migration. Native IDs/count kiểm exact unique rows trong transaction;
SQL constraints không chứng minh discovery đã chạy cô lập.

### 6.3. 2.10–12 — index/chunk metadata checkpoint

Future `knowledge_indexes`: scoped PK(repo,index_id text), FK(repo,commit,snapshot);
configuration_id text + canonical configuration hash, producer/index version,
namespace key unique, backend_kind, embedding_model nullable, build state,
manifest artifact ref, nullable measured duration. UQ phải chứa repo/snapshot/config/
index version; không chỉ repo/commit để reuse index khác config.
`knowledge_chunks`: PK(repo,index_id,chunk_id text), FK index; chunk key unique trong
index, relative path, ordered positive range, content_sha256, source kind và scoped
content artifact ref; không chứa vector/source text lớn trong metadata DB.

Proposed reconciliation §3.4.8: embedding_model NULL với lexical backend thật;
embedding backend yêu cầu actual model/version trong config. Backend chưa chốt thì
chưa build/ready, không dùng giá trị “none/demo-model” để thỏa NOT NULL. Đây không
phải quyết định chọn lexical/embedding hoặc pgvector. State building/ready/failed
là producer lifecycle riêng, không đổi StageStatus. Ready chỉ sau manifest/chunks
cùng snapshot/config đã publish/commit/verify. Retrieval item/source identities
map đúng index/config; stale/incomplete builds không ready. Index metadata migration
đợi H2/KH/VI xác nhận queries/config; không tạo placeholder tables trong M001/M002.

## 7. Reconciliation bắt buộc trước implementation

| DB Design v1.5 | Canonical runtime / đề xuất xử lý |
| --- | --- |
| §2.4.2–5 UUID IDs, GitHub/user/config FKs required | Text IDs, local repo hợp lệ; defer auth/full config service, inline versioned config snapshot ở run; không dummy keys |
| §2.4.5 run lifecycle queued/running/completed/failed | Foundation chỉ immutable run binding; report giữ completeness năm states, không dùng job state để gán report success |
| §2.4.5 PR merge-base/head | CLI hiện direct two-tree/full SHAs; chưa implement PR resolution hoặc đổi revision policy |
| §3.4.2 component spans/qualified_name bắt buộc | Stage file metadata không có spans, module có thể không có symbol/range; giữ nullability/kind hiện hành |
| §3.4.3 import/call, required source_location/parser_version | Actual graph là module import edges, không có call/source spans; không fabricating thêm data để insert |
| §3.4.4 một impact/component, một dependency_path | Canonical cho nhiều changed origins/paths và evidence IDs; review ordering là stage khác, không bắt rank/explanation giả |
| §3.4.5 unverified/verified/invalid | Giữ riêng resolution + support; resolved không đồng nghĩa supported; producer assertion không thay trusted resolver |
| §3.4.6 inventory status chưa partial | Mapping §6.2, không success_empty khi chưa chạy/failed |
| §3.4.8 embedding_model NOT NULL | Nullable có điều kiện backend/config như §6.3; chưa chọn retrieval backend |

Đề xuất không đổi schema public 2.0.0/1.0.0, OpenAPI/types hoặc legacy CLI. Nếu
implementation thấy cần breaking contract change, quay về checkpoint với consumer
impact; không sửa generated files tay. DB Design DOCX chưa được sửa trong phiên này.

## 8. Transaction, retry và DB/file publication

### 8.1. Domain save/load

Port EvidenceStore không đổi. Proposed transaction flow của adapter 2.05:

1. `save_evidence` revalidate/deep-copy; canonical bytes, digest và size check.
2. Mở transaction; tìm immutable run bằng composite key, so toàn bộ expected identity.
   Run không tồn tại không tự tạo placeholder; báo storage failure/conflict có mã đúng.
3. INSERT bundle ON CONFLICT DO NOTHING theo key; nếu conflict, SELECT committed row
   sau đó compare full bytes/identity. Identical no-op; khác payload/identity là
   EvidenceConflict (`evidence_conflict`), transaction rollback.
4. Không UPDATE bundle để “retry thành công”. DB unique key serialize concurrent
   insert; loser chờ bounded lock timeout, rồi so winner. READ COMMITTED đủ cho
   protocol này với immutable rows/RESTRICT; không dùng SELECT-then-INSERT đơn thuần.
5. Commit một lần tại transaction owner. Ambiguous commit/connection loss báo
   EvidenceStorageError (`evidence_storage_failed`); caller có thể retry cùng key/bytes,
   không tự replay workflow chạy producer/input code.
6. Load exact key; absent → None; DB unavailable/query failure → EvidenceStorageError.
   Có row nhưng expected identity khác → conflict, không trả None hoặc bundle foreign.
   Corrupt bytes/hash/schema → storage failure; helper còn revalidate expected identity.

Multi-table report save dùng cùng transaction owner. Concrete adapters nhận bound
connection khi composition muốn atomic run/bundle/report insert, không tự commit
trong nested save. Standalone EvidenceStore dùng own transaction; bound variant
chỉ valid trong context sống. Application port không import SQLAlchemy Connection;
adapter factory ở composition chịu ownership, không xây generic repository framework.
Standalone save yêu cầu run/snapshots/config đã được trusted run registration tạo
trước đó; interface EvidenceStore không có config/manifest inputs nên không được
tự insert run thiếu metadata. Compound writer thực hiện registration và save trong
cùng transaction, giữ scope FK và snapshot requirements như §5.

### 8.2. Report và artifact

Future `persist_run_result(report, actual_configuration, snapshot_metadata,
optional_bundle)` là application use case dự kiến, không phải function đã có.
`snapshot_metadata` lấy từ manifests đã được acquisition/hash validation tin cậy,
gồm repo/commit/hash/manifest_version/materializer_version. Report v2 chỉ có
SnapshotIdentity, không tự chứa hai version fields để tạo snapshot row mới.
Nếu chỉ import report offline, phải có matching snapshot row/metadata đã được
xác minh; thiếu thì reject, không suy version từ một hash hoặc tự điền git-blobs/1.
Null-hash failure side không cần snapshot registration. Trước transaction phải
validate report, identity/config và bundle nếu có; compare overlapping payload với
report, không gộp bundle/report từ hai runs hoặc hai observations khác nhau.
Optional bundle không được suy ra từ việc run từng có bundle: nếu report hiện
không có domain data thì không tự load bundle cũ để điền success. Nếu cùng run đã
có bundle và caller gửi bundle mới khác bytes, conflict thay vì thay thế bản cũ.

Publish complete report bytes dưới backend artifact root trước; flush/publish
exclusive, compute digest/size, không overwrite. Sau publish, một DB transaction
ghi snapshot/run prerequisites, artifacts row, run_reports summary và optional
bundle. Existing repo phải đã provision/authorize; validators bảo vệ scope. Dữ
liệu terminal hiện immutable; status refresh tạo report_id mới, không sửa report cũ.

| Failure point | Kết quả phải báo / recovery |
| --- | --- |
| File write/publish thất bại | Không tạo report/artifact catalog success row; giữ analysis result riêng nếu đã có, surface storage error |
| File publish xong, DB transaction fail | DB rollback, có thể còn orphan file; không báo persisted success; giữ manifest/digest để operator reconcile |
| DB commit acknowledgement mất | Không tự xóa file: commit có thể đã thành công; retry exact IDs/digests để xác định hoặc báo ambiguous storage failure |
| DB có ref nhưng file bị mất/corrupt | Read failure rõ, không dựng report completed từ summary/bundle |
| Domain/report mismatch | Reject trước commit; không persist bundle mới cạnh report cũ trái nhau |

Không distributed transaction hoặc background GC trong 2.20. Orphan cleanup chỉ
operator action có kiểm ownership/scope và DB reachability; không tự recursive
delete hoặc xóa file có thể đã commit. Backup/recovery bao gồm DB và artifact root;
không copy live files tùy ý rồi gọi consistent backup. Không nhầm storage failure
với analysis/test failure; chưa thêm public persistence status vào v2 trong checkpoint.

## 9. Configuration và security contract proposed

| Input backend-only dự kiến | Rule |
| --- | --- |
| SMARTREGRESSION_DATABASE_URL | Required khi explicit DB feature được gọi; dialect PostgreSQL+psycopg; không CLI argv/ini commit DSN thật |
| SMARTREGRESSION_MIGRATION_DATABASE_URL | Migration command dùng riêng owner credentials; runtime không tự đọc/escalate role |
| SMARTREGRESSION_DB_CONNECT_TIMEOUT_SECONDS | Đề xuất default 5, integer 1–30 |
| SMARTREGRESSION_DB_STATEMENT_TIMEOUT_MS | Đề xuất 10000, 100–60000; đặt server-side cho connection |
| SMARTREGRESSION_DB_LOCK_TIMEOUT_MS | Đề xuất 3000, >0 và không vượt statement timeout |
| SMARTREGRESSION_ARTIFACT_ROOT | Required chỉ khi publish report; controlled directory ngoài input repo; không VITE_* |

Names/defaults chưa triển khai. DB optional cho existing read-only CLI/health;
explicit persistence mà thiếu config phải fail rõ, không silently dùng MemoryStore
hoặc SQLite. H1 dùng URL parser/URL object của tooling, không tự split strings,
validate nonempty host/db/user, TLS policy phù hợp deployment: loopback test có thể
disable SSL theo setup rõ; remote yêu cầu certificate verification, không âm thầm
lower security. Error/log/config repr không chứa password/userinfo/raw SQL params.

Một Engine per command/process, bounded QueuePool đề xuất size=2/max_overflow=0,
pool_timeout=5s, pre_ping; short connection contexts, finally dispose. Không mở
connection lúc import, không migration-on-startup/create_all thay migrations.
`Engine.begin()` commit-on-success/rollback-on-exception theo official docs; kiểm
thực trong DB test. Không automatic whole-transaction retries ở foundation.

Migration owner tạo/alter objects; runtime role không DDL/owner, không superuser;
initial scope chỉ SELECT/INSERT immutable run/report/bundle metadata và quyền
schema USAGE cần thiết, không UPDATE/DELETE bundle. Quyền build metadata tương lai
được review tại consumer riêng. Fixed/qualified schema, parameters cho values,
identifiers là declarations cố định; không f-string input thành SQL. Secrets ở
backend environment/secret references, `.env.example` chỉ placeholder; không copy
DSN vào config snapshot/report/tests artifacts hoặc frontend.

Local operator binding và repository_id không là multi-user auth. Không mở DB-
backed multi-user API/report download cho tới khi có real backend authorization.
Stored source/RAG vẫn untrusted data; không thực thi để kiểm SQL hoặc schema.

## 10. Writer ownership và kế hoạch triển khai

Writer boundaries đã được nhóm chốt theo xác nhận H1 (P4), trong allocation đã có.
Agent chưa gửi tin nhắn/khởi công việc thay thành viên; không giả independent review.
Paths chưa tồn tại đều **dự kiến**, cần kiểm lại main khi triển khai để tránh xung đột.

| Deliverable | Writer duy nhất | Reader/reviewer đề xuất | Paths / dependency / acceptance |
| --- | --- | --- | --- |
| Tooling/config/application interfaces | H1 | KH, AN | Checkpoint này; acceptance quyết định §11 |
| Manifest/lockfile cho cả runtime + Alembic | H1 | KH | pyproject.toml, uv.lock; KH gửi dependency need, H1 dùng uv resolve một lần |
| DB settings/engine/error translation | H1 | KH/AN | Dự kiến adapters/storage/{config,connection,errors}.py; actual connection/no-secret evidence |
| Core Table metadata + migration versions/config | KH | H1/AN | Dự kiến adapters/storage/schema.py, migrations/env.py, migrations/versions/, alembic.ini; một writer, một head |
| Run/report persistence ports và trusted config metadata | H1 | KH/AN | Dự kiến application/run_store.py; chưa nối CLI hoặc thay contract trong 2.20-B |
| Foundation run/report metadata adapter | H1 | KH | Dự kiến adapters/storage/run_store.py; sau schema handoff KH, scoped transaction tests |
| Shared DB fixture/setup, migration/recovery integration tests | KH | H1/AN | Dự kiến backend/tests/integration/storage/, conftest storage-local, docs/development/postgresql-setup.md |
| Config/connection unit tests | H1 | KH | Dự kiến backend/tests/unit/test_storage_config.py; không đụng shared conftest của KH |
| Domain EvidenceStore adapter/mapping | H1 trong 2.05 | KH/AN | Dự kiến adapters/storage/evidence_store.py; M003 KH viết sau domain mapping |
| Inventory/index metadata needs | KH / H2 theo task gốc | H1/VI | KH giữ migration writer; H2 gửi config/index/chunk invariant |
| Workflow DB wiring | H1 trong 2.13 tiếp nối | KH/VI/AN | composition.py/application, sau foundation/domain evidence; vẫn giữ CLI không DB |

Không thay public contracts hoặc generated types trong 2.20 trừ khi có task/decision
mới; nếu cần H1 là writer, producer/consumer review trước. KH giữ migration sequence
và fixed schema metadata, H1 không tự thêm version files; KH không tự sửa manifest
song song. Nếu cùng sửa storage path, tách đúng files như bảng, không chung writer.

Timebox proposed, không thay backlog: H1 2h checkpoint/interfaces + 4h config/
connection + 4h run/report boundary + 2h verify/handoff; KH 2h reconcile + 4h
migrations + 4h integration + 2h setup/recovery. Nếu 5-table foundation/real recovery
không vừa slice, báo delta và ưu tiên prerequisites trước; re-estimate do nhóm chốt,
không chuyển 2.05/domain data vào 2.20 để làm như đủ 24h. EvidenceStore 8h vẫn riêng.

## 11. Decision register cho checkpoint

| ID | Trạng thái / người quyết định | Recommendation và phần cần chốt |
| --- | --- | --- |
| P0 | Accepted: user; nguồn team guide/brief hiện hành | PostgreSQL engine; không hỏi lại |
| P1 | Accepted 2026-11-03: Nguyễn Tấn Huy xác nhận nhóm thống nhất, nguồn §1 | Sync Core 2.1 + psycopg3 binary + Alembic; PostgreSQL17 test baseline, revalidate/pin tại implementation |
| P2 | Accepted 2026-11-03: nhóm theo xác nhận H1, nguồn §1 | 5-table foundation, text IDs, inline immutable config, defer auth/full design; reconciliation §7 |
| P3 | Proposed; H1/KH chốt cùng P2 trước M003 | Bounded canonical bytea bundle 2 MiB cho 2.05, chưa normalize/full artifact DB; size vượt thì fail rõ, review lại trước production claim |
| P4 | Accepted 2026-11-03: nhóm theo xác nhận H1, nguồn §1; giữ allocation hiện có | H1 manifest/config/connection/ports, KH Table metadata/migrations/shared DB fixture; không hai writer |
| P5 | Pending domain decisions; không chặn minimum foundation | Retrieval backend/config và domain queries; nullable embedding_model conditional/mapping inventory partial trước migrations consumer |

P1/P2/P4 đã được chốt, đủ đầu vào quyết định để bắt đầu H1/KH implementation.
P3 chặn M003/2.05, không
chặn config/connection; P5 chặn index/inventory consumer schema, không buộc chọn
retrieval ngay. Phạm vi thiết kế này chưa cấp quyền triển khai code; prompt sau
cần giao slice implementation cụ thể. Không hỏi lại permission cho việc viết
tài liệu đã giao; đây là nơi nhóm quyết định tooling/schema mới.

## 12. Verification plan — chưa chạy acceptance DB

| Case / expected behavior | Mức / owner | Evidence cần có |
| --- | --- | --- |
| Python3.14 locked install của stack; import/tool version đúng | Real environment H1/KH | uv locked result + versions, OS/arch; chưa coi PyPI metadata là pass |
| Config missing/invalid; DSN chứa secret không xuất lỗi/log | Unit fake H1; real connect failure KH | Expected stable code, captured redacted stderr/log |
| Metadata ID quá byte-size limit/U+0000 | Unit + PostgreSQL H1/KH | Explicit persistence error trước SQL, không truncate hoặc đổi canonical ID |
| Fresh empty DB → M001/M002; đúng PK/FK/checks và Alembic head | PostgreSQL thật KH | Version/server image, migration command/exit, schema introspection |
| M001 populated → M002; data giữ; upgrade lại no-op | PostgreSQL thật KH | Before/after fixture assertions và revision; không drop DB né upgrade |
| Inject lỗi giữa DDL, không còn schema half-applied; không stamp head giả | PostgreSQL thật KH | Version/schema sau rollback và reproduction |
| Connection context đóng, pool timeout hữu hạn, engine dispose | Unit H1 + real KH | No leaked connection/use after close; measured bounded failure |
| Repo/run/snapshot FK sai SHA/hash/cross repo bị reject | PostgreSQL thật KH | Explicit SQL negative tests, rollback và unchanged row counts |
| Failure run giữ null hashes; không có snapshot data giả | Typed + PostgreSQL H1/KH | Failure report reload và constraints |
| Commit/rollback multi-row run/report operation | PostgreSQL thật KH/H1 | Inject error sau insert, assert no partial committed rows |
| Bundle round-trip giữ arrays/identity/path/spans/excerpt | PostgreSQL thật H1/2.05 | Fixture input versus full reloaded bundle; fake tests không thay DB |
| Same-key identical retry no-op; changed data/identity conflict | PostgreSQL thật H1/2.05 | Row count=1, old bytes unchanged, EvidenceConflict |
| Concurrent identical/different writes | Hai DB connections thật KH/H1 | One immutable row; loser no-op/conflict, bounded lock wait |
| Absent khác unavailable/corrupt row; wrong expected identity | Unit + PostgreSQL H1/2.05 | None chỉ absent; explicit errors, không foreign payload |
| Canonical bytea cap/hash/codec corruption, gồm JSON string U+0000 | Unit + PostgreSQL H1/2.05 | Không truncation, exact round-trip supported bundle hoặc deliberate size rejection |
| Report partial có failed stage, inactive stages/null measurements | Typed + PostgreSQL H1/KH | Summary/full artifact tương ứng, không completed từ bundle load |
| File publish fail / DB fail sau publish / ambiguous commit | Controlled filesystem + PostgreSQL H1/KH | DB rollback, orphan/ack loss xử lý như §8, không false success |
| Missing/corrupt artifact hoặc symlink/traversal locator | Filesystem + DB H1/KH | Read failure, digest mismatch; không đọc ngoài artifact root |
| Runtime role không ALTER/DROP/UPDATE immutable bundle | PostgreSQL thật KH | Permission-negative assertions, không dùng owner để giả least privilege |
| Backup+restore DB và immutable artifacts vào isolated restore DB/root | PostgreSQL/tools thật KH | Scoped source/target IDs, commands, restore replay/hash checks |
| Existing non-DB CLI/health/contracts không regression | Backend checks H1/KH | Relevant suite, Ruff/export/type checks theo change; không vô hiệu gates |

DB tests dùng dedicated database có marker/allowlist rõ, không default vào URL
thật của developer. Setup/reset/recovery commands phải explicit target, inspect
identity trước thao tác xóa; không chạy trong checkpoint. KH triển khai test setup
và executable commands rồi cập nhật verified-commands; không ghi lệnh dự kiến là
đã verified. Nếu dùng container cho PostgreSQL test service, không gộp runner/input
execution hoặc coi container là isolation proof; không sửa CI khi task chưa giao.

Recovery drill đề xuất: dừng writes có kiểm soát trong test setup, backup DB và
artifact tree ở cùng quiescent checkpoint, restore vào DB/root mới, xác minh scoped
reports/bundles/hash và failed/partial metadata. Không có RPO/RTO claim khi chưa đo.
Down migration tạo lại cột không khôi phục bytes đã xóa; backup/restore khác transaction
rollback. Destructive downgrade trên dữ liệu không disposable không thuộc phép thử này.

## 13. Brief triển khai tiếp theo

### 13.1. H1 — 2.20-B connection/config/application boundary

**Input:** main mới nhất; P1/P2/P4 được chốt với nguồn; canonical contracts và
KH schema handoff khi tới adapter tests. Giữ 12h H1, không nhận luôn slice KH.

**Scope/files:** H1 cập nhật pyproject/uv.lock bằng package manager theo dependency
đã chốt; storage config/connection/errors + unit tests, application run/report ports,
run metadata adapter khi KH cung cấp Table metadata. `.env.example` placeholders
backend-only và handoff 2.20. Không sửa migration files/schema.py/shared DB fixtures
do KH viết; không chạm contracts/generated types, UI, runner, ORM, retrieval.

**Behavior:** explicit DB config, no import-time connection, finite timeouts,
transaction owner duy nhất; scoped immutable run/report metadata và safe errors;
artifact bytes không vào DB. Có thể implement config/connection trước schema,
nhưng không gọi run persistence acceptance xong khi KH prerequisite chưa có.
Đưa schema request cho KH qua handoff file, không tự gửi tin nhắn bên ngoài.

**Tests/output:** config redaction/validation unit tests, actual connection và
commit/rollback cùng KH fixture, row/metadata round-trip khi schema sẵn; locked
install + relevant lint/backend/contract checks, exact commands/results, pending.
Giữ read-only analyze/health không bắt DB; workflow wiring là 2.13 follow-up.

**Stop conditions:** tooling/schema chưa chốt; KH schema không khớp; nguồn cần
breaking change/auth/extra infrastructure ngoài scope. Tiếp tục phần độc lập đã
đủ input, không tạo fake DB/Migrations để báo hoàn tất. Không commit/push nếu chưa giao.

### 13.2. KH — migration mechanism/integration checks

**Input:** P1/P2/P4 rõ, H1 dependency lock + config/engine contract, mapping §5–7.
Giữ 12h KH. Có thể soạn migration code theo metadata handoff trước connection merge,
nhưng acceptance cần stack thật; không sửa manifest song song với H1.

**Scope/files:** một Alembic environment/head, fixed schema, Table metadata và
M001/M002, storage-local DB fixtures/integration tests/setup-recovery docs. M003+
chỉ sau domain design tương ứng được giao; không dựng full Sprint3/4 tables.
Alembic env lấy migration credential từ backend config, không nhúng DSN vào ini,
không migration-on-web-start/create_all. Autogenerate chỉ candidate phải review,
không giả tự nhận diện mọi CHECK/constraint hoặc migration mất dữ liệu.

**Tests/output:** fresh/upgrade/reapply/failed migration, composite identity FKs,
real transaction/concurrency boundaries, runtime-role permissions, scoped backup/
restore drill. Fixture SQL/rows synthetic có nhãn, không source/fault labels/secret.
Ghi PostgreSQL exact version/image, commands/exit/revisions và file ownership;
gửi H1 schema import names/fields bằng handoff. Reviewer AN vẫn đề xuất/pending.

**Stop conditions:** migration conflict/multiple heads, shared file concurrent
writer, DB target không xác minh dedicated test, scope vượt estimate hoặc thiếu
domain producer metadata. Không drop/stamp/reset DB để che failure, không dùng
SQLite/mock thay acceptance PostgreSQL, không tự đổi grants trên shared DB.

## 14. Kiểm chứng checkpoint và AI disclosure

Đã thực hiện read-only: git status/root/remotes/log, fetch main, đọc source/grep
manifest/lock và tests; trích workbook OOXML + DB/Proposal DOCX; đọc official URLs
ở §3 và PostgreSQL constraints. Không gửi source/code nội bộ tới những URLs đó.
Không cài dependency, kết nối PostgreSQL, chạy migrations/backend tests hoặc
re-run CI trong task docs-only. Các DB test cases §12 là planned, không phải pass.

Kiểm trước bàn giao: local links/anchors/fences, table structure và diff scope;
so hash DOCX/workbook với baseline, source/manifests/generated không đổi. Không
dùng git diff --check một mình để khẳng định untracked Markdown đã được check.

| Kiểm thực tế ngày 2026-11-03, cwd checkout ở §1 | Kết quả / giới hạn |
| --- | --- |
| `git fetch origin main`, `git log -4 --oneline origin/main`, diff HEAD với origin/main trước sửa | Exit 0; d30388f, không source diff tại baseline |
| Python stdlib ZIP/XML đọc workbook, DB/Proposal DOCX | Đã đọc briefs/sections nêu trong §1, không authoring hoặc sửa binary files |
| Python urllib đọc PyPI JSON và official pages §3 | Metadata/version/excerpts quan sát; không install/import tooling hoặc test connection |
| Python stdlib kiểm local links/anchors/fences/table columns/whitespace trên hai Markdown files | Pass, exit 0, có kiểm cả file checkpoint untracked |
| So bytes/hash workbook và DB DOCX với `git show origin/main:<path>` | Trùng baseline; SHA256 workbook 372ca1d3a1d72a510efee1191fe394e01df45e704bb150711496d313e358b45f, DB DOCX 67d987c3abce518ac198babfbe8115a957051d8dfe8513ccd3954ef43e8beed3 |
| `git diff --check`, `git status --short`, explicit changed/untracked path assertion | Pass; chỉ checkpoint mới và decision-register thay đổi, không commit/push |

Không chạy pytest/Ruff/exporter/frontend vì không đổi code/config/contracts;
không lấy 313 tests pass của phiên 2.13 làm kết quả của checkpoint này. D13 trong
decision-register tách engine đã accepted khỏi D06 lịch sử; D14 ghi nhận P1/P2/P4
accepted theo xác nhận H1 sau merge checkpoint, không coi merge tự chốt proposal.

Self-review dùng Coordinator/Backend/Reviewer, rules 00/01/02/03/04/06/12/13,
api-contracts/security-review; spreadsheet skill chỉ đọc workbook. Không gọi
self-review là independent approval. AI: OpenAI Codex hỗ trợ audit, alternatives,
mapping, test matrix và tài liệu; đã đọc Proposal v1.4 Appendix C/D. Người dùng/
nhóm cần review, hiểu và chốt thiết kế; không lấy chữ ký/tỉ lệ lịch sử làm approval
hoặc contribution mới. Không service/process local mới; chỉ Markdown thay đổi.

**Trạng thái bàn giao:** P1/P2/P4 đã được nhóm thống nhất theo xác nhận H1;
implementation 2.20 vẫn chưa bắt đầu. Có thể chuyển sang brief 2.20-B; P3 cần chốt
trước 2.05 và P5 trước consumer migrations tương ứng. Chưa có runtime acceptance,
mentor approval hoặc hoàn thành task/sprint được suy diễn. Lượt ghi nhận quyết định
này chỉ sửa Markdown cục bộ, chưa commit/push.
