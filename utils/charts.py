"""Reusable Plotly chart builders with consistent Aidapt dark theme."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Theme constants ────────────────────────────────────────────────────────────
TEAL   = "#00C9B1"
BLUE   = "#3B82F6"
PURPLE = "#7C3AED"
GOLD   = "#F59E0B"
GREEN  = "#10B981"
RED    = "#EF4444"
SLATE  = "#475569"
MUTED  = "rgba(255,255,255,0.25)"

CLIENT_COLORS = {"C001": TEAL, "C002": BLUE, "C003": PURPLE}
CLIENT_NAMES  = {"C001": "Alpha Retail", "C002": "Beta Logistics", "C003": "Gamma Finance"}

PALETTE = [TEAL, BLUE, PURPLE, GOLD, GREEN, RED, "#F97316", "#06B6D4"]

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

def _fig(title=""):
    fig = go.Figure()
    lay = LAYOUT_BASE.copy()
    if title:
        lay["title"] = dict(text=title, font=dict(size=12, color="rgba(255,255,255,0.85)"), x=0, xanchor="left")
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
            x=df[x], y=df[col], name=name,
            mode="lines+markers",
            line=dict(color=colors[i % len(colors)], width=2.5, dash=dash),
            marker=dict(size=5, color=colors[i % len(colors)]),
            fill="tozeroy" if len(y_cols) == 1 else "none",
            fillcolor=colors[0].replace(")", ",0.08)").replace("rgb", "rgba") if len(y_cols)==1 else None,
        ))
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ── Bar chart ──────────────────────────────────────────────────────────────────
def bar_chart(df, x, y, color=TEAL, title="", horizontal=False, y_fmt=None, text=None):
    fig = _fig(title)
    kwargs = dict(
        x=df[y] if horizontal else df[x],
        y=df[x] if horizontal else df[y],
        orientation="h" if horizontal else "v",
        marker=dict(color=color, opacity=0.85, line=dict(width=0)),
        text=df[text] if text else None,
        textposition="outside" if text else "none",
        textfont=dict(size=10, color="rgba(255,255,255,0.7)"),
    )
    fig.add_trace(go.Bar(**kwargs))
    fig.update_traces(marker_cornerradius=5)
    if y_fmt:
        ax = "xaxis" if horizontal else "yaxis"
        fig.update_layout(**{ax: dict(tickformat=y_fmt)})
    return fig


# ── Multi-bar ──────────────────────────────────────────────────────────────────
def multi_bar(df, x, y_cols, names=None, colors=None, title="", stacked=False, y_fmt=None):
    fig = _fig(title)
    colors = colors or PALETTE
    barmode = "stack" if stacked else "group"
    for i, col in enumerate(y_cols):
        name = (names or y_cols)[i]
        fig.add_trace(go.Bar(
            x=df[x], y=df[col], name=name,
            marker=dict(color=colors[i % len(colors)], opacity=0.85, line=dict(width=0)),
        ))
    fig.update_traces(marker_cornerradius=4)
    fig.update_layout(barmode=barmode)
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    return fig


# ── Combo (bar + line) ─────────────────────────────────────────────────────────
def combo_chart(df, x, bar_col, line_col, bar_name="", line_name="",
                bar_color=TEAL, line_color=GOLD, title="", y_fmt=None):
    fig = _fig(title)
    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_col], name=bar_name,
        marker=dict(color=bar_color, opacity=0.75, line=dict(width=0)),
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_col], name=line_name,
        mode="lines+markers",
        line=dict(color=line_color, width=2.5, dash="dot"),
        marker=dict(size=6, color=line_color),
        yaxis="y2",
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
        labels=labels, values=values,
        hole=0.65,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#0B1520", width=2)),
        textinfo="label+percent",
        textfont=dict(size=10),
        insidetextorientation="horizontal",
    ))
    if title:
        fig.update_layout(
            title=dict(text=title, font=dict(size=12, color="rgba(255,255,255,0.85)"), x=0, xanchor="left")
        )
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
            sub = df[df[color_col] == grp]
            sizes = np.sqrt(sub[size].clip(lower=1)) / 8
            sizes = sizes.clip(lower=8, upper=40)
            fig.add_trace(go.Scatter(
                x=sub[x], y=sub[y],
                mode="markers+text" if label_col else "markers",
                name=str(grp),
                marker=dict(size=sizes, color=col_map.get(grp, TEAL),
                            opacity=0.8, line=dict(color="rgba(255,255,255,0.3)", width=1)),
                text=sub[label_col] if label_col else None,
                textposition="top center", textfont=dict(size=9),
                hovertemplate=(
                    f"<b>%{{text}}</b><br>{x_title}: %{{x:.1f}}<br>{y_title}: %{{y:.1f}}"
                    f"<br>Net 3yr: $%{{customdata:,.0f}}<extra>{grp}</extra>"
                ),
                customdata=sub[size],
            ))
    # Quadrant lines
    fig.add_hline(y=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.add_vline(x=3, line=dict(color="rgba(255,255,255,0.08)", dash="dot", width=1))
    fig.update_xaxes(range=[1, 5.3], title_text=x_title, title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(range=[1, 5.3], title_text=y_title, title_font=dict(size=10, color=MUTED))
    return fig


# ── Gauge ──────────────────────────────────────────────────────────────────────
def gauge(value, title="", max_val=5, color=TEAL):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(font=dict(size=28, color="white", family="DM Mono"), suffix=""),
        title=dict(text=title, font=dict(size=11, color="rgba(255,255,255,0.6)")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="rgba(255,255,255,0.3)",
                      tickfont=dict(size=9, color="rgba(255,255,255,0.4)")),
            bar=dict(color=color, thickness=0.25),
            bgcolor="rgba(255,255,255,0.04)",
            borderwidth=0,
            steps=[
                dict(range=[0, max_val*0.4], color="rgba(239,68,68,0.12)"),
                dict(range=[max_val*0.4, max_val*0.7], color="rgba(245,158,11,0.12)"),
                dict(range=[max_val*0.7, max_val], color="rgba(16,185,129,0.12)"),
            ],
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="DM Sans", color="rgba(255,255,255,0.6)"),
        height=180,
    )
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
