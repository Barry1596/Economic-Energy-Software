"""Unit tests for economic metrics: NPV, IRR, payback, PI, WACC."""

from __future__ import annotations

import math

import pytest

from fiscal_model.economics.metrics import (
    npv,
    irr,
    payback_period,
    profitability_index,
    wacc,
    discount_factor,
)


class TestNPV:
    """Net Present Value tests."""

    def test_single_cashflow(self):
        # $100 at t=0, no discounting → $100
        assert npv([100.0], 0.10) == pytest.approx(100.0)

    def test_flat_cashflow(self):
        # $100/year for 5 years at 10%
        cf = [0.0] + [100.0] * 5  # t=0 zero, then income
        # npf.npv: CF0 + CF1/(1+r) + CF2/(1+r)^2...
        # = 0 + 100/(1.1) + 100/(1.21) + 100/(1.331) + 100/(1.4641) + 100/(1.61051)
        expected = (
            100 / 1.1
            + 100 / 1.1**2
            + 100 / 1.1**3
            + 100 / 1.1**4
            + 100 / 1.1**5
        )
        assert npv(cf, 0.10) == pytest.approx(expected, rel=1e-4)

    def test_negative_npv(self):
        # Investing $1000, getting back $100/year → negative NPV
        cf = [-1000.0] + [100.0] * 10
        result = npv(cf, 0.10)
        assert result < 0

    def test_zero_discount(self):
        cf = [-100, 50, 50, 50]
        assert npv(cf, 0.0) == pytest.approx(50.0)

    def test_high_discount(self):
        # Very high rate should make future cashflows nearly zero
        cf = [0.0, 1000.0, 1000.0]
        result = npv(cf, 10.0)  # 1000% discount
        assert result < 200


class TestIRR:
    """Internal Rate of Return tests."""

    def test_simple_irr(self):
        # -100 + 110/(1+irr) = 0 → irr = 0.10
        cf = [-100.0, 110.0]
        assert irr(cf) == pytest.approx(0.10, rel=0.01)

    def test_irr_known_value(self):
        # -100, 50, 50, 50 → IRR ≈ 23.38%
        cf = [-100.0, 50.0, 50.0, 50.0]
        result = irr(cf)
        assert 0.20 < result < 0.30

    def test_all_negative(self):
        import math
        cf = [-100.0, -50.0, -25.0]
        result = irr(cf)
        assert math.isnan(result) or result == 0.0


class TestPayback:
    """Payback period tests."""

    def test_exact_payback(self):
        cf = [-100.0, 50.0, 50.0]  # Payback exactly at year 2
        assert payback_period(cf) == pytest.approx(2.0)

    def test_never_recovers(self):
        cf = [-100.0, 10.0, 10.0, 10.0]
        assert payback_period(cf) is None

    def test_immediate(self):
        cf = [50.0, 50.0]
        assert payback_period(cf) == 0.0

    def test_interpolation(self):
        # -100 + 40 + 40 + 40 = 20 at year 3 → payback during year 3
        cf = [-100.0, 40.0, 40.0, 40.0]
        # After year 2: cumulative = -20
        # Year 3: recovers 20 out of 40 → 0.5 years into year 3
        # So payback = 2.5 years
        result = payback_period(cf)
        assert result == pytest.approx(2.5, rel=0.01)


class TestProfitabilityIndex:
    def test_pi_greater_than_one(self):
        cf = [-100.0, 60.0, 60.0]  # NPV > 0 → PI > 1
        assert profitability_index(cf, 0.10) > 1.0

    def test_pi_less_than_one(self):
        cf = [-100.0, 10.0, 10.0]
        assert profitability_index(cf, 0.10) < 1.0


class TestWACC:
    def test_standard_wacc(self):
        # E=60%, Ke=12%, D=40%, Kd=8%, T=22%
        result = wacc(0.60, 0.12, 0.40, 0.08, 0.22)
        expected = 0.60 * 0.12 + 0.40 * 0.08 * 0.78
        assert result == pytest.approx(expected)

    def test_no_debt(self):
        result = wacc(1.0, 0.10, 0.0, 0.05)
        assert result == pytest.approx(0.10)

    def test_ratio_mismatch(self):
        with pytest.raises(ValueError):
            wacc(0.5, 0.10, 0.3, 0.05)


class TestDiscountFactor:
    def test_year_zero(self):
        assert discount_factor(0.10, 0) == pytest.approx(1.0)

    def test_year_five(self):
        assert discount_factor(0.10, 5) == pytest.approx(1 / 1.1**5)
