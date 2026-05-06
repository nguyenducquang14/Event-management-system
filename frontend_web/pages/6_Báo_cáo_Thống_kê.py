"""
pages/5_reports.py
Trang Báo cáo & Thống kê — biểu đồ, xuất Excel, top guests, venue usage
"""

import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

from app.database import DatabaseManager
from app.ui.components import section, stat_row, styled_df, show_success
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Báo cáo | EMS", page_icon="📊", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# 1. BỨC TƯỜNG LỬA
if "token" not in st.session_state or "user_info" not in st.session_state:
    st.warning("Vui lòng đăng nhập để truy cập!")
    st.stop()

user_info = st.session_state["user_info"]
roles = user_info.get("roles", [])
is_admin = "Admin" in roles
is_organizer = "Organizer" in roles

if not is_admin and not is_organizer:
    st.error("Lỗi 403: Cấm truy cập. Khu vực này dành riêng cho Ban tổ chức và Admin.")
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

@st.cache_resource
def get_engine():
    from app.config import engine
    return engine

db  = get_db()
eng = get_engine()

st.markdown("## :material/analytics: Báo cáo & Thống kê")

# ── Load dashboard stats ─────────────────────────────────────
with st.spinner("Đang tải số liệu..."):
    if owner_id:
        my_summary = db.events.execute_query(f"SELECT * FROM view_event_summary WHERE event_id IN (SELECT event_id FROM Events WHERE organizer_id = {owner_id})") or []
        counts = db.events.execute_query(f"""
            SELECT 
                COUNT(DISTINCT r.guest_id) as total_guests,
                COUNT(r.registration_id) as total_registrations,
                SUM(r.attendance_status = 'Attended') as total_attended
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            WHERE e.organizer_id = {owner_id}
        """)
        class DummyStats:
            total_events = len(my_summary)
            total_guests = counts[0].get("total_guests") if counts and counts[0] else 0
            total_registrations = int(counts[0].get("total_registrations") or 0) if counts and counts[0] else 0
            total_attended = int(counts[0].get("total_attended") or 0) if counts and counts[0] else 0
            total_income = sum(float(s["total_income"] or 0) for s in my_summary)
            total_expense = sum(float(s["total_expense"] or 0) for s in my_summary)
            net_balance = total_income - total_expense
        stats = DummyStats()
        summary = my_summary
    else:
        stats = db.get_dashboard_stats()
        summary = db.events.get_summary()

stat_row([
    ("Tổng sự kiện",    stats.total_events,        "blue"),
    ("Tổng khách",      stats.total_guests,         "purple"),
    ("Tổng đăng ký",    stats.total_registrations,  "teal"),
    ("Đã tham dự",      stats.total_attended,        "green"),
    ("Tỉ lệ TB",
     f"{(stats.total_attended / stats.total_registrations * 100 if stats.total_registrations else 0):.1f}%",
     "amber"),
])
st.markdown("")

# ── TABS ─────────────────────────────────────────────────────
(tab_event, tab_guest, tab_venue,
 tab_finance, tab_period, tab_excel) = st.tabs([
    ":material/event: Sự kiện", ":material/emoji_events: Top khách", ":material/apartment: Địa điểm",
    ":material/payments: Tài chính", ":material/calendar_month: Báo cáo kỳ", ":material/download: Xuất Excel",
])


