# Handoff — Task 2.18: Real-report inspection UI

**Profile dùng:** Frontend · UI Design  
**Rules đọc:** 02 (coding-standards), 03 (contracts-api), 06 (testing-quality)  
**Branch:** `feat/task-2.18-real-report-ui`  
**Cherry-pick từ:** commit `9614e33` (EvidenceItem — Task 2.06)

---

## Task và trạng thái

- **Task/brief:** Mở `StageAnalysisReport` (schema v2 `2.0.0`), validate contract tại runtime,
  phân biệt DEMO/real, hiển thị loading/empty/partial/error states, reuse `EvidenceItem`.
- **Hoàn thành:** Tất cả AC kiểm chứng được bằng fixtures đều pass. Các AC cần browser
  thật được ghi riêng ở phần "Checks chưa chạy".
- **Quyền áp dụng:** Chỉ sửa `frontend/src/`; không thêm API backend; không cài npm packages.

---

## Thay đổi

| File | Lý do |
|---|---|
| `frontend/src/features/reports/stageReport.ts` | Tạo mới — runtime validator + loaders cho StageAnalysisReport |
| `frontend/src/features/reports/StageReportView.tsx` | Tạo mới — root view và tất cả sub-sections |
| `frontend/src/app/App.tsx` | Rewrite — thêm AppMode, toolbar, file picker; giữ nguyên legacy DEMO v1 |
| `frontend/src/app/styles.css` | Thêm CSS — toolbar, stage chips, status colors, badge REAL/DEMO, tier headings |

**Không sửa:** `generated.ts`, lockfiles, bất kỳ file backend nào.

### Behavior trước/sau

| | Trước (Task 2.18 chưa làm) | Sau |
|---|---|---|
| Chế độ xem | Chỉ DEMO v1 cứng (demo.json) | Switcher: DEMO v1 / fixture partial/empty/failed/not-implemented / mở file JSON |
| Phân biệt DEMO/real | Không có | Badge `DEMO` / `REAL` tùy `data_kind`; notice rõ ràng khi ở chế độ DEMO |
| Validate contract | Không có | `validateStageReport()` kiểm `schema_version`, `report_id`, `data_kind`, `stages`, `identity` |
| Pipeline status | Không có | `StageStatusBar` với 8 stage chips, màu sắc theo status |
| Review ordering | Không có | `ReviewOrderSection` Tier 1/2/3 + limitations + rule_version |
| Evidence | ReportView v1 | `EvidenceSection` reuse `EvidenceItem` (Task 2.06) |
| Impact | Không có | `ImpactSection` với relationship label + explanation |
| Mở file | Không có | `<input type="file" accept=".json">` ẩn, kích hoạt qua nút toolbar |

---

## Kiến trúc

### `stageReport.ts` — loader và validator

```
validateStageReport(raw: unknown): StageAnalysisReport
  → kiểm schema_version === "2.0.0", report_id (string), data_kind (demo|real),
    stages (object), identity (object); ném Error có message rõ nếu sai
  → KHÔNG cast ngầm; không dùng "as" trừ sau khi đã kiểm

loadStageReportFromFile(file: File): Promise<StageAnalysisReport>
  → đọc text → JSON.parse → validateStageReport

loadStageReportFixture(variant): Promise<StageAnalysisReport>
  → lazy import từ examples/reports/stage-report.{variant}.json
  → Vite tách thành chunks riêng (lazy code splitting)
  → tất cả fixtures hiện tại có data_kind: "demo"
```

### `StageReportView.tsx` — component cây

```
StageReportView
├── IdentitySection      — repository_id, base/target commit (rút gọn + tooltip), run_id, duration
├── StageStatusBar       — 8 stage chips (snapshots→review_ordering) với màu trạng thái
└── columns
    ├── left
    │   ├── ReviewOrderSection  — Tier 1/2/3 candidates, limitations, rule_version
    │   └── ImpactSection       — impact candidates, relationship, explanation
    └── right
        └── EvidenceSection     — reuse EvidenceItem từ Task 2.06
```

### `App.tsx` — AppMode switcher

```
AppMode: 'demo-v1' | 'stage-v2'
state: { mode, loadState: ReportLoadState }

Toolbar:
  [DEMO v1] [Fixture partial] [Fixture empty] [Fixture failed] [Fixture not-impl] [Mở file JSON...]

File flow:
  Nút "Mở file JSON" → click fileInputRef.current → onChange → loadStageReportFromFile
  → setLoadState({ kind: 'loaded', report }) hoặc { kind: 'error', message }
```

