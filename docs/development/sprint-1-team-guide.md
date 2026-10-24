# Hướng dẫn phối hợp nhóm — Sprint 1

**Cập nhật 2026-10-24:** Nguyễn Tấn Huy đã chốt Python + pytest cho repository
đầu vào theo [ADR 0002](../architecture/decisions/0002-python-pytest-input.md).
Các câu pending về lựa chọn cặp công nghệ trong snapshot bên dưới được thay thế
cho riêng điểm này; phiên bản input, implementation, G1 và phê duyệt phân công vẫn
cần bằng chứng/quyết định riêng. Không coi lựa chọn này là hoàn thành Sprint 1.

**Trạng thái: đề xuất để nhóm xác nhận; chưa phải phân công được phê duyệt.**
Đối chiếu workspace ngày 2026-10-20. Tài liệu này chuẩn bị cách làm việc;
không chứng minh Sprint 1 hoặc bất kỳ task nào đã hoàn thành.

## 1. Bắt đầu sử dụng

1. Tìm tên mình trong bảng thành viên, chọn **một task** ở bảng Sprint 1.
2. Xác nhận scope sprint, dependency và writer của file dùng chung với nhóm.
3. Dùng prompt bắt đầu ở mục 7 hoặc ví dụ theo tên ở mục 8.
4. Làm trên checkout/branch riêng; bàn giao bằng [handoff](../templates/handoff.md)
   và nhờ thành viên khác review trước khi người được nhóm giao tích hợp.

Đọc [AGENTS.md](../../AGENTS.md) làm điểm vào; lệnh setup/check lấy từ
[verified-commands](verified-commands.md), không sao chép kết quả kiểm tra cũ thành
kết quả của task mới. Một thành viên có thể dùng nhiều profile theo công việc.

## 2. Nguồn, hiện trạng và quyết định cần xác nhận

### Nguồn đã đối chiếu

| Nguồn | Phần đã dùng | Giới hạn |
| --- | --- | --- |
| [Proposal v1.4](../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx) | §7 yêu cầu/rules, §10.2, §11.1–11.5 sprint/evaluation, Appendix C/D | Revision chưa có bằng chứng phê duyệt hiện hành; chữ ký lịch sử không duyệt tài liệu mới |
| [Project Plan v1.1](<../../C1.SE26_DOCUMENTS/C1SE.26_ProjectPlan_v1.1 jsa.docx>) | §3.2.1 lịch, §3.2.3 detailed schedule, §4.1/4.2 workstreams và Tables 14/15 | Phạm vi, giờ và mục tiêu dataset khác một số nguồn bên dưới |
| [Scrum workbook v1.4](../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned_v1.4.xlsx) | Sheets `Main`, `Product Backlog`, `Sprint 1 Backlog`, `Sprint 1 Reports`, `References` | Trạng thái là planned/proposed/not started trong file, chưa phải tiến độ repo; không sửa workbook trong task này |
| [Architecture v1.3](<../../C1.SE26_DOCUMENTS/C1SE26_Architecture_v1.3%20(1).docx>) | §3.3 technical constraints | Thiết kế đích, không phải các service đã được triển khai |
| [Database v1.5](../../C1.SE26_DOCUMENTS/C1SE26_DataBase_v1.5.docx) | §1.3 scope, §2.1 và §2.4 thiết kế Sprint 1 | PostgreSQL target cần xác nhận trước migration; bảng thiết kế không tự trở thành scope implementation |
| Repo hiện tại | [ownership](module-ownership.md), [quyết định](decision-register.md), [backlog bootstrap](../backlog/bootstrap.md), source/API/UI/tests/manifests và CI | Đọc implementation và định nghĩa checks; không chạy product suite trong task tài liệu này |

Bốn DOCX được trích xuất đoạn văn/bảng chữ; XLSX được trích xuất dữ liệu ô của
14 sheet, sau đó đọc các sheet liên quan nêu trên. Không kiểm hết nội dung mọi
sheet, hình/sơ đồ nhúng, comments, objects hoặc tính lại công thức bằng Excel.
Không tuyên bố đã đọc toàn bộ nội dung Office hoặc xác minh nghiên cứu bên ngoài.

### Những khác biệt cần nhóm quyết định

