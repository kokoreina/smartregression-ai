# Kiểm chứng task 2.19, phần inventory/runner

Ngày 2026-11-05. Scope/expected trước quan sát ở
[task handoff](../../development/task-2.19-khanh.md). Baseline main `ee1f7db`.
Cwd: checkout `work/publish-inventory-s2` của task Khánh; Python
`D:\C1.SE26\Repo-Sprint2-Khanh-2.20\.venv\Scripts\python.exe` (3.14.5), Git for
Windows, Docker Desktop Linux. Không clean-install dependencies trong lượt này.

## Commands và bằng chứng

```powershell
& scripts/integrity/verify.ps1 -PythonExe <locked-backend-python>
& scripts/integrity/verify.ps1 -PythonExe <locked-backend-python> -RuntimeOnly
```

| Lượt | Quan sát thật | Artifact local, không commit |
| --- | --- | --- |
| Full gate | Pytest 748 passed/94 skipped, 1 warning, 142.57s; Ruff/exporter pass; Docker runtime 26 failed ở git init trước worker | `var/integrity-verification-4defbc3c381e4ea783f82482bb07013f/evidence.json` và logs |
| Runtime sau rút ngắn đường dẫn | 20 failed/6 passed, 38.88s; Docker CreateFile Access is denied dưới pytest temp 0700 | `var/i-386f00d2f082457e930abd8854100207/evidence.json` |
| Probe một ca sau tách workspace | 1 passed/25 deselected, 2.86s, worker Docker thật | Local `var/p-*` probe, không thay whole runtime gate |
| Mutation guard | 5 failures khi bỏ membership; 14 failures khi bỏ scope/completeness, không setup errors | `var/integrity-mutation-085a46c821e44df7825d68c01a79e05a/evidence.json` và JUnit/logs |
| Runtime cuối sau tách workspace | **26 passed**, 82.99s, 0 failure/error/skip, 26 observations; đúng source hashes, materialization/container cleanup đạt | `var/i-14b5f9f71b4d47d2bae53d4dbebb9a02/evidence.json`, `runtime.xml`, `docker-integrity.log`, `w/*/observation.json` |

Giữ cả failed runs. Git path probe tái hiện `Filename too long` khi source root
dài 233 ký tự, đường ngắn 216 ký tự init thành công. Docker error probe xác định
daemon không đọc được materialization dưới pytest private temp; đổi sang thư mục
`w/<uuid>` do harness tạo với quyền kế thừa. Probe script ban đầu thiếu tạo parent
basetemp và fail setup; đã sửa, không tính lượt đó là runtime pass.

Đã đọc trực tiếp evidence cuối `passed:true`, 26 testcase JUnit, observations và
đối chiếu hash source. Image ID:
`sha256:582fdd71b5795514c7aa17cda9963f42c3f0a9c2c2db0156cb1f578f116b3033`.
Runtime kết thúc `2026-11-05T14:09:44Z` (21:09 giờ Việt Nam).
Source/runtime production không đổi trong các sửa test path và diagnostics.
Full suite mặc định ở lượt đầu; sau sửa harness chỉ focused/runtime được chạy lại,
không đổi counts lịch sử thành kết quả default suite trên source cuối. Source CI
trên commit push là kiểm chứng bổ sung riêng, chưa dùng kết quả CI chưa quan sát.

## Ranh giới kết luận

Default suite dùng Docker transport double có nhãn; opt-in dùng actual worker,
isolation checks, timeout/output cap và kiểm xóa đúng container. Corruption injection
là fixture tại boundary; SQL chỉ recording port. Không chạy PostgreSQL, candidate
benchmark, UI browser hoặc research metrics mới. 94 skips giữ điều kiện gốc,
không bỏ/hạ gate. `test_failed` của positive dispatch là fixture cố ý raise,
không chứng minh phát hiện fault hoặc production isolation.

Partial reports giữ các producers chưa nối. Kết quả task này bổ sung 2.19/AC
inventory-runner, không thay acceptance A01–A07 của toàn Sprint 2 hoặc reviewer VI.
OpenAI Codex hỗ trợ tests/debug/docs; cần human review theo phân công nhóm.
