"""
Economic metrics: NPV, IRR, payback period, profitability index, WACC.

Uses ``numpy-financial`` under the hood for reliable numerical computation.
"""

from __future__ import annotations

try:
    import numpy_financial as npf
except ImportError:
    npf = None  # type: ignore[assignment]


def npv(cashflows: list[float], discount_rate: float) -> float:
    """
    Net Present Value.

    Args:
        cashflows: Cashflow series starting at **year 0** (t=0).
        discount_rate: Annual discount rate as a decimal (e.g. 0.10 = 10%).

    Returns:
        NPV in the same currency unit as cashflows.
    """
    if npf is not None:
        return npf.npv(discount_rate, cashflows)  # npf handles t=0 edge
    # Pure-Python fallback
    return sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows: list[float], guess: float = 0.10) -> float:
    """
    Internal Rate of Return.

    Args:
        cashflows: Cashflow series starting at year 0.
        guess: Initial guess for the root-finding algorithm.

    Returns:
        IRR as a decimal. Returns ``float('inf')`` if all cashflows are
        non-negative (no investment required / fully cost-recovered from day 1).
        Returns ``0.0`` if all cashflows are non-positive.
    """
    # Edge cases: all-positive or all-negative cashflows
    if all(cf >= 0 for cf in cashflows):
        return float("inf")  # No investment needed → infinite return
    if all(cf <= 0 for cf in cashflows):
        return 0.0

    if npf is not None:
        try:
            result = npf.irr(cashflows)
            return result if not (result is None or (isinstance(result, float) and result != result)) else 0.0
        except Exception:
            return 0.0
    return _irr_fallback(cashflows, guess)


def _irr_fallback(cashflows: list[float], guess: float = 0.10) -> float:
    """Simple Newton-Raphson IRR solver when numpy-financial is not available."""
    rate = guess
    for _ in range(1000):
        npv_val = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
        d_npv = sum(
            -t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows) if t > 0
        )
        if abs(d_npv) < 1e-12:
            break
        rate -= npv_val / d_npv
        if rate <= -0.999:  # Avoid division by zero and meaningless IRR
            return 0.0
    return rate


def payback_period(cashflows: list[float]) -> float | None:
    """
    Simple payback period (undiscounted).

    Returns:
        Number of years to recover the initial investment.
        Returns ``0.0`` if all cashflows are non-negative (immediate payback).
        Returns ``None`` if never reached.
    """
    # Edge case: all cashflows are non-negative → immediate payback
    if all(cf >= 0 for cf in cashflows):
        return 0.0

    cumulative = 0.0
    for t, cf in enumerate(cashflows):
        cumulative += cf
        if cumulative >= 0:
            if t == 0:
                return 0.0
            prev_cumulative = cumulative - cf
            fraction = -prev_cumulative / (cf if abs(cf) > 1e-12 else 1e-12)
            return max(0.0, t - 1 + fraction)
    return None  # Never recovered


def profitability_index(cashflows: list[float], discount_rate: float) -> float:
    """
    Profitability Index (PI) = (NPV + PV of investment) / PV of investment.

    PI > 1.0 means the project creates value (positive NPV).
    """
    pv_investment = 0.0
    pv_returns = 0.0
    for t, cf in enumerate(cashflows):
        pv = cf / (1 + discount_rate) ** t
        if cf < 0:
            pv_investment += abs(pv)
        else:
            pv_returns += pv
    if pv_investment == 0:
        return float("inf")
    return pv_returns / pv_investment


def wacc(
    equity_ratio: float,
    cost_of_equity: float,
    debt_ratio: float,
    cost_of_debt: float,
    tax_rate: float = 0.22,
) -> float:
    """
    Weighted Average Cost of Capital (WACC).

    Args:
        equity_ratio: E / (E + D)
        cost_of_equity: Ke (decimal)
        debt_ratio: D / (E + D)
        cost_of_debt: Kd (decimal, pre-tax)
        tax_rate: Corporate tax rate (decimal)

    Returns:
        WACC as a decimal.
    """
    if abs(equity_ratio + debt_ratio - 1.0) > 1e-6:
        raise ValueError(f"Equity ratio ({equity_ratio}) + debt ratio ({debt_ratio}) must sum to 1.0")
    return equity_ratio * cost_of_equity + debt_ratio * cost_of_debt * (1 - tax_rate)


def discount_factor(discount_rate: float, year: int) -> float:
    """Discount factor for a given year: 1 / (1 + r)^year."""
    return 1.0 / (1 + discount_rate) ** year