# ════════════════════════════════════════════════════════════
# TAB 1: SỰ KIỆN
# ════════════════════════════════════════════════════════════
with tab_event:
    section("bar_chart", "Thống kê tổng hợp sự kiện")

    if not summary:
        st.info("Chưa có dữ liệu.")
    else:
        df_s = pd.DataFrame(summary)
        avg_rate = float(df_s["attendance_rate_pct"].mean() or 0)

        c_gauge, c_empty = st.columns([1, 2])

        # Gauge chart
        with c_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_rate,
                title={"text": "Tỉ lệ tham dự TB (%)", "font": {"color": "#000000"}},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"color": "#000000"}},
                    "bar":  {"color": "#6366f1"},
                    "steps": [
                        {"range": [0,  40], "color": "#fee2e2"},
                        {"range": [40, 70], "color": "#fef3c7"},
                        {"range": [70,100], "color": "#d1fae5"},
                    ],
                    "threshold": {"line": {"color": "#ef4444", "width": 3},
                                  "thickness": 0.75, "value": avg_rate},
                },
                number={"suffix": "%", "font": {"size": 36, "color": "#000000"}},
            ))
            fig_gauge.update_layout(
                height=240,
                margin=dict(l=20, r=20, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#000000"),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Stacked bar: Attended + No-show
        st.markdown("#### Biểu đồ Thống kê Đăng ký & Tham dự")
        fig_bar = go.Figure()
        names = df_s["event_name"].str[:25]
        fig_bar.add_bar(
            name="Attended", x=names,
            y=df_s["total_attended"].astype(float),
            marker_color="#6366f1",
        )
        fig_bar.add_bar(
            name="No-show",  x=names,
            y=df_s["total_noshow"].astype(float),
            marker_color="#f87171",
        )
        fig_bar.add_bar(
            name="Registered", x=names,
            y=df_s["total_registered"].fillna(0).astype(float)
               - df_s["total_attended"].astype(float)
               - df_s["total_noshow"].astype(float),
            marker_color="#c7d2fe",
        )
        fig_bar.update_traces(textfont_color="#000000")
        fig_bar.update_layout(
            barmode="stack", height=350,
            legend=dict(orientation="h", y=-0.2, font=dict(color="#000000")),
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000")),
            yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        styled_df(summary, height=300)


# ════════════════════════════════════════════════════════════
# TAB 2: TOP KHÁCH
# ════════════════════════════════════════════════════════════
with tab_guest:
    section("emoji_events", "Top khách tích cực nhất")

    col_sl, col_sort = st.columns([2, 2])
    top_n    = col_sl.slider("Hiển thị top", 5, 50, 15, key="rpt_top_n")
    sort_by  = col_sort.selectbox("Sắp xếp theo",
                                  ["total_registrations", "total_attended", "personal_rate_pct"],
                                  key="rpt_sort")

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
                ORDER BY {sort_by} DESC
                LIMIT {top_n}
            """) or []
        else:
            activity = db.guests.get_activity(limit=top_n)

    if activity:
        df_a = pd.DataFrame(activity)
        df_a = df_a.sort_values(sort_by, ascending=False)

        # Horizontal bar chart
        fig_h = px.bar(
            df_a, y="guest_name", x="total_attended",
            orientation="h",
            color="personal_rate_pct",
            color_continuous_scale="Viridis",
            labels={"guest_name": "Khách", "total_attended": "Đã tham dự",
                    "personal_rate_pct": "Tỉ lệ (%)"},
            height=max(300, top_n * 28),
        )
        fig_h.update_traces(textfont_color="#000000")
        fig_h.update_layout(
            margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
            yaxis=dict(autorange="reversed"),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
            coloraxis_colorbar=dict(
                titlefont=dict(color="#000000"),
                tickfont=dict(color="#000000")
            )
        )
        st.plotly_chart(fig_h, use_container_width=True)

        styled_df(activity, height=300)

        csv = df_a.to_csv(index=False).encode("utf-8")
        st.download_button("Tải CSV", csv, "top_guests.csv", "text/csv", icon=":material/download:")


# ════════════════════════════════════════════════════════════
# TAB 3: ĐỊA ĐIỂM
# ════════════════════════════════════════════════════════════
with tab_venue:
    section("apartment", "Thống kê sử dụng địa điểm")

    with st.spinner():
        if owner_id:
            venues = db.events.execute_query(f"""
                SELECT v.venue_id, v.venue_name, v.capacity, v.availability_status,
                       COUNT(e.event_id) AS total_events,
                       SUM(e.status = 'Completed') AS completed_events
                FROM Venues v
                JOIN Events e ON v.venue_id = e.venue_id
                WHERE e.organizer_id = {owner_id}
                GROUP BY v.venue_id, v.venue_name, v.capacity, v.availability_status
            """) or []
        else:
            venues = db.events.execute_query("SELECT * FROM view_venue_usage") or []

    if venues:
        df_v = pd.DataFrame(venues)
        
        # Bar chart: venue vs total events
        fig_bar_v = px.bar(
            df_v,
            x="venue_name", y="total_events",
            color="availability_status",
            labels={"venue_name": "Địa điểm", "total_events": "Số sự kiện", "availability_status": "Trạng thái"},
            height=380,
            title="Số lượng sự kiện theo địa điểm",
        )
        fig_bar_v.update_traces(textfont_color="#000000")
        fig_bar_v.update_layout(
            margin=dict(l=0, r=0, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000")),
            yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
            legend=dict(font=dict(color="#000000")),
            title=dict(font=dict(color="#000000")),
        )
        st.plotly_chart(fig_bar_v, use_container_width=True)

        styled_df(venues, badge_cols=["availability_status"], height=280)
    else:
        st.info("Chưa có dữ liệu địa điểm.")


# ════════════════════════════════════════════════════════════
# TAB 4: TÀI CHÍNH
# ════════════════════════════════════════════════════════════
with tab_finance:
    section("payments", "Báo cáo tài chính tổng hợp")

    with st.spinner():
        if owner_id:
            fin_balance = db.events.execute_query(f"""
                SELECT e.event_id, e.event_name, 
                       COALESCE(SUM(CASE WHEN f.type='Income' THEN f.amount END),0) as total_income,
                       COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) as total_expense,
                       COALESCE(SUM(CASE WHEN f.type='Income' THEN f.amount END),0) - COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) as net_balance
                FROM Events e
                LEFT JOIN Finances f ON e.event_id = f.event_id
                WHERE e.organizer_id = {owner_id}
                GROUP BY e.event_id, e.event_name
                HAVING total_income > 0 OR total_expense > 0
            """) or []
        else:
            fin_balance = db.finances.get_balance_all()

    if fin_balance:
        df_bal = pd.DataFrame(fin_balance)

        # Bar chart: net balance per event
        colors = ["#34d399" if float(v) >= 0 else "#f87171" for v in df_bal["net_balance"]]
        fig_bal_bar = go.Figure(go.Bar(
            x=df_bal["event_name"].str[:18],
            y=df_bal["net_balance"].astype(float),
            marker_color=colors,
            text=df_bal["net_balance"].astype(float).apply(lambda x: f"{x/1e6:+.1f}M"),
            textposition="auto"
        ))
        fig_bal_bar.update_traces(textfont_color="#000000")
        fig_bal_bar.update_layout(
            title=dict(text="Số dư ròng theo sự kiện", font=dict(color="#000000")),
            height=380,
            margin=dict(l=0, r=0, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000")),
            yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
        )
        st.plotly_chart(fig_bal_bar, use_container_width=True)

        styled_df(fin_balance, height=260)
    else:
        st.info("Chưa có giao dịch tài chính nào.")


# ════════════════════════════════════════════════════════════
# TAB 5: BÁO CÁO KỲ
# ════════════════════════════════════════════════════════════
with tab_period:
    section("calendar_month", "Báo cáo sự kiện theo khoảng thời gian",
            "Gọi sp_event_report")

    col1, col2, col3 = st.columns([2, 2, 1])
    from_d = col1.date_input("Từ ngày", value=date.today() - timedelta(days=180))
    to_d   = col2.date_input("Đến ngày", value=date.today() + timedelta(days=180))
    run    = col3.button("Xem", icon=":material/search:", use_container_width=True, key="rpt_period_btn")

    if run:
        with st.spinner("Đang truy xuất dữ liệu..."):
            if owner_id:
                rows = db.events.execute_query(f"""
                    SELECT event_name, start_time, status, venue_name,
                           total_registered, total_attended, attendance_rate_pct,
                           total_income, total_expense, net_balance
                    FROM view_event_summary
                    WHERE event_id IN (SELECT event_id FROM Events WHERE organizer_id = {owner_id})
                    AND DATE(start_time) BETWEEN '{from_d}' AND '{to_d}'
                    ORDER BY start_time
                """) or []
            else:
                rows = db.get_event_report(str(from_d), str(to_d))
        if rows:
            df_r = pd.DataFrame(rows)
            st.caption(f"Tìm thấy {len(rows)} sự kiện từ {from_d} đến {to_d}")
            styled_df(rows, height=350)

            # Mini charts
            if "total_attended" in df_r.columns:
                fig_mini = px.bar(
                    df_r, x="event_name", y=["total_registered","total_attended"],
                    barmode="overlay", height=260,
                    labels={"event_name":"Sự kiện","value":"Số người"},
                )
                fig_mini.update_traces(textfont_color="#000000")
                fig_mini.update_layout(
                    margin=dict(l=0,r=0,t=10,b=10), 
                    xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000")),
                    yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)", 
                    legend=dict(orientation="h", y=-0.4, font=dict(color="#000000")),
                    font=dict(color="#000000"),
                    hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
                )
                st.plotly_chart(fig_mini, use_container_width=True)

            csv = df_r.to_csv(index=False).encode("utf-8")
            st.download_button("Tải CSV kỳ này", csv, f"report_{from_d}_{to_d}.csv", "text/csv", icon=":material/download:")
        else:
            st.info("Không có sự kiện nào trong khoảng này.")


# ════════════════════════════════════════════════════════════
# TAB 6: XUẤT EXCEL
# ════════════════════════════════════════════════════════════
with tab_excel:
    section("download", "Xuất báo cáo Excel (.xlsx)", "Chọn sheet, tạo file và tải về ngay")
    from sqlalchemy import text as sqlt

    if owner_id:
        SHEET_QUERIES = {
            "📋 Tổng hợp sự kiện":   f"SELECT * FROM view_event_summary WHERE event_id IN (SELECT event_id FROM Events WHERE organizer_id = {owner_id})",
            "💰 Báo cáo tài chính":  f"SELECT * FROM view_finance_report WHERE event_id IN (SELECT event_id FROM Events WHERE organizer_id = {owner_id})",
            "👥 Danh sách khách":    f"SELECT DISTINCT g.guest_id, g.guest_name, g.email, g.phone_number, g.address, g.created_at FROM Guests g JOIN Registrations r ON g.guest_id = r.guest_id JOIN Events e ON r.event_id = e.event_id WHERE e.organizer_id = {owner_id}",
            "🏢 Địa điểm":           f"SELECT v.venue_name, COUNT(e.event_id) as total_events FROM Venues v JOIN Events e ON v.venue_id = e.venue_id WHERE e.organizer_id = {owner_id} GROUP BY v.venue_name",
            "✅ Đăng ký (an toàn)":  f"SELECT * FROM v_safe_registrations WHERE event_name IN (SELECT event_name FROM Events WHERE organizer_id = {owner_id})",
            "🏆 Top khách":          f"SELECT g.guest_name, g.email, COUNT(r.event_id) AS total_reg, SUM(r.attendance_status='Attended') AS total_attended FROM Guests g JOIN Registrations r ON g.guest_id=r.guest_id JOIN Events e ON r.event_id = e.event_id WHERE e.organizer_id = {owner_id} GROUP BY g.guest_id ORDER BY total_reg DESC",
        }
    else:
        SHEET_QUERIES = {
            "📋 Tổng hợp sự kiện":   "SELECT * FROM view_event_summary",
            "💰 Báo cáo tài chính":  "SELECT * FROM view_finance_report",
            "👥 Danh sách khách":    "SELECT guest_id,guest_name,email,phone_number,address,created_at FROM Guests ORDER BY guest_name",
            "🏢 Địa điểm":           "SELECT * FROM view_venue_usage",
            "✅ Đăng ký (an toàn)":  "SELECT * FROM v_safe_registrations",
            "🏆 Top khách":          """
                SELECT g.guest_name, g.email,
                       COUNT(r.event_id) AS total_reg,
                       SUM(r.attendance_status='Attended') AS total_attended
                FROM Guests g JOIN Registrations r ON g.guest_id=r.guest_id
                GROUP BY g.guest_id ORDER BY total_reg DESC
            """,
        }

    selected_sheets = st.multiselect(
        "Chọn sheet muốn xuất:",
        list(SHEET_QUERIES.keys()),
        default=list(SHEET_QUERIES.keys())[:3],
    )

    col_fmt, col_btn = st.columns([2, 1])
    include_summary = col_fmt.checkbox("Thêm sheet 'Tổng quan' đầu tiên", value=True)

    if col_btn.button("Tạo file Excel", icon=":material/description:", use_container_width=True) and selected_sheets:
        buf = io.BytesIO()
        with st.spinner("Đang tạo Excel..."):
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                # Summary sheet
                if include_summary:
                    summary_data = {
                        "Chỉ số": ["Tổng sự kiện", "Tổng khách", "Tổng đăng ký",
                                    "Đã tham dự", "Tổng thu (VND)", "Tổng chi (VND)", "Số dư (VND)"],
                        "Giá trị": [
                            stats.total_events, stats.total_guests, stats.total_registrations,
                            stats.total_attended,
                            float(stats.total_income), float(stats.total_expense), float(stats.net_balance),
                        ],
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name="Tổng quan", index=False)
                    ws0 = writer.sheets["Tổng quan"]
                    ws0.column_dimensions["A"].width = 25
                    ws0.column_dimensions["B"].width = 20

                # Data sheets
                for sheet_label in selected_sheets:
                    sql = SHEET_QUERIES[sheet_label]
                    clean_name = "".join(c for c in sheet_label if c.isalnum() or c in " _-")[:31]
                    df_sheet = pd.read_sql(sqlt(sql), eng)
                    df_sheet.to_excel(writer, sheet_name=clean_name, index=False)
                    ws = writer.sheets[clean_name]
                    for col in ws.columns:
                        ws.column_dimensions[col[0].column_letter].width = min(
                            max((len(str(c.value)) for c in col if c.value), default=10) + 4, 50
                        )

        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"EMS_Report_{ts}.xlsx"

        st.download_button(
            "Tải file Excel",
            data=buf.getvalue(),
            file_name=fname,
            icon=":material/download:",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        show_success(
            f"File '{fname}' đã sẵn sàng — "
            f"{len(selected_sheets) + (1 if include_summary else 0)} sheets"
        )

        # Preview
        st.divider()
        st.markdown("**Preview — Tổng hợp sự kiện:**")
        preview = summary
        if preview:
            styled_df(preview[:5], height=200)
