"""
pages/6_Ve_Cua_Toi.py
Trang hiển thị và quản lý vé của khách tham dự
"""
import streamlit as st
import time
from sqlalchemy import text
from app.config import get_db
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Vé Của Tôi", page_icon="🎟️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- CSS ÉP MÀU TRẮNG CHO KHUNG NHẬP LIỆU (TEXTAREA) ---
st.markdown("""
<style>
    /* Đặt nền trắng và chữ đen cho khung nhập lý do hoàn tiền */
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

# --- HÀM POP-UP CHUYỂN NHƯỢNG VÉ ---
@st.dialog("Ủy quyền tham dự (Chuyển nhượng)")
def transfer_ticket_dialog(registration_id, event_name):
    st.markdown(f"**Sự kiện:** {event_name}")
    st.info("Nhập email của người nhận vé để ủy quyền tham dự cho toàn bộ số lượng vé này. Hệ thống sẽ tạo hồ sơ tự động nếu chưa có.")
    
    new_email = st.text_input("Email người nhận *")
    new_name = st.text_input("Họ và Tên người nhận *")
    
    if st.button("Xác nhận ủy quyền", type="primary", use_container_width=True):
        if not new_email or not new_name:
            st.error("Vui lòng nhập đầy đủ thông tin!")
        elif new_email == st.session_state["user_info"]["email"]:
            st.error("Không thể tự chuyển nhượng cho chính mình!")
        else:
            with st.spinner("Đang xử lý..."):
                with get_db() as db:
                    # Lấy hoặc tạo guest mới
                    guest = db.execute(text("SELECT guest_id FROM Guests WHERE email = :email"), {"email": new_email}).fetchone()
                    if not guest:
                        db.execute(text("INSERT INTO Guests (guest_name, email) VALUES (:name, :email)"), {"name": new_name, "email": new_email})
                        guest = db.execute(text("SELECT guest_id FROM Guests WHERE email = :email"), {"email": new_email}).fetchone()
                    new_guest_id = guest.guest_id
                    
                    # Kiểm tra xem người nhận đã có vé sự kiện này chưa
                    event_id_row = db.execute(text("SELECT event_id FROM Registrations WHERE registration_id = :rid"), {"rid": registration_id}).fetchone()
                    if event_id_row:
                        existing_reg = db.execute(text("SELECT registration_id FROM Registrations WHERE event_id = :eid AND guest_id = :gid"), {"eid": event_id_row.event_id, "gid": new_guest_id}).fetchone()
                        if existing_reg:
                            st.error("Người đại diện mới đã có đăng ký tham gia sự kiện này rồi!")
                            return
                    
                    # Cập nhật registration (sang tên)
                    db.execute(text("UPDATE Registrations SET guest_id = :new_gid WHERE registration_id = :rid"), {"new_gid": new_guest_id, "rid": registration_id})
                st.success(f"Đã ủy quyền tham dự thành công cho {new_name}!")
                time.sleep(1.5)
                st.rerun()

# --- HÀM POP-UP YÊU CẦU HOÀN TIỀN ---
@st.dialog("Hủy đăng ký và Yêu cầu hoàn tiền")
def refund_ticket_dialog(registration_id, event_name):
    st.markdown(f"**Sự kiện:** {event_name}")
    st.warning("Bạn có chắc chắn muốn yêu cầu hoàn tiền không? Ban tổ chức sẽ liên hệ với bạn để xử lý nếu sự kiện hỗ trợ hoàn tiền.")
    
    reason = st.text_area("Lý do hoàn tiền (Tùy chọn)")
    
    if st.button("Gửi yêu cầu hoàn tiền", type="primary", use_container_width=True):
        with st.spinner("Đang gửi yêu cầu..."):
            with get_db() as db:
                # Mở rộng ENUM của attendance_status nếu chưa có
                try:
                    db.execute(text("ALTER TABLE Registrations MODIFY COLUMN attendance_status ENUM('Registered', 'Attended', 'No-show', 'Refund Requested', 'Refunded') NOT NULL DEFAULT 'Registered'"))
                except Exception:
                    pass
                
                db.execute(text("UPDATE Registrations SET attendance_status = 'Refund Requested' WHERE registration_id = :rid"), {"rid": registration_id})
            st.success("Đã gửi yêu cầu hoàn tiền thành công! Trạng thái vé đã được cập nhật.")
            time.sleep(1.5)
            st.rerun()

st.title(":material/local_activity: Vé Của Tôi")

with get_db() as db:
    try:
        my_tickets = db.execute(text("""
            SELECT r.registration_id, e.event_id, e.event_name, 
                   DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') as start_time,
                   DATE_FORMAT(e.end_time, '%d/%m/%Y %H:%i') as end_time,
                   v.venue_name, v.address as venue_address, r.attendance_status,
                   IFNULL(e.ticket_price, 0) as ticket_price,
                   IFNULL(e.image_url, 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80') as image_url,
                   IFNULL(r.ticket_count, 1) as ticket_count,
                   IFNULL(r.ticket_type, 'Standard') as ticket_type,
                   r.vat_company
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Venues v ON e.venue_id = v.venue_id
            WHERE r.guest_id = :gid
            ORDER BY e.start_time DESC
        """), {"gid": guest_id}).fetchall()
    except Exception:
        my_tickets = db.execute(text("""
            SELECT r.registration_id, e.event_id, e.event_name, 
                   DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') as start_time,
                   DATE_FORMAT(e.end_time, '%d/%m/%Y %H:%i') as end_time,
                   v.venue_name, v.address as venue_address, r.attendance_status,
                   IFNULL(e.ticket_price, 0) as ticket_price,
                   IFNULL(e.image_url, 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80') as image_url,
                   1 as ticket_count,
                   'Standard' as ticket_type,
                   NULL as vat_company
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Venues v ON e.venue_id = v.venue_id
            WHERE r.guest_id = :gid
            ORDER BY e.start_time DESC
        """), {"gid": guest_id}).fetchall()
    
if not my_tickets:
    st.info("Bạn chưa đăng ký sự kiện nào.", icon=":material/info:")
else:
    for t in my_tickets:
        t_dict = dict(t._mapping)
        with st.container(border=True):
            col_img, col1, col2 = st.columns([1, 2.5, 0.8])
            with col_img:
                st.image(t_dict["image_url"], use_container_width=True)
            with col1:
                st.markdown(f"### :material/event_seat: {t_dict['event_name']}")
                st.markdown(f"**:material/schedule: Thời gian:** {t_dict['start_time']} - {t_dict['end_time']}  \n**:material/location_on: Địa điểm:** {t_dict['venue_name']} ({t_dict['venue_address']})")
                
                status_color = "green" if t_dict["attendance_status"] == "Attended" else (
                               "red" if t_dict["attendance_status"] in ["No-show", "Refund Requested", "Refunded"] else "blue")
                st.markdown(f"**:material/info: Trạng thái:** :{status_color}[{t_dict['attendance_status']}]")
                
                if t_dict["ticket_price"] > 0:
                    total_paid = float(t_dict['ticket_price']) * t_dict['ticket_count'] * (2 if "VIP" in t_dict['ticket_type'] else 1)
                    st.markdown(f"**:material/payments: Tổng thanh toán:** {total_paid:,.0f} VNĐ")
                else:
                    st.markdown(f"**:material/payments: Phí tham dự:** Miễn phí")
                    
                st.markdown(f"**:material/style: Số lượng & Hạng vé:** **{t_dict['ticket_count']}** vé `{t_dict['ticket_type']}`")
                if t_dict.get("vat_company"):
                    st.markdown(f"**:material/receipt_long: Yêu cầu xuất VAT:** {t_dict['vat_company']}")
                    
            with col2:
                st.write("")
                if t_dict["attendance_status"] == "Registered":
                    if st.button("Ủy quyền", icon=":material/swap_horiz:", key=f"transfer_{t_dict['registration_id']}", use_container_width=True):
                        transfer_ticket_dialog(t_dict['registration_id'], t_dict['event_name'])
                        
                    if t_dict["ticket_price"] > 0:
                        if st.button("Hoàn tiền", icon=":material/currency_exchange:", key=f"refund_{t_dict['registration_id']}", use_container_width=True):
                            refund_ticket_dialog(t_dict['registration_id'], t_dict['event_name'])
                    else:
                        if st.button("Hủy đăng ký", icon=":material/cancel:", key=f"cancel_{t_dict['registration_id']}", use_container_width=True):
                            with get_db() as db:
                                db.execute(text("DELETE FROM Registrations WHERE registration_id = :rid"), {"rid": t_dict["registration_id"]})
                            st.warning("Đã hủy đăng ký thành công!")
                            st.rerun()
                else:
                    st.button("Không thể thao tác", icon=":material/block:", disabled=True, key=f"dis_{t_dict['registration_id']}", use_container_width=True)