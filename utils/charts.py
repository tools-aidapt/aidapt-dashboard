"""Reusable Plotly chart builders — Aidapt premium dark theme."""

import copy
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── Brand colours ──────────────────────────────────────────────────────────────
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

COLOR_CYCLE = ["#3B82F6", "#8B5CF6", "#F59E0B", "#00C9B1", "#10B981", "#EF4444",
               "#F97316", "#06B6D4", "#EC4899", "#A855F7", "#14B8A6", "#FBBF24"]
PALETTE = COLOR_CYCLE[:]

# ── Shared layout ──────────────────────────────────────────────────────────────
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="rgba(255,255,255,0.55)", size=11),
    margin=dict(l=12, r=12, t=36, b=8),
    legend=dict(
        bgcolor="rgba(15,25,35,0.7)",
        bordercolor="rgba(255,255,255,0.06)",
        borderwidth=1,
        font=dict(size=10, color="rgba(255,255,255,0.65)"),
        orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5,
        itemgap=16,
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(size=10, color="rgba(255,255,255,0.4)"),
        linecolor="rgba(255,255,255,0.06)",
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(size=10, color="rgba(255,255,255,0.4)"),
        linecolor="rgba(0,0,0,0)",
        showgrid=True,
    ),
    hoverlabel=dict(
        bgcolor="#0F1E2D",
        bordercolor="rgba(255,255,255,0.12)",
        font=dict(color="white", size=12, family="DM Sans"),
        namelength=-1,
    ),
)


def build_client_maps(clients_df: pd.DataFrame):
    global CLIENT_NAMES, CLIENT_COLORS
    CLIENT_NAMES  = {}
    CLIENT_COLORS = {}
    for i, (_, row) in enumerate(clients_df.iterrows()):
        cid = row["client_id"]
        CLIENT_NAMES[cid]  = row["client_name"]
        CLIENT_COLORS[cid] = COLOR_CYCLE[i % len(COLOR_CYCLE)]


def client_name(cid):  return CLIENT_NAMES.get(cid, cid)
def client_color(cid): return CLIENT_COLORS.get(cid, TEAL)

def _hex_to_rgba(hex_color, alpha=0.8):
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(0,201,177,{alpha})"

def _to_num(series):
    return pd.to_numeric(series, errors="coerce")

def _fig(title=""):
    title_obj = dict(
        text=title,
        font=dict(size=13, color="rgba(255,255,255,0.9)", family="DM Sans"),
        x=0, xanchor="left", pad=dict(b=4),
    ) if title else None

    layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="rgba(255,255,255,0.55)", size=11),
        margin=dict(l=12, r=12, t=36, b=8),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10, color="rgba(255,255,255,0.4)"),
            linecolor="rgba(255,255,255,0.06)",
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10, color="rgba(255,255,255,0.4)"),
            linecolor="rgba(0,0,0,0)",
            showgrid=True,
        ),
        legend=dict(
            bgcolor="rgba(15,25,35,0.7)",
            bordercolor="rgba(255,255,255,0.06)",
            borderwidth=1,
            font=dict(size=10, color="rgba(255,255,255,0.65)"),
            orientation="h",
            yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5,
        ),
        hoverlabel=dict(
            bgcolor="#0F1E2D",
            bordercolor="rgba(255,255,255,0.12)",
            font=dict(color="white", size=12, family="DM Sans"),
        ),
        title=title_obj,
    )
    return go.Figure(layout=layout)

def config():
    return {"displayModeBar": False, "responsive": True}

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

def kpi_card(label, value, unit="", delta="", delta_type="flat", accent=TEAL):
    delta_cls = {"up":"delta-up","down":"delta-down","flat":"delta-flat"}.get(delta_type,"delta-flat")
    arrow = {"up":"▲ ","down":"▼ ","flat":""}.get(delta_type,"")
    return (f'<div class="kpi-card" style="--accent:{accent}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>'
            f'<div class="kpi-delta {delta_cls}">{arrow}{delta}</div></div>')

