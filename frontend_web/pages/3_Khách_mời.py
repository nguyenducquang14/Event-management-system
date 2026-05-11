"""
pages/2_guests.py
Trang Quản lý Khách mời — search realtime, data_editor, CRUD
"""

import streamlit as st
import pandas as pd

from app.database import DatabaseManager
from app.database.schemas import GuestCreate
from app.ui.components import (
    section, stat_row, styled_df,
    show_success, show_error, search_bar,
)
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Khách mời | EMS", page_icon="👥", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# 1. BỨC TƯỜNG LỬA (Phân quyền bảo mật)
if "token" not in st.session_state or "user_info" not in st.session_state:
    st.warning("Vui lòng đăng nhập để truy cập!")
    st.stop()

user_info = st.session_state["user_info"]
roles = user_info.get("roles", [])
is_admin = "Admin" in roles
is_organizer = "Organizer" in roles

if not is_admin and not is_organizer:
    st.error("Lỗi 403: Cấm truy cập.")
    st.stop()

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

owner_id = None
if is_organizer and not is_admin:
    from app.database.repositories.organizer_repo import OrganizerRepository
    org_repo = OrganizerRepository()
    owner_id = org_repo.get_or_create_organizer(user_info.get("email"), user_info.get("name"))


@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# ── Page header ──────────────────────────────────────────────
c_title, c_btn = st.columns([4, 1])
c_title.markdown("## :material/group: Quản lý Khách mời")
add_new = c_btn.button("Thêm khách mới", icon=":material/add:", use_container_width=True)

# ── Search bar (realtime) ────────────────────────────────────
kw = st.text_input(
    "Tìm kiếm",
    placeholder="Tìm theo tên hoặc email...",
    key="guest_search",
    label_visibility="collapsed",
)

# ── Load data ────────────────────────────────────────────────
with st.spinner("Đang tải..."):
    if owner_id:
        query = f"SELECT DISTINCT g.* FROM Guests g JOIN Registrations r ON g.guest_id = r.guest_id JOIN Events e ON r.event_id = e.event_id WHERE e.organizer_id = {owner_id}"
        if kw:
            query += f" AND (g.guest_name LIKE '%{kw}%' OR g.email LIKE '%{kw}%')"
        guests = db.events.execute_query(query) or []
        total_label = f"Khách của tôi: {len(guests)} khách"
    else:
        if kw:
            guests = db.guests.search(kw)
            total_label = f"Tìm thấy: {len(guests)} khách"
        else:
            result = db.guests.get_all(page=1, page_size=200)
            guests = result.get("data", [])
            total_label = f"Tổng: {result.get('total', 0)} khách"

# ── Stats ────────────────────────────────────────────────────
total = len(guests) if owner_id else db.guests.count()
stat_row([
    ("Tổng khách mời", total, "blue"),
    ("Kết quả hiện tại", len(guests), "purple"),
    ("", "", "gray"),
    ("", "", "gray"),
])
st.caption(total_label)
st.markdown("")

# ── TABS ─────────────────────────────────────────────────────
tab_list, tab_activity, tab_add, tab_edit, tab_delete = st.tabs([
    ":material/list: Danh sách", ":material/emoji_events: Hoạt động", ":material/person_add: Thêm mới", ":material/edit: Sửa thông tin", ":material/delete: Xóa"
])


# ════════════════════════════════════════════════════════════
# TAB 1: DANH SÁCH
# ════════════════════════════════════════════════════════════
with tab_list:
    if not guests:
        st.info("Không tìm thấy khách nào.")
    else:
        section("list", "Danh sách khách mời", "Chuyển sang tab 'Sửa thông tin' để cập nhật dữ liệu")

        df_guests = pd.DataFrame(guests)
        keep_cols = [c for c in
                     ["guest_id","guest_name","email","phone_number","address","created_at"]
                     if c in df_guests.columns]
        
        df_display = df_guests[keep_cols].rename(columns={
            "guest_id": "ID", "guest_name": "Họ tên",
            "email": "Email", "phone_number": "Điện thoại",
            "address": "Địa chỉ", "created_at": "Tạo lúc"
        })

        styled_df(df_display.to_dict("records"), height=420)

        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button("Tải CSV", csv, "guests.csv", "text/csv", icon=":material/download:")


