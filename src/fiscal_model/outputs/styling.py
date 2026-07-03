"""
Kosmetik-Dokumen styling constants — BCG / McKinsey / Bain palette.

This is the SINGLE SOURCE OF TRUTH for all visual styling across
Excel, PDF, and chart outputs. When the palette changes, change it here.

References
----------
- Skill: ``C:\\Users\\VivoBook\\.agents\\skills\\kosmetik-dokumen\\SKILL.md``
- Palette: navy #0B2545, biru_primer #13315C, abu_gelap #4A4E69,
  abu_terang #E9EAEC, aksen #8DA9C4, putih #FFFFFF, teks_isi #1F2937.
- Semantic: positif #1B7F3A, negatif #C0392B, netral #9CA3AF, perhatian #F4B400.
- Fonts: Inter (body), Lato Bold (headings), Consolas (mono).
"""

from __future__ import annotations


# ══════════════════════════════════════════════════════════════════════
# Brand Palette (layout / text)
# ══════════════════════════════════════════════════════════════════════

NAVY = "#0B2545"
BIRU_PRIMER = "#13315C"
ABU_GELAP = "#4A4E69"
ABU_TERANG = "#E9EAEC"
AKSEN = "#8DA9C4"
PUTIH = "#FFFFFF"
TEKS_ISI = "#1F2937"
ZEBRA_STRIP = "#F9FAFB"  # Very light zebra stripe for dense tables
INPUT_BG = "#F0F4FF"  # Light blue for editable cells


# ══════════════════════════════════════════════════════════════════════
# Semantic Palette (data — charts, conditional formatting)
# ══════════════════════════════════════════════════════════════════════

POSITIF = "#1B7F3A"
NEGATIF = "#C0392B"
NETRAL = "#9CA3AF"
PERHATIAN = "#F4B400"
INFO = NAVY  # The primary "story" series color
GRIDLINE = "#E5E7EB"  # Thin horizontal gridlines


# ══════════════════════════════════════════════════════════════════════
# Typography
# ══════════════════════════════════════════════════════════════════════

FONT_BODY = "Inter"
FONT_HEADING = "Lato Bold"
FONT_MONO = "Consolas"
FONT_FALLBACK = "Calibri"

FONT_SIZE_H1 = 28  # Cover title / governing thought (24–32)
FONT_SIZE_H2 = 18  # Section heading (16–18)
FONT_SIZE_H3 = 13  # Subheading (13–14)
FONT_SIZE_BODY = 11  # Body text (10–11)
FONT_SIZE_CAPTION = 9  # Caption, source, footnote (8–9)
FONT_SIZE_CHART_LABEL = 10  # Axis & data labels (9–10)
FONT_SIZE_KPI = 36  # Big KPI number (28–40)


# ══════════════════════════════════════════════════════════════════════
# Layout / Spacing
# ══════════════════════════════════════════════════════════════════════

PAGE_MARGIN_CM = 2.0
LINE_HEIGHT = 1.4
BORDER_WIDTH = 0.5  # pts (for tables)
DIVIDER_WIDTH = 2.0  # pts (for accent lines under headings)
CALLBOX_BORDER = 3.0  # pts (for recommendation callout box)


# ══════════════════════════════════════════════════════════════════════
# Excel-specific
# ══════════════════════════════════════════════════════════════════════

EXCEL_PAPER_A4 = 9
EXCEL_PAPER_A3 = 8
EXCEL_HEADER_ROW_HEIGHT = 28
EXCEL_DATA_ROW_HEIGHT = 20


# ══════════════════════════════════════════════════════════════════════
# Chart-specific (matplotlib)
# ══════════════════════════════════════════════════════════════════════

CHART_DPI = 150
CHART_FIGSIZE = (9, 5)  # inches, wide format
CHART_FIGSIZE_SQUARE = (6, 6)
CHART_FIGSIZE_WIDE = (12, 5)


# ══════════════════════════════════════════════════════════════════════
# Color sequences for multi-series charts
# ══════════════════════════════════════════════════════════════════════

MULTI_SERIES_PALETTE = [
    NAVY,       # Story series
    ABU_GELAP,  # Comparison 1
    NETRAL,     # Comparison 2
    "#D1D5DB",  # Comparison 3 (lighter)
]

SENSITIVITY_PALETTE = [
    POSITIF,    # Upside
    NETRAL,     # Reference
    NEGATIF,    # Downside
]


# ══════════════════════════════════════════════════════════════════════
# Helper: get matplotlib rcParams dict for a Tufte-clean chart
# ══════════════════════════════════════════════════════════════════════

def get_matplotlib_style() -> dict:
    """Return matplotlib rcParams for a clean, Tufte-aligned chart."""
    return {
        # Fonts
        "font.family": "sans-serif",
        "font.sans-serif": [FONT_BODY, FONT_FALLBACK],
        "font.size": FONT_SIZE_CHART_LABEL,
        # Axis
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.edgecolor": NETRAL,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRIDLINE,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.7,
        "xtick.color": ABU_GELAP,
        "ytick.color": ABU_GELAP,
        # Figure
        "figure.dpi": CHART_DPI,
        "figure.facecolor": PUTIH,
        "axes.facecolor": PUTIH,
        # Legend
        "legend.frameon": False,
        "legend.fontsize": FONT_SIZE_CAPTION,
        "legend.labelcolor": ABU_GELAP,
        # No more defaults with lots of colors
        "axes.prop_cycle": None,
    }
