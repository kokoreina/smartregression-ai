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
