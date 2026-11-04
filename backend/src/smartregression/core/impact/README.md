# Impact

`python_snapshot.py` cung cấp AST observations cho symbol spans và thay đổi trực
tiếp. [dependency_graph.py](dependency_graph.py) bổ sung graph import tĩnh theo
một repository/revision đã được caller đóng băng:

- Edge có chiều `importer -> imported module`.
- Absolute và relative imports resolve được trong cùng snapshot tạo supported edge.
  Relative resolution dùng package context của file; `__init__.py` được xem là
  module package. `from .sub import models` chỉ tạo edge tới package `sub` khi
  package đó có trong snapshot, không suy đoán `models` là attribute hay module
  con.
- Relative import hợp lệ nhưng thiếu target dùng `target_not_in_snapshot`;
  vượt package root dùng `relative_import_beyond_root`; thiếu thông tin resolve
  dùng `relative_import_unresolved`.
- Star imports, dynamic imports và missing modules tạo `unresolved` record, không
  bị coi là không có dependency. Dynamic import alias trực tiếp từ `importlib`
  được nhận diện khi tên hàm có thể xác định tĩnh.
- Mọi node và edge endpoint mang cùng repository/revision; module này không đọc,
  checkout hoặc thực thi source.

Đây là graph import tĩnh giới hạn, không phải full call graph và không chứng minh
behavior thay đổi hay an toàn để bỏ test. Snapshot authorization,
changed-component contract và persistence vẫn chờ các task 2.15, 2.01, 2.14.

Tạo nhận định ảnh hưởng từ change model và evidence, có trace về đúng commit.
Không suy diễn findings giả thành kết quả thật.

## Reverse-reachable potential impact

`build_potential_impact` nhận `RunIdentity`, `ChangePayload` và một `GraphPayload`
thuộc snapshot base hoặc target của identity. Component thay đổi là candidate
`changed`; importer cách một cạnh là `direct`, còn importer chỉ reachable qua
component trung gian là `indirect`. Graph không được nối các component cùng tên
giữa hai revision; path được resolve theo snapshot đã chọn (deleted component có
thể dùng `previous_path` trong base, còn added component chỉ có trong target).

`ImpactPath.nodes` giữ chiều cạnh gốc, từ candidate tới changed component, ví dụ
`[a.py, b.py, c.py]`. Các path đơn giản hợp lệ được deduplicate và sort ổn định;
cycle và self-loop không được lặp node hoặc làm traversal vô hạn. Candidate chỉ
thể hiện static import reachability có khả năng ảnh hưởng, không chứng minh
runtime behavior đã thay đổi.

Phân tích này không bao phủ dynamic imports, reflection, call graph, runtime
dispatch hoặc các quan hệ không biểu diễn được bởi static import graph. Vì vậy
không tìm thấy path không chứng minh không có ảnh hưởng, và có path cũng không
chứng minh behavior chắc chắn thay đổi.
