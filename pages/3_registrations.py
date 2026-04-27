"""
pages/3_registrations.py
Trang Đăng ký & Check-in — gọi Stored Procedures, per-row check-in button
"""

import streamlit as st
import pandas as pd
from datetime import date

from app.database import DatabaseManager
from app.ui.components import (
    badge, section, stat_row, styled_df, show_success, show_error,
)
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Đăng ký & Check-in | EMS", page_icon="✅", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# ── Page header ──────────────────────────────────────────────
st.markdown("## :material/how_to_reg: Đăng ký & Check-in")

# ── Chọn sự kiện (dùng toàn trang) ─────────────────────────
with st.spinner("Đang tải sự kiện..."):
    events = db.events.get_all() or []

ev_map = {e["event_id"]: f"#{e['event_id']} {e['event_name']} [{e.get('status','')}]"
          for e in events}

if not ev_map:
    st.warning("Chưa có sự kiện nào. Tạo sự kiện trước.")
    st.stop()

col_sel, col_refresh = st.columns([4, 1])
selected_event_id = col_sel.selectbox(
    "Chọn sự kiện",
    list(ev_map.keys()),
    format_func=lambda x: ev_map[x],
    key="reg_event_sel",
)
if col_refresh.button("Làm mới", icon=":material/refresh:", use_container_width=True):
    st.rerun()

# Load stats for selected event
with st.spinner():
    ev_detail = db.events.get_by_id(selected_event_id) or {}
    regs      = db.registrations.get_by_event(selected_event_id)
    stats_ev  = db.registrations.count_by_event(selected_event_id)

# ── KPI row ──────────────────────────────────────────────────
stat_row([
    ("Tổng đăng ký",   stats_ev.get("total", 0),      "blue"),
    ("Registered",     stats_ev.get("registered", 0),  "purple"),
    ("Attended ✓",     stats_ev.get("attended", 0),    "green"),
    ("No-show ✗",      stats_ev.get("noshow", 0),      "red"),
    ("Tỉ lệ tham dự",  f"{float(stats_ev.get('rate_pct') or 0):.1f}%",
                                                        "amber"),
])
st.markdown("")

# ── TABS ─────────────────────────────────────────────────────
tab_list, tab_register, tab_checkin, tab_bulk, tab_cancel = st.tabs([
    ":material/list: Danh sách đăng ký",
    ":material/person_add: Đăng ký mới",
    ":material/check_circle: Check-in",
    ":material/block: No-show hàng loạt",
    ":material/delete: Hủy đăng ký",
])


# ════════════════════════════════════════════════════════════
# TAB 1: DANH SÁCH
# ════════════════════════════════════════════════════════════
with tab_list:
    if not regs:
        st.info("Sự kiện này chưa có đăng ký nào.")
    else:
        # Filter by status
        status_opts = ["Tất cả", "Registered", "Attended", "No-show"]
        sf = st.selectbox("Lọc trạng thái", status_opts, key="reg_sf")

        filtered = regs if sf == "Tất cả" else [r for r in regs if r.get("attendance_status") == sf]

        # Render with per-row check-in button
        section("list", f"Danh sách — {ev_detail.get('event_name','')}", f"{len(filtered)} khách")

        if filtered:
            for reg in filtered:
                status = reg.get("attendance_status", "")
                c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
                c1.markdown(f"**{reg['guest_name']}**")
                c2.markdown(reg.get("email", ""))
                c3.markdown(badge(status), unsafe_allow_html=True)
                c4.markdown(
                    str(reg.get("checkin_time") or "—"),
                    help="Thời gian check-in"
                )
                # Per-row check-in button (chỉ cho Registered)
                if status == "Registered":
                    if c5.button("Check-in", icon=":material/check_circle:", key=f"ci_{reg['guest_id']}_{selected_event_id}"):
                        result = db.checkin_guest(selected_event_id, reg["guest_id"])
                        if result.success:
                            show_success(result.message)
                            st.rerun()
                        else:
                            show_error(result.message)
                elif status == "Attended":
                    c5.markdown("<span class='material-symbols-rounded' style='color:#10b981;font-size:1rem;vertical-align:middle;'>check_circle</span> Done", unsafe_allow_html=True)

            st.divider()
            csv = pd.DataFrame(regs).to_csv(index=False).encode("utf-8")
            st.download_button("Tải CSV", csv,
                               f"registrations_event_{selected_event_id}.csv", "text/csv", icon=":material/download:")


