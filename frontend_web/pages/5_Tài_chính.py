"""
pages/4_finance.py
Trang Tài chính — Income/Expense, biểu đồ, gọi Stored Procedures
ĐÃ SỬA: xóa st.button() bên trong st.form() → dùng st.selectbox thay thế
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import text
from app.config import get_db as get_db_session

from app.database import DatabaseManager
from app.ui.components import (
    section, stat_row, styled_df, show_success, show_error,
)
from app.ui.styles import CUSTOM_CSS

st.set_page_config(page_title="Tài chính | EMS", page_icon="💰", layout="wide")
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

db = get_db()

# ── Header ───────────────────────────────────────────────────
st.markdown("## 💰 Quản lý Tài chính")

# ── Global KPIs ──────────────────────────────────────────────
with st.spinner("Đang tải số liệu..."):
    if owner_id:
        my_balances = db.events.execute_query(f"""
            SELECT e.event_id, e.event_name, 
                   COALESCE(SUM(CASE WHEN f.type='Income' THEN f.amount END),0) as total_income,
                   COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) as total_expense,
                   COALESCE(SUM(CASE WHEN f.type='Income' THEN f.amount END),0) - COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) as net_balance,
                   COUNT(f.finance_id) as total_transactions
            FROM Events e
            LEFT JOIN Finances f ON e.event_id = f.event_id
            WHERE e.organizer_id = {owner_id}
            GROUP BY e.event_id, e.event_name
            HAVING total_transactions > 0
        """) or []
        balances = my_balances
        total_income = sum(float(b["total_income"]) for b in balances)
        total_expense = sum(float(b["total_expense"]) for b in balances)
        net_all = total_income - total_expense
    else:
        total_income  = db.finances.get_total_income_all()
        total_expense = db.finances.get_total_expense_all()
        net_all       = total_income - total_expense
        balances      = db.finances.get_balance_all()

stat_row([
    ("Tổng thu toàn hệ thống",  f"{total_income/1e6:.1f}M VND",  "green"),
    ("Tổng chi toàn hệ thống",  f"{total_expense/1e6:.1f}M VND", "red"),
    ("Số dư ròng tổng",         f"{net_all/1e6:+.1f}M VND",      "green" if net_all >= 0 else "red"),
    ("Số sự kiện có tài chính", len(balances),                    "blue"),
])
st.markdown("")

# ── Tabs ─────────────────────────────────────────────────────
tab_overview, tab_income, tab_expense, tab_detail, tab_period, tab_bank = st.tabs([
    ":material/analytics: Tổng hợp",
    ":material/add_circle: Ghi thu nhập",
    ":material/remove_circle: Ghi chi phí",
    ":material/info: Chi tiết sự kiện",
    ":material/calendar_month: Báo cáo kỳ",
    ":material/account_balance: Tài khoản NH",
])

# Đảm bảo bảng Organizers có các cột thông tin ngân hàng
with get_db_session() as sess:
    try:
        sess.execute(text("ALTER TABLE Organizers ADD COLUMN bank_name VARCHAR(100), ADD COLUMN bank_account_number VARCHAR(50), ADD COLUMN bank_account_name VARCHAR(150)"))
        sess.commit()
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# TAB 1: TỔNG HỢP
# ════════════════════════════════════════════════════════════
with tab_overview:
    if not balances:
        st.info("Chưa có giao dịch tài chính nào.")
    else:
        df_b = pd.DataFrame(balances)
        
        section("bar_chart", "Thu − Chi − Số dư theo sự kiện")
        names = df_b["event_name"].str[:25]
        fig = go.Figure()
        fig.add_bar(name="Thu (Income)", x=names,
                    y=df_b["total_income"].astype(float), marker_color="#34d399")
        fig.add_bar(name="Chi (Expense)", x=names,
                    y=df_b["total_expense"].astype(float), marker_color="#fb923c")
        fig.add_scatter(name="Số dư", x=names,
                        y=df_b["net_balance"].astype(float),
                        mode="lines+markers",
                        line=dict(color="#6366f1", width=2.5),
                        yaxis="y2")
        fig.update_traces(textfont_color="#000000")
        fig.update_layout(
            barmode="group", height=400,
            yaxis2=dict(overlaying="y", side="right", color="#000000", tickfont=dict(color="#000000"), title=dict(font=dict(color="#000000"))),
            legend=dict(orientation="h", y=-0.2, font=dict(color="#000000")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10),
            xaxis=dict(tickangle=0, color="#000000", tickfont=dict(color="#000000"), title=dict(font=dict(color="#000000"))),
            yaxis=dict(color="#000000", tickfont=dict(color="#000000"), title=dict(font=dict(color="#000000"))),
            font=dict(color="#000000"),
            hoverlabel=dict(font_color="#000000", bgcolor="#FFFFFF"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        section("table_view", "Bảng số dư từng sự kiện")
        disp = [{
            "Sự kiện":   str(b["event_name"])[:30],
            "Thu (M)":   f"{float(b['total_income'])/1e6:.1f}",
            "Chi (M)":   f"{float(b['total_expense'])/1e6:.1f}",
            "Số dư (M)": f"{float(b['net_balance'])/1e6:+.1f}",
            "GD":        b.get("total_transactions", 0),
        } for b in balances]
        styled_df(disp, height=320)


# ════════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════════
def _load_event_select():
    events = db.events.get_all() or []
    if owner_id:
        events = [e for e in events if e.get("organizer_id") == owner_id]
    return {e["event_id"]: f"#{e['event_id']} {e['event_name']}" for e in events}


# ════════════════════════════════════════════════════════════
# TAB 2: GHI THU NHẬP
# ════════════════════════════════════════════════════════════
with tab_income:
    section("add_circle", "Ghi nhận thu nhập", "Gọi sp_add_finance_record với type='Income'")

    ev_map_i = _load_event_select()

    # ── Gợi ý danh mục — NGOÀI form (không dùng st.button trong form) ──
    st.markdown("**💡 Chọn mô tả nhanh (tùy chọn):**")
    income_examples = [
        "Phí đăng ký tham dự", "Tài trợ doanh nghiệp",
        "Thu từ bán vé", "Tài trợ NEU", "Thu từ workshop",
    ]
    # Dùng st.selectbox thay st.button — hoàn toàn hợp lệ ngoài form
    quick_desc_i = st.selectbox(
        "Mô tả gợi ý",
        ["(Tự nhập bên dưới)"] + income_examples,
        key="income_quick_desc",
        label_visibility="collapsed",
    )

    # ── Form chỉ chứa input + submit button ──────────────────
    with st.form("form_income_gd3", clear_on_submit=True):
        ev_sel_i = st.selectbox(
            "Sự kiện *",
            list(ev_map_i.keys()),
            format_func=lambda x: ev_map_i.get(x, str(x)),
            key="fin_ev_income",
        )
        amount_i = st.number_input(
            "Số tiền thu (VND) *",
            min_value=1.0, step=100_000.0, format="%.0f",
        )
        # Nếu đã chọn gợi ý thì pre-fill, không thì để trống
        default_desc = "" if quick_desc_i.startswith("(") else quick_desc_i
        desc_i = st.text_input(
            "Mô tả *",
            value=default_desc,
            placeholder="Phí tài trợ, phí đăng ký...",
        )
        submitted_inc = st.form_submit_button(
            "Ghi thu nhập [sp_add_finance_record]",
            icon=":material/add_circle:",
            use_container_width=True,
        )

    if submitted_inc:
        if not desc_i.strip():
            show_error("Vui lòng nhập mô tả giao dịch.")
        else:
            with st.spinner("Đang gọi sp_add_finance_record..."):
                result = db.add_income(int(ev_sel_i), float(amount_i), desc_i.strip())
            if result.success:
                show_success(result.message)
                new_bal = db.finances.get_net_balance(int(ev_sel_i))
                st.metric("Số dư mới", f"{new_bal:+,.0f} VND",
                          delta=f"+{float(amount_i):,.0f} (thu)")
            else:
                show_error(result.message)


# ════════════════════════════════════════════════════════════
# TAB 3: GHI CHI PHÍ
# ════════════════════════════════════════════════════════════
with tab_expense:
    section("remove_circle", "Ghi nhận chi phí", "Gọi sp_add_finance_record với type='Expense'")

    ev_map_e = _load_event_select()

    # ── Danh mục chi phí — NGOÀI form ────────────────────────
    st.markdown("**📂 Danh mục chi phí:**")
    expense_categories = [
        "Thuê địa điểm", "Catering / ăn uống", "In ấn / tài liệu",
        "Trang thiết bị", "Marketing / PR", "Chi phí nhân sự", "Khác",
    ]
    col_cat = st.selectbox(
        "Danh mục",
        expense_categories,
        key="expense_cat_select",
        label_visibility="collapsed",
    )

    # ── Form ──────────────────────────────────────────────────
    with st.form("form_expense_gd3", clear_on_submit=True):
        ev_sel_e = st.selectbox(
            "Sự kiện *",
            list(ev_map_e.keys()),
            format_func=lambda x: ev_map_e.get(x, str(x)),
            key="fin_ev_expense",
        )
        amount_e = st.number_input(
            "Số tiền chi (VND) *",
            min_value=1.0, step=100_000.0, format="%.0f",
        )
        desc_e = st.text_input(
            "Mô tả chi tiết *",
            placeholder="Thuê hội trường A, catering 100 người...",
        )
        submitted_exp = st.form_submit_button(
            "Ghi chi phí [sp_add_finance_record]",
            icon=":material/remove_circle:",
            use_container_width=True,
        )

    if submitted_exp:
        if not desc_e.strip():
            show_error("Vui lòng nhập mô tả giao dịch.")
        else:
            full_desc = f"[{col_cat}] {desc_e.strip()}"
            with st.spinner("Đang gọi sp_add_finance_record..."):
                result = db.add_expense(int(ev_sel_e), float(amount_e), full_desc)
            if result.success:
                show_success(result.message)
                new_bal = db.finances.get_net_balance(int(ev_sel_e))
                color = "normal" if new_bal >= 0 else "inverse"
                st.metric("Số dư mới", f"{new_bal:+,.0f} VND",
                          delta=f"-{float(amount_e):,.0f} (chi)", delta_color=color)
            else:
                show_error(result.message)


# ════════════════════════════════════════════════════════════
# TAB 4: CHI TIẾT SỰ KIỆN
# ════════════════════════════════════════════════════════════
with tab_detail:
    section("info", "Chi tiết tài chính một sự kiện")

    ev_map_d = _load_event_select()
    if ev_map_d:
        eid_d = st.selectbox(
            "Chọn sự kiện",
            list(ev_map_d.keys()),
            format_func=lambda x: ev_map_d.get(x, str(x)),
            key="fin_detail_ev",
        )

        with st.spinner():
            bal          = db.finances.get_balance_by_event(eid_d)
            txns_income  = db.finances.get_by_type(eid_d, "Income")
            txns_expense = db.finances.get_by_type(eid_d, "Expense")

        if bal:
            m1, m2, m3, m4 = st.columns(4)
            inc_v = float(bal["total_income"])
            exp_v = float(bal["total_expense"])
            net_v = float(bal["net_balance"])
            m1.metric("Tổng thu",  f"{inc_v:,.0f} VND")
            m2.metric("Tổng chi",  f"{exp_v:,.0f} VND")
            m3.metric("Số dư",    f"{net_v:+,.0f} VND",
                      delta=f"{net_v:+,.0f}", delta_color="normal")
            m4.metric("Giao dịch", bal.get("total_transactions", 0))

        c_inc, c_exp = st.columns(2)
        with c_inc:
            st.markdown("**:material/add_circle: Thu nhập**")
            if txns_income:
                for t in txns_income:
                    st.markdown(
                        f"<span class='material-symbols-rounded' style='color:#10b981;font-size:1.1rem;vertical-align:middle;'>check_circle</span> `{t['transaction_date']}` — "
                        f"**{float(t['amount']):,.0f} VND** — {t.get('description','')}"
                    )
            else:
                st.info("Chưa có thu nhập.")

        with c_exp:
            st.markdown("**:material/remove_circle: Chi phí**")
            if txns_expense:
                for t in txns_expense:
                    st.markdown(
                        f"<span class='material-symbols-rounded' style='color:#ef4444;font-size:1.1rem;vertical-align:middle;'>cancel</span> `{t['transaction_date']}` — "
                        f"**{float(t['amount']):,.0f} VND** — {t.get('description','')}"
                    )
            else:
                st.info("Chưa có chi phí.")

        # Xóa giao dịch — nút này NGOÀI form nên hoàn toàn hợp lệ
        st.divider()
        all_txns = (txns_income or []) + (txns_expense or [])
        if all_txns:
            txn_map = {
                t["finance_id"]:
                f"#{t['finance_id']} [{t.get('type','')}] "
                f"{float(t['amount']):,.0f} VND — {str(t.get('description',''))[:40]}"
                for t in all_txns
            }
            col_sel, col_del = st.columns([3, 1])
            del_fin_id = col_sel.selectbox(
                "Chọn giao dịch cần xóa",
                list(txn_map.keys()),
                format_func=lambda x: txn_map[x],
                key="del_fin",
            )
            # ✅ st.button NGOÀI form → không lỗi
            if col_del.button("Xóa", icon=":material/delete:", key="del_fin_btn", use_container_width=True):
                db.finances.delete(del_fin_id)
                show_success(f"Đã xóa giao dịch #{del_fin_id}!")
                st.rerun()


# ════════════════════════════════════════════════════════════
# TAB 5: BÁO CÁO KỲ
# ════════════════════════════════════════════════════════════
with tab_period:
    import pandas as _pd
    section("calendar_month", "Báo cáo tài chính theo khoảng thời gian")

    c1, c2 = st.columns(2)
    from_d = c1.date_input("Từ ngày", value=_pd.Timestamp.today() - _pd.Timedelta(days=90))
    to_d   = c2.date_input("Đến ngày", value=_pd.Timestamp.today() + _pd.Timedelta(days=90))

    # ✅ st.button NGOÀI form → hợp lệ
    if st.button("Xem báo cáo", icon=":material/search:", key="fin_period_btn"):
        with st.spinner():
            if owner_id:
                rows = db.events.execute_query(f"""
                    SELECT event_name, type, amount, description, transaction_date 
                    FROM view_finance_report 
                    WHERE event_id IN (SELECT event_id FROM Events WHERE organizer_id = {owner_id})
                    AND transaction_date BETWEEN '{from_d}' AND '{to_d}'
                    ORDER BY transaction_date DESC
                """) or []
            else:
                rows = db.finances.get_period_report(str(from_d), str(to_d))
        if rows:
            df_p = pd.DataFrame(rows)
            styled_df(rows, height=350)
            csv_p = df_p.to_csv(index=False).encode("utf-8")
            st.download_button("Tải CSV", csv_p,
                               "finance_period_report.csv", "text/csv", icon=":material/download:")
        else:
            st.info("Không có giao dịch trong khoảng thời gian này.")


# ════════════════════════════════════════════════════════════
# TAB 6: TÀI KHOẢN NGÂN HÀNG
# ════════════════════════════════════════════════════════════
with tab_bank:
    section("account_balance", "Cấu hình Tài khoản Ngân hàng", "Thông tin này sẽ hiển thị cho khách hàng khi họ chọn phương thức thanh toán chuyển khoản.")
    
    if owner_id:
        with get_db_session() as sess:
            org_info = sess.execute(text("SELECT bank_name, bank_account_number, bank_account_name FROM Organizers WHERE organizer_id = :oid"), {"oid": owner_id}).fetchone()
            
        with st.form("form_bank_account", border=True):
            b_name = st.text_input("Tên Ngân hàng *", value=org_info.bank_name if org_info and org_info.bank_name else "", placeholder="VD: Vietcombank, Techcombank, MBBank...")
            b_num = st.text_input("Số Tài khoản *", value=org_info.bank_account_number if org_info and org_info.bank_account_number else "", placeholder="VD: 0123456789")
            b_acc_name = st.text_input("Tên Chủ tài khoản *", value=org_info.bank_account_name if org_info and org_info.bank_account_name else "", placeholder="VD: CONG TY TNHH ABC hoặc NGUYEN VAN A")
            
            if st.form_submit_button("Lưu cấu hình", type="primary", icon=":material/save:", use_container_width=True):
                if not b_name or not b_num or not b_acc_name:
                    show_error("Vui lòng điền đầy đủ thông tin tài khoản ngân hàng!")
                else:
                    with get_db_session() as sess:
                        sess.execute(text("""
                            UPDATE Organizers 
                            SET bank_name = :bname, bank_account_number = :bnum, bank_account_name = :baccname 
                            WHERE organizer_id = :oid
                        """), {
                            "bname": b_name, "bnum": b_num, "baccname": b_acc_name, "oid": owner_id
                        })
                        sess.commit()
                    show_success("Đã cập nhật thông tin tài khoản ngân hàng thành công!")
                    import time
                    time.sleep(1.5)
                    st.rerun()
    else:
        st.info("Tính năng cấu hình tài khoản ngân hàng chỉ dành cho Ban tổ chức (Organizer).")