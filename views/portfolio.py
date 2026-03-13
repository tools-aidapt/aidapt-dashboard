"""Page 1 — Executive Portfolio Overview"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, line_chart, multi_bar, bar_chart, donut, combo_chart, config,
    fmt_currency, fmt_num, fmt_pct,
    build_automation_trend, build_support_ticket_trend,
    build_tickets_open_trend, build_high_priority_trend,
    build_resolution_time_trend,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, PALETTE,
    CLIENT_COLORS, CLIENT_NAMES, _to_num,
)


def _scol(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _ssum(df, *candidates):
    c = _scol(df, *candidates)
    return _to_num(df[c]).sum() if c else 0

def _smean(df, *candidates):
    c = _scol(df, *candidates)
    v = _to_num(df[c]).mean() if c else float('nan')
    return None if pd.isna(v) else v

def _filter(data, selected_client):
    clients_df = data["clients"]
    if selected_client == "All Clients":
        cids = clients_df["client_id"].tolist()
    else:
        cids = clients_df[clients_df["client_name"] == selected_client]["client_id"].tolist()
    return {k: df[df["client_id"].isin(cids)] if isinstance(df, pd.DataFrame) and "client_id" in df.columns else df
            for k, df in data.items()}, cids


def render(data, selected_client, filter_banner=""):
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-title">Executive Portfolio Overview</div>
        <div class="topbar-sub">
          {'All clients' if selected_client == 'All Clients' else selected_client}
          &nbsp;·&nbsp; Live data
        </div>
      </div>
      <div class="topbar-badge">◎ PORTFOLIO</div>
    </div>
    """, unsafe_allow_html=True)

    if filter_banner:
        st.markdown(filter_banner, unsafe_allow_html=True)

    fd, cids = _filter(data, selected_client)
    monthly = fd["kpi_monthly"]
    daily   = fd["kpi_daily"]
    clients = fd["clients"]
    opps    = fd["opportunities"]
    fins    = fd["opp_financials"]

    # ── Aggregate KPIs ─────────────────────────────────────────────────────────
    total_hours   = _to_num(monthly["hours_saved"]).sum() if "hours_saved" in monthly.columns else 0
    total_savings = _ssum(monthly, "cost_savings_usd", "cost_savings")
    total_runs    = _to_num(daily["automation_runs_success"]).sum() if "automation_runs_success" in daily.columns else 0
    total_runs_f  = _to_num(daily["automation_runs_failed"]).sum() if "automation_runs_failed" in daily.columns else 0
    success_rate  = total_runs / max(1, total_runs + total_runs_f) * 100

    # ── Active clients: use UNFILTERED clients so count is never 0 ───────────
    _all_clients = data["clients"]
    _all_st_col  = next((c for c in ["status","phase"] if c in _all_clients.columns), None)
    if _all_st_col:
        active_clients = len(_all_clients[_all_clients[_all_st_col].isin(["Active","Pilot"])])
        live_count     = len(_all_clients[_all_clients[_all_st_col] == "Active"])
        pilot_count    = len(_all_clients[_all_clients[_all_st_col] == "Pilot"])
    else:
        active_clients = len(_all_clients)
        live_count     = len(_all_clients)
        pilot_count    = 0

    _roi_col = _scol(monthly, "actual_roi_multiple", "roi_percent", "actual_roi")
    latest_roi_vals = (
        monthly.dropna(subset=[_roi_col]).sort_values("month").groupby("client_id")[_roi_col].last()
        if _roi_col else pd.Series(dtype=float)
    )
    portfolio_roi = latest_roi_vals.mean() if not latest_roi_vals.empty else 0

    all_months = monthly["month"].dropna().drop_duplicates().sort_values() if "month" in monthly.columns else pd.Series()
    if len(all_months) >= 2:
        this_m = all_months.iloc[-1]
        prev_m = all_months.iloc[-2]
        delta_hours   = (_to_num(monthly[monthly["month"]==this_m]["hours_saved"]).sum()
                       - _to_num(monthly[monthly["month"]==prev_m]["hours_saved"]).sum()) if "hours_saved" in monthly.columns else 0
        delta_savings = (_ssum(monthly[monthly["month"]==this_m], "cost_savings_usd","cost_savings")
                       - _ssum(monthly[monthly["month"]==prev_m], "cost_savings_usd","cost_savings"))
    else:
        delta_hours = delta_savings = 0

    # ── Ticket KPIs ────────────────────────────────────────────────────────────
    avg_resolution  = _smean(daily, "avg_resolution_hrs")
    avg_open        = _smean(daily, "tickets_open")
    total_hp        = _to_num(daily["high_priority_count"]).sum() if "high_priority_count" in daily.columns else None
    avg_hp_day      = _smean(daily, "high_priority_count")
    tickets_created = _to_num(daily["support_tickets_created"]).sum() if "support_tickets_created" in daily.columns else None
    tickets_closed  = _to_num(daily["tickets_closed"]).sum() if "tickets_closed" in daily.columns else None
    res_rate        = (tickets_closed / max(1, tickets_created) * 100) if (tickets_created and tickets_closed) else None
    net_benefit     = _ssum(monthly, "net_benefit_usd", "net_benefit_ytd", "net_benefit")
    delivery_total  = _ssum(monthly, "delivery_cost_usd", "delivery_cost")

    # Solutions live/pilot count
    sols = fd["solutions"]
    _sol_col = next((c for c in ["status","phase"] if c in sols.columns), None)
    live_sols  = len(sols[sols[_sol_col]=="Live"])  if (_sol_col and not sols.empty) else 0
    pilot_sols = len(sols[sols[_sol_col]=="Pilot"]) if (_sol_col and not sols.empty) else 0
    back_sols  = len(sols[~sols[_sol_col].isin(["Live","Pilot"])]) if (_sol_col and not sols.empty) else 0

    # 3yr net from financials
    fins_all = data["opp_financials"]
    if selected_client != "All Clients" and not fins_all.empty:
        fins_all = fins_all[fins_all["client_id"].isin(cids)]
    _net3yr_col = next((c for c in ["net_3yr_usd","net_3yr","net_three_year_usd"] if c in fins_all.columns), None)
    net3yr = _to_num(fins_all[_net3yr_col]).sum() if _net3yr_col else 0

    # ── Slim scorecard: colored top-border, compact height ────────────────────
    def slim_card(label, value, unit, delta, accent):
        delta_arrow = "▲ " if delta and delta.startswith("+") else ("▼ " if delta and delta.startswith("-") else "")
        delta_color = "#10B981" if delta_arrow == "▲ " else ("#EF4444" if delta_arrow == "▼ " else "#64748B")
        unit_html   = f'<span style="font-size:15px;font-weight:400;color:#64748B;margin-left:2px">{unit}</span>' if unit else ""
        delta_html  = f'<div style="font-size:11px;color:{delta_color};margin-top:5px">{delta_arrow}{delta}</div>' if delta else '<div style="height:16px"></div>'
        return f"""
        <div style="background:#0F1923;border:1px solid rgba(255,255,255,0.06);
                    border-top:2px solid {accent};border-radius:10px;
                    padding:16px 18px 14px 18px;min-height:96px">
          <div style="font-size:9px;font-weight:700;letter-spacing:1.8px;
                      text-transform:uppercase;color:#475569;margin-bottom:8px">{label}</div>
          <div style="font-size:28px;font-weight:700;line-height:1;
                      font-family:'DM Mono',monospace;color:{accent}">{value}{unit_html}</div>
          {delta_html}
        </div>"""

    delta_hrs_str = (f"+{fmt_num(delta_hours,0)} vs last month" if delta_hours >= 0
                     else f"{fmt_num(delta_hours,0)} vs last month")
    delta_sav_str = (f"+{fmt_currency(delta_savings)} vs last month" if delta_savings >= 0
                     else f"{fmt_currency(delta_savings)} vs last month")
    res_rate_val  = f"{res_rate:.0f}%" if res_rate is not None else "—"
    res_rate_sub  = (f"{int(tickets_closed):,} closed of {int(tickets_created):,} created"
                     if (tickets_closed and tickets_created) else "Ticket resolution rate")

    # ── Row 1: Automations / Hours / Cost / ROI ────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(slim_card("Total Automations Run", fmt_num(total_runs), "",
        f"+{success_rate:.1f}% success rate", "#00C9B1"), unsafe_allow_html=True)
    c2.markdown(slim_card("Total Hours Saved", fmt_num(total_hours), "hrs",
        delta_hrs_str, "#3B82F6"), unsafe_allow_html=True)
    c3.markdown(slim_card("Total Cost Savings", fmt_currency(total_savings), "",
        delta_sav_str, "#10B981"), unsafe_allow_html=True)
    c4.markdown(slim_card("Portfolio ROI", f"{portfolio_roi:.2f}", "×",
        f"vs delivery cost {fmt_currency(delivery_total)}", "#F59E0B"), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Row 2: Solutions / 3yr / Ticket Res / Avg Resolution ──────────────────
    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(slim_card("Live Solutions", str(live_sols), "",
        f"{pilot_sols} Pilot · {back_sols} Backlog", "#7C3AED"), unsafe_allow_html=True)
    c6.markdown(slim_card("3-Yr Net Value", fmt_currency(net3yr) if net3yr else "$0", "",
        "Portfolio business case total", "#F97316"), unsafe_allow_html=True)
    c7.markdown(slim_card("Ticket Res. Rate", res_rate_val, "",
        res_rate_sub, "#EC4899"), unsafe_allow_html=True)
    c8.markdown(slim_card("Avg Resolution Time",
        f"{avg_resolution:.0f}" if avg_resolution else "—", " hrs",
        "Avg ticket close time", "#06B6D4"), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Row 3: Backlog / High Priority / Net Benefit / Avg HP/Day ─────────────
    c9, c10, c11, c12 = st.columns(4)
    c9.markdown(slim_card("Avg Open Backlog",
        f"{avg_open:.0f}" if avg_open else "—", "",
        "Avg open tickets at any time", "#00C9B1"), unsafe_allow_html=True)
    c10.markdown(slim_card("High Priority Tickets",
        fmt_num(total_hp) if total_hp is not None else "—", "",
        "Total high/urgent raised", "#EF4444"), unsafe_allow_html=True)
    c11.markdown(slim_card("Net Benefit", fmt_currency(net_benefit), "",
        "Savings minus delivery cost", "#10B981"), unsafe_allow_html=True)
    c12.markdown(slim_card("Avg High Priority/Day",
        f"{avg_hp_day:.1f}" if avg_hp_day else "—", "",
        "Avg high priority per day", "#F59E0B"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


    # ── Row 3: ROI trend + Cost savings by client ──────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-hdr">Monthly ROI Trend</div>'
                    '<div class="section-sub">Actual ROI multiple · Selected period</div>', unsafe_allow_html=True)
        if _roi_col and not monthly.empty:
            roi_pivot = (monthly.dropna(subset=[_roi_col])
                                .pivot_table(index="month", columns="client_id", values=_roi_col, aggfunc="mean")
                                .reset_index())
            roi_pivot["month_str"] = roi_pivot["month"].dt.strftime("%b %Y")
            y_cols  = [c for c in cids if c in roi_pivot.columns]
            names   = [CLIENT_NAMES.get(c, c) for c in y_cols]
            colors  = [CLIENT_COLORS.get(c, PALETTE[i % len(PALETTE)]) for i, c in enumerate(y_cols)]
            if y_cols:
                fig = line_chart(roi_pivot, "month_str", y_cols, names=names, colors=colors, y_fmt=".2f")
                fig.update_yaxes(ticksuffix="x")
                fig.add_hline(y=0, line=dict(color="rgba(239,68,68,0.4)", width=1, dash="dot"))
                st.plotly_chart(fig, use_container_width=True, config=config())

    with col_b:
        st.markdown('<div class="section-hdr">Cost Savings by Client</div>'
                    '<div class="section-sub">Total savings in selected period · USD</div>', unsafe_allow_html=True)
        _sav_col = _scol(monthly, "cost_savings_usd", "cost_savings")
        if _sav_col and not monthly.empty:
            sav_by_client = (_to_num(monthly.groupby("client_id")[_sav_col].sum())
                             .reset_index()
                             .merge(data["clients"][["client_id","client_name"]], on="client_id", how="left"))
            sav_by_client = sav_by_client.sort_values(_sav_col, ascending=True)
            cols_mapped = [CLIENT_COLORS.get(c, TEAL) for c in sav_by_client["client_id"]]
            fig = bar_chart(sav_by_client, "client_name", _sav_col,
                            color=cols_mapped, horizontal=True)
            fig.update_xaxes(tickprefix="$", tickformat=",.0f")
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 4: Hours saved + Automation donut ─────────────────────────────────
    col_c, col_d = st.columns([2, 1])

    with col_c:
        st.markdown('<div class="section-hdr">Hours Saved by Month & Client</div>'
                    '<div class="section-sub">Stacked by client · Selected period</div>', unsafe_allow_html=True)
        if "hours_saved" in monthly.columns and not monthly.empty:
            hs_pivot = (monthly.pivot_table(index="month", columns="client_id",
                                            values="hours_saved", aggfunc="sum")
                               .fillna(0).reset_index())
            hs_pivot["month_str"] = hs_pivot["month"].dt.strftime("%b %Y")
            y_cols2 = [c for c in cids if c in hs_pivot.columns]
            names2  = [CLIENT_NAMES.get(c, c) for c in y_cols2]
            colors2 = [CLIENT_COLORS.get(c, PALETTE[i % len(PALETTE)]) for i, c in enumerate(y_cols2)]
            if y_cols2:
                fig = multi_bar(hs_pivot, "month_str", y_cols2, names=names2, colors=colors2, stacked=True)
                fig.update_yaxes(ticksuffix=" hrs")
                st.plotly_chart(fig, use_container_width=True, config=config())

    with col_d:
        st.markdown('<div class="section-hdr">Automation Success Rate</div>'
                    '<div class="section-sub">Runs successful vs failed</div>', unsafe_allow_html=True)
        fig = donut(
            ["Successful", "Failed"],
            [round(success_rate, 1), round(100 - success_rate, 1)],
            colors=[TEAL, "rgba(239,68,68,0.5)"],
        )
        fig.update_layout(
            annotations=[dict(text=f"<b>{success_rate:.1f}%</b>", x=0.5, y=0.5,
                              font_size=18, font_color="white", showarrow=False,
                              font=dict(family="DM Mono"))]
        )
        st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 5: Net benefit + Opps by value type ───────────────────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown('<div class="section-hdr">Net Benefit by Client</div>'
                    '<div class="section-sub">Benefit minus delivery cost · Selected period</div>', unsafe_allow_html=True)
        _nb_col = _scol(monthly, "net_benefit_usd", "net_benefit_ytd", "net_benefit")
        if _nb_col and not monthly.empty:
            net_pivot = (monthly.pivot_table(index="month", columns="client_id",
                                             values=_nb_col, aggfunc="sum")
                                .fillna(0).reset_index())
            net_pivot["month_str"] = net_pivot["month"].dt.strftime("%b %Y")
            y_cols3 = [c for c in cids if c in net_pivot.columns]
            names3  = [CLIENT_NAMES.get(c, c) for c in y_cols3]
            colors3 = [CLIENT_COLORS.get(c, PALETTE[i % len(PALETTE)]) for i, c in enumerate(y_cols3)]
            if y_cols3:
                fig = line_chart(net_pivot, "month_str", y_cols3, names=names3, colors=colors3)
                fig.update_yaxes(tickprefix="$", tickformat=",.0f")
                fig.add_hline(y=0, line=dict(color="rgba(239,68,68,0.4)", width=1, dash="dot"))
                st.plotly_chart(fig, use_container_width=True, config=config())

    with col_f:
        st.markdown('<div class="section-hdr">Opportunities by Value Driver</div>'
                    '<div class="section-sub">Primary value type across all opps</div>', unsafe_allow_html=True)
        _vt_col = _scol(opps, "value_type_primary", "value_type")
        if not opps.empty and _vt_col:
            vt = opps[_vt_col].value_counts().reset_index()
            vt.columns = ["type", "count"]
            fig = donut(vt["type"].tolist(), vt["count"].tolist())
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 6: Support health charts ──────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Support Health</div>'
                '<div class="section-sub">Ticket trends · Resolution performance · Backlog</div>',
                unsafe_allow_html=True)

    sh1, sh2 = st.columns(2)
    with sh1:
        st.plotly_chart(build_support_ticket_trend(daily, cids), use_container_width=True, config=config())
    with sh2:
        st.plotly_chart(build_resolution_time_trend(daily, cids), use_container_width=True, config=config())

    sh3, sh4 = st.columns(2)
    with sh3:
        st.plotly_chart(build_tickets_open_trend(daily, cids), use_container_width=True, config=config())
    with sh4:
        st.plotly_chart(build_high_priority_trend(daily, cids), use_container_width=True, config=config())

    # ── Summary table ──────────────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Client Summary Table</div>'
                '<div class="section-sub">Key metrics per client · Selected period</div>',
                unsafe_allow_html=True)

    summary_rows = []
    # Guard: only iterate if client_id column exists
    if "client_id" in data["clients"].columns:
        for _, cl in data["clients"].iterrows():
            try:
                cid  = cl["client_id"]
                # Safe filter — only filter if client_id col exists in each tab
                def _safe_filter(df, cid):
                    if df.empty or "client_id" not in df.columns:
                        return df
                    return df[df["client_id"] == cid]

                mon = _safe_filter(data["kpi_monthly"], cid)
                day = _safe_filter(data["kpi_daily"], cid)
                fin = _safe_filter(data["opp_financials"], cid)
                sol = _safe_filter(data["solutions"], cid)
                opp = _safe_filter(data["opportunities"], cid)

                _rc = _scol(mon, "actual_roi_multiple","roi_percent","actual_roi")
                latest_roi = (mon.dropna(subset=[_rc]).sort_values("month")[_rc].iloc[-1]
                              if _rc and not mon.dropna(subset=[_rc]).empty else None)

                _sc    = next((c for c in ["status","phase"] if c in sol.columns), None)
                live_s = len(sol[sol[_sc] == "Live"]) if _sc and not sol.empty else 0
                avg_res     = _to_num(day["avg_resolution_hrs"]).mean() if "avg_resolution_hrs" in day.columns else None
                avg_open_bl = _to_num(day["tickets_open"]).mean()       if "tickets_open" in day.columns else None

                summary_rows.append({
                    "Client":           cl.get("client_name", cid),
                    "Type":             cl.get("client_type", "—"),
                    "Solutions Live":   live_s,
                    "Hours Saved":      f'{_to_num(mon["hours_saved"]).sum():,.0f} hrs' if "hours_saved" in mon.columns else "—",
                    "Cost Savings":     fmt_currency(_ssum(mon,"cost_savings_usd","cost_savings")),
                    "ROI (Actual)":     f'{latest_roi:.2f}x' if latest_roi is not None else "—",
                    "Avg Resolution":   f'{avg_res:.0f} hrs' if avg_res and not np.isnan(avg_res) else "—",
                    "Avg Open Backlog": f'{avg_open_bl:.0f}' if avg_open_bl and not np.isnan(avg_open_bl) else "—",
                    "Open Opps":        len(opp[opp["initiative_status"].isin(["Backlog","In Pilot"])]) if "initiative_status" in opp.columns else 0,
                })
            except Exception:
                continue

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True, height=180)
