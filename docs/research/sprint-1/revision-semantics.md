# Task 1.06 — Quy tắc xác định phiên bản phân tích

**Trạng thái: draft / proposed, chờ nhóm review.** Ngày soạn: 2026-10-24.
Task thuộc PB03; owner ghi trong workbook là **Do Ha An**. Reviewer 1.06 được
guide đề xuất là **Nguyen Tan Huy**, chưa có xác nhận review cho bản này. [S4] [S5]

Tài liệu trả lời ba câu hỏi: so sánh commit nào với commit nào, giữ kết quả đúng
phiên bản khi PR thay đổi ra sao, và đọc bằng chứng ở phiên bản nào. Đây là đầu
vào thiết kế cho 1.07; chưa phải implementation hoặc kết quả spike đã chạy.

## 1. Phạm vi và cách đọc trạng thái

- **Có trong nguồn:** yêu cầu đã được viết trong tài liệu nhóm. Cụm này không có
  nghĩa nhóm hoặc mentor đã phê duyệt bản hiện hành.
- **Proposed:** cách cụ thể hóa do draft này đề xuất, cần người có trách nhiệm chốt.
- **Pending:** chưa có xác nhận hoặc chưa đủ dữ liệu để quyết định.
- Bản này chưa ghi quyết định nào là `accepted`. D05 trong decision register vẫn
  `pending`; việc có mô tả trong Proposal không tự đóng D05. [S6]

Phạm vi 1.06 là repository identity, cặp revision, PR snapshot và quy tắc evidence.
1.07 chỉ spike Git diff mức file trên fixture do task tạo hoặc được phép dùng.
Không chọn parser/ngôn ngữ đầu vào, tạo DB/worker, sửa contract hay chạy code/test
của repository đầu vào. Draft 1.06 không cần chờ 1.04 hoàn thành. [S5]

User đã giao soạn draft này. Việc nhóm chấp nhận scope, reviewer và xác nhận không
có writer khác trên các paths liên quan vẫn `pending`; Git status cục bộ không
chứng minh tình trạng làm việc của đồng đội.

## 2. Nguồn và yêu cầu đã được viết

| Nguồn | Vị trí để người review tìm lại | Nội dung liên quan |
| --- | --- | --- |
| [S1 — Proposal v1.4](../../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx) | §7, FR-03; BR-02; NFR-05; §12.6 | PR mặc định dùng merge-base/head; khóa SHA; head mới cần run mới; giữ đúng phiên bản; xét base và target cho code xóa/đổi tên |
| [S2 — Architecture v1.3](<../../../C1.SE26_DOCUMENTS/C1SE26_Architecture_v1.3 (1).docx>) | §2.2; §4.1 bước 1–3; §5.2 nguyên tắc dữ liệu | Resolve commit pair hoặc PR merge-base/head, lưu cặp SHA và dùng snapshot đã khóa |
| [S3 — Database v1.5](../../../C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx) | §1.4 Definitions, Acronyms and Abbreviations; §2.4.5 `analysis_runs`; §3.4.1 `changed_files`; §3.4.5 `evidence_references` | Full commit ID 40/64 hex; PR dùng merge-base/head; head mới tạo run mới; quy tắc old/new path và evidence |
| [S4 — Scrum workbook v1.4](../../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx) | `Sprint 1 Backlog!B13:G14`; `Product Backlog!B10:H10` | 1.06: revision/SHA freezing, 8h; 1.07: diff/file metadata, 14h; PB03 truy vết FR-03 |
| [S5 — Guide Sprint 1](../../development/sprint-1-team-guide.md) | §3 bảng task; §5 phối hợp; §8 ví dụ Do Ha An | Draft độc lập, phối hợp 1.04; 1.07 đợi semantics đủ rõ, dùng fixture riêng và giữ contract |
| [S6 — Decision register](../../development/decision-register.md) | D03, D05 và quy ước trạng thái | Contract bootstrap là nguồn chuẩn; PR semantics còn pending ở chỉ mục quyết định |
| [S7 — Backend contract](../../../backend/src/smartregression/contracts/models.py) | `Commit`, `CommitPair`, `AnalysisRequest`, `ChangedComponent`, `EvidenceReference`, `AnalysisReport` | Shape hiện hành và giới hạn biểu diễn |
| [S8 — Rule 09](../../rules/09-impact-selection.md) | Yêu cầu và ví dụ | Full SHA, semantics rõ, evidence deleted ở base, inventory ở target |
| [S9 — Rule 03](../../rules/03-contracts-api.md) | Contracts/API | Phân biệt repo/revision/run; không sửa generated artifacts hoặc schema tùy ý |