def badge(text, status="live"):
    return f'<span class="badge badge-{status}">{text}</span>'


# ══════════════════════════════════════════════════════════════════════════════
#  LINE CHART  — glowing line, smooth area fill, dot markers with halo
# ══════════════════════════════════════════════════════════════════════════════
def line_chart(df, x, y_cols, names=None, colors=None, title="", y_fmt=None, dash_cols=None):
    fig = _fig(title)
    colors    = colors or PALETTE
    dash_cols = dash_cols or []
    single    = len(y_cols) == 1

    for i, col in enumerate(y_cols):
        name  = (names or y_cols)[i]
        color = colors[i % len(colors)]
        dash  = "dot" if col in dash_cols else "solid"
        rgba_fill = _hex_to_rgba(color, 0.10)

        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=name,
            mode="lines+markers",
            line=dict(color=color, width=3, dash=dash, shape="spline", smoothing=0.8),
            marker=dict(
                size=8, color="#0F1923",
                line=dict(color=color, width=2.5),
                symbol="circle",
            ),
            fill="tozeroy" if single else "none",
            fillcolor=rgba_fill if single else None,
            hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y}}<extra></extra>",
        ))

        # glow layer (wider, transparent line behind)
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=name,
            mode="lines",
            line=dict(color=_hex_to_rgba(color, 0.18), width=10, dash=dash, shape="spline", smoothing=0.8),
            showlegend=False,
            hoverinfo="skip",
        ))

    # bring data lines to front by reordering traces
    n = len(y_cols)
    order = list(range(0, 2*n, 2)) + list(range(1, 2*n, 2))  # data traces first, glows last
    fig.data = tuple(fig.data[i] for i in order)

    fig.update_layout(height=300)
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  BAR CHART  — rounded, gradient-ish color with subtle hover highlight
# ══════════════════════════════════════════════════════════════════════════════
def bar_chart(df, x, y, color=TEAL, title="", horizontal=False, y_fmt=None, text=None):
    fig = _fig(title)

    # Build per-bar color list if a list was passed, otherwise single color
    if isinstance(color, list):
        bar_colors = color
    else:
        bar_colors = color

    fig.add_trace(go.Bar(
        x=df[y] if horizontal else df[x],
        y=df[x] if horizontal else df[y],
        orientation="h" if horizontal else "v",
        marker=dict(
            color=bar_colors,
            opacity=0.9,
            line=dict(width=0),
            cornerradius=6,
        ),
        text=df[text] if text else None,
        textposition="outside" if text else "none",
        textfont=dict(size=10, color="rgba(255,255,255,0.7)"),
        hovertemplate="%{y}" if horizontal else "%{x}<br><b>%{y:,.0f}</b><extra></extra>",
    ))

    fig.update_layout(height=300)
    if y_fmt:
        ax = "xaxis" if horizontal else "yaxis"
        fig.update_layout(**{ax: dict(tickformat=y_fmt)})
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-BAR  — grouped/stacked with rounded corners and opacity depth
# ══════════════════════════════════════════════════════════════════════════════
def multi_bar(df, x, y_cols, names=None, colors=None, title="", stacked=False, y_fmt=None):
    fig = _fig(title)
    colors = colors or PALETTE
    for i, col in enumerate(y_cols):
        name  = (names or y_cols)[i]
        color = colors[i % len(colors)]
        fig.add_trace(go.Bar(
            x=df[x], y=df[col], name=name,
            marker=dict(color=color, opacity=0.88, line=dict(width=0), cornerradius=5),
            hovertemplate=f"<b>{name}</b><br>%{{x}}<br><b>%{{y:,.0f}}</b><extra></extra>",
        ))
    fig.update_layout(barmode="stack" if stacked else "group", height=300)
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  COMBO  — bar (filled) + dotted line on secondary axis
# ══════════════════════════════════════════════════════════════════════════════
def combo_chart(df, x, bar_col, line_col, bar_name="", line_name="",
                bar_color=TEAL, line_color=GOLD, title="", y_fmt=None):
    fig = _fig(title)
    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_col], name=bar_name,
        marker=dict(color=bar_color, opacity=0.75, line=dict(width=0), cornerradius=5),
        yaxis="y",
        hovertemplate=f"<b>{bar_name}</b><br>%{{x}}<br>%{{y}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_col], name=line_name, mode="lines+markers",
        line=dict(color=line_color, width=2.5, dash="dot", shape="spline", smoothing=0.7),
        marker=dict(size=7, color="#0F1923", line=dict(color=line_color, width=2)),
        yaxis="y2",
        hovertemplate=f"<b>{line_name}</b><br>%{{x}}<br>%{{y}}<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=y_fmt or ""),
        yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(size=10, color=line_color), tickformat=y_fmt or ""),
        barmode="group", height=300,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  DONUT  — thick ring, dark separator, center annotation
