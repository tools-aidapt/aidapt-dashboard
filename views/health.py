"""Page 4 — Data Health Check"""

import streamlit as st
import pandas as pd
import numpy as np


def render(data: dict, selected_client: str, filter_banner: str = ""):
    daily     = data["kpi_daily"]
    monthly   = data["kpi_monthly"]
    clients   = data["clients"]
    baselines = data.get("baselines", pd.DataFrame())
    sentiment = data.get("ticket_sentiment", pd.DataFrame())

    st.markdown("""
    <div style='padding:16px 0 8px'>
      <h2 style='color:#E2E8F0;margin:0;font-size:1.5rem'>Data Health Check</h2>
      <p style='color:#9BA8B5;margin:4px 0 0;font-size:0.85rem'>
        Data completeness, freshness, and quality across all tabs
      </p>
    </div>""", unsafe_allow_html=True)

    today = pd.Timestamp.today()

    def check_row(label, status, detail):
        color = "#10B981" if status else "#EF4444"
        icon  = "✓" if status else "✗"
        st.markdown(f"""
        <div style='background:#111827;border-radius:6px;padding:10px 16px;margin:4px 0;
                    display:flex;justify-content:space-between;align-items:center;
                    border-left:2px solid {color}'>
          <span style='color:#E2E8F0;font-size:0.85rem'>{label}</span>
          <span style='color:{color};font-size:0.85rem'>{icon} {detail}</span>
        </div>""", unsafe_allow_html=True)

    # ── Tab completeness ──────────────────────────────────────────────────────
    st.markdown("#### Tab Completeness")
    tabs = {
        "CLIENTS":          (clients,                                     3),
        "OPPORTUNITIES":    (data.get("opportunities",  pd.DataFrame()), 1),
        "OPP_FINANCIALS":   (data.get("opp_financials", pd.DataFrame()), 1),
        "KPI_DAILY":        (daily,                                       10),
        "KPI_MONTHLY":      (monthly,                                     1),
        "TICKET_SENTIMENT": (sentiment,                                   1),
        "BASELINES":        (baselines,                                   1),
    }
    for tab_name, (df, min_rows) in tabs.items():
        rows = len(df)
        ok   = rows >= min_rows
        check_row(tab_name, ok,
                  f"{rows} rows" if ok else f"Only {rows} rows (expected ≥{min_rows})")

    # ── KPI_MONTHLY derived columns ───────────────────────────────────────────
    st.markdown("#### KPI_MONTHLY — Auto-Calculated Columns")
    new_cols = {
        "hours_saved":                "Hours saved (from KPI_DAILY)",
        "automation_runs_total":      "Total automation runs (from KPI_DAILY)",
        "success_rate_monthly":       "Monthly success rate (from KPI_DAILY)",
        "avg_resolution_hrs_monthly": "Avg resolution hrs (from KPI_DAILY)",
    }
    for col, label in new_cols.items():
        present = col in monthly.columns and monthly[col].notna().any()
        check_row(label, present,
                  "Populated" if present else "Empty — check KPI_DAILY has data for matching client+month")

    # ── Data freshness ────────────────────────────────────────────────────────
    st.markdown("#### Data Freshness")
    if not daily.empty and "date" in daily.columns:
        latest = daily["date"].max()
        if pd.notnull(latest):
            days_old = (today - pd.to_datetime(latest)).days
            check_row("KPI_DAILY last entry", days_old <= 7,
                      f"Last: {pd.to_datetime(latest).strftime('%d %b %Y')} ({days_old}d ago)")

    if not sentiment.empty and "week_start" in sentiment.columns:
        latest_sent = sentiment["week_start"].max()
        if pd.notnull(latest_sent):
            weeks_old = (today - pd.to_datetime(latest_sent)).days / 7
            check_row("TICKET_SENTIMENT fresh", weeks_old <= 2,
                      f"Last week: {pd.to_datetime(latest_sent).strftime('%d %b %Y')} ({weeks_old:.0f} wks ago)")

    if not monthly.empty:
        check_row("KPI_MONTHLY has data", len(monthly) > 0, f"{len(monthly)} monthly rows")

    # ── Baseline coverage ─────────────────────────────────────────────────────
    st.markdown("#### Baseline Coverage")
    client_ids = clients["client_id"].tolist() if not clients.empty else []
    key_kpis = ["avg_resolution_hrs","support_tickets_created",
                "hours_saved","automation_runs_success",
                "tickets_open","high_priority_count"]
    for cid in client_ids:
        cname = (clients[clients["client_id"] == cid]["client_name"].iloc[0]
                 if not clients.empty else cid)
        if not baselines.empty and "client_id" in baselines.columns:
            bl_cid  = baselines[baselines["client_id"] == cid]
            covered = [k for k in key_kpis if "kpi_name" in bl_cid.columns and k in bl_cid["kpi_name"].values]
            ok = len(covered) >= 4
            check_row(f"Baselines — {cname}", ok,
                      f"{len(covered)}/{len(key_kpis)} key KPIs have baselines")
        else:
            check_row(f"Baselines — {cname}", False, "BASELINES tab is empty")

    # ── Ticket column fill rate ───────────────────────────────────────────────
    st.markdown("#### KPI_DAILY — Ticket Column Fill Rate")
    ticket_cols = ["tickets_open","tickets_closed","avg_resolution_hrs","high_priority_count"]
    for cid in client_ids:
        cname = (clients[clients["client_id"] == cid]["client_name"].iloc[0]
                 if not clients.empty else cid)
        d = daily[daily["client_id"] == cid]
        if d.empty:
            check_row(cname, False, "No daily data at all")
            continue
        fill_rates = {}
        for col in ticket_cols:
            if col in d.columns:
                fill_rates[col] = d[col].notna().sum() / len(d)
        avg_fill = np.mean(list(fill_rates.values())) if fill_rates else 0
        ok = avg_fill >= 0.8
        check_row(f"{cname} — ticket columns", ok, f"{avg_fill*100:.0f}% filled")
        if not ok and fill_rates:
            for col, rate in fill_rates.items():
                if rate < 0.8:
                    check_row(f"  └ {col}", False, f"{rate*100:.0f}% filled")

    # ── Source indicator ──────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    src       = data.get("_source", "unknown")
    refreshed = data.get("_refreshed", "—")
    if src == "live":
        st.success(f"✓ Live data from Google Sheets · Last refreshed {refreshed}")
    else:
        st.warning(f"⚠ Demo data (Google Sheets not connected) · Generated at {refreshed}")
