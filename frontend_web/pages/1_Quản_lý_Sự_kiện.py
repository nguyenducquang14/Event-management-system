"""
pages/1_events.py
Trang Quản lý Sự kiện — CRUD đầy đủ + data_editor + filter + dialog
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
from sqlalchemy import text
from app.config import get_db as get_db_session

from app.database import DatabaseManager
from app.database.schemas import EventCreate
from app.ui.components import (
    badge, section, stat_row, styled_df, show_success, show_error,
)
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Sự kiện | EMS", page_icon="📋", layout="wide")
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
    /* Ẩn các menu của Guest và trang styles.py không cần thiết */
    [data-testid="stSidebarNav"] ul li:nth-last-child(1),
    [data-testid="stSidebarNav"] ul li:nth-last-child(2),
    [data-testid="stSidebarNav"] ul li:nth-last-child(3),
    [data-testid="stSidebarNav"] ul li:nth-last-child(4),
    [data-testid="stSidebarNav"] ul li:nth-last-child(5),
    [data-testid="stSidebarNav"] ul li:nth-last-child(6) { display: none !important; }
</style>
""", unsafe_allow_html=True)

owner_id = None
if is_organizer and not is_admin:
    from app.database.repositories.organizer_repo import OrganizerRepository
    org_repo = OrganizerRepository()
    owner_id = org_repo.get_or_create_organizer(user_info.get("email"), user_info.get("name"))

# Đảm bảo cột branding_config tồn tại
with get_db_session() as sess:
    try:
        sess.execute(text("ALTER TABLE Events ADD COLUMN branding_config JSON"))
        sess.commit()
    except Exception:
        pass # Bỏ qua nếu cột đã tồn tại

# ── Load db ──────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# ── Sidebar filter ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/filter_list: Bộ lọc")
    status_f = st.selectbox(
        "Trạng thái",
        ["Tất cả", "Draft", "Scheduled", "Full", "Completed", "Cancelled"],
        key="ev_status_filter",
    )
    keyword = st.text_input("Tìm theo tên", placeholder="Hội thảo AI...", key="ev_kw")
    st.divider()
    st.caption("📋 Quản lý Sự kiện")

# ── Page header ──────────────────────────────────────────────
c_title, c_btn = st.columns([4, 1])
c_title.markdown("## :material/event: Quản lý Sự kiện")
add_new = c_btn.button("Tạo sự kiện mới", icon=":material/add:", use_container_width=True)

# ── Load data ────────────────────────────────────────────────
sf = None if status_f == "Tất cả" else status_f
with st.spinner("Đang tải dữ liệu..."):
    events = db.events.get_all(status_filter=sf)
    
if owner_id and events:
    events = [e for e in events if e.get("organizer_id") == owner_id]

# Filter by keyword
if keyword and events:
    kw_lower = keyword.lower()
    events = [e for e in events if kw_lower in str(e.get("event_name", "")).lower()]

# ── Summary stats ────────────────────────────────────────────
if events:
    df_ev = pd.DataFrame(events)
    total   = len(events)
    sched   = sum(1 for e in events if e.get("status") == "Scheduled")
    full    = sum(1 for e in events if e.get("status") == "Full")
    comp    = sum(1 for e in events if e.get("status") == "Completed")
    stat_row([
        ("Tổng sự kiện",   total, "blue"),
        ("Scheduled",      sched, "green"),
        ("Full",           full,  "red"),
        ("Completed",      comp,  "gray"),
    ])
    st.markdown("")

# ── TABS ─────────────────────────────────────────────────────
tab_list, tab_detail, tab_edit, tab_delete = st.tabs([
    ":material/list: Danh sách", ":material/info: Chi tiết", ":material/edit: Tạo / Sửa", ":material/delete: Xóa"
])


# ════════════════════════════════════════════════════════════
# TAB 1: DANH SÁCH
# ════════════════════════════════════════════════════════════
with tab_list:
    if not events:
        st.info("Không có sự kiện nào khớp với bộ lọc.")
    else:
        # Hiển thị bảng có badge màu
        display_cols = [
            "event_id", "event_name", "start_time", "end_time",
            "venue_name", "organizer_name", "status",
            "current_registered", "slots_remaining",
        ]
        disp = [{k: r.get(k) for k in display_cols if k in r} for r in events]
        styled_df(disp, badge_cols=["status"], height=420)

        # Download CSV
        csv = pd.DataFrame(events).to_csv(index=False).encode("utf-8")
        st.download_button("Tải CSV", csv, "events.csv", "text/csv", icon=":material/download:")


