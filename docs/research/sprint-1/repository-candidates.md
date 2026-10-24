# 1.03 — Danh sách Repository ứng viên (Candidate Repositories)

**Cập nhật tích hợp 2026-10-24:** xem [candidate evidence](candidate-evidence-20261024.md)
cho hai SHA/license đã đọc lại, hạn chế dependency, đề xuất chính/dự phòng và hiệu
chỉnh dataset target. Python/pytest đã accepted; các câu D05 chưa chốt bên dưới
thuộc snapshot draft cũ. Không diễn giải stars/contamination/50 pairs ở đây thành
kết quả đã xác minh mới hoặc dataset đã được chấp nhận.

**Trạng thái:** Draft — Đề xuất ứng viên, chờ kiểm chứng thực tế và nhóm duyệt D05  
**Author:** Dang Dai Viet (Dataset, Dashboard & Evaluation)  
**Reviewer đề xuất:** Do Ha An (Change Impact / Backend) & Nguyen Tan Huy (Research & Integration)  
**Tài liệu cơ sở:**
- [docs/research/sprint-1/repository-screening.md](repository-screening.md) (Checklist sàng lọc — Task 1.02)
- [docs/research/sprint-1/research-questions.md](research-questions.md) (Research Questions & Baselines — Task 1.01)
- [docs/research/evaluation-protocol.md](../evaluation-protocol.md) (Evaluation Protocol — Task 1.11)
- [docs/rules/11-research-evaluation.md](../../rules/11-research-evaluation.md) (Quy ước tính toán & liêm chính nghiên cứu)

---

## 1. Mục tiêu và Nguyên tắc sàng lọc

### 1.1 Mục tiêu
Đề xuất danh sách các repository nguồn mở ứng viên để:
1. Chuẩn bị nguồn dữ liệu thực nghiệm phục vụ việc trích xuất **target 50 cặp commit** (tối thiểu 30 cặp, với ≥15 ca lỗi trên ≥2 repository) theo Proposal v1.4 §11.4 *(cần xác minh)* và Project Plan v1.1 §4.2 *(cần xác minh)*.
2. Cung cấp đầu vào ứng viên cho Do Ha An (Task 1.06/1.07 — Revision semantics & Git diff spike) và Tran Hung Khanh (Task 1.05 — Test environment & runner).
3. Đảm bảo tính minh bạch, giấy phép rõ ràng và kiểm soát các rủi ro phương pháp luận (data contamination, quy mô test suite).

### 1.2 Giả định và Giới hạn (Bắt buộc tuân thủ)
- **Giả định ngôn ngữ & framework [D05]:** Toàn bộ ứng viên dưới đây được khảo sát theo giả định tạm thời **Python + pytest** (chờ nhóm chính thức chốt D05).
- **Không coi candidate là đã chọn:** Đây hoàn toàn là **danh sách đề xuất**, KHÔNG PHẢI quyết định cuối cùng. Nhóm cần thống nhất trước khi clone hoặc chạy mã nguồn.
- **Chưa chạy lệnh thực thi mã nguồn đầu vào:** Workspace hiện tại chưa clone và chưa chạy test của bất kỳ repo ứng viên nào. Các trạng thái về thời gian chạy test suite và tính tương thích nền tảng (Windows/Linux) ghi rõ là **chưa đo**, cần runner cô lập của Tran Hung Khanh (Task 1.05) đo đạc thực tế.

---

## 2. Tiêu chí Quy mô Test Suite và Vấn đề của Repo Nhỏ

Trong nghiên cứu Chọn lọc Kiểm thử Hồi quy (Regression Test Selection — RTS), việc đo lường mức tiết kiệm thời gian (**Time Saving**) và giảm thiểu test (**Test Reduction**) phụ thuộc trực tiếp vào kích thước của test suite:
- **Nguy cơ với repo quá nhỏ (ví dụ: TinyDB, humanize):**
  - TinyDB chỉ có khoảng 1.800 dòng code và 1.600 dòng test, dự án đang ở trạng thái bảo trì (*maintenance mode*).
  - humanize là thư viện tiện ích nhỏ với bộ test rất nhẹ.
  - Nếu test suite chạy quá nhanh (chỉ mất vài giây), việc áp dụng phân tích tĩnh, RAG và LLM để chọn tập con test sẽ tạo ra chi phí phân tích (**overhead**) lớn hơn rất nhiều so với thời gian chạy toàn bộ test suite. Khi đó, chỉ số **End-to-End Time Saving sẽ bị âm lớn hoặc trở thành nhiễu đo lường**.
