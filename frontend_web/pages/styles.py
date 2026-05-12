CUSTOM_CSS = """
<style>
    /* --- Global Font and Base Colors --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="st-"], .stMarkdownContainer, p, h1, h2, h3, h4, h5, h6, span, div, button, input, label, li { 
        font-family: 'Inter', sans-serif !important; 
    }
    
    /* Main app background */
    .stApp { 
        background-color: #F8FAFC !important; 
    }
    
    /* General text color */
    h1, h2, h3, h4, h5, h6 { 
        color: #0F172A !important; 
        font-weight: 700 !important; 
    }
    p, span, label, li, .stMarkdownContainer { 
        color: #334155 !important; 
    }

    /* --- Layout and Containers --- */
    .block-container { 
        padding: 2.5rem 3rem 4rem 3rem !important; 
        max-width: 1200px !important; 
    }
    div[data-testid="stForm"], 
    div[data-testid="stVerticalBlockBorderWrapper"] > div, 
    div[data-testid="metric-container"], 
    .stAlert,
    .stExpander { 
        background-color: #FFFFFF !important; 
        border-radius: 12px !important; 
        border: 1px solid #E2E8F0 !important; 
        padding: 1.25rem !important; 
        transition: box-shadow 0.3s ease-in-out, transform 0.3s ease !important; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important; 
    }
    div[data-testid="stForm"]:hover, 
    div[data-testid="stVerticalBlockBorderWrapper"] > div:hover, 
    div[data-testid="metric-container"]:hover,
    .stExpander:hover { 
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important; 
        transform: translateY(-2px) !important; 
    }

    /* --- Sidebar Styling --- */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 1px solid #E2E8F0 !important; 
    }
    /* Hide specific guest menus for Admin/Organizer */
    [data-testid="stSidebarNav"] ul li:nth-child(8),
    [data-testid="stSidebarNav"] ul li:nth-child(9),
    [data-testid="stSidebarNav"] ul li:nth-child(10),
    [data-testid="stSidebarNav"] ul li:nth-child(11),
    [data-testid="stSidebarNav"] ul li:nth-child(12),
    [data-testid="stSidebarNav"] ul li:nth-last-child(1),
    [data-testid="stSidebarNav"] ul li:nth-last-child(2),
    [data-testid="stSidebarNav"] ul li:nth-last-child(3),
    [data-testid="stSidebarNav"] ul li:nth-last-child(4),
    [data-testid="stSidebarNav"] ul li:nth-last-child(5) { 
        display: none !important; 
    }

    /* --- Buttons --- */
    button[kind="primary"] { 
        background-color: #1E3A8A !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        border-radius: 8px !important; 
        padding: 0.5rem 1.5rem !important; 
        font-weight: 600 !important; 
        transition: all 0.2s ease-in-out !important; 
    }
    button[kind="primary"]:hover { 
        background-color: #1E40AF !important; 
        transform: translateY(-2px); 
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important; 
    }
    button[kind="primary"] p, button[kind="primary"] div { 
        color: #FFFFFF !important; 
    }
    button[kind="secondary"] { 
        background-color: #FFFFFF !important; 
        color: #0F172A !important; 
        border: 1px solid #CBD5E1 !important; 
        border-radius: 8px !important; 
        padding: 0.5rem 1.5rem !important; 
        font-weight: 500 !important; 
        transition: all 0.2s ease-in-out !important; 
    }
    button[kind="secondary"]:hover { 
        background-color: #F1F5F9 !important; 
        border-color: #94A3B8 !important; 
        transform: translateY(-2px); 
    }
    button[kind="secondary"] p, button[kind="secondary"] div { 
        color: #0F172A !important; 
    }

    /* --- Input Fields --- */
    input, 
    textarea, 
    div[data-baseweb="input"], 
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"], 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div { 
        background-color: #FFFFFF !important; 
        border-radius: 8px !important; 
        border: 1px solid #CBD5E1 !important; 
        color: #0F172A !important; 
        padding: 0.25rem 0.5rem !important; 
    }
    input:focus, 
    textarea:focus, 
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within { 
        border-color: #1E3A8A !important; 
        box-shadow: 0 0 0 1px #1E3A8A !important; 
    }

    /* --- Metrics --- */
    div[data-testid="metric-container"] label { 
        color: #64748B !important; 
        font-weight: 500 !important; 
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { 
        color: #1E3A8A !important; 
        font-weight: 700 !important; 
        font-size: 2rem !important; 
    }

    /* --- Calendar and Popover (for Date/Time inputs, Selectboxes) --- */
    div[data-baseweb="popover"] > div,
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] div,
    div[role="listbox"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    div[data-baseweb="calendar"] span, div[data-baseweb="calendar"] p, div[data-baseweb="calendar"] label {
        background-color: transparent !important;
        color: #000000 !important;
    }
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
    div[data-baseweb="calendar"] svg {
        fill: #000000 !important;
        color: #000000 !important;
        background-color: transparent !important;
    }
    div[data-baseweb="calendar"] button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
    }
    div[data-baseweb="calendar"] button[aria-selected="true"],
    div[data-baseweb="calendar"] button[aria-selected="true"]:hover {
        background-color: #2563EB !important;
    }
    div[data-baseweb="calendar"] button[aria-selected="true"] span,
    div[data-baseweb="calendar"] button[aria-selected="true"] p {
        color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] button:disabled, 
    div[data-baseweb="calendar"] button[aria-disabled="true"] {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] button:disabled span,
    div[data-baseweb="calendar"] button[aria-disabled="true"] span,
    div[data-baseweb="calendar"] button[aria-disabled="true"] p {
        color: #94A3B8 !important;
    }
    div[data-baseweb="calendar"] button:hover:not(:disabled):not([aria-selected="true"]) {
        background-color: #F1F5F9 !important;
    }
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

    /* --- Table and DataFrame --- */
    [data-testid="stTable"] *, th, td {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    /* Invert colors for stDataFrame (data_editor) to match light theme */
    [data-testid="stDataFrame"] {
        filter: invert(1) hue-rotate(180deg);
    }
    
    /* --- Specific overrides for Home.py (Guest CSS) --- */
    /* Ensure Home.py's guest CSS aligns with the new theme */
    .stAlert p, .stRadio p, .stRadio span, .stRadio div {
        color: #000000 !important;
    }
    
    /* --- Custom Badges (for status, etc.) --- */
    .st-emotion-cache-10trblm { /* Target Streamlit's default markdown container for badges */
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.2em 0.6em;
        margin: 0.1em;
        border-radius: 0.5em;
        font-size: 0.8em;
        font-weight: 600;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        color: #FFFFFF; /* Default text color for badges */
    }
    .st-emotion-cache-10trblm[data-testid="stMarkdownContainer"] > p > :first-child {
        margin-right: 0.2em;
    }
    .st-emotion-cache-10trblm[data-testid="stMarkdownContainer"] > p {
        margin-bottom: 0;
    }

    /* Badge colors */
    .st-emotion-cache-10trblm[data-color="blue"] { background-color: #3B82F6; } /* Tailwind blue-500 */
    .st-emotion-cache-10trblm[data-color="green"] { background-color: #10B981; } /* Tailwind green-500 */
    .st-emotion-cache-10trblm[data-color="red"] { background-color: #EF4444; } /* Tailwind red-500 */
    .st-emotion-cache-10trblm[data-color="amber"] { background-color: #F59E0B; } /* Tailwind amber-500 */
    .st-emotion-cache-10trblm[data-color="purple"] { background-color: #8B5CF6; } /* Tailwind purple-500 */
    .st-emotion-cache-10trblm[data-color="gray"] { background-color: #6B7280; } /* Tailwind gray-500 */
    .st-emotion-cache-10trblm[data-color="teal"] { background-color: #14B8A6; } /* Tailwind teal-500 */
    .st-emotion-cache-10trblm[data-color="orange"] { background-color: #F97316; } /* Tailwind orange-500 */
    .st-emotion-cache-10trblm[data-color="pink"] { background-color: #EC4899; } /* Tailwind pink-500 */
    .st-emotion-cache-10trblm[data-color="indigo"] { background-color: #6366F1; } /* Tailwind indigo-500 */
    
    /* Specific badge styling for event status */
    .st-emotion-cache-10trblm[data-status="Draft"] { background-color: #9CA3AF; } /* Gray */
    .st-emotion-cache-10trblm[data-status="Scheduled"] { background-color: #22C55E; } /* Green */
    .st-emotion-cache-10trblm[data-status="Full"] { background-color: #F97316; } /* Orange */
    .st-emotion-cache-10trblm[data-status="Completed"] { background-color: #6B7280; } /* Darker Gray */
    .st-emotion-cache-10trblm[data-status="Cancelled"] { background-color: #EF4444; } /* Red */
    .st-emotion-cache-10trblm[data-status="Registered"] { background-color: #3B82F6; } /* Blue */
    .st-emotion-cache-10trblm[data-status="Attended"] { background-color: #10B981; } /* Green */
    .st-emotion-cache-10trblm[data-status="No-show"] { background-color: #EF4444; } /* Red */
    .st-emotion-cache-10trblm[data-status="Refund Requested"] { background-color: #F59E0B; } /* Amber */
    .st-emotion-cache-10trblm[data-status="Refunded"] { background-color: #6B7280; } /* Gray */

    /* Custom background colors for text elements */
    .blue-background { background-color: #DBEAFE; color: #1E40AF; padding: 0.2em 0.4em; border-radius: 0.3em; }
    .green-background { background-color: #D1FAE5; color: #065F46; padding: 0.2em 0.4em; border-radius: 0.3em; }
    .gray-background { background-color: #E5E7EB; color: #374151; padding: 0.2em 0.4em; border-radius: 0.3em; }
    .red-background { background-color: #FEE2E2; color: #991B1B; padding: 0.2em 0.4em; border-radius: 0.3em; }
    .amber-background { background-color: #FEF3C7; color: #92400E; padding: 0.2em 0.4em; border-radius: 0.3em; }
    
</style>
"""

# GUEST_CSS for Home.py (unauthenticated pages)
GUEST_CSS = """
<style>
    /* Hide sidebar and sidebar toggle button */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* Set default background for the app */
    .stApp {
        background-color: #F8FAFC !important;
    }
    
    /* Set default text color for all elements */
    .stMarkdownContainer, .stMarkdownContainer p, h1, h2, h3, h4, h5, h6, label, li, strong, b, .stAlert p, .stRadio p, .stRadio span, .stRadio div {
        color: #000000 !important;
    }
    
    /* Set white background and black text for input fields */
    input, div[data-baseweb="input"], div[data-baseweb="input"] > div,
    textarea, div[data-baseweb="textarea"], div[data-baseweb="textarea"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Specific styling for the login/register form container */
    [data-testid="column"]:nth-of-type(2) {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
    [data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
</style>
"""