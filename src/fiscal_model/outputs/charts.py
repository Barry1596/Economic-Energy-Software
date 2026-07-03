"""
Chart generator — produces BCG/McKinsey/Tufte-styled financial charts
using matplotlib.

Supports:
- Waterfall (bridge: revenue → net cashflow)
- Tornado (sensitivity NPV swing)
- Line chart (multi-year trends with direct labeling)
- Bar horizontal (cost breakdown sorted descending)
"""

from __future__ import annotations

import io
from typing import Optional

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend

    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.patches import FancyBboxPatch
except ImportError:
    raise ImportError("matplotlib is required for charts. pip install matplotlib")

from fiscal_model.outputs.styling import (
    NAVY,
    BIRU_PRIMER,
    ABU_GELAP,
    ABU_TERANG,
    AKSEN,
    PUTIH,
    TEKS_ISI,
    POSITIF,
    NEGATIF,
    NETRAL,
    PERHATIAN,
    INFO,
    GRIDLINE,
    FONT_BODY,
    FONT_HEADING,
    FONT_SIZE_H2,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    FONT_SIZE_CHART_LABEL,
    CHART_DPI,
    CHART_FIGSIZE,
    CHART_FIGSIZE_WIDE,
    CHART_FIGSIZE_SQUARE,
    get_matplotlib_style,
)
from fiscal_model.utils.formatting import humanize_number, humanize_currency, Currency


# ── Setup ────────────────────────────────────────────────────────────

plt.rcParams.update(get_matplotlib_style())


# ── Waterfall Chart ──────────────────────────────────────────────────

def waterfall_chart(
    components: dict[str, float],
    title: str = "Cashflow Waterfall",
    subtitle: str = "",
    ylabel: str = "USD",
    filename: Optional[str] = None,
) -> plt.Figure:
    """
    Build a waterfall (bridge) chart — shows how you get from A to B.

    Args:
        components: Ordered dict of {label: value}. First = starting point.
        title: Main action title.
        subtitle: Smaller subtitle / source line.
        ylabel: Y-axis label (e.g. "USD").
        filename: If provided, save to this path.

    Returns:
        matplotlib Figure.
    """
    labels = list(components.keys())
    values = list(components.values())

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_WIDE)
    fig.patch.set_facecolor(PUTIH)

    # Compute cumulative bottoms for waterfall bars
    bottoms = [0.0] * len(values)
    bars = [0.0] * len(values)
    for i in range(len(values)):
        if i == 0:
            bars[i] = values[i]
            bottoms[i] = 0
        else:
            prev_total = sum(values[:i])
            if values[i] >= 0:
                bars[i] = values[i]
                bottoms[i] = prev_total
            else:
                bars[i] = abs(values[i])
                bottoms[i] = prev_total + values[i]

    # Colors: start = navy, positive = green, negative = red, total = navy
    colors = []
    for i, v in enumerate(values):
        if i == 0:
            colors.append(NAVY)
        elif i == len(values) - 1:
            colors.append(NAVY)
        elif v >= 0:
            colors.append(POSITIF)
        else:
            colors.append(NEGATIF)

    ax.bar(labels, bars, bottom=bottoms, color=colors, width=0.6, edgecolor="none")

    # Data labels
    for i, (label, val) in enumerate(zip(labels, values)):
        y_pos = bottoms[i] + bars[i] / 2
        ax.text(
            i,
            y_pos,
            humanize_currency(val, Currency.USD),
            ha="center",
            va="center",
            fontsize=FONT_SIZE_CHART_LABEL,
            fontweight="bold",
            color=PUTIH if abs(val) > 0 else TEKS_ISI,
        )

    # Connector lines between bars
    for i in range(len(labels) - 1):
        top = bottoms[i] + bars[i] if values[i] >= 0 else bottoms[i]
        next_bottom = bottoms[i + 1]
        ax.plot(
            [i + 0.3, i + 0.7],
            [top, next_bottom],
            color=NETRAL,
            linewidth=0.8,
            linestyle="--",
        )

    ax.set_title(title, fontsize=FONT_SIZE_H2, fontweight="bold", color=NAVY, pad=15)
    if subtitle:
        ax.text(
            0.5,
            -0.12,
            subtitle,
            transform=ax.transAxes,
            ha="center",
            fontsize=FONT_SIZE_CAPTION,
            color=ABU_GELAP,
            style="italic",
        )

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: humanize_currency(x)))
    ax.tick_params(axis="x", rotation=30)
    ax.set_ylabel(ylabel)

    fig.tight_layout()
    if filename:
        fig.savefig(filename, dpi=CHART_DPI, bbox_inches="tight", facecolor=PUTIH)
    return fig


