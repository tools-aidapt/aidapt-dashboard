"""Page 2 — Client Deep Dive"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, line_chart, multi_bar, bar_chart, combo_chart,
    gauge, config, fmt_currency, fmt_num, fmt_pct,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, CLIENT_COLORS, CLIENT_NAMES,
)

# ── Column name aliases ────────────────────────────────────────────────────────
# Maps the canonical name the code uses → possible real column names in the Sheet.
# This means the code works regardless of how columns are named in Google Sheets.
_COL_ALIASES = {
    "net_benefit_risk_adj":   ["net_benefit_risk_adj", "net_benefit_risk_adjusted", "net_benefit"],
    "hours_saved_annual":     ["hours_saved_annual", "annual_hours_saved", "hours_saved_per_year"],
    "net_3yr_usd":            ["net_3yr_usd", "net_3yr", "net_three_year_usd", "net_3year_usd"],
    "roi_multiple_annual":    ["roi_multiple_annual", "roi_multiple", "annual_roi_multiple", "roi_x"],
    "annual_total_benefit":   ["annual_total_benefit", "total_annual_benefit", "annual_benefit"],
    "annual_total_cost":      ["annual_total_cost", "total_annual_cost", "annual_cost"],
    "payback_months":         ["payback_months", "payback_period_months", "payback"],
}

def _col(df: pd.DataFrame, canonical: str):
    """Return the actual column name in df for a canonical alias, or None if not found."""
    for candidate in _COL_ALIASES.get(canonical, [canonical]):
        if candidate in df.columns:
            return candidate
    return None

def _safe(df: pd.DataFrame, canonical: str) -> pd.Series:
    """Return the series for a canonical column name, or a NaN series if missing."""
    c = _col(df, canonical)
    if c:
        return pd.to_numeric(df[c], errors="coerce")
    return pd.Series([np.nan] * len(df), index=df.index)


def render(data, selected_client, filter_banner=""):
    clients_df = data["clients"]

    # ── Client must be selected ────────────────────────────────────────────────
    if selected_client == "All Clients":
        st.info("👈  Select a specific client from the sidebar to view the deep dive.")
        return

    cl_row = clients_df[clients_df["client_name"] == selected_client].iloc[0]
    cid    = cl_row["client_id"]

    monthly = data["kpi_monthly"][data["kpi_monthly"]["client_id"] == cid].sort_values("month")
    daily   = data["kpi_daily"][data["kpi_daily"]["client_id"]   == cid].sort_values("date")
    opps    = data["opportunities"][data["opportunities"]["client_id"] == cid]
    fins    = data["opp_financials"][data["opp_financials"]["client_id"] == cid].copy()
    sols    = data["solutions"][data["solutions"]["client_id"] == cid]

    accent = CLIENT_COLORS.get(cid, TEAL)

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-title">{selected_client} — Client Deep Dive</div>
        <div class="topbar-sub">
          {cl_row['client_type']} &nbsp;·&nbsp; {cl_row['industry']} &nbsp;·&nbsp;
          {cl_row['fte_count']} FTEs &nbsp;·&nbsp; ${cl_row['fte_hourly_rate_usd']}/hr fully loaded
        </div>
      </div>
      <div class="topbar-badge">⬡ DEEP DIVE</div>
    </div>
    """, unsafe_allow_html=True)

    if filter_banner:
        st.markdown(filter_banner, unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────────────────────────────
    latest_m    = monthly.dropna(subset=["roi_percent"]).sort_values("month")
    actual_roi  = latest_m["roi_percent"].iloc[-1]  if not latest_m.empty else None
    prev_roi    = latest_m["roi_percent"].iloc[-2]  if len(latest_m) >= 2 else None
    planned_roi = _safe(fins, "roi_multiple_annual").mean() if not fins.empty else None
    hours_mtd   = monthly[monthly["month"] == monthly["month"].max()]["hours_saved"].sum() if not monthly.empty else 0
    net_ytd     = monthly["net_benefit_ytd"].sum() if "net_benefit_ytd" in monthly.columns else 0
    avg_payback = _safe(fins, "payback_months").mean() if not fins.empty else None

    roi_delta_type = "up" if (actual_roi and prev_roi and actual_roi > prev_roi) else "down" if (actual_roi and prev_roi) else "flat"
    roi_delta_str  = f"vs {prev_roi:.2f}x last month" if prev_roi is not None else "First active month"

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, html in [
        (c1, kpi_card("ROI (Actual)", f"{actual_roi:.2f}" if actual_roi else "—", "x",
                      roi_delta_str, roi_delta_type, accent)),
        (c2, kpi_card("ROI (Planned)", f"{planned_roi:.2f}" if planned_roi else "—", "x",
                      "From business case", "flat", GOLD)),
        (c3, kpi_card("Hours Saved MTD", fmt_num(hours_mtd), "hrs",
                      "Current month only", "flat", GREEN)),
        (c4, kpi_card("Net Benefit YTD", fmt_currency(net_ytd), "",
                      "Benefits minus delivery cost", "up" if net_ytd > 0 else "down", BLUE)),
        (c5, kpi_card("Avg Payback", f"{avg_payback:.1f}" if avg_payback and not np.isnan(avg_payback) else "—", "mo",
                      f"{len(fins)} active opportunities", "flat", PURPLE)),
    ]:
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Row 2: Actual vs Planned ROI + Efficiency trend ────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-hdr">Actual vs Planned ROI</div>'
                    '<div class="section-sub">Monthly actual ROI vs business case target</div>',
                    unsafe_allow_html=True)
        roi_df = monthly.dropna(subset=["roi_percent"]).copy()
        roi_df["month_str"] = roi_df["month"].dt.strftime("%b %Y")
        roi_df["planned"]   = planned_roi

        if not roi_df.empty:
            fig = combo_chart(roi_df, "month_str", "roi_percent", "planned",
                              bar_name="Actual ROI", line_name="Planned ROI",
                              bar_color=accent, line_color=GOLD)
            fig.update_yaxes(ticksuffix="x")
            fig.add_hline(y=0, line=dict(color="rgba(239,68,68,0.3)", width=1, dash="dot"))
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_b:
        st.markdown('<div class="section-hdr">Efficiency Improvement %</div>'
                    '<div class="section-sub">Month-on-month productivity gain</div>',
                    unsafe_allow_html=True)
        eff_df = monthly[["month","efficiency_improvement_percent"]].copy()
        eff_df["month_str"] = eff_df["month"].dt.strftime("%b %Y")
        eff_df = eff_df.dropna(subset=["efficiency_improvement_percent"])
        if not eff_df.empty:
            fig = line_chart(eff_df, "month_str", ["efficiency_improvement_percent"],
                             names=["Efficiency %"], colors=[GREEN])
            fig.update_yaxes(tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 3: Daily automations + Pipeline ───────────────────────────────────
    col_c, col_d = st.columns([1.6, 1])

    with col_c:
        st.markdown('<div class="section-hdr">Daily Automation Runs (Last 30 Days)</div>'
                    '<div class="section-sub">Successful vs failed · Trend shows ramp-up</div>',
                    unsafe_allow_html=True)
        last30 = daily.tail(30).copy()
        last30["date_str"] = last30["date"].dt.strftime("%d %b")
        if not last30.empty:
            fig = multi_bar(last30, "date_str",
                            ["automation_runs_success","automation_runs_failed"],
                            names=["Successful","Failed"],
                            colors=[accent, "rgba(239,68,68,0.6)"],
                            stacked=True)
            fig.update_xaxes(tickangle=-45, nticks=10)
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_d:
        st.markdown('<div class="section-hdr">Opportunity Pipeline</div>'
                    '<div class="section-sub">Status breakdown · Current opportunities</div>',
                    unsafe_allow_html=True)
        if not opps.empty:
            status_counts = opps["initiative_status"].value_counts()
            status_order  = ["Backlog","In Pilot","Live"]
            def _hex_to_rgba(h, a=0.8):
                h = h.lstrip("#"); r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
                return f"rgba({r},{g},{b},{a})"
            status_colors = ["rgba(100,116,139,0.8)", "rgba(59,130,246,0.8)", _hex_to_rgba(accent)]
            labels = [s for s in status_order if s in status_counts.index]
            values = [status_counts.get(s, 0) for s in labels]
            colors = [status_colors[status_order.index(s)] for s in labels]

            from utils.charts import donut
            fig = donut(labels, values, colors=colors)
            fig.update_layout(
                annotations=[dict(text=f"<b>{len(opps)}</b><br><span style='font-size:10px'>Total</span>",
                                  x=0.5, y=0.5, font_size=16, font_color="white", showarrow=False,
                                  font=dict(family="DM Mono"))]
            )
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 4: Hours saved + Cost savings monthly ──────────────────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown('<div class="section-hdr">Hours Saved per Month</div>'
                    '<div class="section-sub">Cumulative productivity benefit</div>',
                    unsafe_allow_html=True)
        hs_df = monthly[["month","hours_saved"]].copy()
        hs_df["month_str"] = hs_df["month"].dt.strftime("%b %Y")
        fig = line_chart(hs_df, "month_str", ["hours_saved"], names=["Hours Saved"], colors=[accent])
        fig.update_yaxes(ticksuffix=" hrs")
        st.plotly_chart(fig, use_container_width=True, config=config())

    with col_f:
        st.markdown('<div class="section-hdr">Monthly P&L View</div>'
                    '<div class="section-sub">Cost savings, delivery cost, net benefit</div>',
                    unsafe_allow_html=True)
        pl_df = monthly[["month","cost_savings","delivery_cost","net_benefit_ytd"]].copy()
        pl_df["month_str"] = pl_df["month"].dt.strftime("%b %Y")
        fig = multi_bar(pl_df, "month_str",
                        ["cost_savings","delivery_cost"],
                        names=["Cost Savings","Delivery Cost"],
                        colors=[GREEN, "rgba(239,68,68,0.6)"])
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Opportunity detail table ───────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Opportunity Detail</div>'
                '<div class="section-sub">All opportunities · Financial summary</div>',
                unsafe_allow_html=True)

    if not opps.empty and not fins.empty:
        # Build a safe fins subset using only columns that actually exist
        fin_cols_wanted = {
            "opp_id":             "opp_id",
            "annual_total_benefit": _col(fins, "annual_total_benefit"),
            "annual_total_cost":    _col(fins, "annual_total_cost"),
            "net_benefit_risk_adj": _col(fins, "net_benefit_risk_adj"),
            "roi_multiple_annual":  _col(fins, "roi_multiple_annual"),
            "payback_months":       _col(fins, "payback_months"),
            "net_3yr_usd":          _col(fins, "net_3yr_usd"),
            "hours_saved_annual":   _col(fins, "hours_saved_annual"),
        }
        # Only select columns that were found
        real_fin_cols = ["opp_id"] + [v for k, v in fin_cols_wanted.items() if v and v != "opp_id"]
        fins_sub = fins[[c for c in real_fin_cols if c in fins.columns]].copy()

        # Rename back to canonical names for consistent downstream use
        rename_map = {v: k for k, v in fin_cols_wanted.items() if v and v != k and v in fins_sub.columns}
        fins_sub = fins_sub.rename(columns=rename_map)

        merged = opps.merge(fins_sub, on="opp_id", how="left")

        # Build display with safe .get() for each column
        def safe_col(df, col):
            return df[col] if col in df.columns else pd.Series([None]*len(df), index=df.index)

        display = pd.DataFrame({
            "ID":               safe_col(merged, "opp_id"),
            "Opportunity":      safe_col(merged, "opp_name"),
            "Function":         safe_col(merged, "function"),
            "Status":           safe_col(merged, "initiative_status"),
            "Priority Score":   pd.to_numeric(safe_col(merged, "priority_score"), errors="coerce"),
            "Planned ROI":      pd.to_numeric(safe_col(merged, "roi_multiple_annual"), errors="coerce"),
            "Payback (mo)":     pd.to_numeric(safe_col(merged, "payback_months"), errors="coerce"),
            "3yr Net Value":    pd.to_numeric(safe_col(merged, "net_3yr_usd"), errors="coerce"),
            "Annual Hrs Saved": pd.to_numeric(safe_col(merged, "hours_saved_annual"), errors="coerce"),
            "Risk":             safe_col(merged, "risk_tier"),
        })

        display["Planned ROI"]    = display["Planned ROI"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "—")
        display["Payback (mo)"]   = display["Payback (mo)"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        display["3yr Net Value"]  = display["3yr Net Value"].apply(fmt_currency)
        display["Annual Hrs Saved"] = display["Annual Hrs Saved"].apply(lambda x: f"{x:,.0f} hrs" if pd.notna(x) else "—")
        display["Priority Score"] = display["Priority Score"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        st.dataframe(display, use_container_width=True, hide_index=True)
    elif opps.empty:
        st.info("No opportunities found for this client.")

    # ── Solutions timeline ─────────────────────────────────────────────────────
    if not sols.empty:
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">Solutions Deployed</div>'
                    '<div class="section-sub">Kickoff to go-live timeline</div>',
                    unsafe_allow_html=True)
        sol_display = sols[["solution_id","solution_name","kickoff_date","go_live_date",
                             "status","time_to_go_live_days"]].copy()
        sol_display.columns = ["ID","Solution","Kickoff","Go-Live","Status","Time to Live (days)"]
        st.dataframe(sol_display, use_container_width=True, hide_index=True)
