"""
app/ui/components.py
Các component dùng chung: badges, banners, dialogs, filters
"""

import streamlit as st
import pandas as pd
from typing import Any

# ── Status badge HTML ────────────────────────────────────────

STATUS_COLORS = {
    # Events
    "Scheduled": ("#dbeafe", "#1d4ed8"),
    "Draft":     ("#f3f4f6", "#374151"),
    "Full":      ("#fee2e2", "#991b1b"),
    "Completed": ("#d1fae5", "#065f46"),
    "Cancelled": ("#fef3c7", "#92400e"),
    # Registrations
    "Registered": ("#e0e7ff", "#3730a3"),
    "Attended":   ("#d1fae5", "#065f46"),
    "No-show":    ("#fee2e2", "#991b1b"),
    # Venues
    "Available":   ("#d1fae5", "#065f46"),
    "Booked":      ("#fee2e2", "#991b1b"),
    "Maintenance": ("#fef3c7", "#92400e"),
    # Finance
    "Income":  ("#d1fae5", "#065f46"),
    "Expense": ("#fee2e2", "#991b1b"),
}

def badge(text: str) -> str:
    bg, color = STATUS_COLORS.get(str(text), ("#f3f4f6", "#374151"))
    return (
        f'<span style="background:{bg};color:{color};padding:2px 9px;'
        f'border-radius:20px;font-size:.68rem;font-weight:600;'
        f'white-space:nowrap">{text}</span>'
    )


# ── Notification helpers ─────────────────────────────────────

def show_success(msg: str):
    st.toast(f"✓  {msg}", icon="✅")
    st.success(f"✓  {msg}")

def show_error(msg: str):
    st.toast(f"✗  {msg}", icon="❌")
    st.error(f"✗  {msg}")

def show_result(message: str, success: bool):
    if success:
        show_success(message)
    else:
        show_error(message)


# ── Search bar ───────────────────────────────────────────────

def search_bar(placeholder: str = "Tìm kiếm...", key: str = "search") -> str:
    return st.text_input(
        "🔍", placeholder=placeholder, key=key, label_visibility="collapsed"
    )


# ── Section divider ──────────────────────────────────────────

def section(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.5rem;'
        f'margin:1.2rem 0 .6rem;padding-bottom:.5rem;'
        f'border-bottom:2px solid #e5e7f0">'
        f'<span style="font-size:1.1rem">{icon}</span>'
        f'<div><div style="font-size:.95rem;font-weight:600;color:#1f2937">{title}</div>'
        f'{"" if not subtitle else f"<div style=font-size:.72rem;color:#6b7280>{subtitle}</div>"}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ── Stat row ─────────────────────────────────────────────────

def stat_row(items: list[tuple[str, Any, str]]):
    """items = [(label, value, color), ...]  color: green|red|blue|amber|gray"""
    c_map = {
        "green": ("#d1fae5","#065f46"), "red":  ("#fee2e2","#991b1b"),
        "blue":  ("#dbeafe","#1d4ed8"), "amber":("#fef3c7","#92400e"),
        "gray":  ("#f3f4f6","#374151"), "purple":("#ede9fe","#5b21b6"),
    }
    cols = st.columns(len(items))
    for col, (label, value, color) in zip(cols, items):
        bg, fg = c_map.get(color, ("#f3f4f6","#374151"))
        col.markdown(
            f'<div style="background:{bg};border-radius:10px;padding:.75rem 1rem;text-align:center">'
            f'<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.6px;color:{fg};margin-bottom:.2rem">{label}</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:{fg}">{value}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Action button row ────────────────────────────────────────

def action_bar(*buttons: tuple[str, str]) -> str | None:
    """buttons = [(label, key), ...]  Returns key of clicked button or None."""
    cols = st.columns(len(buttons) + 4)  # left-align
    for i, (label, key) in enumerate(buttons):
        if cols[i].button(label, key=key, use_container_width=True):
            return key
    return None


# ── DataFrame with badges ────────────────────────────────────

def styled_df(
    data: list[dict],
    badge_cols: list[str] | None = None,
    height: int = 380,
) -> None:
    """Render dataframe. Badge_cols are rendered as HTML in a markdown table."""
    if not data:
        st.info("Không có dữ liệu.")
        return

    df = pd.DataFrame(data)

    if not badge_cols:
        st.dataframe(df, use_container_width=True, hide_index=True, height=height)
        return

    # Build HTML table with badges
    headers = list(df.columns)
    html = '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:.78rem">'
    html += "<thead><tr>"
    for h in headers:
        html += (
            f'<th style="padding:.5rem .7rem;background:#f9fafb;'
            f'border-bottom:2px solid #e5e7f0;text-align:left;'
            f'color:#6b7280;font-size:.68rem;text-transform:uppercase;'
            f'letter-spacing:.5px;white-space:nowrap">{h}</th>'
        )
    html += "</tr></thead><tbody>"

    for i, row in df.iterrows():
        bg = "#fafafa" if i % 2 else "#ffffff"
        html += f'<tr style="background:{bg}">'
        for h in headers:
            val = row[h]
            if h in badge_cols:
                cell = badge(str(val)) if val is not None else "—"
            else:
                cell = ("—" if val is None or (isinstance(val, float) and pd.isna(val))
                        else str(val))
            html += (
                f'<td style="padding:.45rem .7rem;'
                f'border-bottom:1px solid #f3f4f6;'
                f'color:#374151;vertical-align:middle">{cell}</td>'
            )
        html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"Tổng: {len(df)} dòng")
