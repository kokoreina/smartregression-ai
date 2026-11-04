# PostgreSQL foundation task 2.20

PostgreSQL và P1/P2/P4 đã được nhóm chốt; nguồn tại
[checkpoint](../../../../../docs/development/task-2.20-checkpoint.md) và
[decision register](../../../../../docs/development/decision-register.md).
Stack synchronous SQLAlchemy Core + psycopg binary; Alembic thuộc dev dependencies
dành cho migration operator. Đã có schema 5 bảng, hai migrations và adapter run/report.
User giao KH hoàn thiện adapter sau phần schema; xem
[bàn giao adapter](../../../../../docs/development/task-2.20-adapter.md).

- `schema`: Core Table objects repositories/snapshots/analysis_runs/artifacts/run_reports.
- `run_store.PostgresRunReportStore`: một transaction ghi immutable metadata; exact
  retry no-op, khác nội dung conflict. `BoundRunReportStore` dùng transaction caller.
- `report_publication.ReportFiles` và `application.persistence.persist_report`:
  publish file nguyên vẹn trước DB, giữ file khi DB lỗi/ack không rõ; read kiểm
  digest/size/report identity. Root artifact được cấp rõ, không links/junctions.

- `config.load_database_settings`: explicit backend configuration, runtime/migration
  credential riêng. Remote mặc định `sslmode=verify-full`; chỉ hỗ trợ query `sslmode`
  và `sslrootcert`. Plaintext chỉ khi caller bật `allow_loopback_test=True` và host
  chính xác `localhost`, `127.0.0.1` hoặc `::1` cho dedicated test DB.
- `connection.database_engine`: lazy engine trong context có disposal, pool 2,
  overflow 0, pool wait 5s, pre-ping. Connect timeout default 5s; statement 10000ms;
  lock 3000ms. Query không được override các giới hạn này.
- `connection.database_transaction`: `Engine.begin()` commit/rollback ownership,
  translate driver/SQLAlchemy errors thành `RunStorageError`; không tự retry.
  Adapter dùng bound connection không được tự commit/rollback.
- Logger SQLAlchemy engine/pool có tên `smartregression_storage` bị tắt có chủ ý:
  pool DEBUG có thể lộ raw driver exception dù `hide_parameters=True`. Boundary
  trả stable safe codes; không log URL hoặc dùng exception locals để xuất diagnostics.
  Psycopg diagnostics bị lọc trong storage context bằng ContextVar, không thay policy
  của thread/context khác; version upgrade phải rà lại logger names của driver.

Không mở connection khi import; không migration-on-startup/create_all, không SQLite
fallback. Existing analyze/health chưa dùng DB và vẫn chạy không DB settings.
Application port/preparation ở `application/run_store.py` không import DB libraries.
Report bytes nằm ngoài DB; descriptor/supplied bytes không chứng minh file đã publish
hoặc caller có quyền repository. Không suy completed từ metadata/bundle.

KH sở hữu schema/migrations/DB fixtures và đã nhận bàn giao phần adapter từ H1 theo
user. PostgreSQL thật đạt 40 tests, gồm adapter/recovery; task handoff tách bằng chứng
local khỏi CI/human acceptance. Vector backend, EvidenceBundle 2.05, inventory
domain persistence, workflow default DB wiring và history catalog reader còn riêng.
Lịch sử phần H1 ban đầu:
[handoff 2.20-B](../../../../../docs/development/task-2.20-b.md).