| Điểm | Bằng chứng cụ thể | Cách xử lý trong bản đề xuất |
| --- | --- | --- |
| Sprint Goal và mức hoàn thiện | Proposal §11.2 + workbook `Sprint 1 Reports!B7`: research foundation + technical spike; Project Plan §3.2.1 và §3.2.3: Git Integration & Components Mapping, PB01–04/PB23 theo mức feature | Dùng 12 task spike của workbook làm cơ sở đề xuất; chưa coi là cam kết hoàn thành toàn bộ PB01–04/PB23 |
| Ước lượng | `Main!L20` = 194 giờ; `Sprint 1 Backlog!G8:G19` cộng thành 112 giờ, `G38` cũng 112; Project Plan §3.2.3 = 250 giờ gồm 155 giờ overhead | Giữ ước lượng từng task từ sheet Sprint 1; chưa chốt capacity/lịch mới, không cộng các con số khác phạm vi |
| Spike chưa được tách task đủ rõ | Proposal §10/§11.2 yêu cầu dependency/test discovery và checkout → diff → discovery → single-test execution; workbook 1.05/1.07 mới mô tả config/diff | Đưa vào gate G1 bên dưới; nhóm cần bổ sung task/giờ hoặc xác nhận cách bao phủ, không tuyên bố gate đã đạt |
| Dataset | Proposal §11.4, workbook `Product Backlog!G30`/`References!F10`: mục tiêu ≥2 repo, ≥30 commit pairs, ≥15 verified fault-bearing cases; Project Plan §4.2 Table 15 và phần QA nêu 50 pairs | Sprint này đề xuất screening/protocol/candidate evidence; quy mô cuối cùng và yêu cầu hoàn tất dataset ngay Sprint 1 còn pending |
| Product Owner | Workbook `Main!F7` ghi Jan Samuelsson; Project Plan §4.2 Table 15 ghi Nguyen Tan Huy | Giữ vai trò kỹ thuật đã thống nhất trong nguồn; chưa gán quyền phê duyệt sản phẩm/merge từ tài liệu này |
| Tên/mã thành viên | Project Plan bìa và bảng team có mã khác nhau cho Pham Phan Hoang Huy | Dùng họ tên không dấu như workbook để tránh đoán cách viết/mã; không đưa mã, điện thoại, email vào guide |
| Hướng dẫn Git cũ | Rule 05, workflow và agent-rules-setup còn ghi chưa có Git; kiểm tra hiện tại có Git, branch `main`, remote `origin` | Dùng hiện trạng phiên kiểm tra; chưa xác minh remote default branch, quyền hay branch protection |

**Cần nhóm xác nhận trước khi coi đây là sprint commitment:** scope spike hay feature,
capacity và lịch bắt đầu thực tế, gate G1, dataset target, reviewer/người tích hợp và
người có quyền chấp nhận đầu ra. Trong lúc chờ, có thể soạn protocol, policy và khảo
sát code độc lập; phần implementation phụ thuộc quyết định phải giữ trạng thái blocked/pending.
Không suy ra tiến độ từ lịch tháng 9 trong Project Plan hoặc ngày hiện tại.

### Bản đồ triển khai hiện tại

| Trạng thái | Bằng chứng và hệ quả |
| --- | --- |
| Đã có, có thể tái sử dụng | Python/FastAPI/Pydantic và React/TypeScript; hướng API/CLI → application → core/interfaces; [models](../../backend/src/smartregression/contracts/models.py) là nguồn contract; schema/types có generator |
| Đã có, giới hạn rõ | API có [GET /health](../../backend/src/smartregression/api/routes/health.py), chỉ health tiến trình; [CLI](../../backend/src/smartregression/cli/main.py) chỉ validate report; không có analyze endpoint |
| DEMO | [App](../../frontend/src/app/App.tsx) và [ReportView](../../frontend/src/features/reports/ReportView.tsx) tải fixture, chưa kết nối repo/phân tích/LLM/chạy input tests |
| Chưa triển khai | Git/impact/evidence/retrieval/selection/evaluation chủ yếu README-only; [runner port](../../backend/src/smartregression/core/execution/ports.py) chỉ Protocol; chưa có persistence/provider/worker thật |
| Cần kiểm chứng trong task code sau | Tests contract/API/CLI và [source CI](../../.github/workflows/ci.yml) có định nghĩa; chưa xác nhận chúng pass trong phiên này, CI input-repo là luồng khác |

Giữ stack bootstrap. Ngôn ngữ/framework **repo đầu vào**, provider/index/DB, PR diff
semantics và runner cụ thể vẫn theo [D05–D09](decision-register.md). Pytest dùng cho
SmartRegression không tự quyết định framework repo đầu vào. Có enum report không
chứng minh job lifecycle đã có; contract chưa có job ID, queued/running/cancelled.

## 3. Sprint Goal, task và đầu ra đề xuất

**Sprint Goal đề xuất:** tạo nền tảng nghiên cứu có thể kiểm chứng và các spike tối
thiểu cho repository access, frozen revisions, diff và run lifecycle; làm rõ config,
RAG scope, selection/fallback và evaluation để Sprint 2 có input ổn định.

Owner của 12 task lấy từ `Sprint 1 Backlog!B8:G19`. Reviewer, dependency, paths và
tiêu chí chi tiết dưới đây là đề xuất bổ sung. IDs 1.01–1.12 là task con; PB IDs là
truy vết tới product backlog, **hoàn thành task con không đồng nghĩa PB hoàn thành**.

Mã tên: **H1** = Nguyen Tan Huy; **AN** = Do Ha An; **H2** = Pham Phan Hoang Huy;
**KH** = Tran Hung Khanh; **VI** = Dang Dai Viet. Hai thành viên tên Huy luôn dùng
họ tên đầy đủ trong prompt, branch/PR và handoff.

Các file `docs/research/sprint-1/*` dưới đây là **đầu ra dự kiến chưa được tạo**.
Phạm vi sửa thực tế cần được giao trong brief; không hiểu bảng là quyền sửa toàn
module. File nguồn dùng chung chỉ sửa sau bước phối hợp mục 5.