# ══════════════════════════════════════════════════════════════════════════════
def donut(labels, values, title="", colors=None):
    fig = _fig()
    colors = colors or PALETTE
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=0.68,
        marker=dict(
            colors=colors[:len(labels)],
            line=dict(color="#0B1520", width=3),
        ),
        textinfo="label+percent",
        textfont=dict(size=10, color="rgba(255,255,255,0.75)"),
        insidetextorientation="horizontal",
        pull=[0.03] + [0]*(len(labels)-1),
        hovertemplate="<b>%{label}</b><br>%{value}<br>%{percent}<extra></extra>",
    ))
    if title:
        fig.update_layout(title=dict(
            text=title, font=dict(size=13, color="rgba(255,255,255,0.9)"), x=0, xanchor="left"))
    fig.update_layout(showlegend=False, height=280)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  BUBBLE CHART
# ══════════════════════════════════════════════════════════════════════════════
def bubble_chart(df, x, y, size, color_col=None, label_col=None, title="",
                 x_title="Feasibility Score →", y_title="Value Score →", colors=None):
    fig = _fig(title)
    if color_col and color_col in df.columns:
        groups  = df[color_col].unique()
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
                            opacity=0.85, line=dict(color="rgba(255,255,255,0.25)", width=1)),
                text=sub[label_col] if label_col else None,
                textposition="top center", textfont=dict(size=9),
                customdata=sub[size],
                hovertemplate="<b>%{text}</b><br>Feasibility: %{x:.1f}<br>Value: %{y:.1f}<br>$%{customdata:,.0f}<extra></extra>",
            ))
    fig.add_hline(y=3, line=dict(color="rgba(255,255,255,0.07)", dash="dot", width=1))
    fig.add_vline(x=3, line=dict(color="rgba(255,255,255,0.07)", dash="dot", width=1))
    fig.update_xaxes(range=[0.5,5.5], title_text=x_title, title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[0.5,5.5], title_text=y_title, title_font=dict(size=10, color=MUTED))
    fig.update_layout(height=400)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  GAUGE
# ══════════════════════════════════════════════════════════════════════════════
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
                dict(range=[0, max_val*0.4],  color="rgba(239,68,68,0.12)"),
                dict(range=[max_val*0.4, max_val*0.7], color="rgba(245,158,11,0.12)"),
                dict(range=[max_val*0.7, max_val],     color="rgba(16,185,129,0.12)"),
            ],
        ),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=20,r=20,t=50,b=20),
                      font=dict(family="DM Sans", color="rgba(255,255,255,0.6)"), height=180)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  OPPORTUNITY CHARTS
