"""Page 1 — Executive Portfolio Overview"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, line_chart, multi_bar, bar_chart, donut,
    combo_chart, config, fmt_currency, fmt_num, fmt_pct,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, PALETTE,
    CLIENT_COLORS, CLIENT_NAMES,
)


def _filter(data, selected_client):
    """Return filtered copies of all dataframes."""
    clients_df = data["clients"]
    if selected_client == "All Clients":
        cids = clients_df["client_id"].tolist()
    else:
        cids = clients_df[clients_df["client_name"] == selected_client]["client_id"].tolist()
    return {k: df[df["client_id"].isin(cids)] if "client_id" in df.columns else df
            for k, df in data.items()}, cids


def render(data, selected_client):
    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-title">Executive Portfolio Overview</div>
        <div class="topbar-sub">
          {'All clients' if selected_client == 'All Clients' else selected_client}
          &nbsp;·&nbsp; Live data &nbsp;·&nbsp; Through Mar 2026
        </div>
      </div>
      <div class="topbar-badge">◎ PORTFOLIO</div>
    </div>
    """, unsafe_allow_html=True)

    fd, cids = _filter(data, selected_client)
    monthly = fd["kpi_monthly"]
    daily   = fd["kpi_daily"]
    clients = fd["clients"]
    opps    = fd["opportunities"]
    fins    = fd["opp_financials"]

    # ── Aggregate KPIs ─────────────────────────────────────────────────────────
    total_hours   = monthly["hours_saved"].sum()
    total_savings = monthly["cost_savings"].sum()
    total_runs    = daily["automation_runs_success"].sum()
    total_runs_f  = daily["automation_runs_failed"].sum()
    success_rate  = total_runs / max(1, total_runs + total_runs_f) * 100
    active_clients = len(clients[clients["status"].isin(["Active","Pilot"])])

    # ROI: use latest non-null month per client, then average
    latest_roi_vals = (
        monthly.dropna(subset=["roi_percent"])
               .sort_values("month")
               .groupby("client_id")["roi_percent"]
               .last()
    )
    portfolio_roi = latest_roi_vals.mean() if not latest_roi_vals.empty else 0

    # Deltas vs prev month
    this_month = monthly[monthly["month"] == monthly["month"].max()]
    prev_month = monthly[monthly["month"] == monthly["month"].drop_duplicates().nlargest(2).iloc[-1]]
    delta_hours   = this_month["hours_saved"].sum() - prev_month["hours_saved"].sum()
    delta_savings = this_month["cost_savings"].sum() - prev_month["cost_savings"].sum()
    delta_runs    = (daily[daily["date"].dt.month == daily["date"].dt.month.max()]["automation_runs_success"].sum()
                   - daily[daily["date"].dt.month == (daily["date"].dt.month.max()-1)]["automation_runs_success"].sum())

    # ── Scorecards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, kpi_card("Total Hours Saved", fmt_num(total_hours), "hrs",
                      f"{fmt_num(delta_hours,0)} vs last month", "up" if delta_hours>0 else "down", TEAL)),
        (c2, kpi_card("Total Cost Savings", fmt_currency(total_savings), "",
                      f"{fmt_currency(delta_savings)} vs last month", "up" if delta_savings>0 else "down", GREEN)),
        (c3, kpi_card("Portfolio ROI", f"{portfolio_roi:.2f}", "x",
                      "Latest month avg across clients", "flat", BLUE)),
        (c4, kpi_card("Automations Run", fmt_num(total_runs), "",
                      f"Success rate {success_rate:.1f}%", "up" if success_rate > 95 else "flat", PURPLE)),
        (c5, kpi_card("Active Clients", str(active_clients), f"/ {len(clients)}",
                      f"{len(clients[clients['status']=='Active'])} Live · {len(clients[clients['status']=='Pilot'])} Pilot",
                      "flat", GOLD)),
    ]
    for col, html in cards:
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Row 2: ROI trend + Cost savings by client ──────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-hdr">Monthly ROI Trend</div>'
                    '<div class="section-sub">Actual ROI multiple across all active clients</div>',
                    unsafe_allow_html=True)
        # Pivot monthly ROI by client
        roi_pivot = (monthly.dropna(subset=["roi_percent"])
                             .pivot_table(index="month", columns="client_id", values="roi_percent", aggfunc="mean")
                             .reset_index())
        roi_pivot["month_str"] = roi_pivot["month"].dt.strftime("%b %Y")

        y_cols  = [c for c in ["C001","C002","C003"] if c in roi_pivot.columns and c in cids]
        names   = [CLIENT_NAMES[c] for c in y_cols]
        colors  = [CLIENT_COLORS[c] for c in y_cols]

        if y_cols:
            fig = line_chart(roi_pivot, "month_str", y_cols, names=names,
                             colors=colors, y_fmt=".2f")
            fig.update_yaxes(ticksuffix="x")
            fig.add_hline(y=0, line=dict(color="rgba(239,68,68,0.4)", width=1, dash="dot"))
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_b:
        st.markdown('<div class="section-hdr">Cumulative Cost Savings by Client</div>'
                    '<div class="section-sub">Total savings since go-live · USD</div>',
                    unsafe_allow_html=True)
        sav_by_client = (monthly.groupby("client_id")["cost_savings"]
                                .sum().reset_index()
                                .merge(data["clients"][["client_id","client_name"]], on="client_id"))
        sav_by_client = sav_by_client.sort_values("cost_savings", ascending=True)
        cols_mapped = [CLIENT_COLORS.get(c, TEAL) for c in sav_by_client["client_id"]]
        fig = bar_chart(sav_by_client, "client_name", "cost_savings",
                        color=cols_mapped, horizontal=True, y_fmt="$,.0f")
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 3: Hours saved by client type + Automation success ─────────────────
    col_c, col_d = st.columns([2, 1])

    with col_c:
        st.markdown('<div class="section-hdr">Hours Saved by Month & Client</div>'
                    '<div class="section-sub">Stacked by client · Tracks ramp-up trajectory</div>',
                    unsafe_allow_html=True)
        hs_pivot = (monthly.pivot_table(index="month", columns="client_id",
                                        values="hours_saved", aggfunc="sum")
                           .fillna(0).reset_index())
        hs_pivot["month_str"] = hs_pivot["month"].dt.strftime("%b %Y")
        y_cols2 = [c for c in ["C001","C002","C003"] if c in hs_pivot.columns and c in cids]
        names2  = [CLIENT_NAMES[c] for c in y_cols2]
        colors2 = [CLIENT_COLORS[c] for c in y_cols2]
        if y_cols2:
            fig = multi_bar(hs_pivot, "month_str", y_cols2, names=names2,
                            colors=colors2, stacked=True, y_fmt=",.0f")
            fig.update_yaxes(ticksuffix=" hrs")
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_d:
        st.markdown('<div class="section-hdr">Automation Success Rate</div>'
                    '<div class="section-sub">Runs successful vs failed · All clients</div>',
                    unsafe_allow_html=True)
        fig = donut(
            ["Successful", "Failed"],
            [round(success_rate, 1), round(100 - success_rate, 1)],
            colors=[TEAL, "rgba(239,68,68,0.5)"],
        )
        # Centre annotation
        fig.update_layout(
            annotations=[dict(text=f"<b>{success_rate:.1f}%</b>", x=0.5, y=0.5,
                              font_size=18, font_color="white", showarrow=False,
                              font=dict(family="DM Mono"))]
        )
        st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 4: Net benefit YTD + Opps by value type ───────────────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown('<div class="section-hdr">Net Benefit YTD by Client</div>'
                    '<div class="section-sub">Benefit minus delivery cost · Cumulative</div>',
                    unsafe_allow_html=True)
        net_pivot = (monthly.pivot_table(index="month", columns="client_id",
                                         values="net_benefit_ytd", aggfunc="sum")
                            .fillna(0).reset_index())
        net_pivot["month_str"] = net_pivot["month"].dt.strftime("%b %Y")
        y_cols3 = [c for c in ["C001","C002","C003"] if c in net_pivot.columns and c in cids]
        names3  = [CLIENT_NAMES[c] for c in y_cols3]
        colors3 = [CLIENT_COLORS[c] for c in y_cols3]
        if y_cols3:
            fig = line_chart(net_pivot, "month_str", y_cols3, names=names3, colors=colors3)
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")
            fig.add_hline(y=0, line=dict(color="rgba(239,68,68,0.4)", width=1, dash="dot"))
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_f:
        st.markdown('<div class="section-hdr">Opportunities by Value Driver</div>'
                    '<div class="section-sub">Primary value type across all opps</div>',
                    unsafe_allow_html=True)
        if not opps.empty:
            vt = opps["value_type_primary"].value_counts().reset_index()
            vt.columns = ["type", "count"]
            fig = donut(vt["type"].tolist(), vt["count"].tolist())
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 5: Summary table ───────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Client Summary Table</div>'
                '<div class="section-sub">Key metrics per client · All time</div>',
                unsafe_allow_html=True)

    # Build summary
    summary_rows = []
    for _, cl in clients.iterrows():
        cid  = cl["client_id"]
        mon  = data["kpi_monthly"][data["kpi_monthly"]["client_id"] == cid]
        opp  = data["opportunities"][data["opportunities"]["client_id"] == cid]
        fin  = data["opp_financials"][data["opp_financials"]["client_id"] == cid]
        sol  = data["solutions"][data["solutions"]["client_id"] == cid]
        latest_roi = mon.dropna(subset=["roi_percent"]).sort_values("month")["roi_percent"].iloc[-1] if not mon.dropna(subset=["roi_percent"]).empty else None
        summary_rows.append({
            "Client":          cl["client_name"],
            "Type":            cl["client_type"],
            "Status":          cl["status"],
            "Solutions Live":  len(sol[sol["status"]=="Live"]),
            "Hours Saved":     f'{mon["hours_saved"].sum():,.0f} hrs',
            "Cost Savings":    fmt_currency(mon["cost_savings"].sum()),
            "ROI (Actual)":    f'{latest_roi:.2f}x' if latest_roi is not None else "—",
            "3yr Net Value":   fmt_currency(fin["net_3yr_usd"].sum()),
            "Avg Payback":     f'{fin["payback_months"].mean():.1f} mo' if not fin.empty else "—",
            "Open Opps":       len(opp[opp["initiative_status"].isin(["Backlog","In Pilot"])]),
        })

    st.dataframe(
        pd.DataFrame(summary_rows),
        use_container_width=True,
        hide_index=True,
        height=160,
    )
