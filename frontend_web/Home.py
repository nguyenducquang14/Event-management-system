"""
Home.py
Trang chủ và Màn hình Đăng nhập của ứng dụng Web Streamlit
"""
import streamlit as st
from app.database.auth_models import login_user, register_user, Base as AuthBase, seed_data
from app.config import get_db, engine # Assuming app.config is where get_db and engine are defined
from app.ui.styles import CUSTOM_CSS, GUEST_CSS # Import GUEST_CSS from styles.py
from sqlalchemy import text
import time

st.set_page_config(page_title="EMS | Trang chủ", page_icon="📅", layout="wide")

# --- KHỞI TẠO CƠ SỞ DỮ LIỆU BẢO MẬT (AUTH) ---
# Tự động tạo các bảng users, roles nếu chưa có và chèn dữ liệu quyền hạn mặc định
@st.cache_resource
def init_auth_db():
    # with engine.begin() as conn:
    #     conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    #     AuthBase.metadata.drop_all(conn)
    #     conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    AuthBase.metadata.create_all(engine)
    with get_db() as db_session:
        seed_data(db_session)

init_auth_db()

def render_landing_page():
    # Dùng layout wide và cột space lớn để ép 2 nút ra góc ngoài cùng bên phải
    col_logo, col_space, col_login, col_reg = st.columns([3, 6, 1, 1])
    
    with col_logo:
        st.markdown("### :material/event: Hệ thống EMS")
        
    with col_login:
        if st.button("Đăng nhập", use_container_width=True):
            st.session_state["current_page"] = "login"
            st.rerun()
            
    with col_reg:
        if st.button("Đăng ký", type="primary", use_container_width=True):
            st.session_state["current_page"] = "register"
            st.rerun()
            
    st.divider()
    
    # Phần Hero Section (Slogan & Giới thiệu)
    st.markdown("<h1 style='text-align: center; color: #000000; font-size: 3rem;'>EventOS: Nền tảng Quản trị Sự kiện Chuyên nghiệp</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #000000; margin-bottom: 2rem;'>Vận hành mượt mà. Kết nối dễ dàng. Quản trị toàn diện.</h4>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; font-size: 1.15rem; max-width: 900px; margin: 0 auto; line-height: 1.6; color: #000000;'>
    <strong>DATCOM EventOS</strong> là giải pháp phần mềm thế hệ mới, được thiết kế để giải quyết triệt để các bài toán phức tạp trong công tác điều phối và tổ chức sự kiện. Dù bạn đang vận hành một hội thảo quy mô nhỏ hay một chuỗi sự kiện doanh nghiệp lớn, hệ thống của chúng tôi sẽ giúp số hóa toàn bộ quy trình, từ khâu lên ý tưởng ban đầu đến khi phân tích báo cáo hậu sự kiện.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Phần Chi tiết tính năng (Chia 2 cột)
    col_feat, col_tech = st.columns(2, gap="large")
    
    with col_feat:
        st.markdown("### :material/star: Tính năng Cốt lõi")
        st.markdown("""
        - **:material/calendar_today: Quản lý Lịch trình & Sự kiện Thông minh:** Khởi tạo, theo dõi và cập nhật trạng thái các sự kiện theo thời gian thực. Tự động hóa việc kiểm tra tình trạng trống của các địa điểm tổ chức để tránh xung đột lịch trình.
        - **:material/groups: Mạng lưới Khách mời & Ban tổ chức:** Lưu trữ tập trung thông tin khách mời (Email, Số điện thoại) với độ bảo mật cao. Theo dõi sát sao tiến độ gửi lời mời và xác nhận tham dự. Phân quyền quản lý rõ ràng cho từng thành viên trong ban tổ chức.
        - **:material/how_to_reg: Kiểm soát Điểm danh Hiện đại:** Quản lý danh sách đăng ký tham gia trực tiếp trên hệ thống. Tự động cập nhật sức chứa của địa điểm ngay khi có khách đăng ký mới.
        - **:material/analytics: Báo cáo & Phân tích Đa chiều:** Hệ thống tự động trích xuất các báo cáo thống kê về tỷ lệ tham dự thực tế, mật độ sử dụng cơ sở vật chất và các chỉ số hiệu suất của sự kiện.
        """)
        
    with col_tech:
        st.markdown("### :material/security: Nền tảng Công nghệ & Bảo mật")
        st.info("""
        **Kiến trúc mạnh mẽ:** Được xây dựng trên kiến trúc lõi mạnh mẽ, DATCOM EventOS không chỉ đáp ứng tốt các sự kiện thông thường mà còn được tối ưu hóa hiệu năng để xử lý khối lượng dữ liệu khổng lồ trong các đợt đăng ký quy mô lớn.
        """, icon=":material/rocket_launch:")
        st.success("""
        **Phân quyền Đa tầng (RBAC):** Hệ thống kiểm soát truy cập nghiêm ngặt dựa trên vai trò (Admin, Organizer, Staff), đảm bảo chỉ những nhân sự được cấp quyền mới có thể thao tác trên dữ liệu nhạy cảm.
        """, icon=":material/admin_panel_settings:")
        st.warning("""
        **Giao diện Tốc độ cao:** Khác biệt với các nền tảng Web cồng kềnh, hệ thống quản trị nội bộ được vận hành qua Giao diện Dòng lệnh (CLI) tiên tiến, cho phép các chuyên viên điều phối thao tác với tốc độ mili-giây, không độ trễ.
        """, icon=":material/speed:")

def render_login_page():
    # Bơm CSS để định dạng khung form
    st.markdown("""
    <style>
    [data-testid="column"]:nth-of-type(2) {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    [data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("← Quay lại Trang chủ"):
        st.session_state["current_page"] = "landing"
        st.rerun()
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Căn giữa Form trên màn hình
    _, col_main, _ = st.columns([1, 1.2, 1])
    
    with col_main:
        st.title(":material/login: Đăng nhập")
        st.markdown("Vui lòng đăng nhập để quản lý Sự kiện, Khách mời và Tài chính.")
        st.divider()
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập (Username)")
            password = st.text_input("Mật khẩu (Password)", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Đăng nhập", type="primary", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Vui lòng nhập đầy đủ thông tin!", icon=":material/warning:")
                else:
                    with st.spinner("Đang xác thực..."):
                        with get_db() as db_session:
                            result = login_user(db_session, username, password)
                    
                    if result["success"]:
                        # Lưu thông tin vào session_state của Streamlit
                        st.session_state["token"] = result["token"]
                        st.session_state["user_info"] = result["user_info"]
                        st.success("Đăng nhập thành công!", icon=":material/check_circle:")
                        st.rerun() # Refresh lại trang để vào Dashboard
                    else:
                        st.error(result["error"], icon=":material/error:")

def render_register_page():
    # Bơm CSS để định dạng khung form
    st.markdown("""
    <style>
    [data-testid="column"]:nth-of-type(2) {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    [data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("← Quay lại Trang chủ"):
        st.session_state["current_page"] = "landing"
        st.rerun()
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Căn giữa Form trên màn hình
    _, col_main, _ = st.columns([1, 1.2, 1])
    
    with col_main:
        st.title(":material/person_add: Đăng ký Tài khoản")
        st.markdown("Điền thông tin dưới đây để tạo tài khoản mới.")
        st.divider()
        
        # Lựa chọn loại tài khoản để phân quyền RBAC
        acc_type = st.radio("Bạn muốn tham gia với tư cách:", ["🤝 Doanh nghiệp / Đối tác tham dự", "⚙️ Ban tổ chức sự kiện"], horizontal=True)
        
        with st.form("register_form"):
            if "Đối tác" in acc_type:
                fullname = st.text_input("Họ tên Người đại diện *", placeholder="Ví dụ: Nguyễn Văn A")
                username = st.text_input("Tên đăng nhập *", placeholder="Ví dụ: nguyenvana")
                role_assign = "Guest" # Quyền Guest đóng vai trò là Doanh nghiệp/Đối tác tham gia sự kiện
            else:
                fullname = st.text_input("Tên Ban tổ chức *", placeholder="Ví dụ: Hiệp hội Tech VN")
                username = st.text_input("Tài khoản Ban tổ chức *", placeholder="Ví dụ: tech_org")
                role_assign = "Organizer" # Quyền Organizer quản lý sự kiện
                
            email = st.text_input("Địa chỉ Email *", placeholder="Ví dụ: email@domain.com")
            password = st.text_input("Mật khẩu *", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu *", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True)
            
        # ĐƯA LOGIC RA NGOÀI FORM (Tránh lỗi ngầm của Streamlit)
        if submitted:
            print(f"DEBUG: Đang xử lý đăng ký cho Username: {username}, Email: {email}")
            if not fullname or not username or not email or not password or not confirm_password:
                st.error("Vui lòng điền đầy đủ thông tin!", icon=":material/warning:")
            elif password != confirm_password:
                st.error("Mật khẩu xác nhận không khớp!", icon=":material/warning:")
            else:
                try:
                    with st.spinner("Đang kết nối Database để tạo tài khoản..."):
                        with get_db() as db_session:
                            res = register_user(db_session, username, password, fullname, email, role_assign)
                    
                    if res["success"]:
                        st.success(f"{res['message']} Đang chuyển hướng...", icon=":material/check_circle:")
                        time.sleep(1.5)
                        st.session_state["current_page"] = "login"
                        st.rerun()
                    else:
                        st.error(f"Lỗi hệ thống: {res['error']}", icon=":material/error:")
                except Exception as e:
                    # Bắt mọi lỗi sập kết nối và ép hiển thị ra màn hình
                    st.error(f"Lỗi Database nghiêm trọng: {str(e)}", icon=":material/warning:")
                    print(f"CRITICAL ERROR: {str(e)}")

def render_dashboard():
    user = st.session_state["user_info"]
    roles = user.get("roles", [])
    
    # NẾU LÀ GUEST: Chuyển hướng thẳng đến trang Sự kiện Công khai, bỏ qua Dashboard Admin
    if "Guest" in roles and "Admin" not in roles and "Organizer" not in roles:
        st.switch_page("pages/7_Sự_Kiện_Công_Khai.py")
        return
        
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # --- ẨN CÁC MENU CỦA GUEST ĐỐI VỚI ADMIN/ORGANIZER ---
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] ul li:nth-child(8),
        [data-testid="stSidebarNav"] ul li:nth-child(9),
        [data-testid="stSidebarNav"] ul li:nth-child(10),
        [data-testid="stSidebarNav"] ul li:nth-child(11),
        [data-testid="stSidebarNav"] ul li:nth-child(12),
        [data-testid="stSidebarNav"] ul li:nth-last-child(1),
        [data-testid="stSidebarNav"] ul li:nth-last-child(2),
        [data-testid="stSidebarNav"] ul li:nth-last-child(3),
        [data-testid="stSidebarNav"] ul li:nth-last-child(4),
        [data-testid="stSidebarNav"] ul li:nth-last-child(5) { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Chào mừng đến với Hệ thống Quản lý Sự kiện! :material/celebration:")
    
    st.success(f"Xin chào **{user['name']}**!")
    st.info(f"Vai trò của bạn trong hệ thống: **{', '.join(roles)}**")
    
    st.markdown("### 👈 Vui lòng chọn các chức năng từ Menu bên trái.")
    
    st.divider()
    if st.button("Đăng xuất", icon=":material/logout:"):
        st.session_state.clear()
        st.rerun()

# --- LUỒNG ĐIỀU KHIỂN CHÍNH ---
# Khởi tạo state current_page nếu chưa có
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "landing"

if "token" in st.session_state:
    render_dashboard()
else:
    # Chỉ chèn CSS làm ẩn sidebar và đổi màu khi chưa đăng nhập
    st.markdown(GUEST_CSS, unsafe_allow_html=True)
    
    if st.session_state["current_page"] == "landing":
        render_landing_page()
    elif st.session_state["current_page"] == "login":
        render_login_page()
    elif st.session_state["current_page"] == "register":
        render_register_page()