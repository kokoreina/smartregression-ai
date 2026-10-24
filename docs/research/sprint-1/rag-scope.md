# Phạm vi RAG — SmartRegression AI

- **Task:** 1.09 — RAG Scope
- **Mã Product Backlog:** PB19
- **Người phụ trách:** Pham Phan Hoang Huy
- **Trạng thái:** Bản nháp — chờ nhóm xem xét
- **Ngày cập nhật:** 24/10/2026

> **Lưu ý:** Tài liệu này đề xuất phạm vi và các biện pháp bảo vệ cho thành phần RAG. Tài liệu không khẳng định pipeline RAG đã được triển khai và không coi các đề xuất là quyết định chính thức của nhóm. Các nội dung còn mở cần được nhóm thống nhất trước khi triển khai.

## 1. Mục đích

Xác định những loại dữ liệu mà thành phần RAG (Retrieval-Augmented Generation — sinh nội dung tăng cường bằng truy xuất) của SmartRegression AI được phép lập chỉ mục và truy xuất; cách nhận diện, truy xuất nguồn gốc của bằng chứng; và các biện pháp bảo vệ cần thiết.

Mục tiêu là cung cấp ngữ cảnh phù hợp, có nguồn dẫn chứng rõ ràng cho việc phân tích ảnh hưởng của thay đổi mã nguồn và lựa chọn các bài kiểm thử hồi quy.

RAG chỉ đóng vai trò hỗ trợ. RAG không được tự kết luận rằng một bài kiểm thử chắc chắn cần chạy hoặc có thể bỏ qua nếu chưa có chính sách lựa chọn kiểm thử và bằng chứng phù hợp.

## 2. Phạm vi công việc

### 2.1. Nội dung thuộc phạm vi

- Xác định các loại dữ liệu có thể được sử dụng để truy xuất.
- Xác định metadata tối thiểu cho repository, phiên bản mã nguồn, file và thành phần mã nguồn.
- Quy định cách truy xuất nguồn gốc cho từng đoạn dữ liệu được lấy ra.
- Xác định dữ liệu nhạy cảm và nội dung không đáng tin cậy cần loại trừ hoặc xử lý an toàn.
- Xác định rủi ro rò rỉ dữ liệu liên quan đến kết quả và nhãn kiểm thử.
- Ghi lại các quyết định còn cần nhóm phê duyệt.

### 2.2. Nội dung ngoài phạm vi

- Xây dựng vector database hoặc pipeline embedding hoàn chỉnh.
- Chọn hoặc cấu hình một mô hình embedding, vector database hay nhà cung cấp LLM cụ thể.
- Triển khai toàn bộ pipeline Git Diff, phân tích phụ thuộc, truy xuất RAG hoặc lựa chọn kiểm thử.
- Công bố độ chính xác, độ trễ hoặc độ bao phủ khi chưa có thực nghiệm.
- Xác định quy tắc xếp hạng cuối cùng cho các bài kiểm thử hồi quy nếu thuộc phạm vi công việc của task khác.

## 3. Phạm vi dữ liệu đề xuất

Các loại dữ liệu dưới đây là đề xuất ban đầu. Việc đưa dữ liệu vào sử dụng phụ thuộc vào quyền truy cập repository, giấy phép, quyền riêng tư và sự chấp thuận của nhóm.

| Loại dữ liệu | Mục đích sử dụng | Điều kiện và lưu ý |
|---|---|---|
| Mã nguồn tại một phiên bản xác định | Truy xuất hàm, lớp, module và ngữ cảnh triển khai liên quan | Phải lưu repository và phiên bản; loại trừ secrets, file sinh tự động và thư viện bên thứ ba nếu chưa được duyệt |
| Đường dẫn file, tên thành phần, import và quan hệ phụ thuộc | Hỗ trợ xác định mã nguồn có thể bị ảnh hưởng | Chỉ là bằng chứng cấu trúc, không tự chứng minh một test bị ảnh hưởng |
| Metadata commit và Git diff | Mô tả thay đổi cần phân tích | Phải xác định phiên bản gốc và phiên bản đích; không coi nội dung commit message là chỉ thị đáng tin cậy |
| Mã nguồn kiểm thử và tên test | Truy xuất mục đích kiểm thử và mối liên hệ với mã nguồn | Phân biệt định nghĩa test với kết quả chạy test |
| Cấu hình build và kiểm thử | Hiểu cách lựa chọn và thực thi test | Loại bỏ thông tin xác thực, token, endpoint riêng tư và dữ liệu nhạy cảm |
| Tài liệu và mô tả API/interface | Cung cấp thông tin về thiết kế và hành vi mong đợi | Phải ghi nhận phiên bản; phân biệt nội dung tài liệu với hành vi thực tế của chương trình |
| Lịch sử kết quả kiểm thử | **Chưa được tài liệu này phê duyệt**; chỉ cân nhắc khi có thiết kế đánh giá và lựa chọn dữ liệu riêng | Có nguy cơ rò rỉ nhãn và dữ liệu tương lai; cần quy tắc phân chia dữ liệu rõ ràng |

