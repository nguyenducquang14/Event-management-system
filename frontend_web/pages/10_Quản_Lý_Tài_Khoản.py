"""
pages/7_Quan_Ly_Tai_Khoan.py
Cập nhật thông tin cá nhân dành cho Guest
"""
import streamlit as st
import datetime
from sqlalchemy import text
from app.config import get_db
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Quản Lý Tài Khoản", page_icon="👤", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "token" not in st.session_state or "user_info" not in st.session_state:
    st.switch_page("Home.py")

roles = st.session_state["user_info"].get("roles", [])
if "Guest" not in roles:
    st.error("Lỗi 403: Cấm truy cập. Không gian này dành riêng cho Khách mời / Người tham dự.")
    st.stop()

# --- PHÂN QUYỀN SIDEBAR CHO GUEST ---
if "Admin" not in roles and "Organizer" not in roles:
    st.markdown("""
    <style>
        /* Ẩn TẤT CẢ các menu quản trị, chỉ giữ lại 5 menu cuối cùng của Guest */
        [data-testid="stSidebarNav"] ul li { display: none !important; }
        [data-testid="stSidebarNav"] ul li:nth-last-child(1),
        [data-testid="stSidebarNav"] ul li:nth-last-child(2),
        [data-testid="stSidebarNav"] ul li:nth-last-child(3),
        [data-testid="stSidebarNav"] ul li:nth-last-child(4),
        [data-testid="stSidebarNav"] ul li:nth-last-child(5) { display: list-item !important; }
    </style>
    """, unsafe_allow_html=True)
    with st.sidebar:
        st.info(f"Xin chào, **{st.session_state['user_info']['name']}**", icon=":material/person:")
        if st.button("Đăng xuất", icon=":material/logout:", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")

user_info = st.session_state["user_info"]
user_email = user_info.get("email")

def get_or_create_guest(email, name):
    with get_db() as db:
        # Đảm bảo bảng Guests có đầy đủ các cột mở rộng
        for col, col_type in [
            ("is_public", "BOOLEAN DEFAULT TRUE"),
            ("job_title", "VARCHAR(150)"),
            ("company", "VARCHAR(150)"),
            ("gender", "VARCHAR(20)"),
            ("dob", "DATE"),
            ("bio", "TEXT"),
            ("linkedin_url", "VARCHAR(255)"),
            ("services_offered", "VARCHAR(255)"),
            ("buying_intent", "VARCHAR(255)"),
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("kyc_status", "VARCHAR(50) DEFAULT 'Unverified'"),
            ("portfolio_url", "VARCHAR(500)"),
            ("video_url", "VARCHAR(500)")
        ]:
            try:
                db.execute(text(f"ALTER TABLE Guests ADD COLUMN {col} {col_type}"))
            except Exception:
                pass
            
        guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        if not guest:
            db.execute(text("INSERT INTO Guests (guest_name, email) VALUES (:name, :email)"), {"name": name, "email": email})
            guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        return dict(guest._mapping)

guest_record = get_or_create_guest(user_email, user_info["name"])
guest_id = guest_record["guest_id"]

st.title(":material/manage_accounts: Quản Lý Tài Khoản Cá Nhân")

verified_badge = "✅ (Đã xác minh KYC)" if guest_record.get("is_verified") else "⚠️ (Chưa xác minh KYC)"
st.markdown(f"**Hồ sơ của:** {guest_record.get('guest_name')} {verified_badge}")

tab_profile = st.tabs(["👤 Thông tin Hồ sơ"])[0]

# TAB 1: PROFILE
with tab_profile:
    with st.form("form_edit_profile", border=True):
        st.info("Cập nhật thông tin cá nhân và nhu cầu kết nối để nâng cao trải nghiệm tại sự kiện.", icon=":material/person:")
        
        st.markdown("#### 1. Thông tin Cá nhân")
        c1, c2 = st.columns(2)
        new_name = c1.text_input("Họ và Tên *", value=guest_record["guest_name"])
        
        current_dob = guest_record.get("dob")
        default_dob = current_dob if current_dob else datetime.date(2000, 1, 1)
        new_dob = c2.date_input("Ngày sinh", value=default_dob, min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
        
        c_gender, c_phone = st.columns(2)
        gender_opts = ["Không tiết lộ", "Nam", "Nữ", "Khác"]
        current_gender = guest_record.get("gender")
        gender_idx = gender_opts.index(current_gender) if current_gender in gender_opts else 0
        new_gender = c_gender.selectbox("Giới tính", gender_opts, index=gender_idx)
        new_phone = c_phone.text_input("Số điện thoại liên hệ", value=guest_record.get("phone_number") or "")

        st.markdown("#### 2. Thông tin Công việc")
        c3, c4 = st.columns(2)
        new_job = c3.text_input("Chức danh / Nghề nghiệp", value=guest_record.get("job_title") or "", placeholder="Ví dụ: Sinh viên, Chuyên viên...")
        new_company = c4.text_input("Đơn vị / Tổ chức / Trường học", value=guest_record.get("company") or "", placeholder="Ví dụ: Đại học XYZ...")
        
        new_linkedin = st.text_input("Website / Mạng xã hội (LinkedIn/Facebook)", value=guest_record.get("linkedin_url") or "", placeholder="https://linkedin.com/in/...")
        new_bio = st.text_area("Giới thiệu ngắn về bản thân", value=guest_record.get("bio") or "", placeholder="Vài dòng giới thiệu để mọi người dễ dàng làm quen với bạn...", height=100)
        
        st.markdown("#### 3. Nhu cầu Giao lưu (Networking)")
        c5, c6 = st.columns(2)
        new_services = c5.text_area("Sở trường / Lĩnh vực chuyên môn", value=guest_record.get("services_offered") or "", placeholder="Ví dụ: Lập trình Python, Marketing, Thiết kế đồ họa...", height=80)
        new_intent = c6.text_area("Mục tiêu tìm kiếm tại sự kiện", value=guest_record.get("buying_intent") or "", placeholder="Ví dụ: Tìm kiếm cơ hội việc làm, học hỏi kiến thức mới, kết nối bạn bè...", height=80)

        st.markdown("#### 4. Chế độ Bảo mật")
        is_public_val = guest_record.get("is_public")
        is_public_val = True if is_public_val is None else bool(is_public_val)
        new_is_public = st.checkbox("Hiển thị hồ sơ trên Danh bạ Sự kiện để mọi người có thể kết nối", value=is_public_val)
        
        if st.form_submit_button("Lưu thay đổi", icon=":material/save:", type="primary", use_container_width=True):
            with get_db() as db:
                db.execute(text("""
                    UPDATE Guests 
                    SET guest_name = :name, phone_number = :phone, is_public = :is_public,
                        job_title = :job_title, company = :company, gender = :gender, 
                        dob = :dob, bio = :bio, linkedin_url = :linkedin,
                        services_offered = :services, buying_intent = :intent
                    WHERE guest_id = :gid
                """), {
                    "name": new_name, "phone": new_phone, "is_public": new_is_public,
                    "job_title": new_job, "company": new_company, "gender": new_gender,
                    "dob": new_dob, "bio": new_bio, "linkedin": new_linkedin, "services": new_services, "intent": new_intent, "gid": guest_id
                })
                db.execute(text("UPDATE users SET full_name = :name WHERE email = :email"), {"name": new_name, "email": user_email})
            
            st.session_state["user_info"]["name"] = new_name
            st.success("Cập nhật hồ sơ chuyên nghiệp thành công!")
            st.rerun()

# TAB 2: SHOWCASE
with tab_showcase:
    st.subheader("Gian hàng ảo (Virtual Booth & Showcase)")
    st.write("Cập nhật tài liệu quảng cáo (Brochure) và video giới thiệu để đối tác có thể tìm hiểu trước về sản phẩm/dịch vụ của bạn.")
    
    with st.form("form_showcase", border=True):
        new_portfolio = st.text_input("Đường dẫn Tài liệu / Brochure / Portfolio (URL PDF/Drive)", value=guest_record.get("portfolio_url") or "", placeholder="https://drive.google.com/...")
        new_video = st.text_input("Video giới thiệu doanh nghiệp (YouTube / Vimeo URL)", value=guest_record.get("video_url") or "", placeholder="https://youtube.com/watch?v=...")
        
        if st.form_submit_button("Cập nhật Gian hàng ảo", icon=":material/store:", type="primary", use_container_width=True):
            with get_db() as db:
                db.execute(text("UPDATE Guests SET portfolio_url = :p, video_url = :v WHERE guest_id = :gid"), {"p": new_portfolio, "v": new_video, "gid": guest_id})
            st.success("Đã cập nhật Virtual Booth thành công!")
            st.rerun()

# TAB 3: TEAM
with tab_team:
    st.subheader("Quản lý Tài khoản Con (Parent - Child Accounts)")
    st.write("Là Tài khoản Mẹ (Admin Doanh nghiệp), bạn có thể quản lý danh sách các đại diện khác cùng công ty tham gia sự kiện.")
    
    company_name = guest_record.get("company")
    if not company_name:
        st.warning("Vui lòng cập nhật Tên Doanh Nghiệp ở tab 'Hồ sơ Doanh nghiệp' trước khi quản lý nhóm.")
    else:
        with get_db() as db:
            team = db.execute(text("SELECT guest_name, email, job_title FROM Guests WHERE company = :c AND guest_id != :gid"), {"c": company_name, "gid": guest_id}).fetchall()
            
        if team:
            for t in team:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1], vertical_alignment="center")
                    c1.markdown(f"**{t.guest_name}** - {t.job_title or 'Thành viên'}")
                    c1.caption(f":material/mail: {t.email}")
                    c2.button("Xóa quyền", icon=":material/delete:", key=f"del_{t.email}", use_container_width=True)
        else:
            st.info("Chưa có đại diện nào khác trong doanh nghiệp của bạn tham gia hệ thống.")
            
        st.markdown("---")
        with st.expander("➕ Mời thêm nhân sự đại diện"):
            st.write(f"Gửi đường link sau cho nhân viên của bạn để họ liên kết vào tài khoản công ty **{company_name}**:")
            st.code(f"https://eventos.datcom.vn/invite?comp={guest_id}&code=AUTO_GEN_CODE")
            st.button("Tạo tài khoản phụ trực tiếp", icon=":material/person_add:")