| Task / PB / giờ | Owner → reviewer đề xuất | Dependency | Đầu ra và paths dự kiến | Tiêu chí nghiệm thu đề xuất |
| --- | --- | --- | --- | --- |
| 1.01 / PB23 / 10h | H1 → VI | Không chặn bởi quyết định công nghệ | `docs/research/sprint-1/research-questions.md` | RQ, baselines full/dependency/LLM-only, hybrid và no-RAG; numerator/denominator, N/A, overhead, split và giới hạn; nguồn nghiên cứu kiểm chứng trước trích |
| 1.02 / PB23 / 8h | VI → H1 | Draft 1.01, có thể soạn song song | `docs/research/sprint-1/repository-screening.md` | Checklist license/quyền, history, test có sẵn, reproducibility, loại flaky/infra, tiêu chí nhận/loại và provenance; chưa giả nhãn fault |
| 1.03 / PB01 / 8h | VI → AN | 1.02; chọn cặp ngôn ngữ/framework còn pending | `docs/research/sprint-1/repository-candidates.md` | Repo chính/dự phòng, URL/commit/license đã kiểm tra, lý do và bằng chứng build/discovery nếu thực sự chạy; thiếu quyền/network ghi rõ, không coi candidate là đã chọn |
| 1.04 / PB01 / 12h | H1 → AN | 1.03 cho case thật; mock có thể làm trước | `docs/research/sprint-1/repository-access.md`; nếu được giao code: adapter GitHub tại `backend/src/smartregression/adapters/`, application và tests tương ứng | Prototype nhận diện repo được phép; phân biệt success/unauthorized/not-found/service error bằng double hoặc request được phép; credential không ra UI/log; không xây auth platform đầy đủ |
| 1.05 / PB02 / 8h | KH → AN | Draft trước; candidate từ 1.03 để kiểm chứng | `docs/research/sprint-1/test-environment.md`; xem runner port, không tự implement runner | So sánh ứng viên ngôn ngữ/framework bằng evidence; config command/args, test location, timeout/resources; invalid command/limits bị từ chối theo thiết kế; các phép chạy code đầu vào phải đợi isolation/policy |
| 1.06 / PB03 / 8h | AN → H1 | Draft độc lập; phối hợp 1.04 | `docs/research/sprint-1/revision-semantics.md` | Nêu so sánh hai commit/PR, phương án merge-base, frozen SHA và PR head thay đổi; nhóm quyết semantics còn pending trước khi code phụ thuộc |
| 1.07 / PB03 / 14h | AN → H2 | 1.06 đủ rõ, fixture được phép; diff file không cần chốt parser | `backend/src/smartregression/core/git/`, `backend/tests/fixtures/git/`, test riêng trong `backend/tests/unit/`; ghi findings vào tài liệu của AN | Spike read-only add/modify/delete/rename, SHA thiếu/sai, previous_path; kết quả đúng phiên bản và có giới hạn; không sửa repo đầu vào hay chạy code của nó |
| 1.08 / PB04 / 8h | H1 → KH | 1.04/1.06; contract thống nhất với AN/VI/KH | `docs/research/sprint-1/run-lifecycle.md`; code application/tests riêng nếu brief giao prototype | Run ID, trạng thái/chuyển trạng thái, failure reason, timestamps và retry/duplicate semantics được mô tả/kiểm chứng ở mức spike; dùng double nếu chưa có worker/DB; không báo pipeline thật đã chạy |
| 1.09 / PB19 / 10h | H2 → AN | 1.06 cung cấp snapshot; xem 1.01 để cách ly labels | `docs/research/sprint-1/rag-scope.md` | Loại dữ liệu index, repo/commit/path/symbol metadata, provenance/secret exclusion, prompt injection và data policy; không index labels/outcomes hoặc chọn provider/vector DB thay nhóm |
| 1.10 / PB22 / 10h | KH → H2 | Draft độc lập; chốt với 1.05/1.09 | `docs/research/sprint-1/selection-policy.md` | Decision table cho S=(D∪M∪L)∩T, L không loại D/M, unknown IDs, invalid evidence, discovery failure vs inventory rỗng; chế độ fallback/stop và failure status trung thực; chưa implement selector |
| 1.11 / PB24 / 8h | H1 → VI | 1.01/1.02; phối hợp 1.05/1.10 | H1 là writer [evaluation protocol](../research/evaluation-protocol.md), có thể thêm `docs/research/sprint-1/evaluation-report-template.md` | Cohort/split/fault adjudication, baselines, budget/repeats pending có chủ thể quyết; selection frozen trước outcomes, null/N/A, failed/excluded runs; template không chứa số đo bịa |
| 1.12 / PB23 / 8h | H1 → KH | Handoff 1.01–1.11; kiểm tra G1 | `docs/research/sprint-1/review.md` | Tổng hợp demo/evidence, decisions/pending, task nào đủ/chưa đủ AC; đối chiếu goal/gate, không ghi completed cho spike chưa được chạy/kiểm chứng |

Workbook có tổng **112 giờ estimate**: H1 46h, AN 22h, H2 10h, KH 18h, VI 16h.
Đây là số kế hoạch, không phải effort thực hay capacity đã xác nhận. H1 có tải cao;
nhóm nên cân đối sau khi bổ sung gate G1. H2 có thể hỗ trợ review metadata/security,
VI chuẩn bị evidence tổng hợp, nhưng không tự thay owner hoặc nhận giờ đã làm.