### 3.1. Dữ liệu mặc định phải loại trừ

Trừ khi nhóm phê duyệt một ngoại lệ có kiểm soát, không đưa vào chỉ mục:

- API key, mật khẩu, access token, private key, connection string và các thông tin bí mật khác.
- Dữ liệu cá nhân hoặc dữ liệu khách hàng/sản xuất mang tính bảo mật không cần thiết.
- File build, cache, binary, thư viện được đóng gói sẵn và file sinh tự động không có mục đích sử dụng đã được duyệt.
- File nằm ngoài repository hoặc phiên bản được cấp quyền.
- Nội dung bên ngoài chưa xác minh được nguồn gốc hoặc giấy phép.
- Kết quả hoặc nhãn kiểm thử theo cách làm lộ đáp án của quá trình đánh giá.

Không thể xác định dữ liệu an toàn chỉ dựa vào phần mở rộng hoặc tên file. Cần có quy tắc loại trừ và quét secrets trước khi lập chỉ mục.

## 4. Quy tắc chia nhỏ dữ liệu (Chunking)

Đề xuất thứ tự ưu tiên:

1. Sử dụng đơn vị mã nguồn theo cấu trúc, chẳng hạn hàm, phương thức, lớp hoặc khai báo hoàn chỉnh khi có thể phân tích cú pháp.
2. Giữ lại ngữ cảnh cấp file và các lệnh import khi cần thiết để hiểu thành phần mã nguồn.
3. Chỉ sử dụng cách chia theo số dòng giới hạn khi không thể phân tích cấu trúc.
4. Tránh gộp nhiều thành phần mã nguồn không liên quan vào cùng một đoạn.
5. Mỗi đoạn dữ liệu phải có tham chiếu ổn định đến file nguồn và phiên bản tương ứng.

Kích thước chunk, phần chồng lặp, mô hình embedding, phương pháp xếp hạng và số lượng kết quả truy xuất chưa được xác định trong tài liệu này. Những thông số đó cần được lựa chọn và đánh giá trên các repository đại diện, không tự đặt số liệu khi chưa có thực nghiệm.

## 5. Metadata tối thiểu đề xuất

Mỗi đoạn dữ liệu được lập chỉ mục cần có metadata đủ để xác định và kiểm tra nguồn gốc. Trước khi triển khai, cần đối chiếu cấu trúc này với các contract hiện có của dự án.

| Trường dữ liệu | Yêu cầu | Mục đích |
|---|---|---|
| `repository_id` | Bắt buộc | Xác định repository |
| `revision` | Bắt buộc | Xác định commit hoặc snapshot bất biến được sử dụng |
| `path` | Bắt buộc | Xác định đường dẫn file tương đối từ thư mục gốc repository |
| `content_type` | Bắt buộc | Phân biệt mã nguồn, test, cấu hình, tài liệu và các loại dữ liệu khác |
| `chunk_id` | Bắt buộc | Định danh đoạn dữ liệu trong snapshot |
| `start_line`, `end_line` | Bắt buộc khi xác định được vị trí dòng | Xác định phạm vi nguồn |
| `symbol_name`, `symbol_type` | Tùy chọn nếu phân tích được thành phần mã nguồn | Hỗ trợ truy xuất theo symbol |
| `content_hash` | Khuyến nghị | Phát hiện nội dung cũ hoặc đã thay đổi |
| `language` | Khuyến nghị khi xác định được | Hỗ trợ xử lý theo ngôn ngữ |
| `source_url` | Tùy chọn | Liên kết đến nguồn khi có và người dùng được cấp quyền |

Tên trường ở trên chỉ là đề xuất. Trước khi triển khai, cần đối chiếu với các model contract hiện có và ưu tiên tái sử dụng tên trường, kiểu dữ liệu đã được dự án thống nhất.

## 6. Truy xuất nguồn gốc và bằng chứng