# ══════════════════════════════════════════════════════════════════════════════
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

    _fs = next((c for c in ["feasibility_score"] if c in merged.columns), None)
    _vs = next((c for c in ["value_score"]       if c in merged.columns), None)
    _st = next((c for c in ["initiative_status","status"] if c in merged.columns), None)
    if not _fs or not _vs:
        return fig

    status_colors = {"Live":TEAL,"Pilot":BLUE,"In Pilot":BLUE,"Backlog":"#64748B","Paused":RED}
    for cid in merged["client_id"].unique():
        sub = merged[merged["client_id"]==cid].copy()
        sub["_fs"] = _to_num(sub[_fs])
        sub["_vs"] = _to_num(sub[_vs])
        sub = sub.dropna(subset=["_fs","_vs"])
        if sub.empty: continue
        sizes  = np.sqrt(sub["_size"].clip(lower=1)) / 25
        sizes  = sizes.clip(lower=10, upper=45)
        colors = [status_colors.get(s,"#64748B") for s in (sub[_st] if _st else ["Backlog"]*len(sub))]
        fig.add_trace(go.Scatter(
            x=sub["_fs"], y=sub["_vs"], mode="markers+text", name=client_name(cid),
            marker=dict(size=sizes, color=colors, opacity=0.85,
                        line=dict(color="rgba(255,255,255,0.25)", width=1)),
            text=sub["opp_name"] if "opp_name" in sub.columns else sub["opp_id"],
            textposition="top center", textfont=dict(size=8),
            customdata=sub["_size"],
            hovertemplate="<b>%{text}</b><br>Feasibility: %{x:.1f}<br>Value: %{y:.1f}<br>$%{customdata:,.0f}<extra></extra>",
        ))
    fig.add_hline(y=3, line=dict(color="rgba(255,255,255,0.07)", dash="dot", width=1))
    fig.add_vline(x=3, line=dict(color="rgba(255,255,255,0.07)", dash="dot", width=1))
    fig.update_xaxes(range=[0.5,5.5], title_text="Feasibility Score →", title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[0.5,5.5], title_text="Value Score →",       title_font=dict(size=10, color=MUTED))
    fig.update_layout(height=400)
    return fig


