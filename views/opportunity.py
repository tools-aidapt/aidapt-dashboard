"""Page 3 — Opportunity Prioritisation Matrix"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    build_opportunity_bubble, build_value_by_function,
    fmt_currency, CLIENT_NAMES, CLIENT_COLORS, TEAL,
)


def _card(col, title, val, sub, color):
    col.markdown(f"""
    <div style='background:#111827;border-radius:8px;padding:14px 16px;
                border-left:3px solid {color}'>
      <div style='color:#9BA8B5;font-size:0.72rem;font-weight:600;text-transform:uppercase'>{title}</div>
      <div style='color:{color};font-size:1.4rem;font-weight:700;margin:4px 0 2px'>{val}</div>
      <div style='color:#9BA8B5;font-size:0.72rem'>{sub}</div>
    </div>""", unsafe_allow_html=True)


def render(data: dict, selected_client: str, filter_banner: str = ""):
    opps = data["opportunities"]
    fin  = data.get("opp_financials", pd.DataFrame())

    if selected_client != "All Clients":
        cid_row = data["clients"][data["clients"]["client_name"] == selected_client]
        if not cid_row.empty:
            cid  = cid_row.iloc[0]["client_id"]
            opps = opps[opps["client_id"] == cid]
            fin  = fin[fin["client_id"] == cid] if not fin.empty else fin
            cids = [cid]
        else:
            cids = []
    else:
        cids = list(CLIENT_NAMES.keys())

    st.markdown("""
    <div style='padding:16px 0 8px'>
      <h2 style='color:#E2E8F0;margin:0;font-size:1.5rem'>Opportunity Matrix</h2>
      <p style='color:#9BA8B5;margin:4px 0 0;font-size:0.85rem'>
        Portfolio prioritisation — value vs feasibility · bubble size = net annual benefit
      </p>
    </div>""", unsafe_allow_html=True)

    if filter_banner:
        st.markdown(filter_banner, unsafe_allow_html=True)

    # ── Scorecards ────────────────────────────────────────────────────────────
    _is_col  = next((c for c in ["initiative_status","status","opp_status"] if c in opps.columns), None)
    _nb_col  = next((c for c in ["net_benefit","net_benefit_risk_adj"] if c in fin.columns), None)
    _pb_col  = next((c for c in ["payback_months","payback_period_months","payback"] if c in fin.columns), None)

    status_counts = opps[_is_col].value_counts() if (_is_col and not opps.empty) else pd.Series()
    total_net3yr  = (pd.to_numeric(fin[_nb_col], errors="coerce").sum() * 3
                     if (_nb_col and not fin.empty) else 0)
    avg_payback   = (pd.to_numeric(fin[_pb_col], errors="coerce").mean()
                     if (_pb_col and not fin.empty) else np.nan)
    top_priority  = (pd.to_numeric(opps["priority_score"], errors="coerce").max()
                     if "priority_score" in opps.columns and not opps.empty else np.nan)

    c1, c2, c3, c4 = st.columns(4)
    _card(c1, "Total Opportunities", str(len(opps)),
          f"{status_counts.get('Live',0)} Live · {status_counts.get('Pilot',0)} Pilot · {status_counts.get('Backlog',0)} Backlog",
          "#00C9B1")
    _card(c2, "Portfolio 3-Yr Net Value",
          f"${total_net3yr:,.0f}" if total_net3yr else "—",
          "Cumulative net benefit at current pipeline", "#10B981")
    _card(c3, "Avg Payback Period",
          f"{avg_payback:.1f} mo" if not np.isnan(avg_payback) else "—",
          "Average months to recover implementation cost", "#F59E0B")
    _card(c4, "Top Priority Score",
          f"{top_priority:.1f}" if not np.isnan(top_priority) else "—",
          "Highest opportunity priority score (max 10)", "#8B5CF6")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Bubble + value by function ─────────────────────────────────────────────
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.plotly_chart(build_opportunity_bubble(opps, fin), use_container_width=True)
    with col_r:
        st.plotly_chart(build_value_by_function(opps, fin), use_container_width=True)

    # ── Full opportunity register ─────────────────────────────────────────────
    st.markdown("### Full Opportunity Register")
    if opps.empty:
        st.info("No opportunities found.")
        return

    merged = opps.copy()
    if not fin.empty:
        merge_cols = ["opp_id"] + [c for c in ["impl_cost","net_benefit","roi_multiple","payback_months"] if c in fin.columns]
        merged = merged.merge(fin[merge_cols], on="opp_id", how="left")

    _is_col2 = next((c for c in ["initiative_status","status"] if c in merged.columns), None)
    status_order  = {"Live": 0, "Pilot": 1, "In Pilot": 1, "Backlog": 2, "Paused": 3}
    status_colors = {"Live": "#00C9B1", "Pilot": "#3B82F6", "In Pilot": "#3B82F6",
                     "Backlog": "#F59E0B", "Paused": "#EF4444"}

    if _is_col2:
        merged["_sort"] = merged[_is_col2].map(status_order).fillna(9)
        merged = merged.sort_values(["_sort","priority_score"], ascending=[True, False])

    for _, row in merged.iterrows():
        status_val = row.get(_is_col2, "") if _is_col2 else ""
        color = status_colors.get(status_val, "#9BA8B5")
        cn    = CLIENT_NAMES.get(row["client_id"], row["client_id"])

        roi_str  = f"{row['roi_multiple']:.1f}×"   if pd.notnull(row.get("roi_multiple"))  else "—"
        net_str  = f"${row['net_benefit']:,.0f}/yr" if pd.notnull(row.get("net_benefit"))   else "—"
        pb_str   = f"{row['payback_months']:.0f} mo" if pd.notnull(row.get("payback_months")) else "—"
        impl_str = f"${row['impl_cost']:,.0f}"       if pd.notnull(row.get("impl_cost"))    else "—"
        ps_str   = f"{row['priority_score']:.1f}"   if pd.notnull(row.get("priority_score")) else "—"
        _vt = next((c for c in ["value_type_primary","value_type"] if c in row.index), None)
        vt_str = row[_vt] if _vt else "—"

        st.markdown(f"""
        <div style='background:#111827;border-radius:6px;padding:12px 16px;
                    margin:5px 0;border-left:3px solid {color}'>
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <div>
              <span style='color:#E2E8F0;font-weight:600;font-size:0.9rem'>{row.get('opp_name','—')}</span>
              <span style='color:#9BA8B5;font-size:0.8rem;margin-left:10px'>{row.get('opp_id','')}</span>
              <span style='background:{color}22;color:{color};font-size:0.7rem;padding:2px 6px;
                          border-radius:4px;margin-left:8px'>{status_val}</span>
            </div>
            <div style='color:#9BA8B5;font-size:0.8rem'>{cn}</div>
          </div>
          <div style='margin-top:6px;display:flex;gap:20px;flex-wrap:wrap;font-size:0.8rem'>
            <span style='color:#9BA8B5'>📂 {row.get('function','—')}</span>
            <span style='color:#9BA8B5'>🤖 {row.get('ai_pattern','—')}</span>
            <span style='color:#9BA8B5'>💡 {vt_str}</span>
            <span style='color:#F59E0B'>Priority {ps_str}</span>
            <span style='color:#10B981'>ROI {roi_str}</span>
            <span style='color:#00C9B1'>Net {net_str}</span>
            <span style='color:#9BA8B5'>Impl {impl_str}</span>
            <span style='color:#9BA8B5'>Payback {pb_str}</span>
          </div>
        </div>""", unsafe_allow_html=True)
