"""Page 2 — Client Deep Dive"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, line_chart, multi_bar, bar_chart, combo_chart,
    gauge, config, fmt_currency, fmt_num, fmt_pct,
    build_support_ticket_trend, build_tickets_open_trend,
    build_high_priority_trend, build_resolution_time_trend,
    build_baseline_comparison, donut,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, CLIENT_COLORS, CLIENT_NAMES,
    _to_num, _hex_to_rgba,
)


def _scol(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _safe(df, *cols):
    c = _scol(df, *cols)
    if c:
        return pd.to_numeric(df[c], errors="coerce")
    return pd.Series([np.nan] * len(df), index=df.index)


def render(data, selected_client, filter_banner=""):
    clients_df = data["clients"]

    if selected_client == "All Clients":
        st.info("👈  Select a specific client from the sidebar to view the deep dive.")
        return

    cl_row = clients_df[clients_df["client_name"] == selected_client].iloc[0]
    cid    = cl_row["client_id"]

    monthly   = data["kpi_monthly"][data["kpi_monthly"]["client_id"] == cid].sort_values("month")
    daily     = data["kpi_daily"][data["kpi_daily"]["client_id"] == cid].sort_values("date")
    opps      = data["opportunities"][data["opportunities"]["client_id"] == cid]
    fins      = data["opp_financials"][data["opp_financials"]["client_id"] == cid].copy()
    sols      = data["solutions"][data["solutions"]["client_id"] == cid]
    baselines = data.get("baselines", pd.DataFrame())
    if not baselines.empty and "client_id" in baselines.columns:
        baselines = baselines[baselines["client_id"] == cid]

    accent = CLIENT_COLORS.get(cid, TEAL)

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-title">{selected_client} — Client Deep Dive</div>
        <div class="topbar-sub">
          {cl_row.get('client_type','—')} &nbsp;·&nbsp; {cl_row.get('industry','—')}
          &nbsp;·&nbsp; {cl_row.get('fte_count','—')} FTEs
          &nbsp;·&nbsp; ${cl_row.get('fte_hourly_rate_usd','—')}/hr fully loaded
        </div>
      </div>
      <div class="topbar-badge">⬡ DEEP DIVE</div>
    </div>
    """, unsafe_allow_html=True)

    if filter_banner:
        st.markdown(filter_banner, unsafe_allow_html=True)

    # ── Baseline improvement banner ────────────────────────────────────────────
    def _bl_val(kpi):
        if baselines.empty or "kpi_name" not in baselines.columns:
            return None
        row = baselines[baselines["kpi_name"] == kpi]
        if row.empty:
            return None
        return pd.to_numeric(row.iloc[0]["baseline_value"], errors="coerce")

    def _bl_delta(kpi, current_val):
        bl = _bl_val(kpi)
        if bl is None or pd.isna(bl) or bl == 0 or current_val is None or (isinstance(current_val, float) and np.isnan(current_val)):
            return "", "flat"
        pct = (current_val - bl) / abs(bl) * 100
        return f"{abs(pct):.0f}% vs pre-AI baseline", "down" if pct < 0 else "up"

    bl_res = _bl_val("avg_resolution_hrs")
    bl_open = _bl_val("tickets_open")
    cur_res  = _to_num(daily["avg_resolution_hrs"]).mean() if "avg_resolution_hrs" in daily.columns else None
    cur_open = _to_num(daily["tickets_open"]).mean() if "tickets_open" in daily.columns else None

    if bl_res and cur_res and not np.isnan(cur_res):
        res_imp = (bl_res - cur_res) / bl_res * 100
        st.markdown(f"""
        <div style='background:rgba(0,201,177,0.07);border:1px solid rgba(0,201,177,0.2);
                    border-radius:10px;padding:12px 18px;margin-bottom:16px;'>
          <span style='color:#00C9B1;font-weight:700;font-size:12px;'>📈 AI IMPACT vs PRE-AI BASELINE</span>
          &nbsp;&nbsp;
          <span style='color:rgba(255,255,255,0.7);font-size:12px;'>
            Resolution Time ↓{res_imp:.0f}% ({bl_res:.0f}hrs → {cur_res:.0f}hrs)
            {'&nbsp;&nbsp;·&nbsp;&nbsp; Open Backlog ↓' + f'{((bl_open-cur_open)/bl_open*100):.0f}% ({bl_open:.0f} → {cur_open:.0f})' if (bl_open and cur_open and not np.isnan(cur_open)) else ''}
          </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 1: Core KPI Scorecards ─────────────────────────────────────────────
    _roi_col = _scol(monthly, "actual_roi_multiple","roi_percent","actual_roi")
    latest_m   = monthly.dropna(subset=[_roi_col]).sort_values("month") if _roi_col else monthly.iloc[0:0]
    actual_roi = latest_m[_roi_col].iloc[-1]  if not latest_m.empty else None
    prev_roi   = latest_m[_roi_col].iloc[-2]  if len(latest_m) >= 2 else None
    planned_roi = _safe(fins, "roi_multiple","roi_multiple_annual").mean() if not fins.empty else None
    hours_mtd  = (_to_num(monthly[monthly["month"] == monthly["month"].max()]["hours_saved"]).sum()
                  if not monthly.empty and "hours_saved" in monthly.columns else 0)
    _nb_col    = _scol(monthly, "net_benefit_usd","net_benefit_ytd","net_benefit")
    net_ytd    = _to_num(monthly[_nb_col]).sum() if _nb_col else 0
    _pb_col    = _scol(fins, "payback_months","payback_period_months","payback")
    avg_payback = pd.to_numeric(fins[_pb_col], errors="coerce").mean() if _pb_col and not fins.empty else None

    roi_delta_type = "up" if (actual_roi and prev_roi and actual_roi > prev_roi) else "down" if (actual_roi and prev_roi) else "flat"
    roi_delta_str  = f"vs {prev_roi:.2f}x last month" if prev_roi is not None else "First active month"

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, html in [
        (c1, kpi_card("ROI (Actual)",    f"{actual_roi:.2f}" if actual_roi else "—", "x",
                      roi_delta_str, roi_delta_type, accent)),
        (c2, kpi_card("ROI (Planned)",   f"{planned_roi:.2f}" if planned_roi and not np.isnan(planned_roi) else "—", "x",
                      "From business case", "flat", GOLD)),
        (c3, kpi_card("Hours Saved MTD", fmt_num(hours_mtd), "hrs", "Current month only", "flat", GREEN)),
        (c4, kpi_card("Net Benefit YTD", fmt_currency(net_ytd), "",
                      "Benefits minus delivery cost", "up" if net_ytd > 0 else "down", BLUE)),
        (c5, kpi_card("Avg Payback",     f"{avg_payback:.1f}" if avg_payback and not np.isnan(avg_payback) else "—", "mo",
                      f"{len(fins)} active opportunities", "flat", PURPLE)),
    ]:
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Row 2: Ticket KPI Scorecards with baseline deltas ──────────────────────
    avg_res   = _to_num(daily["avg_resolution_hrs"]).mean()     if "avg_resolution_hrs"    in daily.columns else None
    avg_open  = _to_num(daily["tickets_open"]).mean()           if "tickets_open"           in daily.columns else None
    total_hp  = _to_num(daily["high_priority_count"]).sum()     if "high_priority_count"    in daily.columns else None
    t_created = _to_num(daily["support_tickets_created"]).sum() if "support_tickets_created" in daily.columns else None

    res_delta_str,  res_delta_type  = _bl_delta("avg_resolution_hrs", avg_res)
    open_delta_str, open_delta_type = _bl_delta("tickets_open", avg_open)
    hp_delta_str,   hp_delta_type   = _bl_delta("high_priority_count", total_hp)

    t1, t2, t3, t4 = st.columns(4)
    for col, html in [
        (t1, kpi_card("Avg Resolution Time",
                      f"{avg_res:.0f}" if avg_res and not np.isnan(avg_res) else "—", " hrs",
                      res_delta_str or "Avg ticket close time", res_delta_type, RED)),
        (t2, kpi_card("Avg Open Backlog",
                      f"{avg_open:.0f}" if avg_open and not np.isnan(avg_open) else "—", "",
                      open_delta_str or "Avg open tickets", open_delta_type, GOLD)),
        (t3, kpi_card("High Priority Total",
                      fmt_num(total_hp) if total_hp is not None and not np.isnan(total_hp) else "—", "",
                      hp_delta_str or "High/urgent tickets raised", hp_delta_type, RED)),
        (t4, kpi_card("Daily Tickets Created",
                      f"{t_created/max(1,len(daily)):.1f}" if t_created is not None else "—", "/day",
                      "Avg tickets created per day", "flat", BLUE)),
    ]:
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Row 3: ROI chart + Pipeline donut ─────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-hdr">Actual vs Planned ROI</div>'
                    '<div class="section-sub">Monthly actual ROI vs business case target</div>',
                    unsafe_allow_html=True)
        if _roi_col and not monthly.empty:
            roi_df = monthly.dropna(subset=[_roi_col]).copy()
            roi_df["month_str"] = roi_df["month"].dt.strftime("%b %Y")
            roi_df["planned"]   = planned_roi if planned_roi else 0
            fig = combo_chart(roi_df, "month_str", _roi_col, "planned",
                              bar_name="Actual ROI", line_name="Planned ROI",
                              bar_color=accent, line_color=GOLD)
            fig.update_yaxes(ticksuffix="x")
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_b:
        st.markdown('<div class="section-hdr">Opportunity Pipeline</div>'
                    '<div class="section-sub">Status breakdown · Current opportunities</div>',
                    unsafe_allow_html=True)
        _is_col = _scol(opps, "initiative_status","status","opp_status")
        if not opps.empty and _is_col:
            status_counts = opps[_is_col].value_counts()
            status_order  = ["Backlog","In Pilot","Pilot","Live"]
            labels = [s for s in status_order if s in status_counts.index]
            if not labels:
                labels = status_counts.index.tolist()
            values = [status_counts.get(s, 0) for s in labels]
            colors = [TEAL if s=="Live" else BLUE if s in ("Pilot","In Pilot") else "#64748B" for s in labels]
            fig = donut(labels, values, colors=colors)
            fig.update_layout(
                annotations=[dict(text=f"<b>{len(opps)}</b>",
                                  x=0.5, y=0.5, font_size=20, font_color="white",
                                  showarrow=False, font=dict(family="DM Mono"))]
            )
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 4: Daily automations ───────────────────────────────────────────────
    col_c, col_d = st.columns([1.6, 1])

    with col_c:
        st.markdown('<div class="section-hdr">Daily Automation Runs (Last 30 Days)</div>'
                    '<div class="section-sub">Successful vs failed · Trend shows ramp-up</div>',
                    unsafe_allow_html=True)
        last30 = daily.tail(30).copy()
        last30["date_str"] = last30["date"].dt.strftime("%d %b")
        last30["automation_runs_success"] = _to_num(last30["automation_runs_success"])
        last30["automation_runs_failed"]  = _to_num(last30["automation_runs_failed"])
        if not last30.empty:
            fig = multi_bar(last30, "date_str",
                            ["automation_runs_success","automation_runs_failed"],
                            names=["Successful","Failed"],
                            colors=[accent, "rgba(239,68,68,0.6)"], stacked=True)
            fig.update_xaxes(tickangle=-45, nticks=10)
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_d:
        st.markdown('<div class="section-hdr">Hours Saved per Month</div>'
                    '<div class="section-sub">Cumulative productivity benefit</div>',
                    unsafe_allow_html=True)
        if "hours_saved" in monthly.columns and not monthly.empty:
            hs_df = monthly[["month","hours_saved"]].copy()
            hs_df["month_str"]  = hs_df["month"].dt.strftime("%b %Y")
            hs_df["hours_saved"] = _to_num(hs_df["hours_saved"])
            fig = line_chart(hs_df, "month_str", ["hours_saved"], names=["Hours Saved"], colors=[accent])
            fig.update_yaxes(ticksuffix=" hrs")
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 5: P&L ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">Monthly P&L View</div>'
                '<div class="section-sub">Cost savings vs delivery cost vs net benefit</div>',
                unsafe_allow_html=True)
    _cs_col = _scol(monthly, "cost_savings_usd","cost_savings")
    _dc_col = _scol(monthly, "delivery_cost_usd","delivery_cost")
    if _cs_col and _dc_col and not monthly.empty:
        pl_df = monthly[["month", _cs_col, _dc_col]].copy()
        pl_df["month_str"] = pl_df["month"].dt.strftime("%b %Y")
        pl_df[_cs_col] = _to_num(pl_df[_cs_col])
        pl_df[_dc_col] = _to_num(pl_df[_dc_col])
        fig = multi_bar(pl_df, "month_str", [_cs_col, _dc_col],
                        names=["Cost Savings","Delivery Cost"],
                        colors=[GREEN, "rgba(239,68,68,0.6)"])
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 6: Support health charts ──────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Support Health</div>'
                '<div class="section-sub">Ticket metrics vs pre-AI baseline</div>',
                unsafe_allow_html=True)

    sup1, sup2 = st.columns(2)
    with sup1:
        st.plotly_chart(build_resolution_time_trend(daily, [cid]), use_container_width=True, config=config())
    with sup2:
        st.plotly_chart(build_tickets_open_trend(daily, [cid]),    use_container_width=True, config=config())

    sup3, sup4 = st.columns(2)
    with sup3:
        st.plotly_chart(build_support_ticket_trend(daily, [cid]),  use_container_width=True, config=config())
    with sup4:
        st.plotly_chart(build_high_priority_trend(daily, [cid]),   use_container_width=True, config=config())

    # ── Before vs After AI ────────────────────────────────────────────────────
    if not baselines.empty:
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">Before vs After AI</div>'
                    '<div class="section-sub">Current averages vs pre-AI baseline</div>',
                    unsafe_allow_html=True)
        fig = build_baseline_comparison(daily, baselines, cid)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Opportunity detail table ───────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Opportunity Detail</div>'
                '<div class="section-sub">All opportunities · Financial summary</div>',
                unsafe_allow_html=True)

    _is_col = _scol(opps, "initiative_status","status","opp_status")
    if not opps.empty and not fins.empty:
        fins_sub = fins.copy()
        merged = opps.merge(fins_sub, on="opp_id", how="left", suffixes=("","_fin"))

        def _sc(df, col):
            return df[col] if col in df.columns else pd.Series([None]*len(df), index=df.index)

        _roi_fin = _scol(fins_sub, "roi_multiple","roi_multiple_annual")
        _pb_fin  = _scol(fins_sub, "payback_months","payback_period_months","payback")

        display = pd.DataFrame({
            "ID":             _sc(merged, "opp_id"),
            "Opportunity":    _sc(merged, "opp_name"),
            "Function":       _sc(merged, "function"),
            "Status":         _sc(merged, _is_col) if _is_col else pd.Series(["—"]*len(merged)),
            "Priority Score": pd.to_numeric(_sc(merged, "priority_score"), errors="coerce"),
            "Net Benefit/yr": pd.to_numeric(_sc(merged, "net_benefit"), errors="coerce"),
            "ROI Multiple":   pd.to_numeric(_sc(merged, _roi_fin) if _roi_fin else pd.Series([None]*len(merged)), errors="coerce"),
            "Payback (mo)":   pd.to_numeric(_sc(merged, _pb_fin)  if _pb_fin  else pd.Series([None]*len(merged)), errors="coerce"),
            "Risk":           _sc(merged, "risk_tier") if "risk_tier" in merged.columns else pd.Series(["—"]*len(merged)),
        })
        display["Net Benefit/yr"] = display["Net Benefit/yr"].apply(fmt_currency)
        display["ROI Multiple"]   = display["ROI Multiple"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "—")
        display["Payback (mo)"]   = display["Payback (mo)"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        display["Priority Score"] = display["Priority Score"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        st.dataframe(display, use_container_width=True, hide_index=True)
    elif opps.empty:
        st.info("No opportunities found for this client.")

    # ── Solutions timeline ─────────────────────────────────────────────────────
    if not sols.empty:
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">Solutions Deployed</div>'
                    '<div class="section-sub">Go-live timeline</div>', unsafe_allow_html=True)
        _sc2 = _scol(sols, "status","phase","solution_status","deployment_status")
        disp_cols = [c for c in ["solution_name","go_live_date",_sc2,"fte_impacted","version","notes"]
                     if c and c in sols.columns]
        st.dataframe(sols[disp_cols], use_container_width=True, hide_index=True)
