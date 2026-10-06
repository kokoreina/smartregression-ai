# Tích hợp GitHub Actions của repository đầu vào — pending

Thư mục này dành cho adapter/workflow gọi SmartRegression trong repo được phân tích
sau khi spike chốt ngôn ngữ/framework, checkout policy và isolated runner.
Chưa cung cấp action thực thi, chưa clone hoặc chạy repo bên ngoài.
Thiết kế sau này cần resolve commit pair, truyền test inventory, xuất report artifact,
validate selection và chuyển execution sang worker cô lập với quyền tối thiểu.

CI kiểm tra source của SmartRegression nằm ở .github/workflows/ci.yml, không ở đây.
