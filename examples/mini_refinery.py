"""
Example: Mini Refinery PSC Financial Model.

A realistic 10-year model simulating a 10,000 BOPD mini refinery
under Indonesia's PSC Cost Recovery fiscal regime.

Run::

    python examples/mini_refinery.py
"""

from __future__ import annotations

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
from fiscal_model.economics.metrics import npv, irr, payback_period
from fiscal_model.outputs.excel import ExcelReportGenerator
from fiscal_model.outputs.pdf import PDFReportGenerator


def main():
    YEARS = list(range(2026, 2036))  # 10-year horizon
    N = len(YEARS)

    # Production: ramp-up → plateau → decline
    rates = [3000, 7000, 10000, 10000, 10000, 9500, 8500, 7500, 6000, 5000]

    production = ProductionProfile(
        vectors=ProductionProfileVectors(years=YEARS, rates_bopd=rates),
        source_description="10,000 BOPD Mini Refinery — 3y ramp-up, 3y plateau, decline",
    )

    # Oil price: $70/bbl ICP with 2% annual escalation
    price = PriceAssumption(oil_price_usd_bbl=70.0, escalation_pct=0.02)

    # Capex: $80M spread over first 3 years
    capex = CapexSchedule(
        items=[
            CapexScheduleItem(category="FEED & Engineering", cost_usd=5_000_000, year_incurred=2026, depreciation_life_years=10),
            CapexScheduleItem(category="Process Units", cost_usd=25_000_000, year_incurred=2027, depreciation_life_years=15),
            CapexScheduleItem(category="Utilities", cost_usd=15_000_000, year_incurred=2027, depreciation_life_years=10),
            CapexScheduleItem(category="Storage Tanks", cost_usd=10_000_000, year_incurred=2027, depreciation_life_years=15),
            CapexScheduleItem(category="Pipeline & Offsite", cost_usd=15_000_000, year_incurred=2028, depreciation_life_years=15),
            CapexScheduleItem(category="EPC Contingency", cost_usd=10_000_000, year_incurred=2028, depreciation_life_years=10),
        ],
        description="10,000 BOPD Mini Refinery — EPC Package",
        contingency_pct=10.0,
    )

    # Opex: ~$8–12M/year depending on production level
    opex = OpexSchedule(
        years=YEARS,
        categories={
            OpexCategory.PRODUCTION: [2.5, 4.0, 5.5, 5.5, 5.5, 5.2, 4.8, 4.2, 3.5, 3.0],
            OpexCategory.MAINTENANCE: [1.0, 1.5, 2.0, 2.0, 2.0, 2.2, 2.5, 2.8, 3.0, 3.0],
            OpexCategory.LABOR: [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
            OpexCategory.LOGISTICS: [0.8, 1.2, 1.5, 1.5, 1.5, 1.4, 1.3, 1.2, 1.0, 0.8],
            OpexCategory.HSE: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
        },
    )

    # PSC fiscal terms (Indonesian standard post-2010)
    psc_input = PSCInput(
        name="Mini Refinery — 10,000 BOPD",
        version="2.0",
        client="PT Reka Elang Inovasi (Internal Study)",
        production=production,
        price=price,
        capex=capex,
        opex=opex,
        ftp_pct=0.20,
        ftp_contractor_split=0.50,
        cost_recovery_ceiling_pct=0.80,
        cost_recovery_depreciation_life_years=10.0,
        contractor_split_after_cr=0.35,
        investment_credit_pct=0.05,
        tax_rate_pct=0.22,
        discount_rate_pct=0.10,
        dmo_pct=0.25,
        dmo_fee_usd_bbl=0.50,
        notes="Base case financial model for 10,000 BOPD mini refinery. "
              "Assumes ICP $70/bbl, 2% escalation, standard PSC terms.",
    )

    # Run engine
    engine = PSCCostRecovery(psc_input)
    result = engine.calculate()

    # Print summary
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   MINI REFINERY — FINANCIAL MODEL RESULTS               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"   Horizon:    {min(YEARS)}–{max(YEARS)} ({N} years)")
    print(f"   CapEx:      ${capex.total_including_contingency_usd:,.0f}")
    print(f"   Peak Rate:  {max(rates):,} BOPD")
    print(f"   Cum. Prod:  {result.cumulative_production_mmboe:.2f} MMBOE")
    print(f"   ---")
    print(f"   NPV:        ${result.npv_contractor:,.0f}")
    print(f"   IRR:        {result.irr_contractor:.1%}")
    print(f"   Payback:    {result.payback_period_years:.1f} yrs" if result.payback_period_years else "   Payback: N/A")
    print(f"   PI:         {result.profitability_index:.2f}")
    print(f"   Gov. Take:  {result.government_take_pct_of_gross:.1f}%")
    print(f"   ---")
    print(f"   Total CR:   ${result.total_cost_recovery:,.0f}")
    print(f"   Unrecov:    ${result.unrecovered_costs_at_end:,.0f}")

    if result.warnings:
        print(f"\n   ⚠ Warnings:")
        for w in result.warnings:
            print(f"     - {w}")

    # Generate outputs
    xlsx_path = "mini_refinery_output.xlsx"
    pdf_path = "mini_refinery_output.pdf"

    ExcelReportGenerator(result).build().save(xlsx_path)
    print(f"\n   ✓ Excel: {xlsx_path}")

    PDFReportGenerator(result).build().save(pdf_path)
    print(f"   ✓ PDF:   {pdf_path}")


if __name__ == "__main__":
    main()