**G1 — gate kỹ thuật còn cần nhóm phân rã:** Proposal §10 và §11.2 yêu cầu chứng
minh checkout → diff → discovery → single-test execution, dependency prototype và
chọn đúng một ngôn ngữ/framework đầu vào. Đề xuất AN phụ trách parser/dependency
spike, KH phụ trách discovery và single-test spike trong runner cô lập, VI cung cấp
candidate, H2 review provenance, H1 tổng hợp quyết định. Đây là phần bổ sung đề xuất,
chưa có task ID/estimate riêng trong 12 task; không giấu vào 1.05/1.07 rồi coi đủ giờ.
Chưa có isolation/quyền chạy thì chỉ soạn thiết kế và fixtures, ghi gate chưa đạt.

**Ngoài phạm vi đề xuất:** hoàn chỉnh PB01–04 như tính năng production, toàn bộ
dataset có nhãn, RAG/provider/vector DB thật, selector đầy đủ, runner production,
dashboard phân tích thật, input-repo CI integration và benchmark cuối kỳ. Nhóm
chọn scope feature của Project Plan thì phải lập lại task/estimate/AC trước triển khai.

## 4. Mỗi thành viên làm phần nào, dùng profile nào?

| Thành viên / vai trò từ Project Plan §4.2 | Task Sprint 1 | Vùng làm việc theo brief | Bàn giao chính |
| --- | --- | --- | --- |
| Nguyen Tan Huy — Project Leader / Research & Integration | 1.01, 1.04, 1.08, 1.11, 1.12 | Research/protocol của mình; adapter/application/API chỉ khi brief 1.04/1.08 giao code; không sở hữu mọi module | RQ/protocol → VI; access/lifecycle → AN/KH/VI; tổng hợp → cả nhóm |
| Do Ha An — Change Impact / Backend | 1.06, 1.07 | Git/revision docs và core/git, fixtures/tests Git riêng; core/impact chỉ cho spike G1 được nhóm giao thêm | Frozen SHA/diff contract → H1/H2/KH/VI |
| Pham Phan Hoang Huy — LLM & RAG | 1.09 | `rag-scope.md`; đọc retrieval/evidence/adapters để thiết kế, chưa triển khai index/provider | Metadata/provenance/data policy → AN/KH/H1 |
| Tran Hung Khanh — Regression Selection / CI/CD | 1.05, 1.10 | Test-environment/selection-policy docs; runner/discovery spike chỉ khi G1 được giao | Config/limits/fallback → H1/AN/H2; môi trường → VI |
| Dang Dai Viet — Dataset, Dashboard & Evaluation | 1.02, 1.03 | Screening/candidates docs; dashboard đang là consumer tham khảo, chưa tự sửa UI ngoài task | Repo/license/provenance → AN/KH; dataset criteria → H1; review protocol |

Đây là ánh xạ theo workstream, không trùng hoàn toàn năm vùng kỹ thuật ở
[module ownership](module-ownership.md). Ví dụ Application/UI là boundary chung:
H1 điều phối access/lifecycle, AN review backend, VI review consumer. Không tự gán
toàn bộ frontend hoặc toàn bộ evaluation cho một người theo tên vùng cũ.

### Routing theo công việc

Chỉ mở hàng phù hợp. Các số rule bên dưới là số trong
[bảng routing AGENTS](../../AGENTS.md); agent phải mở đúng file, không chỉ đọc tên.

| Công việc / task | Profile chính | Rules | Skill khi trigger phù hợp |
| --- | --- | --- | --- |
| Điều phối, scope, review sprint (1.12) | [Coordinator](../agents/coordinator.md) | 00/01/05/13 | Không cần skill chỉ để chia task |
| RQ, screening, candidate, protocol (1.01–03, 1.11) | [QA/Research](../agents/qa-research.md) | 06/11/13; 00 nếu scope xung đột | [evaluation-integrity](../../.agents/skills/evaluation-integrity/SKILL.md) |
| Access/application/lifecycle (1.04, 1.08) | [Backend/Contracts](../agents/backend-contracts.md) | 02/03/06; 10 khi chạm execution | [api-contracts](../../.agents/skills/api-contracts/SKILL.md) khi đổi contract; [security-review](../../.agents/skills/security-review/SKILL.md) khi review access/secret |
| SHA/diff/Git spike (1.06, 1.07) | [Change Impact](../agents/change-impact.md) | 01/09/06 | [test-driven-development](../../.agents/skills/test-driven-development/SKILL.md) cho behavior có test rõ; security-review nếu có shell/untrusted input |
| Test config/isolation (1.05, G1) | [DevOps/Runner](../agents/devops-runner.md) | 10/12/06 | security-review; [github-actions-hardening](../../.agents/skills/github-actions-hardening/SKILL.md) chỉ nếu task giao workflow |
| RAG scope (1.09) | [RAG/LLM](../agents/rag-llm.md) | 04/08/06/13 | security-review cho dữ liệu/prompt; không cần gọi LLM để soạn policy |
| Selection/fallback (1.10) | [Regression Selection](../agents/regression-selection.md) | 03/09/06/13 | api-contracts chỉ khi đổi shared input/output |
| UI khi có task được giao bổ sung | [Frontend/Dashboard](../agents/frontend-dashboard.md) | 02/03/06 | [ui-design](../../.agents/skills/ui-design/SKILL.md), [accessibility-review](../../.agents/skills/accessibility-review/SKILL.md); [webapp-testing](../../.agents/skills/webapp-testing/SKILL.md) nếu cần browser và tool có sẵn |
| Review công việc người khác | [Reviewer](../agents/reviewer.md) | 05/14 và rules module | Skill theo rủi ro cụ thể, không nạp cả catalog |
| Lỗi chưa rõ nguyên nhân | Profile module | Thêm 07 | [systematic-debugging](../../.agents/skills/systematic-debugging/SKILL.md) |

