# Task 2.19 — Kiểm thử tích hợp identity và evidence

Đây là phần 4 giờ của Đỗ Hà An trong [brief 2.19](sprint-2-team-guide.md#task-219).
Khánh phụ trách inventory và runner. Baseline `0745266` đã có task 2.17 và các
module retrieval 2.10–2.12.

Bộ test tạo một Git repo cục bộ với hai commit cố định, chạy workflow thật rồi
kiểm tra report qua CLI validation, publication và đọc lại artifact. Test
retrieval dùng snapshot Git, index manifest, impact producer và context validator
thật. Evidence quan sát được gắn nhãn DEMO tại biên report. Phần SQL dùng một
đối tượng ghi nhận metadata được chuyển tới cổng lưu trữ.

| Ca | Kỳ vọng đặt trước | Kết quả quan sát |
| --- | --- | --- |
| 4 ca acquisition | Sai authorized root, ref di động, SHA vắng mặt hoặc blob SHA phải trả exit 2 | Đúng mã lỗi, không sinh JSON và Git working tree giữ trạng thái ban đầu |
| 8 ca evidence không hợp lệ | Chặn sai repo/commit/snapshot, span đảo, reference không tồn tại và trạng thái xác minh thiếu căn cứ | CLI validator exit 1, publication từ chối trước khi tạo artifact hoặc gọi cổng lưu |
| 1 ca đối chứng | Graph và impact tạo path `consumer.py → calc.py` từ Git fixture, evidence quan sát giữ partial | Report đọc lại giữ path, danh tính và trạng thái `unverified` |
| 2 ca evidence chưa thể xác minh | Evidence trỏ file thiếu hoặc span vượt nội dung tiếp tục là `unverified` | Report hợp schema, evidence vẫn partial sau publication và đọc lại |
| 2 ca stale index | Index commit cũ hoặc cấu hình cũ bị chặn trước khi tạo context | Cả hai trả `stale_index`. Index đúng đi qua ranking và giữ snapshot/cấu hình trong artifact |
| 6 ca đọc artifact sai danh tính | Sai repo, run, base, target, snapshot hoặc report ID bị từ chối | Reader báo lỗi, bytes giữ nguyên và lượt đọc đúng danh tính thành công |
| 1 ca partial analysis | Parse failure được giữ qua workflow, publication và đọc lại | Graph failed, có path và mã lỗi. Analysis exit 2, validator exit 0 cho report hợp schema |

Chạy lại tại root repo bằng môi trường đã đồng bộ từ lockfile.

```powershell
uv run pytest backend/tests/integration/test_identity_evidence_flow.py -vv
```

Lần chạy tập trung có **24 ca pass**. Log và fixture artifacts của lần chạy local
nằm trong `var/task-2.19/focused.log` và `var/task-2.19/evidence-temp/`.
Toàn bộ backend có **682 pass, 75 skip và 1 warning**. Các skip theo điều kiện
PostgreSQL opt-in và POSIX FIFO trên Windows. Ruff lint, format và kiểm tra
schema exporter đều qua.
Trong một tiến trình thử nghiệm riêng, bỏ điều kiện so sánh identity/report ID
trong reader làm cả 6 ca đọc sai danh tính fail với `DID NOT RAISE RunStorageError`.
Chạy lại bằng reader bình thường đưa cả 6 ca về pass.

Phần xác minh nội dung nguồn của evidence, tích hợp retrieval vào lệnh `analyze`
và kiểm chứng PostgreSQL/runner thật cần evidence riêng khi các luồng đó sẵn sàng.
Ca unknown test ID và failed discovery thuộc phần inventory/runner của Khánh.

OpenAI Codex hỗ trợ xây fixture, viết test và tài liệu. Kết quả kiểm thử local và
rà soát bằng agent được bàn giao cho reviewer của nhóm.
