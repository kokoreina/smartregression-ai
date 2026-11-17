# Sprint 3 — Team guide: Gemini, selection và execution

> Historical guide for the former 20 research tasks (9 November 2026). Task IDs and assignments below are preserved as history, not the current 75-task web backlog. Use the [current guide](../sprint-3-team-guide.md) and [canonical audit](../sprint-3-phase-1-audit.md).

Tài liệu hướng dẫn triển khai theo [Sprint Backlog hiện hành](../../../C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned.xlsx), không thay thế acceptance criteria (AC) trong workbook hoặc quyết định nguồn. Đọc `Sprint 3 Backlog!B8:G27`, task briefs hàng 57–195, effort/capacity hàng 198–213 và `Sprint 3 Reports!B5:Q63` khi giao việc.

Ngày đối chiếu: **2026-11-09, Asia/Bangkok**. Trạng thái dưới đây là ảnh chụp khi viết guide, phải kiểm tra lại khi nhận task.

## 1. Bắt đầu nhanh

1. Đọc [AGENTS.md](../../../AGENTS.md), kiểm tra root/branch/status và hướng dẫn thư mục con; giữ thay đổi có sẵn.
2. Tìm tên mình ở [phân công](#phan-cong), mở task tương ứng và hàng [định tuyến](#dinh-tuyen).
3. Kiểm tra [G0/G1/G2](#gates). Huy bắt đầu **3.14**; các thành viên khác chuẩn bị theo [bảng chờ G2](#chuan-bi).
4. Giao từng đầu ra có thể kiểm chứng cho AI bằng [mẫu prompt](#prompt-agent); không giao toàn bộ sprint trong một lượt.
5. Hoàn thành module tests, review và [handoff](../../templates/handoff.md); chỉ đóng task khi đủ [Definition of Done](#done).

Mục tiêu sprint: context/inventory đã xác thực → Gemini đề xuất → kiểm tra ID/evidence → selection/fallback theo policy → freeze manifest → runner cô lập → PostgreSQL/report/dashboard → pilot tái lập được.

Giữ phạm vi: Python/pytest đầu vào, PostgreSQL, structural/local lexical retrieval, CLI-first và dashboard đọc file report. Chỉ chọn/chạy test **hiện có** của repository đầu vào; vẫn viết tests cho SmartRegression. Không thêm multi-provider framework, embeddings/vector DB, auth/history API, durable queue, arbitrary-repository execution service hoặc full research benchmark.

## 2. Baseline, nguồn và hiện trạng

| Hạng mục | Trạng thái tại lần đối chiếu |
| --- | --- |
| Remote | Đã fetch `origin/main` ngày 2026-11-09; SHA **`ac2f55283c8be865c72ca25308a4e00e5e3a827e`**, merge PR #57. Xem [source cố định][main-source] |
| Workspace đang viết guide | Branch `work/sprint-1-local-closeout-20261031` là checkout cũ, không phải nền triển khai Sprint 3. Đã bảo toàn thay đổi Office/output có sẵn |
| Đã có trên main | Snapshot/change/graph/mapping/context producers, CLI/application, stage contracts, PostgreSQL foundation/evidence/inventory/index metadata và report UI. Có source không đồng nghĩa mọi nhánh lỗi đã nghiệm thu |
| G0 | **Pending.** So với completed-work commit `929b3365e17131fd74a8fd495c3795da4bf2692b`, main còn thiếu các thay đổi workflow/persistence, mapping artifact, bounded lexical build/search wiring và UI nested validation/integrity |
| Quyết định | PostgreSQL/P3 theo [decision register trên main][main-decisions]; local lexical theo [ADR 0003][adr3]; tích hợp Sprint 2 theo [ADR 0004][adr4]; selection theo [s1-selection-v1][policy]. Gemini-first/Huy-first theo yêu cầu nhóm và workbook |
| Chưa có bằng chứng Sprint 3 | G1 live Gemini, G2 CLI handoff và integrated pilot chưa được thực hiện bởi việc lập backlog/guide. Không ghi Done hoặc live-pass |
| Đầu vào còn cần xác minh | Exact model ID/SDK, structured-output support, dữ liệu được gửi, hard budgets/price/usage; lịch khả dụng; pilot split/repeats/rubric. Giao xử lý tại 3.14/3.16/3.12 trước bước liên quan |

Workbook ghi lịch sử PR #58–#63 merge vào các nhánh trung gian. Lần viết guide này xác nhận khoảng thiếu bằng source diff, không coi trạng thái merged là bằng chứng đã vào main. Không tích hợp Sprint 2 trong thay đổi tài liệu này; người nhận 3.14 phải kiểm lại remote và lập baseline kết hợp mới.

Nguồn đọc bổ sung: [Sprint 2 guide](../sprint-2-team-guide.md), [completion plan trên main][s2-plan], [contracts](../../contracts/README.md), [evaluation protocol](../../research/evaluation-protocol.md), [Proposal §12.6 và Appendices C/D](../../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx).

Một số [profiles](../../agents/coordinator.md), [rules](../../rules/00-governance.md), [verified commands local](../verified-commands.md) và protocol chứa snapshot bootstrap cũ. Dùng các quy tắc bất biến, tra quyết định/source mới để xác định hiện trạng; không sao chép câu “chưa có Git/DB/framework” thành pending hiện tại. Pending provider lịch sử không mở lại lựa chọn Gemini; exact model và quyền egress vẫn cần xác minh. Link GitHub cố định dùng cho nguồn main chưa có trong checkout này; sau khi cập nhật môi trường phải đọc file tương ứng tại baseline mới.

<a id="phan-cong"></a>
## 3. Phân công và effort

Đây là **estimate**, không phải actual hours hoặc bằng chứng hoàn thành. Tên viết tắt: H1 = Nguyễn Tấn Huy; H2 = Phạm Phan Hoàng Huy; KH = Trần Hưng Khánh; AN = Đỗ Hà An; VI = Đặng Đại Việt.

| Task | Nội dung | Owner | Giờ | Phụ thuộc chính và đầu ra |
| --- | --- | --- | ---: | --- |
| 3.01 | Freeze validated selection manifest | KH | 12 | G2, 3.15; hoàn thiện với 3.02/06/07/08 → manifest bất biến |
| 3.02 | Manifest identity/inventory partition | AN | 10 | G2, 3.15, contract 3.01 → validator dùng chung |
| 3.03 | Giải thích selected/not-selected | H2 | 12 | G2, 3.05/06, contract 3.01 → reasons/evidence |
| 3.04 | Gemini adapter/structured proposals | H1 | 14 | G0, 3.14/15 → typed provider outcomes |
| 3.05 | Validate Gemini IDs/evidence | H2 | 12 | G2, 3.18, 3.15 → proposal đã kiểm tra |
| 3.06 | Conservative selection | H2 | 14 | G2, 3.05; interfaces 3.02/07/08 và finalizer 3.01 → quyết định theo policy |
| 3.07 | Provider-error fallback | AN | 8 | G2, 3.15, error types 3.04/16 → configured fallback |
| 3.08 | Incomplete/config-change fallback | AN | 10 | G2, 3.15/02 → stop/full-suite rules |
| 3.09 | Isolated selected/full execution | KH | 18 | G2, 3.01/02/06/07/08 ready, storage interface 3.19 → bounded runner |
| 3.10 | Outcomes/error categories | KH | 12 | G2, 3.09, result contract 3.15, 3.19 → normalized outcomes |
| 3.11 | Report dashboard | VI | 18 | G2, 3.15; nghiệm thu với 3.03/10/19 → report UI |
| 3.12 | Reproducible pilot manifests/cases | VI | 12 | G2, constraints 3.14; trước 3.13 → frozen pilot inputs |
| 3.13 | Integrated pilot/handoff | H1 | 12 | G2, 3.01–12 và 3.18/19 ready → actual integrated evidence |
| 3.14 | Baseline/provider/data/budget readiness | H1 | 6 | Bắt đầu đầu tiên; G0 trước dependent implementation → readiness record |
| 3.15 | Contracts/application boundaries | H1 | 10 | G0, 3.14 → contracts/fixtures/compatibility |
| 3.16 | Gemini config/budgets/live smoke | H1 | 12 | G0, 3.14/15/04 → G1 evidence |
| 3.17 | CLI Gemini workflow/G2 handoff | H1 | 10 | G0/G1, 3.15, context/inventory Sprint 2 → framework trên main |
| 3.18 | Bounded context/prompt/source egress | H2 | 12 | G2, 3.15, initial context 3.17 → context/prompt refinement |
| 3.19 | Persist proposal/selection/execution | KH | 14 | G2, 3.15, contracts 3.01/10; không chờ runner → PostgreSQL extension |
| 3.20 | Final regression/acceptance evidence | AN | 4 | Evidence 3.13 và module tests → AC/evidence matrix |

| Thành viên | Giờ task |
| --- | ---: |
| Nguyễn Tấn Huy | 64 |
| Phạm Phan Hoàng Huy | 50 |
| Trần Hưng Khánh | 56 |
| Đỗ Hà An | 32 |
| Đặng Đại Việt | 30 |
| **Tổng task** | **232** |
| Dự phòng riêng | 32 |
| **Nguồn lực dự kiến** | **264** |

Giờ task bao gồm module tests và sửa lỗi/review trong scope. **3.20 chỉ có 4h cho tổng hợp cuối**, không gánh toàn bộ QA. Phần tích hợp Sprint 2 còn thiếu là prerequisite riêng, chưa có remaining estimate và không được cộng ngầm vào task Sprint 3. Các cột Day 1–15 trong Excel là mẫu tracking; lịch/availability chưa xác nhận. H1 có **52h trước G2**, không hứa xong trong 2–3 ngày. Ghi actual effort theo giờ thực làm, không sao chép estimate thành actual.

<a id="gates"></a>
## 4. Thứ tự và điều kiện chuyển bước

### G0 — Xác nhận nền Sprint 2

H1 làm reconciliation trong 3.14. Nếu main còn thiếu, tách việc tích hợp Sprint 2, giữ thay đổi main mới hơn và ghi estimate riêng. Chỉ đạt G0 sau khi có main SHA chứa đủ dependency, nguồn/contracts/consumer khớp, migration head thống nhất và checks phù hợp trên baseline kết hợp. Không cherry-pick/merge nguyên nhánh cũ chỉ vì có commit “completed”.

### G1 — Chứng minh gọi Gemini thật

Thứ tự H1: **3.14 → 3.15 → 3.04 → 3.16 (G1)**. G1 cần synthetic fixture được phép gửi, backend-only key, model ID đã xác minh/pin, structured response và giới hạn context/output/time/retry/cost. Lưu command, config/model, timestamp, response đã redacted, latency/usage nếu có và cách kiểm budget. Có offline provider-error tests; mock không thay live proof.

### G2 — Bàn giao CLI/application nền

Sau G1, H1 thực hiện **3.17**: context và inventory thật từ frozen fixture, typed proposal, minimum schema/ID/snapshot guards; selection/execution giữ đúng trạng thái `not_run` theo contract được chốt tại 3.15, không fake kết quả để schema pass. Framework phải vào main và CI/checks liên quan pass; handoff có command, fixture/config và giới hạn. G2 chưa bao gồm semantic/context coverage đầy đủ của 3.05/18.

<a id="chuan-bi"></a>
### Chuẩn bị trong lúc Huy làm nền

| Người | Làm được ngay trước G2 | Chờ G2 trước dependent implementation |
| --- | --- | --- |
| H2 | Đọc policy, audit retrieval, lập cases injection/invalid ID/evidence/context overflow; review proposal contract | Hoàn thiện context/validation/selector và reasons |
| KH | Khảo sát schema/runner/harness hiện có; đề xuất manifest/storage interfaces và isolation cases | Migration/manifest/runner gắn contract đã bàn giao |
| AN | Chuẩn bị decision table/negative fixtures và review identity/fallback contracts | Nối validators/fallback với provider/workflow thật |
| VI | Phác thảo UI states, khảo sát report consumer và license/candidate manifests | Implement dashboard theo generated contract và freeze pilot inputs |

Chuẩn bị/review không có nghĩa tự tạo public DTO hoặc policy cạnh tranh. Các thành viên trao đổi interface với H1 ngay khi 3.15 soạn, nhưng chưa nghiệm thu dependent behavior từ mock.

### Sau G2 đến nghiệm thu

- **H2:** 3.18 → 3.05 → 3.06 → 3.03.
- **AN:** 3.02 và 3.07 từ contracts; 3.08 sau validator 3.02; cùng H2 kiểm precedence.
- **KH:** 3.01 và 3.19 từ contracts; 3.09 sau selection/validation/fallback sẵn sàng; 3.10 sau actual execution.
- **VI:** 3.11 từ stable report contract; 3.12 chuẩn bị pilot, hoàn thành trước 3.13.
- **H1:** 3.13 khi các module ready; **AN:** 3.20 sau evidence pilot.

Không tạo vòng chờ: 3.02 dùng **contract** manifest, không đợi producer 3.01 hoàn tất; 3.19 dùng **result contract** từ 3.15/thiết kế 3.10, không chờ runner chạy; 3.06 dùng fallback interfaces/decision fixtures trước, sau đó parity-test implementation. 3.01 freeze kết quả đã validate khi tích hợp, không tự implement một selector khác. 3.13 tạo evidence đầu vào cho 3.20; không yêu cầu 3.20 Done mới được chạy pilot.

<a id="dinh-tuyen"></a>
## 5. Profile, rule và skill theo task

Tất cả task code đọc [02 — Coding](../../rules/02-coding-standards.md), [06 — Testing](../../rules/06-testing-quality.md); tài liệu/handoff theo [13](../../rules/13-documentation-ai-use.md). Đọc [00](../../rules/00-governance.md) khi có xung đột quyết định/phạm vi. Các hàng dưới bổ sung theo module, không yêu cầu nạp toàn bộ bộ hướng dẫn.

| Nhóm | Task | Profile | Rules trọng tâm | Skill và lúc kích hoạt |
| --- | --- | --- | --- | --- |
| A | 3.14 | [Coordinator](../../agents/coordinator.md), [RAG/LLM](../../agents/rag-llm.md) | [00](../../rules/00-governance.md), [01](../../rules/01-architecture.md), [08](../../rules/08-llm-rag.md), [13](../../rules/13-documentation-ai-use.md) | [security-review](../../../.agents/skills/security-review/SKILL.md) cho egress/secrets/provider config |
| B | 3.15, 3.17 | [Backend/Contracts](../../agents/backend-contracts.md) | [01](../../rules/01-architecture.md), [02](../../rules/02-coding-standards.md), [03](../../rules/03-contracts-api.md), [06](../../rules/06-testing-quality.md) | [api-contracts](../../../.agents/skills/api-contracts/SKILL.md) cho producer/consumer; [TDD](../../../.agents/skills/test-driven-development/SKILL.md) cho behavior test được |
| C | 3.04, 3.16, 3.18 | [RAG/LLM](../../agents/rag-llm.md) | [01](../../rules/01-architecture.md), [06](../../rules/06-testing-quality.md), [08](../../rules/08-llm-rag.md); thêm [04](../../rules/04-data-storage.md) khi chạm storage/retrieval | security-review cho provider/context trust; TDD cho behavior; api-contracts nếu đổi DTO |
| D | 3.03, 3.05, 3.06 | [Regression Selection](../../agents/regression-selection.md), RAG/LLM | [03](../../rules/03-contracts-api.md), [06](../../rules/06-testing-quality.md), [08](../../rules/08-llm-rag.md), [09](../../rules/09-impact-selection.md) | TDD chính; security-review ở output/evidence boundary |
| E | 3.02, 3.07, 3.08 | Regression Selection, [QA/Research](../../agents/qa-research.md) | 03, 06, 09 ở trên | TDD chính; api-contracts khi thay contract validation |
| F | 3.01, 3.19 | Backend/Contracts | 01, 03, [04](../../rules/04-data-storage.md), 06 | TDD; api-contracts cho public schema/consumers |
| G | 3.09, 3.10 | [DevOps/Runner](../../agents/devops-runner.md) | 06, [10](../../rules/10-runner-security.md), [12](../../rules/12-ci-dependencies.md) | security-review cho runner; TDD cho dispatch/outcome/error behavior |
| H | 3.11 | [Frontend/Dashboard](../../agents/frontend-dashboard.md) | 02, 03, 06 | [ui-design](../../../.agents/skills/ui-design/SKILL.md) khi thiết kế; [accessibility-review](../../../.agents/skills/accessibility-review/SKILL.md) khi kiểm semantics/focus; [webapp-testing](../../../.agents/skills/webapp-testing/SKILL.md) khi kiểm browser |
| I | 3.12 | QA/Research | 06, [11](../../rules/11-research-evaluation.md), 13 | [evaluation-integrity](../../../.agents/skills/evaluation-integrity/SKILL.md) cho manifest/split/labels/claims |
| J | 3.13, 3.20 | Coordinator, QA/Research, [Reviewer](../../agents/reviewer.md) | [05](../../rules/05-git-pr.md), 06, 11, 13, [14](../../rules/14-enforcement.md) | evaluation-integrity cho pilot/claims; webapp-testing cho UI acceptance; security-review nếu review runner/provider boundary |

Chọn một skill chính theo bước đang làm; mở thêm khi trigger khớp. Đọc SKILL.md trước áp dụng. [systematic-debugging](../../../.agents/skills/systematic-debugging/SKILL.md) dùng khi lỗi chưa rõ nguyên nhân, kèm [rule 07](../../rules/07-debugging-change-control.md); [github-actions-hardening](../../../.agents/skills/github-actions-hardening/SKILL.md) chỉ khi tạo/sửa/review workflow; [ux-research](../../../.agents/skills/ux-research/SKILL.md) chỉ khi thực hiện nghiên cứu usability. Không có skill Gemini/PostgreSQL riêng trong danh mục hiện tại. Profiles không khởi sub-agent, rules/skills không cấp thêm quyền công cụ.

## 6. Hướng dẫn thực hiện theo thành viên

Mỗi task dưới đây dùng nhóm định tuyến A–J ở trên. Các paths là phạm vi dự kiến, phải xác nhận trên baseline nhận việc. Thư mục nguồn có thể chưa hiện diện trong checkout cũ: dùng [cây backend trên main][backend-main] để khảo sát, không tạo lại module đã có. Mọi checks ở phần này là **cần chạy khi triển khai**, không phải kết quả của việc viết guide. Xem [bộ checks](#checks) cho command và điều kiện runtime.

### Nguyễn Tấn Huy — nền trước, tích hợp sau

#### Task 3.14 — Readiness, 6h · nhóm A

- **Bắt đầu/input:** làm đầu tiên; đọc workbook Reports, main source/decisions, Sprint 2 handoffs, provider/data requirements. Phạm vi bước readiness là reconciliation/ghi quyết định; không tự chạy live.
- **Thực hiện:** ghi SHA và khoảng thiếu G0; tách việc tích hợp còn lại. Xác minh Gemini model/SDK/structured output bằng tài liệu nhà cung cấp hiện hành; ghi nguồn/ngày. Xác định fixture được gửi, nơi giữ key, hard limits và cách đo usage/cost trước live.
- **Đầu ra/AC:** readiness record có phần sẵn sàng/chưa sẵn sàng, baseline và compatibility evidence. Model/budget/egress không còn giá trị suy đoán khi chuyển 3.16; G0 có actual combined-main checks.
- **Kiểm chứng:** ancestry/source diff, consumers/schema/migration head, data authorization; cases thiếu key/quyền/ngân sách/model support được ghi blocker, không lấp bằng default tùy ý.
- **Bàn giao:** cho chính H1 ở 3.15/16 và VI ở 3.12; đính nguồn, config không chứa secret, G0 evidence hoặc remaining prerequisite. Reviewer chỉ ghi khi có review thật.

#### Task 3.15 — Contracts/application boundaries, 10h · nhóm B

- **Bắt đầu/input/path:** G0 và 3.14; đọc `contracts/`, `application/`, `core/`, `composition.py`, CLI và UI consumers dưới [backend][backend-main]/[frontend][frontend-main]. KH góp ý storage; H2/VI góp ý proposal/report.
- **Thực hiện:** định nghĩa request/proposal/selection/result/error tối thiểu, version/identity/provenance và các trạng thái partial/not-run/null. Tái dùng models/stages, không buộc một report “đã chọn test” để biểu diễn proposal-only. Chốt compatibility/migration impact, export/generate bằng tooling.
- **Đầu ra/AC:** backend canonical contracts, valid/invalid fixtures và consumer mapping thống nhất; SDK không vào core. Contracts cho manifest/outcomes đủ để KH/AN chuẩn bị mà không chờ runner.
- **Kiểm chứng:** optional/default/null/unknown fields, wrong IDs/SHA, partial/not-run; backend tests, exporter/generated drift và frontend typecheck/consumer checks.
- **Bàn giao:** H2/KH/AN/VI nhận schema/fixture/version; H1 là shared writer. Review đề xuất H2/VI; không tự ghi approved.

#### Task 3.04 — Gemini adapter, 14h · nhóm C

- **Bắt đầu/input/path:** G0, 3.14/15; interface và typed contracts; `adapters/llm/`, core port phù hợp và `composition.py`.
- **Thực hiện:** map typed request/response, tách SDK ở adapter, inject implementation; phân loại success/refusal/auth/quota/transport và malformed/empty/truncated output. Dùng cấu hình do 3.16 sở hữu, không duplicate retry/workflow ở adapter.
- **Đầu ra/AC:** structured proposal và typed failure, không model-generated executable command hoặc secret trong report/log. Chưa cần full selector/runner.
- **Kiểm chứng:** fake-provider offline cho success và từng error boundary, schema rejection/import direction; Ruff và tests liên quan. Actual live smoke thuộc 3.16.
- **Bàn giao:** cho H1 3.16/17, AN 3.07 và H2 3.05; error map, fixture và limits. Review đề xuất H2.

#### Task 3.16 — Config/budget/live smoke, 12h · nhóm C

- **Bắt đầu/input/path:** G0, 3.14/15/04; verified provider docs và quyền dùng fixture/budget. Config/composition/provider adapter và opt-in verification phù hợp; key qua backend environment, không `VITE_*`.
- **Thực hiện:** pin exact model; context/output caps, shared deadline, attempts và transient retries hữu hạn; chống retry vượt budget/tính phí lặp. Redact telemetry; không tự đổi model. Đầu tiên offline, sau đó một live synthetic-fixture smoke trong scope được phép.
- **Đầu ra/AC:** G1 artifact có actual model/config, timestamp/latency và usage khi provider trả; unknown cost/usage giữ null. Nếu chưa tính được cost, phải có cách chặn ngân sách trước live; không ghi cost=0 để tiếp tục.
- **Kiểm chứng:** missing key, auth/quota/refusal, timeout, exhausted retry/deadline/context/output/budget; live tách unit suite. Không in key/raw-sensitive prompt.
- **Bàn giao:** G1 evidence cho 3.17, error/budget map cho AN, version/config cho H2/VI. Review đề xuất H2.

#### Task 3.17 — CLI/application và G2, 10h · nhóm B

- **Bắt đầu/input/path:** G0/G1, 3.15, actual frozen context/inventory Sprint 2; `application/analysis.py`, `cli/main.py`, `composition.py` và producer interfaces hiện hành.
- **Thực hiện:** nối CLI → application → adapter; minimal bounded context và schema/ID/snapshot guards; giữ run/stage/failure identity. Guard nền dùng lại được; 3.05/18 bổ sung coverage, không rebuild một luồng song song.
- **Đầu ra/AC:** proposal flow dùng input thực của fixture kiểm soát; selection/execution còn not_run nếu chưa triển khai. Framework merge main và CI/checks pass trước dependent implementation.
- **Kiểm chứng:** offline integrated valid/error/no-context/wrong-snapshot cases; permitted live proposal với baseline inputs trong egress đã chốt. Lưu exact command/fixtures và redacted report; không tự bịa cờ CLI Gemini trước khi implement.
- **Bàn giao:** G2 contract/command/main SHA/CI/limits cho cả nhóm, chỉ rõ extension points. Review đề xuất H2.

#### Task 3.13 — Integrated pilot/handoff, 12h · nhóm J

- **Bắt đầu/input/path:** G2, 3.01–12/18/19 ready; frozen pilot manifest 3.12 và module evidence. Phạm vi là workflow tích hợp, harness/evidence và sửa lỗi integration có owner phối hợp.
- **Thực hiện:** actual live Gemini → validation/selection hoặc fallback → manifest freeze → isolated execution → DB read-back → report/UI. Ghi attempt ledger cả failed/excluded runs, environment/model/prompt/budget và deviations.
- **Đầu ra/AC:** tái lập được theo main SHA; không nhầm mock/live, recommendation/dispatch hay failed fallback/pass. Không suy reduction/retention chưa đo; evidence đủ cho 3.20.
- **Kiểm chứng:** happy path, provider failure, invalid evidence/ID, config-change và runner failure; DB/report round-trip, browser và final-main CI/checks. Dùng cùng frozen identities suốt luồng.
- **Bàn giao:** AN nhận commands/artifacts/limitations/task AC matrix để tổng hợp; H1 chịu trách nhiệm giải thích quyết định/code AI hỗ trợ. Review đề xuất AN.

### Phạm Phan Hoàng Huy — context, validation, selection, reasons

#### Task 3.18 — Bounded context/prompt/egress, 12h · nhóm C

- **Bắt đầu/input/path:** G2, 3.15 và initial context 3.17; `core/retrieval/`, application context/LLM boundary. Đọc ADR 0003/0004, không xây lại retrieval storage.
- **Thực hiện:** version prompt/packing/relevance/truncation; lấy bounded verified bytes, giữ repo/SHA/path/range và base/target riêng. Áp dụng source authorization/exclusions trước egress, giữ incomplete/truncated state.
- **Đầu ra/AC:** context xác định được nguồn, không secrets/evaluator labels; source/comment không thay policy/tools. Empty retrieval khác lỗi hoặc thiếu context.
- **Kiểm chứng:** deterministic packing, token/context cap, injection, secret leakage/redaction, stale snapshot và empty/truncated cases; offline tests và review data flow.
- **Bàn giao:** 3.05/H1 nhận prompt/config/version, fixtures và limitations; review đề xuất AN.

#### Task 3.05 — Gemini ID/evidence validation, 12h · nhóm D

- **Bắt đầu/input/path:** G2, 3.18, proposal contract 3.15; `core/selection/`, `core/evidence/`, application resolver và trusted snapshots.
- **Thực hiện:** kiểm schema, exact native IDs/membership, repo/allowed SHA, evidence bytes/path/range và mức hỗ trợ lý do. Tách wrong identity khỏi unsupported semantic evidence; giữ rejection reasons cho policy.
- **Đầu ra/AC:** JSON đúng chưa đủ để accepted; model confidence không override guard. Unknown L/support sai không bị silently drop thành dependency-only; wrong snapshot phải stop.
- **Kiểm chứng:** unknown/duplicate/parameterized IDs, forged/tampered evidence, wrong commits/ranges, unsupported reasons và injection; đối chiếu resolver thật, không mock toàn bộ validation.
- **Bàn giao:** 3.06 và AN nhận validation outcomes/decision fixtures; review đề xuất AN.

#### Task 3.06 — Conservative selection, 14h · nhóm D

- **Bắt đầu/input/path:** G2/3.05; interfaces 3.02/07/08, finalizer 3.01; `core/selection/` và application orchestration. Policy nguồn là [s1-selection-v1][policy].
- **Thực hiện:** validate membership rồi tính S=(D∪M∪L)∩T, not-selected=T−S; giữ inventory order và ghi dedup. Nối validation/fallback của AN, kết quả cho KH freeze; không duplicate decision table trong CLI/UI.
- **Đầu ra/AC:** L không loại D/M; partition đầy đủ T, provenance/mode/trigger rõ. Áp dụng ưu tiên stop/full-suite/provider-only ở mục 7; thiếu runner eligibility không được dispatch.
- **Kiểm chứng:** happy hybrid, valid duplicates, invalid D/M, simultaneous triggers, invalid L/support, partial analysis, empty S/T và leakage boundary. Integration parity với validators/finalizer thật.
- **Bàn giao:** manifest writer KH, reasons 3.03 và AN nhận policy/config revision/test matrix; review đề xuất AN.

#### Task 3.03 — Reasons selected/not-selected, 12h · nhóm D

- **Bắt đầu/input/path:** G2, 3.05/06, manifest contract 3.01; selection decision/reason builders, evidence resolution và report serialization.
- **Thực hiện:** gắn dependency/modified/validated-LLM reasons theo test hoặc nhóm tường minh; bảo toàn allowed base evidence cho deleted code và target inventory. Không tự suy “không rủi ro” từ not-selected.
- **Đầu ra/AC:** decision coverage truy vết được; references resolve và đánh giá support; uncertainty/missing support không thành lý do chắc chắn.
- **Kiểm chứng:** reason coverage, wrong range/SHA, deleted/base evidence, missing support; DB/report read-back khi nối 3.19; contracts/consumer checks nếu shape đổi.
- **Bàn giao:** VI tiêu thụ reasons, KH persist metadata; review đề xuất AN.

### Trần Hưng Khánh — manifest, PostgreSQL và runner

#### Task 3.01 — Freeze manifest, 12h · nhóm F

- **Bắt đầu/input/path:** G2, 3.15 manifest contract; `core/selection/`, application finalization/storage boundary. Có thể xây finalizer từ fixture trước khi policy producer hoàn tất.
- **Thực hiện:** dựng immutable manifest từ decision đã validate; bind run/repo/target, inventory/config/policy hashes, exact selected/not-selected, reasons/mode/digest. Nối validator 3.02; không âm thầm sửa payload lỗi.
- **Đầu ra/AC:** freeze trước dispatch/evaluator join; cùng payload replay ổn định, conflicting payload bị reject. Hoàn thiện tích hợp với 3.06/07/08 trước runner.
- **Kiểm chứng:** round-trip, deterministic ordering/hash, replay/conflict, partition validation và freeze-before-execution; tests/storage boundary theo impact.
- **Bàn giao:** AN/H2 dùng manifest contract/fixtures; 3.09 nhận immutable artifact. Public schema qua H1; review đề xuất AN.

#### Task 3.19 — Persistence, 14h · nhóm F

- **Bắt đầu/input/path:** G2/3.15, contracts 3.01 và result design 3.10; không chờ actual runner. Tái dùng `adapters/storage/`, application stores và `migrations/` trên [main][main-source].
- **Thực hiện:** chỉ bổ sung schema/payload cần thiết; bind run/repo/target/inventory/config/model/prompt/policy. Giữ immutable selection/outcomes, replay/conflict, payload caps và secret/log redaction; một forward migration chain từ head thật.
- **Đầu ra/AC:** PostgreSQL typed read/write nhất quán; unknown usage không thành zero; không viết lại storage service. SQL/filesystem publication failure/retry không tạo dữ liệu “ready” sai hoặc xóa artifact khi commit outcome chưa rõ.
- **Kiểm chứng:** dedicated real PostgreSQL upgrade, transaction/rollback/retry/conflict/read-back; concurrency/ambiguous commit, restart/recovery và artifact consistency phù hợp phần thêm. Fake/SQLite không thay runtime acceptance; không dùng DB cá nhân/shared production.
- **Bàn giao:** H1/3.09/10/VI nhận store interfaces, migration head và reproduction evidence. KH là migration writer, H1 điều phối contract; review đề xuất AN.

#### Task 3.09 — Isolated execution, 18h · nhóm G

- **Bắt đầu/input/path:** G2; 3.01/02/06/07/08 ready, storage interface 3.19; `core/execution/`, `adapters/runners/` và harness có sẵn. Chỉ approved repositories/prebuilt environments.
- **Thực hiện:** nhận frozen target/validated native IDs bằng argument vector; worker riêng, không execute input code trong web/application process. Áp dụng filesystem/network/secrets/CPU/memory/time/output limits và cancellation/cleanup cho cả process con.
- **Đầu ra/AC:** selected/full-suite dispatch đúng identity/mode, reject wrong SHA/ID; không privileged, Docker socket, production key hoặc model-generated shell. Container một mình không chứng minh isolation.
- **Kiểm chứng:** actual isolated selected/full runs; tampered manifest/ID, timeout/crash/cancel, output/resource limits và cleanup evidence. Phân biệt test failure với runner/setup/infrastructure failure.
- **Bàn giao:** 3.10 nhận bounded execution events, H1/AN nhận eligibility/failure evidence; review đề xuất AN.

#### Task 3.10 — Outcomes/errors, 12h · nhóm G

- **Bắt đầu/input/path:** G2, 3.09, result contract 3.15, persistence 3.19; execution result adapter/store và report mapping.
- **Thực hiện:** normalize actual outcomes/durations/redacted bounded logs, đối chiếu dispatched/observed IDs. Giữ recommendation, actual dispatch và execution status riêng.
- **Đầu ra/AC:** phân biệt not-selected, runner-skipped, assertion/setup/build failure, timeout/cancel/infrastructure; missing/unexpected IDs làm rõ execution chưa đầy đủ. Failed tests không trở thành fault labels.
- **Kiểm chứng:** selected/full/skipped, collection/setup/assertion error, truncated log, incomplete run và unknown duration; DB/report round-trip, producer-consumer parity.
- **Bàn giao:** VI hiển thị outcomes; H1/AN dùng pilot/acceptance. Review đề xuất AN; schema đổi phối hợp H1.

### Đỗ Hà An — validation, fallback và kiểm chứng cuối

#### Task 3.02 — Manifest/inventory validator, 10h · nhóm E

- **Bắt đầu/input/path:** G2, 3.15 và **contract** 3.01; không đợi producer hoàn tất. Shared validation trong contracts/core/application boundary phù hợp, phối hợp H1 nếu đổi schema.
- **Thực hiện:** validate frozen identity/hash, exact membership, unique/disjoint selected/not-selected và đầy đủ T. Không “repair” unknown ID bằng intersection.
- **Đầu ra/AC:** reject wrong SHA/config/hash, overlap/duplicate/missing/unknown IDs; failed/partial inventory không thành complete classification. T rỗng hợp lệ phân biệt discovery failure.
- **Kiểm chứng:** positive/negative fixtures, exact parameterized nodeids, empty/partial T; parity với final producer KH trước runner.
- **Bàn giao:** KH/H2 nhận reusable validator và error fixtures; review đề xuất H2.

#### Task 3.07 — Provider-only fallback, 8h · nhóm E

- **Bắt đầu/input/path:** G2, 3.15 và typed provider failures 3.04/16; selection/fallback policy boundary, không tự gọi SDK từ validator.
- **Thực hiện:** map timeout/malformed/empty/refusal/quota/budget failure vào configured policy; giữ trigger và final mode. Chỉ dùng D∪M khi prerequisites đủ và policy cho phép; empty result cần full suite đủ điều kiện hoặc stop.
- **Đầu ra/AC:** provider failure không che invalid evidence/incomplete analysis; retry/budget hết không được vượt hard limits hoặc silently succeed.
- **Kiểm chứng:** deadline/retry exhaustion, quota/refusal/output errors và multiple triggers; chứng minh invalid support không bị xếp provider-only.
- **Bàn giao:** H2 nối policy, KH dispatch mode; review đề xuất KH.

#### Task 3.08 — Incomplete/config-change fallback, 10h · nhóm E

- **Bắt đầu/input/path:** G2, 3.15/02; parser/mapping limitations và runner eligibility contract; shared fallback module cùng 3.07, không policy copy riêng.
- **Thực hiện:** áp dụng stop/full-suite cho partial parsing, unresolved rename/delete mapping, build/config/dependency change và invalid L/support. Wrong snapshot/failed-partial T/invalid D-M phải stop trước.
- **Đầu ra/AC:** complete empty T → no_tests; full suite chỉ khi trusted T, exact target và approved bounded environment. Runner không khả dụng hoặc fallback fail không báo safe/passed.
- **Kiểm chứng:** unsupported code, rename/delete gaps, unknown L, invalid support, combined triggers và unavailable runner; decision-table integration với 3.06/09.
- **Bàn giao:** H2 nhận policy outcomes/precedence cases, KH cung cấp eligibility; review đề xuất H2.

#### Task 3.20 — Final acceptance evidence, 4h · nhóm J

- **Bắt đầu/input/path:** actual 3.13 evidence sau module-level tests; task AC/evidence matrix và final main revision, không xây lại toàn bộ QA trong 4h.
- **Thực hiện:** map từng task AC tới exact SHA/command/environment/artifact; kiểm final integration, migration head, contract/UI consistency, G0/G1/G2 và remaining failures.
- **Đầu ra/AC:** coverage evidence đủ, thiếu gì vẫn mở ở owning task; không fabricated Done/approval. Giữ failed/excluded/unverified cases và actual review status.
- **Kiểm chứng:** final-main CI/regression/runtime/browser links; tái lập có chọn lọc khi evidence chưa đủ hoặc baseline thay đổi. Kết quả từ nhánh cũ không tự áp dụng cho main mới.
- **Bàn giao:** H1 nhận closeout summary, limits và remaining items. Review đề xuất H1; cùng phiên agent chỉ là self-review, không independent human review.

### Đặng Đại Việt — report UI và pilot inputs

#### Task 3.11 — Dashboard report, 18h · nhóm H

- **Bắt đầu/input/path:** G2/3.15; generated types và actual stage report tại [frontend main][frontend-main], `frontend/src/features/reports/`, app/components/styles. Nghiệm thu cuối với 3.03/10/19.
- **Thực hiện:** mở rộng file-report UI cho Gemini provenance, selection/reasons/fallback, recommendation/dispatch/outcomes, timing và known usage/cost. Dùng runtime nested validation, tái dùng design hiện tại; không thêm auth/history/API flow.
- **Đầu ra/AC:** malformed nested report bị reject; unknown ≠ zero; not-selected ≠ runner-skipped; failed fallback không nhìn như pass/safe. DEMO và real có nhãn rõ.
- **Kiểm chứng:** contract/validation fixtures, lint/typecheck/build/contracts check; browser thực cho file loading/rejection/recovery, long paths, keyboard/focus và narrow viewport. HTTP 200/SSR/typecheck không thay browser evidence; A07 waiver Sprint 2 không áp dụng ở đây.
- **Bàn giao:** H1/AN nhận report fixtures và browser/URL/states/results/limitations. Public contract qua H1; review đề xuất AN.

#### Task 3.12 — Pilot manifests/cases, 12h · nhóm I

- **Bắt đầu/input/path:** G2, data/budget constraints 3.14; existing candidate/environment evidence, research protocol và pilot manifest location chốt khi nhận task. Trước G2 chỉ khảo sát permissions/candidates.
- **Thực hiện:** freeze approved repo/base-target SHA, license/provenance, environment/inventory hashes, eligibility/exclusions, split/config trước run. Tái dùng candidate phù hợp; không mặc định nguồn public là được gửi/chạy ở mọi môi trường.
- **Đầu ra/AC:** tuning/pilot tách held-out evaluation, fault-bearing claims có independent provenance/adjudication hoặc ghi unverified. Không tuyên bố đủ full PB23 dataset targets.
- **Kiểm chứng:** replay manifest, permission/license/exclusions, leakage boundary và frozen config; cùng fault/fix/near-duplicate không chia gây leakage. Sample/repeats/rubric được chốt trước comparative claims, không chọn sau khi thấy kết quả.
- **Bàn giao:** H1 chạy 3.13; AN review provenance/leakage. Giữ selector inputs tách evaluator-only outcomes/labels.

## 7. Policy và ranh giới kỹ thuật dùng chung

### Selection/fallback

Theo [policy accepted s1-selection-v1][policy]: T là complete native target inventory; D là dependency tests; M là added/modified/renamed target tests; L là LLM additions có support hợp lệ. Deleted base test có thể là evidence, không phải runnable target ID.

Validate membership **trước** S=(D∪M∪L)∩T. L không loại D/M. selected và not-selected unique/disjoint, union bằng T, giữ inventory order; valid input duplicates được ghi/dedup, manifest cuối không chứa duplicates. Không dùng intersection để làm mất unknown required IDs.

| Ưu tiên | Điều kiện | Kết quả bắt buộc |
| --- | --- | --- |
| 1 | Wrong repo/snapshot/SHA; failed/partial T; invalid required D/M | Stop; các trigger khác không override |
| 2 | Prerequisites hợp lệ và T rỗng | no_tests; không phải passing regression check |
| 3 | Invalid L/support hoặc incomplete analysis/config-change/unresolved mapping | Eligible full suite hoặc stop, kể cả đồng thời provider timeout |
| 4 | Chỉ provider failure, D/M complete/valid và configured policy cho phép | D∪M; nếu rỗng với T không rỗng thì eligible full suite hoặc stop |
| 5 | Các input hợp lệ | Freeze hybrid S; S rỗng với T không rỗng vẫn cần eligible full suite hoặc stop |

Full-suite eligibility cần exact frozen target, trusted complete T, authorized compatible prebuilt environment và enforced isolation/time/output/resource limits. Thiếu eligibility chặn dispatch. Budget exhaustion không bỏ qua prerequisites. Actual fallback failure giữ execution/infrastructure failure, không báo safe/passed.

### Provider, execution và dữ liệu

- API/CLI → application → core/interfaces; adapter implement port, composition root nối config. SDK Gemini không vào core; backend models/stages là contract source, artifacts sinh qua tooling.
- Gemini key chỉ backend, không frontend/log/prompt/shared artifacts. Pin verified model; ghi prompt/config version và actual usage; không silent model switch. Shared deadline/attempt/token/cost caps phải có cách enforcement trước live; unknown usage/cost là null/N/A.
- Source/comments/RAG/model output không có quyền đổi policy/tool permissions. Structured JSON chưa chứng minh ID/evidence/semantic support đúng. Source egress chỉ theo quyền đã ghi; base/target provenance riêng.
- Runner worker nằm ngoài web/application process; argument vector, authorized paths và identities; không dùng shell từ model. Kiểm network/install hooks, symlinks, resources, child-process cancellation và cleanup, không chỉ nhãn UI.
- PostgreSQL dùng foundation hiện có, một migration chain. Freeze manifest trước execution/evaluator join; persist immutable provenance và explicit retry/conflict/failure. Không log raw sensitive content hoặc coi rollback migration là data recovery.

### Pilot và trách nhiệm AI

Freeze commit/environment/inventory/model/prompt/budget/config trước so sánh; outcomes/labels/future commits không vào selector/retrieval. Phân biệt real fault, mutation, flaky và infrastructure. Test fail không tự thành confirmed fault; một fault nhiều failing tests vẫn là một fault ID.

Theo [rule 11](../../rules/11-research-evaluation.md), planned selection reduction khác actual dispatch reduction; time boundary gồm overhead đã khai báo, saving có thể âm. Không có ground truth/mẫu số hợp lệ thì retention/accuracy là N/A. Lưu failures/exclusions và uncertainty; pilot nhỏ không chứng minh benchmark hoàn chỉnh.

[Proposal Appendices C/D](../../../C1.SE26_DOCUMENTS/C1SE26_SmartRegression_AI_Proposal_Merged_v1.4.docx) yêu cầu sinh viên review, hiểu và xác minh AI output. Handoff/PR ghi tool, mục đích, giai đoạn/phạm vi và checks thực; không bịa contribution ratio, chữ ký hoặc mentor approval. Guide được Codex hỗ trợ đối chiếu/soạn/self-review theo yêu cầu Huy; chưa khẳng định nhóm đã review tài liệu mới.

<a id="checks"></a>
## 8. Kiểm chứng khi triển khai

Các lệnh sau đã đối chiếu định nghĩa với [verified commands trên main][main-commands], manifests/scripts tại baseline. **Không chạy chúng trong task viết guide này.** Cwd root; chọn locked runtime đang được dự án hỗ trợ. Trước dùng, đọc lại phiên bản command theo main nhận việc; phần snapshot cũ trong verified commands không thay kết quả mới.

| Khi nào | Checks cần thực hiện |
| --- | --- |
| Đổi Python behavior | Focused pytest theo test thực tế của task, `uv run ruff check .`, `uv run ruff format --check .`; gate regression/CI rộng hơn theo impact |
| Đổi public contracts | Sửa source → `uv run python scripts/export_contracts.py` → `npm --prefix frontend run contracts:generate`; sau đó exporter `--check`, `npm --prefix frontend run contracts:check`, backend fixtures và frontend typecheck/consumer checks |
| Đổi frontend | `npm --prefix frontend run lint`, `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`, contracts check nếu liên quan; browser theo luồng 3.11 |
| Đổi persistence/migrations | Đọc [storage setup trên main][pg-setup] và `scripts/storage/run_checks.py`/`scripts/storage/verify.ps1`; dedicated PostgreSQL upgrade/read-back/failure/recovery theo phạm vi. Kiểm opt-in skips, DB/runtime URL và environment trước chạy |
| Đổi inventory/mapping | Đọc wrappers `scripts/inventory/verify_complete.ps1`, `scripts/mapping/verify.ps1` trên main; dùng approved isolated environments và options thật, không thực thi input repo trực tiếp trên host |
| Tích hợp/regression | `uv run pytest` và gates liên quan; wrapper `scripts/integrity/verify.ps1` hiện có trên main phải đọc coverage/options trước dùng. Subset pass không thay full relevant gate |
| Gemini/selection/runner Sprint 3 | Focused offline tests và opt-in runtime harness cần được bổ sung trong owning task. Chưa có command Sprint 3 đã xác minh tại baseline; không bịa `gemini-smoke`, CLI flags hay `npm test` |

Mỗi evidence ghi command đầy đủ, cwd, SHA, environment/config/fixture, timestamp, exit/result, artifact và giới hạn. Unit/mock khác actual live/DB/isolated runner/browser. Có key chỉ ở runtime hợp lệ; không đưa credentials vào command được lưu/chia sẻ. Không chạy production/shared DB để chứng minh một migration.

Nếu gặp lỗi: dùng systematic-debugging, tái hiện nhỏ nhất, tách môi trường/quyền/dependency khỏi code failure; không skip test, giảm gate hoặc thêm permissive fallback để báo pass. Không có browser tool thì ghi chưa kiểm chứng và giữ UI acceptance mở; waiver Sprint 2 A07 và A02/A03 browser subchecks không áp dụng cho Sprint 3.

## 9. Làm việc với AI agent và clean code

Mỗi lần giao một behavior/đầu ra, ghi rõ task và giới hạn paths. Agent đọc implementation/callers/fixtures trước viết; tận dụng module/interface hiện có, chỉ thêm abstraction phục vụ consumer thật. Không rewrite hệ thống, duplicate DTO/decision table, tạo generic framework, fake success hoặc đổi dependency cho helper nhỏ. Không sửa generated types/lockfiles bằng tay.

Với behavior/bug test được: xác định expected boundary, thêm hoặc chọn regression test có ý nghĩa, quan sát failure khi phù hợp, sửa tối thiểu rồi chạy focused + related checks. Không tạo test chỉ mirror implementation hay mock hết nghiệp vụ. Không dùng lời hứa “không bug” thay bằng chứng và limitations.

<a id="prompt-agent"></a>
### Mẫu prompt theo task

Điền đủ placeholder từ brief ở mục 6, kể cả baseline và scope. Nếu chia một task thành nhiều phiên, truyền handoff gần nhất và nói phần nào đã có evidence; không yêu cầu agent audit toàn repo hoặc nạp mọi skill.

```text
Bạn hỗ trợ <tên thành viên> tại D:\smart-regression-ai.
Thực hiện task <3.xx — tên>, đầu ra phiên này: <behavior/artifact>.
Đọc AGENTS.md áp dụng, Sprint 3 team guide mục task, backlog brief,
<profile>, <rules>, <skill chính và trigger>. Mở thêm skill khi cần boundary thật.
Baseline: <main SHA đã xác minh>; gate/dependency: <đạt hoặc còn thiếu>.
Đọc thêm: <contract/policy/handoff/producer/consumer cụ thể>.

Chỉ sửa <paths/scope>. Shared writer: <người/module>; không sửa <ngoài scope>.
Kiểm tra root/branch/status, bảo toàn thay đổi có sẵn và implementation đang có.
Nếu prerequisite thiếu, tiếp tục phần độc lập, ghi blocker; không tạo mock-success
để vượt gate. Không thay owner/estimate/policy đã chấp nhận.

Acceptance: <các điều kiện quan sát được và edge cases>.
Tận dụng cấu trúc sẵn có, thay đổi nhỏ, không thêm abstraction/dependency suy đoán.
Thực hiện code/test trong scope; chạy <focused checks và runtime checks được giao>.
Live/provider/source-egress/input-execution chỉ theo <fixture/quyền/budget/môi trường>;
nếu chưa có quyền tương ứng, giữ phần đó chưa chạy, không tự suy quyền từ guide.

Báo: thay đổi/lý do, contract/consumer impact, command/cwd/kết quả thực,
checks chưa chạy và giới hạn, evidence/handoff cho <người/task>.
Không tự commit/push/mở PR/merge khi chưa được giao riêng.
```

### Ví dụ bắt đầu 3.14 cho Huy

```text
Hỗ trợ Nguyễn Tấn Huy làm 3.14: reconciliation và readiness record trước code Gemini.
Đọc AGENTS.md, guide task 3.14/nhóm A, Sprint 3 Reports, decision register/ADR/policy
hiện hành. Kiểm tra Git và fetch main nếu có thể, ghi SHA; không checkout/reset đè tree.
Đối chiếu G0 source/contracts/migration/consumer; tách integration Sprint 2 còn thiếu
và estimate riêng, chưa thực hiện integration trong phiên readiness này.
Xác minh model/SDK/structured output bằng nguồn Gemini chính thức hiện hành;
lập bảng permitted data/egress, secret handling, hard budgets, price/usage evidence.
Áp dụng security-review cho trust boundary, không in secret.
Chỉ đọc source; đầu ra là readiness/handoff trong phản hồi, chưa sửa file/code,
chưa live call hoặc chạy input repo. Ghi pending và điều kiện để chuyển 3.15/16.
Không commit/push/PR/merge. Không tự bịa model, budget hay claim G0 đã đạt.
```

## 10. Tích hợp, PR và bàn giao

### Một writer điều phối file chung

| Người | Vùng điều phối | Cách phối hợp |
| --- | --- | --- |
| H1 | Canonical contracts, application workflow, composition/config; dependency chung khi cần | Consumer gửi yêu cầu/fixture; H1 điều phối source/export/generate, không có hai bản DTO |
| KH | Migration chain, storage, manifest/runner | Chốt store/result interfaces với H1; chỉ một migration writer từ head thật |
| H2 | Prompt/context/selection/reasons | Dùng validation/fallback của AN; không copy policy vào UI/CLI |
| AN | Validation/fallback/decision fixtures | Phối hợp H2 về precedence, KH về manifest/eligibility |
| VI | UI/pilot manifests | Dùng generated types và actual report; contract đổi qua H1 |

Mỗi thành viên dùng branch/worktree riêng khi được giao implementation; không nhiều writer chung working tree. Thỏa thuận thứ tự sửa file chung và handoff revision. Không reset/clean/force push để giải conflict; không chỉnh required checks/quyền GitHub. Profile Reviewer không tạo independent approval.

### Nhóm PR đề xuất

| Slice | Task | Điều kiện review/integrate |
| --- | --- | --- |
| Foundation contracts | 3.15, sau readiness 3.14/G0 | Contract fixtures + generated/consumer checks; H2/VI review đề xuất |
| Gemini adapter/config | 3.04/16; có thể tách hai PR khi đủ lớn | Offline failure matrix và G1 live evidence tách biệt |
| CLI/G2 | 3.17 | Actual-input proposal flow, main merge + CI trước dependent implementation |
| Context/proposal validation | 3.18/05 | Versioned context, injection/ID/evidence/budget cases |
| Validators/fallback | 3.02/07/08; có thể tách theo behavior | Interfaces thống nhất H2/KH; decision-table negatives |
| Manifest/persistence | 3.01/19; tách nếu migration lớn | Replay/conflict + real PostgreSQL; chưa claim full runner flow |
| Selection/reasons | 3.06/03 | Validator/fallback/manifest interfaces sẵn sàng; integration parity |
| Runner/outcomes | 3.09/10 | Actual isolated execution, failure/cleanup và storage read-back |
| UI và pilot inputs | 3.11, 3.12 thường hai PR riêng | UI contracts/browser; pilot manifest/provenance freeze |
| Integration/acceptance | 3.13/20 | Evidence trên final integrated main, remaining failures rõ |

Đây là cách chia theo đầu ra, không bắt buộc một task một PR. PR ghi base/dependency, task/AC, behavior trước/sau, tests thực, contract/migration impact, risk/limits và AI disclosure theo [template](../../../.github/pull_request_template.md). Author xin review sau self-check; reviewer trong guide là **đề xuất**, chưa phải đã approve.

Có thể chuẩn bị PR phụ thuộc trên nhánh nền khi được giao, ghi rõ base. Merge vào feature branch chỉ là tích hợp trung gian. Khi đưa vào main phải kiểm ancestry/source, resolve consumer/migration drift và chạy checks phù hợp với baseline kết hợp; không chuyển evidence của nhánh cũ thành final-main pass. Không mở PR/commit/push tự động chỉ vì guide mô tả quy trình.

### Definition of Ready

- Task/AC/owner/estimate rõ từ workbook; baseline SHA và gate tương ứng có evidence.
- Input/contract/fixture ổn định đủ cho phạm vi; phân biệt mock test input với live acceptance input.
- Paths và shared writer rõ; runtime/data/budget/secret permissions cho bước cần thực hiện được ghi nhận.
- Checks/expected failure cases xác định; nếu dependency thiếu thì khoanh phần độc lập hoặc giữ prerequisite mở.

<a id="done"></a>
### Definition of Done và handoff

- Đạt AC của task trên revision được bàn giao; code sạch trong scope, không placeholder success, không generated drift.
- Focused/module/integration checks theo impact có kết quả thực; runtime yêu cầu live/DB/runner/browser không thay bằng mock/typecheck. Skips và environment failures được báo riêng.
- Contract/consumer/migration/docs liên quan được cập nhật trong task implementation được giao; không thay policy/owner/estimate âm thầm.
- Handoff theo [template](../../templates/handoff.md): task/branch/SHA, behavior/files, source quyết định, contract/version/config, command/cwd/environment/result, redacted artifacts, limits và next owner.
- Trạng thái tách rõ: implemented local → verified trên nhánh → reviewed khi thật sự có review → integrated main. Chỉ ghi task/sprint Done theo AC, quy trình nhóm và evidence trên baseline tích hợp; không suy approval từ CI.

| Mốc nghiệm thu | Evidence cần dẫn, chỉ điền sau khi thực hiện |
| --- | --- |
| G0 | Main SHA, source reconciliation, contracts/consumer và migration head/checks |
| G1 | Live command/fixture/quyền/budget, actual model/config, redacted response/usage |
| G2 | Main merge/CI, frozen context/inventory, proposal artifact, command và limits |
| Selection/fallback | Decision table/negative fixtures, freeze artifact, order/identity/digest |
| Runner/DB | Actual isolated dispatch/outcomes/limits/cleanup, real DB upgrade/read-back/recovery |
| UI | Browser/URL/date, file rejection/recovery, keyboard/focus/narrow viewport |
| Closeout | Attempt ledger/split/config, task AC traceability, final main CI, actual review và pending |

Sau khi có evidence, cập nhật nơi tracking nguồn theo phạm vi task được giao; không ghi pass vào ô bằng chứng đang trống chỉ để đủ checklist. Nếu điều kiện vận hành chưa đủ, bàn giao rõ phần đã đạt và phần còn mở thay vì tuyên bố hoàn tất sprint.

[main-source]: https://github.com/kokoreina/smartregression-ai/tree/ac2f55283c8be865c72ca25308a4e00e5e3a827e
[backend-main]: https://github.com/kokoreina/smartregression-ai/tree/ac2f55283c8be865c72ca25308a4e00e5e3a827e/backend/src/smartregression
[frontend-main]: https://github.com/kokoreina/smartregression-ai/tree/ac2f55283c8be865c72ca25308a4e00e5e3a827e/frontend/src
[main-decisions]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/development/decision-register.md
[main-commands]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/development/verified-commands.md
[adr3]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/architecture/decisions/0003-local-lexical-retrieval.md
[adr4]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/architecture/decisions/0004-sprint-2-integration-decisions.md
[policy]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/research/sprint-1/selection-policy.md
[s2-plan]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/development/sprint-2-completion-plan.md
[pg-setup]: https://github.com/kokoreina/smartregression-ai/blob/ac2f55283c8be865c72ca25308a4e00e5e3a827e/docs/development/postgresql-setup.md
