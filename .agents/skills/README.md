# Skills cho SmartRegression AI

Đây là mười quy trình tùy chọn theo dạng Agent Skills (`SKILL.md`), được viết cho
repo này và chỉ nạp khi mô tả trigger phù hợp. Chúng không phải agents, không cấp
quyền và không thay thế [AGENTS.md](../../AGENTS.md), profile, rules, ADR hoặc task.
Đọc một skill chính; chỉ mở skill bổ sung khi task đi qua boundary tương ứng.

## Danh mục

| Skill | Dùng khi |
| --- | --- |
| [ux-research](ux-research/SKILL.md) | Lập kế hoạch usability test hoặc chuyển NFR thành nhiệm vụ đo được |
| [ui-design](ui-design/SKILL.md) | Thiết kế/sửa dashboard và report UI |
| [accessibility-review](accessibility-review/SKILL.md) | Review keyboard, semantics, responsive và accessibility |
| [webapp-testing](webapp-testing/SKILL.md) | Kiểm tra UI trong browser khi browser tool có sẵn |
| [api-contracts](api-contracts/SKILL.md) | Thay API/schema hoặc producer-consumer contract |
| [test-driven-development](test-driven-development/SKILL.md) | Sửa behavior có thể tái hiện bằng test |
| [systematic-debugging](systematic-debugging/SKILL.md) | Có lỗi chưa rõ nguyên nhân hoặc môi trường/test failure |
| [security-review](security-review/SKILL.md) | Review luồng dữ liệu, input không tin cậy, secrets, runner |
| [github-actions-hardening](github-actions-hardening/SKILL.md) | Thêm/sửa/review workflow GitHub Actions |
| [evaluation-integrity](evaluation-integrity/SKILL.md) | Thiết kế dataset, baseline, metrics hoặc báo cáo thực nghiệm |

## Nguồn và kiểm soát nguồn

Các skill trên được viết lại theo nhu cầu repo; không chép nguyên `SKILL.md`, script
hay assets từ các nguồn. Tham khảo quy trình/mẫu tại:

- [github/awesome-copilot](https://github.com/github/awesome-copilot): MIT ở
  [LICENSE](https://github.com/github/awesome-copilot/blob/main/LICENSE). Đường dẫn
  tham khảo: `skills/web-design-reviewer`, `agents/accessibility`,
  `skills/webapp-testing`, `skills/security-review`,
  `skills/github-actions-hardening`, `skills/docs-sync-audit`.
- [obra/superpowers](https://github.com/obra/superpowers): MIT, được công bố tại
  [repo](https://github.com/obra/superpowers). Đường dẫn tham khảo:
  `skills/test-driven-development`, `skills/systematic-debugging`.
- [OpenAI Codex skill guidance](https://developers.openai.com/cookbook/topic/agents):
  xác nhận quy ước repo-local `.agents/skills/` và progressive disclosure. Đây là
  tài liệu hướng dẫn, không phải skill upstream được cài.

Các URL đang trỏ nhánh `main`, không phải snapshot bất biến. Truy cập GitHub trực
tiếp trong phiên này bị chặn bởi proxy; vì vậy chưa xác minh SHA commit hiện hành,
ngày sửa gần nhất hoặc đầy đủ license cho từng file. Chỉ dùng các quy trình chung
để tạo hướng dẫn nội bộ; trước khi chép nguyên văn hay cập nhật theo upstream, phải
xác minh commit, license và toàn bộ assets của đúng skill. Không có script/assets
bên ngoài được nhập hoặc thực thi.

## Quy tắc áp dụng

- Skill là hướng dẫn task, không phải policy; khi xung đột, AGENTS/rules và yêu cầu
  người dùng có hiệu lực cao hơn.
- UI/UX phải giữ nhãn DEMO, semantics null/unknown và contract hiện có; không thiết
  kế trạng thái backend chưa hỗ trợ như thể đã có.
- TDD/debugging không bắt buộc thêm test hình thức; làm theo rule 06 và lệnh đã xác minh.
- Security/evaluation phải giữ ranh giới runner, provenance, label isolation và mẫu số.
- Review skill chỉ đưa ra evidence; không tự approve, merge hoặc đổi quyền.
- Không dùng browser workflow nếu công cụ/browser không sẵn có; nêu rõ phần chưa xác minh.