# ════════════════════════════════════════════════════════════
# TAB 2: HOẠT ĐỘNG
# ════════════════════════════════════════════════════════════
with tab_activity:
    import plotly.express as px

    section("emoji_events", "Top khách tích cực", "Khách tham dự nhiều sự kiện nhất")
    top_n = st.slider("Hiển thị top", 5, 30, 10, key="guest_top_n")

    with st.spinner():
        if owner_id:
            activity = db.events.execute_query(f"""
                SELECT g.guest_name, g.email,
                       COUNT(r.event_id) AS total_registrations,
                       SUM(r.attendance_status='Attended') AS total_attended,
                       ROUND(SUM(r.attendance_status='Attended') / NULLIF(COUNT(r.event_id),0) * 100, 2) AS personal_rate_pct
                FROM Guests g 
                JOIN Registrations r ON g.guest_id=r.guest_id
                JOIN Events e ON r.event_id = e.event_id
                WHERE e.organizer_id = {owner_id}
                GROUP BY g.guest_id, g.guest_name, g.email
                ORDER BY total_registrations DESC
                LIMIT {top_n}
            """) or []
        else:
            activity = db.guests.get_activity(limit=top_n)

    if activity:
        df_a = pd.DataFrame(activity)

        # Bar chart
        fig = px.bar(
            df_a, x="guest_name", y="total_registrations",
            color="personal_rate_pct",
            color_continuous_scale="Blues",
            labels={"guest_name": "Khách", "total_registrations": "Tổng đăng ký",
                    "personal_rate_pct": "Tỉ lệ (%)"},
            height=320,
        )
        fig.update_traces(textfont_color="#000000")
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000"), title=dict(font=dict(color="#000000"))),
            yaxis=dict(color="#000000", tickfont=dict(color="#000000"), title=dict(font=dict(color="#000000"))),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
            coloraxis_colorbar=dict(
                x=1.05,
                titlefont=dict(color="#000000"),
                tickfont=dict(color="#000000")
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table
        styled_df(activity, height=300)
    else:
        st.info("Chưa có dữ liệu hoạt động.")

    # Chi tiết một khách
    st.divider()
    section("history", "Lịch sử sự kiện của một khách")
    if guests:
        guest_map = {g["guest_id"]: f"#{g['guest_id']} {g['guest_name']}" for g in guests}
        sel_g = st.selectbox("Chọn khách", list(guest_map.keys()),
                             format_func=lambda x: guest_map[x], key="guest_hist_sel")
        hist = db.guests.get_events_of_guest(sel_g)
        if hist:
            styled_df(hist, badge_cols=["attendance_status", "status"], height=220)
        else:
            st.info("Chưa đăng ký sự kiện nào.")


# ════════════════════════════════════════════════════════════
# TAB 3: THÊM MỚI
# ════════════════════════════════════════════════════════════
with tab_add:
    section("person_add", "Thêm khách mời mới")

    with st.form("form_add_guest", clear_on_submit=True):
        name  = st.text_input("Họ tên *")
        email = st.text_input("Email *")
        c1, c2 = st.columns(2)
        phone = c1.text_input("Điện thoại")
        addr  = c2.text_input("Địa chỉ")

        col_btn, _ = st.columns([1, 3])
        submitted = col_btn.form_submit_button("Thêm khách", icon=":material/add:", use_container_width=True)

    if submitted:
        if not name or not email:
            show_error("Họ tên và Email là bắt buộc.")
        else:
            try:
                new_id = db.guests.create(
                    GuestCreate(
                        guest_name=name, email=email,
                        phone_number=phone or None,
                        address=addr or None,
                    )
                )
                show_success(f"Đã thêm khách '{name}' (ID: {new_id})!")
                st.rerun()
            except Exception as e:
                show_error(f"Lỗi: {e}")

    # Bulk add hint
    st.divider()
    st.markdown("**💡 Thêm nhiều khách cùng lúc:** Upload file CSV với cột `guest_name, email, phone_number, address`")
    uploaded = st.file_uploader("Tải file CSV", type="csv", key="guest_bulk_upload")
    if uploaded:
        df_up = pd.read_csv(uploaded)
        st.dataframe(df_up.head(), use_container_width=True)
        if st.button("Import tất cả", icon=":material/upload:"):
            ok, fail = 0, 0
            for _, row in df_up.iterrows():
                try:
                    db.guests.create(GuestCreate(
                        guest_name=str(row.get("guest_name", "")),
                        email=str(row.get("email", "")),
                        phone_number=str(row.get("phone_number", "")) or None,
                        address=str(row.get("address", "")) or None,
                    ))
                    ok += 1
                except Exception:
                    fail += 1
            show_success(f"Import thành công: {ok} | Lỗi: {fail}")
            st.rerun()


# ════════════════════════════════════════════════════════════
# TAB 4: SỬA THÔNG TIN
# ════════════════════════════════════════════════════════════
with tab_edit:
    section("edit", "Sửa thông tin khách mời")

    if not guests:
        st.info("Không có khách nào.")
    else:
        guest_map2 = {g["guest_id"]: f"#{g['guest_id']} {g['guest_name']}" for g in guests}
        edit_gid = st.selectbox(
            "Chọn khách cần sửa",
            list(guest_map2.keys()),
            format_func=lambda x: guest_map2[x],
            key="guest_edit_sel",
        )
        g_cur = db.guests.get_by_id(edit_gid) or {}

        with st.form("form_edit_guest"):
            name_u  = st.text_input("Họ tên *",    value=g_cur.get("guest_name", ""))
            email_u = st.text_input("Email *",       value=g_cur.get("email", ""))
            c1, c2 = st.columns(2)
            phone_u = c1.text_input("Điện thoại",  value=g_cur.get("phone_number", "") or "")
            addr_u  = c2.text_input("Địa chỉ",     value=g_cur.get("address", "") or "")
            saved = st.form_submit_button("Lưu thay đổi", icon=":material/save:", use_container_width=True)

        if saved:
            try:
                db.guests.update(
                    edit_gid,
                    GuestCreate(
                        guest_name=name_u, email=email_u,
                        phone_number=phone_u or None, address=addr_u or None,
                    ),
                )
                show_success(f"Đã cập nhật khách #{edit_gid}!")
                st.rerun()
            except Exception as e:
                show_error(f"Lỗi: {e}")


# ════════════════════════════════════════════════════════════
# TAB 5: XÓA
# ════════════════════════════════════════════════════════════
with tab_delete:
    section("delete", "Xóa khách mời", "Xóa cascade toàn bộ lịch sử đăng ký của khách này")

    if not guests:
        st.info("Không có khách nào.")
    else:
        guest_map3 = {g["guest_id"]: f"#{g['guest_id']} {g['guest_name']} ({g['email']})" for g in guests}
        del_gid = st.selectbox(
            "Chọn khách cần xóa",
            list(guest_map3.keys()),
            format_func=lambda x: guest_map3[x],
            key="guest_del_sel",
        )
        g_del = db.guests.get_by_id(del_gid)
        if g_del:
            st.warning(f"⚠️ Sẽ xóa: **{g_del['guest_name']}** — {g_del['email']}")

        confirm_g = st.checkbox("Xác nhận muốn xóa khách này", key="confirm_del_guest")
        if st.button("Xóa vĩnh viễn", icon=":material/delete_forever:", disabled=not confirm_g):
            db.guests.delete(del_gid)
            show_success(f"Đã xóa khách #{del_gid}!")
            st.rerun()

if add_new:
    st.rerun()
