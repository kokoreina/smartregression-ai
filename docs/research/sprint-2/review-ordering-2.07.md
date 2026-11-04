# Review Ordering — Task 2.07

**Rule version:** `2.07-v1`
**Author:** Dang Dai Viet (VI)
**Date:** 2026-11-01
**Sprint:** 2 — Change impact + dependency analysis

> [!NOTE]
> Đây là tài liệu nghiên cứu cho Task 2.07. Module này chỉ sản xuất **ordered review starting points cho con người** — không chọn tests, không ước lượng fault probability, không gán fault labels.

---

## 1. Mục tiêu và phạm vi

Task 2.07 xây dựng thuật toán xếp hạng **deterministic** cho danh sách components cần review sau khi phân tích impact. Đầu ra là danh sách `ReviewCandidate` có thứ tự ổn định, phục vụ:

- **H1 (2.13):** tích hợp vào workflow, tiêu thụ `ReviewOrder`
- **H1/VI (2.18):** hiển thị trên UI real-report

**Không nằm trong scope:**
- Chọn test để chạy (Task 2.09/2.16/2.17)
- Ước lượng fault probability hay confidence score
- Phân tích xuyên repo hoặc dynamic execution

---

## 2. Thuật toán 2.07-v1

### 2.1 Input

```python
order_for_review(
    changed: Sequence[ChangedComponent],   # từ 2.01 (AN)
    edges:   Sequence[tuple[str, str]],    # (importer, importee) từ 2.03 (H2)
    limitations: Sequence[str],            # từ 2.17/python_snapshot
) -> ReviewOrder
```

Edge convention: `(importer_path, importee_path)` — importer **phụ thuộc vào** importee, khớp với output của `module_edges()` trong `python_snapshot.py`.

### 2.2 Quy tắc phân tầng

| Tier | Ý nghĩa | Cách xác định |
|------|---------|----------------|
| **1** | Directly changed executable | Mọi `ChangedComponent` trong input |
| **2** | Direct dependents | Importer có cạnh trực tiếp đến một Tier-1 path |
| **3** | Indirect dependents | Transitive importers (BFS từ Tier 2), không thuộc Tier 1 hoặc 2 |

### 2.3 Quy tắc dedup

- Nếu một path xuất hiện ở nhiều tier → **giữ tier thấp nhất** (1 < 2 < 3)
- Cùng path nhưng khác symbol trong `ChangedComponent` → **giữ nguyên** (2 entries riêng biệt)
- Trùng cả path lẫn symbol → **loại bản trùng**

### 2.4 Stable tie-breaking

Trong cùng một tier, sắp xếp **alphabetically ascending** theo `(path, symbol or "")` để đảm bảo output giống nhau khi chạy nhiều lần với cùng input.

### 2.5 Cycle safety

BFS dùng `visited` set — mọi path chỉ được thăm một lần, không vòng lặp vô hạn với cyclic imports.

### 2.6 Partial graph detection

Khi `edges` rỗng → tự động thêm `"partial_graph"` vào `limitations` output. Caller-supplied limitations được giữ nguyên và merge vào output.

### 2.7 Lớp chuyển đổi mỏng (Thin Adapters) nối dữ liệu thật (Task 2.01 & 2.04)

Hỗ trợ chuyển đổi trực tiếp các payload chuẩn từ các stage khác trong hệ thống sang `ReviewOrder`:

1. **`order_from_impact_payload(impact: ImpactPayload, *, graph: GraphPayload | None = None, limitations: Sequence[str] = ()) -> ReviewOrder`:**
   - Chuyển `ImpactCandidate` sang `ReviewCandidate`:
     - `relationship == "changed"` → Tier 1 (`reason="directly changed"`)
     - `relationship == "direct"` → Tier 2 (`reason="direct dependent (distance 1)"`)
     - `relationship == "indirect"` → Tier 3 (`reason="indirect dependent (min distance N)"`)
   - **Trích xuất khoảng cách (distance):** Tra cứu chuỗi `nodes` trong `ImpactPath` (`len(nodes) - 1`) để tính khoảng cách đồ thị ngắn nhất.
   - **Deduplication:** Nếu một component xuất hiện qua nhiều change origins (vừa direct vừa indirect), giữ Tier thấp nhất (1 < 2 < 3) và khoảng cách ngắn nhất.
   - **Tương thích 'partial':** Nếu `graph.unresolved` không rỗng (chứa `star_import`, `dynamic_import`, v.v.), tự động gán nhãn `"partial_graph"` cùng các mã lỗi chi tiết.

2. **`order_from_stage_changes(changes: ChangePayload, graph: GraphPayload, *, limitations: Sequence[str] = ()) -> ReviewOrder`:**
   - Chuyển đổi `ChangePayload` (2.01) và `GraphPayload` (2.03) sang `order_for_review()`.

---

## 3. Fixtures và oracle thủ công

### Fixture A — No changed components

```
Input:
  changed = []
  edges   = []

Oracle:
  candidates = ()
  limitations contains "partial_graph"  (edges empty)
```