# ════════════════════════════════════════════════════════════
# TAB 2: CHI TIẾT
# ════════════════════════════════════════════════════════════
with tab_detail:
    section(":material/info:", "Chi tiết sự kiện", "Xem thông tin đầy đủ + KPIs")

    ev_ids = [e["event_id"] for e in events] if events else []
    ev_names = {e["event_id"]: f"#{e['event_id']} — {e['event_name']}" for e in (events or [])}

    if not ev_ids:
        st.info("Không có sự kiện nào.")
    else:
        selected_id = st.selectbox(
            "Chọn sự kiện",
            ev_ids,
            format_func=lambda x: ev_names.get(x, str(x)),
            key="ev_detail_sel",
        )

        with st.spinner():
            raw_ev = db.events.execute_query(f"""
                SELECT e.*, 
                       v.venue_name, v.capacity AS venue_capacity, v.address AS venue_address,
                       o.organizer_name,
                       (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as current_registered,
                       (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id AND r.attendance_status = 'Attended') as total_attended,
                       (SELECT COALESCE(SUM(CASE WHEN f.type='Income' THEN f.amount END),0) - COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) FROM Finances f WHERE f.event_id = e.event_id) AS net_balance
                FROM Events e
                LEFT JOIN Venues v ON e.venue_id = v.venue_id
                LEFT JOIN Organizers o ON e.organizer_id = o.organizer_id
                WHERE e.event_id = {selected_id}
            """)
            
            if raw_ev:
                ev = raw_ev[0]
                reg = ev.get("current_registered") or 0
                attended = ev.get("total_attended") or 0
                ev["attendance_rate_pct"] = (attended / reg * 100) if reg > 0 else 0
                if ev.get("max_capacity"):
                    ev["slots_remaining"] = ev["max_capacity"] - reg
                else:
                    ev["slots_remaining"] = None
            else:
                ev = db.events.get_by_id(selected_id)
                if ev:
                    ev["attendance_rate_pct"] = 0
                    ev["net_balance"] = 0
                    ev["slots_remaining"] = ev.get("max_capacity")

        if ev:
            # KPI row
            rate = float(ev.get("attendance_rate_pct") or 0)
            bal  = float(ev.get("net_balance") or 0)
            slots = ev.get("slots_remaining")
            reg   = ev.get("current_registered") or 0

            stat_row([
                ("Đã đăng ký",     reg,   "blue"),
                ("Tỉ lệ tham dự",  f"{rate:.1f}%",  "green" if rate >= 60 else "amber"),
                ("Số dư tài chính", f"{bal/1e6:+.1f}M VND", "green" if bal >= 0 else "red"),
                ("Chỗ còn trống",  "∞" if slots is None else slots, "gray"),
            ])
            st.markdown("")

            c1, c2 = st.columns(2)
            c1.markdown(f"**Tên:** {ev['event_name']}")
            c1.markdown(f"**Bắt đầu:** {ev['start_time']}")
            c1.markdown(f"**Kết thúc:** {ev['end_time']}")
            c1.markdown(f"**Trạng thái:** {badge(ev['status'])}", unsafe_allow_html=True)
            c2.markdown(f"**Địa điểm:** {ev.get('venue_name','—')}")
            c2.markdown(f"**Sức chứa venue:** {ev.get('venue_capacity','—')}")
            c2.markdown(f"**Ban tổ chức:** {ev.get('organizer_name','—')}")
            c2.markdown(f"**Mô tả:** {ev.get('description') or '—'}")
            
            if ev.get("image_url"):
                st.image(ev["image_url"], use_container_width=True)

            # --- MÃ QR CHECK-IN / CHECK-OUT ---
            st.divider()
            st.markdown("### :material/qr_code_scanner: Mã QR Điểm danh Sự kiện")
            st.info("Ban tổ chức có thể in mã QR này và đặt tại bàn tiếp đón. Khách mời hoặc nhân viên có thể sử dụng ứng dụng quét để điểm danh nhanh chóng.")
            
            c_qr1, c_qr2 = st.columns(2)
            # Tạo URL chứa QR thông qua API miễn phí
            ci_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=CHECKIN_EVENT_{selected_id}"
            co_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=CHECKOUT_EVENT_{selected_id}"
            
            with c_qr1:
                with st.container(border=True):
                    st.markdown("<h4 style='text-align: center; color: #10b981;'>📥 MÃ CHECK-IN</h4>", unsafe_allow_html=True)
                    _, c_img1, _ = st.columns([1, 2, 1])
                    c_img1.image(ci_url, use_container_width=True)
                    st.caption(f"<div style='text-align: center'>Dữ liệu: CHECKIN_EVENT_{selected_id}</div>", unsafe_allow_html=True)
                    
            with c_qr2:
                with st.container(border=True):
                    st.markdown("<h4 style='text-align: center; color: #ef4444;'>📤 MÃ CHECK-OUT</h4>", unsafe_allow_html=True)
                    _, c_img2, _ = st.columns([1, 2, 1])
                    c_img2.image(co_url, use_container_width=True)
                    st.caption(f"<div style='text-align: center'>Dữ liệu: CHECKOUT_EVENT_{selected_id}</div>", unsafe_allow_html=True)

            # Registrations sub-table
            st.divider()
            st.markdown("**Danh sách đăng ký của sự kiện này:**")
            regs = db.registrations.get_by_event(selected_id)
            if regs:
                disp_r = [{"Tên khách": r["guest_name"],
                            "Email": r["email"],
                            "Ngày ĐK": r["registration_date"],
                            "Trạng thái": r["attendance_status"],
                            "Check-in": r.get("checkin_time") or "—"} for r in regs]
                styled_df(disp_r, badge_cols=["Trạng thái"], height=220)
            else:
                st.info("Chưa có đăng ký nào.")
                
            # Nút điều hướng nhanh sang trang Khách mời / Đăng ký
            st.markdown("---")
            if st.button("👉 Quản lý Khách mời, Đăng ký & Check-in cho Sự kiện này", type="primary", use_container_width=True):
                # Lưu event_id vào session để sang trang kia tự động chọn
                st.session_state["reg_event_sel"] = selected_id
                st.switch_page("pages/4_Đăng_ký_và_Check_in.py")