`docs/agents` là hồ sơ vai trò; `docs/rules` là quy ước; `.agents/skills` là workflow
bổ trợ. Chúng không đổi model, cấp quyền, tự mở sub-agent hoặc tạo review độc lập.
Không cần một agent riêng cho mỗi thành viên/profile. Kỹ năng trong catalog hiện là
quy trình nội bộ có nguồn tham khảo; không mặc định là upstream package đã pin commit.

Cách dùng không phụ thuộc client: ghi rõ “Mở `docs/agents/change-impact.md`, các rule
được AGENTS định tuyến và `.agents/skills/.../SKILL.md` khi trigger khớp”. Agent phải
đọc nội dung cần dùng. Không giả mọi IDE tự nạp profile/rules, có slash command hoặc
browser tool. Xem [setup agents](agent-rules-setup.md) và giới hạn client tại đó.

## 5. Phối hợp file dùng chung và thứ tự làm

### Một writer tại một thời điểm

Trước khi nhận shared file, ghi vào brief/PR hoặc bảng task nhóm đang dùng: task,
file, writer, consumer/reviewer, thời điểm nhận và handoff trả file. Đây là quy ước
phối hợp thủ công, không phải lock tự động hay quyền truy cập filesystem.

| File/boundary khi task thực sự cần sửa | Người tích hợp đề xuất | Consumer/reviewer cần phối hợp | Thứ tự |
| --- | --- | --- | --- |
| [models.py](../../backend/src/smartregression/contracts/models.py) | H1 cho 1.04/1.08; người viết được ghi riêng trong brief | AN (producer Git), KH (lifecycle/runner), VI (UI/report); H2 nếu evidence thay đổi | Thống nhất mẫu input/output, compatibility và version policy → writer sửa model/tests → sinh artifacts → consumer kiểm tra |
| [OpenAPI](../../contracts/generated/openapi.json), [generated.ts](../../frontend/src/types/generated.ts), [exporter](../../scripts/export_contracts.py), [types generator](../../frontend/scripts/contracts.mjs) | Cùng writer của thay đổi contract, H1 điều phối | AN/VI | Sinh sau model; cả producer/consumer đối chiếu trước khi nhận handoff; không sửa generated bằng tay |
| [demo fixture](../../examples/reports/demo.json) | VI nếu có task consumer được giao | H1/AN | Chỉ đổi khi contract yêu cầu, validate backend; giữ DEMO; fixtures Git riêng của AN không dùng chung file này |
| [evaluation protocol](../research/evaluation-protocol.md) | H1 (1.11) | VI review dataset, KH review môi trường, H2 review leakage | Người khác đề xuất qua review/handoff; soạn tài liệu riêng rồi H1 tổng hợp, tránh cùng sửa protocol |
| pyproject/uv.lock hoặc frontend package/lock | KH nếu nhóm giao dependency task riêng | Owner module + H1; VI nếu frontend | Chốt nhu cầu/phạm vi trước; package manager sinh lockfile, không chỉnh tay hoặc thêm dependency chỉ để soạn docs |
| [source CI](../../.github/workflows/ci.yml) / input integration | KH nếu có task CI riêng | H1/AN; Reviewer security | Source CI và input-repo CI tách scope; review trust/permissions; không suy ra quyền GitHub từ vai trò |
| [AGENTS](../../AGENTS.md), ADR, [decision register](decision-register.md), guide này | H1 điều phối; writer theo task cụ thể | Owner bị ảnh hưởng + reviewer khác tác giả | Ghi proposed/pending/accepted đúng bằng chứng; ADR chỉ khi có quyết định đủ căn cứ; không đổi rule để né gate |

Danh sách này **không tự giao việc sửa** models, manifests, CI hoặc governance trong
Sprint 1. Đầu ra docs được chia file riêng ở mục 3 để phần lớn thành viên làm độc lập.

### Thứ tự và những việc có thể làm song song

1. **Chốt brief:** nhóm xác nhận scope/capacity/G1, H1 ghi accepted/proposed/pending
   theo quyết định có thật; xác nhận writer/reviewer và nhánh tích hợp.
2. **Soạn độc lập:** H1 làm 1.01; VI draft 1.02; AN draft 1.06; H2 draft 1.09;
   KH draft 1.05/1.10. Dùng giả định được ghi rõ, chưa code theo quyết định pending.