Tự kiểm: không có changed → không có gì để review. Limitation phải nêu partial graph.

### Fixture B — Single changed file, no graph

```
Input:
  changed = [ChangedComponent(path="auth.py", change="modified")]
  edges   = []

Oracle:
  candidates = [ReviewCandidate(path="auth.py", symbol=None, tier=1)]
  limitations contains "partial_graph"
```

Tự kiểm: 1 candidate Tier-1, symbol = None (file-level), partial_graph vì edges rỗng.

### Fixture C — Direct dependent chain

```
Input:
  changed = [ChangedComponent(path="core.py", change="modified")]
  edges   = [("api.py", "core.py"), ("web.py", "api.py")]

Oracle:
  core.py  → Tier 1
  api.py   → Tier 2 (imports core.py directly)
  web.py   → Tier 3 (imports api.py → transitive)
  limitations = ()  (edges non-empty)
```

Tự kiểm bằng tay: edges tạo graph `web.py → api.py → core.py`. core bị đổi → api là direct dep → web là indirect dep. Không auto partial_graph vì có edge.

### Fixture D — Alphabetical tie-breaking (Tier 2)

```
Input:
  changed = [ChangedComponent(path="lib.py", change="modified")]
  edges   = [("z_svc.py", "lib.py"), ("a_svc.py", "lib.py"), ("m_svc.py", "lib.py")]

Oracle Tier-2 order (by path alpha):
  a_svc.py, m_svc.py, z_svc.py
```

Tự kiểm: 3 direct dependents cùng tier, sắp xếp theo alpha path.

### Fixture E — Dedup: path ở Tier 1 + có self-edge

```
Input:
  changed = [ChangedComponent(path="a.py", change="modified")]
  edges   = [("b.py", "a.py"), ("a.py", "a.py")]  # self-edge

Oracle:
  a.py → Tier 1 (only once)
  b.py → Tier 2
```

Tự kiểm: a.py đã Tier 1, self-edge không nâng lên Tier 2 thứ hai.

### Fixture F — web.py imports TWO Tier-2 nodes (dedup Tier 3)

```
Input:
  changed = [ChangedComponent(path="core.py", change="modified")]
  edges   = [
    ("api/login.py",   "core.py"),
    ("api/profile.py", "core.py"),
    ("web/app.py",     "api/login.py"),
    ("web/app.py",     "api/profile.py"),   # same node, two paths
  ]

Oracle:
  core.py        → Tier 1
  api/login.py   → Tier 2
  api/profile.py → Tier 2
  web/app.py     → Tier 3 (only once, despite two Tier-2 importees)
```

Tự kiểm: web/app.py xuất hiện 2 lần trong BFS expansion nhưng `visited` set loại bản trùng.

### Fixture G — Cycle A → B → A

```
Input:
  changed = [ChangedComponent(path="a.py", change="modified")]
  edges   = [("b.py", "a.py"), ("a.py", "b.py")]

Oracle:
  a.py → Tier 1
  b.py → Tier 2
  (total 2 candidates, no Tier 3, no infinite loop)
```

Tự kiểm: b.py là direct importer của a.py → Tier 2. a.py là importer của b.py nhưng đã thuộc Tier 1 → `visited` chặn. BFS kết thúc.

### Fixture H — Full pipeline (xem `TestFullPipelineScenario`)

Xem docstring test `test_full_ordering_example` trong [`test_review_ordering.py`](../../../backend/tests/unit/test_review_ordering.py) — oracle 7 candidates được đếm tay từ fixture, không copy từ code output.

---

## 4. Limitations đã biết

| Limitation | Ghi chú |
|------------|---------|
| `partial_graph` | Edges rỗng = không có graph info, chỉ Tier-1 được đảm bảo |
| `import_observations_only_not_complete_dependency_graph` | Từ `module_edges()` — static import, không phải call graph |
| `relative_import_unresolved` | Relative imports không resolve được target path |
| `dynamic_import` | `__import__()` / `import_module()` không trace được |
| `star_import` | `from x import *` che dependencies thật |

**Dependency edge không chứng minh behavioral impact** (per rule 09): Tier-2/3 là gợi ý review, không phải xác nhận fault.

---

## 5. Kết quả kiểm chứng nghi ngờ & Trạng thái pending

### 5.1 Kiểm chứng 3 câu hỏi / nghi ngờ về dữ liệu thực tế Task 2.04 & 2.01:

1. **`potential_impact` có đưa khoảng cách (distance) không?**
   - **Thực tế:** Trong `ImpactCandidate` **không có trường `distance` trực tiếp**, mà chỉ có `relationship: Literal["changed", "direct", "indirect"]`.
   - **Giải pháp chuyển đổi:** `ImpactPayload` cung cấp danh sách `paths: list[ImpactPath]`. Mỗi `ImpactPath` có chuỗi `nodes: list[RepoPath]` từ candidate đến changed module origin. Lớp chuyển đổi mỏng tra cứu `nodes` để tính chính xác khoảng cách đồ thị `distance = len(nodes) - 1` (ví dụ: direct = 1 hop, indirect = 2, 3... hops) và đưa vào trường `reason` của `ReviewCandidate`.

