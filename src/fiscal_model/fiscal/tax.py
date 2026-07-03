"""
Tax calculations for Indonesian oil & gas fiscal regimes.

Key taxes:
- PPh Badan (Corporate Income Tax): 22% (since 2022)
- PPh 26 (Branch Profit Tax / Dividend Withholding): 20%
- PPN / VAT (Pajak Pertambahan Nilai): 11% (since 2024, up from 10%)
- PBB (Land & Building Tax): varies
- LBT / Local taxes (Pajak Daerah): varies by region
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaxRates:
    """Standard Indonesian tax rates for oil & gas (as of 2026)."""

    pph_badan: float = 0.22  # Corporate income tax
    pph_26: float = 0.20  # Branch profit tax / dividend withholding
    ppn: float = 0.11  # VAT (PPN) — increased to 12% in 2025 per UU HPP
    pbb: float = 0.0  # Land & building tax (case-dependent)
    withholding_tax_service: float = 0.02  # PPh 23 on services (2%)


def corporate_tax(taxable_income: float, rate: float = 0.22) -> float:
    """
    Calculate corporate income tax (PPh Badan).

    Assumes a flat rate. For PSC contracts signed before 2010, the rate
    may be the rate at the time of signature. Post-2010 contracts use
    the prevailing rate.

    Args:
        taxable_income: Net taxable income.
        rate: Corporate tax rate (default 22%).

    Returns:
        Tax payable.
    """
    return max(0.0, taxable_income * rate)


def branch_profit_tax(after_tax_profit: float, rate: float = 0.20) -> float:
    """
    Calculate branch profit tax (PPh 26) on dividends repatriated abroad.

    For PSC contractors, this is typically waived during the production
    phase and applied only on actual dividend distribution.

    Args:
        after_tax_profit: Profit after corporate tax.
        rate: Branch profit tax rate (default 20%).
    """
    return max(0.0, after_tax_profit * rate)


def vat(cost: float, rate: float = 0.11) -> float:
    """
    Calculate VAT (PPN) on costs.

    In PSC, VAT is typically recoverable (reimbursed by the government
    as part of cost recovery), so this is often cashflow-neutral.
    """
    return cost * rate


def effective_tax_burden(
    taxable_income: float,
    pph_rate: float = 0.22,
    bpt_rate: float = 0.20,
    apply_bpt: bool = True,
) -> dict[str, float]:
    """
    Calculate the full tax burden on contractor income.

    Returns:
        Dict with pph, bpt, total, and effective_rate.
    """
    pph = corporate_tax(taxable_income, pph_rate)
    after_pph = taxable_income - pph
    bpt = branch_profit_tax(after_pph, bpt_rate) if apply_bpt else 0.0

    total = pph + bpt
    effective = total / taxable_income if taxable_income > 0 else 0.0

    return {
        "pph_badan": pph,
        "branch_profit_tax": bpt,
        "total_tax": total,
        "effective_rate": effective,
    }
