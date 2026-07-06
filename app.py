"""
Energi Economic Software — Streamlit Web App
=============================================
Jalankan:  streamlit run app.py
Buka:      http://localhost:8501

Fitur:
- Input parameter PSC (production, capex, opex, fiscal terms)
- Run financial model engine
- Dashboard KPI + waterfall chart + cashflow table
- Export Excel (BCG/McKinsey styled) & PDF (investment memo)
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path

# Pastikan src/ ada di path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set matplotlib backend SEBELUM import pyplot (mencegah warning & memastikan headless)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import streamlit as st  # noqa: E402
import pandas as pd  # noqa: E402

from fiscal_model.schemas.inputs import (  # noqa: E402
    PSCInput,
    ProductionProfile,
    ProductionProfileVectors,
    PriceAssumption,
    CapexSchedule,
    CapexScheduleItem,
    OpexSchedule,
    OpexCategory,
)
from fiscal_model.fiscal.psc import PSCCostRecovery  # noqa: E402
from fiscal_model.outputs.excel import ExcelReportGenerator  # noqa: E402
from fiscal_model.outputs.pdf import PDFReportGenerator  # noqa: E402
from fiscal_model.outputs.charts import (  # noqa: E402
    waterfall_chart,
    trend_chart,
    bar_horizontal_sorted,
)
from fiscal_model.outputs.styling import (  # noqa: E402
    NAVY,
    BIRU_PRIMER,
    ABU_GELAP,
    ABU_TERANG,
    AKSEN,
    PUTIH,
    TEKS_ISI,
    ZEBRA_STRIP,
    POSITIF,
    NEGATIF,
    NETRAL,
    PERHATIAN,
)

# ══════════════════════════════════════════════════════════════════════
# Page Config
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Energi Economic Software",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# Custom CSS — Kosmetik-Dokumen (BCG/McKinsey/Bain)
# 3 lapisan: narasi (action title + governing thought + so-what),
# data-viz (Tufte/FT hygiene), kosmetik (palet navy + Inter/Lato).
# ══════════════════════════════════════════════════════════════════════

st.markdown(
    f"""
