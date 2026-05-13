# BÁO CÁO TỔNG QUAN HỆ THỐNG QUẢN LÝ SỰ KIỆN (EMS)

**Ngày:** 13/05/2026

**Tác giả:** Gemini Code Assist

## 1. Giới thiệu

Hệ thống Quản lý Sự kiện (Event Management System - EMS) là một ứng dụng web toàn diện được xây dựng trên nền tảng Streamlit và cơ sở dữ liệu SQL. Hệ thống được thiết kế để số hóa và tối ưu hóa toàn bộ quy trình tổ chức, quản lý và tham gia sự kiện, từ khâu lập kế hoạch của ban tổ chức đến trải nghiệm kết nối của người tham dự.

Kiến trúc của hệ thống phân chia rõ ràng hai luồng người dùng chính:

1.  **Quản trị viên (Admin / Organizer):** Cung cấp bộ công cụ mạnh mẽ để quản lý mọi khía cạnh của sự kiện.
2.  **Khách tham dự (Guest):** Cung cấp một cổng thông tin (portal) hiện đại để tương tác, kết nối và tận dụng tối đa giá trị từ sự kiện.

## 2. Phân tích Chức năng chi tiết

### 2.1. Luồng Quản trị viên (Admin / Organizer)

Đây là khu vực quản lý nội bộ, được bảo vệ bằng tài khoản và phân quyền chi tiết, đảm bảo chỉ những người có thẩm quyền mới có thể truy cập.

#### 2.1.1. Dashboard Ban Tổ Chức (`2_Dashboard_Ban_Tổ_Chức.py`)

- **Luồng tạo sự kiện nhanh (2 bước):** Giao diện được thiết kế đặc biệt cho Ban tổ chức (Organizer) để nhanh chóng khởi tạo một sự kiện mới.
    - **Bước 1:** Nhập thông tin cơ bản (tên, ngày, địa điểm).
    - **Bước 2:** Cấu hình chi tiết các hạng vé (giá, số lượng) và thiết kế biểu mẫu đăng ký tùy chỉnh (custom fields) để thu thập thông tin chuyên sâu từ khách mời.

#### 2.1.2. Quản lý Sự kiện (`1_Quản_lý_Sự_kiện.py`)

- **CRUD đầy đủ:** Tạo, xem, sửa, xóa sự kiện.
- **Bộ lọc & Tìm kiếm:** Dễ dàng lọc sự kiện theo trạng thái (Sắp diễn ra, Đã đầy, Đã hoàn thành...) và tìm kiếm theo tên.
- **Xem chi tiết:** Hiển thị thông tin đầy đủ của một sự kiện, bao gồm các chỉ số hiệu suất chính (KPIs) như tỷ lệ tham dự, số dư tài chính, và số chỗ còn trống.
- **Tạo mã QR:** Tự động tạo mã QR cho việc Check-in và Check-out, có thể in ra và đặt tại quầy lễ tân.
- **Tùy chỉnh Giao diện (Branding):** Cho phép tùy chỉnh màu sắc, ảnh bìa cho từng trang sự kiện riêng biệt.
- **Quản lý đăng ký nhanh:** Xem danh sách khách đã đăng ký cho sự kiện và điều hướng nhanh đến trang Check-in.

#### 2.1.3. Quản lý Khách mời (`3_Khách_mời.py`)

- **CRUD Khách mời:** Quản lý tập trung cơ sở dữ liệu khách mời của hệ thống.
- **Tìm kiếm thời gian thực:** Tìm kiếm khách mời theo tên hoặc email.
- **Import hàng loạt:** Hỗ trợ tải lên file CSV để thêm nhiều khách mời cùng lúc.
- **Phân tích hoạt động:**
    - Thống kê "Top khách tích cực" (những người tham gia nhiều sự kiện nhất).
    - Xem lịch sử tham gia sự kiện của một khách mời cụ thể.

#### 2.1.4. Đăng ký & Check-in (`4_Đăng_ký_và_Check_in.py`)

- **Giao diện tập trung:** Quản lý toàn bộ lượt đăng ký cho một sự kiện được chọn.
- **Check-in bằng một cú nhấp:** Nút "Check-in" được tích hợp trên mỗi dòng thông tin khách mời, giúp nhân viên lễ tân thao tác nhanh chóng.
- **Đăng ký thủ công:** Cho phép nhân viên đăng ký cho khách trực tiếp tại sự kiện.
- **Xử lý hàng loạt:** Cung cấp chức năng đánh dấu "No-show" (không tham dự) cho tất cả những ai đã đăng ký nhưng không check-in sau khi sự kiện kết thúc.
- **Kết thúc sự kiện:** Một stored procedure tự động hóa việc chuyển trạng thái sự kiện sang "Completed" và cập nhật "No-show".

