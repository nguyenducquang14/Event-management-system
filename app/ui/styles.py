"""
app/ui/styles.py
Custom CSS và theme cho toàn bộ Streamlit UI
"""

CUSTOM_CSS = """
<style>
/* ── GLOBAL ─────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #f8f9fb;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f3a 0%, #14192e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* ── SIDEBAR LOGO ───────────────────────────── */
.sidebar-logo {
    text-align: center;
    padding: 1.2rem 0 0.6rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 0.8rem;
}
.sidebar-logo h2 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff !important;
    margin: 0.4rem 0 0;
    letter-spacing: 0.5px;
}
.sidebar-logo p {
    font-size: 0.72rem;
    color: #94a3b8 !important;
    margin: 0;
}
.sidebar-badge {
    display: inline-block;
    background: rgba(99,102,241,0.25);
    color: #a5b4fc !important;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 4px;
}

/* ── METRIC CARDS ───────────────────────────── */
.metric-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.1rem 1.2rem 1rem;
    border: 1px solid #e5e7f0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    transition: box-shadow .2s, transform .15s;
    height: 100%;
}
.metric-card:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,0.09);
    transform: translateY(-2px);
}
.metric-icon {
    font-size: 1.6rem;
    margin-bottom: 0.4rem;
    display: block;
}
.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #6b7280;
    margin-bottom: 0.25rem;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
    color: #111827;
}
.metric-sub {
    font-size: 0.75rem;
    color: #9ca3af;
    margin-top: 0.3rem;
}
.metric-card.blue   { border-top: 3px solid #3b82f6; }
.metric-card.green  { border-top: 3px solid #10b981; }
.metric-card.purple { border-top: 3px solid #8b5cf6; }
.metric-card.amber  { border-top: 3px solid #f59e0b; }
.metric-card.red    { border-top: 3px solid #ef4444; }
.metric-card.teal   { border-top: 3px solid #14b8a6; }

/* ── SECTION HEADER ─────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 1.4rem 0 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e5e7f0;
}
.section-header h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin: 0;
}

/* ── QUICK ACTION BUTTONS ───────────────────── */
.qab-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin: 0.8rem 0;
}
.qab {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all .15s;
}
.qab-primary { background: #4f46e5; color: #fff; }
.qab-primary:hover { background: #4338ca; }
.qab-success { background: #059669; color: #fff; }
.qab-amber   { background: #d97706; color: #fff; }

/* ── STATUS BADGES ──────────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-scheduled { background: #dbeafe; color: #1d4ed8; }
.badge-completed { background: #d1fae5; color: #065f46; }
.badge-draft     { background: #f3f4f6; color: #374151; }
.badge-full      { background: #fee2e2; color: #991b1b; }
.badge-cancelled { background: #fef3c7; color: #92400e; }

/* ── RESULT BANNERS ─────────────────────────── */
.result-ok  {
    background: #ecfdf5; border: 1px solid #6ee7b7;
    color: #065f46; border-radius: 8px;
    padding: 0.6rem 1rem; font-size: 0.85rem;
    font-weight: 500; margin: 0.5rem 0;
}
.result-err {
    background: #fef2f2; border: 1px solid #fca5a5;
    color: #991b1b; border-radius: 8px;
    padding: 0.6rem 1rem; font-size: 0.85rem;
    font-weight: 500; margin: 0.5rem 0;
}

/* ── DATAFRAME ──────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e5e7f0;
}

/* ── FORM INPUTS ────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div {
    border-radius: 8px !important;
}

/* ── FOOTER ─────────────────────────────────── */
.app-footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    border-top: 1px solid #e5e7f0;
    margin-top: 2rem;
    font-size: 0.75rem;
    color: #9ca3af;
}
.app-footer a { color: #6366f1; text-decoration: none; }
.app-footer a:hover { text-decoration: underline; }

/* ── PAGE TITLE ─────────────────────────────── */
.page-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.25rem;
}
.page-subtitle {
    font-size: 0.85rem;
    color: #6b7280;
    margin-bottom: 1rem;
}

/* ── HIDE DEFAULT STREAMLIT ELEMENTS ────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }
</style>
"""

def metric_card(icon: str, label: str, value: str, sub: str = "", color: str = "blue") -> str:
    return f"""
    <div class="metric-card {color}">
        <span class="metric-icon">{icon}</span>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{sub}</div>' if sub else ''}
    </div>
    """

def section_header(icon: str, title: str) -> str:
    return f"""
    <div class="section-header">
        <span style="font-size:1.1rem">{icon}</span>
        <h3>{title}</h3>
    </div>
    """

def result_banner(text: str, success: bool) -> str:
    cls = "result-ok" if success else "result-err"
    icon = "✓" if success else "✗"
    return f'<div class="{cls}">{icon}  {text}</div>'

def status_badge(status: str) -> str:
    cls = {
        "Scheduled": "badge-scheduled",
        "Completed": "badge-completed",
        "Draft":     "badge-draft",
        "Full":      "badge-full",
        "Cancelled": "badge-cancelled",
    }.get(status, "badge-draft")
    return f'<span class="badge {cls}">{status}</span>'

SIDEBAR_HTML = """
<div class="sidebar-logo">
    <div style="font-size:2.2rem">📅</div>
    <h2>Event Management</h2>
    <p>NEU · DATCOM Lab</p>
    <span class="sidebar-badge">Project 14 · v2.0</span>
</div>
"""

FOOTER_HTML = """
<div class="app-footer">
    NEU DATCOM Lab &nbsp;·&nbsp; Event Management System &nbsp;·&nbsp; Project 14 &nbsp;·&nbsp;
    <a href="https://github.com" target="_blank">GitHub</a> &nbsp;·&nbsp; v2.0
</div>
"""
