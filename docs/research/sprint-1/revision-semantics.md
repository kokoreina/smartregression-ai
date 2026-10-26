# Task 1.06 — Quy tắc xác định phiên bản phân tích

**Trạng thái: accepted — hoàn thành đặc tả task 1.06.** Cập nhật: 2026-10-26.
Nguồn chốt baseline: user xác nhận trong chat ngày 2026-10-26:
“oke ták 6 đã chốt rồi hãy push và gửi request vào nhóm main giúp tôi”.
Đây là xác nhận do user truyền đạt; không tự điền tên người quyết định, ngày
họp trước đó hoặc phê duyệt mentor khi chưa có bằng chứng riêng.
Task thuộc PB03; owner trong workbook là **Do Ha An**. [S4]

Bản đầu đã được GitHub user **kokoreina** review `APPROVED` trong [PR #5][R1]
và merge vào `main`; không còn đúng khi mô tả tài liệu này là chưa từng được review.
Review không có nội dung kết luận riêng cho các câu hỏi semantics. Handoff của
[PR #9][R2] trước đó vẫn ghi PR policy pending. Xác nhận của user ngày 2026-10-26
đóng phần pending về baseline thiết kế 1.06; không thay đổi lịch sử hai PR đó
hoặc nhận rằng PR/ref resolver đã được triển khai.

Tài liệu trả lời ba câu hỏi: so sánh commit nào với commit nào, giữ kết quả đúng
phiên bản khi PR thay đổi ra sao, và đọc bằng chứng ở phiên bản nào. Đây là đầu
vào thiết kế cho 1.07. Spike direct diff hai SHA đã có trong PR #9; PR/ref resolver
vẫn chưa triển khai. Không tạo implementation trùng với spike đó. [S12] [S13]

## 1. Phạm vi và cách đọc trạng thái

- **Có trong nguồn:** yêu cầu đã được viết trong tài liệu nhóm. Cụm này không có
  nghĩa nhóm hoặc mentor đã phê duyệt bản hiện hành.
- **Proposed:** cách cụ thể hóa do draft này đề xuất, cần người có trách nhiệm chốt.
- **Pending:** chưa có xác nhận hoặc chưa đủ dữ liệu để quyết định.
- D05 hiện **accepted lựa chọn Python + pytest** theo ADR 0002 và **revision
  semantics 1.06** theo xác nhận A01; parser/discovery và phiên bản input vẫn
  được theo dõi riêng. Không ghi cả D05 là
  pending hoặc accepted dựa trên một phần của quyết định. [S6] [S10]
- `Reviewed/merged` ghi nhận sự kiện GitHub; `accepted baseline` ghi nhận quyết
  định thiết kế. A01 ở mục 10 đã được xác nhận; giới hạn implementation vẫn giữ rõ.

Phạm vi 1.06 là repository identity, cặp revision, PR snapshot và quy tắc evidence.
1.07 chỉ spike Git diff mức file trên fixture do task tạo hoặc được phép dùng.
Không chọn parser/ngôn ngữ đầu vào, tạo DB/worker, sửa contract hay chạy code/test
của repository đầu vào. Draft 1.06 không cần chờ 1.04 hoàn thành. [S5]

User giao hoàn thiện hồ sơ 1.06 trong phiên này. Writer của thay đổi tài liệu là
task của Do Ha An, được Codex hỗ trợ; paths gồm file này, chỉ mục D05 và
[handoff 1.06](an-revision-handoff.md). Consumer/reviewer đề xuất: Nguyen Tan Huy,
Pham Phan Hoang Huy; chưa ghi họ đã review lần cập nhật này. Baseline là
`origin/main` tại `e937f669fefada31d5254b355f92f24e88e41725`; không có
tracked change cục bộ trước sửa. Git status không chứng minh không có đồng đội
đang sửa file ở máy khác. Không sửa code Git/runner hoặc handoff của người khác.

### Tóm tắt sáu quy tắc đã chốt

1. Cặp commit do user chỉ định: direct diff `base_sha → target_sha`.
2. PR: `base_sha = merge-base(base_tip_sha, pr_head_sha)`, `target_sha = pr_head_sha`.
3. Branch/tag resolve thành full commit SHA trước phân tích; consumer chỉ nhận SHA
   đã khóa, không tự dùng lại tên branch hoặc `HEAD`.
4. Sau freeze không thay cặp SHA; PR head mới, kể cả force-push, là yêu cầu/run mới.
5. Code bị xóa đọc evidence ở base; rename dùng path cũ tại base, path mới tại target.
6. Thiếu/sai commit hoặc không xác định được merge-base duy nhất thì báo lỗi;
   không trả kết quả rỗng để thay cho lỗi hoặc tự đổi cách so sánh.

Sáu quy tắc là baseline thiết kế 1.06 đã được user xác nhận. Chi tiết ở mục 4–8;
phạm vi implementation và follow-up ở mục 10. Việc chốt thiết kế không phải bằng
chứng runtime hoặc xác nhận toàn bộ 1.07/G1 đã hoàn thành.

## 2. Nguồn và yêu cầu đã được viết

| Nguồn | Vị trí để người review tìm lại | Nội dung liên quan |
| --- | --- | --- |
| [S1 — Proposal v1.4](../../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx) | §7, FR-03; BR-02; NFR-05; §12.6 | PR mặc định dùng merge-base/head; khóa SHA; head mới cần run mới; giữ đúng phiên bản; xét base và target cho code xóa/đổi tên |
| [S2 — Architecture v1.3](<../../../C1.SE26_DOCUMENTS/C1SE26_Architecture_v1.3 (1).docx>) | §2.2; §4.1 bước 1–3; §5.2 nguyên tắc dữ liệu | Resolve commit pair hoặc PR merge-base/head, lưu cặp SHA và dùng snapshot đã khóa |
| [S3 — Database v1.5](../../../C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx) | §1.4 Definitions, Acronyms and Abbreviations; §2.4.5 `analysis_runs`; §3.4.1 `changed_files`; §3.4.5 `evidence_references` | Full commit ID 40/64 hex; PR dùng merge-base/head; head mới tạo run mới; quy tắc old/new path và evidence |
| [S4 — Scrum workbook v1.4](../../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx) | `Sprint 1 Backlog!B13:G14`; `Product Backlog!B10:H10` | 1.06: revision/SHA freezing, 8h; 1.07: diff/file metadata, 14h; PB03 truy vết FR-03 |
| [S5 — Guide Sprint 1](../../development/sprint-1-team-guide.md) | §3 bảng task; §5 phối hợp; §8 ví dụ Do Ha An | Draft độc lập, phối hợp 1.04; 1.07 đợi semantics đủ rõ, dùng fixture riêng và giữ contract |
| [S6 — Decision register](../../development/decision-register.md) | D03, D05 và quy ước trạng thái | Contract bootstrap là nguồn chuẩn; tách acceptance của revision semantics khỏi implementation/G1 |
| [S7 — Backend contract](../../../backend/src/smartregression/contracts/models.py) | `Commit`, `CommitPair`, `AnalysisRequest`, `ChangedComponent`, `EvidenceReference`, `AnalysisReport` | Shape hiện hành và giới hạn biểu diễn |
| [S8 — Rule 09](../../rules/09-impact-selection.md) | Yêu cầu và ví dụ | Full SHA, semantics rõ, evidence deleted ở base, inventory ở target |
| [S9 — Rule 03](../../rules/03-contracts-api.md) | Contracts/API | Phân biệt repo/revision/run; không sửa generated artifacts hoặc schema tùy ý |
| [S10 — ADR 0002](../../architecture/decisions/0002-python-pytest-input.md) | Decision; Consequences | Python/pytest đã accepted; PR policy pending trong snapshot lịch sử này được giải quyết về thiết kế bằng A01, không sửa ADR cũ |
| [S11 — Repository access](repository-access.md) | Boundary và handoff | 1.04 là prototype offline; chưa cung cấp clone/PR metadata thật |
| [S12 — Git diff spike](git-diff-spike.md) | Phạm vi và đoạn cuối | Hai full SHA, direct diff, rename threshold 50%; không resolve refs hoặc chốt PR policy |
| [S13 — Implementation handoff](implementation-handoff-20261024.md) | Thay đổi và AC; Review và tiếp tục | Có local fixture spike; PR policy pending tại thời điểm 2026-10-24; kết quả test là của phiên tích hợp |

Bằng chứng GitHub kiểm tra trực tiếp ngày 2026-10-24:

| Sự kiện | Dữ liệu đã xác minh | Phạm vi chứng minh |
| --- | --- | --- |
| [Review PR #5][R1] | `APPROVED`, login `kokoreina`, 13:30:54 UTC+07; review ID `5637165169`; body rỗng | Bản đầu đã được người khác review; chưa có kết luận riêng cho Q01–Q10 |
| [Merge PR #5][R3] | `merged_by=kokoreina`, 13:31:04 UTC+07; merge commit `7c006ee09f0758b90bd348b99384d26003a78617` | Bản đầu đã tích hợp vào main, không chứng minh PR resolver chạy thật |
| [Merge PR #9][R2] | main đã chứa direct diff spike và handoff tại commit `23bc998509a1f4fe31022aa75e0bef2dd90c40d5` | Cần tái sử dụng phần đã có; handoff vẫn tách PR semantics khỏi phạm vi spike |

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

**Accepted trong baseline 1.06 — Q02/Q03:** với yêu cầu so sánh hai revision, `base_sha` là commit
resolve từ input base; `target_sha` là commit resolve từ input target. Đọc chênh
lệch giữa hai cây file này. Không tự đổi base thành parent hay merge-base.

Ví dụ input là tag `v1.0` và branch `feature/login`: resolve cả hai thành commit
đầy đủ một lần, sau đó chỉ dùng hai SHA kết quả. Ref là đầu vào của bước resolve;
`AnalysisRequest.commits` hiện chỉ nhận full SHA, không nhận branch/tag. [S7]

Quy tắc cho spike:

- Hai commit không bắt buộc có quan hệ tổ tiên; direct diff vẫn là so sánh hai cây
  file đã chỉ định. Không tự diễn giải thành thay đổi riêng của một PR. [G1]
- Base bằng target là cặp hợp lệ, trả không có thay đổi file. Điều này không có
  nghĩa test đã pass hoặc không có rủi ro regression.
- Nếu target là merge commit do user chỉ định, vẫn so trực tiếp với base đã chọn;
  không tự chọn parent thứ nhất hoặc tạo combined diff.

## 5. PR dùng merge-base và PR head

**Có trong nguồn:** FR-03 đã quy định mặc định PR là merge-base → PR head. BR-02
giữ kết quả cũ tại commit cũ. Architecture và Database mô tả cùng hướng. [S1] [S2] [S3]

**Accepted trong baseline 1.06 — Q01/Q02:** áp dụng yêu cầu đó cho 1.07 bằng cách phân biệt:

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

**Accepted trong baseline 1.06 — Q04:** đọc toàn bộ kết quả merge-base. Chỉ tiếp tục nếu có đúng một
kết quả và đủ history để xác định kết quả đó. Không có tổ tiên chung, history
thiếu, nhiều merge-base hoặc lỗi Git đều phải báo rõ. Không tự chuyển sang direct
diff, dùng empty tree hoặc tạo virtual merge commit. Với shallow history, đề xuất
dừng bước resolve PR cho đến khi bên cung cấp repository bổ sung history. [G2]

## 6. Resolve và kiểm tra SHA trước phân tích

**Accepted trong baseline 1.06 — Q02/Q03:** dùng trình tự dưới đây cho mỗi yêu cầu:

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

**Accepted trong baseline 1.06 — Q05:**

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

**Accepted về mapping/evidence trong baseline 1.06 — Q06:** đường dẫn tính từ root repository, giữ đúng tên trong Git;
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

**Q07 — cấu hình spike hiện tại:** dùng rename threshold 50% và ghi cấu hình/Git
version trong evidence kiểm chứng. Git nhận diện rename theo độ tương đồng;
đổi tên kèm sửa nhiều có thể được báo thành delete + add. Không suy ra rename
chắc chắn từ tên giống nhau. [G1]

Binary vẫn có thể được liệt kê ở mức file; không tạo excerpt/line range giả.
Contract evidence hiện cần dòng dương nên không biểu diễn được mọi bằng chứng
binary hoặc file rỗng bằng source line reference. 1.07 chỉ xuất metadata khi phù
hợp; biểu diễn evidence không có dòng là contract impact cho task riêng. [S7]

## 9. Lỗi, giới hạn và contract impact

**Baseline xử lý lỗi 1.06 — Q04/Q08:** phân biệt các nguyên nhân dưới đây. Đây là nhãn thiết kế,
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

## 10. Quyết định và việc còn lại sau review

Giữ IDs Q01–Q10 để truy vết bản đầu. User xác nhận task 1.06 đã chốt ngày
2026-10-26; acceptance dưới đây chỉ thuộc baseline thiết kế. Các chi tiết
implementation/lifecycle ngoài đặc tả vẫn là follow-up, không tự coi đã chạy.

| ID cũ | Nội dung đã làm rõ trong đặc tả | Bằng chứng/phạm vi hiện tại | Phần còn lại |
| --- | --- | --- | --- |
| Q01 | Scope 1.06 và PR merge-base/head | Accepted qua A01; bản đầu reviewed/merged trong PR #5 | Không giả xác nhận lock file trên máy đồng đội |
| Q02 | Boundary ở mục 6: access/acquisition → resolve/freeze → diff | LocalGit của PR #9 chỉ nhận repo local và hai full SHA; 1.04 offline chưa cung cấp PR metadata thật | Giao writer resolver/acquisition trước khi triển khai boundary đó, không chặn việc hoàn tất thiết kế |
| Q03 | Direct diff, full SHA, ref/tag normalization, base=target ở mục 4/6 | Accepted về thiết kế qua A01; Contract/LocalGit đã có full-SHA/direct diff | Kiểm chứng ref resolver ở task code riêng |
| Q04 | Một merge-base, đủ history, lỗi rõ ở mục 5/9 | Accepted về thiết kế qua A01; LocalGit không tự chọn merge-base | Chưa có runtime PR resolver |
| Q05 | Freeze, head đổi, force-push ở mục 7 | Accepted về thiết kế qua A01, phù hợp FR-03/BR-02 | Transport/live race giao follow-up 1.04/1.08 |
| Q06 | CommitPair là cặp diff thực, evidence rename/delete ở mục 8 | Accepted về thiết kế qua A01; tương thích contract hiện tại | Consumer review khi wiring, không sửa models trong 1.06 |
| Q07 | Rename threshold và binary/path limits ở mục 8/9 | Spike #9 đã dùng 50%; binary metadata khác source evidence | Ghi cấu hình đã dùng và giới hạn; không cần một quyết định sản phẩm mới để mô tả implementation hiện có |
| Q08 | Read-only, lỗi, resource bounds và fixture boundary | LocalGit dùng timeout 15s, output cap 2.000.000 bytes/lệnh và source limit 256.000 bytes; lỗi commit hiện gộp `invalid_commit` | Các gap phân loại lỗi/coverage thuộc review 1.07; không tự tuyên bố chúng đã đủ AC |
| Q09 | Metadata bổ sung chưa có trong contract | Đã ghi contract impact ở mục 9 | Follow-up producer/consumer riêng trước tích hợp provenance đầy đủ |
| Q10 | Stale/cancel/retry/idempotency | Giữ nguyên snapshot; lifecycle thực tế chưa được chốt | Follow-up 1.08; không cần triển khai để hoàn tất đặc tả 1.06 |

**A01 — accepted, theo xác nhận trực tiếp của user ngày 2026-10-26.** Sáu quy tắc
tóm tắt và chi tiết mục 4–8 là baseline thiết kế cho 1.07/consumer; giới hạn
runtime ở mục 9 và 11 được giữ nguyên. Không suy acceptance từ merge: nguồn mới
là thông báo chốt task do user cung cấp trong chat.

| Nội dung xác nhận A01 | Giá trị hiện có |
| --- | --- |
| Quy tắc đã chốt | Sáu quy tắc ở mục 1, chi tiết mục 4–8 |
| Nguồn xác nhận | User thông báo trực tiếp trong chat: “oke ták 6 đã chốt rồi hãy push và gửi request vào nhóm main giúp tôi” |
| Người quyết định cụ thể trong nhóm | User truyền đạt task đã chốt; không cung cấp tên người chốt riêng, nên không tự điền |
| Review bản đầu | kokoreina, APPROVED, [PR #5 review][R1] |
| Kết luận phạm vi semantics | Accepted về thiết kế; không phải chứng nhận runtime hoặc nghiệm thu toàn bộ 1.07/G1 |
| Ngày nhận xác nhận A01 | 2026-10-26, Asia/Bangkok; ngày họp/chốt trước đó không được cung cấp |

Writer cập nhật riêng PR semantics trong D05, không đóng phần parser/discovery/
phiên bản input chưa có bằng chứng. Không sửa ADR 0002 hoặc handoff lịch sử để
thay đổi nội dung từng được ghi tại thời điểm trước quyết định này. [S6] [S10]

## 11. Bàn giao và đối chiếu implementation hiện tại

### Definition of Done cho 1.06

- [x] Có nguồn FR-03/BR-02, architecture/database, contract và task ownership.
- [x] Định nghĩa base/target cho commit pair và PR, phân biệt base tip/merge-base.
- [x] Mô tả resolve full SHA, freeze, head mới và force-push.
- [x] Mô tả evidence/path cho added/modified/deleted/renamed và contract impact.
- [x] Bản đầu đã có review độc lập và merge; link bằng chứng ở mục 2.
- [x] Có phạm vi consumer, gap implementation, follow-up và handoff riêng.
- [x] Có nguồn xác nhận A01 từ user ngày 2026-10-26; cập nhật baseline và riêng phần D05 liên quan.

**Task 1.06 hoàn thành ở phạm vi đặc tả revision semantics**, theo xác nhận A01.
Bản cập nhật trạng thái được gửi bằng PR riêng vào main; chưa xem là đã merge
trước khi GitHub xác nhận. Không sửa trạng thái workbook hoặc nghiệm thu các task
khác trong thay đổi này.

### Không làm lại spike đã có

[LocalGit](../../../backend/src/smartregression/adapters/git_local.py) và
[tests](../../../backend/tests/integration/test_git_local.py) đã được đưa vào main
qua PR #9. Bản cập nhật 1.06 chỉ đọc code/tests để đối chiếu, không chạy chúng
hoặc nhận kết quả test cũ làm kết quả của phiên này. [S12] [S13]

| Nội dung 1.06 | Phần code/tests hiện có | Phần chưa được chứng minh ở đây |
| --- | --- | --- |
| Commit pair/direct diff | `LocalGit.diff(base, target)`, add/modify/delete/rename, base=target | Không có PR metadata/ref resolver hoặc merge-base policy runtime |
| Full SHA/commit object | Shape 40/64 lowercase và kiểm object type | SHA-256 chưa được fixture kiểm chứng trong handoff; lỗi thiếu/sai/không tồn tại đang gộp |
| Snapshot evidence | `read_text(sha, path)` đọc blob đúng commit; test working tree bẩn và deleted base | Chưa tạo/validate đầy đủ EvidenceReference hoặc report production |
| Rename và path | Threshold 50%, previous_path; reject mode/path không hỗ trợ | Chưa có coverage đầy đủ cho rename kèm sửa, mọi tên Unicode, resource-limit rename hoặc copy |
| Binary | Diff mức file và `read_text` từ chối source chứa NUL | Chưa có source-line evidence cho binary/empty file; không gán dòng giả |
| Mutable PR | Đã mô tả invariant freeze ở mục 7 | Chưa có live PR/race/force-push integration test hoặc resolver |

Đây là đối chiếu phạm vi, không phải review độc lập toàn bộ code #9. Không kết
luận 1.07 hoặc G1 đã Done chỉ vì có implementation/handoff. Người nhận 1.07 nên
review phần hiện có và bổ sung gap theo brief, thay vì triển khai adapter thứ hai.

### Handoff cho consumer

- 1.04/acquisition: cung cấp repo identity đã được phép, repo local và metadata
  cùng snapshot; chưa có acquisition thật thì dùng fixture riêng, không tự clone.
- Resolver trước diff: tạo full `base_sha/target_sha`; PR base là merge-base;
  không đặt logic resolve mutable refs trong hàm diff đã nhận hai SHA.
- 1.07: nhận repo local được phép và cặp SHA đã khóa; giữ ChangedComponent;
  fixtures do task tạo, không sửa checkout đầu vào hoặc chạy code/test của nó.
- 1.08: giữ identity/cặp SHA cho run; không thay bằng head mới khi retry; lifecycle
  và production retry/dedup vẫn là follow-up riêng.
- 1.09: metadata/index/evidence phải đúng repo, commit và path; base và target
  là hai snapshot khác nhau, không gán evidence deleted vào target.

Không yêu cầu runner/parser/candidate thật để hoàn tất tài liệu semantics này.
Trước khi sửa code 1.07, phối hợp với Huy vì PR #9 đã đưa implementation vào main;
không suy ra ownership hay reviewer mới từ việc merge. [S5] [S13]

## 12. Kiểm chứng và bàn giao

Xem [handoff 1.06](an-revision-handoff.md) để biết baseline, paths, lệnh/kết quả và
bằng chứng đóng A01. Giữ lịch sử kiểm tra bản đầu trong PR #5; kết quả cũ không được
viết thành kết quả của lần cập nhật này. Chỉ chạy checks tài liệu cho thay đổi này;
không chạy lại product/runner tests hoặc code repository đầu vào.

AI hỗ trợ: Codex đối chiếu nguồn, metadata review GitHub, code boundary đã merge,
giải thích thuật ngữ và hoàn thiện tài liệu 1.06; tự kiểm tra của phiên này là
self-review. Review bản đầu của kokoreina là sự kiện có thật, không đồng nghĩa đã
review các sửa đổi mới. A01 dựa trên xác nhận của user, không giả review mới của
kokoreina. Do Ha An và nhóm cần hiểu/chỉnh/xác minh phần
nhận. Không tự gán chữ ký, tỷ lệ đóng góp hoặc phê duyệt mentor. Tham chiếu Proposal
Appendix C/D [S1] và [rule 13](../../rules/13-documentation-ai-use.md).

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
[S10]: ../../architecture/decisions/0002-python-pytest-input.md
[S11]: repository-access.md
[S12]: git-diff-spike.md
[S13]: implementation-handoff-20261024.md
[R1]: https://github.com/kokoreina/smartregression-ai/pull/5#pullrequestreview-5637165169
[R2]: https://github.com/kokoreina/smartregression-ai/pull/9
[R3]: https://github.com/kokoreina/smartregression-ai/pull/5
[G1]: https://git-scm.com/docs/git-diff
[G2]: https://git-scm.com/docs/git-merge-base
[G3]: https://git-scm.com/docs/git-rev-parse