- **Yêu cầu bổ sung ứng viên quy mô lớn hơn:**
  - Cần ít nhất một repository có quy mô trung bình/lớn (hàng chục file test, hàng trăm test cases, thời gian chạy đủ dài từ vài chục giây đến vài phút, cấu trúc phụ thuộc phức tạp hơn) để việc đánh giá RTS có ý nghĩa thực tế.
  - Do đó, tài liệu này bổ sung thêm ứng viên **`marshmallow-code/marshmallow`** bên cạnh `sqlparse`, `tinydb` và `humanize`.

---

## 3. Bảng tổng hợp các Repository ứng viên đề xuất

*Tất cả ứng viên ở trạng thái "Đề xuất, chờ kiểm chứng". Con số stars/commit lấy theo thời điểm kiểm tra qua GitHub API ngày 2026-10-24.*

| Repository ứng viên | Ngôn ngữ / Test framework | License (SPDX) | Stars GitHub | Commits toàn lịch sử | Cửa sổ commit đề xuất (Commit Range) | Rủi ro Contamination | Đánh giá quy mô test suite |
|---|---|---|---|---|---|---|---|
| [`msiemens/tinydb`](https://github.com/msiemens/tinydb) | Python / pytest | **MIT** | ~7.5k | ~750 | `v4.0.0` .. `HEAD` *(từ 05/2020)* | Chưa kiểm chứng | Nhỏ (~1.6k dòng test; có nguy cơ overhead > time saving) |
| [`andialbrecht/sqlparse`](https://github.com/andialbrecht/sqlparse) | Python / pytest | **BSD-3-Clause** | ~4.0k | ~1,390 | `0.4.0` .. `HEAD` *(từ 10/2020)* | Chưa kiểm chứng | Trung bình (12 file test cú pháp độc lập) |
| [`marshmallow-code/marshmallow`](https://github.com/marshmallow-code/marshmallow) | Python / pytest | **MIT** | ~7.2k | ~3,750 | `3.10.0` .. `dev` *(từ 12/2020)* | Chưa kiểm chứng | Đủ lớn (19 file test, hàng trăm test cases phức tạp) |
| [`python-humanize/humanize`](https://github.com/python-humanize/humanize) | Python / pytest | **MIT** | ~760 | ~1,100 | `4.0.0` .. `main` *(từ 2022)* | Chưa kiểm chứng | Nhỏ (7 file test tiện ích cơ bản) |

---

## 4. Hồ sơ chi tiết từng Repository ứng viên

*(Điền theo mẫu Phần 6 của checklist 1.02; mọi ô chưa kiểm chứng ghi rõ chưa kiểm chứng)*

### 4.1 Hồ sơ repo: `msiemens/tinydb`

*Thư viện cơ sở dữ liệu hướng tài liệu thuần Python, tối giản.*

| Mục | Giá trị | Nguồn / Lệnh kiểm tra | Ngày kiểm tra |
|---|---|---|---|
| **URL** | `https://github.com/msiemens/tinydb` | GitHub Repository | 2026-10-24 |
| **License (SPDX)** | **MIT** | [Permalink LICENSE](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/LICENSE) *(SHA: `edff96aeb2616402e9489d46e90a592c05565621`)* | 2026-10-24 |
| **Số stars GitHub** | 7,574 | GitHub API (`stargazers_count`) | 2026-10-24 |
| **Ngày tạo repo (created_at)** | 2013-07-12 | GitHub API | 2026-10-24 |
| **Lần push gần nhất (pushed_at)** | 2026-10-15 | GitHub API | 2026-10-24 |
| **Số commit (toàn lịch sử)** | ~750 commits (chính xác tùy thời điểm đếm) | GitHub Commits API Link header | 2026-10-24 |
| **Cửa sổ commit đề xuất** | **Từ tag `v4.0.0` (`69e96f1`, 05/2020) đến `HEAD`** | Lý do: Lịch sử repo từ 2013, các commit trước v4.0.0 phụ thuộc Python 2.7/3.4 không thể chạy trên môi trường Python hiện đại. Chỉ cửa sổ từ v4.0.0 trở đi mới chạy được. | 2026-10-24 |
| **Số file test tìm thấy** | 9 file test trong `tests/` (`test_tinydb.py`, `test_queries.py`, `test_storages.py`,...) | GitHub Git Trees API | 2026-10-24 |
| **pytest collect OK?** | **Chưa chạy** (quan sát có file `pytest.ini` và thư mục `tests/`; chưa chạy thực tế trong runner) | Cần runner cô lập thực hiện | 2026-10-24 |
| **Test IDs ổn định?** | **Chưa chạy kiểm tra** | Cần runner cô lập thực hiện | 2026-10-24 |
| **Thời gian chạy test suite** | **Chưa đo** (chưa clone và chưa chạy trong runner) | Cần runner cô lập đo đạc | 2026-10-24 |
| **Có CI history?** | Có (GitHub Actions workflows) | `.github/workflows/` | 2026-10-24 |
| **Có issue tracker?** | Có (GitHub Issues) | GitHub API (`open_issues_count`) | 2026-10-24 |
| **Trong Defects4J/BugsInPy?** | Không | Đối chiếu 17 dự án BugsInPy | 2026-10-24 |
| **Rủi ro contamination** | **Chưa kiểm chứng** (Stars chỉ là chỉ báo yếu; LLM có thể đã thấy mã nguồn public). Giảm thiểu: Ưu tiên chọn commit mới hoặc sau cutoff của model. | Đánh giá rủi ro LLM | 2026-10-24 |
| **Số cặp commit ứng viên (ước tính)** | **Chưa xác minh** (chưa có danh sách commit/issue cụ thể). Dự án đang ở *maintenance mode*, số ca lỗi trong cửa sổ v4.0.0 có thể hạn chế. | Cần rà soát Git log cụ thể | 2026-10-24 |
| **Điều kiện loại nào vi phạm?** | Cần xem xét: Quy mô test suite quá nhỏ có thể làm nhiễu chỉ số Time Saving. | Nhận xét quy mô | 2026-10-24 |
| **Kết luận** | **Đề xuất, chờ kiểm chứng** | Thư viện thuần Python không cần DB server, nhưng cần kiểm chứng quy mô test và số ca lỗi trong cửa sổ v4.0.0. | 2026-10-24 |

---

### 4.2 Hồ sơ repo: `andialbrecht/sqlparse`

*Thư viện phân tích cú pháp SQL thuần Python.*

| Mục | Giá trị | Nguồn / Lệnh kiểm tra | Ngày kiểm tra |
|---|---|---|---|
| **URL** | `https://github.com/andialbrecht/sqlparse` | GitHub Repository | 2026-10-24 |
| **License (SPDX)** | **BSD-3-Clause** | [Permalink LICENSE](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/LICENSE) *(SHA: `60cdc649726bf1bc4f1b336050560b336da715ec`)* | 2026-10-24 |
| **Số stars GitHub** | 4,023 | GitHub API (`stargazers_count`) | 2026-10-24 |
| **Ngày tạo repo (created_at)** | 2012-04-18 | GitHub API | 2026-10-24 |
| **Lần push gần nhất (pushed_at)** | 2026-08-13 | GitHub API | 2026-10-24 |
| **Số commit (toàn lịch sử)** | ~1,390 commits | GitHub Commits API Link header | 2026-10-24 |
| **Cửa sổ commit đề xuất** | **Từ tag `0.4.0` (`d8ea71b`, 10/2020) đến `HEAD`** | Lý do: Bản 0.4.0 loại bỏ hỗ trợ Python cũ, chuẩn hóa chạy trên Python 3.8+. | 2026-10-24 |
| **Số file test tìm thấy** | 12 file test trong `tests/` (`test_parse.py`, `test_format.py`, `test_split.py`,...) | GitHub Git Trees API | 2026-10-24 |
| **pytest collect OK?** | **Chưa chạy** (quan sát có tài liệu hướng dẫn pytest và thư mục `tests/`) | Cần runner cô lập thực hiện | 2026-10-24 |
| **Test IDs ổn định?** | **Chưa chạy kiểm tra** | Cần runner cô lập thực hiện | 2026-10-24 |
| **Thời gian chạy test suite** | **Chưa đo** | Cần runner cô lập đo đạc | 2026-10-24 |
| **Có CI history?** | Có (GitHub Actions workflows ma trận Python) | `.github/workflows/` | 2026-10-24 |
| **Có issue tracker?** | Có (GitHub Issues: >300 open issues, nhiều PR) | GitHub API (`open_issues_count`) | 2026-10-24 |
| **Trong Defects4J/BugsInPy?** | Không | Đối chiếu 17 dự án BugsInPy | 2026-10-24 |
| **Rủi ro contamination** | **Chưa kiểm chứng** | Giảm thiểu bằng commit range gần đây | 2026-10-24 |
| **Số cặp commit ứng viên (ước tính)** | **Chưa xác minh** (cần trích xuất danh sách SHA và issue cụ thể trong cửa sổ 0.4.0). | Cần rà soát Git log cụ thể | 2026-10-24 |
| **Điều kiện loại nào vi phạm?** | Chưa phát hiện vi phạm tiêu chí nhận | Checklist 1.02 | 2026-10-24 |
| **Kết luận** | **Đề xuất, chờ kiểm chứng** | Ứng viên sáng giá do các module cú pháp phân tách độc lập (lex/parse/format), rất phù hợp với bài toán change impact. | 2026-10-24 |

---

### 4.3 Hồ sơ repo: `marshmallow-code/marshmallow`

*Thư viện chuyển đổi và kiểm thực dữ liệu (Serialization/Deserialization & Validation) rất phổ biến, có cấu trúc phức tạp và test suite phong phú.*

| Mục | Giá trị | Nguồn / Lệnh kiểm tra | Ngày kiểm tra |
|---|---|---|---|
| **URL** | `https://github.com/marshmallow-code/marshmallow` | GitHub Repository | 2026-10-24 |
| **License (SPDX)** | **MIT** | [Permalink LICENSE](https://github.com/marshmallow-code/marshmallow/blob/b762ea2d59ca52fe5df76b90de14bed7e5ec5607/LICENSE) *(SHA: `b762ea2d59ca52fe5df76b90de14bed7e5ec5607`)* | 2026-10-24 |
| **Số stars GitHub** | 7,246 | GitHub API (`stargazers_count`) | 2026-10-24 |
| **Ngày tạo repo (created_at)** | 2013-11-10 | GitHub API | 2026-10-24 |
| **Lần push gần nhất (pushed_at)** | 2026-10-23 | GitHub API | 2026-10-24 |
| **Số commit (toàn lịch sử)** | ~3,750 commits | GitHub Commits API Link header | 2026-10-24 |
| **Cửa sổ commit đề xuất** | **Từ tag `3.10.0` (12/2020) đến `dev`** | Lý do: Bản 3.x ổn định, chạy trên Python 3.8+, lịch sử commit sửa lỗi validation phong phú. | 2026-10-24 |
| **Số file test tìm thấy** | 19 file test trong `tests/` (`test_schema.py`, `test_fields.py`, `test_validation.py`,...) | GitHub Git Trees API | 2026-10-24 |
| **pytest collect OK?** | **Chưa chạy** (quan sát có `pytest` trong cấu hình dev dependencies) | Cần runner cô lập thực hiện | 2026-10-24 |
| **Test IDs ổn định?** | **Chưa chạy kiểm tra** | Cần runner cô lập thực hiện | 2026-10-24 |
| **Thời gian chạy test suite** | **Chưa đo** (dự kiến dài hơn đáng kể so với tinydb/humanize do số lượng test lớn) | Cần runner cô lập đo đạc | 2026-10-24 |
| **Có CI history?** | Có (GitHub Actions workflows) | `.github/workflows/` | 2026-10-24 |
| **Có issue tracker?** | Có (GitHub Issues: 161 open issues) | GitHub API (`open_issues_count`) | 2026-10-24 |
| **Trong Defects4J/BugsInPy?** | Không | Đối chiếu 17 dự án BugsInPy | 2026-10-24 |
| **Rủi ro contamination** | **Chưa kiểm chứng** | Giảm thiểu bằng commit range gần đây | 2026-10-24 |
| **Số cặp commit ứng viên (ước tính)** | **Chưa xác minh** (tiềm năng cao do số lượng closed PR sửa lỗi rất lớn). | Cần rà soát Git log cụ thể | 2026-10-24 |
| **Điều kiện loại nào vi phạm?** | Chưa phát hiện vi phạm tiêu chí nhận | Checklist 1.02 | 2026-10-24 |
| **Kết luận** | **Đề xuất, chờ kiểm chứng** | Đạt yêu cầu về quy mô: test suite đủ lớn, cấu trúc phụ thuộc phức tạp giữa schemas và fields, giúp việc đánh giá Test Reduction và Time Saving có ý nghĩa thực tế. | 2026-10-24 |

---

### 4.4 Hồ sơ repo: `python-humanize/humanize`

*Thư viện tiện ích chuyển đổi số và thời gian sang dạng đọc cho người.*

| Mục | Giá trị | Nguồn / Lệnh kiểm tra | Ngày kiểm tra |
|---|---|---|---|
| **URL** | `https://github.com/python-humanize/humanize` | GitHub Repository | 2026-10-24 |
| **License (SPDX)** | **MIT** | [Permalink LICENCE](https://github.com/python-humanize/humanize/blob/a2006eabf832081cc60d8579d9d53789ed8d8d0b/LICENCE) *(SHA: `a2006eabf832081cc60d8579d9d53789ed8d8d0b`)* | 2026-10-24 |
| **Số stars GitHub** | 765 | GitHub API (`stargazers_count`) | 2026-10-24 |
| **Ngày tạo repo (created_at)** | 2022-03-06 *(chuyển sang org python-humanize)* | GitHub API | 2026-10-24 |
| **Lần push gần nhất (pushed_at)** | 2026-10-22 | GitHub API | 2026-10-24 |
| **Số commit (toàn lịch sử)** | ~1,100 commits | GitHub Commits API Link header | 2026-10-24 |
| **Cửa sổ commit đề xuất** | **Từ tag `4.0.0` (2022) đến `main`** | Lý do: Giai đoạn chuẩn hóa trên org mới, hỗ trợ Python 3.8+ / 3.11+. | 2026-10-24 |
| **Số file test tìm thấy** | 7 file test trong `tests/` (`test_filesize.py`, `test_number.py`,...) | GitHub Git Trees API | 2026-10-24 |
| **pytest collect OK?** | **Chưa chạy** (khai báo `pytest>=9` trong `pyproject.toml`) | Cần runner cô lập thực hiện | 2026-10-24 |
| **Test IDs ổn định?** | **Chưa chạy kiểm tra** | Cần runner cô lập thực hiện | 2026-10-24 |
| **Thời gian chạy test suite** | **Chưa đo** | Cần runner cô lập đo đạc | 2026-10-24 |
| **Có CI history?** | Có (GitHub Actions) | `.github/workflows/` | 2026-10-24 |
| **Có issue tracker?** | Có (GitHub Issues) | GitHub API (`open_issues_count`) | 2026-10-24 |
| **Trong Defects4J/BugsInPy?** | Không | Đối chiếu 17 dự án BugsInPy | 2026-10-24 |
| **Rủi ro contamination** | **Chưa kiểm chứng** (Stars thấp <1k nhưng vẫn là repo public) | Giảm thiểu bằng commit range gần đây | 2026-10-24 |
| **Số cặp commit ứng viên (ước tính)** | **Chưa xác minh** | Cần rà soát Git log cụ thể | 2026-10-24 |
| **Điều kiện loại nào vi phạm?** | Cần xem xét: Quy mô test suite nhỏ | Nhận xét quy mô | 2026-10-24 |
| **Kết luận** | **Đề xuất, chờ kiểm chứng** | Thích hợp làm ứng viên dự phòng hoặc làm bộ kiểm chứng bổ trợ; không nên làm ứng viên chính duy nhất do test suite nhỏ. | 2026-10-24 |

---

## 5. Phân tích Đánh đổi về Rủi ro Contamination và Benchmark Sẵn có

Khi lựa chọn dataset thực nghiệm, nhóm cần cân nhắc sự đánh đổi (trade-off) quan trọng:
1. **Repository nguồn mở tự nhiên (In-the-wild repositories như trên):**
   - *Ưu điểm:* Không bị đóng gói sẵn vào các benchmark LLM nổi tiếng, giảm nguy cơ model đã học thuộc giải pháp kiểm thử từ các bài báo khoa học.
   - *Thách thức:* **Tốn công sức xác minh ground truth**. Nhóm phải tự thực hiện quy trình 2 reviewer độc lập để kiểm chứng từng commit sửa lỗi, xác nhận test fail trên commit lỗi và test pass sau khi fix.
2. **Benchmark đã công bố (ví dụ: BugsInPy):**
   - *Ưu điểm:* Đã có sẵn 493 ca lỗi thật kèm reproducible environment và test outcomes đã kiểm chứng.
   - *Thách thức:* Rủi ro contamination rất cao vì BugsInPy là một trong những benchmark phổ biến nhất trong các nghiên cứu đánh giá LLM cho Python.
- **Khuyến nghị cho nhóm:** Giữ nguyên phương án khảo sát repo tự nhiên, và sử dụng commit range gần đây (sau ngày cutoff dữ liệu huấn luyện của LLM) để giảm thiểu rủi ro contamination.

---

## 6. Đề xuất sơ bộ gửi Nguyen Tan Huy (chủ trì Task 1.11 — Evaluation Protocol)

*Nội dung này là đề xuất phối hợp, không phải quyết định độc lập của Task 1.03:*
- **Về mục tiêu mẫu:** Proposal §11.4 đặt mục tiêu 50 cặp commit (tối thiểu 30 cặp có ≥15 ca lỗi trên ≥2 repo). Để đạt con số này một cách trung thực, cần trích xuất danh sách commit SHA cụ thể từ ít nhất 2 repo có quy mô đủ lớn (ví dụ: `sqlparse` và `marshmallow`, kết hợp `tinydb`).
- **Về phân chia Pilot / Held-out:** Đề xuất Nguyen Tan Huy xem xét phân chia tập Pilot (~20%) và Held-out (~80%) theo nguyên tắc:
  - Phân chia theo mốc thời gian commit (các commit cũ hơn trong commit range dùng cho Pilot; các commit mới nhất dùng cho Held-out).
  - Khóa (freeze) danh sách SHA và test inventory của từng tập trước khi chạy selector.

---

## 7. Những gì tài liệu này KHÔNG làm

Tuân thủ [Rule 00 — Governance](../../rules/00-governance.md) và [Rule 11 — Research/Evaluation](../../rules/11-research-evaluation.md):
- **Không tự ý chốt quyết định ngôn ngữ:** D05 vẫn là giả định đề xuất, cần sự đồng thuận của cả nhóm.
- **Không tự ý clone hay chạy mã nguồn trong workspace:** Đợi runner cô lập do Tran Hung Khanh thiết kế (Task 1.05 / Gate G1).
- **Không khẳng định đạt target sample size khi chưa có danh sách SHA:** Số lượng 50 cặp hay 15 ca lỗi chỉ là mục tiêu đề xuất, chưa phải dữ liệu đã thu thập.
- **Không đưa ra kết luận "Nhận" chính thức:** Mọi ứng viên đều dừng ở mức "Đề xuất, chờ kiểm chứng".

---

## 8. Nguồn lệnh có thể tái lập (Reproducible API Commands)

Bất kỳ thành viên nào cũng có thể kiểm chứng lại các con số GitHub bằng lệnh Python:

```python
import urllib.request, json, re


def check_repo(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}", headers={"User-Agent": "Mozilla/5.0"}
    )
    r = json.loads(urllib.request.urlopen(req).read())
    # Lấy số trang commit cuối cùng
    c_req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/commits?per_page=1",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    link = urllib.request.urlopen(c_req).headers.get("Link", "")
    m = re.search(r'page=(\d+)>; rel="last"', link)
    commits = m.group(1) if m else "N/A"
    print(
        f"[{repo}] Stars: {r['stargazers_count']} | Created: {r['created_at']} | Pushed: {r['pushed_at']} | License: {r.get('license', {}).get('spdx_id')} | Commits: {commits}"
    )


for r in [
    "msiemens/tinydb",
    "andialbrecht/sqlparse",
    "marshmallow-code/marshmallow",
    "python-humanize/humanize",
]:
    check_repo(r)
```

---

## 9. AI Use Disclosure (tuân thủ Rule 13)

File này được soạn thảo với sự hỗ trợ của Antigravity IDE:
- **Phạm vi AI hỗ trợ:** Hỗ trợ chạy script truy vấn GitHub API để lấy dữ liệu số stars, created_at, pushed_at, commit count và permalink file LICENSE; hỗ trợ định dạng cấu trúc Markdown theo mẫu hồ sơ repo của Task 1.02.
- **Phạm vi rà soát và kiểm soát của tác giả (Dang Dai Viet):** 
  - Tác giả đã kiểm tra thực tế, phát hiện và chỉ ra các điểm lệch số liệu, các khẳng định thiếu căn cứ về thời gian chạy test / độ ổn định nền tảng trong bản thảo trước.
  - Tác giả yêu cầu xóa bỏ toàn bộ kết luận "Nhận" quá sớm, chuyển sang "Đề xuất, chờ kiểm chứng", bổ sung phân tích về nguy cơ repo quá nhỏ đối với RTS, yêu cầu bổ sung commit range khả thi và ứng viên có quy mô test suite lớn hơn (`marshmallow`).
- **Trạng thái review:** Bản draft này được hoàn thiện dựa trên phản hồi chi tiết của tác giả Dang Dai Viet; chưa có review độc lập của các thành viên khác trong nhóm tại thời điểm cập nhật file này.
