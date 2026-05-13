"""
pages/2_Dashboard_Ban_To_Chuc.py
Bảng điều khiển tập trung dành riêng cho vai trò Organizer
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, time
import time as time_lib

# Import repository đã được xây dựng để thao tác với DB
from app.database.repositories.organizer_repo import OrganizerRepository
from app.ui.components import styled_df
from app.config import get_db
from app.ui.styles import CUSTOM_CSS # Import CUSTOM_CSS
from sqlalchemy import text

st.set_page_config(page_title="Dashboard Ban Tổ Chức", page_icon="⚙️", layout="wide")

# 1. BỨC TƯỜNG LỬA (Phân quyền bảo mật)
if "token" not in st.session_state or "user_info" not in st.session_state:
    st.warning("Vui lòng đăng nhập để truy cập!")
    st.stop()

roles = st.session_state["user_info"].get("roles", [])
if "Organizer" not in roles and "Admin" not in roles:
    st.error("Lỗi 403: Cấm truy cập. Khu vực này dành riêng cho Ban tổ chức sự kiện.")
    st.stop()

# --- ẨN CÁC MENU CỦA GUEST ĐỐI VỚI ADMIN/ORGANIZER ---
st.markdown("""
<style>
    /* Ẩn các menu của Guest và trang styles.py không cần thiết */
    [data-testid="stSidebarNav"] ul li:nth-last-child(1),
    [data-testid="stSidebarNav"] ul li:nth-last-child(2),
    [data-testid="stSidebarNav"] ul li:nth-last-child(3),
    [data-testid="stSidebarNav"] ul li:nth-last-child(4),
    [data-testid="stSidebarNav"] ul li:nth-last-child(5),
    [data-testid="stSidebarNav"] ul li:nth-last-child(6) { display: none !important; }
    
    /* --- GIAO DIỆN NỀN TRẮNG CHỮ ĐEN CHO DASHBOARD BAN TỔ CHỨC --- */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
    }
    
    /* Chỉnh màu font chung */
    h1, h2, h3, h4, h5, h6, p, label, li, .stMarkdownContainer {
        color: #000000 !important;
    }
    
    /* Ngoại trừ các nút Primary (Nút chính) sẽ giữ chữ trắng */
    button[kind="primary"] p {
        color: #FFFFFF !important;
    }
    
    /* Định dạng Form, Khung Expander và Input */
    [data-testid="stForm"], [data-testid="stExpander"] {
        background-color: #F8FAFC !important;
        border-color: #E2E8F0 !important;
    }
    
    /* Định dạng Input và Selectbox */
    input, div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* --- FIX LỊCH VÀ POPOVER (Ép nền trắng, chữ đen, thêm highlight ngày chọn) --- */
    div[data-baseweb="popover"] > div,
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] div,
    div[role="listbox"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Chữ đen cho các thẻ text trong lịch */
    div[data-baseweb="calendar"] span, div[data-baseweb="calendar"] p, div[data-baseweb="calendar"] label {
        background-color: transparent !important;
        color: #000000 !important;
    }
    
    /* --- HIỂN THỊ LƯỚI LỊCH (GRID) --- */
    div[data-baseweb="calendar"] div[role="grid"] {
        border-top: 1px solid #E2E8F0 !important;
        border-left: 1px solid #E2E8F0 !important;
        margin-top: 10px !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] div[role="gridcell"],
    div[data-baseweb="calendar"] div[role="columnheader"] {
        border-bottom: 1px solid #E2E8F0 !important;
        border-right: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Mũi tên chuyển tháng phải có màu đen để nhìn thấy */
    div[data-baseweb="calendar"] svg {
        fill: #000000 !important;
        color: #000000 !important;
        background-color: transparent !important;
    }
    
    /* Nút ngày tháng trong lịch (mặc định) */
    div[data-baseweb="calendar"] button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
    }
    
    /* Ngày đang được chọn (highlight xanh, chữ trắng) */
    div[data-baseweb="calendar"] button[aria-selected="true"],
    div[data-baseweb="calendar"] button[aria-selected="true"]:hover {
        background-color: #2563EB !important;
    }
    div[data-baseweb="calendar"] button[aria-selected="true"] span,
    div[data-baseweb="calendar"] button[aria-selected="true"] p {
        color: #FFFFFF !important;
    }
    
    /* Các ngày ngoài tháng hoặc bị vô hiệu hóa (Disabled/Outside month) -> Xám mờ giống Windows */
    div[data-baseweb="calendar"] button:disabled, 
    div[data-baseweb="calendar"] button[aria-disabled="true"] {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] button:disabled span,
    div[data-baseweb="calendar"] button[aria-disabled="true"] span,
    div[data-baseweb="calendar"] button:disabled p,
    div[data-baseweb="calendar"] button[aria-disabled="true"] p {
        color: #94A3B8 !important;
    }
    
    /* Hover vào ngày (highlight xám nhạt) */
    div[data-baseweb="calendar"] button:hover:not(:disabled):not([aria-selected="true"]) {
        background-color: #F1F5F9 !important;
    }
    
    /* Tùy chỉnh danh sách Dropdown (Selectbox) */
    li[role="option"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #F1F5F9 !important;
    }
    li[role="option"] span, li[role="option"] p {
        color: #000000 !important;
        background-color: transparent !important;
    }
    
    /* Chỉnh nền trắng và chữ đen cho Bảng (stTable) nhưng bỏ qua stDataFrame (data_editor) để tránh lỗi hiển thị trắng tinh */
    [data-testid="stTable"] *, th, td {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Dùng CSS filter để đảo ngược màu bảng stDataFrame (data_editor) từ nền đen chữ trắng sang nền trắng chữ đen */
    [data-testid="stDataFrame"] {
        filter: invert(1) hue-rotate(180deg);
    }
    
    /* Định dạng các nút phụ (Secondary Buttons) thành nền trắng, chữ đen */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
    }
    button[kind="secondary"] p, button[kind="secondary"] div {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

user_info = st.session_state["user_info"]
user_email = user_info.get("email", "")
user_name = user_info.get("name", "")

# Khởi tạo Repo và định danh Owner
org_repo = OrganizerRepository()
owner_id = org_repo.get_or_create_organizer(user_email, user_name)

# Đảm bảo các cột cho Dynamic Form và Ticket Tiers tồn tại
with get_db() as db:
    try:
        db.execute(text("ALTER TABLE Events ADD COLUMN ticket_tiers JSON, ADD COLUMN custom_fields JSON"))
        db.commit()
    except Exception:
        pass

st.title("⚙️ Tạo Sự kiện Mới")
st.markdown(f"**Đơn vị/Tổ chức:** {user_name} | **Email:** {user_email}")
st.markdown("---")

# --- LUỒNG TẠO SỰ KIỆN TẬP TRUNG ---
_, col_main, _ = st.columns([1, 1.5, 1])

with col_main:
    if "create_step" not in st.session_state:
        st.session_state["create_step"] = 1
        
    if st.session_state["create_step"] == 1:
        st.subheader("Bước 1: Thông tin Cơ bản")
        with st.form("create_event_form", clear_on_submit=True, border=False):
            e_name = st.text_input("Tên sự kiện *")
            e_date = st.date_input("Ngày tổ chức *")
            e_time = st.time_input("Giờ bắt đầu *", value=time(8, 0))
            
            venues = org_repo.get_all_venues()
            venue_dict = {v["venue_name"]: v["venue_id"] for v in venues}
            v_sel = st.selectbox("Địa điểm *", list(venue_dict.keys()))
            
            if st.form_submit_button("Tiếp tục", type="primary", use_container_width=True):
                if not e_name:
                    st.error("Vui lòng nhập tên sự kiện!")
                else:
                    start_datetime = datetime.combine(e_date, e_time)
                    end_datetime = start_datetime + timedelta(hours=4) # Mặc định kéo dài 4 tiếng
                    
                    with get_db() as db:
                        # Lưu sự kiện trực tiếp vào Database và Commit để đảm bảo dữ liệu được ghi nhận
                        db.execute(text("""
                            INSERT INTO Events (event_name, start_time, end_time, venue_id, organizer_id, status)
                            VALUES (:name, :start, :end, :vid, :oid, 'Scheduled')
                        """), {
                            "name": e_name, "start": start_datetime, "end": end_datetime,
                            "vid": venue_dict[v_sel], "oid": owner_id
                        })
                        db.commit()
                        
                        # Tìm event vừa tạo để chuyển tiếp sang bước 2
                        latest = db.execute(text("SELECT event_id, event_name FROM Events WHERE organizer_id = :oid ORDER BY event_id DESC LIMIT 1"), {"oid": owner_id}).fetchone()
                        if latest:
                            st.session_state["new_event_id"] = latest.event_id
                            st.session_state["new_event_name"] = latest.event_name
                            st.session_state["create_step"] = 2
                            st.rerun()
                        else:
                            st.success("Tạo sự kiện thành công!")
                            st.cache_data.clear() # Xóa cache để đảm bảo danh sách sự kiện được cập nhật
                            time_lib.sleep(1.5)
                            st.switch_page("pages/1_Quản_lý_Sự_kiện.py")
                            
    elif st.session_state["create_step"] == 2:
        import json
        st.success(f"Sự kiện **{st.session_state.get('new_event_name', '')}** đã được khởi tạo!")
        st.subheader("Bước 2: Cấu hình Vé & Form đăng ký")
        st.caption("Thiết lập các hạng vé và câu hỏi thu thập thông tin khách mời.")
        
        real_event_id = st.session_state.get("new_event_id")
        
        with get_db() as db:
            ev_data = db.execute(text("SELECT ticket_tiers, custom_fields FROM Events WHERE event_id = :eid"), {"eid": real_event_id}).fetchone()
            
        current_tiers = json.loads(ev_data.ticket_tiers) if ev_data and ev_data.ticket_tiers else [{"Tên Loại Vé": "Standard", "Giá (VNĐ)": 0, "Số lượng": 100, "Mở bán": "2026-01-01", "Đóng bán": "2026-12-31"}]
        current_fields = json.loads(ev_data.custom_fields) if ev_data and ev_data.custom_fields else [{"Tên trường": "Bạn biết đến sự kiện qua đâu?", "Loại": "Trắc nghiệm", "Bắt buộc": True, "Tùy chọn": "Facebook,Website"}]
        
        st.markdown("**1. Cài đặt Hạng vé:**")
        edited_tiers = st.data_editor(pd.DataFrame(current_tiers), num_rows="dynamic", use_container_width=True, key="new_tiers")
        
        st.markdown("**2. Form thông tin tùy chọn:**")
        edited_fields = st.data_editor(
            pd.DataFrame(current_fields), 
            num_rows="dynamic", 
            column_config={
                "Loại": st.column_config.SelectboxColumn("Loại", options=["Văn bản ngắn", "Trắc nghiệm", "Hộp kiểm", "Đánh giá sao"]),
                "Bắt buộc": st.column_config.CheckboxColumn("Bắt buộc")
            },
            use_container_width=True,
            key="new_fields"
        )
        
        c_back, c_save = st.columns(2)
        if c_back.button("Tạo sự kiện khác", use_container_width=True):
            st.session_state["create_step"] = 1
            st.rerun()
            
        if c_save.button("Hoàn tất & Lưu cấu hình", type="primary", use_container_width=True):
            tiers_json = edited_tiers.to_json(orient="records", force_ascii=False)
            fields_json = edited_fields.to_json(orient="records", force_ascii=False)
            with get_db() as db:
                db.execute(text("UPDATE Events SET ticket_tiers = :tiers, custom_fields = :fields WHERE event_id = :eid"), {"tiers": tiers_json, "fields": fields_json, "eid": real_event_id})
                db.commit()
            st.success("Đã lưu cấu hình và hoàn tất tạo sự kiện!")
            st.session_state["create_step"] = 1
            st.cache_data.clear() # Xóa cache để cập nhật dữ liệu toàn hệ thống
            time_lib.sleep(1.5)
            st.switch_page("pages/1_Quản_lý_Sự_kiện.py")