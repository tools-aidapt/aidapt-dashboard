"""
Data Loader — reads from Google Sheets (live) or local Excel (fallback/demo).

Priority:
1. If GOOGLE_SHEET_ID is set in secrets/env → reads from Google Sheets via gspread
2. Otherwise → reads from local demo_data.xlsx (bundled with the app)

To connect live data:
  - Set GOOGLE_SHEET_ID in .streamlit/secrets.toml
  - Set GOOGLE_SERVICE_ACCOUNT JSON in .streamlit/secrets.toml
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

# ── Cache: refresh every 5 minutes ────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Loading data…")
def load_all_data() -> dict:
    """Returns dict of DataFrames keyed by sheet/tab name."""
    # Check if GOOGLE_SHEET_ID is set in secrets
    try:
        sheet_id = st.secrets["GOOGLE_SHEET_ID"]
    except (KeyError, FileNotFoundError):
        sheet_id = None

    if sheet_id:
        try:
            return _load_from_sheets(sheet_id)
        except Exception as e:
            st.error(f"Google Sheets connection failed: {e}")
            st.warning("Check: (1) Sheet is saved as Google Sheets not .xlsx  (2) Sheet is shared with your service account email  (3) GOOGLE_SHEET_ID in secrets matches the actual Sheet URL")
            st.stop()

    return _load_demo_data()


def _load_from_sheets(sheet_id: str) -> dict:
    """Load all tabs from a Google Sheet using a service account."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    sa_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds   = Credentials.from_service_account_info(sa_info, scopes=scopes)
    gc      = gspread.authorize(creds)
    sh      = gc.open_by_key(sheet_id)

    # Row 1 = banner, Row 2 = headers, Row 3+ = data
    # tabs where row 3 is also a helper/note row (skip it too)
    tab_map = {
        "CLIENTS":        ("clients",       2, 3),
        "KPI_DAILY":      ("kpi_daily",     2, 4),
        "KPI_MONTHLY":    ("kpi_monthly",   2, 4),
        "OPPORTUNITIES":  ("opportunities", 3, 4),
        "OPP_FINANCIALS": ("opp_financials",3, 4),
        "SOLUTIONS":      ("solutions",     2, 3),
        "BASELINES":      ("baselines",     2, 3),
    }
    out = {}
    for sheet_name, (key, header_row, data_start_row) in tab_map.items():
        ws       = sh.worksheet(sheet_name)
        all_vals = ws.get_all_values()
        # Row index is 0-based in the list
        headers  = all_vals[header_row - 1]
        rows     = all_vals[data_start_row - 1:]
        # Remove completely empty rows
        rows = [r for r in rows if any(v.strip() for v in r)]
        df   = pd.DataFrame(rows, columns=headers)
        out[key] = _clean_df(df, key)
    return out


