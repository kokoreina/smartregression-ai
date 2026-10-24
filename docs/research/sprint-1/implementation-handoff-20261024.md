# Bàn giao implementation Sprint 1 — 2026-10-24

Nguyễn Tấn Huy giao bổ sung phần còn thiếu 1.01–1.11/G1; không làm 1.12 hoặc sửa
review.md. Đây là handoff kỹ thuật mới, không thay kết quả/handoff cũ của thành viên.
Baseline `origin/main` = `7989209`; working tree ban đầu sạch. Branch:
`feat/s1-git-discovery-spike`. Profile: Coordinator, Change Impact, DevOps/Runner,
Backend/Contracts, QA/Research; skills TDD, security-review, evaluation-integrity,
systematic-debugging và api-contracts cho boundary observations nội bộ.
Đã đọc root AGENTS, profile/rules theo routing, verified-commands và template.
Không có AGENTS con áp dụng được tìm thấy. Không có sub-agent.

## Thay đổi và AC

- **1.07 locally verified:** LocalGit direct diff hai commit, add/modify/delete/rename,
  previous_path, cùng SHA, SHA sai/không tồn tại/blob không phải commit, immutable
  blob reads khi working tree bẩn; reject binary source, symlink và path sai.
- **Dependency/symbol spike locally verified:** AST spans, trực tiếp đổi symbol,
  absolute module-import edges; syntax failure rõ và partial import limitations.
- **1.05/G1 locally verified trên fixture:** pinned image, config validation,
  discovery, empty vs collection error, selected test, failure/skip, unknown ID,
  wrong snapshot, timeout/output cap và cleanup. Không là runner production.
- **1.04/1.08 tái sử dụng:** tests mock access và in-memory lifecycle cũ vẫn chạy;
  không tạo implementation song song hoặc thay policy production.

Các file chính: adapters/git_local.py, adapters/bounded_process.py,
adapters/runners/pytest_spike.py, core/impact/python_snapshot.py, ba test files mới,
scripts/g1 và [git-diff-spike](git-diff-spike.md). README/module docs/architecture và
verified-commands cập nhật đúng mức spike. Public models/generated artifacts không đổi.
Worker.py là producer, FixtureWorker là consumer của JSON observations nội bộ;
không export thành AnalysisReport/API schema, không cần migration hay đổi version.
Validation snapshot/IDs/status tại consumer; harness chỉ hỗ trợ fixture do task tạo.

## Bằng chứng mới (cwd D:/smart-regression-ai)

| Lệnh | Kết quả thực | Giới hạn |
| --- | --- | --- |
| `.venv/Scripts/python.exe -m pytest ...test_python_snapshot.py ...test_git_local.py -q -p no:cacheprovider --tb=short` trước implementation | Collection errors vì thiếu modules mới | Red phase; không là lỗi environment |
| `.venv/Scripts/python.exe -m pytest backend/tests/unit/test_spike_runner.py -q -p no:cacheprovider --tb=short` trước implementation | Collection error thiếu runner module | Red phase |
| `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=short` cuối | **49 passed**, 1 Starlette/httpx deprecation warning; exit 0 | Windows/Python 3.14.3, quyền temp phù hợp; không benchmark |
| `.venv/Scripts/ruff.exe check .` | All checks passed, exit 0 | Lint |
| `.venv/Scripts/ruff.exe format --check .` | 117 files formatted, exit 0 | Formatting |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | exit 0 | Schema/demo fixture consistency |
| `docker version --format '{{.Server.Version}}'` | 27.3.1 | Linux engine qua Docker Desktop; sandbox thường bị pipe ACL, dùng quyền tool đã duyệt |
| `docker build --build-arg BASE_IMAGE=python@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2 -t smartregression-g1:python314-pytest911 -f scripts/g1/Dockerfile scripts/g1` | Image build thành công | PyPI tải chậm/resume một lần; chỉ build stage có network |
| `.venv/Scripts/python.exe scripts/g1/run_spike.py --image sha256:3cd7035210103639f0e52d72b96628a9ef22aea527e5b13f346117ee79cf88ad --output var/g1-20261024-release` | **exit 0**, synthetic G1 checks complete | Không chạy candidate/benchmark |
| `docker ps -a --filter name=smartregression-g1- --format '{{.Names}} {{.Status}}'` | Rỗng, exit 0 | Các container fixture đã cleanup |

