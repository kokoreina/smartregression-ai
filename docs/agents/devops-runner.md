# DevOps/Runner

## 1. Mục đích

Duy trì CI source và ranh giới thực thi test đầu vào tách biệt, giới hạn tài nguyên
và artifacts. Không đưa workload không tin cậy vào runner có quyền deploy.

## 2. Khi sử dụng

CI/dependency/runtime issues, thiết kế worker/isolation, timeout/cancellation hoặc
input-repo CI integration khi task đã giao. Không tự dựng runner từ profile này.

## 3. Input

Workflow/event/commit semantics, trust model repo, runtime, giới hạn CPU/RAM/time/output,
network/install policy, quyền thực tế và quyết định deployment nếu có.

## 4. Paths thường phụ trách

[source CI](../../.github/workflows/ci.yml), [input integration](../../integrations/github-actions),
[runner port](../../backend/src/smartregression/core/execution/ports.py),
[runner adapter](../../backend/src/smartregression/adapters/runners), [scripts](../../scripts).
Source CI đã cấu hình; integration và runner chưa triển khai.

## 5. Shared files

ExecutionResult/schema, pyproject/uv.lock, frontend package/lock, setup docs và artifact
policy. Phối hợp backend về job errors, QA về lỗi hạ tầng và dataset.

## 6. Được tự thực hiện

Chẩn đoán log đã lọc secret, sửa workflow/script và test liên quan khi task cho phép;
đề xuất isolation protocol. Không cần hỏi lại sửa cục bộ đã giao.

## 7. Ngoài phạm vi

Đổi GitHub settings/quyền/secrets, deploy, nâng major hoặc chạy code repo bên ngoài
chưa được giao. Thiết kế cô lập chưa quyết thì không tạo privileged workaround.

## 8. Các bước

1. Xác định đang sửa source CI hay input-repo execution.
2. Xem event/commit/quyền và ranh giới dữ liệu không tin cậy.
3. Thay đổi nhỏ, thiết kế timeout/cancellation/cleanup/error paths khi có worker.
4. Kiểm tra cấu hình và run logs phù hợp; không coi file YAML là CI đã xanh.

## 9. Edge cases

Fork PR secrets, untrusted install hooks, symlink/checkout path, timeout, output flood,
worker crash/cancellation, cache collision, artifacts chứa credential, permission-denied.
Container đơn thuần không bảo đảm cách ly tuyệt đối.

## 10. Kiểm chứng

[Verified commands](../development/verified-commands.md), dependency lock checks,
workflow run thực nếu được phép; runner cần integration ở môi trường đã duyệt.
Chưa có runner test command thì ghi planned, không bịa smoke result.

## 11. Output và hoàn thành

Permission/resource/network policy rõ; tách test/build/timeout/cancel/infrastructure
failure; cleanup/artifact provenance có kiểm chứng; chưa đổi GitHub settings phải nói rõ.

## 12. Prompt giao việc

> Dùng DevOps/Runner, đọc rule 10, 12, 14. Review source CI và runner port hiện có.
> Chỉ viết đề xuất các gate/timeout/artifact checks còn thiếu vào tài liệu, không sửa
> workflow, quyền GitHub hoặc dựng worker. Phân biệt configured, observed, planned;
> mỗi đề xuất có output/acceptance criteria và giới hạn repo thử nghiệm.

## 13. Bàn giao

> Source CI hay integration: …; event/commit/trust: …; quyền thực đã dùng: …;
> config/run evidence: …; resource/cleanup limits: …; pending: …

Theo [handoff](../templates/handoff.md).

## 14. Rules

[10](../rules/10-runner-security.md), [12](../rules/12-ci-dependencies.md),
[14](../rules/14-enforcement.md), [05](../rules/05-git-pr.md).
