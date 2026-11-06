# Task 2.19 — Inventory/runner integrity regressions

Ngày 2026-11-05, Trần Hùng Khánh. Baseline main
`ee1f7db2e47d5857ef2a0af65cd01be8148fc000`; nhánh
`feat/khanh-task-2.19-integrity-regressions`. Đây là phần KH 4h trong
[brief 2.19](sprint-2-team-guide.md#task-219); phần identity/evidence của
[Đỗ Hà An](task-2.19-an.md) đã merge qua PR #45.
Code và kiểm chứng phần KH đã hoàn tất, sẵn sàng review.
Reviewer được phân công: Đặng Đại Việt; review thực tế chưa xác nhận.

## Phạm vi và luồng kiểm tra

26 ca mới trong
[test_inventory_runner_integrity.py](../../backend/tests/integration/test_inventory_runner_integrity.py)
chạy Git fixture hai commit, authorized acquisition, actual fixture collector/worker,
discovery validation, analysis, publication và đọc lại report. Report đã đọc lại
được chuyển thành frozen inventory write, qua consumer guard và fixture dispatch.
Base có test bị xóa ở target; dirty working tree được giữ nguyên và không thay
committed source. Dùng lại exact-byte fixtures 2.08/2.09, không tạo hoặc sửa tests
cho candidate repo, không dùng outcome/fault labels làm input selection.

Mặc định chỉ thay Docker transport bằng double có nhãn. Git, snapshot/diff/graph,
collector, worker controller, validation, filesystem publication và reader là thật.
Opt-in script chạy cùng assertions qua Docker Linux thật, kiểm remove đúng tên
container sau mỗi invocation. SQL vẫn là recording port, không giả transaction
hoặc acceptance PostgreSQL. Ba ca corruption chủ động sửa kết quả sau collector
để mô phỏng lỗi tại application boundary, kể cả ở chế độ Docker.

| Nhóm ca | Số ca | Kỳ vọng đặt trước |
| --- | --- | --- |
| Discovery và report round-trip | 12 | Phân biệt completed nonempty, completed empty, partial, failed, timeout, output limit, duplicate IDs, plugin error, missing/extra worker frame, unsupported ID và exact native IDs |
| Unknown target ID | 5 | ID lạ, ID chỉ còn ở base, chuỗi giống option và ID bị thêm khoảng trắng đều bị chặn trước bất kỳ Docker command; ID đúng vẫn dispatch được |
| Materialization bị sửa | 1 | Digest cũ không cho chạy source đã đổi, không gọi Docker |
| Frozen inventory sai scope/config | 5 | Sai repo, run, target SHA, snapshot hoặc configuration bị chặn; không gọi Docker |
| Corruption tại collector boundary | 3 | Sai identity, partial bị gắn nhãn complete và lỗi hạ tầng giữ failed/error tới report đã đọc lại và consumer guard |

Mọi ca discovery còn kiểm stage summary chuyển tới storage port, identity/target,
CLI report validation, analysis exit code, cleanup thư mục materialize và trạng thái
Git đầu vào. Report hợp schema có thể mang analysis exit 2; validator exit 0 không
đồng nghĩa phân tích thành công. Completed empty cũng chỉ trả tập IDs rỗng, không
là kết luận an toàn. Positive dispatch chạy đúng fixture cố ý raise trong Docker,
ghi `test_failed`; đây không là fault label hay benchmark.

## Chạy lại

Tại root checkout, dùng Python đã sync theo lockfile:

```powershell
$env:PYTHONPATH = (Resolve-Path backend/src).Path
python -m pytest backend/tests/integration/test_inventory_runner_integrity.py -q
& scripts/integrity/verify.ps1 -PythonExe <locked-backend-python>
```

[verify.ps1](../../scripts/integrity/verify.ps1) gọi
[verify.py](../../scripts/integrity/verify.py): full suite mặc định, Ruff, format,
contract exporter; build image fixture hiện có từ pinned Python base; lấy local
image digest rồi chạy 26 ca Docker. `-RuntimeOnly` chỉ chạy runtime sau checks,
không thay full suite. Không đổi security profile, worker/image dependencies hoặc
production composition. Environment opt-in chỉ được đặt cho tiến trình con.

Output mỗi lượt mới tại `var/i-<uuid>/`: `evidence.json`, log commands, JUnit,
Git fixture, report và `observation.json` từng ca. Workspace Docker ở `w/`, tách
khỏi thư mục pytest 0700 để Docker Desktop đọc được trên Windows. Giữ tên ngắn
để tránh MAX_PATH khi Git tạo template hooks; không đổi quyền toàn máy hoặc nới
isolation. Các artifacts này được ignore, không commit. Raw Docker error nếu có
chỉ lưu giới hạn tại `docker-error.log` của fixture cục bộ.

## Kết quả và giới hạn

Full suite PowerShell thường: **748 passed, 94 skipped**, một existing
Starlette/httpx warning; Ruff check, format 259 files và exporter pass. Skip gồm
93 PostgreSQL opt-in và một POSIX FIFO trên Windows. Lượt full gate kết thúc
failed do runtime fixture path, không được ghi thành toàn script pass.

Sau sửa test workspace: 26 ca transport-double pass trong sandbox với external
temp fixture chẩn đoán; đây không thay default gate. Một ca real-Docker success
đã pass; **26/26 ca runtime Docker thật pass**, 82.99s, không failures/errors,
26 observations và cleanup đạt. Kết quả cuối ghi ở
[verification record](../research/sprint-2/integrity-verification-20261105.md).

Full suite mặc định là lượt trước sửa test paths/diagnostics; sau sửa chỉ chạy lại
focused suite và runtime trên đúng source cuối. Không claim default suite đã chạy
lại sau sửa harness. Production bytes giữ nguyên; source CI sẽ chạy default suite
trên commit được push. Không chạy lại DB/frontend vì không đổi các module đó.

Mutation probe riêng, không sửa source production: bỏ membership guard làm 5 ca
unknown-ID fail vì lỗi muộn `invalid_worker_result` thay vì chặn trước dispatch;
bỏ scope/completeness guard làm 14 ca fail `DID NOT RAISE`, không có setup error.
Các mutation không được đưa vào branch. Production source không cần sửa cho AC này.

Phần AN có 24 ca identity/evidence/stale-index/partial-analysis; kết hợp với 26 ca
KH tạo 50 ca 2.19 có scope riêng, không cộng lại các unit tests cũ. Full suite mới
chạy lại cả phần AN và các integration source/evidence đã merge. Không tuyên bố
mọi stage đã nối trong CLI: impact/retrieval/evidence/ordering vẫn theo workflow
hiện hành. Campaign A01–A07/W09 trong
[ADR 0004](../architecture/decisions/0004-sprint-2-integration-decisions.md#6-demo-và-acceptance)
còn đòi hỏi workflow/DB/browser và review của owners; task tests này không tự đóng
whole-sprint acceptance. Không sửa contract/OpenAPI/types, migrations/DB schema,
manifest/lockfile, CI hoặc UI.

OpenAI Codex hỗ trợ đọc repo, thiết kế/viết tests, chẩn đoán và tài liệu. Đã đối
chiếu Proposal v1.4 Appendix C/D; self-review không thay review độc lập. Nhóm giữ
trách nhiệm đọc, hiểu và xác minh, không ghi approval hoặc tỷ lệ đóng góp giả.
