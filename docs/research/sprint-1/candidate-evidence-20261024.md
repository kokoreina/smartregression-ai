# 1.02/1.03 — Kiểm chứng bổ sung candidate ngày 2026-10-24

Codex hỗ trợ Nguyễn Tấn Huy đối chiếu draft của Đặng Đại Việt, giữ ownership và
AI disclosure gốc. Đây là cập nhật evidence, chưa chọn dataset chính thức hoặc
phê duyệt của người khác. Đọc qua GitHub connector, không clone/chạy candidate code.

## Snapshot có thể truy lại

| Repo | Commit được API xác nhận | License đọc trực tiếp | Evidence pytest đã đọc |
| --- | --- | --- | --- |
| TinyDB | `edff96aeb2616402e9489d46e90a592c05565621` | [MIT](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/LICENSE) | [pytest.ini](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/pytest.ini), [test_tinydb.py dòng 1–45](https://github.com/msiemens/tinydb/blob/edff96aeb2616402e9489d46e90a592c05565621/tests/test_tinydb.py) |
| sqlparse | `60cdc649726bf1bc4f1b336050560b336da715ec` | [BSD-3-Clause](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/LICENSE) | [pyproject.toml dòng 1–45](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/pyproject.toml), [test_parse.py dòng 1–45](https://github.com/andialbrecht/sqlparse/blob/60cdc649726bf1bc4f1b336050560b336da715ec/tests/test_parse.py) |

Giữ copyright/license notices khi phân phối bản sao. Chưa audit mọi subdirectory,
license dữ liệu phụ, mọi file test, commit window, fault label hoặc build history.
Không suy ra quyền với repo private hay dữ liệu ngoài license đã đọc.

TinyDB pytest.ini có cờ `--cov`; cần dependency pytest-cov và review plugin policy
trước collection. Image G1 chỉ có pytest nên chưa chứng minh reproducibility của
TinyDB. sqlparse khai báo Python >=3.10 tại snapshot đã đọc; không suy ra mọi commit
lịch sử dùng cùng phiên bản. Test source đã đọc chứng minh có test thực, không
chứng minh collection hoặc test pass.

Đề xuất khảo sát tiếp: sqlparse là candidate chính, TinyDB là dự phòng cho spike
nhỏ; chưa là quyết định lấy mẫu cuối. Marshmallow/humanize giữ trạng thái draft từ
1.03, chưa được kiểm chứng lại trong lượt này. Không dùng stars hay commit count
cũ như số đo mới. Cả hai candidate cần approved environment/dependencies, discovery
lặp lại và build/suite-size evidence trước nhận vào cohort.

## Những điểm cần sửa cách diễn giải của draft cũ

- D05 nay accepted Python/pytest theo [ADR 0002](../../architecture/decisions/0002-python-pytest-input.md),
  không còn chờ lựa chọn cặp công nghệ. Phiên bản/plugins input vẫn pending.
- Đối chiếu chữ trong Proposal v1.4 §11.4: ít nhất 2 repo, 30 distinct commit pairs,
  15 independently verified fault-bearing cases; không ghi target 50 của Proposal.
  Project Plan v1.1 lại dùng 50 pairs. Giữ khác biệt cho nhóm/mentor quyết trước run.
- `pytest --collect-only` đếm/discover IDs, không đo thời gian full suite hoặc kiểm
  chứng mọi test pass; chạy hai lần mới có evidence bước đầu về ID ổn định.
- Không thể suy ra contamination thấp từ stars hoặc việc repo không thuộc benchmark.
  Chưa chọn model/cutoff, nên không thể khẳng định đã lấy commit sau training cutoff.

Nguồn Office: đọc XML text/paragraph/table liên quan của Proposal và Project Plan;
không kiểm sơ đồ/objects hoặc xác minh mọi nội dung Office. Không thay lịch sử
handoff/AI disclosure của Việt; note này là kết quả kiểm chứng bổ sung của phiên mới.
