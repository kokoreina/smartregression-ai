# Impact — chưa triển khai

Đã có [Python AST spike](python_snapshot.py) cho symbol spans, trực tiếp thay đổi
và module-import edges trên fixture. Chưa có impact analysis đầy đủ; edge không
chứng minh behavior hoặc độ an toàn khi bỏ test.

Tạo nhận định ảnh hưởng từ change model và evidence, có trace về đúng commit.
Không suy diễn findings giả thành kết quả thật. Interface cụ thể sẽ chốt sau spike parser.
