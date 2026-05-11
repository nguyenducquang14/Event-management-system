"""
pages/11_Danh_Gia_Tai_Lieu.py
Đánh giá sự kiện và tải tài liệu cho Guest
"""
import streamlit as st
import time
import json
from sqlalchemy import text
from app.config import get_db
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Đánh Giá & Tài Liệu", page_icon="⭐", layout="wide")

GOLDEN_UI_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="st-"], .stMarkdownContainer, p, h1, h2, h3, h4, h5, h6, span, div, button, input, label, li { font-family: 'Inter', sans-serif !important; }
    .block-container { padding: 2.5rem 3rem 4rem 3rem !important; max-width: 1200px !important; }
    .stApp { background-color: #F8FAFC !important; }
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; }
    p, span, label, li, .stMarkdownContainer { color: #334155 !important; }
    button[kind="primary"] { background-color: #1E3A8A !important; color: #FFFFFF !important; border: none !important; border-radius: 8px !important; padding: 0.5rem 1.5rem !important; font-weight: 600 !important; transition: all 0.2s ease-in-out !important; }
    button[kind="primary"]:hover { background-color: #1E40AF !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important; }
    button[kind="primary"] p, button[kind="primary"] div { color: #FFFFFF !important; }
    button[kind="secondary"] { background-color: #FFFFFF !important; color: #0F172A !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; padding: 0.5rem 1.5rem !important; font-weight: 500 !important; transition: all 0.2s ease-in-out !important; }
    button[kind="secondary"]:hover { background-color: #F1F5F9 !important; border-color: #94A3B8 !important; transform: translateY(-2px); }
    button[kind="secondary"] p, button[kind="secondary"] div { color: #0F172A !important; }
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] > div, div[data-testid="metric-container"], .stAlert { background-color: #FFFFFF !important; border-radius: 12px !important; border: 1px solid #E2E8F0 !important; padding: 1.25rem !important; transition: box-shadow 0.3s ease-in-out, transform 0.3s ease !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important; }
    div[data-testid="stForm"]:hover, div[data-testid="stVerticalBlockBorderWrapper"] > div:hover, div[data-testid="metric-container"]:hover { box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important; transform: translateY(-2px) !important; }
    input, textarea, div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border-radius: 8px !important; border: 1px solid #CBD5E1 !important; color: #0F172A !important; padding: 0.25rem 0.5rem !important; }
    input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within { border-color: #1E3A8A !important; box-shadow: 0 0 0 1px #1E3A8A !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0 !important; }
    div[data-testid="metric-container"] label { color: #64748B !important; font-weight: 500 !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #1E3A8A !important; font-weight: 700 !important; font-size: 2rem !important; }
</style>
"""
st.markdown(CUSTOM_CSS + GOLDEN_UI_CSS, unsafe_allow_html=True)

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
        guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        if not guest:
            db.execute(text("INSERT INTO Guests (guest_name, email) VALUES (:name, :email)"), {"name": name, "email": email})
            guest = db.execute(text("SELECT * FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        return dict(guest._mapping)

guest_id = get_or_create_guest(user_email, user_info["name"])["guest_id"]

st.title(":material/reviews: Đánh Giá & Tài Liệu Sự Kiện")

# Lấy các sự kiện người dùng đã tham gia hoặc đã kết thúc
with get_db() as db:
    past_events = db.execute(text("""
        SELECT e.event_id, e.event_name, r.attendance_status, DATE_FORMAT(e.end_time, '%d/%m/%Y') as end_date,
               IFNULL(e.category, 'Khác') as category
        FROM Registrations r
        JOIN Events e ON r.event_id = e.event_id
        WHERE r.guest_id = :gid AND (e.end_time < NOW() OR r.attendance_status = 'Attended')
        ORDER BY e.end_time DESC
    """), {"gid": guest_id}).fetchall()

if not past_events:
    st.info("Bạn chưa có sự kiện nào đã tham gia hoặc đã kết thúc để đánh giá.", icon=":material/info:")
    st.stop()

event_options = {ev.event_id: ev.event_name for ev in past_events}
selected_event_id = st.selectbox("Chọn sự kiện để tương tác:", options=list(event_options.keys()), format_func=lambda x: event_options[x])
selected_event = next(ev for ev in past_events if ev.event_id == selected_event_id)

st.markdown("---")

tab_resource, tab_review = st.tabs([
    "📥 Tài liệu & Chứng nhận",
    "📝 Phản hồi Sự kiện"
])

# --- CÁC HÀM RENDER PHIẾU KHẢO SÁT CHUYÊN BIỆT ---

def _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps_score, comments, details_dict):
    """Hàm helper để tổng hợp và gửi dữ liệu phản hồi vào DB."""
    full_comment = f"Liked: {comments.get('liked', '')}\nImprove: {comments.get('improve', '')}\nFuture: {comments.get('future', '')}"
    details_json_str = json.dumps(details_dict, ensure_ascii=False, indent=2)

    with get_db() as db:
        db.execute(text("""
            INSERT INTO Feedbacks (event_id, guest_id, rating, rating_content, rating_logistics, nps_score, comment, 
                                   comment_liked, comment_improve, future_topics, details_json) 
            VALUES (:eid, :gid, :rating, :rating_content, :rating_logistics, :nps_score, :comment, 
                    :comment_liked, :comment_improve, :future_topics, :details_json)
        """), {
            "eid": event_id, "gid": guest_id, "rating": rating_val,
            "rating_content": rating_content, "rating_logistics": rating_logistics,
            "nps_score": nps_score,
            "comment": full_comment,
            "comment_liked": comments.get('liked', ''), 
            "comment_improve": comments.get('improve', ''), 
            "future_topics": comments.get('future', ''),
            "details_json": details_json_str
        })
    st.success("Đã ghi nhận đánh giá của bạn! Xin chân thành cảm ơn.")
    time.sleep(1.5)
    st.rerun()

def _calc_score(answers):
    score = 0
    for a in answers:
        ans = str(a).lower()
        if any(w in ans for w in ["kém", "tệ", "chậm", "không", "dưới", "cũ", "nông", "nhàm chán", "rời rạc", "lỗi", "suông", "sơ sài", "mơ hồ"]): score += 1
        elif any(w in ans for w in ["bình thường", "tạm", "đạt", "hơi", "an toàn", "cơ bản", "chung chung"]): score += 3
        elif any(w in ans for w in ["tốt", "nhanh", "chuyên nghiệp", "chu đáo", "sạch", "hay", "sâu", "mới", "phù hợp", "ý nghĩa", "rõ", "tiện nghi", "khoa học", "thiết thực"]): score += 4
        else: score += 5
    return int(round(score / len(answers))) if answers else 5

def _render_part_1(prefix):
    st.markdown("<h5>Phần 1: Đánh giá Trải nghiệm Tổng thể</h5>", unsafe_allow_html=True)
    rating_text = st.select_slider(
        "Nhìn chung, bạn đánh giá sự kiện này ở mức độ nào?", 
        options=["Rất không hài lòng", "Không hài lòng", "Bình thường", "Hài lòng", "Cực kỳ hài lòng"], 
        value="Hài lòng",
        key=f"{prefix}_rating"
    )
    return {"Rất không hài lòng": 1, "Không hài lòng": 2, "Bình thường": 3, "Hài lòng": 4, "Cực kỳ hài lòng": 5}.get(rating_text, 4)

def _render_part_3(prefix):
    st.markdown("---")
    st.markdown("<h5>Phần 3: Đánh giá Công tác Tổ chức & Hậu cần</h5>", unsafe_allow_html=True)
    l1 = st.radio("1. Quy trình Check-in và hỗ trợ từ Ban tổ chức:", ["Chậm chạp, lộn xộn", "Đạt yêu cầu", "Nhanh chóng, chuyên nghiệp"], horizontal=True, index=2, key=f"{prefix}_l1")
    l2 = st.radio("2. Chất lượng Cơ sở vật chất (Không gian, chỗ ngồi, vệ sinh):", ["Dưới mức trung bình", "Chấp nhận được", "Khang trang, tiện nghi"], horizontal=True, index=2, key=f"{prefix}_l2")
    l3 = st.radio("3. Các tiện ích đi kèm (Teabreak, wifi, bãi xe...):", ["Không tốt / Không có", "Tạm ổn", "Rất chu đáo"], horizontal=True, index=2, key=f"{prefix}_l3")
    return l1, l2, l3

def _render_part_4(prefix):
    st.markdown("---")
    st.markdown("<h5>Phần 4: Đo lường Sự trung thành (NPS) & Đóng góp ý kiến</h5>", unsafe_allow_html=True)
    st.write("Dựa trên trải nghiệm tại sự kiện, khả năng bạn sẽ giới thiệu các chương trình của chúng tôi cho bạn bè hoặc đối tác là bao nhiêu?")
    nps_score = st.slider("Thang điểm (0 = Chắc chắn không, 10 = Chắc chắn có)", min_value=0, max_value=10, value=9, key=f"{prefix}_nps")
    
    col1, col2 = st.columns(2)
    comment_liked = col1.text_area("Điểm sáng lớn nhất của sự kiện này là gì?", placeholder="Ví dụ: Chuyên môn diễn giả, networking...", height=100, key=f"{prefix}_liked")
    comment_improve = col2.text_area("Chúng tôi cần cải thiện điều gì ở sự kiện sau?", placeholder="Ví dụ: Thời lượng quá dài, âm thanh lỗi...", height=100, key=f"{prefix}_improve")
    
    future_topics = st.text_input("Gợi ý chủ đề, khách mời hoặc hoạt động cho tương lai:", placeholder="Nhập đề xuất của bạn...", key=f"{prefix}_future")
    return nps_score, comment_liked, comment_improve, future_topics

def render_tech_survey(event_id, guest_id):
    with st.form("tech_review_form", border=True):
        st.info("💡 **Khảo sát chuyên sâu - Lĩnh vực CÔNG NGHỆ (IT & Tech)**")
        rating_val = _render_part_1("tech")
        
        st.markdown("---")
        st.markdown("<h5>Phần 2: Đánh giá Nội dung & Chuyên môn Kỹ thuật</h5>", unsafe_allow_html=True)
        q1 = st.radio("1. Mức độ cập nhật và tính đột phá của công nghệ/giải pháp được giới thiệu:", ["Lỗi thời, đã phổ biến", "Có cập nhật nhưng chưa sâu", "Bám sát xu hướng hiện tại", "Mang tính tiên phong, đột phá"], horizontal=True, index=2)
        q2 = st.radio("2. Trình độ chuyên môn và khả năng truyền đạt của Diễn giả/Kỹ sư:", ["Dưới kỳ vọng", "Bình thường", "Tốt, kiến thức vững", "Chuyên gia xuất sắc"], horizontal=True, index=2)
        q3 = st.radio("3. Đánh giá chất lượng của các phiên Demo / Code-live / Hands-on (nếu có):", ["Không có / Bị lỗi kỹ thuật", "Tạm ổn nhưng khó theo dõi", "Trực quan, dễ hiểu", "Cực kỳ ấn tượng và thực tiễn"], horizontal=True, index=2)
        q4 = st.radio("4. Mức độ hữu ích của tài liệu kỹ thuật, slide hoặc mã nguồn được chia sẻ:", ["Sơ sài, không dùng được", "Cơ bản, thiếu chi tiết", "Đầy đủ, có thể tham khảo", "Cực kỳ chi tiết và giá trị"], horizontal=True, index=2)
        
        l1, l2, l3 = _render_part_3("tech")
        nps, liked, improve, future = _render_part_4("tech")
        
        if st.form_submit_button("Gửi Khảo Sát Kỹ Thuật", type="primary", use_container_width=True):
            rating_content = _calc_score([q1, q2, q3, q4])
            rating_logistics = _calc_score([l1, l2, l3])
            details = {"Tính cập nhật công nghệ": q1, "Chuyên môn diễn giả": q2, "Chất lượng Demo": q3, "Tài liệu kỹ thuật": q4, "Check-in": l1, "Cơ sở vật chất": l2, "F&B": l3}
            comments = {"liked": liked, "improve": improve, "future": future}
            _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps, comments, details)

def render_education_survey(event_id, guest_id):
    with st.form("edu_review_form", border=True):
        st.info("💡 **Khảo sát chuyên sâu - Lĩnh vực GIÁO DỤC & ĐÀO TẠO**")
        rating_val = _render_part_1("edu")

        st.markdown("---")
        st.markdown("<h5>Phần 2: Đánh giá Phương pháp Giảng dạy & Học thuật</h5>", unsafe_allow_html=True)
        q1 = st.radio("1. Mức độ bám sát mục tiêu học tập đề ra ban đầu:", ["Hoàn toàn đi chệch hướng", "Chưa đáp ứng đủ kỳ vọng", "Đáp ứng tốt các mục tiêu", "Vượt xa kỳ vọng"], horizontal=True, index=2)
        q2 = st.radio("2. Kỹ năng sư phạm và tính tương tác của Giảng viên/Diễn giả:", ["Thụ động, một chiều", "Có tương tác nhưng ít", "Phương pháp lôi cuốn, sinh động", "Truyền cảm hứng mạnh mẽ"], horizontal=True, index=2)
        q3 = st.radio("3. Mức độ ứng dụng thực tiễn của kiến thức được cung cấp:", ["Thuần lý thuyết suông", "Khó áp dụng thực tế", "Có thể áp dụng ngay", "Rất thực tiễn và mang lại giá trị cao"], horizontal=True, index=2)
        q4 = st.radio("4. Đánh giá chất lượng của giáo trình, bài giảng và bài tập thực hành:", ["Thiếu thốn, không rõ ràng", "Đủ dùng, cần cải thiện hình thức", "Biên soạn chỉn chu, khoa học", "Tuyệt vời, có tính hệ thống cao"], horizontal=True, index=2)

        l1, l2, l3 = _render_part_3("edu")
        nps, liked, improve, future = _render_part_4("edu")

        if st.form_submit_button("Gửi Khảo Sát Đào Tạo", type="primary", use_container_width=True):
            rating_content = _calc_score([q1, q2, q3, q4])
            rating_logistics = _calc_score([l1, l2, l3])
            details = {"Bám sát mục tiêu": q1, "Kỹ năng sư phạm": q2, "Ứng dụng thực tiễn": q3, "Chất lượng giáo trình": q4, "Check-in": l1, "Cơ sở vật chất": l2, "F&B": l3}
            comments = {"liked": liked, "improve": improve, "future": future}
            _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps, comments, details)

def render_entertainment_survey(event_id, guest_id):
    with st.form("ent_review_form", border=True):
        st.info("💡 **Khảo sát chuyên sâu - Lĩnh vực GIẢI TRÍ & SỰ KIỆN NGHỆ THUẬT QUẦN CHÚNG**")
        rating_val = _render_part_1("ent")

        st.markdown("---")
        st.markdown("<h5>Phần 2: Đánh giá Trải nghiệm Cảm xúc & Kỹ thuật Sân khấu</h5>", unsafe_allow_html=True)
        q1 = st.radio("1. Chất lượng của dàn Âm thanh, Ánh sáng và Hiệu ứng sân khấu (VFX):", ["Nhiều lỗi, ảnh hưởng trải nghiệm", "Tạm được, chưa ấn tượng", "Rất tốt, đã mắt đã tai", "Đỉnh cao, đẳng cấp quốc tế"], horizontal=True, index=2)
        q2 = st.radio("2. Kịch bản chương trình và nhịp độ các tiết mục biểu diễn:", ["Rời rạc, gây buồn ngủ", "Dàn trải, có một vài điểm sáng", "Mạch lạc, hấp dẫn", "Bùng nổ cảm xúc từ đầu đến cuối"], horizontal=True, index=2)
        q3 = st.radio("3. Sự cống hiến và mức độ tương tác của nghệ sĩ/khách mời:", ["Thiếu năng lượng, hời hợt", "Biểu diễn tròn vai", "Nhiệt huyết, khuấy động đám đông", "Tuyệt vời, kết nối sâu sắc với khán giả"], horizontal=True, index=2)
        q4 = st.radio("4. Đánh giá về công tác an ninh, phân luồng khán giả và lối thoát hiểm:", ["Lộn xộn, chen lấn nguy hiểm", "Có bảo vệ nhưng chưa chặt chẽ", "Phân luồng tốt, an toàn", "Quy trình kiểm soát an ninh cực kỳ chuẩn mực"], horizontal=True, index=2)

        l1, l2, l3 = _render_part_3("ent")
        nps, liked, improve, future = _render_part_4("ent")

        if st.form_submit_button("Gửi Đánh Giá Sự Kiện", type="primary", use_container_width=True):
            rating_content = _calc_score([q1, q2, q3, q4])
            rating_logistics = _calc_score([l1, l2, l3])
            details = {"Âm thanh & Hiệu ứng": q1, "Kịch bản tiết mục": q2, "Năng lượng nghệ sĩ": q3, "An ninh & Phân luồng": q4, "Check-in": l1, "Cơ sở vật chất": l2, "F&B": l3}
            comments = {"liked": liked, "improve": improve, "future": future}
            _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps, comments, details)

def render_art_survey(event_id, guest_id):
    with st.form("art_review_form", border=True):
        st.info("💡 **Khảo sát chuyên sâu - Lĩnh vực NGHỆ THUẬT THỊ GIÁC & TRIỂN LÃM**")
        rating_val = _render_part_1("art")

        st.markdown("---")
        st.markdown("<h5>Phần 2: Đánh giá Giá trị Thẩm mỹ & Ý niệm Nghệ thuật</h5>", unsafe_allow_html=True)
        q1 = st.radio("1. Bố cục không gian trưng bày và cách thức giám tuyển (Curation):", ["Thiếu logic, rối mắt", "Bình thường, an toàn", "Sắp đặt tinh tế, có sự dẫn dắt", "Không gian nghệ thuật đẳng cấp, đột phá"], horizontal=True, index=2)
        q2 = st.radio("2. Chiều sâu thông điệp và chất lượng của các tác phẩm:", ["Mơ hồ, khó cảm nhận", "Đẹp nhưng chưa sâu sắc", "Ý niệm rõ ràng, chạm đến cảm xúc", "Gây ám ảnh, khơi gợi nhiều suy ngẫm"], horizontal=True, index=2)
        q3 = st.radio("3. Trải nghiệm ánh sáng trưng bày và âm thanh không gian (nếu có):", ["Ánh sáng sai lệch, làm hỏng tác phẩm", "Chưa tôn lên được chi tiết tác phẩm", "Hòa quyện, tạo mood tốt", "Hoàn hảo, làm thăng hoa nghệ thuật"], horizontal=True, index=2)
        q4 = st.radio("4. Chất lượng của ấn phẩm giới thiệu, sách ảnh hoặc thông tin đính kèm tác phẩm:", ["Sơ sài, có lỗi in ấn", "Thiết kế cơ bản, đủ thông tin", "In ấn đẹp, nội dung biên tập kỹ", "Một tác phẩm nghệ thuật thu nhỏ đáng sưu tầm"], horizontal=True, index=2)

        l1, l2, l3 = _render_part_3("art")
        nps, liked, improve, future = _render_part_4("art")

        if st.form_submit_button("Gửi Cảm Nhận Triển Lãm", type="primary", use_container_width=True):
            rating_content = _calc_score([q1, q2, q3, q4])
            rating_logistics = _calc_score([l1, l2, l3])
            details = {"Bố cục không gian": q1, "Chiều sâu thông điệp": q2, "Ánh sáng trưng bày": q3, "Ấn phẩm nghệ thuật": q4, "Check-in": l1, "Cơ sở vật chất": l2, "F&B": l3}
            comments = {"liked": liked, "improve": improve, "future": future}
            _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps, comments, details)

def render_default_survey(event_id, guest_id):
    with st.form("default_review_form", border=True):
        st.info("💡 **Khảo sát Trải nghiệm Sự kiện Tổng hợp**")
        rating_val = _render_part_1("def")

        st.markdown("---")
        st.markdown("<h5>Phần 2: Đánh giá Nội dung Chương trình</h5>", unsafe_allow_html=True)
        q1 = st.radio("1. Đánh giá chất lượng và mức độ hữu ích của nội dung chương trình:", ["Không đạt kỳ vọng, lãng phí thời gian", "Nội dung chung chung", "Hữu ích, cung cấp thông tin mới", "Cực kỳ thiết thực và giá trị"], horizontal=True, index=2)
        q2 = st.radio("2. Kỹ năng thuyết trình và phong thái của diễn giả/người điều phối:", ["Kém tương tác, nhàm chán", "Ổn định nhưng chưa nổi bật", "Thu hút, làm chủ sân khấu tốt", "Vô cùng xuất sắc, phong thái chuyên nghiệp"], horizontal=True, index=2)
        q3 = st.radio("3. Đánh giá việc phân bổ thời lượng giữa các phần của chương trình:", ["Quá dài/ngắn, không hợp lý", "Tạm được, có phần bị gấp gáp", "Kiểm soát thời gian tốt", "Hoàn hảo, tiến độ nhịp nhàng"], horizontal=True, index=2)
        q4 = st.radio("4. Đánh giá cơ hội kết nối (Networking) và giao lưu tại sự kiện:", ["Hoàn toàn không có cơ hội", "Khá hạn chế", "Có không gian để giao lưu", "Tạo được mạng lưới kết nối vô cùng chất lượng"], horizontal=True, index=2)

        l1, l2, l3 = _render_part_3("def")
        nps, liked, improve, future = _render_part_4("def")

        if st.form_submit_button("Gửi Đánh Giá Sự Kiện", type="primary", use_container_width=True):
            rating_content = _calc_score([q1, q2, q3, q4])
            rating_logistics = _calc_score([l1, l2, l3])
            details = {"Chất lượng nội dung": q1, "Kỹ năng thuyết trình": q2, "Phân bổ thời gian": q3, "Cơ hội Networking": q4, "Check-in": l1, "Cơ sở vật chất": l2, "F&B": l3}
            comments = {"liked": liked, "improve": improve, "future": future}
            _submit_feedback_v2(event_id, guest_id, rating_val, rating_content, rating_logistics, nps, comments, details)

# TAB 1: REVIEW
with tab_review:
    with get_db() as db:
        # Tự động tạo bảng Feedbacks nếu chưa có để lưu trữ Đánh giá
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS Feedbacks (
                    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                    event_id INT NOT NULL,
                    guest_id INT NOT NULL,
                    rating INT NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES Events(event_id) ON DELETE CASCADE,
                    FOREIGN KEY (guest_id) REFERENCES Guests(guest_id) ON DELETE CASCADE
                )
            """))
        except Exception:
            pass
            
        # Mở rộng bảng Feedbacks để chứa các câu hỏi khảo sát chi tiết (chạy 1 lần)
        try:
            db.execute(text("ALTER TABLE Feedbacks ADD COLUMN rating_content INT, ADD COLUMN rating_logistics INT, ADD COLUMN nps_score INT, ADD COLUMN comment_liked TEXT, ADD COLUMN comment_improve TEXT, ADD COLUMN future_topics TEXT;"))
            db.execute(text("ALTER TABLE Feedbacks ADD COLUMN nps_score INT, ADD COLUMN comment_liked TEXT, ADD COLUMN comment_improve TEXT, ADD COLUMN future_topics TEXT;"))
        except Exception:
            pass

        # Thêm cột JSON để lưu các câu trả lời chi tiết, linh hoạt
        try:
            db.execute(text("ALTER TABLE Feedbacks ADD COLUMN details_json JSON;"))
        except Exception:
            pass
            
        # Kiểm tra xem người dùng đã đánh giá chưa
        existing_feedback = db.execute(text("SELECT * FROM Feedbacks WHERE event_id = :eid AND guest_id = :gid"), 
                                       {"eid": selected_event_id, "gid": guest_id}).fetchone()

    if existing_feedback:
        st.success("Cảm ơn bạn đã gửi đánh giá cho sự kiện này!", icon=":material/check_circle:")
        with st.container(border=True):
            st.markdown("#### Phản hồi của bạn")
            has_detailed_feedback = 'nps_score' in existing_feedback._fields
            
            st.markdown("#### Nội dung phản hồi của bạn")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Đánh giá chung:** {'⭐' * existing_feedback.rating}")
            
            if has_detailed_feedback and existing_feedback.nps_score is not None:
                with c2:
                    st.markdown(f"**Mức độ giới thiệu (NPS):** `{existing_feedback.nps_score}/10`")
                
                st.markdown("---")
                st.markdown("**Nội dung góp ý chi tiết:**")
                st.markdown(f"> **Điều bạn thích nhất:** *{existing_feedback.comment_liked or '(chưa điền)'}*")
                st.markdown(f"> **Điều cần cải thiện:** *{existing_feedback.comment_improve or '(chưa điền)'}*")
                st.markdown(f"> **Gợi ý cho tương lai:** *{existing_feedback.future_topics or '(chưa điền)'}*")
            else:
                st.markdown(f"**Nội dung phản hồi:** {existing_feedback.comment or 'Không có bình luận'}")
            
            st.markdown("---")
            
            # Hiển thị các câu trả lời chi tiết từ JSON
            if 'details_json' in existing_feedback._fields and existing_feedback.details_json:
                st.markdown("**Nội dung khảo sát chi tiết:**")
                try:
                    details = json.loads(existing_feedback.details_json)
                    for question, answer in details.items():
                        st.markdown(f"- **{question}:** *{answer}*")
                except (json.JSONDecodeError, TypeError):
                    st.write(existing_feedback.details_json) # In ra nếu không phải JSON

            # Hiển thị các bình luận góp ý
            st.markdown("**Nội dung góp ý thêm:**")
            st.markdown(f"> **Điều bạn thích nhất:** *{existing_feedback.comment_liked or '(không có)'}*")
            st.markdown(f"> **Điều cần cải thiện:** *{existing_feedback.comment_improve or '(không có)'}*")
            st.markdown(f"> **Gợi ý cho tương lai:** *{existing_feedback.future_topics or '(không có)'}*")
    else:
        category = selected_event.category
        st.subheader(f"📝 Phiếu khảo sát trải nghiệm: {category}")
        st.write("Góp ý của bạn là nguồn thông tin quý giá giúp Ban tổ chức cải thiện chất lượng trong các sự kiện tiếp theo. Xin vui lòng dành vài phút để hoàn thành phiếu khảo sát dưới đây.")
        
        survey_functions = {
            "Công nghệ": render_tech_survey,
            "Giáo dục": render_education_survey,
            "Giải trí": render_entertainment_survey,
            "Nghệ thuật": render_art_survey,
            "Khác": render_default_survey
        }
        
        render_function = survey_functions.get(category, render_default_survey)
        render_function(selected_event_id, guest_id)

# TAB 2: RESOURCES
with tab_resource:
    st.subheader("Kho Tài liệu & Chứng nhận")
    st.write("Truy cập các tài liệu từ sự kiện. Chỉ dành cho người tham gia hợp lệ.")
    
    has_valid_ticket = selected_event.attendance_status in ['Registered', 'Attended', 'Refund Requested']
    if not has_valid_ticket:
        st.warning("Bạn chưa có vé hợp lệ sự kiện này. Không thể truy cập tài liệu.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.markdown("### :material/picture_as_pdf: Slide Thuyết trình")
                st.caption("Định dạng: PDF | Dung lượng: 4.2 MB")
                st.download_button("Tải Slide", data=b"Dummy PDF data", file_name=f"Slide_{selected_event_id}.pdf", mime="application/pdf", icon=":material/download:", use_container_width=True)
                
        with col2:
            with st.container(border=True):
                st.markdown("### :material/photo_library: Thư viện Ảnh")
                st.caption("Định dạng: ZIP | Hình ảnh sự kiện")
                st.download_button("Tải Hình ảnh", data=b"Dummy Image data", file_name=f"Photos_{selected_event_id}.zip", mime="application/zip", icon=":material/download:", use_container_width=True)

        with col3:
            with st.container(border=True):
                st.markdown("### :material/workspace_premium: Chứng nhận")
                if selected_event.attendance_status == 'Attended':
                    st.success("Đủ điều kiện nhận chứng nhận!")
                    st.caption("Định dạng: PDF | Có kèm con dấu điện tử")
                    st.download_button("Tải Chứng nhận", data=b"Dummy Certificate", file_name=f"Certificate_{st.session_state['user_info']['name'].replace(' ', '_')}.pdf", mime="application/pdf", icon=":material/download:", use_container_width=True)
                else:
                    st.warning("Yêu cầu: Đã Check-in (Attended)")
                    st.button("Tải Chứng nhận", disabled=True, icon=":material/lock:", use_container_width=True)

# TAB ANALYTICS: PHÂN TÍCH TƯƠNG TÁC
with tab_analytics:
    st.subheader("Phân tích Tương tác (Engagement Analytics)")
    st.write("Đo lường hiệu quả (ROI) từ việc tham gia sự kiện thông qua các chỉ số tương tác với Gian hàng ảo và Lịch họp.")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lượt xem Gian hàng", "342", "+12% so với hôm qua")
    c2.metric("Lượt tải Brochure", "85", "25% conversion rate")
    c3.metric("Lịch họp đã nhận", "18", "Từ 12 công ty")
    c4.metric("Tỷ lệ chấp nhận họp", "72%", "+5% trung bình ngành")
    
    st.markdown("---")
    st.markdown("**Chi tiết phễu tương tác (Funnel):**")
    import pandas as pd
    funnel_data = pd.DataFrame({
        "Giai đoạn": ["Ghé thăm Profile", "Xem Video/Brochure", "Gửi yêu cầu họp", "Họp thành công (Lead)"],
        "Số lượng": [342, 150, 45, 12]
    })
    st.bar_chart(funnel_data.set_index("Giai đoạn"))

# TAB 3: TÍCH HỢP CRM
with tab_crm:
    st.subheader("Xuất dữ liệu Leads & Tích hợp CRM (Lead Retrieval)")
    st.write("Quản lý danh sách đối tác đã thu thập qua việc quét mã QR, họp 1:1, hoặc kết nối thành công trên nền tảng.")
    
    import pandas as pd
    mock_leads = pd.DataFrame([
        {"Tên Đối Tác": "Nguyễn Văn A", "Chức Vụ": "CEO", "Công Ty": "TechCorp VN", "Email": "a.nguyen@techcorp.vn", "Nguồn": "Quét QR Booth"},
        {"Tên Đối Tác": "Trần Thị B", "Chức Vụ": "CMO", "Công Ty": "Marketing Pro", "Email": "b.tran@marketingpro.com", "Nguồn": "Họp 1:1"},
        {"Tên Đối Tác": "Lê Văn C", "Chức Vụ": "CTO", "Công Ty": "Innovate Ltd", "Email": "c.le@innovate.ltd", "Nguồn": "Chủ động Kết nối"}
    ])
    
    st.markdown("#### :material/recent_patient: Danh sách Leads đã thu thập (3)")
    st.dataframe(mock_leads, use_container_width=True, hide_index=True)
    
    csv_leads = mock_leads.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Xuất danh sách Leads (CSV)", data=csv_leads, file_name=f"Leads_{selected_event_id}.csv", mime="text/csv", type="secondary")
    
    st.markdown("---")
    st.markdown("#### :material/webhook: Tự động đẩy Leads về hệ thống CRM")
    
    with st.container(border=True):
        st.markdown("#### :material/webhook: Cấu hình Webhook / API")
        c1, c2 = st.columns(2)
        c1.selectbox("Chọn nền tảng CRM", ["Salesforce", "HubSpot", "Zoho CRM", "Odoo ERP", "Custom Webhook"])
        c2.text_input("API Key / Webhook URL", type="password", placeholder="https://hooks.salesforce.com/services/...")
        
        st.markdown("**Ánh xạ trường dữ liệu (Field Mapping):**")
        c3, c4, c5 = st.columns(3)
        c3.text_input("Tên đối tác", value="Contact_Name", disabled=True)
        c4.text_input("Chức danh", value="Job_Title", disabled=True)
        c5.text_input("Công ty", value="Company_Name", disabled=True)
        
        if st.button("Kết nối & Đồng bộ ngay", type="primary", icon=":material/sync:", use_container_width=True):
            with st.spinner("Đang xác thực API Key và đẩy dữ liệu Leads..."):
                time.sleep(2)
            st.success(f"Đồng bộ thành công {len(mock_leads)} Contacts mới vào hệ thống CRM của bạn!")