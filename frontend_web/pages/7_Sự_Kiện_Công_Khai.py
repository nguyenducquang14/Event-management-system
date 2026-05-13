"""
pages/5_Su_Kien_Cong_Khai.py
Danh sách các sự kiện công khai và chức năng đăng ký tham gia dành cho Guest
"""
import streamlit as st
import time
import json
from sqlalchemy import text
from app.config import get_db
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Sự Kiện Công Khai", page_icon="📅", layout="wide")
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

guest_record = get_or_create_guest(user_email, user_info["name"])
guest_id = guest_record["guest_id"]

# --- HÀM POP-UP (DIALOG) THANH TOÁN VÀ XUẤT VÉ ---
@st.dialog("Đăng ký Vé Tham Dự", width="large")
def show_registration_dialog(eid, event_name, guest_id, cap, reg_count, price_val):
    st.markdown(f"### :material/confirmation_number: {event_name}")
    
    # Tải Cấu hình Loại Vé và Form Tùy biến từ DB
    with get_db() as db:
        try:
            ev_data = db.execute(text("SELECT ticket_tiers, custom_fields FROM Events WHERE event_id = :eid"), {"eid": eid}).fetchone()
            tiers_json = json.loads(ev_data.ticket_tiers) if ev_data and ev_data.ticket_tiers else None
            fields_json = json.loads(ev_data.custom_fields) if ev_data and ev_data.custom_fields else None
        except Exception:
            tiers_json = None
            fields_json = None
            
    st.markdown("#### 1. Chọn Hạng Vé & Đăng ký nhóm")
    c_type, c_qty = st.columns(2)
    ticket_type = "Standard"
    
    if tiers_json:
        tier_options = [f"{t['Tên Loại Vé']} - {float(t['Giá (VNĐ)']):,.0f} VNĐ" for t in tiers_json]
        selected_tier_str = c_type.selectbox("Loại vé", tier_options)
        ticket_type = selected_tier_str.split(" - ")[0]
        for t in tiers_json:
            if t['Tên Loại Vé'] == ticket_type:
                price_val = float(t['Giá (VNĐ)'])
                break
    else:
        if price_val > 0:
            ticket_type = c_type.selectbox("Loại vé", ["Tiêu chuẩn (Standard)", "VIP (Kèm Ăn trưa & Xe đưa đón)"])
        else:
            ticket_type = "Miễn phí (Free Pass)"
            c_type.text_input("Loại vé", value=ticket_type, disabled=True)
            
    ticket_count = c_qty.number_input("Số lượng vé (Tối đa 10 cho Group)", min_value=1, max_value=10, value=1)
    
    st.markdown("#### 2. Điền thông tin Người tham dự")
    if fields_json:
        st.info("💡 Sự kiện này yêu cầu cung cấp thêm thông tin từ Biểu mẫu Tùy biến của Ban tổ chức.")
        
    attendees_data = []
    phone = guest_record.get("phone_number") or ""
    
    for i in range(ticket_count):
        with st.expander(f"👤 Người tham dự #{i+1} {'(Người đại diện)' if i==0 else ''}", expanded=(i==0)):
            a_name = st.text_input(f"Họ và tên *", value=st.session_state["user_info"]["name"] if i==0 else "", key=f"name_{i}")
            a_email = st.text_input(f"Email *", value=st.session_state["user_info"]["email"] if i==0 else "", key=f"email_{i}")
            if i == 0:
                phone = st.text_input(f"Số điện thoại liên hệ *", value=phone, key=f"phone_{i}")
                
            custom_answers = {}
            if fields_json:
                st.markdown("**Trường thông tin tùy chọn:**")
                for idx, field in enumerate(fields_json):
                    f_name = field.get("Tên trường", f"Câu hỏi {idx}")
                    f_type = field.get("Loại", "Văn bản ngắn")
                    f_req = field.get("Bắt buộc", False)
                    f_opts = str(field.get("Tùy chọn", ""))
                    
                    label = f"{f_name} {'*' if f_req else ''}"
                    if f_type == "Trắc nghiệm" and f_opts:
                        custom_answers[f_name] = st.selectbox(label, [o.strip() for o in f_opts.split(",") if o.strip()], key=f"cf_{i}_{idx}")
                    elif f_type == "Hộp kiểm":
                        custom_answers[f_name] = st.checkbox(label, key=f"cf_{i}_{idx}")
                    elif f_type == "Đánh giá sao":
                        custom_answers[f_name] = st.slider(label, 1, 5, 5, key=f"cf_{i}_{idx}")
                    else:
                        custom_answers[f_name] = st.text_input(label, key=f"cf_{i}_{idx}")
                        
            attendees_data.append({"name": a_name, "email": a_email, "custom": custom_answers})
            
    total_price = price_val * ticket_count * (2 if "VIP" in ticket_type and not tiers_json else 1)
    
    req_vat = False
    company = ""
    tax_code = ""

    if total_price > 0:
        st.markdown("#### 3. Thông tin Xuất Hóa đơn (Tùy chọn)")
        with st.container(border=True):
            req_vat = st.checkbox("Tôi cần xuất hóa đơn đỏ (VAT)")
            if req_vat:
                c3, c4 = st.columns(2)
                company = c3.text_input("Tên Công ty / Tổ chức *")
                tax_code = c4.text_input("Mã số thuế *")
                st.caption("Hóa đơn điện tử sẽ được gửi về email của bạn trong vòng 3-5 ngày làm việc.")
                
        st.markdown("#### 4. Phương thức thanh toán")
        pay_method = st.radio("Chọn phương thức", ["💳 Chuyển khoản ngân hàng", "📱 Ví điện tử (Momo, VNPay, ZaloPay)", "🌍 Thẻ tín dụng/Ghi nợ"])
        
        if pay_method == "💳 Chuyển khoản ngân hàng":
            with get_db() as db:
                try:
                    org_bank = db.execute(text("""
                        SELECT o.bank_name, o.bank_account_number, o.bank_account_name 
                        FROM Events e JOIN Organizers o ON e.organizer_id = o.organizer_id 
                        WHERE e.event_id = :eid
                    """), {"eid": eid}).fetchone()
                    if org_bank and org_bank.bank_name and org_bank.bank_account_number:
                        st.info(f"**Vui lòng chuyển khoản vào tài khoản:**\n\n"
                                f"🏦 **Ngân hàng:** {org_bank.bank_name}\n\n"
                                f"💳 **Số tài khoản:** `{org_bank.bank_account_number}`\n\n"
                                f"👤 **Chủ tài khoản:** {org_bank.bank_account_name}\n\n"
                                f"📝 **Nội dung:** `TT ve {event_name[:20]} - {phone}`", icon=":material/account_balance:")
                    else:
                        st.warning("Ban tổ chức chưa cung cấp thông tin tài khoản ngân hàng. Vui lòng liên hệ trực tiếp với Ban tổ chức để thanh toán.", icon=":material/warning:")
                except Exception:
                    pass

        st.markdown("---")
        c_total, c_btn = st.columns([1, 1], vertical_alignment="bottom")
        c_total.markdown(f"Tổng thanh toán ({ticket_count} vé {ticket_type.split(' ')[0]}): <h3 style='color: #ef4444 !important; margin-top: 0;'>{total_price:,.0f} VNĐ</h3>", unsafe_allow_html=True)
        
        if c_btn.button("Xác nhận & Thanh toán", icon=":material/lock:", type="primary", use_container_width=True):
            if not phone:
                st.error("Vui lòng nhập Số điện thoại liên hệ!")
            elif req_vat and (not company or not tax_code):
                st.error("Vui lòng nhập Tên công ty và Mã số thuế để xuất hóa đơn VAT!")
            else:
                with st.spinner("Đang khởi tạo hợp đồng và xử lý giao dịch..."):
                    time.sleep(2)
                st.toast("Đã ghi nhận thanh toán / yêu cầu báo giá!", icon="✅")
                time.sleep(1)
                
                with st.spinner("Đang xử lý đăng ký..."):
                    with get_db() as db:
                        group_json = json.dumps(attendees_data, ensure_ascii=False)
                        try:
                            db.execute(text("""
                                INSERT INTO Registrations (event_id, guest_id, attendance_status, ticket_count, ticket_type, vat_company, vat_tax_code, group_details) 
                                VALUES (:eid, :gid, 'Registered', :t_count, :t_type, :v_comp, :v_tax, :g_det)
                            """), {
                                "eid": eid, "gid": guest_id, "t_count": ticket_count, "t_type": ticket_type.split(' ')[0],
                                "v_comp": company if req_vat else None, "v_tax": tax_code if req_vat else None, "g_det": group_json
                            })
                        except Exception:
                            db.execute(text("INSERT INTO Registrations (event_id, guest_id, attendance_status) VALUES (:eid, :gid, 'Registered')"), {"eid": eid, "gid": guest_id})
                            
                        if cap and cap > 0 and (reg_count + ticket_count) >= cap:
                            db.execute(text("UPDATE Events SET status = 'Full' WHERE event_id = :eid"), {"eid": eid})
                        
                        desc = f"Bán {ticket_count} vé {ticket_type.split(' ')[0]} - {st.session_state['user_info']['name']}"
                        if req_vat:
                            desc += f" (Cần xuất VAT cho {company} - MST {tax_code})"
                            
                        db.execute(text("INSERT INTO Finances (event_id, type, amount, description) VALUES (:eid, 'Income', :amount, :desc)"), 
                                   {"eid": eid, "amount": total_price, "desc": desc[:200]})
                        
                        db.execute(text("UPDATE Guests SET phone_number = :phone WHERE guest_id = :gid"), {"phone": phone, "gid": guest_id})
                        
                st.success("Thành công! Xác nhận tham dự (và Hóa đơn/Báo giá) đã được gửi vào Email của doanh nghiệp.")
                time.sleep(2)
                st.rerun()
    else:
        st.info("Sự kiện Miễn phí. Vui lòng xác nhận để nhận thư mời/xác nhận tham dự.")
        st.markdown("---")
        if st.button("Xác nhận & Hoàn tất đăng ký", icon=":material/check_circle:", type="primary", use_container_width=True):
            with get_db() as db:
                group_json = json.dumps(attendees_data, ensure_ascii=False)
                try:
                    db.execute(text("""
                        INSERT INTO Registrations (event_id, guest_id, attendance_status, ticket_count, ticket_type, group_details) 
                        VALUES (:eid, :gid, 'Registered', :t_count, :t_type, :g_det)
                    """), {"eid": eid, "gid": guest_id, "t_count": ticket_count, "t_type": ticket_type.split(' ')[0], "g_det": group_json})
                except Exception:
                    db.execute(text("INSERT INTO Registrations (event_id, guest_id, attendance_status) VALUES (:eid, :gid, 'Registered')"), {"eid": eid, "gid": guest_id})
                    
                if cap and cap > 0 and (reg_count + ticket_count) >= cap:
                    db.execute(text("UPDATE Events SET status = 'Full' WHERE event_id = :eid"), {"eid": eid})
            st.success(f"Đăng ký thành công {ticket_count} vé! Xác nhận tham dự đã được gửi vào Email.")
            time.sleep(1.5)
            st.rerun()

