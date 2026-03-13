"""Reusable Plotly chart builders with consistent Aidapt dark theme."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

TEAL   = "#00C9B1"
BLUE   = "#3B82F6"
PURPLE = "#7C3AED"
GOLD   = "#F59E0B"
GREEN  = "#10B981"
RED    = "#EF4444"
SLATE  = "#475569"
MUTED  = "rgba(255,255,255,0.25)"

CLIENT_COLORS = {}
CLIENT_NAMES  = {}

# Reordered: Blue → Purple → Gold → Teal → Green … gives warmer, more distinct client colours
COLOR_CYCLE = ["#3B82F6", "#8B5CF6", "#F59E0B", "#00C9B1", "#10B981", "#EF4444",
               "#F97316", "#06B6D4", "#EC4899", "#A855F7", "#14B8A6", "#FBBF24"]
PALETTE     = COLOR_CYCLE[:]

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="rgba(255,255,255,0.6)", size=11),
    margin=dict(l=10, r=10, t=28, b=10),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
        font=dict(size=10, color="rgba(255,255,255,0.6)"),
        orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=10), linecolor="rgba(255,255,255,0.08)",
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=10), linecolor="rgba(255,255,255,0.08)",
    ),
    hoverlabel=dict(bgcolor="#1E293B", bordercolor="rgba(255,255,255,0.15)",
                    font=dict(color="white", size=11)),
)


def build_client_maps(clients_df: pd.DataFrame):
    global CLIENT_NAMES, CLIENT_COLORS
    CLIENT_NAMES  = {}
    CLIENT_COLORS = {}
    for i, (_, row) in enumerate(clients_df.iterrows()):
        cid = row["client_id"]
        CLIENT_NAMES[cid]  = row["client_name"]
        CLIENT_COLORS[cid] = COLOR_CYCLE[i % len(COLOR_CYCLE)]


def client_name(cid):
    return CLIENT_NAMES.get(cid, cid)

def client_color(cid):
    return CLIENT_COLORS.get(cid, TEAL)

def _hex_to_rgba(hex_color, alpha=0.8):
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(0,201,177,{alpha})"

def _to_num(series):
    return pd.to_numeric(series, errors="coerce")

def _fig(title=""):
    fig = go.Figure()
    lay = LAYOUT_BASE.copy()
    if title:
        lay["title"] = dict(text=title, font=dict(size=12, color="rgba(255,255,255,0.85)"),
                            x=0, xanchor="left")
    fig.update_layout(**lay)
    return fig

def config():
    return {"displayModeBar": False, "responsive": True}


# ── Line chart ─────────────────────────────────────────────────────────────────
def line_chart(df, x, y_cols, names=None, colors=None, title="", y_fmt=None, dash_cols=None):
    fig = _fig(title)
    colors = colors or PALETTE
    dash_cols = dash_cols or []
    for i, col in enumerate(y_cols):
        name = (names or y_cols)[i]
        dash = "dot" if col in dash_cols else "solid"
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=name, mode="lines+markers",
            line=dict(color=colors[i % len(colors)], width=2.5, dash=dash),
            marker=dict(size=5, color=colors[i % len(colors)]),
            fill="tozeroy" if len(y_cols) == 1 else "none",
            fillcolor=_hex_to_rgba(colors[0], 0.08) if len(y_cols) == 1 else None,
        ))
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ── Bar chart ──────────────────────────────────────────────────────────────────
def bar_chart(df, x, y, color=TEAL, title="", horizontal=False, y_fmt=None, text=None):
    fig = _fig(title)
    fig.add_trace(go.Bar(
        x=df[y] if horizontal else df[x],
        y=df[x] if horizontal else df[y],
        orientation="h" if horizontal else "v",
        marker=dict(color=color, opacity=0.85, line=dict(width=0)),
        text=df[text] if text else None,
        textposition="outside" if text else "none",
        textfont=dict(size=10, color="rgba(255,255,255,0.7)"),
    ))
    fig.update_traces(marker_cornerradius=5)
    if y_fmt:
        ax = "xaxis" if horizontal else "yaxis"
        fig.update_layout(**{ax: dict(tickformat=y_fmt)})
    return fig


# ── Multi-bar ──────────────────────────────────────────────────────────────────
def multi_bar(df, x, y_cols, names=None, colors=None, title="", stacked=False, y_fmt=None):
    fig = _fig(title)
    colors = colors or PALETTE
    for i, col in enumerate(y_cols):
        name = (names or y_cols)[i]
        fig.add_trace(go.Bar(
            x=df[x], y=df[col], name=name,
            marker=dict(color=colors[i % len(colors)], opacity=0.85, line=dict(width=0)),
        ))
    fig.update_traces(marker_cornerradius=4)
    fig.update_layout(barmode="stack" if stacked else "group")
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ── Combo (bar + line) ─────────────────────────────────────────────────────────
def combo_chart(df, x, bar_col, line_col, bar_name="", line_name="",
                bar_color=TEAL, line_color=GOLD, title="", y_fmt=None):
    fig = _fig(title)
    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_col], name=bar_name,
        marker=dict(color=bar_color, opacity=0.75, line=dict(width=0)), yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_col], name=line_name, mode="lines+markers",
        line=dict(color=line_color, width=2.5, dash="dot"),
        marker=dict(size=6, color=line_color), yaxis="y2",
    ))
    fig.update_traces(selector=dict(type="bar"), marker_cornerradius=5)
    fig.update_layout(
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickformat=y_fmt or ""),
        yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(size=10, color=line_color), tickformat=y_fmt or ""),
        barmode="group",
    )
    return fig


# ── Donut ──────────────────────────────────────────────────────────────────────
def donut(labels, values, title="", colors=None):
    fig = _fig()
    colors = colors or PALETTE
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#0B1520", width=2)),
        textinfo="label+percent", textfont=dict(size=10),
        insidetextorientation="horizontal",
    ))
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=12, color="rgba(255,255,255,0.85)"),
                                     x=0, xanchor="left"))
    fig.update_layout(showlegend=False)
    return fig


# ── Bubble / scatter ───────────────────────────────────────────────────────────
def bubble_chart(df, x, y, size, color_col=None, label_col=None, title="",
                 x_title="Feasibility Score →", y_title="Value Score →", colors=None):
    fig = _fig(title)
    if color_col and color_col in df.columns:
        groups = df[color_col].unique()
        col_map = dict(zip(groups, (colors or PALETTE)))
        for grp in groups:
            sub   = df[df[color_col] == grp]
            sizes = np.sqrt(_to_num(sub[size]).clip(lower=1)) / 8
            sizes = sizes.clip(lower=8, upper=40)
            fig.add_trace(go.Scatter(
                x=sub[x], y=sub[y],
                mode="markers+text" if label_col else "markers",
                name=str(grp),
                marker=dict(size=sizes, color=col_map.get(grp, TEAL),
                            opacity=0.8, line=dict(color="rgba(255,255,255,0.3)", width=1)),
                text=sub[label_col] if label_col else None,
                textposition="top center", textfont=dict(size=9),
                customdata=sub[size],
            ))
    fig.add_hline(y=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.add_vline(x=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.update_xaxes(range=[1, 5.3], title_text=x_title, title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[1, 5.3], title_text=y_title, title_font=dict(size=10, color=MUTED))
    return fig


# ── Gauge ──────────────────────────────────────────────────────────────────────
def gauge(value, title="", max_val=5, color=TEAL):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(font=dict(size=28, color="white", family="DM Mono"), suffix=""),
        title=dict(text=title, font=dict(size=11, color="rgba(255,255,255,0.6)")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="rgba(255,255,255,0.3)",
                      tickfont=dict(size=9, color="rgba(255,255,255,0.4)")),
            bar=dict(color=color, thickness=0.25),
            bgcolor="rgba(255,255,255,0.04)", borderwidth=0,
            steps=[
                dict(range=[0, max_val*0.4], color="rgba(239,68,68,0.12)"),
                dict(range=[max_val*0.4, max_val*0.7], color="rgba(245,158,11,0.12)"),
                dict(range=[max_val*0.7, max_val], color="rgba(16,185,129,0.12)"),
            ],
        ),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=20, r=20, t=50, b=20),
                      font=dict(family="DM Sans", color="rgba(255,255,255,0.6)"), height=180)
    return fig


# ── KPI card HTML ──────────────────────────────────────────────────────────────
def kpi_card(label, value, unit="", delta="", delta_type="flat", accent=TEAL):
    delta_cls = {"up": "delta-up", "down": "delta-down", "flat": "delta-flat"}.get(delta_type, "delta-flat")
    arrow = {"up": "▲ ", "down": "▼ ", "flat": ""}.get(delta_type, "")
    return f"""
    <div class="kpi-card" style="--accent:{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
        <div class="kpi-delta {delta_cls}">{arrow}{delta}</div>
    </div>
    """

def badge(text, status="live"):
    return f'<span class="badge badge-{status}">{text}</span>'

def fmt_currency(v, decimals=0):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.{decimals}f}"

def fmt_pct(v, decimals=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{v*100:.{decimals}f}%" if abs(v) < 10 else f"{v:.{decimals}f}%"

def fmt_num(v, decimals=0):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{v:,.{decimals}f}"


# ── Opportunity bubble chart ───────────────────────────────────────────────────
def build_opportunity_bubble(opps: pd.DataFrame, fin: pd.DataFrame):
    fig = _fig("Opportunity Matrix — Value vs Feasibility")
    if opps.empty:
        return fig

    merged = opps.copy()
    if not fin.empty and "opp_id" in fin.columns:
        nb_col = next((c for c in ["net_benefit","net_benefit_risk_adj"] if c in fin.columns), None)
        if nb_col:
            merged = merged.merge(fin[["opp_id", nb_col]], on="opp_id", how="left")
            merged["_size"] = _to_num(merged[nb_col]).clip(lower=0).fillna(10000)
        else:
            merged["_size"] = 20000
    else:
        merged["_size"] = 20000

    _is_col = next((c for c in ["initiative_status","status"] if c in merged.columns), None)
    _fs_col = next((c for c in ["feasibility_score"] if c in merged.columns), None)
    _vs_col = next((c for c in ["value_score"] if c in merged.columns), None)

    if not _fs_col or not _vs_col:
        return fig

    status_colors = {"Live": TEAL, "Pilot": BLUE, "In Pilot": BLUE,
                     "Backlog": "#64748B", "Paused": RED}

    for cid in merged["client_id"].unique():
        sub = merged[merged["client_id"] == cid].copy()
        sub["_fs"] = _to_num(sub[_fs_col])
        sub["_vs"] = _to_num(sub[_vs_col])
        sub = sub.dropna(subset=["_fs","_vs"])
        if sub.empty:
            continue
        sizes = np.sqrt(sub["_size"].clip(lower=1)) / 25
        sizes = sizes.clip(lower=10, upper=45)
        colors = [status_colors.get(s, "#64748B")
                  for s in (sub[_is_col] if _is_col else ["Backlog"]*len(sub))]
        fig.add_trace(go.Scatter(
            x=sub["_fs"], y=sub["_vs"],
            mode="markers+text",
            name=client_name(cid),
            marker=dict(size=sizes, color=colors, opacity=0.8,
                        line=dict(color="rgba(255,255,255,0.3)", width=1)),
            text=sub["opp_name"] if "opp_name" in sub.columns else sub["opp_id"],
            textposition="top center", textfont=dict(size=8),
            customdata=sub["_size"],
            hovertemplate="<b>%{text}</b><br>Feasibility: %{x:.1f}<br>Value: %{y:.1f}<br>Net Benefit: $%{customdata:,.0f}<extra></extra>",
        ))

    fig.add_hline(y=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.add_vline(x=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.update_xaxes(range=[0.5, 5.5], title_text="Feasibility Score →", title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[0.5, 5.5], title_text="Value Score →", title_font=dict(size=10, color=MUTED))
    fig.update_layout(height=400)
    return fig


def build_value_by_function(opps: pd.DataFrame, fin: pd.DataFrame):
    """Stacked bar of net benefit by business function."""
    fig = _fig("Net Benefit by Function")
    if opps.empty or fin.empty:
        return fig

    nb_col = next((c for c in ["net_benefit","net_benefit_risk_adj"] if c in fin.columns), None)
    if not nb_col:
        return fig

    merged = opps.merge(fin[["opp_id", nb_col]], on="opp_id", how="left")
    merged[nb_col] = _to_num(merged[nb_col])
    _fn_col = next((c for c in ["function","dept","department"] if c in merged.columns), None)
    if not _fn_col:
        return fig

    grp = merged.groupby(_fn_col)[nb_col].sum().reset_index().sort_values(nb_col, ascending=True)
    fig.add_trace(go.Bar(
        x=grp[nb_col], y=grp[_fn_col], orientation="h",
        marker=dict(color=TEAL, opacity=0.8, line=dict(width=0)),
    ))
    fig.update_traces(marker_cornerradius=4)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(height=400)
    return fig


# ── Ticket / support charts ────────────────────────────────────────────────────
def build_automation_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("Automation Runs — Weekly Trend")
    for cid in client_ids:
        df = daily[daily["client_id"] == cid].copy()
        if df.empty:
            continue
        df = df.sort_values("date")
        df["automation_runs_success"] = _to_num(df["automation_runs_success"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk = df.groupby("week", as_index=False)["automation_runs_success"].sum()
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["automation_runs_success"],
            name=client_name(cid), mode="lines+markers",
            line=dict(color=client_color(cid), width=2.5), marker=dict(size=5),
        ))
    fig.update_layout(yaxis=dict(title_text="Runs / Week"))
    return fig


def build_support_ticket_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("Support Tickets — Created vs Closed")
    lay = LAYOUT_BASE.copy()
    lay["barmode"] = "group"
    fig.update_layout(**lay)
    for cid in client_ids:
        df = daily[daily["client_id"] == cid].copy()
        if df.empty:
            continue
        df["support_tickets_created"] = _to_num(df["support_tickets_created"])
        df["tickets_closed"]          = _to_num(df["tickets_closed"])
        df["month"] = df["date"].dt.to_period("M").apply(lambda x: str(x))
        grp = df.groupby("month", as_index=False).agg(
            created=("support_tickets_created","sum"),
            closed=("tickets_closed","sum"),
        )
        color = client_color(cid)
        fig.add_trace(go.Bar(x=grp["month"], y=grp["created"],
                             name=f"{client_name(cid)} — Created",
                             marker_color=color, opacity=0.85))
        fig.add_trace(go.Bar(x=grp["month"], y=grp["closed"],
                             name=f"{client_name(cid)} — Closed",
                             marker_color=color, opacity=0.4))
    return fig


def build_tickets_open_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("Open Ticket Backlog — Weekly Avg")
    for cid in client_ids:
        df = daily[daily["client_id"] == cid].copy()
        if df.empty:
            continue
        df = df.sort_values("date")
        df["tickets_open"] = _to_num(df["tickets_open"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk = df.groupby("week", as_index=False)["tickets_open"].mean()
        color = client_color(cid)
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["tickets_open"],
            name=client_name(cid), mode="lines+markers",
            line=dict(color=color, width=2.5), marker=dict(size=5),
            fill="tozeroy", fillcolor=_hex_to_rgba(color, 0.08),
        ))
    fig.update_layout(yaxis=dict(title_text="Avg Open Tickets"))
    return fig


def build_high_priority_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("High Priority Tickets — Weekly")
    lay = LAYOUT_BASE.copy()
    lay["barmode"] = "group"
    fig.update_layout(**lay)
    for cid in client_ids:
        df = daily[daily["client_id"] == cid].copy()
        if df.empty:
            continue
        df = df.sort_values("date")
        df["high_priority_count"] = _to_num(df["high_priority_count"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk = df.groupby("week", as_index=False)["high_priority_count"].sum()
        fig.add_trace(go.Bar(x=wk["week"], y=wk["high_priority_count"],
                             name=client_name(cid),
                             marker_color=client_color(cid), opacity=0.85))
    return fig


def build_resolution_time_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("Avg Resolution Time — Weekly (hrs)")
    for cid in client_ids:
        df = daily[daily["client_id"] == cid].copy()
        if df.empty:
            continue
        df = df.sort_values("date")
        df["avg_resolution_hrs"] = _to_num(df["avg_resolution_hrs"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk = df.groupby("week", as_index=False)["avg_resolution_hrs"].mean()
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["avg_resolution_hrs"],
            name=client_name(cid), mode="lines+markers",
            line=dict(color=client_color(cid), width=2.5), marker=dict(size=5),
        ))
    fig.update_layout(yaxis=dict(title_text="Avg Resolution (hrs)"))
    return fig


def build_baseline_comparison(daily: pd.DataFrame, baselines: pd.DataFrame, client_id: str):
    fig = _fig("Before vs After AI · Key KPIs")
    if daily.empty or baselines is None or baselines.empty:
        return fig

    kpis = [
        ("avg_resolution_hrs",      "Avg Resolution (hrs)"),
        ("support_tickets_created", "Daily Tickets Created"),
        ("tickets_open",            "Avg Open Backlog"),
        ("high_priority_count",     "Daily High Priority"),
    ]

    labels, before_vals, after_vals = [], [], []
    for kpi, label in kpis:
        if "kpi_name" not in baselines.columns:
            continue
        bl_row = baselines[baselines["kpi_name"] == kpi]
        if bl_row.empty:
            continue
        bl_val = pd.to_numeric(bl_row.iloc[0]["baseline_value"], errors="coerce")
        if pd.isna(bl_val) or bl_val == 0:
            continue
        if kpi not in daily.columns:
            continue
        current = _to_num(daily[kpi]).mean()
        if pd.isna(current):
            continue
        labels.append(label)
        before_vals.append(round(bl_val, 1))
        after_vals.append(round(current, 1))

    if not labels:
        return fig

    lay = LAYOUT_BASE.copy()
    lay["title"] = dict(text="Before vs After AI · Key KPIs",
                        font=dict(size=12, color="rgba(255,255,255,0.85)"), x=0, xanchor="left")
    lay["barmode"] = "group"
    fig.update_layout(**lay)
    fig.add_trace(go.Bar(name="Before AI", x=labels, y=before_vals,
                         marker=dict(color="rgba(100,116,139,0.7)", line=dict(width=0))))
    fig.add_trace(go.Bar(name="After AI",  x=labels, y=after_vals,
                         marker=dict(color=_hex_to_rgba(CLIENT_COLORS.get(client_id, TEAL), 0.85),
                                     line=dict(width=0))))
    fig.update_traces(marker_cornerradius=4)
    return fig