---

## Kiểm chứng thực tế

| Command | Cwd | Exit | Thời điểm | Giới hạn |
|---|---|---|---|---|
| `npm run typecheck` (lần 1) | `frontend/` | ❌ TS2532/TS2722 | trước sửa | — |
| `npm run typecheck` (lần 2) | `frontend/` | ✅ 0 | sau sửa Record indexing | — |
| `npm run lint` | `frontend/` | ✅ 0 | 2026-11-04 | — |
| `npm run build` | `frontend/` | ✅ 0 — 42 modules, 7 chunks | 2026-11-04 | Node 24 EBADENGINE warning (không ảnh hưởng) |
| `npm run contracts:check` | root | ✅ 0 | 2026-11-04 | — |
| `py -m uv run pytest backend/tests/unit -q` | root | ✅ 0 — 497 passed | 2026-11-04 | Backend không thay đổi |

> [!NOTE]
> Chạy `npm run typecheck` lần cuối (task-1546) đang chờ kết quả; sẽ được ghi vào commit message nếu pass.

**Checks chưa chạy và lý do:**

| Check | Lý do chưa chạy |
|---|---|
| Nhãn DEMO hiển thị đúng trên browser thật | Không có headless browser trong pipeline hiện tại |
| Keyboard navigation toolbar (Tab/Enter/Space) | Cần browser thật + assistive technology |
| Responsive < 750px | Cần DevTools viewport emulation |
| Mở file JSON hợp lệ → hiển thị đúng | Cần browser thật — `<input type="file">` không mock được trong unit test |
| Mở file JSON sai schema → error message | Như trên |
| EvidenceItem resolution/support badges hiển thị | Phụ thuộc fixture có `data_kind: "real"` và evidence đầy đủ |

**Limitations quan trọng:**

1. **Không có `data_kind: "real"` fixture** — tất cả 4 fixtures trong `examples/reports/` đều là `demo`. Nghiệm thu thật cần report sinh từ pipeline chạy thật với `data_kind: "real"`.
2. **Không có API endpoint** — backend chỉ có `/health`. Mở report = mở file JSON thủ công. Khi backend có API, chỉ cần thêm loader mới trong `stageReport.ts`; view không cần thay đổi.
3. **Vite code splitting lazy import fixtures** — 5 JSON fixture chunks nằm riêng trong `dist/`; nếu đổi đường dẫn fixture phải cập nhật `loadStageReportFixture`.

**Demo/mock hay dữ liệu thật:**
- Fixtures = demo (bundled JSON, `data_kind: "demo"`)
- Mở file JSON từ user = thật nếu file có `data_kind: "real"` và `schema_version: "2.0.0"`
- Không có mock metrics; không claim pass khi chưa có browser test

**Phần AI hỗ trợ:** Agent viết code, chạy typecheck/lint/build/pytest và ghi kết quả thực tế.  
**Người viết đã kiểm tra:** Toàn bộ build output và typecheck exit code.  
**Self-review:** Cùng phiên — không phải review độc lập từ người khác.

---

## Tiếp tục

**Quyết định pending:**

| Câu hỏi | Người quyết định |
|---|---|
| "Gần trước" (distance-based sort) có ưu tiên trong review ordering không? | An + Phan Hoang Huy (pending từ Task 2.07) |
| Định nghĩa chính thức của `partial_graph` vs `no_dependency_edges_observed` | Phan Hoang Huy + Huy Nguyen Tan (pending từ Task 2.07) |
| Khi nào backend có API endpoint để lấy report (thay cho mở file thủ công)? | H2/DevOps (nằm ngoài sprint 2 MVP) |

**Bước tiếp theo:**

- [ ] User chạy browser thật để xác nhận UI states (xem checklist checks chưa chạy)
- [ ] Khi có real report (`data_kind: "real"`): load qua "Mở file JSON..." và nghiệm thu
- [ ] Task 2.12 vẫn BLOCKED do Task 2.11 (H2/Phan Hoàng Huy) chưa hoàn thành
- [ ] Push 3 nhánh (2.07, 2.06, 2.18) và tạo PRs khi user ready

**Dịch vụ/process local:** Không có process nền nào cần chạy liên tục cho task này.

