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

## 5. Chưa kiểm chứng / pending

| Mục | Trạng thái | Chờ ai |
|-----|-----------|--------|
| Input thật từ `ChangedComponent` của AN (2.01) | Pending | AN bàn giao |
| Graph edges thật từ H2 (2.03/2.04) | Pending | H2 bàn giao |
| Integration với workflow H1 (2.13) | Pending | H1 |
| CI Python 3.14 pass | Chưa chạy CI | — |
| Cross-language / non-Python paths | Ngoài MVP scope | — |
| Symbol-level edges (call graph) | Chỉ file-level import hiện có | Future task |

---

## 6. Files bàn giao

| File | Mô tả |
|------|-------|
| [`backend/src/smartregression/core/impact/review_ordering.py`](../../../backend/src/smartregression/core/impact/review_ordering.py) | Logic chính — `order_for_review()`, `ReviewCandidate`, `ReviewOrder` |
| [`backend/tests/unit/test_review_ordering.py`](../../../backend/tests/unit/test_review_ordering.py) | 43 unit tests, 11 nhóm, oracle thủ công |
| [`docs/research/sprint-2/review-ordering-2.07.md`](review-ordering-2.07.md) | Tài liệu này |

---

## 7. Kết quả kiểm chứng thực tế

```
Command:  py -m uv run pytest backend/tests/unit/test_review_ordering.py -v
Platform: win32 -- Python 3.14.10, pytest-9.1.1
Result:   43 passed in 0.56s

Command:  py -m uv run ruff check backend/src/.../review_ordering.py backend/tests/.../test_review_ordering.py
Result:   All checks passed (after --fix: 3 auto-fixed import sort issues)

Command:  py -m uv run ruff format --check ...
Result:   2 files already formatted

Command:  py -m uv run pytest backend/tests/unit/ -q
Result:   112 passed in 1.86s  (toàn bộ unit suite)
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