# TAB 4: KYC
with tab_kyc:
    st.subheader("Xác minh Doanh nghiệp (Verification Badge)")
    st.write("Tải lên Giấy phép kinh doanh để nhận dấu tích xanh (✅), tăng độ uy tín với các đối tác cấp cao.")
    
    status = guest_record.get("kyc_status", "Unverified")
    is_ver = guest_record.get("is_verified", False)
    
    if is_ver or status == "Verified":
        st.success("Doanh nghiệp của bạn đã được xác minh KYC! Biểu tượng ✅ sẽ hiển thị cạnh tên công ty trên danh bạ đối tác.", icon=":material/verified:")
    elif status == "Pending":
        st.info("Hồ sơ đang chờ Ban tổ chức phê duyệt. Quá trình này có thể mất 1-2 ngày làm việc.", icon=":material/hourglass_empty:")
    else:
        with st.form("form_kyc", border=True):
            st.markdown("**Vui lòng cung cấp các tài liệu sau để xét duyệt:**")
            st.text_input("Mã số doanh nghiệp (Tax Code) *")
            st.file_uploader("Tải lên Giấy chứng nhận Đăng ký Kinh doanh (Bản Scan PDF/JPG) *")
            st.text_input("Thư ủy quyền đại diện (Nếu bạn không phải người đại diện pháp luật)")
            
            if st.form_submit_button("Gửi Yêu Cầu Xác Minh", type="primary", use_container_width=True):
                with get_db() as db:
                    db.execute(text("UPDATE Guests SET kyc_status = 'Pending' WHERE guest_id = :gid"), {"gid": guest_id})
                st.success("Đã gửi yêu cầu xác thực KYC thành công!")
                import time; time.sleep(1.5)
                st.rerun()