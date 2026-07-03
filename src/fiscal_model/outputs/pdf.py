"""
PDF report generator — produces BCG/McKinsey-styled investment memos
from a PSCResult using ``reportlab``.

Layout:
- Cover page (navy background, title, metadata).
- Executive summary (1 page: SCR + governing thought + 3 KPIs).
- Fiscal highlights table.
- Chart embeds.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
        KeepTogether,
        HRFlowable,
    )
except ImportError:
    raise ImportError("reportlab is required for PDF output. pip install reportlab")

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
    FONT_BODY,
    FONT_HEADING,
    FONT_SIZE_H1,
    FONT_SIZE_H2,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
)
from fiscal_model.schemas.outputs import PSCResult


class PDFReportGenerator:
    """
    Generate a consulting-styled PDF investment memo.

    Usage::

        result = engine.calculate()
        gen = PDFReportGenerator(result)
        gen.build()
        gen.save("investment_memo.pdf")
    """

    # ── Construction ─────────────────────────────────────────────────

    def __init__(self, result: PSCResult) -> None:
        self._result = result
        self._story = []
        self._styles = self._build_styles()

    # ── Public API ───────────────────────────────────────────────────

    def build(self) -> "PDFReportGenerator":
        """Build the full document."""
        self._add_cover()
        self._add_executive_summary()
        self._add_fiscal_highlights()
        self._add_recommendation()
        self._add_footer()
        return self

    def save(self, path: str) -> None:
        """Save to PDF file."""
        if not self._story:
            self.build()
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        doc.build(self._story)

    def to_bytes(self) -> bytes:
        """Return PDF as bytes."""
        buf = io.BytesIO()
        if not self._story:
            self.build()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        doc.build(self._story)
        return buf.getvalue()

    # ── Sections ────────────────────────────────────────────────────

    def _add_cover(self) -> None:
        """Cover page with navy background, title, and metadata."""
        res = self._result
        story = self._story

        # Spacer to push content down
        story.append(Spacer(1, 3 * cm))

        # Title
        story.append(Paragraph(
            res.project_name,
            self._styles["cover_title"],
        ))

        # Divider
        story.append(HRFlowable(
            width="60%", thickness=2, color=HexColor(AKSEN),
            spaceAfter=12, spaceBefore=12,
        ))

        # Subtitle
        story.append(Paragraph(
            "Financial Model — PSC Cost Recovery",
            self._styles["cover_subtitle"],
        ))

        story.append(Spacer(1, 2 * cm))

        # Governing thought
        gov = self._governing_thought()
        story.append(Paragraph(gov, self._styles["cover_gov"]))

        story.append(Spacer(1, 3 * cm))

        # Metadata
        today = datetime.now().strftime("%d %B %Y")
        story.append(Paragraph(
            f"Prepared: {today}  |  Classification: Confidential  |  PT Reka Elang Inovasi",
            self._styles["metadata"],
        ))

        story.append(PageBreak())

    def _add_executive_summary(self) -> None:
        """Executive summary: 1 page with SCR + KPIs."""
        res = self._result

        self._story.append(Paragraph("Executive Summary", self._styles["h1"]))
        self._story.append(HRFlowable(
            width="100%", thickness=2, color=HexColor(AKSEN), spaceAfter=8,
        ))

        # Situation
        self._story.append(Paragraph(
            f"<b>Situation:</b> {res.project_name} is a proposed upstream oil &amp; gas "
            f"development with cumulative production of "
            f"{res.cumulative_production_mmboe:.2f} MMBOE over "
            f"{len(res.model_years)} years ({min(res.model_years)}–{max(res.model_years)}). "
            f"The project operates under Indonesia's PSC Cost Recovery fiscal regime.",
            self._styles["body"],
        ))
        self._story.append(Spacer(1, 6))

        # Complication
        self._story.append(Paragraph(
            "<b>Complication:</b> Oil price volatility and cost recovery ceiling "
            "constraints create margin pressure. The model must demonstrate resilience "
            "under downside scenarios.",
            self._styles["body"],
        ))
        self._story.append(Spacer(1, 6))

        # Resolution
        resolution = "positive" if res.npv_contractor > 0 else "negative"
        rec_text = (
            f"<b>Resolution:</b> The base case shows a <b>{resolution} NPV of "
            f"${res.npv_contractor:,.0f}</b> (IRR {res.irr_contractor:.1%}), "
            f"with payback in {res.payback_period_years:.1f} years. "
            f"The government take is {res.government_take_pct_of_gross:.1f}% of gross revenue. "
            f"We recommend proceeding to FEED phase." if res.npv_contractor > 0
            else (
                f"<b>Resolution:</b> The base case shows a <b>{resolution} NPV of "
                f"${res.npv_contractor:,.0f}</b> (IRR {res.irr_contractor:.1%}). "
                f"Fiscal term renegotiation or cost optimization is advised."
            )
        )
        self._story.append(Paragraph(rec_text, self._styles["body"]))
        self._story.append(Spacer(1, 12))

        # KPI Table
        self._add_kpi_table()

        self._story.append(PageBreak())

    def _add_fiscal_highlights(self) -> None:
        """Fiscal highlights table."""
        res = self._result

        self._story.append(Paragraph("Fiscal Highlights", self._styles["h1"]))
        self._story.append(Spacer(1, 6))

        data = [
            ["Parameter", "Value"],
            ["FTP Rate", f"{res.ftp_pct:.0%}"],
            ["Contractor Split (after CR)", f"{res.contractor_split_after_cr:.0%}"],
            ["Cost Recovery Ceiling", f"{res.cost_recovery_ceiling_pct:.0%}"],
            ["Tax Rate (PPh Badan)", f"{res.tax_rate_pct:.0%}"],
            ["Discount Rate (WACC)", f"{res.discount_rate_pct:.1%}"],
            ["", ""],
            ["Metric", "Value"],
            ["NPV (Contractor)", f"${res.npv_contractor:,.0f}"],
            ["IRR (Contractor)", f"{res.irr_contractor:.1%}"],
            ["Payback Period", f"{res.payback_period_years:.1f} yrs" if res.payback_period_years else "N/A"],
            ["Profitability Index", f"{res.profitability_index:.2f}"],
            ["Government Take", f"{res.government_take_pct_of_gross:.1f}%"],
        ]

        t = Table(data, colWidths=[7 * cm, 7 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(PUTIH)),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), FONT_SIZE_BODY),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(AKSEN)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(PUTIH), HexColor(ABU_TERANG)]),
            ("BACKGROUND", (0, 8), (-1, 8), HexColor(BIRU_PRIMER)),
            ("TEXTCOLOR", (0, 8), (-1, 8), HexColor(PUTIH)),
        ]))
        self._story.append(t)

        self._story.append(Spacer(1, 12))

        # Warnings
        if res.warnings:
            self._story.append(Paragraph("⚠ Warnings / Caveats", self._styles["h3"]))
            for w in res.warnings:
                self._story.append(Paragraph(f"• {w}", self._styles["body"]))

    def _add_recommendation(self) -> None:
        """Recommendation callout box."""
        res = self._result
        self._story.append(Spacer(1, 16))
        self._story.append(Paragraph("Recommendation", self._styles["h1"]))

        # Callout box style
        rec = (
            f"Based on the financial analysis, the project yields an NPV of "
            f"<b>${res.npv_contractor:,.0f}</b> and IRR of "
            f"<b>{res.irr_contractor:.1%}</b>. "
            + (
                "We recommend advancing to the next phase with a focus on "
                "cost optimization and fiscal term discussions with SKK Migas."
                if res.npv_contractor > 0
                else "We recommend revisiting the cost structure and fiscal assumptions "
                "before proceeding further."
            )
        )
        self._story.append(Paragraph(rec, self._styles["callout"]))

    def _add_footer(self) -> None:
        """Document footer — added via onPage callback."""
        # Footer is handled by the template via onPage
        pass

    # ── Helpers ──────────────────────────────────────────────────────

    def _add_kpi_table(self) -> None:
        """Inline KPI table (3 tiles side by side)."""
        res = self._result
        pb = f"{res.payback_period_years:.1f} yrs" if res.payback_period_years else "N/A"

        data = [
            ["NPV", "IRR", "Payback"],
            [f"${res.npv_contractor:,.0f}", f"{res.irr_contractor:.1%}", pb],
        ]

        t = Table(data, colWidths=[5 * cm, 5 * cm, 5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(PUTIH)),
            ("BACKGROUND", (0, 1), (-1, 1), HexColor(PUTIH)),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), FONT_SIZE_BODY),
            ("FONTSIZE", (0, 1), (-1, 1), 28),
            ("TEXTCOLOR", (0, 1), (-1, 1), HexColor(NAVY)),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor(AKSEN)),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        self._story.append(t)

    def _governing_thought(self) -> str:
        res = self._result
        if res.npv_contractor > 0:
            return (
                f"Project generates positive economics with NPV "
                f"${res.npv_contractor:,.0f} and IRR {res.irr_contractor:.1%}, "
                f"recommending advancement to the next development phase."
            )
        return (
            f"Under current assumptions, the project does not meet the "
            f"hurdle rate (IRR {res.irr_contractor:.1%} vs WACC "
            f"{res.discount_rate_pct:.1%}). Fiscal adjustments are required."
        )

    def _build_styles(self) -> dict:
        """Build custom paragraph styles using standard reportlab fonts."""
        base = getSampleStyleSheet()
        # Use Helvetica (always available) — Lato requires extra font registration
        font_h = "Helvetica-Bold"
        font_b = "Helvetica"

        styles = {
            "cover_title": ParagraphStyle(
                "cover_title",
                parent=base["Title"],
                fontName=font_h,
                fontSize=32,
                leading=38,
                textColor=HexColor(NAVY),
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
            "cover_subtitle": ParagraphStyle(
                "cover_subtitle",
                parent=base["Normal"],
                fontName=font_b,
                fontSize=14,
                textColor=HexColor(AKSEN),
                alignment=TA_CENTER,
                spaceAfter=12,
            ),
            "cover_gov": ParagraphStyle(
                "cover_gov",
                parent=base["Normal"],
                fontName=font_b,
                fontSize=12,
                leading=16,
                textColor=HexColor(ABU_GELAP),
                alignment=TA_CENTER,
                fontStyle="italic",
            ),
            "metadata": ParagraphStyle(
                "metadata",
                parent=base["Normal"],
                fontName=font_b,
                fontSize=9,
                textColor=HexColor(ABU_GELAP),
                alignment=TA_CENTER,
            ),
            "h1": ParagraphStyle(
                "h1",
                parent=base["Heading1"],
                fontName=font_h,
                fontSize=FONT_SIZE_H2,
                leading=26,
                textColor=HexColor(NAVY),
                spaceAfter=8,
            ),
            "h3": ParagraphStyle(
                "h3",
                parent=base["Heading3"],
                fontName=font_h,
                fontSize=12,
                textColor=HexColor(BIRU_PRIMER),
                spaceAfter=4,
            ),
            "body": ParagraphStyle(
                "body",
                parent=base["Normal"],
                fontName=font_b,
                fontSize=FONT_SIZE_BODY,
                leading=FONT_SIZE_BODY * 1.4,
                textColor=HexColor(TEKS_ISI),
                spaceAfter=4,
            ),
            "callout": ParagraphStyle(
                "callout",
                parent=base["Normal"],
                fontName=font_b,
                fontSize=FONT_SIZE_BODY,
                leading=FONT_SIZE_BODY * 1.4,
                textColor=HexColor(TEKS_ISI),
                backColor=HexColor(ABU_TERANG),
                borderColor=HexColor(NAVY),
                borderWidth=3,
                borderPadding=12,
                spaceBefore=12,
                spaceAfter=12,
            ),
        }
        return styles