Ngày đối chiếu: 2026-10-24. Năm file Office trong `C1.SE26_DOCUMENTS/` đã được
so sánh SHA-256 và trùng byte với năm file user cung cấp ngoài workspace. Nội dung
liên quan được đọc từ text/bảng DOCX và ô XLSX; chưa kiểm layout, sơ đồ nhúng,
comments hay tính lại công thức Excel. Không dùng số trang chưa được kiểm chứng.

## 3. Thuật ngữ bằng ví dụ

| Thuật ngữ | Nghĩa dùng trong draft |
| --- | --- |
| Repository identity | Danh tính repository được phép phân tích; khác đường dẫn thư mục local |
| Ref | Tên trỏ đến phiên bản, ví dụ branch `main` hoặc tag `v1.0`; tên có thể trỏ sang commit khác |
| Full SHA | Mã commit đầy đủ, 40 hoặc 64 ký tự hex theo contract; phải kiểm tra commit tồn tại |
| Base | Snapshot trước dùng để so sánh; không luôn là đầu nhánh đích |
| Target | Snapshot sau dùng để so sánh, cũng là phiên bản inventory test theo rule 09 |
| Merge-base | Tổ tiên chung tốt nhất của hai commit theo quan hệ lịch sử Git |
| Frozen SHA | SHA đã khóa cho một lần phân tích; không resolve lại ref giữa các bước |
| Evidence | Bằng chứng gắn commit, path và dòng có thật; đúng JSON chưa chứng minh nội dung đúng |

Git có thể có nhiều merge-base cho cùng một cặp commit. Đây là lý do cần policy
riêng, thay vì mặc định lấy một kết quả bất kỳ. [G2]

## 4. Hai commit được chỉ định

**Proposed — Q02/Q03:** với yêu cầu so sánh hai revision, `base_sha` là commit
resolve từ input base; `target_sha` là commit resolve từ input target. Đọc chênh
lệch giữa hai cây file này. Không tự đổi base thành parent hay merge-base.

Ví dụ input là tag `v1.0` và branch `feature/login`: resolve cả hai thành commit
đầy đủ một lần, sau đó chỉ dùng hai SHA kết quả. Ref là đầu vào của bước resolve;
`AnalysisRequest.commits` hiện chỉ nhận full SHA, không nhận branch/tag. [S7]

Đề xuất cho spike:

- Hai commit không bắt buộc có quan hệ tổ tiên; direct diff vẫn là so sánh hai cây
  file đã chỉ định. Không tự diễn giải thành thay đổi riêng của một PR. [G1]
- Base bằng target là cặp hợp lệ, trả không có thay đổi file. Điều này không có
  nghĩa test đã pass hoặc không có rủi ro regression.
- Nếu target là merge commit do user chỉ định, vẫn so trực tiếp với base đã chọn;
  không tự chọn parent thứ nhất hoặc tạo combined diff.

## 5. PR dùng merge-base và PR head

**Có trong nguồn:** FR-03 đã quy định mặc định PR là merge-base → PR head. BR-02
giữ kết quả cũ tại commit cũ. Architecture và Database mô tả cùng hướng. [S1] [S2] [S3]

