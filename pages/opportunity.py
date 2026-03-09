"""Page 3 — Opportunity Prioritisation Matrix"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, bar_chart, donut, bubble_chart, multi_bar,
    config, fmt_currency, fmt_num, badge,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, PALETTE,
    CLIENT_COLORS, CLIENT_NAMES,
)


def render(data, selected_client):
    clients_df = data["clients"]

    if selected_client == "All Clients":
        cids = clients_df["client_id"].tolist()
        subtitle = "All clients"
    else:
        cl_row = clients_df[clients_df["client_name"] == selected_client].iloc[0]
        cids   = [cl_row["client_id"]]
        subtitle = selected_client

    opps = data["opportunities"][data["opportunities"]["client_id"].isin(cids)].copy()
    fins = data["opp_financials"][data["opp_financials"]["client_id"].isin(cids)].copy()

    merged = opps.merge(fins[["opp_id","roi_multiple_annual","payback_months",
                               "net_3yr_usd","hours_saved_annual",
                               "annual_total_benefit","annual_total_cost"]], on="opp_id", how="left")
    merged["client_name"] = merged["client_id"].map(CLIENT_NAMES)

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-title">Opportunity Prioritisation Matrix</div>
        <div class="topbar-sub">{subtitle} &nbsp;·&nbsp; {len(opps)} opportunities</div>
      </div>
      <div class="topbar-badge">◈ MATRIX</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Scorecards ─────────────────────────────────────────────────────────────
    total_opps  = len(opps)
    live_opps   = len(opps[opps["initiative_status"] == "Live"])
    pilot_opps  = len(opps[opps["initiative_status"] == "In Pilot"])
    avg_priority = opps["priority_score"].mean()
    total_net3yr = fins["net_3yr_usd"].sum()
    avg_payback  = fins["payback_months"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, html in [
        (c1, kpi_card("Total Opportunities", str(total_opps), "",
                      f"Across {len(opps['client_id'].unique())} client(s)", "flat", TEAL)),
        (c2, kpi_card("Live Automations", str(live_opps), "",
                      f"{pilot_opps} in pilot now", "up" if live_opps > 0 else "flat", GREEN)),
        (c3, kpi_card("In Pilot", str(pilot_opps), "",
                      "Being tested with real data", "flat", BLUE)),
        (c4, kpi_card("Avg Priority Score", f"{avg_priority:.2f}", "/ 5",
                      "Combined value + feasibility", "flat", PURPLE)),
        (c5, kpi_card("Portfolio 3yr Net Value", fmt_currency(total_net3yr), "",
                      f"Avg payback: {avg_payback:.1f} mo" if not np.isnan(avg_payback) else "—",
                      "flat", GOLD)),
    ]:
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Row 2: Bubble chart + Priority bar ─────────────────────────────────────
    col_a, col_b = st.columns([1.2, 1])

    with col_a:
        st.markdown('<div class="section-hdr">Value vs Feasibility Matrix</div>'
                    '<div class="section-sub">Bubble size = 3yr net value · Colour = client · Top-right = best bets</div>',
                    unsafe_allow_html=True)
        if not merged.empty:
            fig = bubble_chart(
                merged.fillna({"net_3yr_usd": 10000}),
                x="feasibility_score", y="value_score",
                size="net_3yr_usd", color_col="client_name",
                label_col="opp_id",
                colors=list(CLIENT_COLORS.values()),
            )
            # Quadrant labels
            fig.add_annotation(x=1.3, y=4.9, text="High Value,<br>Low Feasibility",
                               showarrow=False, font=dict(size=8, color="rgba(255,255,255,0.2)"))
            fig.add_annotation(x=4.0, y=4.9, text="✦ DO NOW",
                               showarrow=False, font=dict(size=9, color="rgba(0,201,177,0.4)", family="DM Sans"))
            fig.add_annotation(x=1.3, y=1.2, text="Low Priority",
                               showarrow=False, font=dict(size=8, color="rgba(255,255,255,0.2)"))
            fig.add_annotation(x=4.0, y=1.2, text="Quick Wins",
                               showarrow=False, font=dict(size=8, color="rgba(245,158,11,0.4)"))
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True, config=config())

    with col_b:
        st.markdown('<div class="section-hdr">Top Opportunities by Priority Score</div>'
                    '<div class="section-sub">Ranked highest to lowest · All filtered clients</div>',
                    unsafe_allow_html=True)
        if not merged.empty:
            top = merged.sort_values("priority_score", ascending=True).tail(8)
            top["label"] = top["opp_id"] + " · " + top["opp_name"].str[:25]
            colors_map = [CLIENT_COLORS.get(c, TEAL) + "CC" for c in top["client_id"]]
            fig = bar_chart(top, "label", "priority_score",
                            color=colors_map, horizontal=True)
            fig.update_xaxes(range=[0, 5.3])
            fig.add_vline(x=3.5, line=dict(color="rgba(245,158,11,0.4)", width=1, dash="dot"))
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Row 3: Status donut + Value type donut + Function bar ─────────────────
    col_c, col_d, col_e = st.columns(3)

    with col_c:
        st.markdown('<div class="section-hdr">Pipeline Status</div>'
                    '<div class="section-sub">Distribution by initiative status</div>',
                    unsafe_allow_html=True)
        sc = opps["initiative_status"].value_counts()
        order  = ["Backlog","In Pilot","Live"]
        labels = [s for s in order if s in sc.index]
        values = [sc[s] for s in labels]
        colors = ["rgba(100,116,139,0.8)","rgba(59,130,246,0.8)","rgba(0,201,177,0.85)"][:len(labels)]
        fig = donut(labels, values, colors=colors)
        st.plotly_chart(fig, use_container_width=True, config=config())

    with col_d:
        st.markdown('<div class="section-hdr">Value Driver Split</div>'
                    '<div class="section-sub">Primary value type of each opp</div>',
                    unsafe_allow_html=True)
        vc = opps["value_type_primary"].value_counts()
        fig = donut(vc.index.tolist(), vc.values.tolist(), colors=PALETTE)
        st.plotly_chart(fig, use_container_width=True, config=config())

    with col_e:
        st.markdown('<div class="section-hdr">Net 3yr Value by Function</div>'
                    '<div class="section-sub">USD · Stacked by client</div>',
                    unsafe_allow_html=True)
        if not merged.empty:
            fn_grp = (merged.groupby(["function","client_id"])["net_3yr_usd"]
                            .sum().reset_index()
                            .pivot(index="function", columns="client_id", values="net_3yr_usd")
                            .fillna(0).reset_index())
            c_cols = [c for c in ["C001","C002","C003"] if c in fn_grp.columns]
            c_names = [CLIENT_NAMES[c] for c in c_cols]
            c_clrs  = [CLIENT_COLORS[c]+"CC" for c in c_cols]
            fig = multi_bar(fn_grp, "function", c_cols, names=c_names,
                            colors=c_clrs, stacked=True)
            fig.update_yaxes(tickprefix="$", tickformat=",.0f")
            st.plotly_chart(fig, use_container_width=True, config=config())

    # ── Full portfolio register ────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Full Portfolio Register</div>'
                '<div class="section-sub">All opportunities · Sort any column · Export to CSV below</div>',
                unsafe_allow_html=True)

    if not merged.empty:
        reg = merged[[
            "opp_id","opp_name","client_name","function","initiative_status",
            "priority_score","value_type_primary","roi_multiple_annual",
            "payback_months","net_3yr_usd","hours_saved_annual","risk_tier","buy_build",
        ]].copy()
        reg.columns = [
            "ID","Opportunity","Client","Function","Status",
            "Priority","Value Type","Planned ROI",
            "Payback (mo)","3yr Net","Annual Hrs","Risk","Buy/Build",
        ]
        reg["Planned ROI"]  = reg["Planned ROI"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "—")
        reg["Payback (mo)"] = reg["Payback (mo)"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
        reg["3yr Net"]      = reg["3yr Net"].apply(fmt_currency)
        reg["Annual Hrs"]   = reg["Annual Hrs"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "—")
        reg["Priority"]     = reg["Priority"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        st.dataframe(reg, use_container_width=True, hide_index=True)

        # CSV export
        csv = reg.to_csv(index=False).encode("utf-8")
        st.download_button("⬇  Export to CSV", csv,
                           file_name="aidapt_opportunity_register.csv",
                           mime="text/csv")