# ── Tornado Chart ────────────────────────────────────────────────────

def tornado_chart(
    variables: list[str],
    npv_swings: list[float],
    base_npv: float,
    title: str = "Sensitivity: NPV Impact by Variable",
    subtitle: str = "",
    filename: Optional[str] = None,
) -> plt.Figure:
    """
    Tornado / sensitivity chart — horizontal bars showing NPV swing per variable.

    Bars are sorted by swing magnitude (largest at top). Green = upside, Red = downside.

    Args:
        variables: Variable names (sorted by swing magnitude).
        npv_swings: NPV deviation from base case for each variable (matching order).
        base_npv: Base case NPV (for annotation).
        title: Action title.
        subtitle: Source/caption.
        filename: Save path.
    """
    fig, ax = plt.subplots(figsize=(10, max(4, len(variables) * 0.45)))
    fig.patch.set_facecolor(PUTIH)

    n = len(variables)
    y_pos = range(n)

    colors = [POSITIF if v >= 0 else NEGATIF for v in npv_swings]
    ax.barh(y_pos, npv_swings, color=colors, height=0.5, edgecolor="none")

    # Labels
    for i, (var, val) in enumerate(zip(variables, npv_swings)):
        label = f"{humanize_number(val)} ({'↑' if val >= 0 else '↓'})"
        x_pos = val + (max(abs(v) for v in npv_swings) * 0.02) if val >= 0 else val - (max(abs(v) for v in npv_swings) * 0.05)
        ha = "left" if val >= 0 else "right"
        ax.text(x_pos, i, label, va="center", ha=ha, fontsize=FONT_SIZE_CHART_LABEL, color=TEKS_ISI)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(variables)
    ax.axvline(x=0, color=NETRAL, linewidth=1.0)

    # Annotate base NPV
    ax.text(
        0.98, 0.02, f"Base NPV: ${base_npv:,.0f}",
        transform=ax.transAxes, ha="right", fontsize=FONT_SIZE_CAPTION,
        color=ABU_GELAP, style="italic",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=ABU_TERANG, edgecolor="none"),
    )

    ax.set_title(title, fontsize=FONT_SIZE_H2, fontweight="bold", color=NAVY, pad=15)
    if subtitle:
        ax.text(0.5, -0.08, subtitle, transform=ax.transAxes, ha="center",
                fontsize=FONT_SIZE_CAPTION, color=ABU_GELAP, style="italic")

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: humanize_number(x)))
    fig.tight_layout()
    if filename:
        fig.savefig(filename, dpi=CHART_DPI, bbox_inches="tight", facecolor=PUTIH)
    return fig


# ── Line Chart (Trend) ───────────────────────────────────────────────