**Proposed — Q01/Q02:** áp dụng yêu cầu đó cho 1.07 bằng cách phân biệt:

| Tên | Giá trị |
| --- | --- |
| `base_tip_sha` | Đầu nhánh đích được ghi nhận cho lần resolve PR này |
| `pr_head_sha` | Đầu nhánh PR được ghi nhận cho lần resolve PR này |
| `base_sha` | Merge-base duy nhất của `base_tip_sha` và `pr_head_sha` |
| `target_sha` | Chính `pr_head_sha` |

Đây là tên giải thích trong draft, chưa phải fields mới được thêm vào contract.
`CommitPair.base/target` được đề xuất lưu **cặp thực sự dùng để diff**, tức
`base_sha/target_sha`; không thay `base` bằng `base_tip_sha`. [S7]

Ví dụ minh họa, các chữ là nhãn commit, không phải SHA đầu vào hợp lệ:

```text
      B---C       đầu nhánh đích
     /
A---+
     \
      D---E       PR head

base_tip_sha = C
pr_head_sha  = E
base_sha     = A
target_sha   = E
```

Direct diff `C → E` so hai đầu nhánh. Policy PR của tài liệu nhóm so `A → E`.
Không dùng commit merge thử do nền tảng CI tạo làm target mặc định. Git mô tả
so sánh từ merge-base tới đầu nhánh qua three-dot diff; draft đề xuất tính ra SHA
base trước rồi diff bằng cặp SHA tường minh để có thể truy vết. [G1]

**Proposed — Q04:** đọc toàn bộ kết quả merge-base. Chỉ tiếp tục nếu có đúng một
kết quả và đủ history để xác định kết quả đó. Không có tổ tiên chung, history
thiếu, nhiều merge-base hoặc lỗi Git đều phải báo rõ. Không tự chuyển sang direct
diff, dùng empty tree hoặc tạo virtual merge commit. Với shallow history, đề xuất
dừng bước resolve PR cho đến khi bên cung cấp repository bổ sung history. [G2]

## 6. Resolve và kiểm tra SHA trước phân tích

**Proposed — Q02/Q03:** dùng trình tự dưới đây cho mỗi yêu cầu:

1. Nhận repository identity đã được xác thực quyền và liên kết tới repository
   local được phép đọc. Không suy ra quyền truy cập từ một tên repo hợp lệ.
2. Phân biệt input là full SHA, branch hay tag. Branch/tag cần namespace rõ như
   `refs/heads/...`, `refs/tags/...` hoặc mapping upstream đã thống nhất; từ chối
   tên mơ hồ. Spike không nhận short SHA hoặc biểu thức revision tùy ý.
3. Resolve branch/tag thành commit đầy đủ. Annotated tag phải được peel tới
   commit; tag trỏ blob/tree bị từ chối. Git có cơ chế kiểm tra commit-ish bằng
   `^{commit}`; input không tin cậy phải được truyền như dữ liệu, tránh nhầm option. [G3]
4. Kiểm tra kết quả là full SHA chữ thường dài 40/64 theo `Commit`; object tồn tại
   và thực sự trỏ tới commit trong repository đang xử lý. Đúng regex chưa đủ. [S7]
5. Với PR, xác định thêm merge-base theo mục 5. Chỉ khóa cặp SHA sau khi bước này
   thành công; lưu repository identity cùng cặp SHA.
6. Các consumer nhận cặp SHA đã khóa, không tự resolve lại branch/tag, không dùng
   working tree hoặc `HEAD` hiện tại thay cho commit được giao.

Schema hỗ trợ 40/64 ký tự không chứng minh spike đã kiểm chứng cả SHA-1 lẫn
SHA-256. 1.07 phải ghi object format và phiên bản Git thực sự đã test; thiếu hỗ
trợ runtime phải được báo rõ, không coi là commit không tồn tại một cách tùy ý.

