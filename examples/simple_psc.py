"""
Example: Simple PSC Cost Recovery model.

This is the minimal getting-started example — a small oil field
with 5-year horizon to demonstrate the basic API.

Run::

    python examples/simple_psc.py
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
from fiscal_model.outputs.excel import ExcelReportGenerator

# ── 1. Define production profile ─────────────────────────────────────

production = ProductionProfile(
    vectors=ProductionProfileVectors(
        years=[2026, 2027, 2028, 2029, 2030],
        rates_bopd=[5000, 8000, 10000, 8500, 6000],
    ),
    source_description="Small field with peak at year 3",
)

# ── 2. Price assumption ─────────────────────────────────────────────

price = PriceAssumption(
    oil_price_usd_bbl=75.0,
    escalation_pct=0.02,
)

# ── 3. Capital expenditure ──────────────────────────────────────────

capex = CapexSchedule(
    items=[
        CapexScheduleItem(
            category="Drilling",
            cost_usd=5_000_000,
            year_incurred=2026,
            depreciation_life_years=5,
        ),
        CapexScheduleItem(
            category="Facility",
            cost_usd=8_000_000,
            year_incurred=2026,
            depreciation_life_years=10,
        ),
    ],
    description="Initial capex for small field development",
    contingency_pct=10.0,
)

# ── 4. Operating expenditure ────────────────────────────────────────

opex = OpexSchedule(
    years=[2026, 2027, 2028, 2029, 2030],
    categories={
        OpexCategory.PRODUCTION: [1_200_000, 1_500_000, 1_800_000, 1_600_000, 1_300_000],
        OpexCategory.MAINTENANCE: [500_000, 600_000, 700_000, 750_000, 800_000],
        OpexCategory.LABOR: [300_000, 300_000, 300_000, 300_000, 300_000],
        OpexCategory.LOGISTICS: [200_000, 250_000, 300_000, 280_000, 250_000],
    },
)

# ── 5. PSC fiscal terms ─────────────────────────────────────────────

psc_input = PSCInput(
    name="Simple PSC Case Study",
    version="1.0",
    client="PT Reka Elang Inovasi",
    production=production,
    price=price,
    capex=capex,
    opex=opex,
    ftp_pct=0.20,
    ftp_contractor_split=0.50,
    cost_recovery_ceiling_pct=0.80,
    cost_recovery_depreciation_life_years=5.0,
    contractor_split_after_cr=0.35,
    investment_credit_pct=0.05,
    tax_rate_pct=0.22,
    discount_rate_pct=0.10,
    dmo_pct=0.25,
    dmo_fee_usd_bbl=0.50,
    notes="Simple case study for documentation.",
)

# ── 6. Run fiscal engine ────────────────────────────────────────────

engine = PSCCostRecovery(psc_input)
result = engine.calculate()

# ── 7. Print summary ────────────────────────────────────────────────

print("=" * 60)
print(f"  {result.project_name}")
print(f"  Model Horizon: {min(result.model_years)}–{max(result.model_years)}")
print("=" * 60)
print(f"  NPV (Contractor):     ${result.npv_contractor:,.0f}")
print(f"  IRR (Contractor):     {result.irr_contractor:.1%}")
print(f"  Payback Period:       {result.payback_period_years:.1f} yrs" if result.payback_period_years else "  Payback: N/A")
print(f"  Profitability Index:  {result.profitability_index:.2f}")
print(f"  Government Take:      {result.government_take_pct_of_gross:.1f}%")
print(f"  Total Gross Revenue:  ${result.total_gross_revenue:,.0f}")
print(f"  Cum. Production:      {result.cumulative_production_mmboe:.2f} MMBOE")
print("=" * 60)

if result.warnings:
    print("\nWarnings:")
    for w in result.warnings:
        print(f"  ⚠ {w}")

# ── 8. Generate Excel report ────────────────────────────────────────

gen = ExcelReportGenerator(result)
gen.build()
output_path = "simple_psc_output.xlsx"
gen.save(output_path)
print(f"\nExcel report saved to: {output_path}")