- Mỗi kết quả truy xuất phải giữ tham chiếu đến repository, phiên bản, đường dẫn và chunk.
- Nếu có thông tin dòng, cần trả về phạm vi dòng liên quan.
- Bằng chứng trong báo cáo phân tích phải thuộc đúng phiên bản đã được lập chỉ mục.
- Nếu file nguồn thay đổi sau khi lập chỉ mục, phải đánh dấu dữ liệu cũ hoặc xây dựng lại chỉ mục; không được gán nội dung cũ cho phiên bản mới.
- Hệ thống phải phân biệt bằng chứng truy xuất được với phần diễn giải do mô hình sinh ra.
- Nếu không đủ bằng chứng, hệ thống phải nêu rõ giới hạn thay vì tự tạo đường dẫn nguồn hoặc khẳng định quan hệ phụ thuộc chưa được chứng minh.

## 7. Bảo mật và ranh giới tin cậy

### 7.1. Secrets và dữ liệu nhạy cảm

- Áp dụng quy tắc loại trừ và quét secrets trước khi lập chỉ mục.
- Không đưa secrets vào embedding, log truy xuất, prompt, báo cáo hoặc dữ liệu kiểm thử.
- Duy trì quyền truy cập repository; RAG không được tiết lộ dữ liệu cho người không có quyền xem nguồn.
- Xác định cách lưu giữ và xóa dữ liệu đã lập chỉ mục khi repository hoặc phiên bản bị xóa.

### 7.2. Prompt injection trong nội dung truy xuất

Mã nguồn, comment, tài liệu, commit message, tên test và nội dung issue đều phải được coi là dữ liệu đầu vào không đáng tin cậy, không phải chỉ thị điều khiển LLM.

- Không cho phép nội dung truy xuất ghi đè chỉ thị hệ thống, quyền truy cập hoặc phạm vi công việc đã được phê duyệt.
- Không thực thi lệnh hoặc gọi công cụ chỉ vì nội dung truy xuất yêu cầu.
- Phân tách rõ nội dung bằng chứng và ghi nguồn của nội dung trong ngữ cảnh gửi cho mô hình.
- Kiểm thử với comment hoặc tài liệu có nội dung cố gắng chuyển hướng mô hình hay tiết lộ secrets.

### 7.3. Quyền truy cập và ghi log

- Áp dụng nguyên tắc quyền tối thiểu cho repository và chỉ mục.
- Hạn chế ghi toàn bộ mã nguồn vào log khi chỉ cần mã định danh nguồn và thông tin chẩn đoán tối thiểu.
- Bảo đảm báo cáo và log không tiết lộ dữ liệu đã bị loại trừ hoặc dữ liệu không được phép truy cập.

## 8. Ngăn rò rỉ dữ liệu và sai lệch đánh giá

Ngữ cảnh truy xuất không được cung cấp cho mô hình đáp án mà quá trình đánh giá đang cần đo lường.

- Phân biệt mã nguồn định nghĩa test với kết quả test đã quan sát.
- Không truy xuất kết quả hoặc nhãn kiểm thử trong tương lai khi đánh giá lựa chọn test tại một phiên bản trước đó.
- Xác định cách chia dữ liệu theo thời gian hoặc phiên bản trước khi sử dụng kết quả lịch sử.
- Ghi nhận phiên bản và nguồn dữ liệu có sẵn tại thời điểm ra quyết định.
- Không sử dụng kết quả pass/fail chỉ xuất hiện sau khi test chạy làm bằng chứng vốn phải có trước khi lựa chọn test.
- Mọi trường hợp sử dụng kết quả lịch sử cần được ghi thành quyết định riêng, kèm mục đích và biện pháp ngăn rò rỉ.

Đây là các biện pháp đề xuất. Nhóm cần thống nhất quy trình đánh giá cụ thể với người phụ trách chính sách lựa chọn regression test.

## 9. Định dạng đầu ra truy xuất đề xuất

Mỗi kết quả RAG nên cung cấp:

- Đoạn nội dung hoặc tham chiếu đến chunk.
- Mã repository và phiên bản.
- Đường dẫn file và phạm vi dòng nếu có.
- Metadata symbol nếu có.
- Điểm hoặc thứ hạng truy xuất nếu cơ chế truy xuất cung cấp.
- Loại nội dung và thông tin nguồn đủ để phân biệt bằng chứng với phần giải thích được sinh ra.

Điểm truy xuất chỉ là tín hiệu xếp hạng, không phải xác suất đã được hiệu chuẩn về tính đúng đắn. Các thành phần phía sau không được xem điểm này là bằng chứng chắc chắn rằng mã nguồn bị ảnh hưởng.

