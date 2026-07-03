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
import tempfile
from pathlib import Path
import sys

# Pastikan src/ ada di path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from fiscal_model.schemas.inputs import (
    PSCInput,
    ProductionProfile,
    ProductionProfileVectors,
    PriceAssumption,
    CapexSchedule,
    CapexScheduleItem,
    OpexSchedule,
    OpexCategory,
)
from fiscal_model.fiscal.psc import PSCCostRecovery
from fiscal_model.economics.metrics import npv, irr
from fiscal_model.outputs.excel import ExcelReportGenerator
from fiscal_model.outputs.pdf import PDFReportGenerator
from fiscal_model.outputs.charts import (
    waterfall_chart,
    trend_chart,
    tornado_chart,
    bar_horizontal_sorted,
    figure_to_bytes,
)
from fiscal_model.outputs.styling import (
    NAVY,
    BIRU_PRIMER,
    PUTIH,
    POSITIF,
    NEGATIF,
    NETRAL,
    ABU_GELAP,
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
# Custom CSS (kosmetik-dokumen palette)
# ══════════════════════════════════════════════════════════════════════

st.markdown(
    f"""
<style>
    .main-header {{
        color: {NAVY};
        font-size: 28px;
        font-weight: 700;
        border-bottom: 3px solid {BIRU_PRIMER};
        padding-bottom: 10px;
        margin-bottom: 20px;
    }}
    .kpi-box {{
        background: {NAVY};
        color: {PUTIH};
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin: 5px;
    }}
    .kpi-label {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        margin: 5px 0;
    }}
    .kpi-positive {{ color: {POSITIF}; }}
    .kpi-negative {{ color: {NEGATIF}; }}
    .gov-thought {{
        background: #F0F4FF;
        border-left: 4px solid {NAVY};
        padding: 15px 20px;
        margin: 15px 0;
        font-size: 14px;
        color: #1F2937;
        border-radius: 0 8px 8px 0;
    }}
    .section-header {{
        color: {NAVY};
        font-size: 18px;
        font-weight: 600;
        margin-top: 20px;
        padding: 8px 0;
        border-bottom: 2px solid #E9EAEC;
    }}
    .stButton > button {{
        background: {NAVY};
        color: {PUTIH};
        font-weight: 600;
        border: none;
        padding: 10px 30px;
        border-radius: 6px;
        width: 100%;
    }}
    .stButton > button:hover {{
        background: {BIRU_PRIMER};
    }}
    .download-btn {{
        margin: 10px 0;
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
    capex_spread = st.slider("Capex spread over first N years", 1, 5, 3)
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

    # Capex
    total_capex = total_capex_mm * 1_000_000
    annual_capex = total_capex / capex_spread
    capex_items = []
    categories = ["Engineering", "Equipment", "Construction", "Pipeline", "Infrastructure"]
    for i in range(capex_spread):
        cat = categories[i % len(categories)] if capex_spread <= len(categories) else f"Phase {i+1}"
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

st.markdown('<div class="main-header">⛽ Energi Economic Software — PSC Financial Model</div>', unsafe_allow_html=True)

if run:
    with st.spinner("Running fiscal engine..."):
        try:
            inp = build_input()
            st.session_state.input_data = inp
            engine = PSCCostRecovery(inp)
            result = engine.calculate()
            st.session_state.result = result
            st.success("Model calculation complete!")
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.result = None

# ══════════════════════════════════════════════════════════════════════
# Show Results
# ══════════════════════════════════════════════════════════════════════

if st.session_state.result is not None:
    res = st.session_state.result
    inp = st.session_state.input_data

    # ── Governing Thought ──
    gov = (
        f"<b>Governing Thought:</b> Project NPV "
        f"<span style='color:{POSITIF if res.npv_contractor > 0 else NEGATIF}'>"
        f"${res.npv_contractor:,.0f}</span> "
        f"(IRR {'>' + '999%' if res.irr_contractor == float('inf') else f'{res.irr_contractor:.1%}'}), "
        f"Government take {res.government_take_pct_of_gross:.1f}%. "
        + ("Project layak secara ekonomi." if res.npv_contractor > 0 else "Perlu optimasi fiscal term.")
    )
    st.markdown(f'<div class="gov-thought">{gov}</div>', unsafe_allow_html=True)

    # ── KPI Tiles ──
    k1, k2, k3 = st.columns(3)

    pb_str = "Immediate" if res.payback_period_years == 0.0 else (
        f"{res.payback_period_years:.1f} yrs" if res.payback_period_years else "N/A"
    )
    irr_str = f">{999}%" if res.irr_contractor == float("inf") else f"{res.irr_contractor:.1%}"

    with k1:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-label">NPV (Net Present Value)</div>
            <div class="kpi-value">${res.npv_contractor:,.0f}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-label">IRR</div>
            <div class="kpi-value">{irr_str}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""<div class="kpi-box">
            <div class="kpi-label">Payback Period</div>
            <div class="kpi-value">{pb_str}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Secondary KPIs ──
    k4, k5, k6 = st.columns(3)
    with k4:
        st.metric("Government Take", f"{res.government_take_pct_of_gross:.1f}%")
    with k5:
        st.metric("Total Gross Revenue", f"${res.total_gross_revenue:,.0f}")
    with k6:
        st.metric("Cum. Production", f"{res.cumulative_production_mmboe:.2f} MMBOE")

    st.divider()

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Cashflow", "📈 Charts", "📋 Fiscal Detail", "⬇️ Export"])

    with tab1:
        st.markdown('<div class="section-header">Annual Cashflow Waterfall (Contractor)</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="section-header">Financial Charts</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            # Waterfall chart (single year breakdown — last year)
            last = len(res.contractor.years) - 1
            yr = res.contractor.years[last]
            components = {
                "Gross Revenue": res.contractor.gross_revenue[last],
                f"FTP (to Gov)": -res.government.ftp_share[last],
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

        with col_right:
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

        # Cost breakdown bar
        if inp.opex:
            cats = [c.value for c in inp.opex.categories.keys()]
            totals = [sum(inp.opex.categories[k]) for k in inp.opex.categories]
            fig_bar = bar_horizontal_sorted(
                categories=cats,
                values=totals,
                title="Opex Breakdown by Category (Total)",
            )
            st.pyplot(fig_bar)
            plt.close(fig_bar)

    with tab3:
        st.markdown('<div class="section-header">Fiscal Parameters & Key Metrics</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Fiscal Terms**")
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

        if res.warnings:
            st.warning("\n".join(res.warnings))

    with tab4:
        st.markdown('<div class="section-header">Export Reports</div>', unsafe_allow_html=True)

        col_xl, col_pdf = st.columns(2)

        with col_xl:
            st.markdown("### 📗 Excel Report")
            st.caption("BCG/McKinsey styled — 4 sheets (Dashboard, Cashflow, Fiscal Detail, Economics)")

            # Generate Excel in memory
            gen_xl = ExcelReportGenerator(res)
            gen_xl.build()
            xl_bytes = gen_xl.to_bytes()

            st.download_button(
                label="⬇ Download Excel Report (.xlsx)",
                data=xl_bytes,
                file_name=f"{project_name.replace(' ', '_')}_financial_model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_pdf:
            st.markdown("### 📕 PDF Report")
            st.caption("Investment memo — Cover, Executive Summary, Fiscal Highlights, Recommendation")

            gen_pdf = PDFReportGenerator(res)
            gen_pdf.build()
            pdf_bytes = gen_pdf.to_bytes()

            st.download_button(
                label="⬇ Download PDF Report (.pdf)",
                data=pdf_bytes,
                file_name=f"{project_name.replace(' ', '_')}_investment_memo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

elif not run:
    # Welcome screen
    st.info("👈 **Atur parameter di sidebar**, lalu klik **Run Financial Model**.")
    st.markdown("""
    ### Apa yang bisa dilakukan?
    1. **Input data proyek** — produksi, capex, opex, harga minyak
    2. **Konfigurasi fiscal term PSC** — FTP, cost recovery, split, DMO, pajak
    3. **Lihat hasil** — NPV, IRR, payback, cashflow waterfall
    4. **Export** — Excel (BCG style) & PDF (investment memo)
    """)
