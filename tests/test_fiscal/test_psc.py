"""Integration test for PSC Cost Recovery engine."""

from __future__ import annotations

import pytest

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


def _build_base_input() -> PSCInput:
    """Helper: build a minimal valid PSCInput."""
    return PSCInput(
        name="Test PSC",
        production=ProductionProfile(
            vectors=ProductionProfileVectors(
                years=[2026, 2027, 2028, 2029, 2030],
                rates_bopd=[5000, 8000, 10000, 8500, 6000],
            ),
        ),
        price=PriceAssumption(oil_price_usd_bbl=75.0),
        capex=CapexSchedule(
            items=[
                CapexScheduleItem(
                    category="Drilling",
                    cost_usd=5_000_000,
                    year_incurred=2026,
                    depreciation_life_years=5,
                ),
            ],
            contingency_pct=10.0,
        ),
        opex=OpexSchedule(
            years=[2026, 2027, 2028, 2029, 2030],
            categories={
                OpexCategory.PRODUCTION: [1.0, 1.5, 1.8, 1.6, 1.3],
            },
        ),
        ftp_pct=0.20,
        contractor_split_after_cr=0.35,
        cost_recovery_ceiling_pct=0.80,
        tax_rate_pct=0.22,
        discount_rate_pct=0.10,
    )


class TestPSCCostRecoveryBasic:
    """Smoke tests — does the engine run without errors?"""

    def test_calculate_returns_result(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        assert result is not None
        assert result.project_name == "Test PSC"
        assert len(result.contractor.years) == 5

    def test_contractor_breakdown_has_correct_length(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        assert len(result.contractor.net_cashflow) == 5
        assert len(result.government.net_cashflow) == 5

    def test_government_take_positive(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        assert result.government_take_total > 0
        assert result.government_take_pct_of_gross > 0

    def test_no_error_on_zero_production(self):
        """Edge case: zero production should not crash."""
        inp = PSCInput(
            name="Zero Production",
            production=ProductionProfile(
                vectors=ProductionProfileVectors(
                    years=[2026, 2027],
                    rates_bopd=[0.0, 0.0],
                ),
            ),
            price=PriceAssumption(oil_price_usd_bbl=75.0),
            ftp_pct=0.20,
            contractor_split_after_cr=0.35,
            cost_recovery_ceiling_pct=0.80,
            tax_rate_pct=0.22,
            discount_rate_pct=0.10,
        )
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        assert result.total_gross_revenue == 0.0


class TestPSCCostRecoveryFiscalLogic:
    """Logical consistency checks on the fiscal waterfall."""

    def test_ftp_splits_sum_to_ftp_total(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        for i in range(5):
            ftp_c = result.contractor.ftp_share[i]
            ftp_g = result.government.ftp_share[i]
            gr = result.contractor.gross_revenue[i]
            expected_ftp = 0.20 * gr
            assert ftp_c + ftp_g == pytest.approx(expected_ftp, rel=1e-6)

    def test_contractor_gov_equity_sums_match(self):
        engine = PSCCostRecovery(_build_base_input())
        inp = _build_base_input()
        result = engine.calculate()
        for i in range(5):
            c = result.contractor.equity_split_share[i]
            g = result.government.equity_split_share[i]
            # Ratio should hold
            if c + g > 0:
                ratio = c / (c + g) if (c + g) > 0 else 0.5
                assert ratio == pytest.approx(inp.contractor_split_after_cr, rel=0.01)

    def test_cost_recovery_received_non_negative(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        for cr in result.contractor.cost_recovery_received:
            assert cr >= 0

    def test_tax_paid_positive_when_taxable_positive(self):
        engine = PSCCostRecovery(_build_base_input())
        result = engine.calculate()
        for ti, tax in zip(result.contractor.taxable_income, result.contractor.tax_paid):
            if ti > 0:
                assert tax > 0

    def test_revenue_sums_to_production_x_price(self):
        inp = _build_base_input()
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        # Gross revenue per year = annual production bbl × price per bbl
        annual_prod = inp.production.annual_production_bbl
        price_arr = engine._build_price_array()
        for i in range(5):
            expected = annual_prod[i] * price_arr[i]
            assert result.contractor.gross_revenue[i] == pytest.approx(expected, rel=1e-6)


class TestPSCCostRecoveryEdgeCases:
    """Edge cases and boundary conditions."""

    def test_ftp_zero(self):
        inp = _build_base_input()
        inp.ftp_pct = 0.0
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        # All FTP should be zero
        assert sum(result.contractor.ftp_share) == 0.0
        assert sum(result.government.ftp_share) == 0.0

    def test_no_cost_recovery_ceiling(self):
        """CR ceiling of 1.0 means all costs recovered immediately."""
        inp = _build_base_input()
        inp.cost_recovery_ceiling_pct = 1.0
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        assert result.unrecovered_costs_at_end == 0.0

    def test_tax_rate_zero(self):
        inp = _build_base_input()
        inp.tax_rate_pct = 0.0
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        for tax in result.contractor.tax_paid:
            assert tax == 0.0

    def test_short_horizon(self):
        """1-year horizon should work."""
        inp = PSCInput(
            name="1-Year PSC",
            production=ProductionProfile(
                vectors=ProductionProfileVectors(
                    years=[2026], rates_bopd=[5000]
                ),
            ),
            price=PriceAssumption(oil_price_usd_bbl=75.0),
            ftp_pct=0.20,
            contractor_split_after_cr=0.35,
            cost_recovery_ceiling_pct=0.80,
            tax_rate_pct=0.22,
            discount_rate_pct=0.10,
        )
        engine = PSCCostRecovery(inp)
        result = engine.calculate()
        assert len(result.contractor.years) == 1
