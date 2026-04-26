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

st.set_page_config(page_title="Báo cáo | EMS", page_icon="📊", layout="wide")


@st.cache_resource
def get_db():
    return DatabaseManager()

@st.cache_resource
def get_engine():
    from app.config import engine
    return engine

db  = get_db()
eng = get_engine()

st.markdown("## 📊 Báo cáo & Thống kê")

# ── Load dashboard stats ─────────────────────────────────────
with st.spinner("Đang tải số liệu..."):
    stats = db.get_dashboard_stats()

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
    "📋 Sự kiện", "🏆 Top khách", "🏢 Địa điểm",
    "💰 Tài chính", "📅 Báo cáo kỳ", "📥 Xuất Excel",
])


# ════════════════════════════════════════════════════════════
# TAB 1: SỰ KIỆN
# ════════════════════════════════════════════════════════════
with tab_event:
    section("📋", "Thống kê tổng hợp sự kiện")

    with st.spinner():
        summary = db.events.get_summary()

    if not summary:
        st.info("Chưa có dữ liệu.")
    else:
        df_s = pd.DataFrame(summary)
        avg_rate = float(df_s["attendance_rate_pct"].mean() or 0)

        c_gauge, c_bar = st.columns([1, 2])

        # Gauge chart
        with c_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_rate,
                title={"text": "Tỉ lệ tham dự TB (%)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar":  {"color": "#6366f1"},
                    "steps": [
                        {"range": [0,  40], "color": "#fee2e2"},
                        {"range": [40, 70], "color": "#fef3c7"},
                        {"range": [70,100], "color": "#d1fae5"},
                    ],
                    "threshold": {"line": {"color": "#1f2937", "width": 3},
                                  "thickness": 0.75, "value": avg_rate},
                },
                number={"suffix": "%", "font": {"size": 36}},
            ))
            fig_gauge.update_layout(
                height=240,
                margin=dict(l=20, r=20, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Stacked bar: Attended + No-show
        with c_bar:
            fig_bar = go.Figure()
            names = df_s["event_name"].str[:20]
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
            fig_bar.update_layout(
                barmode="stack", height=240,
                legend=dict(orientation="h", y=-0.3),
                margin=dict(l=0, r=0, t=10, b=60),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickangle=-30),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.dataframe(df_s, use_container_width=True, hide_index=True, height=300)


# ════════════════════════════════════════════════════════════
# TAB 2: TOP KHÁCH
# ════════════════════════════════════════════════════════════
with tab_guest:
    section("🏆", "Top khách tích cực nhất")

    col_sl, col_sort = st.columns([2, 2])
    top_n    = col_sl.slider("Hiển thị top", 5, 50, 15, key="rpt_top_n")
    sort_by  = col_sort.selectbox("Sắp xếp theo",
                                  ["total_registrations", "total_attended", "personal_rate_pct"],
                                  key="rpt_sort")

    with st.spinner():
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
        fig_h.update_layout(
            margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_h, use_container_width=True)

        styled_df(activity, height=300)

        csv = df_a.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Tải CSV", csv, "top_guests.csv", "text/csv")


# ════════════════════════════════════════════════════════════
# TAB 3: ĐỊA ĐIỂM
# ════════════════════════════════════════════════════════════
with tab_venue:
    section("🏢", "Thống kê sử dụng địa điểm")

    with st.spinner():
        venues = db.events.execute_query("SELECT * FROM v_venue_schedule") or []

    if venues:
        df_v = pd.DataFrame(venues)

        # Bubble chart: capacity vs events_hosted, size = avg_fill_rate
        fig_bubble = px.scatter(
            df_v,
            x="total_events_hosted", y="capacity",
            size="avg_fill_rate_pct" if "avg_fill_rate_pct" in df_v.columns else "total_events_hosted",
            color="availability_status" if "availability_status" in df_v.columns else None,
            text="venue_name",
            labels={"total_events_hosted": "Số sự kiện", "capacity": "Sức chứa"},
            height=380,
            title="Sức chứa vs Số sự kiện (size = tỉ lệ lấp đầy TB)",
        )
        fig_bubble.update_traces(textposition="top center")
        fig_bubble.update_layout(
            margin=dict(l=0, r=0, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

        styled_df(venues, badge_cols=["availability_status"], height=280)
    else:
        st.info("Chưa có dữ liệu địa điểm.")


# ════════════════════════════════════════════════════════════
# TAB 4: TÀI CHÍNH
# ════════════════════════════════════════════════════════════
with tab_finance:
    section("💰", "Báo cáo tài chính tổng hợp")

    with st.spinner():
        fin_report = db.finances.get_all_report()
        fin_balance = db.finances.get_balance_all()

    if fin_balance:
        df_bal = pd.DataFrame(fin_balance)

        # Waterfall chart: net balance per event
        fig_wf = go.Figure(go.Waterfall(
            name="Số dư",
            orientation="v",
            measure=["relative"] * len(df_bal),
            x=df_bal["event_name"].str[:18],
            y=df_bal["net_balance"].astype(float),
            connector={"line": {"color": "#9ca3af", "width": 1}},
            increasing={"marker": {"color": "#34d399"}},
            decreasing={"marker": {"color": "#f87171"}},
        ))
        fig_wf.update_layout(
            title="Số dư ròng theo sự kiện (Waterfall)",
            height=320,
            margin=dict(l=0, r=0, t=40, b=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=-30),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

        styled_df(fin_balance, height=260)
    else:
        st.info("Chưa có giao dịch tài chính nào.")


# ════════════════════════════════════════════════════════════
# TAB 5: BÁO CÁO KỲ
# ════════════════════════════════════════════════════════════
with tab_period:
    section("📅", "Báo cáo sự kiện theo khoảng thời gian",
            "Gọi sp_event_report")

    col1, col2, col3 = st.columns([2, 2, 1])
    from_d = col1.date_input("Từ ngày", value=date.today() - timedelta(days=180))
    to_d   = col2.date_input("Đến ngày", value=date.today() + timedelta(days=180))
    run    = col3.button("🔍 Xem", type="primary", use_container_width=True, key="rpt_period_btn")

    if run:
        with st.spinner("Đang gọi sp_event_report..."):
            rows = db.get_event_report(str(from_d), str(to_d))
        if rows:
            df_r = pd.DataFrame(rows)
            st.caption(f"Tìm thấy {len(rows)} sự kiện từ {from_d} đến {to_d}")
            st.dataframe(df_r, use_container_width=True, hide_index=True, height=350)

            # Mini charts
            if "total_attended" in df_r.columns:
                fig_mini = px.bar(
                    df_r, x="event_name", y=["total_registered","total_attended"],
                    barmode="overlay", height=260,
                    labels={"event_name":"Sự kiện","value":"Số người"},
                )
                fig_mini.update_layout(
                    margin=dict(l=0,r=0,t=10,b=60), xaxis=dict(tickangle=-30),
                    paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h",y=-0.4),
                )
                st.plotly_chart(fig_mini, use_container_width=True)

            csv = df_r.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Tải CSV kỳ này", csv, f"report_{from_d}_{to_d}.csv", "text/csv")
        else:
            st.info("Không có sự kiện nào trong khoảng này.")


# ════════════════════════════════════════════════════════════
# TAB 6: XUẤT EXCEL
# ════════════════════════════════════════════════════════════
with tab_excel:
    section("📥", "Xuất báo cáo Excel (.xlsx)", "Chọn sheet, tạo file và tải về ngay")
    from sqlalchemy import text as sqlt

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

    if col_btn.button("📥 Tạo file Excel", type="primary", use_container_width=True) and selected_sheets:
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
            "⬇️ Tải file Excel",
            data=buf.getvalue(),
            file_name=fname,
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
        preview = db.events.get_summary()
        if preview:
            st.dataframe(pd.DataFrame(preview).head(5), use_container_width=True, hide_index=True)