2. **`potential_impact` có đưa limitations không?**
   - **Thực tế:** Bản thân `ImpactPayload` **không mang trường limitations**.
   - **Giải pháp chuyển đổi:** Limitations của đồ thị thực tế được lưu tại `GraphPayload.unresolved` (chứa các `ImportLimitation` như `relative_import_unresolved`, `star_import`, `dynamic_import`, `target_not_in_snapshot`). Adapter nhận `graph: GraphPayload` và tự động trích xuất các mã lỗi này sang `ReviewOrder.limitations`.

3. **Định nghĩa "partial" của họ có khớp với `partial_graph` của bạn không?**
   - **Thực tế:** Khớp về mặt ngữ nghĩa nhưng định nghĩa của 2.03/2.04 chi tiết hơn. Trong 2.07 ban đầu, `partial_graph` chỉ kích hoạt khi `not edges`. Trong 2.03/2.04, một đồ thị là partial khi có unresolved imports hoặc thiếu edges khi có nodes.
   - **Giải pháp chuyển đổi:** Lớp chuyển đổi mỏng tự động gắn nhãn `"partial_graph"` bất cứ khi nào `graph.unresolved` có phần tử, hoặc khi `graph` có nodes nhưng không có edges.

### 5.2 Trạng thái các mục:

| Mục | Trạng thái | Ghi chú |
|-----|-----------|--------|
| Input thật từ Task 2.01 (`ChangePayload` / `ComponentChange`) | **Đã hoàn thành** | Đã kết nối qua `order_from_stage_changes` |
| Graph edges & impact thật từ Task 2.04 (`ImpactPayload`) | **Đã hoàn thành** | Đã kết nối qua `order_from_impact_payload` |
| Integration với workflow H1 (2.13) | Đã sẵn sàng | H1 có thể gọi trực tiếp `order_from_impact_payload` |
| CI Python 3.14 pass | PR #16 đã merge | Nhánh mới đã test pass |
| Review độc lập của người khác | Pending | Chờ reviewer nghiệm thu |

---

## 6. Files bàn giao

| File | Mô tả |
|------|-------|
| [`backend/src/smartregression/core/impact/review_ordering.py`](../../../backend/src/smartregression/core/impact/review_ordering.py) | Logic chính + 2 thin adapters `order_from_impact_payload` & `order_from_stage_changes` |
| [`backend/tests/unit/test_review_ordering.py`](../../../backend/tests/unit/test_review_ordering.py) | 47 unit tests (43 tests ban đầu + 4 tests adapter dữ liệu thật) |
| [`docs/research/sprint-2/review-ordering-2.07.md`](review-ordering-2.07.md) | Tài liệu đặc tả và kết quả kiểm chứng |

---

## 7. Kết quả kiểm chứng thực tế

```
Command:  py -m uv run pytest backend/tests/unit/test_review_ordering.py -v
Platform: win32 -- Python 3.14.10, pytest-9.1.1
Result:   47 passed in 1.15s

Command:  py -m uv run ruff check backend/src/.../review_ordering.py backend/tests/.../test_review_ordering.py
Result:   All checks passed (0 errors)

Command:  py -m uv run ruff format --check ...
Result:   All files already formatted
```

**Self-review note:** Tự kiểm tra trong cùng phiên — không phải review độc lập của người khác.

---

## 8. Handoff → H1, VI (2.13, 2.18)

**Output shape:**

```python
ReviewOrder(
    candidates=(
        ReviewCandidate(
            path="core/auth.py", symbol=None, tier=1, reason="directly changed (modified)"
        ),
        ReviewCandidate(
            path="core/storage.py",
            symbol="Storage.load",
            tier=1,
            reason="directly changed (modified)",
        ),
        ReviewCandidate(
            path="core/storage.py",
            symbol="Storage.save",
            tier=1,
            reason="directly changed (modified)",
        ),
        ReviewCandidate(
            path="api/login.py",
            symbol=None,
            tier=2,
            reason="directly imports changed path 'core/auth.py'",
        ),
        ReviewCandidate(
            path="api/profile.py",
            symbol=None,
            tier=2,
            reason="directly imports changed path 'core/auth.py'",
        ),
        ReviewCandidate(
            path="api/upload.py",
            symbol=None,
            tier=2,
            reason="directly imports changed path 'core/storage.py'",
        ),
        ReviewCandidate(
            path="web/app.py", symbol=None, tier=3, reason="transitively depends on 'api/login.py'"
        ),
    ),
    limitations=(),
    rule_version="2.07-v1",
)
```

**Điểm cần lưu ý cho 2.13/2.18:**
- `tier` field: 1/2/3 — dùng để nhóm hiển thị hoặc lọc
- `symbol` có thể `None` ở Tier 2/3 (chỉ file-level, không có symbol-level dep info)
- `reason` là mô tả text cho human — không phải machine-readable state
- `rule_version` pin cho traceability; nếu thuật toán đổi, version phải tăng
- Không có `confidence`, `fault_probability`, `test_id` — thiết kế cố ý theo AC

