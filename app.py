"""
Aidapt ROI Intelligence Dashboard
Main entry point — run with: streamlit run app.py
"""

import streamlit as st
import datetime
import pandas as pd

st.set_page_config(
    page_title="Aidapt ROI Dashboard",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 2rem 2rem !important; }

[data-testid="stSidebar"] {
    background: #0F1923 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label {
    color: #00C9B1 !important; font-size: 10px !important;
    font-weight: 700 !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* Date input styling */
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: white !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
}

/* Active date range pill */
.date-range-pill {
    background: rgba(0,201,177,0.08);
    border: 1px solid rgba(0,201,177,0.2);
    border-radius: 8px;
    padding: 8px 12px;
    margin: 8px 0;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: rgba(0,201,177,0.9);
    text-align: center;
}
.date-range-pill span {
    display: block;
    font-size: 9px;
    color: rgba(255,255,255,0.3);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}

.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, #00C9B1);
}
.kpi-label {
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #64748B; margin-bottom: 8px;
}
.kpi-value {
    font-size: 28px; font-weight: 700; color: #FFFFFF;
    font-family: 'DM Mono', monospace; line-height: 1;
}
.kpi-unit { font-size: 14px; font-weight: 400; color: #64748B; margin-left: 2px; }
.kpi-delta { font-size: 11px; margin-top: 8px; }
.delta-up   { color: #10B981; }
.delta-down { color: #EF4444; }
.delta-flat { color: #64748B; }

.section-hdr {
    font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.9);
    letter-spacing: 0.3px; margin-bottom: 4px;
}
.section-sub { font-size: 11px; color: #64748B; margin-bottom: 14px; }

.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
}
.badge-live    { background: rgba(16,185,129,0.15); color: #10B981; }
.badge-pilot   { background: rgba(59,130,246,0.15); color: #3B82F6; }
.badge-backlog { background: rgba(100,116,139,0.15); color: #94A3B8; }
.badge-track   { background: rgba(16,185,129,0.15); color: #10B981; }
.badge-risk    { background: rgba(245,158,11,0.15);  color: #F59E0B; }
.badge-behind  { background: rgba(239,68,68,0.15);   color: #EF4444; }

.topbar {
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding-bottom: 14px; margin-bottom: 20px;
}
.topbar-title { font-size: 18px; font-weight: 700; color: white; }
.topbar-sub   { font-size: 11px; color: #64748B; margin-top: 2px; }
.topbar-badge {
    background: rgba(0,201,177,0.1); border: 1px solid rgba(0,201,177,0.25);
    color: #00C9B1; font-size: 11px; padding: 5px 14px; border-radius: 20px;
    font-weight: 700; font-family: 'DM Mono', monospace;
}

/* Active filter banner shown at top of each page */
.filter-banner {
    display: flex; align-items: center; gap: 12px;
    background: rgba(0,201,177,0.06);
    border: 1px solid rgba(0,201,177,0.15);
    border-radius: 10px;
    padding: 8px 16px;
    margin-bottom: 16px;
    font-size: 11px;
    color: rgba(255,255,255,0.5);
}
.filter-banner strong { color: #00C9B1; font-family: 'DM Mono', monospace; }
.filter-dot { width: 6px; height: 6px; border-radius: 50%; background: #00C9B1; flex-shrink: 0; }

.divider { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 18px 0; }

[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px; }

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.45) !important;
    font-weight: 600 !important; font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
    color: #00C9B1 !important;
    border-bottom-color: #00C9B1 !important;
}

[data-testid="stMetric"] label { color: #64748B !important; font-size: 10px !important; }
[data-testid="stMetricValue"] { color: white !important; font-family: 'DM Mono', monospace !important; }

.stApp { background: #0B1520 !important; }

/* Force sidebar always open — never collapse */
[data-testid="stSidebar"] {
    transform: none !important;
    visibility: visible !important;
    display: flex !important;
    min-width: 280px !important;
    max-width: 320px !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    transform: none !important;
    margin-left: 0 !important;
    width: 280px !important;
    min-width: 280px !important;
}
/* Hide the collapse arrow button so user can't collapse it */
[data-testid="stSidebarCollapseButton"],
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

from utils.data_loader import load_all_data
from utils.charts import build_client_maps
from utils.state import init_state

# Logo — try utils/logo first, fall back to root-level logo.py
try:
    from utils.logo import LOGO_B64
except ModuleNotFoundError:
    try:
        from logo import LOGO_B64
    except ModuleNotFoundError:
        LOGO_B64 = ""  # graceful fallback — sidebar shows text only

# ── Initialise session state ───────────────────────────────────────────────────
init_state()

# ── Load data ──────────────────────────────────────────────────────────────────
data = load_all_data()

# ── Build client colour/name maps from real data ───────────────────────────────
build_client_maps(data["clients"])

# ── Determine global date bounds from the data ─────────────────────────────────
def _get_date_bounds(data):
    """Get min/max date across KPI_DAILY and KPI_MONTHLY."""
    dates = []
    if not data["kpi_daily"].empty and "date" in data["kpi_daily"].columns:
        d = data["kpi_daily"]["date"].dropna()
        if not d.empty:
            dates.extend([d.min(), d.max()])
    if not data["kpi_monthly"].empty and "month" in data["kpi_monthly"].columns:
        m = data["kpi_monthly"]["month"].dropna()
        if not m.empty:
            dates.extend([m.min(), m.max()])
    if dates:
        return min(dates).date(), max(dates).date()
    # Sensible fallback
    today = datetime.date.today()
    return (today - datetime.timedelta(days=90)), today

data_min, data_max = _get_date_bounds(data)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Pull the entire sidebar content to the very top — removes the dead space
    # left behind after deleting the pages/ nav items
    st.markdown("""
    <style>
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _logo_img = (f'<img src="data:image/png;base64,{LOGO_B64}" '
                 f'style="width:36px;height:36px;border-radius:8px;flex-shrink:0;" />'
                 if LOGO_B64 else
                 '<div style="width:36px;height:36px;border-radius:8px;background:#1B4FD8;'
                 'display:flex;align-items:center;justify-content:center;'
                 'font-size:18px;flex-shrink:0;">↗</div>')
    st.markdown(f"""
    <div style='padding: 4px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.07);
                margin-bottom: 16px; display:flex; align-items:center; gap:10px;'>
        {_logo_img}
        <div>
            <div style='font-size:14px; font-weight:800; letter-spacing:1px; color:#ffffff;'>Aidapt</div>
            <div style='font-size:9px; color:rgba(255,255,255,0.3); letter-spacing:1px;'>ROI Intelligence Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Client selector ────────────────────────────────────────────────────────
    clients_df = data["clients"]
    client_options = ["All Clients"] + clients_df["client_name"].tolist()
    selected_client = st.selectbox("Active Client", client_options, key="selected_client")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Date range filter ──────────────────────────────────────────────────────
    st.markdown("""
    <div style='font-size:9px; color:rgba(0,201,177,0.9); font-weight:700;
                letter-spacing:1.5px; text-transform:uppercase; margin-bottom:6px;'>
        Date Range
    </div>""", unsafe_allow_html=True)

    # Quick presets
    preset = st.selectbox(
        "Quick Select",
        ["Custom", "Last 30 Days", "Last 60 Days", "Last 90 Days", "All Time"],
        key="date_preset",
        label_visibility="collapsed",
    )

    today = datetime.date.today()
    if preset == "Last 30 Days":
        default_start = today - datetime.timedelta(days=30)
        default_end   = today
    elif preset == "Last 60 Days":
        default_start = today - datetime.timedelta(days=60)
        default_end   = today
    elif preset == "Last 90 Days":
        default_start = today - datetime.timedelta(days=90)
        default_end   = today
    elif preset == "All Time":
        default_start = data_min
        default_end   = data_max
    else:
        default_start = st.session_state.get("date_start", data_min)
        default_end   = st.session_state.get("date_end",   data_max)

    # Force session state to match preset — without this, date_input
    # ignores the value= argument and keeps its own stale state
    if preset != "Custom":
        st.session_state["date_start"] = default_start
        st.session_state["date_end"]   = default_end

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_start = st.date_input("From", value=default_start,
                                   key="date_start", label_visibility="visible")
    with col_d2:
        date_end = st.date_input("To", value=default_end,
                                 key="date_end", label_visibility="visible")

    # Guard against reversed range
    if date_start > date_end:
        st.warning("⚠️ Start date is after end date.")
        date_start, date_end = date_end, date_start

    # Show active filter pill
    days_selected = (date_end - date_start).days + 1
    st.markdown(f"""
    <div class="date-range-pill">
        <span>Active Filter</span>
        {date_start.strftime('%d %b %Y')} → {date_end.strftime('%d %b %Y')}
        <span style='font-size:9px; color:rgba(255,255,255,0.2); margin-top:2px;'>{days_selected} days selected</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Last refresh
    st.markdown(f"""
    <div style='font-size:9px; color:rgba(255,255,255,0.25); letter-spacing:1px;
                text-transform:uppercase; margin-bottom:6px;'>Last Refreshed</div>
    <div style='font-family: DM Mono, monospace; font-size:12px;
                color:rgba(255,255,255,0.6);'>{datetime.datetime.now().strftime('%d %b %Y  %H:%M')}</div>
    """, unsafe_allow_html=True)

    if st.button("↻  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:9px; color:rgba(255,255,255,0.2); letter-spacing:1px;
                text-transform:uppercase; margin-bottom:10px;'>Navigation</div>
    """, unsafe_allow_html=True)

    pages = {
        "◎  Portfolio Overview":  "portfolio",
        "⬡  Client Deep Dive":    "deep_dive",
        "◈  Opportunity Matrix":  "opportunity",
        "⊟  Data Health Check":   "health",
    }
    for label, key in pages.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state["page"] = key

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Apply date filter to data ──────────────────────────────────────────────────
# Convert to timestamps for comparison
ts_start = pd.Timestamp(date_start)
ts_end   = pd.Timestamp(date_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

def _apply_date_filter(data: dict, ts_start, ts_end) -> dict:
    """Return a copy of data with date-indexed tables filtered to the selected range."""
    filtered = dict(data)  # shallow copy — we replace only the filtered frames

    if "kpi_daily" in data and "date" in data["kpi_daily"].columns:
        d = data["kpi_daily"]
        filtered["kpi_daily"] = d[(d["date"] >= ts_start) & (d["date"] <= ts_end)]

    if "kpi_monthly" in data and "month" in data["kpi_monthly"].columns:
        m = data["kpi_monthly"]
        filtered["kpi_monthly"] = m[(m["month"] >= ts_start) & (m["month"] <= ts_end)]

    return filtered

filtered_data = _apply_date_filter(data, ts_start, ts_end)

# ── Filter banner HTML (injected into each page at top) ───────────────────────
client_label  = selected_client
date_label    = f"{date_start.strftime('%d %b %Y')} → {date_end.strftime('%d %b %Y')}"
filter_banner = f"""
<div class="filter-banner">
  <div class="filter-dot"></div>
  <div>
    Client: <strong>{client_label}</strong>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    Period: <strong>{date_label}</strong>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <span style='color:rgba(255,255,255,0.3);'>{days_selected} days</span>
  </div>
</div>
"""

# ── Page routing ───────────────────────────────────────────────────────────────
# Try importing from views/ first (recommended). Falls back to pages/ if views/ doesn't exist yet.
def _import_render(module_name):
    try:
        import importlib
        mod = importlib.import_module(f"views.{module_name}")
    except ModuleNotFoundError:
        import importlib
        mod = importlib.import_module(f"pages.{module_name}")
    return mod.render

page = st.session_state.get("page", "portfolio")

if page == "portfolio":
    _import_render("portfolio")(filtered_data, selected_client, filter_banner)
elif page == "deep_dive":
    _import_render("deep_dive")(filtered_data, selected_client, filter_banner)
elif page == "opportunity":
    _import_render("opportunity")(data, selected_client, filter_banner)
elif page == "health":
    _import_render("health")(data, selected_client, filter_banner)