3. **Trao input:** 1.01 → 1.02 → 1.03; 1.06 → 1.07; 1.03 → kiểm chứng 1.04/1.05;
   1.06 → chốt metadata 1.09. Mock access có thể bắt đầu khi candidate thật chưa có.
4. **Tích hợp có thứ tự:** access + frozen revisions + contract review → 1.08;
   RQ/screening + environment/fallback → 1.11. Không cần provider/DB/runner thật
   để mô tả lifecycle hoặc protocol, nhưng phải ghi rõ prototype/double.
5. **Review/demo:** các handoff → 1.12; G1 chưa đủ thì nêu blocker/việc cần bổ sung.
   Review người khác là công việc thêm, chưa được tính rõ trong 112 giờ.

### Branch, PR và conflict

Đã quan sát branch `main`, remote tên `origin`; chưa xác minh default branch của
remote hoặc quyền tích hợp. Theo [CONTRIBUTING](../../CONTRIBUTING.md), mỗi task dùng
branch nhỏ như `feat/s1-1-07-git-diff` hoặc `docs/s1-1-09-rag-scope` trên checkout
riêng. Tài liệu này không tự tạo branch, stash hay chuyển branch cho working tree bẩn.

Nhóm thống nhất `<integration-branch>` và merge/rebase policy. Trước task và trước PR,
kiểm tra status, cập nhật remote, tích hợp thay đổi từ nhánh đó theo policy đã thống
nhất, rồi kiểm tra lại phần ảnh hưởng. Nếu có công việc chưa lưu, xử lý/bàn giao nó
trước khi cập nhật branch; không tự stash/reset hoặc cherry-pick toàn bộ thay đổi người khác.
Agent chỉ chạy lệnh làm thay đổi Git khi task đã giao rõ; người có quyền thực hiện PR/merge.

PR chứa một đầu ra đủ nhỏ để review, dùng [PR template](../../.github/pull_request_template.md),
ghi task ID/AC, paths, shared files/contract impact, lệnh/kết quả, AI use và pending.
Producer/consumer bị ảnh hưởng cùng review contract; có một reviewer thật khác tác giả.

Khi conflict: dừng sửa file xung đột, đọc cả hai thay đổi và AC, liên hệ owner để
thống nhất kết quả; không chọn ours/theirs hàng loạt. Với generated artifacts, hòa
giải nguồn chuẩn trước rồi tái sinh. Với lockfile, hòa giải manifest và dùng package
manager. Chạy lại checks bị ảnh hưởng, ghi evidence vào handoff.

## 6. Definition of Done và bàn giao

**DoD đề xuất cho phạm vi workbook:**

- Mỗi task 1.01–1.12 có đầu ra đáp ứng AC, hoặc ghi rõ chưa hoàn thành/blocker;
  task thiếu evidence không được đánh dấu completed.
- Prototype có bước tái lập và kết quả thực, case lỗi được kiểm tra; code phải có
  checks liên quan theo rule 06. Mock/spike/DEMO được nhận diện ở tài liệu và demo.
- Contract có producer/consumer review và artifacts đồng bộ nếu thực sự thay đổi.
- Decisions còn pending được giữ rõ; quyết định đã chọn có lý do/bằng chứng/người
  quyết định thật. Không biến phương án agent đề xuất thành accepted.
- Protocol giữ labels/outcomes ngoài selector; target nghiên cứu không thành số đo.
- Tác giả giải thích được đầu ra và phần AI hỗ trợ; có review của người khác, không
  coi agent đổi profile/self-review là review độc lập.
- 1.12 đối chiếu G1. Muốn tuyên bố đạt **Sprint 1 theo Proposal** phải có evidence
  cho gate kỹ thuật và quyết định ngôn ngữ/framework; nếu thiếu, báo chưa đạt gate.

Dùng [handoff template](../templates/handoff.md). Phần tối thiểu: task/trạng thái,
branch/commit nếu có, file thay đổi và lý do, contract/consumer impact, shared writer
đã trả file chưa, command/cwd/kết quả thực, known issues/blocker, next step/người nhận,
phần AI hỗ trợ và người review thực tế. Không gửi key/source nhạy cảm/transcript đầy đủ.

Giữ một nơi theo dõi trạng thái do nhóm thống nhất (issue/workbook/task board);
guide là hướng dẫn và đề xuất baseline, không tự đồng bộ tiến độ hay khóa file.
Nếu nhận task không khớp guide, làm rõ scope mới và cập nhật link/handoff để tránh
có hai danh sách phân công khác nhau cùng được xem là hiện hành.

## 7. Bốn mẫu prompt copy được

Thay toàn bộ placeholder bằng thông tin thật. “Paths được sửa” là giới hạn task,
không phải lệnh ghi đè mọi file trong đó. Mở root workspace, dùng AGENTS làm router;
không dán nguyên catalog/rules vào mọi phiên.

### A. Bắt đầu task

