"""
Data loader — reads from Google Sheets (live) or falls back to demo data.
Sheet schema matches KPI Mart v4:
  Row 1 = column headers
  Row 2 = instructions (ignored)
  Row 3+ = data
"""
 
import streamlit as st
import pandas as pd
import numpy as np
import datetime
 
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
 
 
@st.cache_data(ttl=300)
def load_all_data():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
 
        creds_dict = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sheet_id = st.secrets["GOOGLE_SHEET_ID"]
        sh = gc.open_by_key(sheet_id)
        sheets = {ws.title: ws for ws in sh.worksheets()}
        return {
            "clients":          _read_tab(sheets, "CLIENTS"),
            "opportunities":    _read_tab(sheets, "OPPORTUNITIES"),
            "opp_financials":   _read_tab(sheets, "OPP_FINANCIALS"),
            "kpi_daily":        _read_tab(sheets, "KPI_DAILY"),
            "kpi_monthly":      _read_tab(sheets, "KPI_MONTHLY"),
            "solutions":        _read_tab(sheets, "SOLUTIONS"),
            "ticket_sentiment": _read_tab(sheets, "TICKET_SENTIMENT"),
            "baselines":        _read_tab(sheets, "BASELINES"),
            "_source":    "live",
            "_refreshed": datetime.datetime.now().strftime("%d %b %Y %H:%M"),
        }
    except Exception as e:
        st.warning(f"⚠️ Google Sheets connection failed: {e}. Showing demo data.")
        return _load_demo_data()
 
 
def _read_tab(sheets, name):
    if name not in sheets:
        return pd.DataFrame()
    ws = sheets[name]
    rows = ws.get_all_values()
    if len(rows) < 1:
        return pd.DataFrame()
 
    # Row 1 (index 0) = headers
    # Row 2 (index 1) = instructions (skip)
    # Row 3+ (index 2+) = data
    headers = rows[0]
    if not any(h.strip() for h in headers):
        return pd.DataFrame()
 
    # Deduplicate headers
    seen = {}
    clean_headers = []
    for h in headers:
        h = h.strip()
        if not h:
            h = f"_col_{len(clean_headers)}"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        clean_headers.append(h)
 
    data_rows = rows[2:]  # skip header (0), instructions (1)
    df = pd.DataFrame(data_rows, columns=clean_headers)
 
    # Drop marker / template rows
    df = df[df.iloc[:, 0].str.strip().ne("")]
    df = df[~df.iloc[:, 0].str.startswith("▼")]
    df = df[~df.iloc[:, 0].str.startswith("C00X")]
    df = df.replace("", np.nan)
    df = _clean_df(df)
    return df
 
 
def _clean_df(df):
    # Cast numeric columns
    for col in df.columns:
        if col.startswith("_col_"):
            continue
        series = df[col].dropna()
        if len(series) == 0:
            continue
        numeric = pd.to_numeric(
            series.astype(str)
                  .str.replace(r'[$,%x×]', '', regex=True)
                  .str.replace(',', '', regex=False),
            errors='coerce'
        )
        if numeric.notna().sum() / max(len(series), 1) >= 0.6:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                       .str.replace(r'[$,%x×]', '', regex=True)
                       .str.replace(',', '', regex=False),
                errors='coerce'
            )
 
    # Parse date/time columns
    for col in df.columns:
        if any(k in col.lower() for k in ['date', 'month', 'week', 'start', 'end', 'at']):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass
    return df
 
 
def get_baseline(baselines: pd.DataFrame, client_id: str, kpi_name: str):
    """Return baseline value for a client+KPI, or None if not found."""
    if baselines is None or baselines.empty:
        return None
    row = baselines[
        (baselines["client_id"] == client_id) &
        (baselines["kpi_name"]  == kpi_name)
    ]
    if row.empty:
        return None
    return pd.to_numeric(row.iloc[0]["baseline_value"], errors="coerce")
 
 
