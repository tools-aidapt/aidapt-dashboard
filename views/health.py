"""Page 4 — Data Health Check"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.charts import (
    kpi_card, fmt_currency, fmt_num,
    TEAL, BLUE, PURPLE, GOLD, GREEN, RED, CLIENT_NAMES,
)

# ── Column aliases ─────────────────────────────────────────────────────────────
_COL_ALIASES = {
    "net_benefit_risk_adj":        ["net_benefit_risk_adj", "net_benefit_risk_adjusted", "net_benefit"],
    "hours_saved_annual":          ["hours_saved_annual", "annual_hours_saved", "hours_saved_per_year"],
    "net_3yr_usd":                 ["net_3yr_usd", "net_3yr", "net_three_year_usd", "net_3year_usd"],
    "roi_multiple_annual":         ["roi_multiple_annual", "roi_multiple", "annual_roi_multiple", "roi_x"],
    "annual_total_benefit":        ["annual_total_benefit", "total_annual_benefit", "annual_benefit"],
    "annual_total_cost":           ["annual_total_cost", "total_annual_cost", "annual_cost"],
    "payback_months":              ["payback_months", "payback_period_months", "payback"],
    "annual_productivity_benefit": ["annual_productivity_benefit", "productivity_benefit", "annual_prod_benefit"],
    "minutes_saved_per_unit":      ["minutes_saved_per_unit", "mins_saved_per_unit", "minutes_per_unit"],
    "annual_volume_units":         ["annual_volume_units", "annual_volume", "volume_units", "annual_vol"],
    "adoption_pct":                ["adoption_pct", "adoption_percent", "adoption_rate"],
    "fully_loaded_cost_usd_hr":    ["fully_loaded_cost_usd_hr", "fte_hourly_rate_usd", "cost_per_hour", "hourly_rate"],
    "quality_savings_usd_yr":      ["quality_savings_usd_yr", "quality_savings", "quality_benefit"],
    "impl_cost_usd":               ["impl_cost_usd", "implementation_cost", "impl_cost"],
    "annual_license_cost_usd":     ["annual_license_cost_usd", "license_cost", "annual_license_cost"],
    "risk_haircut_pct":            ["risk_haircut_pct", "risk_haircut", "risk_pct"],
}

def _col(df, canonical):
    for c in _COL_ALIASES.get(canonical, [canonical]):
        if c in df.columns:
            return c
    return None

def _val(row, canonical, default=0):
    """Get a value from a row by canonical name, returning default if not found."""
    c = _col(row.to_frame().T if isinstance(row, pd.Series) else row, canonical)
    if c is None:
        return default
    v = row[c] if isinstance(row, pd.Series) else row.get(c, default)
    try:
        return float(v) if pd.notna(v) else default
    except (TypeError, ValueError):
        return default


def render(data, selected_client, filter_banner=""):
    st.markdown("""
    <div class="topbar">
      <div>
        <div class="topbar-title">Data Health Check</div>
        <div class="topbar-sub">Completeness · Freshness · Formula validation</div>
      </div>
      <div class="topbar-badge">⊟ HEALTH</div>
    </div>
    """, unsafe_allow_html=True)

    if filter_banner:
        st.markdown(filter_banner, unsafe_allow_html=True)

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
        "OPP_FINANCIALS": (data["opp_financials"], ["client_id","opp_id",
                                                     _col(data["opp_financials"], "roi_multiple_annual") or "roi_multiple_annual",
                                                     _col(data["opp_financials"], "payback_months") or "payback_months",
                                                     _col(data["opp_financials"], "net_3yr_usd") or "net_3yr_usd"]),
        "SOLUTIONS":      (data["solutions"],      ["client_id","solution_id","go_live_date","status"]),
    }
    for tab, (df, req_cols) in tab_checks.items():
        # Filter to only cols that exist in the df
        existing_req = [c for c in req_cols if c in df.columns]
        missing_req  = [c for c in req_cols if c not in df.columns]
        total  = len(df) * len(req_cols) if len(df) > 0 else 1
        filled = sum(df[c].notna().sum() for c in existing_req)
        pct    = round(filled / max(1, total) * 100, 1)
        null_counts = {c: int(df[c].isna().sum()) for c in existing_req if df[c].isna().sum() > 0}
        status = "✅ Complete" if pct == 100 and not missing_req else ("⚠️ Partial" if pct > 70 else "❌ Incomplete")
        note = str(null_counts) if null_counts else ("—" if not missing_req else f"Missing cols: {missing_req}")
        checks.append({
            "Sheet": tab, "Rows": len(df), "Required Fields": len(req_cols),
            "Completeness": f"{pct}%", "Status": status,
            "Nulls in key cols": note,
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
            "Client":           cl["client_name"],
            "Type":             cl["client_type"],
            "Last KPI_DAILY":   str(daily_last.date()) if pd.notna(daily_last) else "No data",
            "Last KPI_MONTHLY": str(monthly_last.date()) if pd.notna(monthly_last) else "No data",
            "Opportunities":    opps_count,
            "Financial Models": fins_count,
            "Models = Opps?":   "✅" if opps_count == fins_count else "⚠️ Mismatch",
        })

    st.dataframe(pd.DataFrame(freshness), use_container_width=True, hide_index=True)

    # ── Formula spot-check ─────────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Formula Spot-Check</div>'
                '<div class="section-sub">Verifies key calculations are within expected ranges (10% tolerance)</div>',
                unsafe_allow_html=True)

    fin = data["opp_financials"].copy()

    # Check which input columns actually exist — only run formula checks for rows
    # where all required inputs are present.
    required_input_cols = ["minutes_saved_per_unit", "annual_volume_units",
                           "adoption_pct", "fully_loaded_cost_usd_hr"]
    input_cols_present = [_col(fin, c) for c in required_input_cols]
    can_check_formula  = all(c is not None for c in input_cols_present)

    formula_checks = []

    for _, row in fin.iterrows():
        opp_id = row.get("opp_id", "?")

        if not can_check_formula:
            # Can't recalculate — just report what's stored
            roi_stored = _val(row, "roi_multiple_annual")
            pb_stored  = _val(row, "payback_months")
            formula_checks.append({
                "Opp ID":               opp_id,
                "Productivity Benefit": "⚠️ Input cols missing",
                "Net Benefit":          "⚠️ Input cols missing",
                "ROI Multiple":         f"Stored: {roi_stored:.2f}" if roi_stored else "—",
                "Overall":              "⚠️ Cannot verify",
            })
            continue

        # Pull all inputs using alias lookup
        mins_saved   = _val(row, "minutes_saved_per_unit")
        annual_vol   = _val(row, "annual_volume_units")
        adoption     = _val(row, "adoption_pct")
        # adoption may be stored as 0.75 or 75 — normalise to 0–1
        if adoption > 1:
            adoption = adoption / 100.0
        hourly_rate  = _val(row, "fully_loaded_cost_usd_hr")
        qual_savings = _val(row, "quality_savings_usd_yr")
        impl_cost    = _val(row, "impl_cost_usd")
        lic_cost     = _val(row, "annual_license_cost_usd")
        risk_haircut = _val(row, "risk_haircut_pct")
        # risk_haircut may be 0.20 or 20
        if risk_haircut > 1:
            risk_haircut = risk_haircut / 100.0

        # Recalculate expected values
        expected_prod  = (mins_saved * annual_vol * adoption * hourly_rate) / 60
        expected_total = expected_prod + qual_savings
        expected_cost  = impl_cost + lic_cost
        expected_net   = (expected_total - expected_cost) * (1 - risk_haircut)
        expected_roi   = round(expected_net / max(1, expected_cost), 2)

        # Stored values
        stored_prod = _val(row, "annual_productivity_benefit")
        stored_net  = _val(row, "net_benefit_risk_adj")
        stored_roi  = _val(row, "roi_multiple_annual")

        def _check(stored, expected, pct=0.10, min_abs=100):
            """
            Returns (status_str, is_ok).
            Handles three cases:
              ✅  values match within tolerance
              ⚠️  values match in magnitude but sign is flipped (sheet stores abs value)
              ❌  values genuinely differ
            """
            if expected == 0:
                ok = abs(stored - expected) < min_abs
                return ("✅", True) if ok else (f"❌ (got {stored:,.2f}, expected {expected:,.2f})", False)

            tol = max(abs(expected) * pct, min_abs)
            # Exact match within tolerance
            if abs(stored - expected) <= tol:
                return ("✅", True)
            # Sign-flip: magnitudes match but signs differ — sheet stores absolute value
            if abs(abs(stored) - abs(expected)) <= tol and stored * expected < 0:
                return (f"⚠️ Sign issue: stored {stored:,.0f} but should be {expected:,.0f} "
                        f"(costs exceed benefits — update sheet)", False)
            # Genuine mismatch
            return (f"❌ (got {stored:,.0f}, expected {expected:,.0f})", False)

        def _check_roi(stored, expected):
            tol = max(abs(expected) * 0.10, 0.05)
            if abs(stored - expected) <= tol:
                return ("✅", True)
            if abs(abs(stored) - abs(expected)) <= tol and stored * expected < 0:
                return (f"⚠️ Sign issue: stored {stored:.2f} but should be {expected:.2f}", False)
            return (f"❌ (got {stored:.2f}, expected {expected:.2f})", False)

        prod_str, prod_ok = _check(stored_prod, expected_prod)
        net_str,  net_ok  = _check(stored_net,  expected_net)
        roi_str,  roi_ok  = _check_roi(stored_roi, expected_roi)
        all_ok = prod_ok and net_ok and roi_ok

        # Business viability flag — negative net benefit means costs exceed benefits
        if expected_net < 0:
            viability = "⚠️ Costs > Benefits"
        elif expected_roi < 1:
            viability = "⚠️ ROI < 1x"
        else:
            viability = f"✅ ROI {expected_roi:.1f}x"

        formula_checks.append({
            "Opp ID":               opp_id,
            "Productivity Benefit": prod_str,
            "Net Benefit":          net_str,
            "ROI Multiple":         roi_str,
            "Business Viability":   viability,
            "Overall":              "✅ Pass" if all_ok else ("⚠️ Sign Fix Needed" if not all_ok and "Sign issue" in (net_str + roi_str) else "❌ Fail"),
        })

    if formula_checks:
        st.dataframe(pd.DataFrame(formula_checks), use_container_width=True, hide_index=True)

        passes       = sum(1 for r in formula_checks if r["Overall"] == "✅ Pass")
        sign_issues  = sum(1 for r in formula_checks if "Sign Fix" in r["Overall"])
        fails        = sum(1 for r in formula_checks if r["Overall"] == "❌ Fail")
        total        = len(formula_checks)

        if passes == total:
            st.success(f"✅ All {total} formula checks passed.")
        else:
            msgs = []
            if sign_issues:
                msgs.append(f"**{sign_issues} sign issue(s):** Your sheet stores the absolute value of net benefit / ROI "
                            f"but the formula expects a negative number (because costs exceed benefits). "
                            f"In your OPP_FINANCIALS sheet, update the `net_benefit_risk_adj` and `roi_multiple_annual` "
                            f"cells for those rows to show the negative value, or revisit the business case inputs "
                            f"(reduce `impl_cost_usd`, increase `annual_volume_units`, or lower `risk_haircut_pct`).")
            if fails:
                msgs.append(f"**{fails} calculation mismatch(es):** Stored values differ from what the formula "
                            f"calculates by >10%. Check those rows in OPP_FINANCIALS and correct the inputs "
                            f"or the calculated columns.")
            st.warning(f"{passes}/{total} passed.\n\n" + "\n\n".join(msgs))
    else:
        st.info("No financial records found to check.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.info("💡  **How to use this page:** Run a health check each time you onboard a new client "
            "or update data. Any ❌ rows indicate missing fields or calculation mismatches "
            "that need to be fixed in the Google Sheet before sharing with stakeholders.")