st.title(":material/event: Sự Kiện Công Khai")
st.markdown("Khám phá và đăng ký tham gia các sự kiện, hội thảo và chương trình hấp dẫn trên hệ thống.")

# --- BỘ LỌC TÌM KIẾM ---
with st.container(border=True):
    st.markdown("##### :material/tune: Bộ lọc Tìm kiếm")
    col_cat, col_type, col_aud, col_price = st.columns(4)
    
    categories = ["Tất cả", "Công nghệ", "Giáo dục", "Giải trí", "Nghệ thuật", "Khác"]
    selected_cat = col_cat.selectbox("Ngành nghề (Industry)", categories)
    
    event_types = ["Tất cả", "Conference", "Trade Show", "Workshop", "Networking"]
    selected_type = col_type.selectbox("Loại hình", event_types, format_func=lambda x: {"Conference": "Hội thảo", "Trade Show": "Triển lãm", "Workshop": "Workshop", "Networking": "Giao lưu"}.get(x, x))
    
    audiences = ["Tất cả", "C-level / Executive", "Manager / Director", "Specialist / Staff", "All"]
    selected_aud = col_aud.selectbox("Đối tượng", audiences, format_func=lambda x: {"All": "Mọi đối tượng", "C-level / Executive": "Quản lý cấp cao", "Manager / Director": "Giám đốc/Trưởng phòng", "Specialist / Staff": "Chuyên viên/Sinh viên"}.get(x, x))
    
    selected_fee = col_price.selectbox("Chi phí tham dự", ["Tất cả", "Miễn phí", "Trả phí"])