Đầu ra cần cho phép các thành phần phân tích dẫn nguồn và giúp người review tìm lại nội dung gốc.

## 10. Xử lý lỗi và phương án dự phòng

- Nếu không tìm được bằng chứng phù hợp, trả về trạng thái không có bằng chứng hoặc bằng chứng chưa đủ.
- Nếu không xác minh được phiên bản repository, không được tuyên bố bằng chứng chính xác theo phiên bản.
- Nếu phân tích cú pháp thất bại, sử dụng cách chia chunk dự phòng đã được duyệt và đánh dấu metadata symbol/dòng không khả dụng.
- Nếu kiểm tra secrets hoặc quyền truy cập thất bại, dừng lập chỉ mục nội dung liên quan thay vì âm thầm bỏ qua biện pháp bảo vệ.
- Nếu chỉ mục cũ hoặc không khả dụng, phải báo rõ hạn chế; không được giả vờ rằng truy xuất đã thành công.

Tên API và cấu trúc lỗi cụ thể phải tuân theo contract hiện có của dự án.

## 11. Danh sách tiêu chí nghiệm thu

- [ ] Đã mô tả loại dữ liệu được phép sử dụng và các trường hợp loại trừ.
- [ ] Đã xác định metadata cần thiết và đối chiếu với contract hiện có.
- [ ] Có thể truy xuất nguồn gốc đến repository, phiên bản, đường dẫn và phạm vi nguồn khi có.
- [ ] Đã mô tả cách xử lý secrets và dữ liệu nhạy cảm.
- [ ] Đã xác định nội dung truy xuất là đầu vào không đáng tin cậy.
- [ ] Đã mô tả rủi ro và biện pháp ngăn rò rỉ kết quả/nhãn kiểm thử.
- [ ] Đã liệt kê các quyết định nằm ngoài phạm vi thay vì tự suy đoán.
- [ ] Các câu hỏi còn mở có người phụ trách hoặc được đưa ra nhóm xem xét.
- [ ] Tài liệu được review bởi các thành viên phụ trách kiến trúc, truy xuất và lựa chọn kiểm thử liên quan.

## 12. Các quyết định cần nhóm xem xét

Các nội dung sau vẫn chưa được quyết định trong bản nháp:

1. Những loại dữ liệu nào được phép dùng trong MVP đầu tiên?
2. Có loại trừ hoàn toàn kết quả test lịch sử khỏi RAG trong MVP hay cho phép một quy trình riêng có kiểm soát?
3. Sử dụng parser và phương pháp chia chunk nào cho từng ngôn ngữ được hỗ trợ?
4. Metadata schema chuẩn trong các contract hiện tại là gì?
5. Nhóm sẽ chọn nơi lưu chỉ mục và mô hình embedding nào, nếu cần?
6. Quyền truy cập repository, việc xóa chỉ mục và thời hạn lưu dữ liệu sẽ được thực thi như thế nào?
7. Quy trình chia dữ liệu đánh giá nào ngăn được rò rỉ theo thời gian và nhãn?
8. Ai có quyền phê duyệt thay đổi chính sách dữ liệu RAG?

Tài liệu này chưa chọn vector database, mô hình embedding, nhà cung cấp LLM, kích thước chunk, giá trị top-k hoặc chỉ tiêu hiệu năng cụ thể.

## 13. Công việc liên quan và phụ thuộc

- **Git diff và ngữ nghĩa revision:** cần thiết để gắn ngữ cảnh truy xuất với đúng snapshot gốc và đích.
- **Phân tích phụ thuộc:** có thể cung cấp tín hiệu cấu trúc cho truy xuất, nhưng cần phân biệt với bằng chứng lấy từ mã nguồn.
- **Chính sách lựa chọn regression test:** xác định cách sử dụng bằng chứng truy xuất và cách xử lý độ không chắc chắn.
- **Kế hoạch nghiên cứu và đánh giá:** xác định cách chia dữ liệu và biện pháp chống rò rỉ.

Các mối liên hệ này mô tả những điểm cần phối hợp, không khẳng định các task khác đã hoàn thành.

## 14. Trạng thái review

| Hạng mục | Trạng thái |
|---|---|
| Soạn bản nháp | Đã chuẩn bị nội dung; chờ lưu và review trong repository |
| Đối chiếu với contract hiện tại | Chưa hoàn tất |
| Nhóm phê duyệt | Chờ xác nhận |
| Bắt đầu triển khai code | Không thuộc phạm vi của tài liệu này |