def _clean_df(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Convert all columns coming from Google Sheets (everything is string) into
    correct types: dates → datetime, numbers → float/int, rest stays string.
    """
    df = df.copy()

    # ── Date columns ──────────────────────────────────────────────────────────
    date_cols = {
        "kpi_daily":  ["date"],
        "kpi_monthly": ["month"],
        "solutions":  ["kickoff_date", "go_live_date"],
        "baselines":  ["baseline_start", "baseline_end", "captured_at"],
    }
    for col in date_cols.get(key, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # ── Numeric columns — try every object column ─────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        # Clean common formatting characters from Sheets
        cleaned = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.replace("x", "", regex=False)   # e.g. "2.40x"
            .str.replace("—", "", regex=False)   # em-dash placeholder
            .str.replace("-", "", regex=False)   # formula fallback "-"
            .str.replace(" ", "", regex=False)
        )
        # Only convert if the majority of non-empty values look numeric
        # errors="coerce" means ANY malformed value (e.g. "13.67.6") → NaN, never crashes
        numeric_attempt = pd.to_numeric(cleaned, errors="coerce")
        non_null_orig   = df[col].replace(["", "—", "-", None], np.nan).dropna()
        non_null_num    = numeric_attempt.dropna()
        if len(non_null_orig) == 0 or len(non_null_num) / max(len(non_null_orig), 1) >= 0.7:
            df[col] = numeric_attempt  # convert — mostly numeric, bad values become NaN
        # else leave as string (e.g. opp_name, client_name etc.)

    return df


# ── Demo data (fully calculated, picture-perfect) ─────────────────────────────
def _load_demo_data() -> dict:
    """Generate realistic demo data matching KPI Mart v2 schema exactly."""

    # ── CLIENTS ────────────────────────────────────────────────────────────────
    clients = pd.DataFrame([
        {"client_id": "C001", "client_name": "Alpha Retail",
         "client_type": "AI Transformation", "industry": "Retail",
         "fte_count": 120, "annual_revenue_usd": 8_500_000,
         "fte_hourly_rate_usd": 65, "status": "Active",
         "start_date": "2026-01-06", "primary_contact_email": "alpha@example.com"},
        {"client_id": "C002", "client_name": "Beta Logistics",
         "client_type": "Data / Analytics", "industry": "Logistics",
         "fte_count": 80, "annual_revenue_usd": 5_200_000,
         "fte_hourly_rate_usd": 55, "status": "Active",
         "start_date": "2026-01-20", "primary_contact_email": "beta@example.com"},
        {"client_id": "C003", "client_name": "Gamma Finance",
         "client_type": "Operations / Process", "industry": "Financial Services",
         "fte_count": 200, "annual_revenue_usd": 15_000_000,
         "fte_hourly_rate_usd": 75, "status": "Pilot",
         "start_date": "2026-02-03", "primary_contact_email": "gamma@example.com"},
    ])

    # ── SOLUTIONS ──────────────────────────────────────────────────────────────
    solutions = pd.DataFrame([
        {"client_id": "C001", "solution_id": "S101", "solution_name": "AI Ticket Triage",
         "kickoff_date": "2025-12-24", "go_live_date": "2026-01-18", "status": "Live", "time_to_go_live_days": 25},
        {"client_id": "C001", "solution_id": "S102", "solution_name": "KB Auto-Tagging",
         "kickoff_date": "2026-01-29", "go_live_date": "2026-02-10", "status": "Live", "time_to_go_live_days": 12},
        {"client_id": "C002", "solution_id": "S201", "solution_name": "Shipment Exception Resolver",
         "kickoff_date": "2026-01-18", "go_live_date": "2026-02-05", "status": "Live", "time_to_go_live_days": 18},
        {"client_id": "C003", "solution_id": "S301", "solution_name": "Regulatory Doc Summariser",
         "kickoff_date": "2026-01-21", "go_live_date": "2026-02-15", "status": "Live", "time_to_go_live_days": 25},
    ])

    # ── OPPORTUNITIES ──────────────────────────────────────────────────────────
    opportunities = pd.DataFrame([
        {"client_id": "C001", "opp_id": "OPP-001", "opp_name": "AI Ticket Triage & Draft Response",
         "function": "Support", "tier": "Tier 1", "ai_pattern": "Grounded Q&A (RAG)",
         "value_type_primary": "Productivity", "value_type_secondary": "Quality",
         "plan_classification": "Active Pilot", "initiative_status": "In Pilot",
         "feasibility_score": 3.8, "value_score": 4.2, "priority_score": 4.0,
         "risk_tier": "Medium", "buy_build": "Buy", "hitl_level": "Approve-to-send",
         "pilot_candidate": "Yes", "primary_kpis": "TTFR, edit_rate, resolution_rate",
         "notes": "Phase 1: 2 product lines"},
        {"client_id": "C001", "opp_id": "OPP-002", "opp_name": "Smart KB Article Auto-Tagging",
         "function": "Support", "tier": "Tier 2", "ai_pattern": "Classification",
         "value_type_primary": "Quality", "value_type_secondary": "Productivity",
         "plan_classification": "Backlog", "initiative_status": "Backlog",
         "feasibility_score": 4.1, "value_score": 3.5, "priority_score": 3.8,
         "risk_tier": "Low", "buy_build": "Buy", "hitl_level": "Auto-approve",
         "pilot_candidate": "No", "primary_kpis": "kb_accuracy, search_time",
         "notes": "Dependency: KB hygiene sprint first"},
        {"client_id": "C002", "opp_id": "OPP-003", "opp_name": "Shipment Exception Auto-Resolution",
         "function": "Operations", "tier": "Tier 1", "ai_pattern": "Workflow Automation",
         "value_type_primary": "Productivity", "value_type_secondary": "OpEx Reduction",
         "plan_classification": "Active Pilot", "initiative_status": "In Pilot",
         "feasibility_score": 3.2, "value_score": 4.5, "priority_score": 3.9,
         "risk_tier": "Medium", "buy_build": "Build", "hitl_level": "Human-in-loop",
         "pilot_candidate": "Yes", "primary_kpis": "exceptions_resolved, handling_time",
         "notes": "ERP integration required"},
        {"client_id": "C002", "opp_id": "OPP-004", "opp_name": "Carrier Invoice Anomaly Detection",
         "function": "Finance", "tier": "Tier 2", "ai_pattern": "Anomaly Detection",
         "value_type_primary": "Quality", "value_type_secondary": "Revenue",
         "plan_classification": "Backlog", "initiative_status": "Backlog",
         "feasibility_score": 3.9, "value_score": 4.0, "priority_score": 3.95,
         "risk_tier": "Low", "buy_build": "Buy", "hitl_level": "Approve-to-pay",
         "pilot_candidate": "No", "primary_kpis": "invoice_error_rate, recovery_amt",
         "notes": "SOX controls apply"},
        {"client_id": "C003", "opp_id": "OPP-005", "opp_name": "Regulatory Document Summarisation",
         "function": "Finance", "tier": "Tier 1", "ai_pattern": "Summarisation",
         "value_type_primary": "Productivity", "value_type_secondary": "Compliance",
         "plan_classification": "Live", "initiative_status": "Live",
         "feasibility_score": 4.5, "value_score": 3.8, "priority_score": 4.15,
         "risk_tier": "High", "buy_build": "Buy", "hitl_level": "Approve-to-send",
         "pilot_candidate": "Yes", "primary_kpis": "docs_processed, time_saved",
         "notes": "GDPR guardrails in place"},
    ])

    # ── OPP_FINANCIALS (all calculated correctly) ──────────────────────────────
    def calc_fin(mins_saved, vol, adoption, rate, quality_savings, impl_cost, license_cost, risk_haircut):
        annual_prod  = (mins_saved * vol * adoption * rate) / 60
        annual_qual  = quality_savings
        total_benefit = annual_prod + annual_qual
        total_cost    = impl_cost + license_cost
        net           = (total_benefit - total_cost) * (1 - risk_haircut)
        roi_mult      = round(net / total_cost, 2) if total_cost > 0 else 0
        payback       = round((impl_cost / max(net / 12, 1)), 1)
        gross_3yr     = total_benefit * 3
        net_3yr       = (total_benefit * 3) - (impl_cost + license_cost * 3)
        hours_saved   = (mins_saved * vol * adoption) / 60
        return {
            "annual_productivity_benefit": round(annual_prod),
            "annual_quality_benefit":      round(annual_qual),
            "annual_total_benefit":        round(total_benefit),
            "annual_total_cost":           round(total_cost),
            "net_benefit_risk_adj":        round(net),
            "roi_multiple_annual":         roi_mult,
            "payback_months":              payback,
            "gross_3yr_usd":               round(gross_3yr),
            "net_3yr_usd":                 round(net_3yr),
            "hours_saved_annual":          round(hours_saved),
        }

    fin_inputs = {
        "OPP-001": (5,  24000, 0.75, 65, 15000, 45000, 18000, 0.20),
        "OPP-002": (3,  18000, 0.60, 65,  8000, 12000,  6000, 0.25),
        "OPP-003": (12,  8000, 0.80, 55, 22000, 80000, 24000, 0.15),
        "OPP-004": (8,   5000, 0.70, 55, 35000, 25000, 12000, 0.20),
        "OPP-005": (25,  3000, 0.90, 75,  5000, 30000, 15000, 0.10),
    }
    fin_rows = []
    for opp_id, (mins, vol, adp, rate, qual, impl, lic, risk) in fin_inputs.items():
        c_id = opp_id[:5].replace("PP-0", "00").replace("OPP", "")
        cmap = {"OPP-001": "C001","OPP-002":"C001","OPP-003":"C002","OPP-004":"C002","OPP-005":"C003"}
        row = {"client_id": cmap[opp_id], "opp_id": opp_id,
               "minutes_saved_per_unit": mins, "annual_volume_units": vol,
               "adoption_pct": adp, "fully_loaded_cost_usd_hr": rate,
               "quality_savings_usd_yr": qual, "impl_cost_usd": impl,
               "annual_license_cost_usd": lic, "risk_haircut_pct": risk}
        row.update(calc_fin(mins, vol, adp, rate, qual, impl, lic, risk))
        fin_rows.append(row)
    opp_financials = pd.DataFrame(fin_rows)

    # ── KPI_DAILY (90 days, 3 clients, realistic ramp-up) ─────────────────────
    daily_rows = []
    start = date(2025, 12, 21)
    go_live = {"C001": date(2026, 1, 18), "C002": date(2026, 2, 5), "C003": date(2026, 2, 15)}
    sol2_live = {"C001": date(2026, 2, 10)}
    rng = np.random.default_rng(42)

    for cid in ["C001", "C002", "C003"]:
        gl = go_live[cid]
        for d in (start + timedelta(n) for n in range(73)):
            if d > date(2026, 3, 3):
                break
            days_live = max(0, (d - gl).days)
            if days_live == 0:
                runs_s, runs_f, tickets = 0, 0, 0
            else:
                # Ramp: 0→full over 14 days, then steady with noise
                base = {"C001": 420, "C002": 160, "C003": 95}[cid]
                ramp = min(1.0, days_live / 14)
                # Sol2 adds volume for C001
                if cid == "C001" and d >= sol2_live.get("C001", date(2099,1,1)):
                    base += 180
                runs_s = max(0, int(base * ramp * rng.normal(1.0, 0.05)))
                fail_rate = 0.038
                runs_f  = max(0, int(runs_s * fail_rate * rng.normal(1.0, 0.2)))
                ticket_base = {"C001": 3, "C002": 2, "C003": 1}[cid]
                tickets = max(0, int(ticket_base * rng.normal(1.0, 0.3)))

            total_runs = runs_s + runs_f
            tpr = round((tickets / total_runs * 100), 2) if total_runs > 0 else 0.0
            sr  = round(runs_s / total_runs, 4) if total_runs > 0 else 0.0
            mins_per_run = {"C001": 5, "C002": 12, "C003": 25}[cid]
            hours_saved  = round(runs_s * mins_per_run / 60, 2)
            daily_rows.append({
                "client_id": cid, "date": pd.Timestamp(d),
                "solutions_deployed": 1 if d >= gl else 0,
                "automation_runs_success": runs_s, "automation_runs_failed": runs_f,
                "support_tickets_created": tickets, "tickets_per_100_runs": tpr,
                "success_rate": sr, "hours_saved": hours_saved, "notes": None,
            })
    kpi_daily = pd.DataFrame(daily_rows)

    # ── KPI_MONTHLY (calculated from daily + financial model) ─────────────────
    # Hourly rates per client
    hrly = {"C001": 65, "C002": 55, "C003": 75}
    delivery_cost = {"C001": {"2026-01": 18000, "2026-02": 14400, "2026-03": 12000},
                     "C002": {"2026-01": 14000, "2026-02": 11200, "2026-03": 10000},
                     "C003": {"2026-01":     0, "2026-02":  7200, "2026-03":  6000}}
    rev_gen = {"C001": {"2026-01": 0, "2026-02": 12000, "2026-03": 18000},
               "C002": {"2026-01": 0, "2026-02":     0, "2026-03":  5000},
               "C003": {"2026-01": 0, "2026-02":     0, "2026-03":  2000}}

    monthly_rows = []
    kpi_daily["month_str"] = kpi_daily["date"].dt.strftime("%Y-%m")
    for cid in ["C001","C002","C003"]:
        for mon_str in ["2025-12","2026-01","2026-02","2026-03"]:
            sub = kpi_daily[(kpi_daily["client_id"]==cid) & (kpi_daily["month_str"]==mon_str)]
            hs  = round(sub["hours_saved"].sum(), 1)
            savings = round(hs * hrly[cid])
            dc   = delivery_cost.get(cid, {}).get(mon_str, 0)
            rg   = rev_gen.get(cid, {}).get(mon_str, 0)
            total_val = savings + rg
            roi = round((total_val - dc) / dc, 4) if dc > 0 else None
            runs_total = sub["automation_runs_success"].sum() + sub["automation_runs_failed"].sum()
            eff = round(sub["hours_saved"].sum() / max(1, sub["automation_runs_success"].sum() + 0.01) * 100 / 25, 4)
            # avg time to go live
            sol_sub = solutions[(solutions["client_id"]==cid)]
            avg_ttgl = sol_sub["time_to_go_live_days"].mean() if not sol_sub.empty else None

            # planned roi (from financials)
            fin_sub = opp_financials[opp_financials["client_id"]==cid]
            planned_roi = fin_sub["roi_multiple_annual"].mean() if not fin_sub.empty else None

            net_benefit = round(total_val - dc)

            monthly_rows.append({
                "client_id": cid, "month": pd.Timestamp(mon_str + "-01"),
                "hours_saved": hs, "cost_savings": savings,
                "revenue_generated": rg, "delivery_cost": dc,
                "roi_percent": roi, "efficiency_improvement_percent": round(eff, 4),
                "avg_time_to_go_live_days": avg_ttgl,
                "planned_roi_multiple": planned_roi,
                "actual_vs_plan_roi_pct": round((roi - planned_roi) / abs(planned_roi) * 100, 1) if (roi and planned_roi) else None,
                "net_benefit_ytd": net_benefit,
                "notes": None,
            })
    kpi_monthly = pd.DataFrame(monthly_rows)

    # ── BASELINES ──────────────────────────────────────────────────────────────
    baselines = pd.DataFrame([
        {"client_id": "C001", "kpi_name": "automation_runs_success", "baseline_value": 40,
         "baseline_start": "2025-12-09", "baseline_end": "2026-01-05", "captured_at": "2026-01-06", "notes": "Pre go-live"},
        {"client_id": "C001", "kpi_name": "support_tickets_created", "baseline_value": 6,
         "baseline_start": "2025-12-09", "baseline_end": "2026-01-05", "captured_at": "2026-01-06", "notes": ""},
        {"client_id": "C001", "kpi_name": "cost_savings", "baseline_value": 0,
         "baseline_start": "2025-12-09", "baseline_end": "2026-01-05", "captured_at": "2026-01-06", "notes": ""},
        {"client_id": "C002", "kpi_name": "automation_runs_success", "baseline_value": 25,
         "baseline_start": "2025-12-23", "baseline_end": "2026-01-19", "captured_at": "2026-01-20", "notes": ""},
        {"client_id": "C003", "kpi_name": "automation_runs_success", "baseline_value": 10,
         "baseline_start": "2026-01-01", "baseline_end": "2026-02-14", "captured_at": "2026-02-15", "notes": ""},
    ])

    return {
        "clients":        clients,
        "solutions":      solutions,
        "opportunities":  opportunities,
        "opp_financials": opp_financials,
        "kpi_daily":      kpi_daily,
        "kpi_monthly":    kpi_monthly,
        "baselines":      baselines,
    }
