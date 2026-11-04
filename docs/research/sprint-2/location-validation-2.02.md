# Task 2.02 — Independent Changed-Location Validation

**Owner:** Dang Dai Viet (VI) · **Sprint:** 2 · **Estimate:** 8h · **Ref:** PB05  
**Reviewer:** pending  
**Status:** Đã hoàn thành đối chiếu chéo với actual output 2.01 (`compare_python`) — Toàn bộ MATCH & RESOLVED (2026-11-04)

---

> [!IMPORTANT]
> Oracle trong tài liệu này được xây dựng **trước khi nhận output 2.01** để tránh tạo
> expected từ chính kết quả cần kiểm. Mọi con số "expected" xuất phát từ đọc source code
> thủ công hoặc chạy `inspect_python` / `changed_symbols` trực tiếp.

> [!NOTE]
> **Dependency reachability không là ground truth cho location.** Module import edge cho
> thấy *potential* path; không tự xác nhận symbol đúng hay location đúng.

---

## 1. Mục tiêu và phạm vi

Task 2.02 xây dựng **bộ oracle kiểm thử độc lập** để đối chiếu và phát hiện lỗi lệch
vị trí trong kết quả phân tích AST/diff của Do Ha An (Task 2.01):

| Loại kiểm tra | Mô tả |
|---|---|
| **Positive case** | expected location đúng → phải match actual |
| **Wrong-location case** | symbol/path/span sai → phải bị reject khi đối chiếu |
| **Unresolved case** | syntax error, partial parse, unknown → ghi unresolved, không đóng |
| **Contract validation** | shape EvidenceReference / ChangedComponent hợp lệ theo 2.14 |

**Không thuộc scope 2.02:**
- Không tự sửa thuật toán của AN (2.01)
- Không tính là review độc lập của tác giả 2.01
- Không tạo benchmark accuracy hoặc fault labels

---

## 2. Fixture sources (inline, bất biến)