Không tự fetch/checkout/reset repository đầu vào để chữa lỗi. Thiếu object/history
là lỗi đầu vào hoặc bàn giao; chuẩn bị dữ liệu thuộc boundary thống nhất với 1.04.
Lệnh Git khi triển khai phải truyền danh sách arguments, không ghép shell command;
không bật external diff/textconv cho source không tin cậy.

## 7. PR thay đổi và force-push

**Có trong nguồn:** commit mới trên PR cần run mới; run cũ vẫn giữ cặp SHA cũ.
Database cũng ghi head mới tạo run mới. [S1] (BR-02), [S3] (§2.4.5)

**Proposed — Q05:**

| Thời điểm/tình huống | Hành vi đề xuất |
| --- | --- |
| Phát hiện head hoặc base ref đổi trong lúc chuẩn bị snapshot, trước khi khóa | Dừng chuẩn bị với lý do snapshot đã đổi; caller lấy metadata mới và gửi lại, không trộn hai lần đọc |
| Head đổi sau khi đã khóa, kể cả force-push | Run cũ tiếp tục trên SHA cũ nếu còn đủ objects; yêu cầu phân tích head mới tạo run mới |
| Nhánh đích tiến thêm hoặc PR đổi nhánh đích sau khi khóa | Không tính lại base cho run cũ; lần phân tích mới dùng metadata mới |
| Object cũ không còn khả dụng | Báo thiếu snapshot/object; không thay bằng head mới |
| Retry một bước của run đã khóa | Dùng cùng repository và cặp SHA; policy retry/idempotency chi tiết thuộc 1.08 |

Force-push là việc ref chuyển sang lịch sử khác; không cần xác định đó là push
thường hay force-push để giữ tính bất biến: chỉ cần thấy SHA thay đổi là không
được gán kết quả cũ cho SHA mới.

Cơ chế lấy PR metadata nhất quán và phát hiện race còn cần 1.04/1.08 thống nhất.
Spike local 1.07 kiểm chứng được việc giữ SHA cũ khi ref đổi; điều đó chưa chứng
minh đã phát hiện live PR thay đổi trên GitHub. Nhãn stale/cancel/supersede, nếu
cần, là đề xuất lifecycle riêng, chưa phải trạng thái hiện có. [S7]

## 8. File metadata và evidence của rename/delete

**Proposed — Q06/Q07:** đường dẫn tính từ root repository, giữ đúng tên trong Git;
không đổi hoa/thường hoặc trim khoảng trắng của tên file. `symbol=None` ở spike
mức file. Mapping dùng nguyên `ChangedComponent` hiện tại. [S7]

| Git change | `path` | `change` | `previous_path` | Nơi đọc source evidence |
| --- | --- | --- | --- | --- |
| Added | Đường dẫn mới | `added` | `None` | Target, đường dẫn mới |
| Modified | Đường dẫn hiện tại | `modified` | `None` | Base cho phần bị bỏ; target cho phần thêm/sửa mới |
| Deleted | Đường dẫn cũ đã bị xóa | `deleted` | `None` | Base, đường dẫn cũ |
| Renamed | Đường dẫn mới | `renamed` | Đường dẫn cũ | Base với tên cũ; target với tên mới |

Với rename kèm sửa nội dung, dẫn hai evidence riêng nếu cần giải thích cả trước
và sau. Dòng của base không được dùng làm line range của target. Evidence phải
đọc lại từ đúng commit/path, kiểm dòng tồn tại và hỗ trợ được nhận định. [S8] [S9]

Nếu PR dùng merge-base, “base” trong bảng chính là merge-base, không phải đầu
nhánh đích. `AnalysisReport` hiện chỉ nhận evidence thuộc `commits.base/target`;
không gắn thêm evidence của `base_tip_sha` vào report này. [S7]