<style>
    /* ─── Font & global ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lato:wght@400;700;900&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', 'Calibri', 'Arial', sans-serif;
        color: {TEKS_ISI};
    }}
    h1, h2, h3, h4 {{
        font-family: 'Lato', 'Inter', sans-serif !important;
    }}

    /* ─── Hero (governing thought, navy bg) ─── */
    .hero {{
        background: linear-gradient(135deg, {NAVY} 0%, {BIRU_PRIMER} 100%);
        color: {PUTIH};
        padding: 28px 36px;
        border-radius: 10px;
        margin-bottom: 20px;
    }}
    .hero .kicker {{
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: {AKSEN};
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .hero h1 {{
        color: {PUTIH} !important;
        font-size: 26px;
        font-weight: 700;
        margin: 0 0 8px 0;
        line-height: 1.25;
    }}
    .hero .gov {{
        font-size: 15px;
        color: {PUTIH};
        opacity: 0.92;
        line-height: 1.5;
        border-top: 1px solid {AKSEN};
        padding-top: 10px;
        margin-top: 8px;
    }}

    /* ─── Section header (action title H2) ─── */
    .section-title {{
        color: {NAVY};
        font-family: 'Lato', sans-serif;
        font-size: 20px;
        font-weight: 700;
        padding: 10px 0 8px 0;
        border-bottom: 2px solid {AKSEN};
        margin-top: 24px;
        margin-bottom: 12px;
        line-height: 1.3;
    }}
    .section-subtitle {{
        color: {ABU_GELAP};
        font-size: 12px;
        font-style: italic;
        margin-top: -6px;
        margin-bottom: 12px;
    }}

    /* ─── KPI tiles (rule of 3, navy) ─── */
    .kpi-tile {{
        background: {NAVY};
        color: {PUTIH};
        border-radius: 8px;
        padding: 18px 20px;
        text-align: center;
        height: 100%;
        border-top: 3px solid {AKSEN};
    }}
    .kpi-tile .label {{
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {AKSEN};
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .kpi-tile .value {{
        font-family: 'Lato', sans-serif;
        font-size: 30px;
        font-weight: 900;
        line-height: 1.1;
        margin: 4px 0;
    }}
    .kpi-tile .so-what {{
        font-size: 11px;
        color: {PUTIH};
        opacity: 0.75;
        margin-top: 6px;
        line-height: 1.3;
    }}

    /* ─── Callout boxes ─── */
    .callout-insight {{
        background: {NAVY};
        color: {PUTIH};
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 13px;
        line-height: 1.5;
    }}
    .callout-rec {{
        background: {ABU_TERANG};
        color: {TEKS_ISI};
        padding: 14px 18px;
        border-left: 4px solid {NAVY};
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 13px;
        line-height: 1.5;
    }}
    .callout-rec strong {{ color: {NAVY}; }}
    .callout-warn {{
        background: #FEF3C7;
        color: #78350F;
        padding: 12px 16px;
        border-left: 4px solid {PERHATIAN};
        border-radius: 0 6px 6px 0;
        margin: 10px 0;
        font-size: 13px;
    }}

    /* ─── Tabel (BCG style) ─── */
    .dataframe, .dataframe th, .dataframe td {{
        border: none !important;
    }}
    .dataframe thead th {{
        background: {BIRU_PRIMER} !important;
        color: {PUTIH} !important;
        font-weight: 700 !important;
        text-align: center !important;
        padding: 10px 8px !important;
        font-size: 12px !important;
    }}
    .dataframe tbody tr:nth-child(even) {{
        background: {ZEBRA_STRIP};
    }}
    .dataframe tbody td {{
        font-size: 12px;
        padding: 8px !important;
    }}

    /* ─── Tombol ─── */
    .stButton > button, .stDownloadButton > button {{
        background: {NAVY} !important;
        color: {PUTIH} !important;
        font-family: 'Lato', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 6px !important;
        width: 100%;
        transition: background 0.2s;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: {BIRU_PRIMER} !important;
        color: {PUTIH} !important;
    }}

    /* ─── Sidebar ─── */
    section[data-testid="stSidebar"] {{
        background: #FAFBFC;
    }}
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {NAVY};
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid {AKSEN};
        padding-bottom: 4px;
    }}

    /* ─── Tabs ─── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {ABU_GELAP};
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 0;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        color: {NAVY} !important;
        border-bottom: 3px solid {NAVY} !important;
    }}

    /* ─── Source line (bawah chart) ─── */
    .chart-source {{
        font-size: 11px;
        font-style: italic;
        color: {ABU_GELAP};
        text-align: left;
        margin-top: -8px;
        margin-bottom: 16px;
    }}

    /* ─── Metric (st.metric secondary) ─── */
    [data-testid="stMetric"] {{
        background: {ABU_TERANG};
        padding: 10px 14px;
        border-radius: 6px;
        border-left: 3px solid {AKSEN};
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 11px;
        color: {ABU_GELAP};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    [data-testid="stMetricValue"] {{
        color: {NAVY};
        font-family: 'Lato', sans-serif;
        font-weight: 700;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════
# Session State Init
# ══════════════════════════════════════════════════════════════════════

if "result" not in st.session_state:
    st.session_state.result = None
if "input_data" not in st.session_state:
    st.session_state.input_data = None


# ══════════════════════════════════════════════════════════════════════
# Sidebar — Input Parameters
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/oil-industry.png", width=48)
    st.markdown("## ⛽ Energi Economic")
    st.markdown("*PSC Financial Model v0.1*")
    st.divider()

    # ── Project metadata ──
    st.markdown("### 📋 Project Info")
    project_name = st.text_input("Project Name", value="Mini Refinery Study")
    project_client = st.text_input("Client", value="PT Reka Elang Inovasi")
    project_horizon = st.slider("Model Horizon (years)", 3, 20, 10)
    start_year = st.number_input("Start Year", 2020, 2040, 2026)

    st.divider()

    # ── Production ──
    st.markdown("### 🛢️ Production")
    prod_preset = st.selectbox(
        "Profile Preset",
        ["Plateau + Decline", "Custom Input", "Exponential Decline"],
    )
    if prod_preset == "Plateau + Decline":
        plateau_rate = st.number_input("Plateau Rate (BOPD)", 100, 200_000, 10_000, step=100)
        plateau_years = st.slider("Plateau Duration (years)", 1, project_horizon - 1, 3)
        decline_rate_pct = st.slider("Annual Decline Rate (%)", 1.0, 50.0, 10.0) / 100
    elif prod_preset == "Exponential Decline":
        initial_rate = st.number_input("Initial Rate (BOPD)", 100, 200_000, 15_000, step=100)
        decline_rate_pct = st.slider("Annual Decline Rate (%)", 1.0, 50.0, 15.0) / 100
        plateau_years = 0
        plateau_rate = 0
    else:
        st.caption("Custom rates per year (edit in table below)")

    st.divider()

    # ── Price ──
    st.markdown("### 💰 Oil Price")
    oil_price = st.number_input("ICP Oil Price (USD/bbl)", 30.0, 150.0, 75.0, step=1.0)
    price_esc = st.slider("Annual Escalation (%)", 0.0, 5.0, 2.0) / 100

    st.divider()

    # ── Capex ──
    st.markdown("### 🏗️ Capital Expenditure")
    total_capex_mm = st.number_input("Total Capex (Million USD)", 1.0, 5000.0, 80.0, step=1.0)
    # Clamp max to project_horizon to avoid IndexError (capex year outside model years)
    capex_spread = st.slider(
        "Capex spread over first N years",
        1,
        max(1, min(5, project_horizon)),
        min(3, project_horizon),
        help=f"Maksimal = horizon proyek ({project_horizon} tahun)",
    )
    cr_life = st.slider("CR Depreciation Life (years)", 3, 20, 10)

    st.divider()

    # ── Opex ──
    st.markdown("### 🔧 Operating Cost")
    opex_per_bbl = st.number_input("Opex (USD/bbl)", 1.0, 50.0, 8.0, step=0.5)

    st.divider()

    # ── PSC Fiscal Terms ──
    st.markdown("### 📜 PSC Fiscal Terms")
    ftp = st.slider("FTP (%)", 5, 30, 20) / 100
    ftp_split = st.slider("FTP Contractor Split (%)", 30, 70, 50) / 100
    cr_ceiling = st.slider("Cost Recovery Ceiling (%)", 50, 100, 80) / 100
    contractor_split = st.slider("Contractor Equity Split (%)", 10, 50, 35) / 100
    inv_credit = st.slider("Investment Credit (%)", 0, 20, 5) / 100
    tax_rate = st.slider("Tax Rate — PPh Badan (%)", 10, 40, 22) / 100
    dmo_pct = st.slider("DMO (%)", 0, 30, 25) / 100
    discount_rate = st.slider("Discount Rate / WACC (%)", 5, 20, 10) / 100

    st.divider()

    # ── Run Button ──
    run = st.button("🚀 Run Financial Model", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# Helper: build PSCInput from session state
# ══════════════════════════════════════════════════════════════════════


def build_input() -> PSCInput:
    years = list(range(start_year, start_year + project_horizon))
    n = len(years)

    # Production
    if prod_preset == "Plateau + Decline":
        rates = [plateau_rate] * plateau_years
        decline_years = n - plateau_years
        for t in range(decline_years):
            rate = plateau_rate * math.exp(-decline_rate_pct * t)
            rates.append(round(rate))
    elif prod_preset == "Exponential Decline":
        rates = [round(initial_rate * math.exp(-decline_rate_pct * t)) for t in range(n)]
    else:
        # Custom — default to a simple profile
        rates = [5000, 8000, 10000, 10000, 10000, 9000, 8000, 7000, 6000, 5000][:n]

    production = ProductionProfile(
        vectors=ProductionProfileVectors(years=years, rates_bopd=rates),
        source_description=f"{prod_preset} profile",
    )

    # Price
    price = PriceAssumption(
        oil_price_usd_bbl=oil_price,
        escalation_pct=price_esc,
    )

    # Capex (clamp spread ke horizon untuk safety, mencegah IndexError)
    total_capex = total_capex_mm * 1_000_000
    spread = min(capex_spread, n)  # Safety clamp — tidak boleh melebihi horizon
    annual_capex = total_capex / spread
    capex_items = []
    categories = ["Engineering", "Equipment", "Construction", "Pipeline", "Infrastructure"]
    for i in range(spread):
        cat = categories[i % len(categories)] if spread <= len(categories) else f"Phase {i+1}"
        capex_items.append(
            CapexScheduleItem(
                category=cat,
                cost_usd=annual_capex,
                year_incurred=years[i],
                depreciation_life_years=cr_life,
            )
        )
    capex = CapexSchedule(
        items=capex_items,
        description=f"Total capex ${total_capex_mm:.0f}M spread over {capex_spread} years",
        contingency_pct=10.0,
    )

    # Opex
    opex_per_year_total = [opex_per_bbl * rate * 365 for rate in rates]
    opex = OpexSchedule(
        years=years,
        categories={
            OpexCategory.PRODUCTION: opex_per_year_total,
        },
    )

    # PSC Input
    return PSCInput(
        name=project_name,
        client=project_client,
        production=production,
        price=price,
        capex=capex,
        opex=opex,
        ftp_pct=ftp,
        ftp_contractor_split=ftp_split,
        cost_recovery_ceiling_pct=cr_ceiling,
        cost_recovery_depreciation_life_years=float(cr_life),
        contractor_split_after_cr=contractor_split,
        investment_credit_pct=inv_credit,
        tax_rate_pct=tax_rate,
        discount_rate_pct=discount_rate,
        dmo_pct=dmo_pct,
        dmo_fee_usd_bbl=0.50,
    )


# ══════════════════════════════════════════════════════════════════════
# Main Page
# ══════════════════════════════════════════════════════════════════════

# ── Hero (always visible) ──
if st.session_state.result is not None:
    res = st.session_state.result
    inp = st.session_state.input_data

    irr_str = f">{999}%" if res.irr_contractor == float("inf") else f"{res.irr_contractor:.1%}"
    pb_str = "Immediate" if res.payback_period_years == 0.0 else (
        f"{res.payback_period_years:.1f} yrs" if res.payback_period_years else "N/A"
    )
    is_positive = res.npv_contractor > 0
    decision = "layak diteruskan ke FEED" if is_positive else "perlu renegosiasi fiscal term"
    gov_color = POSITIF if is_positive else NEGATIF

    hero_html = f"""
    <div class="hero">
        <div class="kicker">PSC COST RECOVERY — FINANCIAL MODEL</div>
        <h1>{res.project_name}</h1>
        <div class="gov">
            <strong>Governing Thought:</strong> Project NPV
            <span style="color:{gov_color}; font-weight:700;">${res.npv_contractor:,.0f}</span>
            (IRR {irr_str}), government take {res.government_take_pct_of_gross:.1f}% dari gross revenue
            &mdash; <strong>{decision}.</strong>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
else:
    # Welcome hero
    st.markdown(
        f"""
        <div class="hero">
            <div class="kicker">ENERGI ECONOMIC SOFTWARE · V0.1</div>
            <h1>PSC Financial Modeling &mdash; Made Simple</h1>
            <div class="gov">
                Hitung NPV, IRR, dan government take untuk proyek hulu migas PSC
                Cost Recovery. Atur parameter di sidebar kiri, lalu klik
                <strong>Run Financial Model</strong>. Export hasil ke Excel atau PDF.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if run:
    with st.spinner("Menjalankan fiscal engine..."):
        try:
            inp = build_input()
            st.session_state.input_data = inp
            engine = PSCCostRecovery(inp)
            result = engine.calculate()
            st.session_state.result = result
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.result = None

# ══════════════════════════════════════════════════════════════════════
# Show Results
# ══════════════════════════════════════════════════════════════════════

if st.session_state.result is not None:
    res = st.session_state.result
    inp = st.session_state.input_data

    # ── KPI Tiles (Rule of 3 — NPV / IRR / Payback) ──
    st.markdown('<div class="section-title">Key Economic Indicators</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Tiga metrik utama menentukan kelayakan investasi.</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)

    with k1:
        npv_color = POSITIF if is_positive else NEGATIF
        npv_sowhat = "Project create value" if is_positive else "Project destroy value"
        st.markdown(
            f"""<div class="kpi-tile">
            <div class="label">NPV (Contractor)</div>
            <div class="value" style="color:{npv_color};">${res.npv_contractor:,.0f}</div>
            <div class="so-what">{npv_sowhat}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k2:
        irr_sowhat = "Above WACC" if (res.irr_contractor != float("inf") and res.irr_contractor > res.discount_rate_pct) else "Cost recovered simultaneously"
        st.markdown(
            f"""<div class="kpi-tile">
            <div class="label">IRR</div>
            <div class="value">{irr_str}</div>
            <div class="so-what">{irr_sowhat}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k3:
        pb_sowhat = "Capital returned fast" if (res.payback_period_years is not None and res.payback_period_years <= 3) else "Verify risk exposure"
        st.markdown(
            f"""<div class="kpi-tile">
            <div class="label">Payback Period</div>
            <div class="value">{pb_str}</div>
            <div class="so-what">{pb_sowhat}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Secondary metrics (3 columns) ──
    k4, k5, k6 = st.columns(3)
    with k4:
        st.metric("Government Take", f"{res.government_take_pct_of_gross:.1f}%")
    with k5:
        st.metric("Total Gross Revenue", f"${res.total_gross_revenue:,.0f}")
    with k6:
        st.metric("Cum. Production", f"{res.cumulative_production_mmboe:.2f} MMBOE")

    # ── Recommendation callout ──
    rec_text = (
        "Lanjutkan ke FEED phase dengan fokus pada optimasi cost recovery "
        "dan struktur fiscal term bersama SKK Migas."
        if is_positive
        else "Tinjau ulang struktur biaya dan asumsi fiscal sebelum melanjutkan. "
             "NPV negatif mengindikasikan return di bawah hurdle rate."
    )
    st.markdown(
        f'<div class="callout-rec"><strong>REKOMENDASI:</strong> {rec_text}</div>',
        unsafe_allow_html=True,
    )

    if res.warnings:
        for w in res.warnings:
            st.markdown(f'<div class="callout-warn">⚠ {w}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Cashflow", "📈 Charts", "📋 Fiscal Detail", "⬇️ Export"])

    with tab1:
        st.markdown(
            '<div class="section-title">Contractor Net Cashflow Anjlok di Tahun Akhir Akibat Decline Produksi</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-subtitle">Waterfall per tahun &mdash; gross revenue dipotong FTP, cost recovery, tax, hingga net cashflow.</div>',
            unsafe_allow_html=True,
        )

        # Cashflow table
        cf_data = {
            "Year": res.contractor.years,
            "Gross Revenue": [f"${x:,.0f}" for x in res.contractor.gross_revenue],
            "FTP Share": [f"${x:,.0f}" for x in res.contractor.ftp_share],
            "Cost Recovery": [f"${x:,.0f}" for x in res.contractor.cost_recovery_received],
            "Equity Split": [f"${x:,.0f}" for x in res.contractor.equity_split_share],
            "Taxable Income": [f"${x:,.0f}" for x in res.contractor.taxable_income],
            "Tax Paid": [f"${x:,.0f}" for x in res.contractor.tax_paid],
            "Net Cashflow": [f"${x:,.0f}" for x in res.contractor.net_cashflow],
        }
        df_cf = pd.DataFrame(cf_data).set_index("Year")
        st.dataframe(df_cf, use_container_width=True)

    with tab2:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(
                '<div class="section-title">Cashflow Bridge: Gross Revenue Menuju Net Cashflow</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-subtitle">Tahun terakhir model &mdash; visualisasi pemotongan fiscal.</div>',
                unsafe_allow_html=True,
            )
            # Waterfall chart (single year breakdown — last year)
            last = len(res.contractor.years) - 1
            yr = res.contractor.years[last]
            components = {
                "Gross Revenue": res.contractor.gross_revenue[last],
                "FTP (to Gov)": -res.government.ftp_share[last],
                "Cost Recovery": res.contractor.cost_recovery_received[last],
                "Equity Split": res.contractor.equity_split_share[last],
                "Tax Paid": -res.contractor.tax_paid[last],
                "Net Cashflow": res.contractor.net_cashflow[last],
            }
            fig_wf = waterfall_chart(
                components,
                title=f"Cashflow Bridge — Year {yr}",
            )
            st.pyplot(fig_wf)
            plt.close(fig_wf)
            st.markdown(
                '<div class="chart-source">Sumber: Hasil perhitungan PSC engine. '
                f'Year {yr}, base case.</div>',
                unsafe_allow_html=True,
            )

        with col_right:
            st.markdown(
                '<div class="section-title">Tren Cashflow 10 Tahun: Decline Produksi Tekan Net Cashflow</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-subtitle">Net cashflow (navy) vs gross revenue (abu) vs taxable income.</div>',
                unsafe_allow_html=True,
            )
            # Trend chart: Net cashflow vs Gross Revenue
            fig_tr = trend_chart(
                years=res.contractor.years,
                series={
                    "Net Cashflow": res.contractor.net_cashflow,
                    "Gross Revenue": res.contractor.gross_revenue,
                    "Taxable Income": res.contractor.taxable_income,
                },
                title="Contractor Cashflow Trend",
                highlight_idx=0,
            )
            st.pyplot(fig_tr)
            plt.close(fig_tr)
            st.markdown(
                '<div class="chart-source">Sumber: Hasil perhitungan PSC engine, '
                f'{min(res.contractor.years)}&ndash;{max(res.contractor.years)}.</div>',
                unsafe_allow_html=True,
            )

        # Cost breakdown bar
        if inp.opex:
            st.markdown(
                '<div class="section-title">Opex Terbesar: Production Dominate Total Operating Cost</div>',
                unsafe_allow_html=True,
            )
            cats = [c.value for c in inp.opex.categories.keys()]
            totals = [sum(inp.opex.categories[k]) for k in inp.opex.categories]
            fig_bar = bar_horizontal_sorted(
                categories=cats,
                values=totals,
                title="Opex Breakdown by Category (Total)",
            )
            st.pyplot(fig_bar)
            plt.close(fig_bar)
            st.markdown(
                '<div class="chart-source">Sumber: Input opex per kategori, total nominal.</div>',
                unsafe_allow_html=True,
            )

    with tab3:
        st.markdown(
            '<div class="section-title">Fiscal Terms & Key Metrics &mdash; Snapshot Asumsi vs Hasil</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(
                '<div class="callout-insight"><strong>FISCAL TERMS (INPUT)</strong></div>',
                unsafe_allow_html=True,
            )
            st.write(f"- FTP: {res.ftp_pct:.0%}")
            st.write(f"- Contractor Split (after CR): {res.contractor_split_after_cr:.0%}")
            st.write(f"- Cost Recovery Ceiling: {res.cost_recovery_ceiling_pct:.0%}")
            st.write(f"- Tax Rate: {res.tax_rate_pct:.0%}")
            st.write(f"- Discount Rate: {res.discount_rate_pct:.1%}")

        with col_b:
            st.markdown("**Results**")
            st.write(f"- NPV: ${res.npv_contractor:,.0f}")
            st.write(f"- IRR: {irr_str}")
            st.write(f"- Profitability Index: {res.profitability_index:.2f}")
            st.write(f"- Government Take: {res.government_take_pct_of_gross:.1f}%")
            st.write(f"- Total Cost Recovery: ${res.total_cost_recovery:,.0f}")

    with tab4:
        st.markdown(
            '<div class="section-title">Export &mdash; Excel & PDF dengan Styling Konsultan</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-subtitle">Kedua file siap untuk investment committee / pitch ke stakeholder.</div>',
            unsafe_allow_html=True,
        )

        col_xl, col_pdf = st.columns(2)

        with col_xl:
            st.markdown(
                '<div class="callout-insight"><strong>📗 EXCEL REPORT</strong><br>'
                '4 sheets: Dashboard, Cashflow, Fiscal Detail, Economics. '
                'Header navy, KPI tiles, conditional formatting.</div>',
                unsafe_allow_html=True,
            )

            # Generate Excel in memory
            gen_xl = ExcelReportGenerator(res)
            gen_xl.build()
            xl_bytes = gen_xl.to_bytes()

            st.download_button(
                label="⬇ Download Excel (.xlsx)",
                data=xl_bytes,
                file_name=f"{project_name.replace(' ', '_')}_financial_model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_pdf:
            st.markdown(
                '<div class="callout-insight"><strong>📕 PDF REPORT</strong><br>'
                'Investment memo: Cover navy, Executive Summary (SCR), '
                'Fiscal Highlights, Recommendation box.</div>',
                unsafe_allow_html=True,
            )

            gen_pdf = PDFReportGenerator(res)
            gen_pdf.build()
            pdf_bytes = gen_pdf.to_bytes()

            st.download_button(
                label="⬇ Download PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"{project_name.replace(' ', '_')}_investment_memo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

elif not run:
    # Welcome screen (setelah hero)
    st.markdown(
        '<div class="section-title">Mulai di Sini</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="callout-rec"><strong>LANGKAH 1:</strong> '
        'Atur parameter di sidebar kiri (◀ kiri layar), lalu klik '
        '<strong>Run Financial Model</strong>.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    ### Apa yang bisa dilakukan?
    1. **Input data proyek** — produksi, capex, opex, harga minyak
    2. **Konfigurasi fiscal term PSC** — FTP, cost recovery, split, DMO, pajak
    3. **Lihat hasil** — NPV, IRR, payback, cashflow waterfall
    4. **Export** — Excel (BCG style) & PDF (investment memo)
    """)
