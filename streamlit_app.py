"""
streamlit_app.py — Event Management System v2.0
NEU DATCOM Lab | Project 14
Entry point: redirect sang pages hoặc hiển thị dashboard
Chạy: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Event Management System | NEU DATCOM",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "NEU DATCOM Lab · Project 14 · v2.0"},
)

from app.ui.styles import CUSTOM_CSS, SIDEBAR_HTML, FOOTER_HTML, metric_card, section_header, result_banner
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

@st.cache_resource
def get_db():
    from app.database import DatabaseManager
    return DatabaseManager()

def safe_db():
    try:
        return get_db()
    except Exception as e:
        st.error(f"Không thể kết nối database: {e}")
        st.stop()

db = safe_db()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)
    st.markdown("**Điều hướng nhanh**")
    st.page_link("streamlit_app.py",         label="🏠 Dashboard",         icon="🏠")
    st.page_link("pages/1_events.py",        label="📋 Sự kiện",           icon="📋")
    st.page_link("pages/2_guests.py",        label="👥 Khách mời",         icon="👥")
    st.page_link("pages/3_registrations.py", label="✅ Đăng ký & Check-in",icon="✅")
    st.page_link("pages/4_finance.py",       label="💰 Tài chính",         icon="💰")
    st.page_link("pages/5_reports.py",       label="📊 Báo cáo & Excel",   icon="📊")
    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M · %d/%m/%Y')}")

# ── Dashboard ────────────────────────────────────────────────
st.markdown('<div class="page-title">🏠 Dashboard — Event Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">NEU DATCOM Lab · Project 14 · v2.0</div>', unsafe_allow_html=True)

with st.spinner("Đang tải số liệu..."):
    stats = db.get_dashboard_stats()

income  = float(stats.total_income)
expense = float(stats.total_expense)
net     = float(stats.net_balance)
rate    = (stats.total_attended / stats.total_registrations * 100 if stats.total_registrations else 0)

cols = st.columns(6)
cards_data = [
    ("📅", "Tổng sự kiện",    str(stats.total_events),          f"{stats.upcoming_events} sắp tới", "blue"),
    ("👥", "Tổng khách mời", str(stats.total_guests),           "khách mời",                        "purple"),
    ("📋", "Tổng đăng ký",   str(stats.total_registrations),   f"{stats.total_attended} Attended",  "teal"),
    ("📈", "Tỉ lệ tham dự",  f"{rate:.1f}%",                   "trung bình",                        "green"),
    ("💰", "Tổng thu",       f"{income/1e6:.1f}M VND",          "",                                  "amber"),
    ("📊", "Số dư ròng",     f"{net/1e6:+.1f}M VND",           "Thu − Chi",                         "red" if net < 0 else "green"),
]
for col, (icon, label, value, sub, color) in zip(cols, cards_data):
    col.markdown(metric_card(icon, label, value, sub, color), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Actions
st.markdown(section_header("⚡", "Thao tác nhanh"), unsafe_allow_html=True)
qa = st.columns(5)
links = [
    ("➕ Tạo sự kiện",  "pages/1_events.py"),
    ("✅ Check-in",     "pages/3_registrations.py"),
    ("👤 Thêm khách",   "pages/2_guests.py"),
    ("💰 Ghi thu/chi",  "pages/4_finance.py"),
    ("📊 Báo cáo",      "pages/5_reports.py"),
]
for col, (label, pg) in zip(qa, links):
    col.page_link(pg, label=label, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts
left, right = st.columns([3, 2])
with left:
    st.markdown(section_header("📋", "Thống kê tham dự theo sự kiện"), unsafe_allow_html=True)
    summary = db.events.get_summary()
    if summary:
        df_s = pd.DataFrame(summary)
        fig = go.Figure()
        fig.add_bar(name="Attended",   x=df_s["event_name"].str[:18], y=df_s["total_attended"].astype(float),  marker_color="#6366f1")
        fig.add_bar(name="No-show",    x=df_s["event_name"].str[:18], y=df_s["total_noshow"].astype(float),   marker_color="#f87171")
        fig.update_layout(barmode="stack", height=280, margin=dict(l=0,r=0,t=10,b=55),
                          legend=dict(orientation="h",y=-0.3), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickangle=-30))
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown(section_header("💰", "Thu − Chi theo sự kiện"), unsafe_allow_html=True)
    balances = db.finances.get_balance_all()
    if balances:
        df_b = pd.DataFrame(balances).head(6)
        fig2 = go.Figure()
        fig2.add_bar(name="Thu", x=df_b["event_name"].str[:14], y=df_b["total_income"].astype(float),  marker_color="#34d399")
        fig2.add_bar(name="Chi", x=df_b["event_name"].str[:14], y=df_b["total_expense"].astype(float), marker_color="#fb923c")
        fig2.update_layout(barmode="group", height=280, margin=dict(l=0,r=0,t=10,b=55),
                           legend=dict(orientation="h",y=-0.3), paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickangle=-30))
        st.plotly_chart(fig2, use_container_width=True)

st.markdown(section_header("🔜", "Sự kiện sắp diễn ra"), unsafe_allow_html=True)
upcoming = db.events.get_upcoming()
if upcoming:
    df_up = pd.DataFrame(upcoming)
    show_cols = [c for c in ["event_name","start_time","venue_name","organizer_name","status","slots_remaining"] if c in df_up.columns]
    st.dataframe(df_up[show_cols], use_container_width=True, hide_index=True, height=200)
else:
    st.info("Không có sự kiện sắp diễn ra.")

st.markdown(FOOTER_HTML, unsafe_allow_html=True)
