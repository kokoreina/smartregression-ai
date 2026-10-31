# Repository Screening Checklist — Task 1.02 / PB23

**Cập nhật tích hợp 2026-10-24:** Python/pytest đã chốt ở ADR 0002; dataset target
và kiểm chứng candidate xem [evidence mới](candidate-evidence-20261024.md).
Các giả định pending D05 và target nguồn chưa xác minh bên dưới là snapshot cũ;
không dùng chúng thay quyết định/evidence mới. Nội dung tác giả và review gốc giữ nguyên.

**Trạng thái:** draft — chờ review của Nguyen Tan Huy.

**Đối chiếu 2026-10-31:** [PR #2](https://github.com/kokoreina/smartregression-ai/pull/2)
đã được `kokoreina` approve và merge. Đây là bằng chứng review bản gốc, không tự
phê duyệt các thay đổi mới. Candidate/runtime hiện hành ở
[candidate reproduction](candidate-reproduction.md); trạng thái sprint ở [review](review.md).
Các câu pending/"chưa review" bên dưới thuộc snapshot tác giả năm 2026-10-24.
**Author:** Dang Dai Viet
**AI hỗ trợ:** Antigravity IDE (Claude Sonnet 4.6 Thinking) hỗ trợ draft cấu trúc,
nội dung tiêu chí và phân loại lỗi.
**Reviewer đề xuất (task 1.02):** Nguyen Tan Huy review nội dung checklist này trước
khi Dang Dai Viet dùng làm cơ sở cho task 1.03.

---

## Giả định ghi rõ

| Giả định | Giá trị | Nguồn | Trạng thái |
|---|---|---|---|
| Dataset target | 50 cặp commit, tối thiểu 30 cặp | Proposal v1.4 §11.4; Project Plan §4.2 Table 15 — **cần xác minh số chính xác** | Mục tiêu chứ chưa phải dữ liệu đã thu thập |
| Fault-bearing cases | ≥15 ca lỗi có ground truth xác minh độc lập | Proposal v1.4 §11.4 — **cần xác minh** | Mục tiêu; chưa có ca lỗi nào được ghi nhận |
| Số repository tối thiểu | ≥2 repository riêng biệt | Proposal v1.4 §11.4 — **cần xác minh** | Mục tiêu |
| Ngôn ngữ | Python | **Giả định tạm thời — D05 chưa chốt** | Chờ nhóm xác nhận |
| Test framework | pytest | **Giả định tạm thời — D05 chưa chốt** | Chờ nhóm xác nhận |

> **Lưu ý:** Checklist này được soạn với giả định Python + pytest. Khi D05 được chốt,
> các mục đánh dấu `[D05]` cần xem lại. Không dùng checklist này để chọn
> ngôn ngữ/framework thay nhóm.

---

## Phần 1 — Tiêu chí nhận (tất cả phải đạt)

### 1.1 License và quyền sử dụng

| Mục kiểm tra | Cách kiểm tra | Ghi chú |
|---|---|---|
| License cho phép sử dụng cho nghiên cứu học thuật | Đọc file `LICENSE` hoặc `COPYING` tại root repo; tra cứu tại [choosealicense.com](https://choosealicense.com) hoặc [SPDX](https://spdx.org/licenses/) | Các license phù hợp điển hình: MIT, Apache-2.0, BSD-2/3-Clause, GPL (cần kiểm tra điều khoản phân phối), MPL-2.0. **Không giả định license từ tên tác giả hay ngôn ngữ.** |
| License không cấm dùng test suite hoặc commit history cho mục đích nghiên cứu | Đọc kỹ điều khoản; liên hệ tác giả nếu không rõ | Một số repo có license phần mềm khác với điều khoản dữ liệu |
| Repo không yêu cầu NDA hoặc thỏa thuận riêng để truy cập | Kiểm tra trang GitHub/GitLab | Repo private hoặc internal không dùng được nếu không có quyền |
| Ghi rõ SPDX identifier hoặc URL license đầy đủ | Lấy từ file LICENSE trong repo | Mọi repo được chọn phải có mục này điền đầy đủ |

**Nguồn bắt buộc:** URL đến file LICENSE cụ thể trong repo. Không được điền "MIT"
mà không có link dẫn chứng.

---

### 1.2 Lịch sử Git

*Tất cả ngưỡng trong mục này là **đề xuất**, không phải tiêu chí cứng để loại. Ghi
giá trị thực đo được và lý do nếu một repo không đạt ngưỡng nhưng vẫn được giữ lại.*

| Mục kiểm tra | Ngưỡng đề xuất, chờ nhóm duyệt | Cách kiểm tra |
|---|---|---|
| Số commit trong lịch sử | ≥100 commit (chỉ báo thô về kích thước) | `git log --oneline \| wc -l` hoặc GitHub Insights |
| Khoảng thời gian lịch sử | ≥6 tháng commit thực tế | `git log --format="%ad" --date=short` — xem ngày đầu và cuối |
| Có thể trích xuất cặp commit (base, target) hợp lệ | Cặp liền kề hoặc PR merge commit có thể dùng được | Kiểm tra bằng tay một vài cặp ứng viên |
| Không rewrite history hàng loạt sau ngày nhất định | Quan sát `git log --graph` | Force-push lớn làm mất tính nhất quán của cặp commit |
| **Ước lượng commit sửa lỗi có bằng chứng** (quan trọng hơn tổng số commit) | **≥8 commit/repo** (đề xuất, chờ nhóm duyệt) để có khả năng đạt ≥15 ca trên ≥2 repo | Tìm commit message có từ khoá `fix`, `bug`, `error`, `issue`, `closes #`; kiểm tra issue/PR được liên kết; đếm commit có evidence rõ ràng (không chỉ đếm từ khoá) |

> **Lưu ý về ước lượng commit sửa lỗi:** Tổng số commit không nói lên điều quan trọng;
> chỉ commit có thể truy vết tới issue/PR hoặc có commit message mô tả rõ lỗi mới đủ
> điều kiện làm ca lỗi. Cách ước lượng nhanh:
> ```
> git log --oneline --grep="fix" --grep="bug" --grep="closes" | wc -l
> ```
> Kết quả này chỉ là chặn dưới (nhiều ca lỗi không dùng từ khoá). Cần đọc thêm
> một mẫu commit để đánh giá chất lượng bằng chứng. Ghi rõ cách ước lượng và số
> thực tế trong hồ sơ repo.

> **Chưa kiểm chứng tự động:** Các con số trên cần được đo thực tế trên từng repo
> ứng viên trong task 1.03; không điền ước lượng từ trí nhớ.

---

### 1.3 Test suite có sẵn `[D05]`

| Mục kiểm tra | Yêu cầu | Ghi chú |
|---|---|---|
| Có file test được nhận ra bởi pytest | `pytest --collect-only` hoặc đọc cấu trúc thư mục | Chấp nhận `tests/`, `test_*.py`, `*_test.py` |
| Test có thể chạy tại đa số commit trong lịch sử | Kiểm tra một vài commit cũ xem test còn collect được không | Import errors do API thay đổi là rủi ro cần ghi nhận |
| Test IDs ổn định (không sinh ngẫu nhiên, không phụ thuộc trạng thái ngoài) | Chạy `pytest --collect-only -q` hai lần, so sánh | Stable IDs là điều kiện để SmartRegression tham chiếu test |
| Có ít nhất một test file có nội dung thực (không chỉ placeholder) | Đọc thủ công ≥3 file test | Placeholder repo không cung cấp được fault signal |
| **Thời gian chạy full suite ước tính** | Đề xuất <30 phút để feasible trong pipeline (chờ nhóm duyệt) | Chạy `pytest --co -q \| wc -l` để đếm test; ước tính wall-clock từ CI history hoặc chạy thử một phần |
| **Chạy được trên Windows** `[D05]` | Ưu tiên nếu runner của nhóm là Windows; ghi rõ nếu chỉ chạy được trên Linux/macOS | Kiểm tra CI config (os matrix), README, và chạy thử `pytest --collect-only` trên môi trường Windows nếu có thể |

> **Giả định tạm thời `[D05]`:** Mục này giả định pytest. Nếu D05 chọn framework khác,
> tiêu chí tương đương cần được định nghĩa lại trước khi dùng checklist.

---

### 1.4 Build và discovery có thể lặp lại

| Mục kiểm tra | Yêu cầu | Ghi chú |
|---|---|---|
| Có file dependency rõ ràng | `requirements.txt`, `pyproject.toml`, `setup.cfg`, hoặc tương đương | Thiếu dependency file là dấu hiệu môi trường không ổn định |
| Môi trường cài đặt được mô tả | README hoặc tài liệu có hướng dẫn setup | Không giả định môi trường ngầm định |
| Discovery không yêu cầu dịch vụ ngoài | `pytest --collect-only` không kết nối network, DB live, API bên ngoài | Nếu cần, ghi rõ dependency và xem đây là rủi ro |
| Đã kiểm chứng thực tế trên ít nhất 1 commit | Ghi rõ commit hash, output lệnh và môi trường | Không được điền "có thể chạy" mà chưa thử |

---

## Phần 2 — Tiêu chí loại (bất kỳ mục nào → loại ngay)

| Điều kiện loại | Lý do |
|---|---|
| License cấm nghiên cứu học thuật hoặc không có license rõ ràng | Rủi ro pháp lý |
| Repo private không có quyền truy cập được cấp | Không thể lấy commit history |
| Test suite không tồn tại hoặc toàn bộ là placeholder | Không có inventory để chọn |
| Test IDs không ổn định qua các lần chạy | SmartRegression không tham chiếu được |
| Lịch sử Git bị xóa/rewrite đến mức không còn commit pair hợp lệ | Không có dữ liệu huấn luyện/đánh giá |
| Repo đã ngưng hoạt động >3 năm và không có CI hiện hành | Build/discovery khó tái lập — ngưỡng 3 năm là đề xuất, chờ nhóm duyệt |

**Chuyển sang "cần kiểm thêm" (không loại ngay):**

| Điều kiện | Cách xử lý |
|---|---|
| Repo chỉ có ít contributor (kể cả 1 người) | Không loại ngay — kiểm tra xem có commit sửa lỗi truy vết được không; ground truth do reviewer độc lập xác nhận, không phụ thuộc số người đóng góp của repo |

---

## Phần 3 — Tiêu chí chất lượng (ưu tiên chọn)

*Đây là yếu tố xếp hạng giữa các repo đều vượt qua Phần 1 và Phần 2.*

| Yếu tố | Ưu tiên cao | Ưu tiên thấp |
|---|---|---|
| Số commit pair có thể trích xuất | >100 cặp ứng viên | 30–50 cặp |
| Tỷ lệ commit có thay đổi file Python (không chỉ docs/config) | >50% | <20% |
| Có CI history (GitHub Actions, Travis CI, v.v.) | Có — giúp xác định build đỏ/xanh | Không có |
| Có issue tracker liên kết commit với bug report | Có — hỗ trợ adjudication fault | Không có |
| Đa dạng loại thay đổi (thêm/sửa/xóa/rename) | Tốt cho test change impact | Chỉ thêm file mới |
| Được maintained tích cực (commit trong 12 tháng gần nhất) | Tốt | Đã archive |

---

## Phần 4 — Rủi ro data contamination

> **Lý do:** Các repo Python phổ biến trên GitHub (như `requests`, `flask`, `django`,
> `pytest` chính nó, `numpy`, v.v.) rất có thể **đã nằm trong dữ liệu huấn luyện của
> LLM** mà SmartRegression sử dụng. Điều này tạo ra rủi ro leakage: LLM có thể "biết"
> nội dung commit cụ thể, test name, hoặc bug description mà không phải nhờ khả năng
> phân tích thật sự.

### 4.1 Dấu hiệu rủi ro contamination cao

| Dấu hiệu | Ví dụ |
|---|---|
| Repo có >10.000 GitHub stars | Thư viện nổi tiếng rất có khả năng nằm trong corpus LLM |
| Tên repo/package phổ biến trong cộng đồng Python | `requests`, `flask`, `pandas`, v.v. |
| Repo được đề cập trong paper hoặc blog kỹ thuật lớn | Thường được crawl nhiều |
| Lịch sử commit có trong các dataset benchmark đã công bố (MSR, Defects4J) | Contamination trực tiếp |

### 4.2 Biện pháp giảm thiểu

| Biện pháp | Mô tả |
|---|---|
| Ghi rõ GitHub stars, ngày repo xuất hiện công khai lần đầu | Minh bạch để reviewer tự đánh giá rủi ro — **không dùng stars để loại repo** |
| Không dùng repo đã xuất hiện trong Defects4J, BugsInPy hoặc dataset benchmark tương tự | Tránh double-dipping với benchmark đã công bố |
| Chọn commit từ thời kỳ gần đây (sau cutoff huấn luyện LLM đã biết) | Cần biết cutoff của provider — **chưa xác định vì D06 pending** |
| Sau khi chọn provider (D06): kiểm tra documentation về training cutoff và exclusion list | Cần thực hiện trước khi finalize dataset |

> **Heuristic yếu:** Số stars chỉ là chỉ báo gián tiếp về contamination. Repo ít
> stars có thể vẫn bị contaminate nếu được đề cập trong paper hoặc được fork nhiều.
> Repo nhiều stars lại có thể có test suite và lịch sử lỗi phong phú hơn. Không
> dùng ngưỡng stars để loại — chỉ ghi vào hồ sơ để reviewer cân nhắc cùng với
> các chỉ báo khác.

> **Pending D06:** Cho đến khi provider LLM được chọn, không thể xác định training
> cutoff chính xác. Ghi mục này là **chưa kiểm chứng** trong mọi hồ sơ repo ứng viên.

### 4.3 Mục cần ghi trong hồ sơ từng repo

- Số GitHub stars tại thời điểm screening (kèm ngày và giờ ghi nhận)
- Ngày repo xuất hiện công khai lần đầu (ngày tạo trên GitHub)
- Có trong Defects4J / BugsInPy / dataset benchmark đã biết: có / không / chưa kiểm
- Đánh giá rủi ro contamination: Thấp / Trung bình / Cao (kèm lý do — reviewer tự cân nhắc)

---

## Phần 5 — Phân loại và ghi nguồn gốc ca lỗi

> **Nguyên tắc (rule 11):** Test fail không phải fault. Một fault có thể gây nhiều
> test fail. Mẫu số khi tính Fault Detection Retention là số **fault IDs** có ground
> truth độc lập, không phải số tests fail.

### 5.1 Bốn loại ca lỗi

| Loại | Định nghĩa | Nguồn ground truth | Lưu ý |
|---|---|---|---|
| **Real fault** | Lỗi trong source code được sửa bởi một commit cụ thể; có bằng chứng commit/issue/PR | Issue tracker + commit message + code diff | Adjudication cần **2 reviewer độc lập** xác nhận; xem mục 5.2 |
| **Mutation fault** | Lỗi nhân tạo được tạo bằng mutation operator | Operator + seed + commit snapshot | Cần lưu operator, seed và phiên bản tool. Tool ví dụ: mutmut, cosmic-ray — **chưa chọn tool cụ thể**. |
| **Flaky test** | Test fail không nhất quán giữa các lần chạy không đổi source | Chạy lặp lại ≥3 lần trên cùng commit | Ghi: số lần fail / tổng số lần chạy, môi trường. **Không đưa vào denominator fault.** |
| **Infrastructure failure** | Test fail do runner crash, timeout, network, permission, thiếu dependency | Log lỗi của runner | **Không gộp vào fault count** — báo riêng |

> **Ghi chú về mutation fault:** Trường `fault_type` với giá trị `real` và `mutation`
> khớp với thiết kế trường `case_origin` trong Database Design v1.5. Sprint 1 chưa tạo
> ca lỗi nào dù loại nào. Mutation testing tool (mutmut, cosmic-ray, v.v.) là ví dụ
> minh họa, chưa được nhóm chọn.

### 5.2 Template ghi nguồn gốc từng ca lỗi

Mỗi ca lỗi trong dataset phải có hồ sơ:

```
fault_id:            <chuỗi định danh duy nhất trong dataset>
fault_type:          real | mutation
partition:           pilot | held_out
repository:          <URL>
base_commit:         <full SHA-1 hoặc SHA-256>
target_commit:       <full SHA-1 hoặc SHA-256>
evidence_source:     <URL issue, URL PR, URL commit message>
reviewer_1:          <họ tên reviewer độc lập thứ nhất — không phải tác giả commit>
reviewer_2:          <họ tên reviewer độc lập thứ hai — không phải reviewer_1>
adjudication_date:   <YYYY-MM-DD>
disagreement_notes:  <mô tả bất đồng nếu có; "none" nếu cả hai đồng thuận>
failing_tests:       [<pytest nodeid 1>, <pytest nodeid 2>, ...]
notes:               <mô tả ngắn; ghi "chưa kiểm chứng" nếu chưa verify>
```

> **Adjudication 2 reviewer:**
> - `reviewer_1` và `reviewer_2` phải là hai người khác nhau, đều không phải tác giả
>   commit hoặc người tạo ca lỗi.
> - Nếu cả hai đồng thuận → ghi `disagreement_notes: none`.
> - Nếu bất đồng → ghi rõ điểm bất đồng vào `disagreement_notes`, thảo luận và ghi
>   quyết định cuối vào `notes`; không tự ý resolve mà không có cả hai đồng ý.
> - Sprint 1 chưa có ca lỗi nào dù loại nào — đây là template dùng từ Sprint sau.

### 5.3 Xử lý flaky test và infra failure

| Tình huống | Cách xử lý |
|---|---|
| Test fail không nhất quán | Chạy lại ≥3 lần; nếu xác nhận flaky → đánh dấu riêng, KHÔNG đưa vào denominator fault |
| Timeout chưa có verdict | Ghi là `excluded` với lý do; không gán outcome |
| Runner crash | Ghi là `infra_failure`; không tính vào test fail của fault |
| Build failure tại commit | Ghi là `build_excluded`; toàn bộ commit pair bị loại khỏi cohort |

### 5.4 Chia tập pilot và held-out

> **Lý do:** Tập held-out phải được đóng băng trước khi bất kỳ thành phần nào của
> SmartRegression (selector, prompt, threshold) được điều chỉnh, để tránh leakage.
> Tập pilot dùng để thử quy trình và phát hiện vấn đề sớm mà không "tiêu tốn" dữ liệu
> evaluation. Xem [evaluation-protocol.md](../evaluation-protocol.md) và rule 11.

| Tập | Mục đích | Thời điểm khoá | Ghi chú |
|---|---|---|---|
| **pilot** | Thử screening, adjudication, end-to-end và tuning | Khóa danh tính/split trước tuning; khóa prompt/policy sau pilot | Chỉ tuning trên pilot; không dùng held-out outcomes để tuning |
| **held_out** | Evaluation cuối kỳ, so sánh baseline | Khoá ngay khi tách — **không mở lại** | Không dùng để debug, tune hoặc xem cho đến khi evaluation chính thức |

**Quy trình chia tập (đề xuất):**

1. Sau khi có danh sách repo ứng viên (task 1.03), ước tính tổng số cặp commit có thể thu thập.
2. Quyết định tỷ lệ chia **trước** khi adjudication — ví dụ: 20% pilot, 80% held-out
   (tỷ lệ chính xác cần nhóm duyệt).
3. Chia theo **thời gian hoặc repo** (không phải ngẫu nhiên sau khi xem label) để tránh
   leakage thông tin về fault pattern.
4. Ghi `partition: pilot` hoặc `partition: held_out` vào template 5.2 **trước** khi
   bắt đầu adjudication từng ca.
5. Lưu mapping partition cùng với seed/ngày tách vào một file manifest riêng.

> **Sprint 1:** Chưa có dữ liệu để chia tập. Mục này là thiết kế protocol để thực
> hiện từ Sprint sau. Cần dự phòng đủ repo và cặp commit cho cả hai tập khi screening.

---

## Phần 6 — Mẫu hồ sơ repo ứng viên

*Điền mẫu này cho mỗi repo ứng viên trong task 1.03. Mọi ô phải có nguồn (URL) hoặc
ghi "chưa kiểm chứng".*

```markdown
## Hồ sơ repo: <tên>

| Mục | Giá trị | Nguồn/lệnh | Ngày kiểm tra |
|---|---|---|---|
| URL | | | |
| License (SPDX) | | <URL file LICENSE trong repo> | |
| Số stars GitHub | | <URL trang GitHub> | |
| Số commit (ước tính) | chưa kiểm chứng | git log --oneline \| wc -l | |
| Ngày commit đầu tiên | chưa kiểm chứng | git log --reverse --format="%ad" --date=short \| head -1 | |
| Ngày commit gần nhất | chưa kiểm chứng | git log -1 --format="%ad" --date=short | |
| Số file test tìm thấy | chưa kiểm chứng | find . -name "test_*.py" \| wc -l | |
| pytest collect OK? | Có / Không / Chưa thử | | |
| Test IDs ổn định? | Có / Không / Chưa thử | | |
| Có CI history? | Có / Không | | |
| Có issue tracker? | Có (GitHub Issues / ...) / Không | | |
| Trong Defects4J/BugsInPy? | Có / Không / Chưa kiểm | | |
| Rủi ro contamination | Thấp / Trung bình / Cao | <lý do> | |
| Số cặp commit ứng viên (ước tính) | chưa kiểm chứng | <phương pháp ước tính> | |
| Điều kiện loại nào vi phạm? | Không / <liệt kê> | | |
| Kết luận | Nhận / Loại / Cần kiểm thêm | <lý do ngắn> | |
```

---

## Phần 7 — Quy trình screening từng bước

1. **Kiểm tra license trước** — Loại ngay nếu không có license rõ ràng.
2. **Đọc README và cấu trúc thư mục** — Xác nhận có test suite.
3. **Chạy `pytest --collect-only`** tại một commit gần nhất — Ghi output thực tế.
4. **Xem lịch sử commit** — Ước tính số cặp ứng viên bằng lệnh thực.
5. **Đánh giá rủi ro contamination** — Tra số stars, kiểm tra Defects4J/BugsInPy.
6. **Điền mẫu hồ sơ** ở Phần 6 — Không điền ô nào thiếu nguồn.
7. **Kết luận: nhận / loại / cần kiểm thêm** — Kèm lý do cụ thể.
8. **Handoff cho reviewer** — Kèm output lệnh thực tế nếu đã chạy.

---

## Phần 8 — Những gì checklist này KHÔNG làm

- Không **chọn repo cuối cùng** — đó là quyết định của nhóm sau khi xem xét task 1.03.
- Không **gán nhãn fault** cho bất kỳ commit nào — adjudication cần reviewer độc lập.
- Không **xác nhận ngôn ngữ/framework đầu vào** — D05 vẫn là giả định chờ nhóm.
- Không **quyết định dataset target** — con số 50/30 đã được giao từ Proposal/Project Plan.
- Không **kiểm chứng rủi ro contamination LLM** — chưa có provider (D06 pending).

---

## Phần 9 — Nguồn tham khảo

| Nguồn | Phần liên quan | Ghi chú |
|---|---|---|
| Proposal v1.4 §11.4 | Dataset target, fault-bearing cases | Chưa có bằng chứng mentor approve phiên bản hiện hành |
| Project Plan v1.1 §4.2 Table 15 | Dataset 50 pairs | Xem mâu thuẫn với Proposal ở decision-register D09 |
| [docs/research/evaluation-protocol.md](../evaluation-protocol.md) | Phân loại fault, pipeline tách biệt | Phác thảo, chưa có kết quả |
| [docs/rules/11-research-evaluation.md](../../rules/11-research-evaluation.md) | Mẫu số, định nghĩa fault ID, tách loại lỗi | Quy ước dự án |
| [docs/development/decision-register.md](../../development/decision-register.md) | D05, D06, D09 | Các quyết định pending |
| [choosealicense.com](https://choosealicense.com) | So sánh license | Nguồn bên ngoài; truy cập 2026-10-22; không pin commit |
| [SPDX License List](https://spdx.org/licenses/) | SPDX identifiers | Nguồn bên ngoài; truy cập 2026-10-22; không pin commit |

> **Yêu cầu permalink cho LICENSE của repo ứng viên:** Link file LICENSE trong hồ sơ
> repo (Phần 6) phải là permalink cố định có SHA commit, ví dụ:
> `https://github.com/<owner>/<repo>/blob/<full-SHA>/LICENSE`
> Không dùng link nhánh (`/blob/main/LICENSE`) vì nội dung có thể thay đổi sau screening.

---

## AI use disclosure (rule 13)

File này được soạn với hỗ trợ của Antigravity IDE (Claude Sonnet 4.6 Thinking):

- **Giai đoạn:** Draft tài liệu, Sprint 1, task 1.02/PB23.
- **Phạm vi AI hỗ trợ:** Cấu trúc checklist, nội dung tiêu chí, phần phân loại lỗi
  và mẫu hồ sơ repo. AI đọc rule 06/11/13, evaluation-integrity skill và sprint guide
  để đối chiếu trước khi viết.
- **Phạm vi tác giả:** Dang Dai Viet cung cấp giả định tạm thời về dataset target
  (50/30 cặp — cần xác minh với Proposal) và giả định tạm thời về ngôn ngữ (Python +
  pytest — D05 chưa chốt); đọc, kiểm tra và chịu trách nhiệm nội dung.
- **Chưa được AI làm:** Kiểm chứng repo thực tế, chạy lệnh, tra license, đo số commit.
  Tất cả ô "chưa kiểm chứng" là thực sự chưa kiểm chứng — không phải placeholder giả.
- **Chưa có review độc lập** của thành viên khác tính đến thời điểm cập nhật file này.