# ════════════════════════════════════════════════════════════
# TAB 3: TẠO / SỬA
# ════════════════════════════════════════════════════════════
with tab_edit:
    mode = st.radio("Chế độ", ["Tạo mới", "Sửa sự kiện"], horizontal=True, key="ev_mode")
    
    # Load venues + organizers for selects
    venues_q = db.events.execute_query("SELECT venue_id, venue_name, capacity FROM Venues ORDER BY venue_name") or []
    orgs_q   = db.events.execute_query("SELECT organizer_id, organizer_name FROM Organizers ORDER BY organizer_name") or []
    if owner_id:
        orgs_q = [o for o in orgs_q if o["organizer_id"] == owner_id]
    v_map = {r["venue_name"]: r["venue_id"] for r in venues_q}
    o_map = {r["organizer_name"]: r["organizer_id"] for r in orgs_q}

    # Prefill if editing
    prefill: dict = {}
    if mode.startswith("Sửa") and ev_ids:
        edit_id = st.selectbox(
            "Sự kiện cần sửa",
            ev_ids, format_func=lambda x: ev_names.get(x, str(x)),
            key="ev_edit_sel",
        )
        raw = db.events.get_by_id(edit_id) or {}
        prefill = raw

    with st.form("form_event", clear_on_submit=(mode.startswith("Tạo"))):
        section(":material/edit_note:", "Thông tin sự kiện")
        name = st.text_input(
            "Tên sự kiện *",
            value=prefill.get("event_name", ""),
        )

        c1, c2 = st.columns(2)
        # Parse datetimes for prefill
        default_start = date.today() + timedelta(days=14)
        default_end   = date.today() + timedelta(days=14)
        try:
            if prefill.get("start_time"):
                dt_s = pd.to_datetime(prefill["start_time"])
                default_start = dt_s.date()
                default_st = dt_s.time()
            else:
                from datetime import time
                default_st = time(8, 0)
            if prefill.get("end_time"):
                dt_e = pd.to_datetime(prefill["end_time"])
                default_end = dt_e.date()
                default_et = dt_e.time()
            else:
                from datetime import time
                default_et = time(17, 0)
        except Exception:
            from datetime import time
            default_st = time(8, 0)
            default_et = time(17, 0)

        sd   = c1.date_input("Ngày bắt đầu *", value=default_start)
        st_t = c1.time_input("Giờ bắt đầu *",  value=default_st)
        ed   = c2.date_input("Ngày kết thúc *", value=default_end)
        et_t = c2.time_input("Giờ kết thúc *",  value=default_et)

        c3, c4 = st.columns(2)
        # Find current venue/org name for default
        cur_venue = next((r["venue_name"] for r in venues_q if r["venue_id"] == prefill.get("venue_id")), None)
        cur_org   = next((r["organizer_name"] for r in orgs_q  if r["organizer_id"] == prefill.get("organizer_id")), None)

        v_options = list(v_map.keys())
        o_options = list(o_map.keys())
        v_idx = v_options.index(cur_venue) if cur_venue in v_options else 0
        o_idx = o_options.index(cur_org)   if cur_org in o_options   else 0

        v_sel = c3.selectbox("Địa điểm *", v_options, index=v_idx)
        o_sel = c4.selectbox("Ban tổ chức *", o_options, index=o_idx)

        c5, c6 = st.columns(2)
        status_opts = ["Draft", "Scheduled", "Full", "Completed", "Cancelled"]
        cur_status = prefill.get("status", "Draft")
        s_idx = status_opts.index(cur_status) if cur_status in status_opts else 0
        status_v = c5.selectbox("Trạng thái", status_opts, index=s_idx)
        max_cap  = c6.number_input(
            "Sức chứa tối đa (0=không giới hạn)",
            min_value=0, step=10,
            value=int(prefill.get("max_capacity") or 0),
        )
        img_url = st.text_input("Link ảnh minh họa (URL)", value=prefill.get("image_url") or "", placeholder="Ví dụ: https://images.unsplash.com/...")
        desc = st.text_area("Mô tả", value=prefill.get("description") or "")
        
        st.markdown("---")
        section(":material/palette:", "Tùy chỉnh Giao diện (Branding)")
        branding_conf = {}
        if prefill.get("branding_config"):
            try:
                branding_conf = json.loads(prefill["branding_config"])
            except (json.JSONDecodeError, TypeError):
                branding_conf = {}
        c_brand1, c_brand2, c_brand3 = st.columns(3)
        p_color = c_brand1.color_picker("Màu chủ đạo", value=branding_conf.get("primary_color", "#FF4B4B"))
        bg_color = c_brand2.color_picker("Màu nền trang", value=branding_conf.get("background_color", "#F8F9FA"))
        txt_color = c_brand3.color_picker("Màu chữ", value=branding_conf.get("text_color", "#212529"))
        banner_url = st.text_input("Link ảnh bìa (Banner URL)", value=branding_conf.get("banner_url", ""), placeholder="https://example.com/banner.jpg")

        btn_label = "Tạo sự kiện" if mode.startswith("Tạo") else "Lưu thay đổi"
        btn_icon = ":material/add:" if mode.startswith("Tạo") else ":material/save:"
        submitted = st.form_submit_button(btn_label, icon=btn_icon, use_container_width=True)

    if submitted:
        if not name or not v_options or not o_options:
            show_error("Điền đầy đủ thông tin bắt buộc.")
        else:
            branding_config_dict = {
                "primary_color": p_color,
                "background_color": bg_color,
                "text_color": txt_color,
                "banner_url": banner_url,
                "font_family": "'Inter', sans-serif"
            }
            branding_config_json = json.dumps(branding_config_dict, ensure_ascii=False)
            try:
                data = EventCreate(
                    event_name=name,
                    start_time=datetime.combine(sd, st_t),
                    end_time=datetime.combine(ed, et_t),
                    venue_id=v_map[v_sel],
                    organizer_id=o_map[o_sel],
                    status=status_v,
                    max_capacity=int(max_cap) if max_cap > 0 else None,
                    description=desc or None,
                )
                if mode.startswith("Tạo"):
                    event_id_to_update = None
                    new_id = db.events.create(data)
                    event_id_to_update = new_id
                    show_success(f"Đã tạo sự kiện '{name}' (ID: {new_id})!")
                else:
                    db.events.update(edit_id, data)
                    event_id_to_update = edit_id
                    show_success(f"Đã cập nhật sự kiện #{edit_id}!")
                
                if event_id_to_update:
                    with get_db_session() as sess:
                        sess.execute(text("UPDATE Events SET image_url = :img, branding_config = :brand WHERE event_id = :id"), 
                                     {"img": img_url if img_url else None, "brand": branding_config_json, "id": event_id_to_update})
                st.rerun()
            except Exception as e:
                show_error(f"Lỗi: {e}")