Database thiết kế `old_path/new_path`: added chỉ có new; deleted chỉ có old;
modified hai path bằng nhau; renamed hai path khác nhau. Bảng trên là mapping
sang contract hiện hành, không yêu cầu sửa schema DB hoặc `models.py`. [S3] (§3.4.1)

**Proposed — Q07:** cố định rename threshold 50% cho spike và ghi cấu hình/Git
version trong evidence kiểm chứng. Git nhận diện rename theo độ tương đồng;
đổi tên kèm sửa nhiều có thể được báo thành delete + add. Không suy ra rename
chắc chắn từ tên giống nhau. [G1]

Binary vẫn có thể được liệt kê ở mức file; không tạo excerpt/line range giả.
Contract evidence hiện cần dòng dương nên không biểu diễn được mọi bằng chứng
binary hoặc file rỗng bằng source line reference. 1.07 chỉ xuất metadata khi phù
hợp; biểu diễn evidence không có dòng là contract impact cho task riêng. [S7]

## 9. Lỗi, giới hạn và contract impact

**Proposed — Q04/Q08:** phân biệt các nguyên nhân dưới đây. Đây là nhãn thiết kế,
chưa phải error codes đã được triển khai hoặc API mới.

| Nguyên nhân | Kết quả cần quan sát |
| --- | --- |
| Thiếu base/target | Báo rõ input nào thiếu, không mặc định thành `HEAD` |
| SHA sai định dạng | Từ chối trước diff |
| Ref không resolve được hoặc tên mơ hồ | Báo ref không hợp lệ/không xác định; không đoán branch/tag |
| Object SHA không tồn tại hoặc không phải commit | Báo object thiếu/sai loại; không trả diff rỗng |
| Repository local không hợp lệ hoặc không đúng identity được giao | Dừng với lỗi repository; không tìm repo thay thế |
| History thiếu, không có hoặc có nhiều merge-base | Dừng resolve PR và nêu nguyên nhân xác định được |
| Snapshot/ref đổi trước khi khóa | Yêu cầu lấy snapshot mới theo mục 7 |
| Git timeout/thất bại | Báo lỗi đã loại dữ liệu nhạy cảm; không coi là không có thay đổi |
| Status/path ngoài khả năng contract/spike | Báo unsupported rõ; không silently bỏ file hoặc chuẩn hóa làm sai tên |

Không biến lỗi SHA, history hoặc unsupported thành kết quả an toàn. Không có thay
đổi file, chưa phân tích được và chưa chạy test là ba kết quả khác nhau.

Các giới hạn cần 1.07 ghi riêng: binary/empty file evidence, copy detection, type
change, symlink, submodule, path không giải mã được hoặc có khoảng trắng đầu/cuối,
rename detection bị giới hạn tài nguyên, Git/object format chưa kiểm chứng.
`ChangedComponent.path` dùng `Text(strip_whitespace=True)` nên path có khoảng trắng
đầu/cuối có nguy cơ đổi nghĩa; đề xuất từ chối rõ thay vì làm sai path. [S7]

Contract hiện không có input PR/ref hoặc metadata chuyên biệt như `base_tip_sha`,
thời điểm resolve, diff policy/version, similarity score, binary flag hay stale.
Draft chỉ nêu nhu cầu; nếu cần công khai/lưu trữ các dữ liệu này, mở task contract
riêng có producer/consumer review theo rule 03. Chưa sửa model/generated artifacts.

## 10. Danh sách quyết định cần nhóm chốt

Các tên người/bên dưới là đề xuất phối hợp, chưa phải người đã nhận review hoặc
người có quyền phê duyệt. Bằng chứng chốt phải là link issue/PR/biên bản có thật.

