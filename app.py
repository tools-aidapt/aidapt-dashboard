"""
Aidapt ROI Intelligence Dashboard
Main entry point — run with: streamlit run app.py
"""

import streamlit as st

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

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 2rem 2rem !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0F1923 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] .stSelectbox label { 
    color: #00C9B1 !important; font-size: 10px !important;
    font-weight: 700 !important; letter-spacing: 1.5px !important; text-transform: uppercase !important;
}

/* Cards */
.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
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

/* Section headers */
.section-hdr {
    font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.9);
    letter-spacing: 0.3px; margin-bottom: 4px;
}
.section-sub { font-size: 11px; color: #64748B; margin-bottom: 14px; }

/* Badges */
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

/* Top bar */
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

/* Divider */
.divider { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 18px 0; }

/* Dataframe overrides */
[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px; }

/* Tab styling */
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

/* Metric overrides for dark theme */
[data-testid="stMetric"] label { color: #64748B !important; font-size: 10px !important; }
[data-testid="stMetricValue"] { color: white !important; font-family: 'DM Mono', monospace !important; }

/* Main bg */
.stApp { background: #0B1520 !important; }
</style>
""", unsafe_allow_html=True)

from utils.data_loader import load_all_data
from utils.state import init_state

# ── Initialise session state ───────────────────────────────────────────────────
init_state()

# ── Load data ──────────────────────────────────────────────────────────────────
data = load_all_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.07); margin-bottom: 16px;'>
        <div style='font-size:11px; font-weight:800; letter-spacing:3px; color:#00C9B1; text-transform:uppercase;'>Aidapt</div>
        <div style='font-size:9px; color:rgba(255,255,255,0.3); margin-top:3px; letter-spacing:1px;'>ROI Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    # Client selector
    clients_df = data["clients"]
    client_options = ["All Clients"] + clients_df["client_name"].tolist()
    selected_client = st.selectbox("Active Client", client_options, key="selected_client")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Last refresh
    import datetime
    st.markdown(f"""
    <div style='font-size:9px; color:rgba(255,255,255,0.25); letter-spacing:1px; text-transform:uppercase; margin-bottom:6px;'>Last Refreshed</div>
    <div style='font-family: DM Mono, monospace; font-size:12px; color:rgba(255,255,255,0.6);'>{datetime.datetime.now().strftime('%d %b %Y  %H:%M')}</div>
    """, unsafe_allow_html=True)

    if st.button("↻  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:9px; color:rgba(255,255,255,0.2); letter-spacing:1px; text-transform:uppercase; margin-bottom:10px;'>Navigation</div>
    """, unsafe_allow_html=True)

    pages = {
        "◎  Portfolio Overview":      "portfolio",
        "⬡  Client Deep Dive":        "deep_dive",
        "◈  Opportunity Matrix":      "opportunity",
        "⊟  Data Health Check":       "health",
    }
    for label, key in pages.items():
        active_style = "background:rgba(0,201,177,0.1); color:#00C9B1 !important;" if st.session_state.get("page") == key else ""
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state["page"] = key

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Page routing ───────────────────────────────────────────────────────────────
page = st.session_state.get("page", "portfolio")

if page == "portfolio":
    from pages.portfolio import render
    render(data, selected_client)
elif page == "deep_dive":
    from pages.deep_dive import render
    render(data, selected_client)
elif page == "opportunity":
    from pages.opportunity import render
    render(data, selected_client)
elif page == "health":
    from pages.health import render
    render(data, selected_client)