def trend_chart(
    years: list[int],
    series: dict[str, list[float]],
    title: str = "Production & Revenue Projection",
    subtitle: str = "",
    ylabel: str = "USD",
    highlight_idx: int = 0,
    filename: Optional[str] = None,
) -> plt.Figure:
    """
    Multi-series line chart with one highlighted "story" series (navy) and
    the rest rendered in muted grey.

    Args:
        years: X-axis values.
        series: Dict of {series_name: [values_per_year]}.
        title: Action title.
        subtitle: Caption/source.
        ylabel: Y-axis label.
        highlight_idx: Index of the story series (0 = first).
        filename: Save path.
    """
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE)
    fig.patch.set_facecolor(PUTIH)

    series_names = list(series.keys())
    colors_pool = [NAVY, ABU_GELAP, NETRAL, "#D1D5DB", AKSEN]

    for i, name in enumerate(series_names):
        is_story = i == highlight_idx
        color = NAVY if is_story else colors_pool[i % len(colors_pool)]
        lw = 2.5 if is_story else 1.5
        alpha = 1.0 if is_story else 0.7

        ax.plot(years, series[name], color=color, linewidth=lw, alpha=alpha, label=name)

        # Direct label at the end
        if len(years) > 0:
            ax.text(
                years[-1] + 0.2,
                series[name][-1],
                name,
                fontsize=FONT_SIZE_CHART_LABEL,
                color=color,
                va="center",
                fontweight="bold" if is_story else "normal",
            )

    ax.set_title(title, fontsize=FONT_SIZE_H2, fontweight="bold", color=NAVY, pad=15)
    if subtitle:
        ax.text(0.5, -0.12, subtitle, transform=ax.transAxes, ha="center",
                fontsize=FONT_SIZE_CAPTION, color=ABU_GELAP, style="italic")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: humanize_currency(x)))
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Year")

    fig.tight_layout()
    if filename:
        fig.savefig(filename, dpi=CHART_DPI, bbox_inches="tight", facecolor=PUTIH)
    return fig


# ── Bar Horizontal (Cost Breakdown) ──────────────────────────────────

def bar_horizontal_sorted(
    categories: list[str],
    values: list[float],
    title: str = "Cost Breakdown by Category",
    subtitle: str = "",
    xlabel: str = "USD",
    top_n: Optional[int] = None,
    filename: Optional[str] = None,
) -> plt.Figure:
    """
    Horizontal bar chart sorted by value descending.

    The largest item is highlighted in navy; all others in muted grey.
    """
    # Sort descending
    paired = sorted(zip(values, categories), reverse=True)
    if top_n:
        paired = paired[:top_n]
    sorted_vals, sorted_cats = zip(*paired) if paired else ([], [])

    fig, ax = plt.subplots(figsize=(9, max(3, len(sorted_cats) * 0.4)))
    fig.patch.set_facecolor(PUTIH)

    colors = [NAVY if i == 0 else NETRAL for i in range(len(sorted_cats))]
    ax.barh(range(len(sorted_cats)), sorted_vals, color=colors, height=0.6, edgecolor="none")

    ax.set_yticks(range(len(sorted_cats)))
    ax.set_yticklabels(sorted_cats)
    ax.invert_yaxis()

    # Value labels
    for i, val in enumerate(sorted_vals):
        ax.text(
            val + (max(sorted_vals) * 0.01),
            i,
            humanize_currency(val, Currency.USD),
            va="center",
            fontsize=FONT_SIZE_CHART_LABEL,
            color=TEKS_ISI,
            fontweight="bold" if i == 0 else "normal",
        )

    ax.set_title(title, fontsize=FONT_SIZE_H2, fontweight="bold", color=NAVY, pad=15)
    if subtitle:
        ax.text(0.5, -0.08, subtitle, transform=ax.transAxes, ha="center",
                fontsize=FONT_SIZE_CAPTION, color=ABU_GELAP, style="italic")

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: humanize_currency(x)))
    ax.set_xlabel(xlabel)

    fig.tight_layout()
    if filename:
        fig.savefig(filename, dpi=CHART_DPI, bbox_inches="tight", facecolor=PUTIH)
    return fig


# ── Export ────────────────────────────────────────────────────────────

def figure_to_bytes(fig: plt.Figure, dpi: int = CHART_DPI) -> bytes:
    """Convert a matplotlib figure to PNG bytes (for embedding in Excel/PDF)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=PUTIH)
    buf.seek(0)
    return buf.read()
