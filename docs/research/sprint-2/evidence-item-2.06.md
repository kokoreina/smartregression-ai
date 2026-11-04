# Evidence Item Component — Task 2.06

**Component:** `EvidenceItem`
**Author:** Dang Dai Viet (VI)
**Sprint:** 2 — Change impact + dependency analysis
**Role:** Frontend UI (VI 6h)
**Status:** Component completed & verified

---

## 1. Mục tiêu và phạm vi

Task 2.06 phân công:
- **H1 (6h):** Backend explanation payload, source verification / resolver, và contract integration.
- **VI (6h):** Individual evidence component (`EvidenceItem`) có khả năng tái sử dụng độc lập cho Task 2.18 và tích hợp trực tiếp vào màn hình báo cáo hiện tại.

Tài liệu này ghi lại chi tiết cài đặt và kiểm chứng của component `EvidenceItem`.

---

## 2. Thiết kế Component `EvidenceItem`

Component được đặt tại [`frontend/src/components/EvidenceItem.tsx`](../../frontend/src/components/EvidenceItem.tsx).

### 2.1 Hỗ trợ 2 thế hệ Contract (v1 Legacy & v2 Canonical)

Component hỗ trợ cả hai kiểu dữ liệu:
- **`StageEvidence` (v2 - Canonical contract):** chứa đầy đủ `location` (`SourceLocation`), `snapshot` (`SnapshotIdentity`), `resolution` (`resolved`, `missing`, `mismatched`, `unverified`), `support` (`supported`, `unsupported`, `unverified`), và `verification_reason`.
- **`EvidenceReference` (v1 - Legacy report):** chứa `line_start`, `line_end`, `commit`, `excerpt`, `symbol`.

Hàm `normalizeEvidence` trích xuất và chuẩn hóa trường dữ liệu một cách an toàn mà không làm gãy contract cũ hay mới.

### 2.2 Các trạng thái phân giải nguồn (Resolution Status)

| Trạng thái | Badge Text | Ký hiệu | Ý nghĩa |
|---|---|---|---|
| `resolved` | Đã xác minh nguồn | `✓` | Vị trí tệp và dòng khớp chính xác với snapshot đáng tin cậy |
| `missing` | Thiếu nguồn | `✗` | Tệp hoặc phạm vi dòng không tồn tại trong snapshot |
| `mismatched` | Nội dung lệch | `!` | Nội dung thực tế tại snapshot không khớp với excerpt |
| `unverified` | Chưa kiểm chứng nguồn | `?` | Chưa đối chiếu với snapshot tin cậy của repository |

### 2.3 Các trạng thái hỗ trợ kết luận (Support Status)

| Trạng thái | Badge Text | Ký hiệu | Ý nghĩa |
|---|---|---|---|
| `supported` | Hỗ trợ kết luận | `✓` | Bằng chứng chứng minh được nhận định ảnh hưởng |
| `unsupported` | Không hỗ trợ kết luận | `✗` | Bằng chứng không đủ cơ sở hỗ trợ nhận định ảnh hưởng |
| `unverified` | Chưa kiểm chứng kết luận | `?` | Chưa có kết quả kiểm chứng hỗ trợ cho nhận định này |

### 2.4 Tuân thủ Accessibility (A11y) & UI Design

Tuân thủ nghiêm ngặt các hướng dẫn từ skill `ui-design` và `accessibility-review`:
1. **Không phụ thuộc vào màu sắc đơn thuần:** Mỗi trạng thái badge đều có text rõ ràng kết hợp ký hiệu trực quan (`✓`, `✗`, `!`, `?`).
2. **Cấu trúc ngữ nghĩa (Semantic HTML):** Thẻ `<article>` có `aria-label`, header phân vùng danh tính và trạng thái, khu vực badge có `role="group"` và `role="status"`.
3. **Hiển thị thông tin hash an toàn:** Commit SHA dài được rút gọn hiển thị (10 ký tự) kèm tooltip `title` chứa full hash.
4. **Hiển thị lý do lỗi rõ ràng:** Khi có `verification_reason`, hiển thị khối ghi chú `role="note"` nổi bật.

---

## 3. Tích hợp và Tái sử dụng

- **Màn hình demo hiện tại:** Đã tích hợp trực tiếp vào [`frontend/src/features/reports/ReportView.tsx`](../../frontend/src/features/reports/ReportView.tsx), thay thế khối render inline bằng `<EvidenceItem key={item.id} evidence={item} />`.
- **Handoff cho Task 2.18:** Task 2.18 (Real-report loading/navigation/states) chỉ cần import và tái sử dụng component này, không phải viết lại logic hiển thị bằng chứng.
- **Handoff cho H1 (Task 2.06 Backend):** Khi backend source verifier của H1 hoàn thành và emit `StageEvidence`, frontend có thể truyền thẳng payload vào `EvidenceItem` mà không cần chỉnh sửa component.

---

## 4. Kết quả kiểm chứng kỹ thuật

- `npm run typecheck` (`tsc --noEmit`): **Passed (Exit code 0)**
- `npm run lint` (`eslint .`): **Passed (Exit code 0)**
- `npm run build` (`vite build`): **Passed (Exit code 0, 36 modules transformed)**
- `npm run contracts:check`: **Passed (Exit code 0)**
- `export_contracts.py --check`: **Passed (Exit code 0)**
- `pytest backend/tests/unit -q`: **Passed (497 passed in 18.16s)**