# ════════════════════════════════════════════════════════════
# TAB 2: ĐĂNG KÝ MỚI
# ════════════════════════════════════════════════════════════
with tab_register:
    section(
        "person_add", "Đăng ký khách tham dự",
        "Gọi sp_register_guest — tự kiểm tra trùng lặp, capacity, trạng thái"
    )

    # Load guests for quick search
    all_guests = db.guests.search("") if not hasattr(st.session_state, "_guests_cache") else []
    all_guests = db.guests.execute_query(
        "SELECT guest_id, guest_name, email FROM Guests ORDER BY guest_name LIMIT 200"
    ) or []
    guest_map = {g["guest_id"]: f"#{g['guest_id']} {g['guest_name']} ({g['email']})"
                 for g in all_guests}

    with st.form("form_register", clear_on_submit=False):
        section_inner = st.empty()

        if guest_map:
            sel_guest = st.selectbox(
                "Chọn khách *",
                list(guest_map.keys()),
                format_func=lambda x: guest_map.get(x, str(x)),
                key="reg_guest_sel",
            )
        else:
            sel_guest = st.number_input("Guest ID *", min_value=1, step=1)

        st.info(f"Sẽ đăng ký vào: **{ev_detail.get('event_name', '')}**")

        submitted_reg = st.form_submit_button(
            "Đăng ký ngay [sp_register_guest]",
            icon=":material/app_registration:",
            use_container_width=True,
        )

    if submitted_reg:
        with st.spinner("Đang gọi sp_register_guest..."):
            result = db.register_guest(selected_event_id, int(sel_guest))
        if result.success:
            show_success(result.message)
            st.rerun()
        else:
            show_error(result.message)

    # Đăng ký thủ công bằng Guest ID
    st.divider()
    st.markdown("**Hoặc nhập Guest ID trực tiếp:**")
    c1, c2 = st.columns([2, 1])
    manual_gid = c1.number_input("Guest ID", min_value=1, step=1, key="reg_manual_gid")
    if c2.button("Đăng ký", icon=":material/app_registration:", key="reg_manual_btn", use_container_width=True):
        with st.spinner("Đang gọi sp_register_guest..."):
            result = db.register_guest(selected_event_id, int(manual_gid))
        if result.success:
            show_success(result.message)
            st.rerun()
        else:
            show_error(result.message)


# ════════════════════════════════════════════════════════════
# TAB 3: CHECK-IN
# ════════════════════════════════════════════════════════════
with tab_checkin:
    section(
        "check_circle", "Check-in khách",
        "Gọi sp_guest_checkin — cập nhật attendance_status + ghi checkin_time"
    )

    # Hiển thị danh sách chờ check-in
    pending = db.registrations.get_pending_checkin(selected_event_id)
    if pending:
        st.markdown(f"**{len(pending)} khách chưa check-in:**")

        # Quick check-in table
        for p in pending:
            c1, c2, c3 = st.columns([3, 3, 1])
            c1.markdown(f"**{p['guest_name']}**")
            c2.markdown(p.get("email", ""))
            if c3.button("Check-in", icon=":material/check_circle:", key=f"qci_{p['guest_id']}", help="Check-in ngay"):
                result = db.checkin_guest(selected_event_id, p["guest_id"])
                if result.success:
                    show_success(f"Check-in: {p['guest_name']}")
                    st.rerun()
                else:
                    show_error(result.message)
        st.divider()
    else:
        st.success("🎉 Tất cả khách đã check-in hoặc không có khách nào!")

    # Manual check-in form
    st.markdown("**Check-in theo Guest ID:**")
    c1, c2 = st.columns([2, 1])
    ci_gid = c1.number_input("Guest ID", min_value=1, step=1, key="ci_manual_gid")
    if c2.button("Check-in", icon=":material/check_circle:", use_container_width=True, key="ci_manual_btn"):
        with st.spinner("Đang gọi sp_guest_checkin..."):
            result = db.checkin_guest(selected_event_id, int(ci_gid))
        if result.success:
            show_success(result.message)
            st.rerun()
        else:
            show_error(result.message)