```text
Tôi là [họ tên], phụ trách [workstream]. Tôi đang làm [task/PB ID] của Sprint 1.
Đối chiếu docs/development/sprint-1-team-guide.md; trạng thái scope: [đã chốt/đề xuất].
Đầu ra cần đạt và acceptance criteria: [...].
Paths được sửa: [...]. File dùng chung và writer đã thống nhất: [...].
Dependency đã sẵn sàng: [...]; chưa sẵn sàng: [...]. Reviewer/người nhận handoff: [...].
Hãy kiểm tra root/git status và AGENTS áp dụng; mở profile/rules/skills đúng task,
đối chiếu implementation rồi thực hiện phần đủ điều kiện trong scope.
Giữ thay đổi có sẵn; báo trước khi cần mở rộng phạm vi. Không tự chốt pending.
Kiểm tra theo AC bằng lệnh phù hợp, ghi kết quả thật và handoff theo template repo.
Không commit/push/merge/deploy hoặc mở sub-agent.
```

### B. Tiếp tục từ handoff

```text
Tôi là [họ tên], tiếp nhận [task/PB ID] từ [người] theo handoff [path/nội dung].
Scope/paths/AC còn áp dụng: [...]. Shared files/writer: [...].
Kiểm tra root/git status, AGENTS và profile/rules/skills liên quan; đối chiếu actual
files/diff với handoff trước khi tiếp tục. Xác minh dependency và quyền đã giao.
Giữ thay đổi có sẵn, không làm lại phần đã có evidence nếu không có lý do mới.
Tiếp tục phần còn thiếu trong scope; input thiếu thì nêu blocker và làm phần độc lập.
Chạy checks liên quan phần vừa đổi, cập nhật handoff và người có thể nhận tiếp.
Không commit/push/merge/deploy hoặc mở sub-agent.
```

### C. Đề nghị thay đổi contract/file dùng chung

```text
Tôi là [họ tên], task [ID]. Cần thay [file/contract] để đạt [behavior/AC].
Writer dự kiến: [...]; người đang sửa: [.../chưa xác minh]. Consumers/reviewer: [...].
Paths được sửa: [...]. Quyết định/ủy quyền đã có: [...].
Kiểm tra status/AGENTS, dùng Backend/Contracts, rule 03/06 và api-contracts.
Trước sửa, đối chiếu mẫu input/output, compatibility/version, consumers và dependency.
Chỉ triển khai phần đã được giao và đã phối hợp writer; phần breaking/pending chưa
có quyết định thì ghi phương án/blocker, tiếp tục khảo sát độc lập.
Models là nguồn chuẩn; tái sinh artifacts bằng công cụ, kiểm tra producer/consumer,
fixture và checks liên quan. Bàn giao contract impact cùng evidence và trả shared file.
Không commit/push/merge/deploy hoặc mở sub-agent.
```

### D. Review task thành viên khác

```text
Tôi là [họ tên], review task [ID] của [tác giả]. Đây là task read-only.
Brief/AC: [...]. Diff/branch/commit hoặc paths cụ thể: [...]. Handoff: [...].
Kiểm tra root/status, AGENTS; dùng Reviewer, rules 05/14 và rules module/skills cần thiết.
Đối chiếu scope, contract consumers, evidence/security/leakage và checks tác giả báo.
Findings có file/vị trí, trigger, tác động và confirmed/suspected; nêu phần chưa kiểm.
Phân biệt review của tôi với self-review agent; không approve thay tôi hoặc sửa file.
Báo kết quả thực, không commit/push/merge/deploy hoặc mở sub-agent.
```

## 8. Ví dụ theo từng thành viên

Các prompt sau giao một phần nhỏ từ bảng task; không tự cam kết toàn bộ PB. Với
task code có dependency chưa được nhóm chốt, agent khảo sát/soạn phần độc lập trước.

### Nguyen Tan Huy — 1.08 / PB04

```text
Tôi là Nguyen Tan Huy, phụ trách Research & Integration. Tôi bắt đầu 1.08/PB04.
Đọc guide Sprint 1. Đầu ra: docs/research/sprint-1/run-lifecycle.md mô tả run ID,
state transitions, timestamps, failure/duplicate semantics và boundary API/worker.
Chỉ sửa file tài liệu này; models.py là shared file chưa được giao sửa.
Dependency: có contract bootstrap; handoff 1.04/1.06 và policy worker chưa xác nhận.
Kiểm tra root/status/AGENTS; dùng Backend/Contracts, rules 03/06/13 và Coordinator
khi có scope conflict. Đối chiếu code; tách trạng thái report hiện có với job đề xuất.
Soạn phần độc lập, ghi pending; chưa dựng DB/worker/endpoint. Reviewer đề xuất là
Tran Hung Khanh. Kiểm tra docs và handoff; giữ thay đổi có sẵn, báo trước mở rộng scope.
Không commit/push/merge/deploy hoặc mở sub-agent.
```

### Do Ha An — 1.07 / PB03

