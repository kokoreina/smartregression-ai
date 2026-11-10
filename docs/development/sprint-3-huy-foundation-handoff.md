# Huy — Sprint 3 foundation và readiness 3.14

**Trạng thái ngày 2026-11-10 (Asia/Bangkok): 3.14 hoàn tất readiness cục bộ,
đủ để triển khai offline 3.04. G0 và 3.15 đã tích hợp main. G1/G2 chưa thực hiện.**
Readiness đã được self-review; independent review được theo dõi riêng trên PR.
Không đóng task trong Excel hoặc tuyên bố Sprint 3 hoàn thành. Các quyết định dưới đây được agent chọn trong
phạm vi Nguyễn Tấn Huy ủy quyền ở brief 3.14, không phải mentor approval.

## 1. Phạm vi và baseline

Đã fetch `origin/main` ngày 2026-11-10, SHA
`f729e6ecb3fdb74093632ca5e3946aac3f087a8b` ([source][main]). Làm việc tại
`D:/smart-regression-ai/var/s3-readiness`, detached worktree từ SHA này. Checkout
gốc vẫn ở `562be12`; các thay đổi Office, guide, outputs và helper có sẵn được giữ.
Không triển khai adapter/config/CLI, không thay dependency hoặc đọc credential.

| Prerequisite | Bằng chứng và kết luận hiện tại |
| --- | --- |
| G0 | [PR #64][pr64] đã vào ancestry main. [Handoff G0](sprint-3-g0-integration.md) ghi source reconciliation và campaign PostgreSQL/Docker/inventory; không chạy lại campaign trong task tài liệu |
| 3.15 | [PR #65][pr65] MERGED; đã đọc lại GitHub review `KaiTrann` trên head `f3893d7ac85448d8fde475c328c935220623a64c`; merge SHA bằng baseline |
| Main checks | [CI 42772254046][ci65] được truy vấn lại: completed/success, head SHA đúng baseline; không coi đây là live Gemini evidence |
| Contracts | [Workflow v3](../contracts/workflow-reports.md), `contracts/workflow.py`, `application/proposals.py`, `core/selection/proposals.py` có trên baseline; wrapper v3 giữ v2 analysis, guards kiểm provenance/ID/evidence và input mutation |
| Consumers/storage | Reader/CLI nhận v1/v2/v3; dashboard và PostgreSQL writer vẫn v2-only. Đây là boundary 3.11/3.19, không phải blocker adapter |
| Runtime chưa có | `adapters/llm/README.md` còn skeleton; chưa có Gemini config loader, adapter hoặc live evidence. Câu “chưa chọn provider” trong README là snapshot cũ, được quyết định D21 thay thế; task này không sửa code/module README |

Nguồn task được đọc read-only từ workbook local
`C1.SE26_DOCUMENTS/SmartRegression_AI_Scrum_Project_Aligned.xlsx`,
`Sprint 3 Backlog!B148:D153`: H1, 6h **estimate**, readiness/compatibility và G0;
model/price/egress phải được xác minh trước live. Team guide local ngày 2026-11-09
chưa tracked trên main; ghi chú G0 pending ở guide là lịch sử, không mở lại G0.
Không sửa workbook/guide, không điền actual effort hoặc giả review của nhóm.

## 2. Quyết định 3.14

Trạng thái “đã chốt” là quyết định thiết kế dưới quyền Huy giao. Chỉ cột bằng chứng
mới cho biết nội dung nào đã được kiểm chứng. Sources S1–S12 ở mục 8.

| Hạng mục | Lựa chọn và lý do | Bằng chứng / trạng thái | Bước tiếp theo |
| --- | --- | --- | --- |
| Provider/model | Gemini Developer API, `gemini-3.5-flash-lite`; stable, chi phí thấp, structured output; không fallback model | Đã chốt; nguồn S1/S2 xác nhận model/capability/giá, chưa xác nhận tài khoản nhóm | 3.04 adapter; 3.16 account/model smoke |
| API/SDK | `google-genai==3.0.0`, stateless `client.models.generate_content`, explicit API `v1` | S3; resolver/install/import và mocked v1 serialization đạt trên Windows/Python 3.14.3. Endpoint/account chưa live-tested | 3.04 pin bằng tooling và offline tests; không tự chuyển API nếu server từ chối |
| Output | Provider DTO nhỏ: `suggestions[{test_id, reason, evidence_ids}]`; local validate lại bằng `TestProposal` | S4 và contract 3.15; mocked schema và canonical revalidation đạt | 3.04 malformed/refusal/truncation tests; 3.05 semantic support |
| Thinking | `ThinkingConfig(thinking_level=MINIMAL, include_thoughts=False)`; không dùng `thinking_budget` | S5/S6; SDK serialize được. Không gửi `candidate_count`, không ép sampling knobs cho foundation | 3.04 verify wire; 3.16 xác nhận server behavior/cap |
| Token preflight | Đếm đầy đủ frozen GenerateContentRequest qua SDK `CountTokensConfig.http_options.extra_body.generateContentRequest`, `contents=None` | S7 và mocked body đạt; direct `system_instruction`/`generation_config` bị SDK từ chối local | 3.04 payload parity; 3.16 endpoint/count coverage gate trước generation |
| Data | First smoke chỉ fixture synthetic ở mục 4; source thật phải có manifest egress riêng | Đã chốt theo scope được Huy giao; chưa gửi dữ liệu | 3.16 synthetic; 3.17 explicit real-source permission |
| Credential | Process env `GEMINI_API_KEY` canonical; explicit backend injection; không auto-read `.env` | Đã chốt; baseline không có Gemini loader. Alias/conflict policy ở mục 5 | 3.16 implement/test |
| Limits/accounting | Mục 6: hữu hạn, fail closed trước generation khi không chứng minh được token/cost bound | Đã chốt thiết kế; chưa runtime enforce, chưa cấp quyền chi API trong phiên này | 3.04 transport/error boundaries; 3.16 ledger/deadline/live gates |

Stable model ID không đảm bảo weights bất biến. Ghi configured model cùng observed
`model_version` khi response có; không tự điền version khi provider không trả.
Model này chưa được benchmark cho regression selection; quyết định chọn model
không chứng minh chất lượng chọn test.

## 3. Compatibility và schema

Đã tạo venv trống, export toàn bộ dependency runtime **và dev** từ `uv.lock`
baseline bằng `uv export --frozen --no-emit-project --no-hashes`; resolve thêm
`google-genai==3.0.0` mà giữ mọi pin cũ. Cài 48 packages; `uv pip check` báo
“All installed packages are compatible”. Không sửa pyproject/uv.lock của repo.

| Thành phần | Phiên bản kiểm thực tế |
| --- | --- |
| Runtime | Windows, CPython 3.14.3; dự án yêu cầu `>=3.14,<3.15` |
| SDK | google-genai 3.0.0; metadata Python >=3.11, Pydantic >=2.12.5,<3 |
| Baseline giữ nguyên | Pydantic 2.13.5; FastAPI 0.142.2; SQLAlchemy 2.1.6; httpx 0.28.1 |
| SDK HTTP namespace | httpx2 2.16.0; resolve/import cùng httpx 0.28.1 được, không kết luận mọi runtime path đã tương thích |

**11 assertions offline đạt, 4 mock HTTP requests, 0 live requests:** v1 generation
path; schema; output cap; minimal thinking serialization; canonical proposal parse;
usage mapping; content-only count; full-request extra-body count; hai local rejects
cho unsupported count config; SDK chỉ một request khi mocked 503 với `attempts=1`.
Socket connect bị chặn trong probe, dùng credential giả cố định; không đọc key thật.

SDK phát hai `SyntaxWarning` về escape `\/` trong docstrings types trên Python
3.14.3; import/probe vẫn đạt. Không sửa vendor code hoặc suppress warning để che lỗi.
Chưa chạy Linux/CI, full application tests hay kiểm wire acceptance của Google.

Schema provider chỉ gồm object/array/string, required/additionalProperties và
array caps; không gửi toàn bộ WorkflowReport/ProposalRequest schema. SDK dùng
`response_mime_type='application/json'`, `response_json_schema=...`, không dùng
`response_format` của Interactions. Nhóm constraints minLength/maxLength/uniqueItems
không được Google đảm bảo enforce (S4); giữ validation canonical ở local.

Adapter gắn provenance từ **request trước call**, không nhờ model dựng SHA, model
identity, usage hoặc trạng thái selection/execution. Refusal/empty/MAX_TOKENS là
typed failure; không parse phần JSON bị cắt thành success. Membership/evidence ID
guards hiện có không thay semantic support validation của 3.05.

**Count request:** API reference S7 nhận `generateContentRequest` đầy đủ. SDK 3.0.0
chặn system instruction/generation config qua fields trực tiếp của CountTokensConfig;
đếm riêng context sẽ thiếu instructions/schema. Chốt dùng public `extra_body`
(không gọi private SDK methods), giữ cùng frozen model/system/contents/schema/config
với generation. Không gửi top-level contents cạnh tranh với full request. Probe đã
kiểm SDK serialization; API reference minh họa v1beta, chưa xác minh full-request
count trên v1. Nếu v1 không hỗ trợ, **dừng live**, ghi failure và cập nhật quyết định
API có bằng chứng trước thử tiếp; không fallback endpoint ngầm.

## 4. Synthetic fixture và egress

Fixture ID `s3-g1-synthetic-v1`, nhãn DEMO; 3.16 tạo artifact bằng constructors/
fingerprint helpers 3.15, không hardcode hash giả thành snapshot thật. Đây là input
smoke, không phải candidate benchmark hoặc bằng chứng runner đã chạy test.

| Thành phần | Nội dung được phép |
| --- | --- |
| Repository | Repository synthetic do harness tạo, không remote/private source; frozen base/target và materialized snapshot IDs do tooling tạo |
| Change | `src/math_demo.py`: `add(a,b)` đổi từ `return a+b` thành `return max(0,a+b)`; `multiply(a,b)` giữ nguyên |
| Complete target inventory | `tests/test_math.py::test_add`, `tests/test_math.py::test_add_negative`, `tests/test_math.py::test_multiply`; giữ đúng chuỗi và thứ tự |
| Context/evidence | `synthetic-e1`: add base/target diff có path/side/location; `synthetic-e2`: synthetic test gọi `add(-2,1)` và assert `-1`. Hash text và reference khớp retrieval; evidence resolution phản ánh việc harness thực sự kiểm |
| Wire allowlist | Test IDs; synthetic diff/excerpts; evidence IDs/path/side/location; instructions/schema/prompt version cần thiết. Backend giữ provenance đầy đủ, chỉ gửi phần cần thiết |
| Output mẫu | Suggest `tests/test_math.py::test_add_negative`, reason về thay đổi phép cộng số âm, evidence `synthetic-e1`/`synthetic-e2`; đây là ví dụ, không ép model sinh đúng một golden sentence |

Smoke thành công khi response hoàn chỉnh, DTO/canonical checks đạt, có ít nhất một
suggestion trong inventory, evidence ID tồn tại và người đọc kiểm được support của
fixture. Không bắt model trả nguyên văn câu mẫu. Empty suggestions không đủ positive
G1 smoke. Unknown/duplicate IDs, evidence lạ, wrong provenance, truncated/refusal
phải có negative offline cases; không cố tình gọi trả phí để tạo lỗi đó.

Prompt không chứa actual test outcomes, fault labels, future fixes, key, username,
absolute workspace paths, raw logs hoặc toàn repository. Một source comment yêu cầu
đổi model/bỏ guard/gửi key chỉ là untrusted content. Tools/function calls/code
execution/grounding/URL context/uploads/cache/multimodal đều tắt; adapter không cấp
quyền runner. Không lưu chain-of-thought hoặc raw prompt/response vào log chia sẻ.

**3.17 source thật:** trước egress phải có manifest local gồm permission/license,
repo ID, base/target SHA/snapshots, allowlisted paths/excerpts, byte/content hashes,
provider/model, purpose/tier và loại trừ secrets/PII/evaluator-only data. Có quyền
clone/read/public license không tự cho phép gửi mọi dữ liệu. Chưa có manifest thì
không gửi source thật. Unpaid terms có thể dùng content để cải thiện sản phẩm và
human review; paid vẫn có limited logging (S8). Chưa xác minh tier/account nhóm.

## 5. Credential/config strategy

- Backend composition/config đọc process env `GEMINI_API_KEY`; không tự tìm `.env`
  trong cwd, repo input hoặc thư mục cha. Local developer inject key qua môi trường
  backend bằng cơ chế quản lý secret của mình; không đưa giá trị vào command/handoff.
  File `.env` tồn tại không chứng minh biến đã được nạp.
- Không dùng `GOOGLE_API_KEY` làm alias. Nếu chỉ có alias thì báo configuration
  error yêu cầu canonical name; nếu cả hai có và khác nhau thì fail closed. Nếu cùng
  giá trị, canonical thắng; không log giá trị. Cấu hình loader thuộc 3.16.
- Truyền key explicit cho SDK và explicit Developer API (`enterprise=False` tại
  SDK đã kiểm); không để env của Google đổi backend/API/model/base URL ngầm.
  Chỉ dùng endpoint Google allowlisted, TLS verification bật; không gửi auth qua
  arbitrary redirect/custom endpoint hoặc key trong URL query.
- Missing/blank key là configuration failure, không gọi mạng. Auth/permission
  failure qua mã typed 3.15; không log raw SDK exception/request headers hoặc
  đưa validation input values vào report. Key presence không chứng minh validity.
- Đã có lịch sử key gửi qua chat; trước vận hành lâu dài Huy nên thay key và cung
  cấp qua backend secret config. Phiên này không đọc, kiểm, rotate hoặc revoke key.

## 6. Limits, retry và accounting đã chốt

Đây là yêu cầu triển khai cho 3.04/3.16, **chưa là runtime config hoặc quyền chi tiền**.

| Control | Giới hạn | Cách áp dụng / owner |
| --- | --- | --- |
| Context representation đã có | 16 chunks, 4.096 UTF-8 bytes/chunk, 32.768 bytes tổng text | 3.15 đã enforce; không phải total wire/token cap |
| Total wire bổ sung | 65.536 UTF-8 bytes serialized JSON body generation; count body cũng không vượt mức này | 3.04/16 kiểm sau packing, gồm schema/instructions/inventory; tăng từ đề xuất wire 32 KiB cũ để không xung đột context cap. Không silent truncate |
| Input | <=8.192 tokens toàn request gồm instructions/schema | Full-request count đã qua parity check; count failure/coverage chưa rõ thì không generation |
| Output/thinking | `max_output_tokens=2048`, minimal thinking, một response candidate mặc định; không gửi candidate_count | Không coi minimal/no thought summary là zero thinking. Trước live phải xác minh cap có bound tổng billable candidates + thoughts cho generate_content/model đã chọn |
| Deadline | 45s monotonic overall; mỗi generation <=15.000ms và remaining; count <=5.000ms và remaining | Bao gồm packing/count/backoff/attempt/validation; timeout SDK không thay outer deadline. 3.16 kiểm cancellation không tiếp tục dispatch |
| Calls | <=1 count; <=2 generation attempts; concurrency=1; <=5 runs/session | Attempt count của ProviderResult là generation dispatch thực, không bao gồm count |
| Retry owner | Một coordinator trong provider/config boundary, không sửa request_proposal để gọi lặp | SDK explicit HttpRetryOptions(attempts=1); 3.04 transport classify, 3.16 owns retry/ledger/deadline |
| Retry policy | Tối đa một retry cho transient rate-limit/503/transport khi còn deadline và reserve | Backoff 1–2s, Retry-After lớn hơn chỉ được chờ nếu còn đủ budget/deadline; không rút ngắn yêu cầu server. Auth/config/quota exhausted/refusal/invalid/truncated không retry |
| App budget | <=USD 0,02/run; <=USD 0,10/session; tối đa 5 runs | 3.16 reserve trước **count** và mỗi generation, atomic ledger, không reset session khi process restart hoặc retry |
| Unknown outcome | Usage/cost thiếu giữ null; reservation không tự hoàn khi timeout/disconnect | Một request chưa xác định completion vẫn có thể bị tính tiền. Chỉ reconcile bằng observation/billing đủ căn cứ |

Giá standard text-only S2 tại 2026-11-10: USD **0,30/1M input** và
**2,50/1M output gồm thinking**. Không dùng giá batch/cache/tool hoặc mặc định free.
Nếu cap tổng generated billable tokens 2.048 đã được xác minh cho API đã chọn:

```text
generation reserve = (8192*0.30 + 2048*2.50)/1_000_000 = USD 0.0075776
2 generations      = USD 0.0151552
remaining run cap  = USD 0.0048448 for verified count/other bounded charges
```

Đây là **conditional estimate**, chưa là bound đã chứng minh của generate_content.
S5 nói cap gồm thoughts cho **Interactions**; không tự chuyển semantics sang API
đang chọn. 3.16 phải có nguồn áp dụng trực tiếp cho generate_content/model hoặc
documented conservative upper bound khác nằm trong USD 0,02. Chưa chứng minh được
thì generation bị chặn; không chi trước để “đo rồi mới giới hạn”, không tự tăng budget.
Count endpoint billing cũng phải được xác nhận trước count live; billing FAQ nói
GetTokens không thu phí chưa đủ để mặc định countTokens là cùng operation.

Ledger dùng Decimal hoặc integer subunits để không under-reserve do float. Lưu
session/run/attempt IDs, model/API/config/prompt và price snapshot/date, reserved
amount, actual observed usage, completion/unknown state. Không đưa prompt/key vào
ledger. Chỉ release phần unused đã biết; timeout không chứng minh remote billing dừng.
Application cap không phải cloud hard billing cap và không kiểm soát người khác
cùng dùng key/project. Không tự bật billing, auto-reload hay tăng quota.

Usage mapping theo generate-content REST S9: input=`promptTokenCount`,
output=`candidatesTokenCount`, thinking=`thoughtsTokenCount`, total=`totalTokenCount`.
Giữ từng observed field; không suy null thành 0 hoặc cộng thinking hai lần. Với
text-only/no cache/tools và semantics đã xác minh, estimate từ input và
candidates+thoughts; không gọi đó là invoice actual. Nếu nhiều attempts có unknown
usage thì không ghi aggregate như thể đầy đủ. Actual model version chỉ lấy từ response.

## 7. Gate bàn giao

**Bắt đầu 3.04 được ngay:** baseline/G0/3.15 có nguồn; provider/model/SDK/schema,
credential/data boundaries và error/limit policies đã chốt; isolated compatibility
có bằng chứng. Triển khai adapter nhỏ qua port hiện có, SDK chỉ ở adapters,
mock toàn network; pin dependencies bằng tooling trong scope 3.04 được giao.

Offline matrix tối thiểu: valid/malformed/extra fields/unknown IDs/evidence;
refusal/empty/truncated; auth/permission/config/quota/rate-limit/timeout/transport;
SDK attempts=1; request mutation/serialization/count parity; redacted telemetry;
client cleanup. Không triển khai selector/runner hoặc tái tạo DTO canonical.

**Trước live 3.16 — các external inputs/verification còn mở:**

1. Có scope cho phép live với synthetic fixture, account/key/model access và
   project quota/tier/billing được kiểm đúng môi trường; không suy từ CI/key tồn tại.
2. Loader, pre-count reserve, session ledger, token/wire/deadline/retry guards có
   offline evidence; missing/unknown cost bound phải chặn mạng/generation tương ứng.
3. Xác minh count billing và v1 full-request count coverage bằng nguồn/kiểm chứng
   phù hợp; không count context-only hoặc dùng private SDK transport.
4. Xác minh cap **billable output + thinking** cho generate_content trước generation
   hoặc bound bảo thủ khác trong budget; không lấy Interactions example làm proof.
5. Endpoint acceptance của schema/thinking/config, real usage/model-version mapping
   sẽ được xác minh bằng authorized bounded smoke. Nếu server từ chối thì giữ G1 mở.

**G1** chỉ đạt sau smoke thật có command/config/fixture/quyền/budget/timestamp,
redacted result và usage/latency khi có. **G2** thuộc 3.17: permitted frozen source
context/inventory → proposal/application/CLI → main+CI; selection/execution giữ
not_run khi chưa có implementation. Không dùng waiver browser Sprint 2 cho Sprint 3.

## 8. Nguồn và evidence

Nguồn công khai được GET lại **2026-11-10**, không credential/source egress.
URL mutable là snapshot đọc, không phải account validation.

| ID | Nguồn | Dùng để kết luận |
| --- | --- | --- |
| S1 | [Model](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite) | Exact stable ID, structured/thinking support và limits |
| S2 | [Pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) | Standard text price, thinking billed as output |
| S3 | [PyPI](https://pypi.org/pypi/google-genai/3.0.0/json), [SDK tag README](https://github.com/googleapis/python-genai/blob/v3.0.0/README.md) | Version/Python/dependencies; generate_content/v1/schema |
| S4 | [Structured output](https://aistudio.google.com/docs/structured-output) | Schema subset, constraints phải revalidate local |
| S5 | [Thinking](https://aistudio.google.com/docs/thinking) | Minimal support; Interactions cap semantics không tự áp cho generate_content |
| S6 | [Model migration](https://aistudio.google.com/docs/whats-new-gemini-3.6#migrate-to-gemini-3-5-flash-lite) | Không candidate_count/thinking_budget cho foundation |
| S7 | [CountTokens reference](https://aistudio.google.com/api-reference/tokens/count-tokens), [tokens guide](https://aistudio.google.com/docs/tokens) | Full generateContentRequest, count là egress |
| S8 | [Terms](https://aistudio.google.com/docs/terms) | Paid/unpaid data use, limited retention |
| S9 | [Generate content REST](https://aistudio.google.com/api-reference/generate-content) | Generation config, finish reasons, usage fields |
| S10 | [SDK types](https://github.com/googleapis/python-genai/blob/v3.0.0/google/genai/types.py), [transport](https://github.com/googleapis/python-genai/blob/v3.0.0/google/genai/_api_client.py), [models](https://github.com/googleapis/python-genai/blob/v3.0.0/google/genai/models.py) | Timeout milliseconds; explicit attempts; count field rejection |
| S11 | [Keys](https://aistudio.google.com/docs/api-key), [rate limits](https://aistudio.google.com/docs/rate-limits) | Env precedence, project quota không phải mỗi key |
| S12 | [Billing](https://aistudio.google.com/docs/billing), [troubleshooting](https://aistudio.google.com/docs/troubleshooting) | GetTokens wording, account tier và classified failures |

Local supporting files (ignored, không deliverable/commit):
`var/s3-readiness-check/{sources.json,supplementary-sources.json,*.raw,*.txt,
baseline-requirements.txt,combined-requirements.txt,probe_sdk.py,compatibility.json}`.
Combined requirements SHA256:
`486e4d5440d00969dabd6d62c3c3295b16306348a8e978edca0eb726a1c779ef`.
SDK README SHA256:
`41eff7973d1d8adb213898633ab0be4de9ee013773889d50a92069f943c93621`.
Evidence bị ignore chỉ phục vụ phiên local; reviewer có thể tái tạo theo lệnh dưới,
không phải artifact sẽ tự có trên GitHub.

Các lệnh thực hiện từ worktree; `uv` là
`D:/smart-regression-ai/.tools/bin/uv.exe`, cache nằm trong thư mục tạm:

```powershell
git fetch origin main
git rev-parse origin/main
gh pr view 65 --repo kokoreina/smartregression-ai --json state,mergeCommit,reviews
gh run view 42772254046 --repo kokoreina/smartregression-ai --json conclusion,headSha,status
uv --cache-dir var/s3-readiness-check/uv-cache export --frozen --no-emit-project --no-hashes --output-file var/s3-readiness-check/baseline-requirements.txt
uv --cache-dir var/s3-readiness-check/uv-cache venv --python D:/smart-regression-ai/var/task-2.20-b-venv/Scripts/python.exe var/s3-readiness-check/sdk-venv
uv --cache-dir var/s3-readiness-check/uv-cache pip compile var/s3-readiness-check/sdk-input.txt --python var/s3-readiness-check/sdk-venv/Scripts/python.exe --output-file var/s3-readiness-check/combined-requirements.txt --no-header --quiet
uv --cache-dir var/s3-readiness-check/uv-cache pip install --python var/s3-readiness-check/sdk-venv/Scripts/python.exe --requirement var/s3-readiness-check/combined-requirements.txt
uv --cache-dir var/s3-readiness-check/uv-cache pip check --python var/s3-readiness-check/sdk-venv/Scripts/python.exe
$env:PYTHONPATH=(Join-Path (Get-Location) 'backend/src')
$env:PYTHONDONTWRITEBYTECODE='1'
var/s3-readiness-check/sdk-venv/Scripts/python.exe var/s3-readiness-check/probe_sdk.py
git diff --check
```

`sdk-input.txt` gồm `-r baseline-requirements.txt` và `google-genai==3.0.0`.
Ban đầu export/cache và network resolve trong sandbox thất bại; sau chuyển cache
vào workspace và dùng public network được cấp quyền thì export/resolve/install đạt.
Probe ban đầu giả định camelCase thinking và count config support sai; đã kiểm
wire thực tế, sửa probe và chạy lại đủ 11 assertions. Đây là disposable SDK probes,
không phải tests sản phẩm hoặc implementation 3.04. Không chạy application/Docker/
PostgreSQL/full suite, không gọi Gemini count/generation thật hoặc chi API.

Kiểm tài liệu thực tế: `verify_docs.py` đạt local link destinations, fences,
trailing whitespace và key-pattern check cho hai file; `git diff --check` không
báo lỗi. Đây không phải secret scanner chuyên dụng hoặc external-link/anchor crawl.
Repo không có Markdown lint command chuyên biệt được tìm thấy trong scope kiểm.
`pyproject.toml`/`uv.lock` khớp HEAD; diff sản phẩm/contracts/Office bằng rỗng.

## 9. Lịch sử và trách nhiệm

- 2026-11-09: readiness cũ phát hiện G0 thiếu; model/SDK/limits là recommendations.
- 2026-11-10: PR #64 và #65 đã merge; trạng thái BLOCKED/REVIEW_REQUIRED trước đó
  chỉ là lịch sử, xem G0/task-3.15 handoffs tại revision tương ứng.
- 2026-11-10: phiên 3.14 này chốt readiness và kiểm compatibility cô lập; không tạo
  phê duyệt độc lập hoặc sửa status/effort Office. Phiên soạn ban đầu chỉ làm local.
- Sau bàn giao, Huy giao commit/push/mở PR riêng cho hai tài liệu readiness/D21.
  Scope xuất bản không bao gồm temporary probes, Office hoặc root planning files;
  review/merge không được suy từ kết quả compatibility.

Đã đọc profiles Coordinator/RAG-LLM, rules 00/01/04/06/08/12/13, security-review và
Proposal Appendices C/D hiện tại. Codex hỗ trợ đối chiếu nguồn, SDK probes, soạn
tài liệu và self-review. Huy/nhóm cần đọc, hiểu và review bản bàn giao; không bịa
contribution ratio, người duyệt, chữ ký hoặc mentor approval.

[main]: https://github.com/kokoreina/smartregression-ai/tree/f729e6ecb3fdb74093632ca5e3946aac3f087a8b
[pr64]: https://github.com/kokoreina/smartregression-ai/pull/64
[pr65]: https://github.com/kokoreina/smartregression-ai/pull/65
[ci65]: https://github.com/kokoreina/smartregression-ai/actions/runs/42772254046