def build_value_by_function(opps: pd.DataFrame, fin: pd.DataFrame):
    fig = _fig("Net Benefit by Function")
    if opps.empty or fin.empty: return fig
    nb_col = next((c for c in ["net_benefit","net_benefit_risk_adj"] if c in fin.columns), None)
    if not nb_col: return fig
    merged  = opps.merge(fin[["opp_id",nb_col]], on="opp_id", how="left")
    merged[nb_col] = _to_num(merged[nb_col])
    fn_col  = next((c for c in ["function","dept","department"] if c in merged.columns), None)
    if not fn_col: return fig
    grp = merged.groupby(fn_col)[nb_col].sum().reset_index().sort_values(nb_col, ascending=True)
    # gradient color by value
    vals    = grp[nb_col].tolist()
    max_v   = max(vals) or 1
    bar_cls = [_hex_to_rgba(TEAL, 0.5 + 0.45*(v/max_v)) for v in vals]
    fig.add_trace(go.Bar(
        x=grp[nb_col], y=grp[fn_col], orientation="h",
        marker=dict(color=bar_cls, line=dict(width=0), cornerradius=5),
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(height=400)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  SUPPORT / TICKET CHARTS  — heavily redesigned
# ══════════════════════════════════════════════════════════════════════════════

def build_automation_trend(daily: pd.DataFrame, client_ids: list):
    fig = _fig("Automation Runs — Weekly Trend")
    for cid in client_ids:
        df = daily[daily["client_id"]==cid].copy()
        if df.empty: continue
        df = df.sort_values("date")
        df["automation_runs_success"] = _to_num(df["automation_runs_success"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk    = df.groupby("week", as_index=False)["automation_runs_success"].sum()
        color = client_color(cid)
        cname = client_name(cid)
        # area fill
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["automation_runs_success"], name=cname,
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.8),
            marker=dict(size=7, color="#0F1923", line=dict(color=color, width=2)),
            fill="tozeroy", fillcolor=_hex_to_rgba(color, 0.08),
            hovertemplate=f"<b>{cname}</b><br>%{{x|%b %d}}<br><b>%{{y:,.0f}} runs</b><extra></extra>",
        ))
    fig.update_layout(yaxis=dict(title_text="Runs / Week", title_font=dict(size=10)), height=310)
    return fig


def build_support_ticket_trend(daily: pd.DataFrame, client_ids: list):
    """Created vs Closed — grouped bars per client, closed shown as outlined/lighter."""
    fig = _fig("Support Tickets — Created vs Closed")
    for cid in client_ids:
        df = daily[daily["client_id"]==cid].copy()
        if df.empty: continue
        df["support_tickets_created"] = _to_num(df["support_tickets_created"])
        df["tickets_closed"]          = _to_num(df["tickets_closed"])
        df["month"] = df["date"].dt.to_period("M").apply(lambda x: str(x))
        grp = df.groupby("month", as_index=False).agg(
            created=("support_tickets_created","sum"),
            closed=("tickets_closed","sum"),
        )
        color = client_color(cid)
        cname = client_name(cid)

        # Created — solid fill
        fig.add_trace(go.Bar(
            x=grp["month"], y=grp["created"],
            name=f"{cname} — Created",
            marker=dict(color=color, opacity=0.90, line=dict(width=0), cornerradius=4),
            hovertemplate=f"<b>{cname} Created</b><br>%{{x}}<br><b>%{{y:,.0f}} tickets</b><extra></extra>",
        ))
        # Closed — same color, light fill + border
        fig.add_trace(go.Bar(
            x=grp["month"], y=grp["closed"],
            name=f"{cname} — Closed",
            marker=dict(
                color=_hex_to_rgba(color, 0.25),
                line=dict(color=color, width=1.5),
                cornerradius=4,
            ),
            hovertemplate=f"<b>{cname} Closed</b><br>%{{x}}<br><b>%{{y:,.0f}} tickets</b><extra></extra>",
        ))

    fig.update_layout(barmode="group", height=310,
                      bargap=0.18, bargroupgap=0.06)
    return fig


def build_tickets_open_trend(daily: pd.DataFrame, client_ids: list):
    """Open backlog with smooth area fill and gradient under curve."""
    fig = _fig("Open Ticket Backlog — Weekly Avg")
    for cid in client_ids:
        df = daily[daily["client_id"]==cid].copy()
        if df.empty: continue
        df = df.sort_values("date")
        df["tickets_open"] = _to_num(df["tickets_open"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk    = df.groupby("week", as_index=False)["tickets_open"].mean()
        color = client_color(cid)
        cname = client_name(cid)

        # glow layer
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["tickets_open"], showlegend=False,
            mode="lines", hoverinfo="skip",
            line=dict(color=_hex_to_rgba(color, 0.15), width=10, shape="spline", smoothing=0.8),
        ))
        # main line + area
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["tickets_open"], name=cname,
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.8),
            marker=dict(size=7, color="#0F1923", line=dict(color=color, width=2.5)),
            fill="tozeroy", fillcolor=_hex_to_rgba(color, 0.07),
            hovertemplate=f"<b>{cname}</b><br>%{{x|%b %d}}<br><b>%{{y:.1f}} open tickets</b><extra></extra>",
        ))

    fig.update_layout(yaxis=dict(title_text="Avg Open Tickets", title_font=dict(size=10)), height=310)
    return fig