```text
Tôi là Do Ha An, phụ trách Change Impact / Backend. Tôi bắt đầu 1.07/PB03.
Đầu ra: Git diff spike read-only, add/modify/delete/rename và invalid/missing SHA,
mapping ChangedComponent/previous_path đúng commit pair; không chạy code repo đầu vào.
Paths: backend/src/smartregression/core/git/, backend/tests/fixtures/git/,
backend/tests/unit/test_git_diff.py và docs/research/sprint-1/revision-semantics.md.
Shared models.py không được sửa trong task này; thiếu field thì báo contract impact.
Dependency cần kiểm: 1.06 đã có quyết định semantics chưa; fixture phải do task tạo
hoặc được phép dùng, không tự git init workspace hay sửa checkout đầu vào.
Kiểm tra root/status/AGENTS; dùng Change Impact, rules 01/09/06 và TDD nếu phù hợp.
Nếu semantics chưa chốt, chỉ khảo sát/soạn cases độc lập; nếu đủ điều kiện thì code,
chạy checks phù hợp, báo evidence/giới hạn và handoff cho Pham Phan Hoang Huy review.
Giữ thay đổi có sẵn, báo trước mở rộng scope; không commit/push/merge/deploy hoặc sub-agent.
```

### Pham Phan Hoang Huy — 1.09 / PB19

```text
Tôi là Pham Phan Hoang Huy, phụ trách LLM & RAG. Tôi bắt đầu 1.09/PB19.
Chỉ tạo docs/research/sprint-1/rag-scope.md: index source/tests/docs theo snapshot,
metadata repo/commit/path/symbol, provenance, secret exclusion và input không tin cậy.
Dependency: schema có sẵn; semantics 1.06 và protocol 1.01 cần đối chiếu/handoff.
Không sửa shared models/protocol, không cài provider/index/DB hay gửi source ra ngoài.
Kiểm tra root/status/AGENTS; dùng RAG/LLM, rules 04/08/06/13, security-review khi
review data flow. AC: labels/full-suite outcomes không vào selector/retrieval context,
unknown decisions ghi pending, metadata có ví dụ minh họa rõ nhãn và giới hạn.
Reviewer đề xuất Do Ha An. Kiểm tra docs/handoff cho An và Tran Hung Khanh.
Giữ thay đổi có sẵn, báo trước mở rộng scope; không commit/push/merge/deploy hoặc sub-agent.
```

### Tran Hung Khanh — 1.05 / PB02

```text
Tôi là Tran Hung Khanh, phụ trách Regression Selection / CI/CD. Tôi bắt đầu 1.05/PB02.
Chỉ tạo docs/research/sprint-1/test-environment.md; mô tả config framework/test paths,
approved args, timeout/CPU/RAM/output/network limits và yêu cầu isolation của spike G1.
Dependency: candidate từ 1.03 và cặp language/framework chưa được xác nhận.
Shared runner port/CI/manifests/lockfiles chưa được giao sửa; không chạy code repo ngoài.
Kiểm tra root/status/AGENTS; dùng DevOps/Runner, rules 10/12/06/13 và security-review.
AC: phương án có evidence hoặc ghi chưa xác minh; invalid command/non-positive limits
có case từ chối; discovery failure khác empty inventory; chưa chọn framework thay nhóm.
Reviewer đề xuất Do Ha An. Kiểm tra docs, handoff cho An/Nguyen Tan Huy/Dang Dai Viet.
Giữ thay đổi có sẵn, báo trước mở rộng scope; không commit/push/merge/deploy hoặc sub-agent.
```

### Dang Dai Viet — 1.02 / PB23

```text
Tôi là Dang Dai Viet, phụ trách Dataset, Dashboard & Evaluation. Tôi bắt đầu 1.02/PB23.
Chỉ tạo docs/research/sprint-1/repository-screening.md: checklist license/quyền sử dụng,
history, test có sẵn, build/discovery reproducibility, tiêu chí nhận/loại, provenance.
Dependency: draft 1.01 từ Nguyen Tan Huy chưa xác nhận; có thể soạn checklist độc lập.
Shared evaluation-protocol.md do Nguyen Tan Huy tích hợp; tôi gửi đề xuất qua handoff.
Kiểm tra root/status/AGENTS; dùng QA/Research, rules 06/11/13 và evaluation-integrity.
AC: phân biệt real fault/mutation/flaky/infra, label review độc lập và pilot/held-out;
không biến test fail thành fault, không coi target sample size là dữ liệu đã thu thập.
Không chọn repo/license chưa kiểm, chạy benchmark hay sửa dashboard trong task này.
Reviewer đề xuất Nguyen Tan Huy; kiểm tra docs/handoff cho người tiếp tục 1.03.
Giữ thay đổi có sẵn, báo trước mở rộng scope; không commit/push/merge/deploy hoặc sub-agent.
```

## 9. Giới hạn và trách nhiệm sử dụng AI

Guide được Codex hỗ trợ đọc nguồn, đối chiếu và soạn tài liệu trong task này.
Nhóm chưa xác nhận phân công/reviewer/scope; chưa có review độc lập của thành viên.
Tác giả/người sử dụng cần đọc, kiểm tra, chỉnh sửa và giải thích được phần mình nhận;
ghi tool/mục đích/giai đoạn/phạm vi AI hỗ trợ theo Proposal Appendix C/D và
[rule 13](../rules/13-documentation-ai-use.md). Không tự điền tỷ lệ đóng góp, chữ ký
hoặc trạng thái phê duyệt. Tự kiểm tra của agent được gọi là self-review.

Sau khi nhóm quyết định, cập nhật đúng nguồn scope/ownership và link tới quyết định
có thật; không để guide đề xuất tiếp tục được hiểu là baseline đã duyệt.
