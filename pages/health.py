"""Page 4 — Data Health Check"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, fmt_currency, fmt_num,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, CLIENT_NAMES,
)


def render(data, selected_client):
    st.markdown("""
    <div class="topbar">
      <div>
        <div class="topbar-title">Data Health Check</div>
        <div class="topbar-sub">Completeness · Freshness · Formula validation</div>
      </div>
      <div class="topbar-badge">⊟ HEALTH</div>
    </div>
    """, unsafe_allow_html=True)

    clients_df = data["clients"]

    # ── Per-tab completeness ───────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Tab Completeness</div>'
                '<div class="section-sub">% of required fields populated per sheet</div>',
                unsafe_allow_html=True)

    checks = []
    tab_checks = {
        "CLIENTS":        (data["clients"],       ["client_id","client_name","client_type","industry","fte_hourly_rate_usd"]),
        "KPI_DAILY":      (data["kpi_daily"],      ["client_id","date","automation_runs_success","hours_saved"]),
        "KPI_MONTHLY":    (data["kpi_monthly"],    ["client_id","month","hours_saved","cost_savings","delivery_cost"]),
        "OPPORTUNITIES":  (data["opportunities"],  ["client_id","opp_id","opp_name","feasibility_score","value_score","priority_score"]),
        "OPP_FINANCIALS": (data["opp_financials"], ["client_id","opp_id","roi_multiple_annual","payback_months","net_3yr_usd"]),
        "SOLUTIONS":      (data["solutions"],      ["client_id","solution_id","go_live_date","status"]),
    }
    for tab, (df, req_cols) in tab_checks.items():
        total = len(df) * len(req_cols)
        filled = sum(df[c].notna().sum() for c in req_cols if c in df.columns)
        pct    = round(filled / max(1, total) * 100, 1)
        missing_cols = [c for c in req_cols if c not in df.columns]
        null_counts  = {c: int(df[c].isna().sum()) for c in req_cols if c in df.columns and df[c].isna().sum() > 0}
        status = "✅ Complete" if pct == 100 else ("⚠️ Partial" if pct > 70 else "❌ Incomplete")
        checks.append({
            "Sheet": tab, "Rows": len(df), "Required Fields": len(req_cols),
            "Completeness": f"{pct}%", "Status": status,
            "Nulls in key cols": str(null_counts) if null_counts else "—",
        })

    st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)

    # ── KPI freshness ──────────────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Data Freshness</div>'
                '<div class="section-sub">Most recent row per client per sheet</div>',
                unsafe_allow_html=True)

    freshness = []
    for _, cl in clients_df.iterrows():
        cid = cl["client_id"]
        daily_last   = data["kpi_daily"][data["kpi_daily"]["client_id"]==cid]["date"].max()
        monthly_last = data["kpi_monthly"][data["kpi_monthly"]["client_id"]==cid]["month"].max()
        opps_count   = len(data["opportunities"][data["opportunities"]["client_id"]==cid])
        fins_count   = len(data["opp_financials"][data["opp_financials"]["client_id"]==cid])
        freshness.append({
            "Client": cl["client_name"],
            "Type":   cl["client_type"],
            "Last KPI_DAILY": str(daily_last.date()) if pd.notna(daily_last) else "No data",
            "Last KPI_MONTHLY": str(monthly_last.date()) if pd.notna(monthly_last) else "No data",
            "Opportunities": opps_count,
            "Financial Models": fins_count,
            "Models = Opps?": "✅" if opps_count == fins_count else "⚠️ Mismatch",
        })

    st.dataframe(pd.DataFrame(freshness), use_container_width=True, hide_index=True)

    # ── Formula spot-check ─────────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Formula Spot-Check</div>'
                '<div class="section-sub">Verifies key calculations are within expected ranges</div>',
                unsafe_allow_html=True)

    fin = data["opp_financials"]
    formula_checks = []
    for _, row in fin.iterrows():
        # Recalculate annual_productivity_benefit from inputs
        expected_prod = (row["minutes_saved_per_unit"] * row["annual_volume_units"]
                         * row["adoption_pct"] * row["fully_loaded_cost_usd_hr"]) / 60
        expected_total = expected_prod + row["quality_savings_usd_yr"]
        expected_cost  = row["impl_cost_usd"] + row["annual_license_cost_usd"]
        expected_net   = (expected_total - expected_cost) * (1 - row["risk_haircut_pct"])
        expected_roi   = round(expected_net / max(1, expected_cost), 2)

        prod_ok = abs(row["annual_productivity_benefit"] - expected_prod) < 1
        net_ok  = abs(row["net_benefit_risk_adj"] - expected_net) < 1
        roi_ok  = abs(row["roi_multiple_annual"] - expected_roi) < 0.01
        all_ok  = prod_ok and net_ok and roi_ok

        formula_checks.append({
            "Opp ID":     row["opp_id"],
            "Productivity Benefit": "✅" if prod_ok else f"❌ (got {row['annual_productivity_benefit']:,.0f}, expected {expected_prod:,.0f})",
            "Net Benefit":          "✅" if net_ok  else f"❌ (got {row['net_benefit_risk_adj']:,.0f}, expected {expected_net:,.0f})",
            "ROI Multiple":         "✅" if roi_ok  else f"❌ (got {row['roi_multiple_annual']:.2f}, expected {expected_roi:.2f})",
            "Overall":              "✅ Pass" if all_ok else "❌ Fail",
        })

    st.dataframe(pd.DataFrame(formula_checks), use_container_width=True, hide_index=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.info("💡  **How to use this page:** Run a health check each time you onboard a new client "
            "or update data. Any ❌ rows indicate missing fields or calculation mismatches "
            "that need to be fixed in the Google Sheet before sharing with stakeholders.")