#### 2.1.5. Quản lý Tài chính (`5_Tài_chính.py`)

- **Ghi nhận Thu/Chi:** Giao diện trực quan để nhập các khoản thu (phí tài trợ, bán vé) và chi (thuê địa điểm, catering).
- **Báo cáo tổng quan:** Biểu đồ cột và biểu đồ đường trực quan hóa dòng tiền (thu, chi, số dư) của từng sự kiện.
- **Báo cáo theo kỳ:** Cho phép lọc và xem báo cáo tài chính trong một khoảng thời gian tùy chọn.
- **Cấu hình tài khoản ngân hàng:** Ban tổ chức có thể nhập thông tin tài khoản ngân hàng để hiển thị cho khách hàng khi thanh toán.

#### 2.1.6. Báo cáo & Thống kê (`6_Báo_cáo_Thống_kê.py`)

- **Dashboard đa chiều:** Một trang tổng hợp mạnh mẽ với nhiều tab phân tích chuyên sâu:
    - **Sự kiện:** Tỷ lệ tham dự trung bình, biểu đồ đăng ký vs. tham dự.
    - **Bán vé:** Tốc độ bán vé theo ngày, tỷ lệ lấp đầy sức chứa, phễu chuyển đổi.
    - **Nhân khẩu học:** Phân tích chân dung khách hàng (giới tính, độ tuổi) và phân tích dữ liệu từ các câu hỏi trong form đăng ký.
    - **Top khách:** Bảng xếp hạng những khách mời/công ty tích cực nhất.
    - **Địa điểm:** Thống kê tần suất sử dụng các địa điểm.
    - **Tài chính:** Biểu đồ số dư ròng của các sự kiện.
- **Xuất Excel:** Chức năng xuất báo cáo ra file Excel, cho phép tùy chọn các sheet dữ liệu (tổng hợp, tài chính, danh sách khách...).

### 2.2. Luồng Khách tham dự (Guest)

Đây là cổng thông tin dành cho người dùng cuối, giúp họ khám phá sự kiện và tương tác với cộng đồng.

#### 2.2.1. Cổng Sự kiện (`7_Cổng_Sự_Kiện.py`)

- **Khám phá sự kiện:** Hiển thị danh sách các sự kiện sắp diễn ra với giao diện hiện đại.
- **Bộ lọc thông minh:** Lọc sự kiện theo ngành nghề, loại hình, đối tượng tham dự và chi phí.
- **Sự kiện riêng tư:** Hỗ trợ các sự kiện kín, yêu cầu người dùng nhập mã mời (access code) để xem chi tiết và đăng ký.
- **Quy trình đăng ký chi tiết:**
    - **Chọn hạng vé:** Hỗ trợ nhiều loại vé với các mức giá khác nhau.
    - **Đăng ký nhóm:** Cho phép một người đại diện đăng ký cho nhiều thành viên.
    - **Form tùy biến:** Tự động hiển thị các câu hỏi do ban tổ chức thiết lập.
    - **Xuất hóa đơn VAT:** Tùy chọn nhập thông tin công ty để yêu cầu hóa đơn đỏ.
    - **Thanh toán:** Hỗ trợ nhiều phương thức và hiển thị thông tin chuyển khoản của ban tổ chức.

#### 2.2.2. Quản lý Đăng ký (`8_Quản_Lý_Đăng_Ký.py`)

- **"Vé Của Tôi":** Liệt kê tất cả các sự kiện người dùng đã đăng ký.
- **Ủy quyền tham dự:** Cho phép người dùng chuyển nhượng vé của mình cho người khác.
- **Yêu cầu hoàn tiền/Hủy vé:** Cung cấp chức năng để gửi yêu cầu hoàn tiền hoặc hủy đăng ký (đối với vé miễn phí).

#### 2.2.3. Hồ sơ Doanh nghiệp (`10_Hồ_Sơ_Doanh_Nghiệp.py`)

- **Quản lý thông tin cá nhân:** Cập nhật thông tin công việc, giới thiệu bản thân.
- **Thiết lập nhu cầu kết nối:** Khai báo "Sở trường/Dịch vụ cung cấp" và "Mục tiêu tìm kiếm" để hệ thống AI matchmaking hoạt động hiệu quả.
- **Gian hàng ảo (Virtual Booth):** Cho phép người dùng đính kèm link portfolio (brochure) và video giới thiệu công ty.
- **Xác minh KYC:** Quy trình tải giấy phép kinh doanh để nhận "dấu tích xanh", tăng độ uy tín.

#### 2.2.4. Kết nối & Tương tác (`9_Kết_Nối_Đối_Tác.py`)

