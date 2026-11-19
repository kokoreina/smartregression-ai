# Task 3.48 — Tính tỷ lệ và phạm vi ảnh hưởng

Ngày bàn giao: **19/11/2026**. Owner: Đỗ Hà An. Baseline `effd115` (sau PR #70).
Worktree cá nhân: `feat/an-task-3.46-ownership`; giữ các file task 3.46 riêng, không
gán các thay đổi ownership cho task này. Chưa commit/push/PR, không sửa main.

## Đầu ra

**Đã hoàn thiện implementation và kiểm chứng cục bộ trong phạm vi 3.48; sẵn sàng
review.** Không phải phê duyệt nghiệm thu toàn Sprint 3 hoặc bảo đảm phân tích tĩnh
chính xác tuyệt đối. Reviewer đề xuất theo workbook: Trần Hưng Khánh, chưa approval.

Workbook yêu cầu unique files analyzed/changed/direct/indirect/unknown; changed
không bị đếm vào dependent, direct ưu tiên indirect, thiếu/zero mẫu số là N/A và
không diễn giải tỷ lệ thành xác suất lỗi. Phụ thuộc: 3.21, đầu ra graph có sẵn.

## Quy tắc đo đã kiểm chứng

Gọi A là tập file đọc được cú pháp trong snapshot, C là tập file được chọn thay đổi:

- Mẫu số N = số phần tử duy nhất của A, không phải số node hoặc file đang hiện trên canvas.
- Changed đo được = C giao A. File thuộc snapshot nhưng ngoài A được báo riêng qua
  `unknown_changed_count`; chọn đường dẫn không thuộc snapshot bị từ chối.
- Direct: file phụ thuộc cách C một cạnh import. Indirect: file có khoảng cách ngắn
  nhất lớn hơn một. C, direct, indirect không trùng; đường trực tiếp được ưu tiên.
- Counts tính trên A; potential là hợp của ba nhóm đã đo được. Tỷ lệ = count/N ×100,
  làm tròn hai chữ số thập phân. Không cộng các tỷ lệ đã làm tròn để suy tổng.
- N=0 được producer chuẩn hóa thành denominator=null, percentages=null (N/A).
  C rỗng nhưng N đã biết cho kết quả 0% thật, không phải unknown.
- Giới hạn 150 node/đường trên màn hình không làm giảm totals của snapshot.

Đây là quan hệ import tĩnh trong phạm vi parser, không phải runtime call trace,
không chứng minh hành vi bị thay đổi hoặc xác suất gây lỗi. Các module khởi tạo
package có thể tạo phạm vi gián tiếp rộng, mang tính bảo thủ.

## Những gì đã sửa

1. Nhận diện child module trong `from package import module`, kể cả package tự
   reexport, relative import và alias. Trước đó grouping.py bị bỏ sót cả hai importer.
2. Giữ dependency của câu lệnh import khi tên local bị gán lại; vẫn kiểm lexical
   shadowing riêng khi xác định call. Giữ hậu tố dotted module khi đổi tên alias.
3. Parser config v4 tách cache mới khỏi snapshot cũ; không xóa dữ liệu lịch sử.
4. Explorer ghi **“File giả định thay đổi”** và giải thích đây không phải so sánh hai
   commit. Overlay đã thực sự chỉnh source vẫn giữ nhãn “File thay đổi”.

Không thay API/schema, generated types, migrations, dependency lockfile, quota
hoặc provider. Không thực thi mã nguồn các repo được phân tích.

## Kiểm thử và bằng chứng

**85 backend tests đạt**, gồm:

- 9 ca metrics mới: diamond/duplicate/shortcut, nhiều changed cùng cycle, partial
  coverage, ba trường hợp không có mẫu số, empty change set, canvas truncation,
  đường dẫn không tồn tại.
- Các ca import tuyệt đối/tương đối, alias, package attribute ưu tiên, cycle,
  rebinding và dotted reexport; graph/scenario/snapshot suites hiện có.

**8 browser tests đạt** với fixture được mock và có nhãn: actual counts và paths,
unknown không vẽ thanh 0%, overlay khác hypothesis, mở project/ảnh hưởng file,
lỗi impact hiện rõ, dark mode và saved hypothesis. Không coi fixture là kết quả
phân tích repo thật. Nhãn Explorer mới có regression: đã quan sát test fail với
“File thay đổi”, sửa rồi test pass. Các ca metrics đã đúng baseline được kiểm
chứng bổ sung, không tuyên bố đã sửa thuật toán BFS vốn đang đúng.

Playwright lần đầu thiếu executable; đã cài bản headless tương ứng lock hiện có.
Không đổi version hoặc lockfile. TypeScript typecheck, Vite build, Ruff và ESLint
cho file frontend thay đổi đều đạt. Vite cảnh báo bundle >500kB, không phải
lỗi build và chưa được tối ưu trong task này.

### Hai repo tại commit cố định

Đã chạy lại ngày 19/11, không gọi AI, không ghi DB. sqlparse dùng source snapshot
đã lưu từ lần audit digest; itsdangerous tải lại qua adapter public GitHub có giới
hạn, dùng cùng policy source của app.

| Repo/file | Commit | Changed | Direct | Indirect | Potential / analyzed |
| --- | --- | ---: | ---: | ---: | --- |
| sqlparse: `sqlparse/engine/grouping.py` | `09dbe1eec31ed1b3cd05366748865f11ba427d32` | 1 | 2 | 28 | 31 / 36 = 86,11% |
| itsdangerous: `src/itsdangerous/encoding.py` | `096c8d42545d3b68ea21a4f890fb2b2d8979c0bd` | 1 | 5 | 0 | 6 / 15 = 40% |

Hai direct importer của sqlparse đã đối chiếu câu lệnh import bằng AST:
`engine/__init__.py:8` và `engine/filter_stack.py:11` (còn gọi grouping.group ở dòng 41).
Năm direct importer của itsdangerous: `__init__.py`, `serializer.py`, `signer.py`,
`timed.py`, `url_safe.py`, đều trong `src/itsdangerous/`, khớp các câu `from .encoding`.

Số gián tiếp là kết quả suy từ graph, chưa phải ground truth độc lập của toàn repo.
Còn 1.039 quan hệ chưa giải được ở sqlparse và 310 ở itsdangerous: không dùng số 0
ở một nhóm để cam kết không có ảnh hưởng. Source hash và dòng import trong
`var/task-3.48/real-repo-results.json`; các file này được đưa vào gói bàn giao.

## Lệnh kiểm chứng

Tại root worktree, dùng venv và node theo lock hiện có:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/unit/test_impact_metrics.py backend/tests/unit/test_python_submodule_impact.py backend/tests/unit/test_python_explorer_resolution.py backend/tests/unit/test_explorer_graph.py backend/tests/unit/test_scenarios_unit.py backend/tests/unit/test_snapshot_models.py -q --tb=short
.venv/Scripts/ruff.exe check backend/src/smartregression/core/explorer/graph.py backend/src/smartregression/core/explorer/python_resolution.py backend/tests/unit/test_impact_metrics.py backend/tests/unit/test_python_submodule_impact.py
```

Tại `frontend`, Node 22.14.0:

```powershell
node node_modules/@playwright/test/cli.js test --config playwright.config.mjs --grep 'impact|what-if' --workers=1
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node node_modules/eslint/bin/eslint.js src/features/explorer/Explorer.tsx src/features/explorer/ImpactOverview.tsx tests/project-workspace.spec.mjs
```

Logs/evidence local: `var/task-3.48/`. Screenshot `impact-overview-synthetic.png` là
fixture browser, không phải dữ liệu người dùng. Review tự động không phát hiện
finding cần sửa trong phạm vi được giao; reviewer chỉ đọc code/tests, không tự
chạy lại test. Đây không phải review/phê duyệt độc lập của thành viên nhóm.

## Cách demo và giới hạn bàn giao

Mở repo đúng SHA → chọn file → đọc nhãn giả định, mẫu số, direct/indirect → mở
chuỗi đường dẫn và source để đối chiếu. Với itsdangerous kỳ vọng direct=5; với
sqlparse grouping kỳ vọng direct=2 trong parser config v4. Snapshot cũ ở config
khác cần materialize lại, không thay âm thầm report lịch sử.

Code nằm trên nhánh cá nhân và chưa được publish. App muốn dùng bản sửa phải chạy
backend và frontend từ worktree này; script startup của checkout cũ có thể mở
backend chưa sửa. Không lấy việc build thành công làm bằng chứng live user login
hoặc PostgreSQL đã được nghiệm thu lại trong phiên 19/11.

Codex hỗ trợ implementation/tests/đối chiếu; Hà An cần đọc và giải thích được quy
tắc đếm, nguồn mẫu số và giới hạn trước khi trình bày capstone.
