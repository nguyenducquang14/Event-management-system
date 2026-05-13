"""
pages/11_Ket_Noi_Tuong_Tac.py
Chức năng Tương tác & Kết nối dành cho Guest
"""
import streamlit as st
import time
from sqlalchemy import text
from app.config import get_db
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Kết Nối & Tương Tác", page_icon="🤝", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- CSS ÉP MÀU TRẮNG CHO KHUNG NHẬP LIỆU ---
st.markdown("""
<style>
    input, div[data-baseweb="input"], div[data-baseweb="input"] > div,
    textarea, div[data-baseweb="textarea"], div[data-baseweb="textarea"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

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
        /* Ẩn TẤT CẢ các menu quản trị, chỉ giữ lại 5 menu của Guest */
        [data-testid="stSidebarNav"] ul li { display: none !important; }
        [data-testid="stSidebarNav"] ul li:nth-last-child(2),
        [data-testid="stSidebarNav"] ul li:nth-last-child(3),
        [data-testid="stSidebarNav"] ul li:nth-last-child(4),
        [data-testid="stSidebarNav"] ul li:nth-last-child(5),
        [data-testid="stSidebarNav"] ul li:nth-last-child(6) { display: list-item !important; }
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
        guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        if not guest:
            db.execute(text("INSERT INTO Guests (guest_name, email) VALUES (:name, :email)"), {"name": name, "email": email})
            guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        return dict(guest._mapping)

guest_id = get_or_create_guest(user_email, user_info["name"])["guest_id"]

st.title(":material/forum: Kết Nối & Tương Tác")

# Lấy các sự kiện người dùng đã tham gia để chọn
with get_db() as db:
    my_events = db.execute(text("""
        SELECT e.event_id, e.event_name 
        FROM Registrations r
        JOIN Events e ON r.event_id = e.event_id
        WHERE r.guest_id = :gid AND e.status != 'Cancelled'
        ORDER BY e.start_time DESC
    """), {"gid": guest_id}).fetchall()

if not my_events:
    st.info("Bạn chưa tham gia sự kiện nào. Hãy đăng ký sự kiện để trải nghiệm tính năng kết nối!", icon=":material/info:")
    st.stop()

event_options = {ev.event_id: ev.event_name for ev in my_events}
selected_event_id = st.selectbox("Chọn sự kiện để tương tác:", options=list(event_options.keys()), format_func=lambda x: event_options[x])

st.markdown("---")

tab_agenda, tab_network, tab_match, tab_qr, tab_qa = st.tabs([
    "📅 Lịch trình Sự kiện", 
    "👥 Danh bạ Người tham dự",
    "✨ Gợi ý Kết nối",
    "📱 Quét Mã QR",
    "💬 Hỏi đáp (Q&A)"
])

# TAB 1: LỊCH TRÌNH
with tab_agenda:
    st.subheader("Lịch trình chi tiết")
    st.info("Tính năng này giúp bạn theo dõi các phiên (sessions) diễn ra trong sự kiện để không bỏ lỡ những nội dung quan trọng.")
    
    with st.container(border=True):
        st.markdown("**08:00 - 08:30** | Đón khách & Check-in :material/check_circle:")
        st.markdown("**08:30 - 09:00** | Phát biểu khai mạc")
        st.markdown("**09:00 - 10:30** | Phiên thảo luận chính (Keynote)")
        st.markdown("**10:30 - 10:45** | Tiệc trà (Tea break) :material/local_cafe:")
        st.markdown("**10:45 - 12:00** | Tọa đàm chuyên sâu (Panel Discussion)")
        st.button("Lưu lịch trình vào Google Calendar", icon=":material/event:")

# HÀM POP-UP GỬI LỜI MỜI KẾT NỐI
@st.dialog("Gửi lời mời Hẹn gặp (Networking)")
def meeting_dialog(guest_name, company):
    st.markdown(f"Gửi lời mời gặp mặt tới **{guest_name}** ({company or 'Cá nhân'})")
    c1, c2 = st.columns(2)
    time_slot = c1.selectbox("Khung giờ trống chung", ["09:00 - 09:30", "10:30 - 11:00", "14:00 - 14:30", "16:00 - 16:30"])
    location = c2.selectbox("Địa điểm (Hệ thống tự gán)", ["VIP Lounge - Bàn 01", "Meeting Room A", "Khu vực Networking chung", "Business Center"])
    
    msg = st.text_area("Nội dung trao đổi (Pitching)", value="Chào bạn, mình thấy doanh nghiệp của bạn cung cấp giải pháp rất phù hợp với nhu cầu của bên mình. Mong được trao đổi chi tiết hơn!")
    
    if st.button("Gửi yêu cầu đặt lịch", type="primary", use_container_width=True):
        with st.spinner("Đang gửi..."):
            time.sleep(1)
        st.success(f"Đã gửi lời mời họp tới {guest_name}! Hệ thống đã khóa {time_slot} tại {location}.")
        time.sleep(1.5)
        st.rerun()

# TAB 3: DANH BẠ ĐỐI TÁC & LỊCH HỌP
with tab_network:
    st.subheader("Danh bạ Người tham dự & Giao lưu")
    st.write("Chủ động tìm kiếm và kết nối với những người cùng tham gia sự kiện.")
    st.info("💡 **Bảo mật:** Liên hệ cá nhân sẽ được ẩn cho đến khi cả hai bên chấp nhận kết nối. Những người dùng đánh dấu ẩn hồ sơ sẽ không xuất hiện tại đây.")
    
    with get_db() as db:
        # Đảm bảo bảng Guests có cột is_public
        try:
            db.execute(text("ALTER TABLE Guests ADD COLUMN is_public BOOLEAN DEFAULT TRUE"))
        except Exception:
            pass
            
        try:
            other_guests = db.execute(text("""
                SELECT g.guest_id, g.guest_name, g.email, g.job_title, g.company, g.bio, g.linkedin_url, g.services_offered, g.buying_intent, g.is_verified, g.portfolio_url, g.video_url
                FROM Registrations r
                JOIN Guests g ON r.guest_id = g.guest_id
                WHERE r.event_id = :eid AND r.guest_id != :gid AND (g.is_public = TRUE OR g.is_public IS NULL)
                LIMIT 15
            """), {"eid": selected_event_id, "gid": guest_id}).fetchall()
        except Exception:
            other_guests = db.execute(text("""
                SELECT g.guest_id, g.guest_name, g.email, NULL as job_title, NULL as company, NULL as bio, NULL as linkedin_url, NULL as services_offered, NULL as buying_intent, FALSE as is_verified, NULL as portfolio_url, NULL as video_url
                FROM Registrations r
                JOIN Guests g ON r.guest_id = g.guest_id
                WHERE r.event_id = :eid AND r.guest_id != :gid AND (g.is_public = TRUE OR g.is_public IS NULL)
                LIMIT 15
            """), {"eid": selected_event_id, "gid": guest_id}).fetchall()
        
    if not other_guests:
        st.info("Hiện chưa có đối tác nào chia sẻ hồ sơ công khai.")
    else:
        for og in other_guests:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1], vertical_alignment="center")
                with col1:
                    verified_icon = " ✅" if getattr(og, "is_verified", False) else ""
                    st.markdown(f"**{og.guest_name}**{verified_icon}")
                    if og.job_title or og.company:
                        job_str = f"{og.job_title or 'Thành viên'} tại **{og.company or 'Chưa cập nhật'}**"
                        st.markdown(job_str)
                        
                    # Show Virtual Booth links if present
                    if getattr(og, "portfolio_url", None) or getattr(og, "video_url", None):
                        links = []
                        if getattr(og, "portfolio_url", None): links.append(f"[:material/description: Brochure]({og.portfolio_url})")
                        if getattr(og, "video_url", None): links.append(f"[:material/smart_display: Video]({og.video_url})")
                        st.markdown(" | ".join(links))
                    
                    # Che giấu một phần email để bảo mật thông tin
                    masked_email = f"{og.email[:3]}***@{og.email.split('@')[-1]}"
                    st.caption(f":material/mail: {masked_email}")
                with col2:
                    if st.button("Hẹn gặp", key=f"conn_{og.guest_id}", icon=":material/handshake:", use_container_width=True):
                        meeting_dialog(og.guest_name, og.company)

# TAB 2: SMART MATCHMAKING
with tab_match:
    st.subheader("Hệ thống Đề xuất Kết nối")
    st.write("Hệ thống tự động quét các thẻ 'Sở trường' và 'Mục tiêu' trong Hồ sơ cá nhân để tìm ra những người có cùng sự quan tâm với bạn.")
    
    my_prof = None
    with get_db() as db:
        try:
            my_prof = db.execute(text("SELECT services_offered, buying_intent FROM Guests WHERE guest_id = :gid"), {"gid": guest_id}).fetchone()
        except Exception:
            pass
            
    has_tags = my_prof and (my_prof.services_offered or my_prof.buying_intent)
    
    if not has_tags:
        st.warning("Bạn chưa cập nhật 'Nhu cầu Kết nối' (Buying Intent / Services Offered) trong phần Hồ Sơ Doanh Nghiệp. Vui lòng cập nhật để AI có thể phân tích và đề xuất!")
        st.button("👉 Cập nhật Hồ sơ ngay", on_click=lambda: st.switch_page("pages/10_Hồ_Sơ_Doanh_Nghiệp.py"))
    elif not other_guests:
        st.info("Chưa có đối tác nào đủ dữ liệu để hệ thống ghép cặp.")
    else:
        st.success("✨ Dựa trên hồ sơ của bạn, chúng tôi tìm thấy các đối tác tiềm năng cao nhất sau:")
        # Mô phỏng AI ghép cặp, đưa top 3 lên đầu
        for idx, og in enumerate(other_guests[:3]): 
            with st.container(border=True):
                c1, c2 = st.columns([3, 1], vertical_alignment="center")
                with c1:
                    verified_icon = " ✅" if getattr(og, "is_verified", False) else ""
                    st.markdown(f"🔥 **{og.company or 'Đối tác tiềm năng'}**{verified_icon} (Đại diện: {og.guest_name} - {og.job_title or 'Chuyên viên'})")
                    if og.services_offered:
                        st.markdown(f"✅ **Họ có thể cung cấp:** :green-background[{og.services_offered[:60]}...]")
                    if og.buying_intent:
                        st.markdown(f"💼 **Họ đang có nhu cầu:** :blue-background[{og.buying_intent[:60]}...]")
                        
                    if getattr(og, "portfolio_url", None) or getattr(og, "video_url", None):
                        links = []
                        if getattr(og, "portfolio_url", None): links.append(f"[:material/description: Brochure]({og.portfolio_url})")
                        if getattr(og, "video_url", None): links.append(f"[:material/smart_display: Video]({og.video_url})")
                        st.markdown(" | ".join(links))
                with c2:
                    match_score = 98 - (idx * 7) # AI mock score
                    st.markdown(f"<h3 style='text-align: center; color: #10b981;'>{match_score}% Match</h3>", unsafe_allow_html=True)
                    if st.button("Mời họp 1:1", key=f"match_{og.guest_id}", type="primary", use_container_width=True):
                        meeting_dialog(og.guest_name, og.company)

# TAB 4: LEADS SCANNER (QR)
with tab_qr:
    st.subheader("Trao đổi Namecard Điện tử (Lead Scanning)")
    st.write("Khi gặp gỡ đối tác trực tiếp tại Booth triển lãm hoặc Lounge, hãy sử dụng tính năng này để quét QR và lưu thông tin vào danh bạ (Lead Capture) thay vì danh thiếp giấy.")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            st.markdown("<h5 style='text-align: center;'>Mã QR của bạn</h5>", unsafe_allow_html=True)
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=B2BCONNECT_GID_{guest_id}"
            st.image(qr_url, use_container_width=True)
            st.caption(f"<div style='text-align: center'>B2B_ID: {guest_id}</div>", unsafe_allow_html=True)
            
    with c2:
        st.info("Mở ứng dụng Camera hoặc Scanner để quét mã của đối tác.")
        with get_db() as db:
            comp_row = db.execute(text("SELECT company, job_title FROM Guests WHERE guest_id = :gid"), {"gid": guest_id}).fetchone()
            
        st.markdown(f"**Người đại diện:** {st.session_state['user_info']['name']}")
        st.markdown(f"**Chức vụ:** {comp_row.job_title if comp_row and comp_row.job_title else '(Chưa cập nhật)'}")
        st.markdown(f"**Doanh nghiệp:** {comp_row.company if comp_row and comp_row.company else '(Chưa cập nhật)'}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("📥 Tải Namecard (vCard) về máy", icon=":material/download:")
        st.button("📷 Bật Camera để Quét QR đối tác", type="primary", icon=":material/qr_code_scanner:")

# TAB 3: HỎI ĐÁP
with tab_qa:
    st.subheader("Hỏi đáp Trực tiếp (Live Q&A)")
    st.write("Gửi câu hỏi lên màn hình LED của diễn giả (có thể gửi ẩn danh).")
    
    with st.container(border=True):
        question = st.text_input("Nhập câu hỏi của bạn:")
        is_anonymous = st.checkbox("Gửi ẩn danh")
        
        if st.button("Gửi câu hỏi", icon=":material/send:", type="primary"):
            if not question:
                st.error("Vui lòng nhập câu hỏi!")
            else:
                with st.spinner("Đang gửi lên hệ thống..."):
                    time.sleep(1)
                st.success("Câu hỏi của bạn đã được chuyển tới Ban tổ chức và Diễn giả!")
    
    st.markdown("#### Các câu hỏi đang nổi bật")
    with st.container(border=True):
        st.markdown("**:material/person: Khán giả ẩn danh**")
        st.markdown("Ban tổ chức có thể chia sẻ tài liệu thuyết trình sau sự kiện không ạ?")
        st.button("Upvote (12)", icon=":material/thumb_up:", key="upv1")
        
    with st.container(border=True):
        st.markdown("**:material/person: Nguyễn Trần V...**")
        st.markdown("Cho mình hỏi quy trình cụ thể để áp dụng giải pháp này vào thực tế doanh nghiệp?")
        st.button("Upvote (5)", icon=":material/thumb_up:", key="upv2")