with get_db() as db:
    upcoming_events = db.execute(text("""
        SELECT e.event_id, e.event_name, DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') as start_time, 
               DATE_FORMAT(e.end_time, '%d/%m/%Y %H:%i') as end_time,
               v.venue_name, v.address as venue_address, e.status, e.max_capacity, e.description,
               IFNULL(e.category, 'Khác') as category, 
               IFNULL(e.ticket_price, 0) as ticket_price,
               IFNULL(e.image_url, 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80') as image_url,
               IFNULL(e.event_type, 'Conference') as event_type,
               IFNULL(e.target_audience, 'All') as target_audience,
               IFNULL(e.is_private, FALSE) as is_private,
               e.access_code,
               (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as current_registered
        FROM Events e
        JOIN Venues v ON e.venue_id = v.venue_id
        WHERE e.status IN ('Scheduled', 'Full') AND e.end_time >= NOW()
        ORDER BY e.start_time
    """)).fetchall()
    
    my_regs = db.execute(text("SELECT event_id FROM Registrations WHERE guest_id = :gid"), {"gid": guest_id}).fetchall()
    registered_event_ids = [r.event_id for r in my_regs]

# --- ÁP DỤNG BỘ LỌC ---
filtered_events = []
for ev in upcoming_events:
    ev_dict = dict(ev._mapping)
    
    if selected_cat != "Tất cả" and ev_dict["category"] != selected_cat:
        continue
        
    if selected_type != "Tất cả" and ev_dict["event_type"] != selected_type:
        continue
        
    if selected_aud != "Tất cả" and ev_dict["target_audience"] != selected_aud:
        continue
        
    price = float(ev_dict["ticket_price"])
    if selected_fee == "Miễn phí" and price > 0:
        continue
    if selected_fee == "Trả phí" and price == 0:
        continue
        
    filtered_events.append(ev_dict)