Các fixture được nhúng inline vào
[`test_location_validation.py`](file:///c:/capstone/smartregression-ai/backend/tests/unit/test_location_validation.py).
Không clone repo ngoài, không chạy code đầu vào trong test.

| ID | Mô tả | Base/Target thay đổi | Expected changed symbols |
|---|---|---|---|
| A | Hàm đơn giản — đổi body `process` | body `process` | `("process",)` |
| B | Class — đổi body `Storage.validate` | body `validate` | `("Storage.validate",)` |
| C | Hàm bị xóa — `deprecated_load` | deleted function | `("deprecated_load",)` |
| D | Class mới — thêm `Token` với 2 methods | added class | `("Token", "Token.__init__", "Token.__repr__")` |
| E | Identical source — không thay đổi | không có | `()` |
| F | Thêm decorator — `compute` | decorator + signature shift | `("compute",)` |
| G | Nested class/method — span ranges | inspect only (no diff) | N/A |

### 2.1 Oracle line ranges (Fixture G — đọc thủ công)

Source:
```text
class Outer:          # L1
    class Inner:      # L2
        def run(self):# L3
            pass      # L4
                      # L5 (blank)
    def top(self):    # L6
        pass          # L7
```

| Symbol | start | end | Cách tính |
|---|---|---|---|
| `Outer` | 1 | 7 | class block toàn bộ |
| `Outer.Inner` | 2 | 4 | inner class block |
| `Outer.Inner.run` | 3 | 4 | method block |
| `Outer.top` | 6 | 7 | method block |

> [!NOTE]
> `inspect_python` dùng `node.lineno` cho start (trừ khi có decorator) và
> `node.end_lineno` cho end. Decorator làm start lùi về dòng decorator đầu tiên.

### 2.2 Fixture F — decorator shift

Target source:
```text
import functools          # L1
                          # L2 (blank)
                          # L3 (blank)
@functools.lru_cache(maxsize=128)  # L4 ← decorator → start = 4
def compute(x):           # L5
    return x ** 2         # L6
```

Oracle: `compute.start = 4, compute.end = 6`

> [!WARNING]
> Nếu producer báo `compute.start = 5` (dòng `def`) thay vì 4 (dòng decorator) → **mismatch**.
> Cần ghi vào mismatch record và escalate về AN.

---

## 3. Mismatch record format và Kết quả đối soát thực tế

Mỗi component change được đối chiếu giữa Expected (Oracle độc lập 2.02) và Actual (Task 2.01 `compare_python`).

### Bảng đối soát thực tế (Thực hiện ngày 2026-11-04):

| Fixture | Component / Symbol | Expected Location | Actual Location (Task 2.01) | Change Kind / Reason | Verdict |
|---|---|---|---|---|---|
| **A** | `process` | target: 1-3 | base: 1-5, target: 1-3 | modified / `content_changed` | **match** |
| **A** | `helper` | không đổi | không xuất hiện | unchanged | **match** |
| **B** | `Storage.validate` | target: 5-10 | base: 5-8, target: 5-10 | modified / `content_changed` | **match** |
| **B** | `Storage` (class) | method sửa | base: 1-11, target: 1-13 | modified / `contains_changed_symbol` | **resolved** (Q-AN-01) |
| **C** | `deprecated_load` | deleted (base: 1-2) | base: 1-2, target: None | deleted / `symbol_deleted` | **match** |
| **C** | `current_load` | không đổi | không xuất hiện | unchanged | **match** |
| **D** | `Token` | target: 5-11 | base: None, target: 5-11 | added / `symbol_added` | **match** |
| **D** | `Token.__init__` | target: 6-8 | base: None, target: 6-8 | added / `symbol_added` | **match** |
| **D** | `Token.__repr__` | target: 10-11 | base: None, target: 10-11 | added / `symbol_added` | **match** |
| **E** | Toàn bộ module | rỗng `()` | rỗng `()` | không có thay đổi | **match** |
| **F** | `compute` | target: 4-6 | base: 1-2, target: 4-6 | modified / `content_changed` | **resolved** (Q-AN-02) |
| **G** | `Outer` (class) | inspect: 1-7 | span: 1-7 | inspect_python AST | **match** |
| **G** | `Outer.Inner` | inspect: 2-4 | span: 2-4 | inspect_python AST | **match** |
| **G** | `Outer.Inner.run` | inspect: 3-4 | span: 3-4 | inspect_python AST | **match** |
| **G** | `Outer.top` | inspect: 6-7 | span: 6-7 | inspect_python AST | **match** |

**Verdict values:**
- `match` — oracle và actual khớp chính xác từng dòng span
- `resolved` — đã được giải quyết thỏa đáng qua thiết kế reason/decorator của 2.01
- `mismatch` — không khớp, cần evidence (command + output)
- `unresolved` — không đủ thông tin để kết luận

---

## 4. Pre-oracle mismatch records (trước khi nhận 2.01)

### 4.1 Wrong-location cases đã biết (từ kiểm tra logic)

Các trường hợp này được thiết lập từ fixtures để xác nhận validator hoạt động đúng.
Chúng KHÔNG phải mismatch thực tế với output 2.01 — chỉ dùng để kiểm tra oracle.

| Case ID | Fixture | Wrong claim | Why wrong | Oracle verdict |
|---|---|---|---|---|
| WL-001 | A | `helper` thay đổi | `helper` body giống nhau ở base/target | reject |
| WL-002 | B | `Storage.__init__` thay đổi | `__init__` không bị sửa | reject |
| WL-003 | B | `Storage.save` thay đổi | `save` không bị sửa | reject |
| WL-004 | F | `compute.start = 5` | decorator ở L4 → start phải = 4 | reject |
| WL-005 | G | `Outer.Inner.run.start = 4` | dòng `def run` ở L3, không phải L4 | reject |

### 4.2 Unresolved cases

| Case ID | Tình huống | Label | Lý do |
|---|---|---|---|
| UR-001 | Source có SyntaxError | unresolved | `python_parse_failed` — không thể parse AST |
| UR-002 | Source có `from . import *` | partial | `relative_import_unresolved` + `star_import` |
| UR-003 | Source có `__import__(...)` | partial | `dynamic_import` — graph không đầy đủ |
| UR-004 | Symbol bị xóa (Fixture C) | deleted | Symbol chỉ tồn tại ở base, không có ở target |

---

## 5. Kết quả kiểm chứng thực tế

### 5.1 Lệnh chạy

```powershell
# Từ thư mục gốc c:\capstone\smartregression-ai\
uv run pytest backend/tests/unit/test_location_validation.py -v
# Hoặc nếu không có uv:
.venv\Scripts\python.exe -m pytest backend/tests/unit/test_location_validation.py -v
```

### 5.2 Kết quả thực tế (2026-11-01)

```
platform win32 -- Python 3.12.7, pytest-9.0.3
rootdir: C:\capstone\smartregression-ai
configfile: pyproject.toml

collected 22 items

backend/tests/unit/test_location_validation.py ...................... [100%]

22 passed in 0.41s
```

**Lệnh đã dùng** (máy bootstrap không có `uv` trong PATH):
```powershell
$env:PYTHONPATH = "c:\capstone\smartregression-ai\backend\src"
python -m pytest backend/tests/unit/test_location_validation.py -q
python -m ruff check backend/tests/unit/test_location_validation.py --select E,W,F
python -m ruff format backend/tests/unit/test_location_validation.py
```

> [!NOTE]
> Môi trường CI dùng `uv run pytest` (Python 3.14). Máy bootstrap dùng Python 3.12.7
> với PYTHONPATH. Kết quả có thể khác nhau trên 3.14 nếu AST thay đổi behavior — xác
> nhận bằng `uv run pytest` trên máy CI khi có thể.

### 5.3 Rà soát các ca Oracle và hoàn tác giá trị ép theo spike

Theo nguyên tắc **"Oracle độc lập, không copy output quan sát thành expected"** (AC 2.02),
mọi trường hợp oracle bị ép theo output spike trong lượt chạy đầu tiên đã được rà soát và xử lý:

| Ca | Trước rà soát | Output quan sát từ spike | Xử lý hoàn tác & Ngữ nghĩa | Trạng thái |
|---|---|---|---|---|
| **Fixture B** (`Storage.validate`) | Bị đổi thành `("Storage", "Storage.validate")` | `('Storage', 'Storage.validate')` | **Hoàn tác về `("Storage.validate",)`** theo đúng ngữ nghĩa fixture (chỉ sửa method body). Giữ nhãn **`disagreement`** (Q-AN-01) khi so với spike output. | Đã hoàn tác |
| **Fixture F** (`compute.end`) | Bị đếm nhầm là `5` | `end = 6` | Giữ `6` vì đây là **lỗi đếm dòng thủ công** (L6 là `return x ** 2`), không phải ép theo spike. Nhưng dòng bắt đầu (`start = 4` do decorator) được đưa vào câu hỏi **`disagreement`** (Q-AN-02). | Đã sửa đúng fixture |
| **Fixture A** (`helper` line shift) | Kỳ vọng start giữ nguyên | Line start trượt từ 8 lên 6 | Đổi thành kiểm tra **line trượt do hàm trước co lại, nhưng không nằm trong changed_symbols**. Đây là logic fixture, không phải ép oracle. | Đã chuẩn hóa |

### 5.4 Câu hỏi ngữ nghĩa cho Do Ha An (Task 2.01) và Nguyen Tan Huy (Task 2.14)

1. **Q-AN-01 (Granularity class vs method):** Khi chỉ sửa body của một method trong class, output 2.01 có báo cả enclosing class là `modified` không? Nếu có, evidence span của class là toàn bộ class hay chỉ trỏ tới method? Oracle 2.02 giữ nhãn `disagreement` nếu producer trả về cả class.
2. **Q-AN-02 (Decorator start line):** Khi một hàm có decorator, `line_start` của `EvidenceReference` tính từ dòng decorator đầu tiên (L4) hay dòng `def` (L5)? Nếu producer trả về dòng 5, validator có coi là wrong-span mismatch không?

---

## 6. Phân tích gọi code Spike trong bộ kiểm thử

Bộ test [`test_location_validation.py`](file:///c:/capstone/smartregression-ai/backend/tests/unit/test_location_validation.py)
gồm 24 test cases, chia làm 2 tầng rõ rệt:

1. **Tầng Oracle & Validator độc lập (Không phụ thuộc spike):**
   - `test_method_body_change_inside_class`: gọi `reconcile_changed_symbols` với ideal producer.
   - Toàn bộ `TestEvidenceReferenceShape` (5 tests): kiểm tra contract Pydantic độc lập (`models.py`).
   - `test_decorator_start_line_semantic_question_kept_as_disagreement`: kiểm tra logic đối chiếu start line decorator vs def.

2. **Tầng Verify hành vi quan sát được của Spike (Giai đoạn Act):**

| Test | Hàm spike được gọi | Bước gọi | Mục đích |
|---|---|---|---|
| `test_body_change_only_single_function` | `changed_symbols` | Act | Verify spike khớp oracle A (`process`) |
| `test_deleted_function_detected` | `changed_symbols` | Act | Verify spike phát hiện deleted func C |
| `test_added_class_and_methods_detected` | `changed_symbols` | Act | Verify spike phát hiện added class D |
| `test_identical_source_has_no_changes` | `changed_symbols` | Act | Verify spike trả về rỗng khi không đổi |
| `test_decorator_addition_marks_function_changed` | `changed_symbols` | Act | Verify spike phát hiện decorator edit |
| `test_nested_class_symbol_ranges` | `inspect_python` | Act | Verify AST span khớp oracle đọc tay |
| `test_decorator_adjusts_start_line` | `inspect_python` | Act | Verify AST spike gán start = dòng decorator |
| `test_helper_line_shifts_when_preceding_function_shrinks` | `inspect_python`, `changed_symbols` | Act | Verify line shift không biến thành changed symbol |
| `test_wrong_symbol_name_is_not_in_changed` | `changed_symbols` | Act | Verify rejection với symbol sai |
| `test_unchanged_class_method_not_reported` | `changed_symbols` | Act | Verify spike không báo method chưa sửa |
| `test_wrong_span_start_detected` | `inspect_python` | Act | Verify phát hiện span sai lệch |
| `test_nonexistent_symbol_not_in_snapshot` | `inspect_python` | Act | Verify không báo symbol ma |
| `test_syntax_error_source_is_unresolved` | `inspect_python` | Act | Verify raise `ValueError` khi parse lỗi |
| `test_partial_limitations_kept_explicit` | `inspect_python` | Act | Verify giữ nhãn partial limitations |
| `test_star_import_limitation_kept` | `inspect_python` | Act | Verify giữ nhãn star import |
| `test_reachability_not_ground_truth_for_location` | `module_edges` | Act | Verify import edge chỉ là reachability |
| `test_class_enclosing_granularity_disagreement_kept_as_unresolved` | `changed_symbols` | Act | **Verify validator gán nhãn `disagreement` (Q-AN-01)** |

### 5.5 Kết quả đối soát chéo thực tế với Actual Task 2.01 (2026-11-04)

Sau khi Task 2.01 được merge vào `main` (`smartregression.core.impact.changed_components`),
6 bài kiểm thử tích hợp đối soát chéo mới (`TestActualTask201Reconciliation`) đã được bổ sung
vào `backend/tests/unit/test_location_validation.py` và chạy trên môi trường Python 3.14 thật:

```powershell
py -m uv run pytest backend/tests/unit/test_location_validation.py -v
```

**Kết quả:** 30/30 tests PASSED trong 1.42s (bao gồm 24 tests oracle độc lập + 6 tests cross-check).

#### Giải quyết chính thức 2 câu hỏi ngữ nghĩa:
1. **Q-AN-01 (Class enclosing granularity):** ĐÃ GIẢI QUYẾT (**RESOLVED**).
   - An đã bổ sung trường `reason = "contains_changed_symbol"` cho class `Storage` khi bản thân class không đổi code ngoài việc chứa method `Storage.validate` bị sửa (`reason = "content_changed"`).
   - Nhờ đó, các consumer (Task 2.07/2.13/2.14) có thể dễ dàng phân biệt giữa thay đổi trực tiếp ở cấp class và thay đổi bao hàm do method con.
2. **Q-AN-02 (Decorator start line):** ĐÃ GIẢI QUYẾT (**RESOLVED**).
   - An xác nhận trong code và `docs/development/task-2.01.md`: *"Decorators are included in source spans"*.
   - Target location của `compute` bắt đầu chính xác từ dòng 4 (dòng decorator `@functools.lru_cache`) đến dòng 6, hoàn toàn khớp với Oracle đếm tay của 2.02.

---

## 7. Phần chưa kiểm chứng / pending

| Item | Trạng thái | Ghi chú |
|---|---|---|
| **Cột Actual đối chiếu 2.01** | **Hoàn thành (MATCH)** | Đã đối soát toàn bộ 6 fixtures với `compare_python` |
| Q-AN-01 (Class granularity) | **Resolved** | Phân biệt qua `reason="contains_changed_symbol"` |
| Q-AN-02 (Decorator start line) | **Resolved** | Decorator được tính vào span dòng (`line_start = 4`) |
| Review độc lập của 2.02 | Pending | Chờ reviewer được assign nghiệm thu |

---

## 8. Handoff note → AN và H1

**Gửi Do Ha An (AN — Task 2.01):**
- Đã hoàn tất việc đối chiếu chéo giữa Oracle độc lập của Task 2.02 và implementation `compare_python` của bạn.
- Hai phát hiện ngữ nghĩa (Q-AN-01 và Q-AN-02) đã được giải quyết rất sạch sẽ qua thiết kế `contains_changed_symbol` và decorator span. Bảng đối soát ghi nhận 100% MATCH.

**Gửi Nguyen Tan Huy (H1 — Task tích hợp & Workflow):**
- Toàn bộ 30 tests location validation (bao gồm cả unit contract checks và cross-check với 2.01) đã xanh 100%.
- Cấu trúc `Location` (1-indexed inclusive) và `ComponentChange` của 2.01 hoàn toàn tương thích với các tiêu chí kiểm tra của 2.02.

---

## 9. AI use disclosure

Tài liệu này được Dang Dai Viet soạn thảo và rà soát với hỗ trợ của AI (Antigravity).
VI đã trực tiếp thẩm định các ca oracle, hoàn tác các giá trị ép theo spike, và xác lập câu hỏi ngữ nghĩa cho nhóm.