| ID | Quyết định và phương án đưa ra review | Trạng thái | Bên cần phối hợp đề xuất | Chặn 1.07? |
| --- | --- | --- | --- | --- |
| Q01 | Xác nhận scope/writer/reviewer, không trùng paths; dùng FR-03 merge-base/head làm baseline; ghi liên kết quyết định | pending | Do Ha An, Nguyen Tan Huy, nhóm | Có |
| Q02 | Chốt ranh giới: 1.04 cung cấp identity/repo/PR metadata; resolver tạo cặp SHA; hàm diff chỉ nhận repo local + full SHA; xác định writer của resolver | proposed | Owner 1.04, 1.06, 1.08 | Có; có thể chốt giới hạn fixture local trước |
| Q03 | Chốt input branch/tag/full SHA, từ chối tên mơ hồ/short SHA; kiểm object; direct diff không đòi quan hệ tổ tiên; base=target hợp lệ; object format được hỗ trợ | proposed | Owner 1.06/1.07, reviewer | Có |
| Q04 | PR chỉ nhận merge-base duy nhất với history đủ; shallow/thiếu history/no-base/multiple-base báo lỗi; không tự đổi semantics | proposed | Owner 1.04/1.06, reviewer | Có cho phần PR; 1.07 ghi rõ phần đã kiểm chứng |
| Q05 | Chốt thời điểm freeze, xử lý race và ref đổi; run cũ giữ SHA cũ; thiếu object báo lỗi; lifecycle live giao 1.08 | proposed | Owner 1.04/1.06/1.08 | Có cho quy tắc snapshot |
| Q06 | Chốt `CommitPair` là cặp diff thực; mapping rename/delete và evidence base/target theo mục 8 | proposed | Owner 1.06, 1.08, 1.09; reviewer | Có |
| Q07 | Chốt rename threshold 50%, metadata binary và cách báo các loại/path chưa hỗ trợ | proposed | Owner 1.07, reviewer 1.07 | Có trước khi assert output fixture |
| Q08 | Chốt cách trả lỗi/unsupported nội bộ, timeout/resource bounds của spike và fixture do task tạo; xác nhận không sửa input checkout hoặc chạy code của nó | pending | Owner 1.07, reviewer; owner 1.04 cho acquisition | Có trước triển khai |
| Q09 | Có cần lưu/expose base tip, PR identity, resolve time và policy version; nơi lưu provenance khi contract chưa có field | pending | Owner contracts và 1.08/1.09 | Không chặn diff local; cần trước tích hợp provenance đầy đủ |
| Q10 | Chính sách stale/cancel, retry/idempotency và refresh metadata khi nhánh đích đổi nhưng head giữ nguyên | pending | Owner 1.04/1.08 | Không chặn diff local; cần trước lifecycle live |

Mẫu ghi quyết định khi nhóm thực sự chốt:

```text
ID: Q...
Kết luận và phạm vi: ...
Người quyết định thực tế: ...
Reviewer thực tế: ...
Ngày: ...
Nguồn xác nhận: ...
Mục cần sửa trong draft / task follow-up: ...
```

Chưa có các giá trị này thì giữ `proposed/pending`. Khi có quyết định, writer được
nhóm giao cập nhật phần PR semantics của D05; không đóng cả D05 vì ID đó còn chứa
ngôn ngữ/framework, parser và discovery. [S6]

## 11. Điều kiện bàn giao sang 1.07

- [ ] Nhóm xác nhận Q01 và ghi writer/reviewer/paths không trùng.
- [ ] Q02–Q06 đủ rõ cho phần spike được giao; link quyết định có thật ở mục 10.
- [ ] Q07/Q08 được chốt trước khi triển khai các assertions/hành vi tương ứng.
- [ ] Base/target, PR policy, freeze và mutable PR behavior không còn mâu thuẫn.
- [ ] Fixture do task tạo trong thư mục tạm riêng hoặc đã có quyền dùng; không
  `git init` tại workspace chính và không sửa checkout repository đầu vào.
- [ ] Consumer 1.08/1.09 biết cặp commit thực và quy tắc evidence; phần live còn
  pending được giao rõ, không coi local fixture là bằng chứng tích hợp GitHub.