- **Trung tâm tương tác sự kiện:**
    - **Lịch trình (Agenda):** Xem các phiên thảo luận trong sự kiện.
    - **Danh bạ người tham dự:** Xem hồ sơ của các khách mời khác (có chế độ ẩn thông tin cá nhân).
    - **Gợi ý kết nối (AI Matchmaking):** Hệ thống tự động đề xuất các đối tác tiềm năng dựa trên hồ sơ.
    - **Hẹn gặp:** Gửi lời mời họp 1:1 tới các đối tác khác.
    - **Quét mã QR (Lead Scanning):** Trao đổi namecard điện tử bằng cách quét mã QR của nhau.
    - **Hỏi đáp (Live Q&A):** Gửi câu hỏi trực tiếp cho diễn giả.

#### 2.2.5. Báo cáo & Tài liệu (`11_Báo_Cáo_&_Tài_Liệu.py`)

- **Kho tài liệu:** Tải về các tài liệu sau sự kiện như slide thuyết trình, hình ảnh.
- **Chứng nhận tham dự:** Tự động cấp chứng nhận điện tử cho những người đã check-in thành công.
- **Gửi phản hồi:** Cung cấp các phiếu khảo sát chi tiết, chuyên biệt cho từng loại hình sự kiện (Công nghệ, Giáo dục, Giải trí...).
- **Phân tích tương tác cá nhân:** Xem các chỉ số về lượt xem hồ sơ, lượt tải brochure, số lời mời họp đã nhận.
- **Tích hợp CRM:** Xuất danh sách các "leads" (đối tác tiềm năng) đã thu thập và đồng bộ với các hệ thống CRM bên ngoài (mockup).

## 3. Kiến trúc & Công nghệ

### 3.1. Giao diện người dùng (Frontend)

- **Nền tảng:** **Streamlit**, một framework Python cho phép xây dựng ứng dụng web dữ liệu một cách nhanh chóng.
- **Thiết kế:** Giao diện được tùy chỉnh sâu bằng CSS (`app/ui/styles.py`) để tạo ra một theme hiện đại, nhất quán và chuyên nghiệp, vượt ra ngoài giao diện mặc định của Streamlit.
- **Tổ chức:** Cấu trúc file được sắp xếp logic theo vai trò người dùng (Admin/Guest) và được đánh số thứ tự để kiểm soát menu sidebar. Các script như `organize_project.py` và `doi_ten_sidebar.py` được sử dụng để tự động hóa việc duy trì cấu trúc này.

### 3.2. Lớp ứng dụng (Backend/Application Logic)

- **Ngôn ngữ:** **Python**.
- **Kiến trúc:** Logic nghiệp vụ được đóng gói trong các lớp Repository (`app/database/repositories`), giúp tách biệt phần xử lý dữ liệu khỏi giao diện.
- **Xác thực & Phân quyền:**
    - Sử dụng **SQLAlchemy ORM** để quản lý mô hình người dùng, vai trò và quyền hạn (`app/database/auth_models.py`).
    - Hệ thống phân quyền chi tiết (RBAC) được triển khai ở cả tầng giao diện (ẩn/hiện menu) và tầng backend (kiểm tra vai trò trước khi thực thi hành động).

### 3.3. Cơ sở dữ liệu (Database)

- **Hệ quản trị CSDL:** **MySQL**.
- **Thiết kế bảo mật (`database/phase4_security.sql`):**
    - **RBAC ở tầng CSDL:** Tạo ra các `ROLE` (`event_manager`, `checkin_staff`) với quyền hạn tối thiểu cần thiết (Least Privilege).
    - **View an toàn (Secure Views):** Sử dụng các `VIEW` như `v_safe_guests` để ẩn các thông tin nhạy cảm (email, SĐT) khỏi các vai trò không cần thiết.
    - **Stored Procedures:** Đóng gói các nghiệp vụ phức tạp (đăng ký, check-in, kết thúc sự kiện) vào các Stored Procedure để đảm bảo tính toàn vẹn dữ liệu và tăng cường bảo mật.
- **Tối ưu hóa:** Các chỉ mục (index) được thiết lập trên các cột thường xuyên được truy vấn để đảm bảo hiệu năng.

## 4. Kết luận

Hệ thống EMS là một giải pháp phần mềm mạnh mẽ, được thiết kế tốt và có kiến trúc rõ ràng. Việc áp dụng các nguyên tắc bảo mật từ tầng giao diện đến tầng cơ sở dữ liệu, kết hợp với giao diện người dùng thân thiện và các tính năng tự động hóa thông minh, đã tạo nên một sản phẩm hoàn chỉnh, sẵn sàng cho việc triển khai và vận hành trong thực tế.

---
*Báo cáo được tạo tự động bởi Gemini Code Assist.*