# ════════════════════════════════════════════════════════════
# TAB 4: NO-SHOW HÀNG LOẠT
# ════════════════════════════════════════════════════════════
with tab_bulk:
    section("block", "Đánh dấu No-show hàng loạt",
            "Dùng sau khi sự kiện kết thúc — tất cả 'Registered' chưa check-in sẽ thành No-show")

    pending_count = stats_ev.get("registered", 0)
    if pending_count == 0:
        st.success("Không có khách nào đang ở trạng thái Registered.")
    else:
        st.warning(
            f"⚠️ {pending_count} khách đang ở trạng thái 'Registered' "
            f"sẽ bị chuyển thành 'No-show'."
        )
        confirm_ns = st.checkbox("Xác nhận đánh dấu No-show hàng loạt", key="confirm_noshow")
        if st.button("Thực hiện No-show", icon=":material/block:", disabled=not confirm_ns):
            with st.spinner("Đang cập nhật..."):
                rows = db.registrations.mark_noshow_bulk(selected_event_id)
            show_success(f"Đã đánh dấu {rows} khách là No-show.")
            st.rerun()

    st.divider()
    section("flag", "Kết thúc sự kiện", "Gọi sp_mark_event_completed — tự động No-show + cập nhật status")
    confirm_done = st.checkbox("Xác nhận kết thúc sự kiện", key="confirm_done_ev")
    if st.button("Kết thúc sự kiện [sp_mark_event_completed]", icon=":material/flag:", disabled=not confirm_done):
        with st.spinner("Đang gọi sp_mark_event_completed..."):
            result = db.complete_event(selected_event_id)
        if result.success:
            show_success(result.message)
            st.rerun()
        else:
            show_error(result.message)


# ════════════════════════════════════════════════════════════
# TAB 5: HỦY ĐĂNG KÝ
# ════════════════════════════════════════════════════════════
with tab_cancel:
    section("delete", "Hủy đăng ký", "Xóa hoàn toàn bản ghi đăng ký")

    if not regs:
        st.info("Không có đăng ký nào để hủy.")
    else:
        reg_map = {r["registration_id"]:
                   f"#{r['registration_id']} — {r['guest_name']} [{r['attendance_status']}]"
                   for r in regs}
        cancel_id = st.selectbox(
            "Chọn đăng ký cần hủy",
            list(reg_map.keys()),
            format_func=lambda x: reg_map[x],
            key="cancel_reg_sel",
        )
        sel_reg = next((r for r in regs if r["registration_id"] == cancel_id), None)
        if sel_reg:
            st.info(
                f"Khách: **{sel_reg['guest_name']}** | "
                f"Trạng thái: **{sel_reg['attendance_status']}**"
            )

        confirm_c = st.checkbox("Xác nhận hủy đăng ký này", key="confirm_cancel_reg")
        if st.button("Hủy đăng ký", icon=":material/delete:", disabled=not confirm_c):
            rows = db.registrations.cancel_by_id(cancel_id)
            if rows:
                show_success(f"Đã hủy đăng ký #{cancel_id}!")
                st.rerun()
            else:
                show_error("Không tìm thấy đăng ký.")
