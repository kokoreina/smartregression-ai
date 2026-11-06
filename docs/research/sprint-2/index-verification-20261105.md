# Kiểm chứng exclusions và index metadata, phần KH 2.10/W04

Ngày 2026-11-05, baseline main `ee1f7db`, branch
`feat/khanh-task-2.10-index-storage`. Expected/semantics ở
[handoff](../../development/task-2.10-khanh.md). Đây không phải measured retrieval
quality, fault retention hoặc full Sprint acceptance.

Cwd `work/publish-inventory-s2` của checkout Khánh. Python 3.14.5 từ locked venv
`D:\C1.SE26\Repo-Sprint2-Khanh-2.20\.venv\Scripts\python.exe`; Git for Windows.
Không clean-install mới. Default pytest sandbox có ACL temp limitation; focused
diagnostic run dùng plugin ngoài repo, không tính thay default gate.

| Case group | Kỳ vọng trước chạy | Quan sát |
| --- | --- | --- |
| Allow/exclusion, 22 ca | Cho source/tests/docs; chặn forbidden/evaluation/secret/binary/unsafe paths với reason, không excerpt; PASSWORD keyword map không là secret literal | Pass focused |
| Application/files/config/schema + existing publication, 34 ca | Authorized frozen source, full eligible physical scope, exact bytes/hash/config, fail trước publication với exclusions/gaps/bounds, không ready từ building/failed/orphans | Pass focused, tổng 55 |
| PostgreSQL index, 19 ca mới | Real metadata/chunks/files; concurrent attempts, retries, rollback, limited runtime role, tamper, lost-ack/reconciliation, nullable model | 19/19 pass trong cả hai lượt DB |
| Schema upgrade/recovery | Existing populated data giữ nguyên, one head, reflected metadata match, fresh head, backup/restore exact rows + report/evidence/inventory/index artifacts | Đạt ở lượt DB cuối |

Commands đã chạy local: pytest các modules mới/schema/report publication với
external temp fixture: **55 passed**, 26.61s. Ruff check/format và contract exporter
pass tại mốc chuẩn bị; full suite/real DB không suy từ focused result này.
Lượt đầu test-first fail vì chưa có exclusions module; sau implementation 21 ca
allow/exclusion pass. Test fixture wrong-commit ban đầu tự fail khi tạo invalid
dataclass trước boundary; sửa test gửi wrong requested key vào actual verified loader.
Không hạ assertions/skip để che defect.

Sau đó measured pinned sqlparse tree phát hiện false-positive ở keyword map;
synthetic regression fail trước sửa literal pattern, rồi subset policy/publication
**50 passed**, 42.73s. Không echo candidate source hoặc secret values. Policy version
chưa release, vẫn `index-exclusions/1`; marker/credential exclusion cases giữ nguyên.
Metadata/SQL/ready transition không đổi sau lượt focused này.

## Candidate exclusions và budgets

`scripts/index/measure_exclusions.py --candidate-root <cached-verification-root>`
chạy read-only trên hai tree đã chốt ở 2.08/2.09, verify Git blob/tree và snapshot
identity trước phép đo. Không collection/hooks/import input code. Kết quả cuối tại
`var/index-exclusions-candidates-7242bfbdaed94fc5bde8e914541984b6/evidence.json`:

| Candidate/frozen commit | Eligible/total files | Eligible bytes | Exclusions | Max physical line content |
| --- | --- | --- | --- | --- |
| sqlparse `60cdc649726bf1bc4f1b336050560b336da715ec` | 46/93 | 299.219 | 41 unsupported, 6 evaluation-path matches | 177 bytes |
| TinyDB `edff96aeb2616402e9489d46e90a592c05565621` | 32/65 | 228.909 | 33 unsupported | 137 bytes |

Cả hai dưới total index 32 MiB; line content dưới 8 KiB (thêm delimiter vẫn dưới).
Không tạo chunks hoặc chạy search ở phép đo này, không suy quality/recall/performance
SLA hay complete index acceptance. Lượt trước sửa giữ tại
`var/index-exclusions-candidates-c5cc1d47a5b14289a182cf4aadd7841c/evidence.json`.
Mutation probe trước sửa keyword map: bỏ exclusion guard làm 17/21 ca fail, không
setup errors, source files giữ nguyên. Evidence
`var/exclusion-mutation-5bcf961d75be4df2892ecb6f9b0c3a13/evidence.json`.

Operator reproduction:

```powershell
& scripts/index/verify.ps1 -PythonExe <locked-backend-python>
```

Full gate PowerShell thường trước sửa keyword-map policy: **771 passed, 113 skipped**,
một existing Starlette/httpx warning, 170.96s; Ruff/format/exporter pass. 113 skips
gồm 112 PostgreSQL opt-in và một POSIX FIFO. Sau đó DB thực: 107 passed, 2 existing
candidate-to-DB skips và 3 errors, 54.01s. Đã đọc JUnit: cả 19 index cases pass;
ba errors ở Git object writes của old workflow fixture vì MAX_PATH. Không đổi
assertions hoặc skip các ca đó; rút ngắn harness basetemp dưới invocation-owned
`var/x-<uuid>/t` rồi chạy lại DB riêng. Evidence lỗi giữ tại
`var/storage-verification-010898acf8bb43b59ffea9dc08b9880b/evidence.json`.
Full-script lượt này failed, không dùng source gate pass để suy toàn runtime pass.
Default suite chưa rerun sau keyword-map regression; final focused subset đã pass,
source CI trên commit push là kiểm chứng riêng khi quan sát được.

DB cuối: **110 passed, 2 skipped**, 0 failures/errors. Hai skips là existing
candidate-to-DB checks đòi inventory candidate harness; không skip ca index mới.
Đã đọc trực tiếp `evidence.json` và 112 testcase JUnit tại
`var/storage-verification-64469f41234143fd8eff707910a35b86/`:
`postgresql_pytest_exit=0`, `fresh_head=true`, `revision_head=20261105_05`,
`backup_restore_exact_rows=true`, `index_metadata_chunks_artifact_restore=true`,
`evidence_restore_decode_and_identity=true`, artifact catalog và owned-container
cleanup đều true; `passed=true`.

PostgreSQL 17.11, pinned linux_amd64 image
`postgres@sha256:0b81cec82228160abfa753aeaad0609b709eb26eeb950f2e404ad2326e1cc370`.
Dump SHA-256 `8efed93dc3d7a4da96474bd1ab917fecc06e4d0f813f85f8a93d702d7be243e5`.
Lượt cuối kết thúc `2026-11-05T15:05:34Z`, tức 22:05 giờ Việt Nam. Recovery là
quiescent synthetic fixture, không live backup SLA hoặc arbitrarily shared DB.
Harness không dùng shared DB hoặc credentials sẵn có; artifacts/password không commit.
Index Git/recovery source là task-owned fixture; H2 chunker/search và H1 full workflow
chưa được benchmark hoặc nghiệm thu bằng lượt KH này.

OpenAI Codex hỗ trợ code/tests/verification/docs; actual human review chưa xác nhận.