Artifacts local bị Git ignore: `var/g1-20261024-release/selection.json` và
`observations.json`. Base fixture `a73ec4190527eecf260000f961e73b726cc453bf`, target
`3deb7cc5ef384880fe3fac22cfc96e09ac75f92c`. SHA thay đổi khi tái tạo vì timestamp;
script/selection/observations lưu đúng cặp của mỗi lần chạy. Đây không phải repo thật.

Observation: symbol `add` trực tiếp đổi; edge `tests/test_calc.py → calc.py`;
5 native IDs được collect. Selection frozen_at trước test_add.started_at. Test được
chọn có setup/call/teardown passed. Các case tổng hợp khác: assertion failure exit 1,
skip được nhận diện, empty discovery exit 5, collection error exit 2, wrong snapshot/
unknown ID bị chặn trước dispatch, timeout/output overflow dừng và cleanup.

Worker đo: UID 65534, Seccomp=2, NoNewPrivs=1, interface chỉ lo; memory.max tương
đương 268435456 bytes, pids.max=64, cpu quota/period=100000/100000. Root/source
write probes bị từ chối; Docker inspect xác nhận readonly/network/quota/mounts.
Không stress-test OOM/CPU/PID hoặc chứng minh cách ly arbitrary hostile code.
Image thực tế: Python 3.14.3, pytest 9.1.1, iniconfig 2.3.1, packaging 26.3,
pluggy 1.7.0, pygments 2.21.0. Image ID khóa lần chạy; rebuild transitive chưa hash-lock.

## Debugging, trust và phần chưa kiểm

Những lần thử trước được giữ trong var, không ghi đè: config digest BuildKit không
phải Docker image ID; sửa cách lấy qua inspect. Seccomp thiếu statfs/fstatfs làm
runtime không xác minh procfs; bổ sung hai syscall truy vấn sau diagnostic. Docker
ở máy này dùng cgroup v1; thêm đọc v1/v2 thay vì bỏ kiểm quota. Không fallback host.

Git/source → bounded subprocess + full-SHA/literal-path → snapshot observations;
không chạy hooks/textconv hoặc code đầu vào. Container chỉ mount fixture/worker ro,
không socket, .env hay credentials. Seccomp và snapshot hash là guard cho fixture,
không phải authorization/storage/concurrency boundary production. Unknown statuses
không thành report an toàn. Docker JSON/report validation chỉ hỗ trợ harness này.

Source CI/GitHub checks chưa được khẳng định trước khi PR chạy. Frontend/browser,
external candidate builds/discovery, model/provider/DB và benchmark không chạy.
Không đổi dependency manifests, lockfiles, CI, public contracts hoặc task 1.12.
Không có service/container còn chạy do task; image và artifact local giữ để tái lập.

## Review và tiếp tục

An review Git/semantics, Khánh review runner/config, Phạm Phan Hoàng Huy review
provenance, Việt review reproduction. Python/pytest accepted ở ADR 0002;
PR policy/phiên bản/plugin input production vẫn pending. G1 fixture có evidence,
việc nhóm chấp nhận gate và review độc lập vẫn cần người thật.

Codex hỗ trợ thiết kế spike, code, tests, debugging, tài liệu và self-review theo
brief của Huy. Các thành viên cần hiểu/chỉnh/review phần nhận; không có chữ ký,
phê duyệt mentor hoặc tỷ lệ đóng góp giả. Handoff nghiên cứu riêng sẽ tổng hợp
1.01–1.11; task 1.12 do nhóm làm sau.

Final self-check: links/fences/UTF-8 passed on 20 changed/new Markdown files; credential-pattern check on intended changes passed (not a general secret scanner); task 1.12 unchanged. Git blob stdout is kept separate from diagnostics, with regression coverage. Final full tests: 49 passed in 9.81s.
