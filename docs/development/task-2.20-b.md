# Task 2.20-B — H1 PostgreSQL connection và application boundary

## Trạng thái và nguồn

Ngày triển khai: 2026-11-03. **Phần độc lập H1 đã triển khai cục bộ; durable
run/report adapter và PostgreSQL acceptance còn pending KH schema/fixtures.**
Không đóng task 2.20 hoặc Sprint 2 từ kết quả này.

- Brief user giao implementation H1 theo [checkpoint §13.1](task-2.20-checkpoint.md#131-h1--220-b-connectionconfigapplication-boundary).
- P0/PostgreSQL, P1/Core + psycopg binary + Alembic, P2/five-table foundation và
  P4/writer boundaries đã accepted theo xác nhận H1 ngày 2026-11-03. Nguồn:
  [decision register D13/D14](decision-register.md), [checkpoint](task-2.20-checkpoint.md).
- P3/bundle policy và P5/retrieval vẫn riêng/pending; không triển khai 2.05.
- `git fetch origin main` exit 0; HEAD và origin/main cùng
  `321c1cbc816f56ed5d50345a69e8314e1129fb2b`. Chỉ đối chiếu main, không đọc open PRs.
- Checkout: `D:\smart-regression-ai\var\main-review-20261103`, branch
  `docs/sprint-2-2.20-decisions`. Phiên implementation chưa commit/push, không tạo
  branch mới. Sau bàn giao, user giao commit/push và mở PR để tự review/merge;
  quyền publish này không đóng task 2.20 hoặc tự approve/merge.
- Hai file decision-register/checkpoint đã có thay đổi chưa commit trước phiên này;
  giữ phần accepted P1/P2/P4 và bổ sung liên kết trạng thái implementation.
  Checkout gốc cùng `outputs/`, `start-cliproxy-management.bat` không bị sửa.

Đã đọc root AGENTS và routing phù hợp; không thấy AGENTS con trong checkout.
Profile: Backend/Contracts, Coordinator, Reviewer cho self-review. Rules:
00/01/02/03/04/05/06/07/12/13/14. Skills: test-driven-development, api-contracts,
security-review, systematic-debugging khi tái hiện lỗi. Không chạy sub-agent hoặc
gửi tin nhắn bên ngoài thay KH/AN.

## Thay đổi và contract impact

| File | Behavior / ownership |
| --- | --- |
| `pyproject.toml`, `uv.lock` | H1 thêm runtime SQLAlchemy/psycopg binary, Alembic trong dev group; uv sinh lock |
| `adapters/storage/config.py` | Explicit settings, URL/TLS/timeout validation, role selection, repr không chứa URL |
| `adapters/storage/connection.py` | Lazy owned engine, bounded pool, context transaction, safe infrastructure errors/logging |
| `adapters/storage/errors.py` | Stable `database_configuration_invalid`, không echo input |
| `application/run_store.py` | Typed config/artifact/metadata, preparation validation, save-only `RunReportStore` port |
| Unit tests `test_database_config.py`, `test_database_connection.py`, `test_run_store.py` | Config/lifecycle/driver double, metadata consistency và non-DB regression |
| `.env.example`, storage README, handoff/verified commands | Placeholder configuration, limitations và KH inputs |

Paths code/tests ở dưới `backend/src/smartregression/` và `backend/tests/unit/`.
Không thay canonical v1/v2 contracts, EvidenceStore, generated files, API/CLI,
composition workflow, frontend, schema/migrations, shared conftest hoặc CI.
Application/core không import SQLAlchemy/psycopg; test subprocess kiểm application
import không nạp hai libraries. Không tạo MemoryStore/fake adapter để báo persistence.

Dependency resolve thực: SQLAlchemy **2.1.6**, psycopg/psycopg-binary **3.3.7**,
Alembic **1.20.1**. Python **3.14.3**, uv **0.12.23**, Windows amd64. Revalidated
PyPI metadata trước resolve; locked sync cài mới 32 packages trong virtualenv riêng
`D:\smart-regression-ai\var\task-2.20-b-venv`. Không đổi Python/runtime hoặc upgrade
packages cũ ngoài scope; lock diff thêm các dependencies/transitives cần thiết.
Alembic executable chạy được không có nghĩa migrations đã tồn tại/chạy thành công.

## Configuration và lifecycle

Chỉ gọi `load_database_settings()` khi composition thực sự cần DB. Hàm không tự
đọc `.env`, mở network hoặc fallback sang SQLite. Existing analyze/health không
gọi DB config; kể cả DB URL invalid cũng không ảnh hưởng luồng non-DB hiện tại.

| Input | Behavior đã triển khai |
| --- | --- |
| `SMARTREGRESSION_DATABASE_URL` | Bắt buộc khi explicit runtime DB settings được load |
| `SMARTREGRESSION_MIGRATION_DATABASE_URL` | Chỉ đọc khi caller dùng `migration=True`; không fallback qua lại |
| `SMARTREGRESSION_DB_CONNECT_TIMEOUT_SECONDS` | Default 5; integer 1–30 |
| `SMARTREGRESSION_DB_STATEMENT_TIMEOUT_MS` | Default 10000; integer 100–60000 |
| `SMARTREGRESSION_DB_LOCK_TIMEOUT_MS` | Default 3000; >0 và <= statement timeout |

Dialect bắt buộc `postgresql+psycopg`; host/database/user nonempty. Chặn control
characters, host nhiều đích/socket và database name có cú pháp libpq connection
options/URI. Dùng URL parser của tooling; query chỉ cho `sslmode`, `sslrootcert`.
Unknown/duplicate/empty query values bị reject, không bỏ qua option malformed.
Không cho host/service/options/timeout query ghi đè validated settings.

Remote mặc định `sslmode=verify-full`; có thể cung cấp CA path trong `sslrootcert`.
Client certificates/Unix sockets/multi-host URLs chưa hỗ trợ. Plaintext chỉ khi
caller explicit `allow_loopback_test=True`, host chính xác localhost/127.0.0.1/::1
và URL có `sslmode=disable`. Đây không phải env switch để hạ TLS production.
Không tự load migration credentials hoặc tạo/grant role; permissions vẫn cần KH
kiểm chứng trên DB thật. `.env.example` chỉ chứa placeholders.

```python
from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine, database_transaction

# Infrastructure usage example; không tự chạy và không nối vào CLI hiện tại.
with database_engine(load_database_settings()) as engine:
    with database_transaction(engine) as connection:
        # Future adapter executes parameterized Core statements on this connection.
        pass
```

Một engine owner trong command/process, dispose khi ra context; pool size 2,
max_overflow 0, pool_timeout 5s, pre_ping. Timeout connect và server statement/lock
options được truyền tới psycopg; unit test đi qua SQLAlchemy tới driver double.
`database_transaction` dùng `Engine.begin()`: commit một lần khi success, rollback
khi exception. Bound adapter không tự commit/rollback; không automatic retry.
Connection loss/ambiguous commit là `RunStorageError`, không báo success hoặc tự xóa file.

Errors: `DatabaseConfigurationError.code=database_configuration_invalid`,
`RunStorageError.code=run_storage_failed`, `RunConflict.code=run_storage_conflict`,
`RunMetadataError.code=run_metadata_invalid`. Lỗi infrastructure/parser được surface
bằng safe messages, suppress raw exception chain; không log DSN/SQL/params.
Business exceptions ngoài DB vẫn propagate sau rollback.

Đã tái hiện pool DEBUG leak raw driver text dù hide_parameters bật. Dedicated
SQLAlchemy engine/pool loggers `smartregression_storage` bị tắt; psycopg loggers
được lọc trong storage execution context bằng ContextVar. Context khác giữ policy
cũ; khi upgrade driver phải kiểm lại logger names. Không xuất exception locals/URL
object ra diagnostics. Các SQL của future adapters vẫn phải parameterized.

## Application input và KH handoff

`prepare_run_report(...) -> RunReportWrite` nhận:

- Validated `StageAnalysisReport` v2, revalidate nested mutable collections.
- `RunConfiguration`: actual application version hoặc None, SnapshotLimits,
  actual Python source limit, explicit producer versions hoặc None, target-import
  graph policy và direct-two-tree mode. Không nhận arbitrary secret/source dictionaries.
- `snapshot_manifests`: tuple từ trusted acquisition, cung cấp actual manifest và
  materializer versions. Mọi known snapshot của run phải có matching manifest;
  foreign/missing/conflicting metadata bị reject. Null-hash failure side không tạo row giả.
- `ReportArtifact`: ID, backend-relative storage key, SHA256 và byte size.
- `published_report_bytes`: supplied bytes phải parse thành cùng report và khớp
  exact digest/size của descriptor. Không giữ report bytes trong returned metadata.

`RunReportWrite` chứa canonical identity, report ID/data kind, immutable config JSON
bytes/hash, tuple snapshot metadata, artifact reference, analysis status, 8-stage
summary JSON bytes và nullable measurements. Metadata IDs giới hạn 512 UTF-8 bytes,
không U+0000; không đổi canonical Text hoặc cap native test IDs. Config <=64KiB,
summary <=256KiB; không truncate/drop limitations. Summary không có stage data.

Prepared values không chứng minh file đã publish, snapshot bytes đúng hoặc repository
đã được authorize. Caller phải xác minh các điều đó. Không tự provision repository
từ report input; schema/repository binding không phải multi-user authorization.
Full report read/digest/path verification và publication orchestration còn riêng.

`RunReportStore.save(write)` là port **chưa có SQL implementation**. Scope key
repo/run/report; exact retry no-op, immutable mismatch conflict, unavailable không
trả success. Save-only đáp ứng upcoming writer; chưa tạo history/read API chưa có
consumer. Port không enforce DB constraints/concurrency và không giả đã persistence.

KH cần bàn giao trước adapter:

1. Table metadata import path/symbols chính thức cho 5 tables theo checkpoint §5;
   fixed schema `smartregression`, scoped keys/FKs/checks và một Alembic head.
2. Migration environment/revisions M001/M002 thực tế; không dùng tên phase làm
   Alembic revision ID. KH giữ writer duy nhất, không sửa manifest song song H1.
3. Dedicated test DB identity/fixtures, runtime role và migration role tách quyền;
   PostgreSQL 17.x exact patch/image evidence, setup/teardown không trỏ shared DB.
4. Fixtures/commands cho fresh/upgrade/failure/recovery và connection transactions.
   KH dùng config loader với migration=True cho owner; runtime dùng mặc định.

Sau handoff, H1 dùng KH Tables cho run/report adapter: scoped immutable
prerequisites/catalog/summary trong một transaction, conflict/retry/concurrency,
metadata round-trip, wrong repo/SHA/hash và permission negative cases. Không
khai báo schema song song; bound connection không tự commit. Full report file
publication phải theo checkpoint §8 khi task integration tương ứng được giao.

## Kiểm chứng thực tế

Cwd các lệnh dưới: checkout ở trên. `$taskPython` là
`D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe`, `$taskRuff` cùng
Scripts/ruff.exe, `$taskUv` là `D:/smart-regression-ai/.tools/bin/uv.exe`.
Đây là ký hiệu mô tả lệnh đã chạy, không phải yêu cầu phụ thuộc tool path cá nhân.

| Command/check ngày 2026-11-03 | Kết quả thực / giới hạn |
| --- | --- |
| `git fetch origin main`, `git rev-parse origin/main`, diff HEAD/main | Exit 0; baseline 321c1cb, không source drift trước task |
| Python urllib PyPI JSON cho SQLAlchemy/psycopg/Alembic | Exit 0; versions/Python support nêu trên, không gửi source nội bộ |
| `uv add --no-sync` runtime packages; `uv add --dev --no-sync` Alembic | Exit 0; manifest và lock do uv sinh |
| `uv sync --locked --python D:/smart-regression-ai/.venv/Scripts/python.exe` với `UV_PROJECT_ENVIRONMENT=D:/smart-regression-ai/var/task-2.20-b-venv` | Exit 0; venv mới, 32 packages installed; dùng cache/network, không phải cache-cold/Linux proof |
| `uv lock --check --offline`; `uv sync --locked --offline` cùng task env/cache | Exit 0; manifest/lock nhất quán, environment đã có packages |
| Import/version SQLAlchemy/psycopg/Alembic; `alembic --version` | Exit 0; 2.1.6/3.3.7/1.20.1; chưa chạy migration |
| Focused pytest trước implementation | Fail do config module/metadata symbols chưa có; không claim pass |
| Regression URL empty-query, DB-name option injection, DEBUG driver/pool diagnostics | Fail tái hiện trước sửa; pass trong focused suite sau sửa |
| `python -m pytest backend/tests/unit/test_database_config.py backend/tests/unit/test_database_connection.py backend/tests/unit/test_run_store.py -q -p no:cacheprovider --tb=short` | 69 passed trước test context-reset cuối; final suite có toàn bộ 70 cases mới |
| `ruff check .`; `ruff format --check .` | Exit 0; 172 Python files formatted tại lần chạy final |
| `python scripts/export_contracts.py --check` | Exit 0, generated artifacts không đổi |
| Demo với DB URLs invalid: `python scripts/demo_analysis.py --output D:/smart-regression-ai/var/task-2.20-b-demo-1` | Exit 0; thin=1/failure=2/empty=1; fixture DEMO, analysis incomplete |
| `docker version --format '{{.Server.Version}}'` | Exit 1; Docker Linux engine pipe chưa tồn tại, không có DB service được xác minh |
| `python -m pytest backend/tests -q -p no:cacheprovider --tb=short --basetemp D:/smart-regression-ai/var/task-2.20-b-pytest-final` | Exit 0; **383 passed, 1 skipped, 1 warning**, 68.61s; gồm 70 test cases mới |
| `git diff --check`; explicit local Markdown links/fences/whitespace và scope assertions | Exit 0; có kiểm tra file untracked; không sửa files của KH/generated/frontend/CI |

Pytest dùng Python 3.14.3/task venv, `PYTHONDONTWRITEBYTECODE=1`, MinGit 2.56.0 từ
`D:/smart-regression-ai/var/task-2.13-tools/mingit/cmd` ở đầu PATH để giữ
`--no-lazy-fetch` protection. Basetemp riêng dưới var; không sửa Git hệ thống.

Chưa chạy PostgreSQL connect/commit/rollback thật, schema migrations, runtime-role
permissions, metadata DB round-trip/concurrency/backup-restore. Docker chưa sẵn và
KH schema/shared fixtures chưa có trên fetched main. Không thay DB acceptance bằng
driver doubles. Chưa kiểm Linux/macOS/remote TLS deployment, GitHub CI cho diff này,
human approval. Không chạy frontend vì không đổi contract/frontend. Không bỏ test
hoặc giảm gate để che lỗi; existing warning Starlette/httpx và Windows POSIX FIFO
skip được báo riêng, không sửa dependencies ngoài scope.

## Tiếp tục và AI disclosure

H1 đã làm xong phần độc lập có thể kiểm chứng local. Bước tiếp theo là KH bàn giao
schema/migrations/dedicated DB fixtures, sau đó H1 triển khai adapter và cùng chạy
PostgreSQL acceptance. 2.13 wiring và 2.05 EvidenceStore còn nhiệm vụ riêng; P3/P5
không được tự chốt. Reviewer AN vẫn là đề xuất, chưa có independent approval.

OpenAI Codex hỗ trợ implementation, tests, debugging, docs và self-review; không
khởi chạy agent song song. Đối chiếu chính sách Proposal v1.4 Appendix C/D từ nguồn
đã đọc trong checkpoint: sinh viên phải đọc/hiểu/kiểm chứng phần AI hỗ trợ; chữ ký
lịch sử không approve thay đổi mới. Không bịa contribution ratio hoặc mentor approval.
Không khởi chạy service, container hoặc background worker mới. Local task venv,
pytest basetemps và demo artifacts giữ dưới var/ bị ignore; không tự xóa dữ liệu cũ.