# ════════════════════════════════════════════════════════════
# TAB 4: XÓA
# ════════════════════════════════════════════════════════════
with tab_delete:
    section(":material/delete:", "Xóa sự kiện", "Xóa sẽ cascade xóa toàn bộ đăng ký và tài chính liên quan")

    if not ev_ids:
        st.info("Không có sự kiện nào.")
    else:
        del_id = st.selectbox(
            "Chọn sự kiện cần xóa",
            ev_ids, format_func=lambda x: ev_names.get(x, str(x)),
            key="ev_del_sel",
        )
        ev_del = db.events.get_by_id(del_id)
        if ev_del:
            st.warning(
                f"⚠️ Bạn sắp xóa: **{ev_del['event_name']}**\n\n"
                f"Hành động này sẽ xóa cascade tất cả đăng ký và giao dịch tài chính liên quan!"
            )
            col1, col2 = st.columns([1, 3])
            confirm = col1.checkbox("Tôi xác nhận muốn xóa", key="confirm_del_ev")
            if col2.button("Xóa vĩnh viễn", icon=":material/delete_forever:", disabled=not confirm):
                with st.spinner("Đang xóa..."):
                    db.events.delete(del_id)
                show_success(f"Đã xóa sự kiện #{del_id}!")
                st.rerun()

# ── Floating "Tạo mới" shortcut ──────────────────────────────
if add_new:
    st.session_state["ev_mode"] = "Tạo mới"
    st.rerun()