Cases bàn giao để viết test 1.07: add/modify/delete/rename, rename kèm sửa, binary,
base=target, missing/invalid/unknown SHA, object sai loại, path đặc biệt, working
tree bẩn không lẫn vào commit diff, ref đổi sau freeze, PR base khác base tip,
history thiếu và nhiều merge-base nếu resolver nằm trong brief code đã chốt.
Không bắt 1.07 dựng live PR/lifecycle chỉ để kiểm chứng diff mức file.

Trong khi chờ review, có thể chuẩn bị bảng cases và khảo sát contract độc lập;
chưa triển khai code phụ thuộc policy đang pending. Không cần chờ candidates 1.03,
parser hay runner để soạn semantics và kiểm chứng diff trên fixture được phép. [S5]

## 12. Kiểm chứng và bàn giao draft

Đã đọc nguồn và đối chiếu text/bảng/ô liên quan, contract và rule 03/09. Chỉ tạo
tài liệu này; chưa triển khai resolver/diff, chưa tạo Git fixtures, chưa chạy
product tests hoặc thử lệnh diff trên repository đầu vào.

Kiểm tra thực tế ngày 2026-10-24, cwd là root monorepo:

- Script Python chỉ đọc: PASS cho 12 định nghĩa nguồn, 19 local link tồn tại,
  7 bảng có số cột nhất quán, code fences đóng đủ, whitespace/newline và Q01–Q10.
- `git diff --check`: exit 0 trên tracked diff. File draft đang untracked nên
  whitespace của file này được kiểm bằng script nói trên.
- `git status --short`: có thư mục draft mới và thư mục `smartregression-ai/`
  untracked đã có từ trước; không có tracked change trong phiên.

Các checks này chỉ xác minh tài liệu, không chứng minh semantics đã được fixture
hoặc reviewer độc lập xác nhận. Sau khi chỉnh draft cần kiểm lại phần ảnh hưởng.

AI hỗ trợ: Codex hỗ trợ đối chiếu nguồn, giải thích thuật ngữ, soạn draft và
self-review tài liệu trong giai đoạn thiết kế 1.06. Do Ha An và nhóm cần đọc,
chỉnh sửa, giải thích và xác minh trước khi dùng làm baseline; chưa có review độc
lập hoặc phê duyệt được ghi nhận. Không tự gán tỷ lệ đóng góp/chữ ký. Tham chiếu
Proposal Appendix C/D [S1] và [rule 13](../../rules/13-documentation-ai-use.md).

Nguồn kỹ thuật Git được đối chiếu ngày 2026-10-24; không thay thế quyết định nhóm
hay bằng chứng runtime trên máy chạy spike:

- [G1 — git-diff](https://git-scm.com/docs/git-diff): so sánh hai cây file,
  three-dot/merge-base semantics và rename similarity threshold.
- [G2 — git-merge-base](https://git-scm.com/docs/git-merge-base): merge-base có thể
  có nhiều kết quả; `--all` dùng để liệt kê đầy đủ.
- [G3 — git-rev-parse](https://git-scm.com/docs/git-rev-parse): xác minh object và
  kiểu commit, peel tag và xử lý input để tránh bị hiểu nhầm là option.

[S1]: ../../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx
[S2]: <../../../C1.SE26_DOCUMENTS/C1SE26_Architecture_v1.3 (1).docx>
[S3]: ../../../C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx
[S4]: ../../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx
[S5]: ../../development/sprint-1-team-guide.md
[S6]: ../../development/decision-register.md
[S7]: ../../../backend/src/smartregression/contracts/models.py
[S8]: ../../rules/09-impact-selection.md
[S9]: ../../rules/03-contracts-api.md
[G1]: https://git-scm.com/docs/git-diff
[G2]: https://git-scm.com/docs/git-merge-base
[G3]: https://git-scm.com/docs/git-rev-parse