def improvement_pct(current, baseline):
    try:
        current  = float(current)
        baseline = float(baseline)
        if baseline == 0:
            return None
        return (current - baseline) / abs(baseline) * 100
    except Exception:
        return None
 
 
# ─────────────────────────────────────────────────────────────────────────────
# DEMO DATA — mirrors KPI Mart v4 exactly
# ─────────────────────────────────────────────────────────────────────────────
def _load_demo_data():
 
    # ── CLIENTS ───────────────────────────────────────────────────────────────
    clients = pd.DataFrame([
        {"client_id": "C001", "client_name": "Kenafric Industries",
         "client_type": "AI Transformation", "industry": "FMCG",
         "go_live_date": "2026-01-06", "fte_count": 450,
         "fte_hourly_rate_usd": 18.5, "status": "Active",
         "contract_value_usd": 120000, "annual_revenue_usd": 85000000,
         "region": "East Africa"},
        {"client_id": "C002", "client_name": "TCC Group",
         "client_type": "Data Analytics", "industry": "Telecommunications",
         "go_live_date": "2026-02-01", "fte_count": 280,
         "fte_hourly_rate_usd": 22.0, "status": "Active",
         "contract_value_usd": 95000, "annual_revenue_usd": 210000000,
         "region": "East Africa"},
        {"client_id": "C003", "client_name": "Bank Islami",
         "client_type": "AI Transformation", "industry": "Banking",
         "go_live_date": "2025-12-15", "fte_count": 620,
         "fte_hourly_rate_usd": 28.0, "status": "Active",
         "contract_value_usd": 185000, "annual_revenue_usd": 520000000,
         "region": "Pakistan"},
    ])
    clients["go_live_date"] = pd.to_datetime(clients["go_live_date"])
 
    # ── OPPORTUNITIES ─────────────────────────────────────────────────────────
    opportunities = pd.DataFrame([
        {"client_id": "C001", "opp_id": "OPP-001", "opp_name": "Invoice Processing Automation",
         "function": "Finance", "ai_pattern": "Document AI",
         "value_type_primary": "Productivity", "value_type_secondary": "Quality",
         "priority_score": 8.2, "feasibility_score": 4, "value_score": 4,
         "initiative_status": "Live", "buy_build": "Buy", "hitl_level": "Partial"},
        {"client_id": "C001", "opp_id": "OPP-002", "opp_name": "Demand Forecasting",
         "function": "Supply Chain", "ai_pattern": "Predictive ML",
         "value_type_primary": "Revenue", "value_type_secondary": "OpEx",
         "priority_score": 7.5, "feasibility_score": 3, "value_score": 4,
         "initiative_status": "Pilot", "buy_build": "Build", "hitl_level": "Full"},
        {"client_id": "C001", "opp_id": "OPP-003", "opp_name": "HR Onboarding Automation",
         "function": "HR", "ai_pattern": "RPA + GenAI",
         "value_type_primary": "Productivity", "value_type_secondary": None,
         "priority_score": 6.8, "feasibility_score": 4, "value_score": 3,
         "initiative_status": "Backlog", "buy_build": "Build", "hitl_level": "Partial"},
        {"client_id": "C002", "opp_id": "OPP-004", "opp_name": "Network Fault Prediction",
         "function": "Operations", "ai_pattern": "Predictive ML",
         "value_type_primary": "Quality", "value_type_secondary": "OpEx",
         "priority_score": 8.8, "feasibility_score": 4, "value_score": 5,
         "initiative_status": "Live", "buy_build": "Build", "hitl_level": "None"},
        {"client_id": "C002", "opp_id": "OPP-005", "opp_name": "Customer Churn Prediction",
         "function": "Commercial", "ai_pattern": "Predictive ML",
         "value_type_primary": "Revenue", "value_type_secondary": "Quality",
         "priority_score": 9.1, "feasibility_score": 4, "value_score": 5,
         "initiative_status": "Live", "buy_build": "Build", "hitl_level": "Partial"},
        {"client_id": "C002", "opp_id": "OPP-006", "opp_name": "Call Centre AI Assist",
         "function": "Customer Service", "ai_pattern": "GenAI",
         "value_type_primary": "Productivity", "value_type_secondary": "Quality",
         "priority_score": 7.2, "feasibility_score": 3, "value_score": 4,
         "initiative_status": "Pilot", "buy_build": "Buy", "hitl_level": "Full"},
        {"client_id": "C003", "opp_id": "OPP-007", "opp_name": "AML Transaction Monitoring",
         "function": "Compliance", "ai_pattern": "Predictive ML",
         "value_type_primary": "Quality", "value_type_secondary": "OpEx",
         "priority_score": 9.4, "feasibility_score": 5, "value_score": 5,
         "initiative_status": "Live", "buy_build": "Build", "hitl_level": "Partial"},
        {"client_id": "C003", "opp_id": "OPP-008", "opp_name": "Loan Application Processing",
         "function": "Retail Banking", "ai_pattern": "Document AI",
         "value_type_primary": "Productivity", "value_type_secondary": "Quality",
         "priority_score": 8.5, "feasibility_score": 4, "value_score": 5,
         "initiative_status": "Live", "buy_build": "Buy", "hitl_level": "Partial"},
        {"client_id": "C003", "opp_id": "OPP-009", "opp_name": "Regulatory Reporting Auto",
         "function": "Compliance", "ai_pattern": "RPA",
         "value_type_primary": "OpEx", "value_type_secondary": "Quality",
         "priority_score": 7.8, "feasibility_score": 4, "value_score": 4,
         "initiative_status": "Pilot", "buy_build": "Buy", "hitl_level": "Full"},
    ])
 
    # ── OPP_FINANCIALS ────────────────────────────────────────────────────────
    opp_financials = pd.DataFrame([
        {"client_id":"C001","opp_id":"OPP-001","minutes_saved_per_unit":8,
         "annual_volume":12000,"adoption_pct":0.85,"fully_loaded_cost_per_hr":18.5,
         "quality_savings":5000,"impl_cost":45000,"annual_license_cost":12000,
         "risk_haircut_pct":0.15,"annual_productivity_benefit":25160,
         "annual_total_benefit":25636,"annual_total_cost":27000,
         "net_benefit":-1364,"roi_multiple":-0.09,"payback_months":999},
        {"client_id":"C001","opp_id":"OPP-002","minutes_saved_per_unit":15,
         "annual_volume":3600,"adoption_pct":0.70,"fully_loaded_cost_per_hr":18.5,
         "quality_savings":18000,"impl_cost":80000,"annual_license_cost":24000,
         "risk_haircut_pct":0.25,"annual_productivity_benefit":32813,
         "annual_total_benefit":41259,"annual_total_cost":50667,
         "net_benefit":-9408,"roi_multiple":-0.56,"payback_months":999},
        {"client_id":"C001","opp_id":"OPP-003","minutes_saved_per_unit":12,
         "annual_volume":2400,"adoption_pct":0.80,"fully_loaded_cost_per_hr":18.5,
         "quality_savings":3000,"impl_cost":35000,"annual_license_cost":8000,
         "risk_haircut_pct":0.15,"annual_productivity_benefit":23808,
         "annual_total_benefit":23186,"annual_total_cost":19667,
         "net_benefit":3520,"roi_multiple":0.48,"payback_months":99.4},
        {"client_id":"C002","opp_id":"OPP-004","minutes_saved_per_unit":20,
         "annual_volume":18000,"adoption_pct":0.90,"fully_loaded_cost_per_hr":22.0,
         "quality_savings":25000,"impl_cost":95000,"annual_license_cost":28000,
         "risk_haircut_pct":0.15,"annual_productivity_benefit":118800,
         "annual_total_benefit":122580,"annual_total_cost":59667,
         "net_benefit":62913,"roi_multiple":1.99,"payback_months":18.1},
        {"client_id":"C002","opp_id":"OPP-005","minutes_saved_per_unit":30,
         "annual_volume":9600,"adoption_pct":0.85,"fully_loaded_cost_per_hr":22.0,
         "quality_savings":55000,"impl_cost":120000,"annual_license_cost":36000,
         "risk_haircut_pct":0.20,"annual_productivity_benefit":94080,
         "annual_total_benefit":119264,"annual_total_cost":76000,
         "net_benefit":43264,"roi_multiple":1.08,"payback_months":33.3},
        {"client_id":"C002","opp_id":"OPP-006","minutes_saved_per_unit":10,
         "annual_volume":24000,"adoption_pct":0.75,"fully_loaded_cost_per_hr":22.0,
         "quality_savings":8000,"impl_cost":55000,"annual_license_cost":18000,
         "risk_haircut_pct":0.20,"annual_productivity_benefit":66000,
         "annual_total_benefit":59200,"annual_total_cost":36333,
         "net_benefit":22867,"roi_multiple":1.89,"payback_months":28.9},
        {"client_id":"C003","opp_id":"OPP-007","minutes_saved_per_unit":25,
         "annual_volume":36000,"adoption_pct":0.92,"fully_loaded_cost_per_hr":28.0,
         "quality_savings":85000,"impl_cost":145000,"annual_license_cost":42000,
         "risk_haircut_pct":0.15,"annual_productivity_benefit":386400,
         "annual_total_benefit":399348,"annual_total_cost":90333,
         "net_benefit":309015,"roi_multiple":6.42,"payback_months":5.6},
        {"client_id":"C003","opp_id":"OPP-008","minutes_saved_per_unit":18,
         "annual_volume":21600,"adoption_pct":0.88,"fully_loaded_cost_per_hr":28.0,
         "quality_savings":35000,"impl_cost":85000,"annual_license_cost":25000,
         "risk_haircut_pct":0.15,"annual_productivity_benefit":180288,
         "annual_total_benefit":183745,"annual_total_cost":53333,
         "net_benefit":130412,"roi_multiple":4.60,"payback_months":7.8},
        {"client_id":"C003","opp_id":"OPP-009","minutes_saved_per_unit":12,
         "annual_volume":12000,"adoption_pct":0.80,"fully_loaded_cost_per_hr":28.0,
         "quality_savings":15000,"impl_cost":62000,"annual_license_cost":18000,
         "risk_haircut_pct":0.20,"annual_productivity_benefit":89600,
         "annual_total_benefit":83200,"annual_total_cost":38667,
         "net_benefit":44533,"roi_multiple":3.44,"payback_months":16.7},
    ])
 
    # ── KPI_DAILY ─────────────────────────────────────────────────────────────
    mins_map = {"C001": 8, "C002": 22, "C003": 20}
    rows = []
 
    # C001: 64 days from go-live 2026-01-06
    for d in range(64):
        dt  = datetime.date(2026, 1, 6) + datetime.timedelta(days=d)
        ro  = 420 + d * 3 + (d % 7) * 12
        rf  = max(0, 18 - d // 5)
        tc  = max(1, 8 - d // 10)
        to_ = max(2, 12 - d // 8)
        tcl = min(tc + 1, 6 + d // 12)
        rh  = round(max(14.5, 52.0 - d * 0.587), 1)
        hp  = max(0, 3 - d // 15)
        rows.append({"client_id":"C001","date":dt,"solutions_deployed":2,
                     "automation_runs_success":ro,"automation_runs_failed":rf,
                     "support_tickets_created":tc,
                     "hours_saved":round(ro * mins_map["C001"] / 60, 2),
                     "tickets_per_100_runs":round(tc / ro * 100, 2),
                     "success_rate":round(ro / (ro + rf), 4),
                     "tickets_open":to_,"tickets_closed":tcl,
                     "avg_resolution_hrs":rh,"high_priority_count":hp,"notes":""})
 
    # C002: 38 days from go-live 2026-02-01
    for d in range(38):
        dt  = datetime.date(2026, 2, 1) + datetime.timedelta(days=d)
        ro  = 680 + d * 8 + (d % 5) * 20
        rf  = max(0, 22 - d // 4)
        tc  = max(1, 10 - d // 8)
        to_ = max(3, 15 - d // 7)
        tcl = min(tc + 2, 8 + d // 10)
        rh  = round(max(22.4, 68.0 - d * 1.20), 1)
        hp  = max(0, 4 - d // 10)
        rows.append({"client_id":"C002","date":dt,"solutions_deployed":2,
                     "automation_runs_success":ro,"automation_runs_failed":rf,
                     "support_tickets_created":tc,
                     "hours_saved":round(ro * mins_map["C002"] / 60, 2),
                     "tickets_per_100_runs":round(tc / ro * 100, 2),
                     "success_rate":round(ro / (ro + rf), 4),
                     "tickets_open":to_,"tickets_closed":tcl,
                     "avg_resolution_hrs":rh,"high_priority_count":hp,"notes":""})
 
    # C003: 87 days from go-live 2025-12-15
    for d in range(87):
        dt  = datetime.date(2025, 12, 15) + datetime.timedelta(days=d)
        ro  = 890 + d * 5 + (d % 6) * 18
        rf  = max(0, 25 - d // 6)
        tc  = max(3, 12 - d // 12)
        to_ = max(8, 22 - d // 7)
        tcl = min(tc + 2, 9 + d // 11)
        rh  = round(max(11.0, 74.0 - d * 0.724), 1)
        hp  = max(0, 5 - d // 15)
        rows.append({"client_id":"C003","date":dt,"solutions_deployed":3,
                     "automation_runs_success":ro,"automation_runs_failed":rf,
                     "support_tickets_created":tc,
                     "hours_saved":round(ro * mins_map["C003"] / 60, 2),
                     "tickets_per_100_runs":round(tc / ro * 100, 2),
                     "success_rate":round(ro / (ro + rf), 4),
                     "tickets_open":to_,"tickets_closed":tcl,
                     "avg_resolution_hrs":rh,"high_priority_count":hp,"notes":""})
 
    kpi_daily = pd.DataFrame(rows)
    kpi_daily["date"] = pd.to_datetime(kpi_daily["date"])
 
    # ── KPI_MONTHLY ───────────────────────────────────────────────────────────
    monthly_raw = [
        {"client_id":"C001","month":"2026-01","cost_savings_usd":18500,
         "delivery_cost_usd":8200,"planned_roi_multiple":2.5},
        {"client_id":"C001","month":"2026-02","cost_savings_usd":24800,
         "delivery_cost_usd":8200,"planned_roi_multiple":2.5},
        {"client_id":"C001","month":"2026-03","cost_savings_usd":28200,
         "delivery_cost_usd":8200,"planned_roi_multiple":2.5},
        {"client_id":"C002","month":"2026-02","cost_savings_usd":32000,
         "delivery_cost_usd":11500,"planned_roi_multiple":3.2},
        {"client_id":"C002","month":"2026-03","cost_savings_usd":41500,
         "delivery_cost_usd":11500,"planned_roi_multiple":3.2},
        {"client_id":"C003","month":"2025-12","cost_savings_usd":42000,
         "delivery_cost_usd":18000,"planned_roi_multiple":4.1},
        {"client_id":"C003","month":"2026-01","cost_savings_usd":55000,
         "delivery_cost_usd":18000,"planned_roi_multiple":4.1},
        {"client_id":"C003","month":"2026-02","cost_savings_usd":68000,
         "delivery_cost_usd":18000,"planned_roi_multiple":4.1},
        {"client_id":"C003","month":"2026-03","cost_savings_usd":71000,
         "delivery_cost_usd":18000,"planned_roi_multiple":4.1},
    ]
    kpi_monthly = pd.DataFrame(monthly_raw)
    kpi_monthly["net_benefit_usd"]     = kpi_monthly["cost_savings_usd"] - kpi_monthly["delivery_cost_usd"]
    kpi_monthly["actual_roi_multiple"] = kpi_monthly["net_benefit_usd"] / kpi_monthly["delivery_cost_usd"]
    kpi_monthly["actual_vs_plan_pct"]  = kpi_monthly["actual_roi_multiple"] / kpi_monthly["planned_roi_multiple"]
 
    def _monthly_agg(cid, mo_str, daily_df):
        d = daily_df[
            (daily_df["client_id"] == cid) &
            (daily_df["date"].dt.strftime("%Y-%m") == mo_str)
        ]
        if d.empty:
            return 0, 0, np.nan, np.nan
        hrs  = d["hours_saved"].sum()
        runs = d["automation_runs_success"].sum()
        fail = d["automation_runs_failed"].sum()
        sr   = runs / max(runs + fail, 1)
        res  = pd.to_numeric(d["avg_resolution_hrs"], errors="coerce").dropna()
        return hrs, runs, sr, res.mean() if len(res) > 0 else np.nan
 
    h_l, r_l, s_l, res_l = [], [], [], []
    for _, row in kpi_monthly.iterrows():
        h, r, s, res = _monthly_agg(row["client_id"], str(row["month"])[:7], kpi_daily)
        h_l.append(h); r_l.append(r); s_l.append(s); res_l.append(res)
 
    kpi_monthly["hours_saved"]                = h_l
    kpi_monthly["automation_runs_total"]      = r_l
    kpi_monthly["success_rate_monthly"]       = s_l
    kpi_monthly["avg_resolution_hrs_monthly"] = res_l
    kpi_monthly["month"] = pd.to_datetime(kpi_monthly["month"])
 
    # ── SOLUTIONS ─────────────────────────────────────────────────────────────
    solutions = pd.DataFrame([
        {"client_id":"C001","opp_id":"OPP-001",
         "solution_name":"Invoice Intelligence Platform","solution_type":"Document AI",
         "go_live_date":"2026-01-06","phase":"Live",
         "fte_impacted":85,"version":"v1.2","notes":"Processing 400+ invoices/day"},
        {"client_id":"C001","opp_id":"OPP-002",
         "solution_name":"Demand Signal Engine","solution_type":"Predictive ML",
         "go_live_date":"2026-02-15","phase":"Pilot",
         "fte_impacted":40,"version":"v0.8","notes":"3-month pilot, go-live Q2"},
        {"client_id":"C002","opp_id":"OPP-004",
         "solution_name":"NetGuard Fault Predictor","solution_type":"Predictive ML",
         "go_live_date":"2026-02-01","phase":"Live",
         "fte_impacted":120,"version":"v1.0","notes":"Covering all 12 network zones"},
        {"client_id":"C002","opp_id":"OPP-005",
         "solution_name":"ChurnShield Analytics","solution_type":"Predictive ML",
         "go_live_date":"2026-02-01","phase":"Live",
         "fte_impacted":65,"version":"v1.1","notes":"Integrated with CRM"},
        {"client_id":"C003","opp_id":"OPP-007",
         "solution_name":"AML Sentinel","solution_type":"Predictive ML",
         "go_live_date":"2025-12-15","phase":"Live",
         "fte_impacted":200,"version":"v2.0","notes":"Regulatory approved"},
        {"client_id":"C003","opp_id":"OPP-008",
         "solution_name":"LoanFlow Automation","solution_type":"Document AI",
         "go_live_date":"2025-12-15","phase":"Live",
         "fte_impacted":150,"version":"v1.3","notes":"Handles retail + SME loans"},
        {"client_id":"C003","opp_id":"OPP-009",
         "solution_name":"RegReport Auto","solution_type":"RPA",
         "go_live_date":"2026-01-15","phase":"Pilot",
         "fte_impacted":80,"version":"v0.9","notes":"SBP submission pilot"},
    ])
    solutions["go_live_date"] = pd.to_datetime(solutions["go_live_date"])
 
    # ── TICKET_SENTIMENT ──────────────────────────────────────────────────────
    import random
    random.seed(42)
    ts_rows = []
    configs = [
        ("C001", datetime.date(2026, 1,  5), 5, 3),
        ("C002", datetime.date(2026, 2,  2), 6, 3),
        ("C003", datetime.date(2025,12, 15), 4, 6),
    ]
    for cid, wk_base, neg_start, pos_start in configs:
        for w in range(10):
            wk  = wk_base + datetime.timedelta(weeks=w)
            neg = max(0, neg_start - w // 2 + random.randint(-1, 1))
            pos = min(12, pos_start + w // 2 + random.randint(0, 2))
            neu = random.randint(2, 5)
            total = pos + neu + neg
            ts_rows.append({
                "client_id": cid, "week_start": wk,
                "positive_count": pos, "neutral_count": neu, "negative_count": neg,
                "total_tickets": total,
                "sentiment_score": round((pos - neg) / max(1, total), 3),
            })
    ticket_sentiment = pd.DataFrame(ts_rows)
    ticket_sentiment["week_start"] = pd.to_datetime(ticket_sentiment["week_start"])
 
    # ── BASELINES ─────────────────────────────────────────────────────────────
    baselines = pd.DataFrame([
        # C001 Kenafric Industries
        {"client_id":"C001","kpi_name":"automation_runs_success","baseline_value":0,
         "unit":"count","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Manual count",
         "notes":"No automation existed pre go-live"},
        {"client_id":"C001","kpi_name":"hours_saved","baseline_value":0,
         "unit":"hours","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Calculated",
         "notes":"Zero automation = zero hours saved"},
        {"client_id":"C001","kpi_name":"support_tickets_created","baseline_value":9.2,
         "unit":"count/day","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Daily avg over 4-week baseline period"},
        {"client_id":"C001","kpi_name":"tickets_open","baseline_value":18,
         "unit":"count","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Avg open ticket backlog at EOD"},
        {"client_id":"C001","kpi_name":"avg_resolution_hrs","baseline_value":52,
         "unit":"hours","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Zoho Desk report",
         "notes":"Avg hrs from ticket creation to close"},
        {"client_id":"C001","kpi_name":"high_priority_count","baseline_value":4.5,
         "unit":"count/day","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Daily avg High/Urgent tickets"},
        {"client_id":"C001","kpi_name":"cost_savings_usd","baseline_value":0,
         "unit":"$/month","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Finance",
         "notes":"No AI savings before go-live"},
        {"client_id":"C001","kpi_name":"invoice_processing_time_hrs","baseline_value":6.5,
         "unit":"hours","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"ERP system",
         "notes":"Avg manual invoice processing time"},
        {"client_id":"C001","kpi_name":"invoice_error_rate_pct","baseline_value":8.2,
         "unit":"%","baseline_start":"2025-11-25","baseline_end":"2025-12-25",
         "captured_at":"2026-01-05","captured_by":"Aidapt AM","data_source":"Finance audit",
         "notes":"Manual keying error rate"},
        # C002 TCC Group
        {"client_id":"C002","kpi_name":"automation_runs_success","baseline_value":0,
         "unit":"count","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Manual count",
         "notes":"No automation existed pre go-live"},
        {"client_id":"C002","kpi_name":"hours_saved","baseline_value":0,
         "unit":"hours","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Calculated",
         "notes":"Zero automation = zero hours saved"},
        {"client_id":"C002","kpi_name":"support_tickets_created","baseline_value":13.8,
         "unit":"count/day","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Daily avg incl. network fault tickets"},
        {"client_id":"C002","kpi_name":"tickets_open","baseline_value":22,
         "unit":"count","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Higher backlog due to manual fault diagnosis"},
        {"client_id":"C002","kpi_name":"avg_resolution_hrs","baseline_value":68,
         "unit":"hours","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Zoho Desk report",
         "notes":"Manual fault diagnosis very slow"},
        {"client_id":"C002","kpi_name":"high_priority_count","baseline_value":6.2,
         "unit":"count/day","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Network faults often P1"},
        {"client_id":"C002","kpi_name":"cost_savings_usd","baseline_value":0,
         "unit":"$/month","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"Finance",
         "notes":"No AI savings before go-live"},
        {"client_id":"C002","kpi_name":"network_fault_mttr_hrs","baseline_value":14.2,
         "unit":"hours","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"NOC system",
         "notes":"Mean time to repair network faults"},
        {"client_id":"C002","kpi_name":"churn_rate_monthly_pct","baseline_value":2.8,
         "unit":"%","baseline_start":"2026-01-02","baseline_end":"2026-01-30",
         "captured_at":"2026-01-31","captured_by":"Aidapt AM","data_source":"CRM system",
         "notes":"Monthly customer churn %"},
        # C003 Bank Islami
        {"client_id":"C003","kpi_name":"automation_runs_success","baseline_value":0,
         "unit":"count","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Manual count",
         "notes":"No automation existed pre go-live"},
        {"client_id":"C003","kpi_name":"hours_saved","baseline_value":0,
         "unit":"hours","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Calculated",
         "notes":"Zero automation = zero hours saved"},
        {"client_id":"C003","kpi_name":"support_tickets_created","baseline_value":16.5,
         "unit":"count/day","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"High ticket volume from manual compliance checks"},
        {"client_id":"C003","kpi_name":"tickets_open","baseline_value":28,
         "unit":"count","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Large backlog before AI"},
        {"client_id":"C003","kpi_name":"avg_resolution_hrs","baseline_value":74,
         "unit":"hours","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Zoho Desk report",
         "notes":"Complex banking tickets take time"},
        {"client_id":"C003","kpi_name":"high_priority_count","baseline_value":7.8,
         "unit":"count/day","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Zoho Desk export",
         "notes":"Compliance and AML alerts drive high priority"},
        {"client_id":"C003","kpi_name":"cost_savings_usd","baseline_value":0,
         "unit":"$/month","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Finance",
         "notes":"No AI savings before go-live"},
        {"client_id":"C003","kpi_name":"aml_alert_review_time_hrs","baseline_value":3.8,
         "unit":"hours","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Compliance system",
         "notes":"Manual AML alert review per case"},
        {"client_id":"C003","kpi_name":"loan_processing_days","baseline_value":5.2,
         "unit":"days","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Core banking",
         "notes":"End-to-end loan application processing"},
        {"client_id":"C003","kpi_name":"false_positive_aml_rate","baseline_value":68,
         "unit":"%","baseline_start":"2025-11-15","baseline_end":"2025-12-14",
         "captured_at":"2025-12-14","captured_by":"Aidapt AM","data_source":"Compliance system",
         "notes":"% AML alerts that were false positives"},
    ])
    for col in ["baseline_start","baseline_end","captured_at"]:
        baselines[col] = pd.to_datetime(baselines[col])
 
    return {
        "clients":          clients,
        "opportunities":    opportunities,
        "opp_financials":   opp_financials,
        "kpi_daily":        kpi_daily,
        "kpi_monthly":      kpi_monthly,
        "solutions":        solutions,
        "ticket_sentiment": ticket_sentiment,
        "baselines":        baselines,
        "_source":    "demo",
        "_refreshed": datetime.datetime.now().strftime("%d %b %Y %H:%M"),
    }