st.markdown(f"**:material/filter_alt: Hiển thị:** {len(filtered_events)} sự kiện")

if not filtered_events:
    st.info("Chưa tìm thấy sự kiện doanh nghiệp nào phù hợp với tiêu chí của bạn.", icon=":material/info:")
else:
    import pandas as pd
    for ev_dict in filtered_events:
        eid = ev_dict["event_id"]
        
        # Định dạng hiển thị giá vé
        price_val = float(ev_dict["ticket_price"])
        price_str = "Miễn phí" if price_val == 0 else f"{price_val:,.0f} VNĐ"
        cat_str = ev_dict["category"]
        
        # Lựa chọn Icon theo danh mục sự kiện
        icon_map = {
            "Công nghệ": "computer",
            "Giáo dục": "school",
            "Giải trí": "celebration",
            "Nghệ thuật": "palette",
            "Khác": "event"
        }
        c_icon = icon_map.get(cat_str, "event")
        
        is_private = bool(ev_dict.get("is_private"))
        access_code = ev_dict.get("access_code")
        
        with st.container(border=True):
            col_img, col1, col2 = st.columns([1, 2.2, 0.8])
            with col_img:
                st.image(ev_dict["image_url"], use_container_width=True)
            with col1:
                st.markdown(f"### :material/{c_icon}: {ev_dict['event_name']} {'🔒 (Private)' if is_private else ''}")
                st.markdown(f"**:material/category: Ngành nghề:** :blue-background[{cat_str}] | **:material/corporate_fare: Loại hình:** :gray-background[{ev_dict['event_type']}] | **:material/payments: Phí:** :green-background[{price_str}]")
                st.markdown(f"**:material/schedule: Thời gian:** {ev_dict['start_time']} - {ev_dict['end_time']}  \n**:material/location_on: Địa điểm:** {ev_dict['venue_name']} ({ev_dict['venue_address']})")
                
                # Hiển thị cấp bậc yêu cầu
                if ev_dict['target_audience'] != 'All':
                    st.markdown(f"**:material/assignment_ind: Cấp bậc đề xuất:** `{ev_dict['target_audience']}`")
                
                # XỬ LÝ KHÓA SỰ KIỆN PRIVATE
                show_details = True
                if is_private and eid not in registered_event_ids:
                    st.warning("Sự kiện này chỉ dành cho đối tác VIP hoặc có giấy mời.")
                    code_input = st.text_input("🔑 Nhập mã khách mời (Invite Code) để mở khóa:", key=f"code_{eid}")
                    if code_input != access_code:
                        show_details = False
                        st.caption("Gợi ý: Dùng mã `VIP2026` để test.")
                
                if show_details:
                    # --- Tính toán và Hiển thị số lượng ghế ---
                    cap = ev_dict["max_capacity"]
                    reg_count = ev_dict["current_registered"]
                    is_full = False
                    if cap and cap > 0:
                        slots_rem = cap - reg_count
                        st.markdown(f"**:material/group: Số lượng ghế:** Còn lại **{slots_rem}** / {cap} ghế")
                        if slots_rem <= 0:
                            is_full = True
                    else:
                        st.markdown(f"**:material/group: Số lượng ghế:** Không giới hạn (Đã đăng ký: {reg_count})")
                        
                    st.info(ev_dict["description"] or "Chưa có mô tả.", icon=":material/description:")
                        
            with col2:
                st.write("") 
                if eid in registered_event_ids:
                    st.button("Đã Đăng ký", icon=":material/check_circle:", disabled=True, key=f"reg_{eid}", use_container_width=True)
                elif ev_dict["status"] == "Full" or is_full:
                    st.button("Đã Đầy", icon=":material/block:", disabled=True, key=f"full_{eid}", use_container_width=True)
                else:
                    if st.button("Đăng ký Tham gia", icon=":material/how_to_reg:", type="primary", key=f"btn_reg_{eid}", use_container_width=True):
                        show_registration_dialog(eid, ev_dict["event_name"], guest_id, cap, reg_count, price_val)