"""
Cashflow engine — standalone cashflow calculations that can be composed
with any fiscal regime result.
"""

from __future__ import annotations

from fiscal_model.economics.metrics import npv, irr, payback_period, profitability_index
from fiscal_model.schemas.outputs import FiscalBreakdown, PSCResult


def cumsum(series: list[float]) -> list[float]:
    """Cumulative sum of a series."""
    result = []
    total = 0.0
    for v in series:
        total += v
        result.append(total)
    return result


def net_present_value(result: PSCResult) -> float:
    """Extract NPV from a result (convenience)."""
    return result.npv_contractor


def annual_free_cashflow_from_breakdown(bd: FiscalBreakdown) -> list[float]:
    """Free cash flow = net cashflow (already after tax, after all deductions)."""
    return bd.net_cashflow


def cumulative_net_cashflow(bd: FiscalBreakdown) -> list[float]:
    """Cumulative net cashflow year by year."""
    return cumsum(bd.net_cashflow)


def cashflow_waterfall_table(result: PSCResult) -> list[dict]:
    """
    Build a cashflow waterfall table suitable for charting or Excel output.

    Returns a list of dicts, one per year, with all waterfall components
    for the CONTRACTOR.
    """
    c = result.contractor
    rows = []
    for i, yr in enumerate(c.years):
        rows.append(
            {
                "year": yr,
                "gross_revenue": c.gross_revenue[i],
                "ftp_share": c.ftp_share[i],
                "cost_recovery": c.cost_recovery_received[i],
                "equity_split": c.equity_split_share[i],
                "investment_credit": c.investment_credit[i],
                "taxable_income": c.taxable_income[i],
                "tax_paid": c.tax_paid[i],
                "dmo_revenue": c.dmo_revenue[i],
                "net_cashflow": c.net_cashflow[i],
            }
        )
    return rows


def sensitivity_grid(
    result: PSCResult,
    variable_name: str,
    base_value: float,
    deltas: list[float],
    recalc_fn,
) -> list[dict]:
    """
    Run a sensitivity grid: vary ``variable_name`` by each ``delta``
    and recalculate NPV/IRR.

    Args:
        result: Base case result.
        variable_name: Name of the variable being perturbed.
        base_value: Base value of the variable.
        deltas: List of delta fractions (e.g. [-0.20, -0.10, 0.0, 0.10, 0.20]).
        recalc_fn: Callable(new_value) → PSCResult.

    Returns:
        List of {variable, value, npv, irr} dicts.
    """
    rows = []
    for d in deltas:
        new_val = base_value * (1 + d)
        try:
            r = recalc_fn(new_val)
            rows.append(
                {
                    "variable": variable_name,
                    "delta_pct": d * 100,
                    "value": new_val,
                    "npv": r.npv_contractor,
                    "irr": r.irr_contractor,
                }
            )
        except Exception:
            rows.append(
                {
                    "variable": variable_name,
                    "delta_pct": d * 100,
                    "value": new_val,
                    "npv": float("nan"),
                    "irr": float("nan"),
                }
            )
    return rows