def build_high_priority_trend(daily: pd.DataFrame, client_ids: list):
    """High priority weekly — stacked bars with alert-red accent per client."""
    fig = _fig("High Priority Tickets — Weekly")
    for cid in client_ids:
        df = daily[daily["client_id"]==cid].copy()
        if df.empty: continue
        df = df.sort_values("date")
        df["high_priority_count"] = _to_num(df["high_priority_count"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk    = df.groupby("week", as_index=False)["high_priority_count"].sum()
        color = client_color(cid)
        cname = client_name(cid)

        fig.add_trace(go.Bar(
            x=wk["week"], y=wk["high_priority_count"], name=cname,
            marker=dict(
                color=color, opacity=0.88,
                line=dict(width=0), cornerradius=4,
            ),
            hovertemplate=f"<b>{cname}</b><br>%{{x|%b %d}}<br><b>%{{y:,.0f}} high priority</b><extra></extra>",
        ))

    # add a mean reference line across all clients combined
    all_vals_days = daily.copy()
    if "high_priority_count" in all_vals_days.columns:
        all_vals_days["high_priority_count"] = _to_num(all_vals_days["high_priority_count"])
        all_vals_days["week"] = all_vals_days["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk_all = all_vals_days[all_vals_days["client_id"].isin(client_ids)].groupby("week")["high_priority_count"].sum().reset_index()
        if not wk_all.empty:
            avg = wk_all["high_priority_count"].mean()
            fig.add_hline(
                y=avg,
                line=dict(color="rgba(239,68,68,0.45)", width=1.5, dash="dot"),
                annotation_text=f"Avg {avg:.0f}",
                annotation_font=dict(color="rgba(239,68,68,0.7)", size=10),
                annotation_position="top right",
            )

    fig.update_layout(barmode="group", height=310, bargap=0.2, bargroupgap=0.08)
    return fig


def build_resolution_time_trend(daily: pd.DataFrame, client_ids: list):
    """Avg resolution time — smooth lines with directional color hint."""
    fig = _fig("Avg Resolution Time — Weekly (hrs)")
    for cid in client_ids:
        df = daily[daily["client_id"]==cid].copy()
        if df.empty: continue
        df = df.sort_values("date")
        df["avg_resolution_hrs"] = _to_num(df["avg_resolution_hrs"])
        df["week"] = df["date"].dt.to_period("W").apply(lambda x: x.start_time)
        wk    = df.groupby("week", as_index=False)["avg_resolution_hrs"].mean()
        color = client_color(cid)
        cname = client_name(cid)

        # glow
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["avg_resolution_hrs"], showlegend=False,
            mode="lines", hoverinfo="skip",
            line=dict(color=_hex_to_rgba(color, 0.15), width=10, shape="spline", smoothing=0.8),
        ))
        fig.add_trace(go.Scatter(
            x=wk["week"], y=wk["avg_resolution_hrs"], name=cname,
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.8),
            marker=dict(size=7, color="#0F1923", line=dict(color=color, width=2.5)),
            hovertemplate=f"<b>{cname}</b><br>%{{x|%b %d}}<br><b>%{{y:.1f}} hrs</b><extra></extra>",
        ))

    fig.update_layout(yaxis=dict(title_text="Avg Resolution (hrs)", title_font=dict(size=10)), height=310)
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
        if "kpi_name" not in baselines.columns: continue
        bl_row = baselines[baselines["kpi_name"] == kpi]
        if bl_row.empty: continue
        bl_val = pd.to_numeric(bl_row.iloc[0]["baseline_value"], errors="coerce")
        if pd.isna(bl_val) or bl_val == 0: continue
        if kpi not in daily.columns: continue
        current = _to_num(daily[kpi]).mean()
        if pd.isna(current): continue
        labels.append(label)
        before_vals.append(round(bl_val, 1))
        after_vals.append(round(current, 1))

    if not labels: return fig

    client_col = CLIENT_COLORS.get(client_id, TEAL)
    fig.update_layout(barmode="group", height=320)
    fig.add_trace(go.Bar(
        name="Before AI", x=labels, y=before_vals,
        marker=dict(color="rgba(100,116,139,0.55)", line=dict(width=0), cornerradius=5),
        hovertemplate="<b>Before AI</b><br>%{x}<br>%{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="After AI", x=labels, y=after_vals,
        marker=dict(color=_hex_to_rgba(client_col, 0.88), line=dict(width=0), cornerradius=5),
        hovertemplate="<b>After AI</b><br>%{x}<br>%{y}<extra></extra>",
    ))
    return fig
