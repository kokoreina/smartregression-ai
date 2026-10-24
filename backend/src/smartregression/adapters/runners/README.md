# Runner adapter — chưa triển khai

Đã có [pytest fixture spike](pytest_spike.py), gọi từ
[G1 harness](../../../../../scripts/g1/README.md), chỉ chạy fixture do task tạo trong
Docker có limits. Chưa implement port production hoặc nối vào API/dashboard.

Sẽ implement core/execution/ports.py qua worker cô lập. Cần thiết kế timeout,
resource/network limits, input validation và result transport trước khi chạy code.
Không dùng subprocess trong API để chạy repository được phân tích.
