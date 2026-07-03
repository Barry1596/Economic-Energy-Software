"""
Depreciation schedule generators.

Supports:
- Straight-line (linear depreciation over asset life).
- Declining balance (fixed % of declining value).
- Double-declining balance (200% of straight-line rate).

All functions return per-year depreciation amounts (not accumulated).
"""

from __future__ import annotations

from typing import Sequence


def straight_line(
    cost_basis: float,
    salvage_value: float = 0.0,
    useful_life_years: int = 10,
) -> list[float]:
    """
    Straight-line depreciation.

    Each year gets (cost_basis - salvage) / useful_life_years.

    Returns:
        List of annual depreciation amounts, length = useful_life_years.
    """
    if useful_life_years <= 0:
        raise ValueError("useful_life_years must be positive")
    annual = (cost_basis - salvage_value) / useful_life_years
    return [annual] * useful_life_years


def declining_balance(
    cost_basis: float,
    rate: float,
    salvage_value: float = 0.0,
    useful_life_years: int = 10,
) -> list[float]:
    """
    Declining (reducing) balance depreciation.

    Each year: depreciation = rate × remaining book value.
    The final year adjusts to hit salvage value exactly.

    Args:
        cost_basis: Initial asset cost.
        rate: Depreciation rate (decimal, e.g. 0.25 for 25%).
        salvage_value: Minimum book value.
        useful_life_years: Maximum depreciation period.
    """
    dep = []
    book_value = cost_basis
    for i in range(useful_life_years - 1):
        current_dep = min(book_value * rate, book_value - salvage_value)
        dep.append(current_dep)
        book_value -= current_dep
    # Final year: remaining to salvage
    dep.append(max(0.0, book_value - salvage_value))
    return dep


def double_declining(
    cost_basis: float,
    salvage_value: float = 0.0,
    useful_life_years: int = 10,
) -> list[float]:
    """
    Double-declining balance (200% of straight-line rate).

    Switches to straight-line when SL produces higher depreciation.
    """
    rate = 2.0 / useful_life_years
    return declining_balance(
        cost_basis=cost_basis,
        rate=rate,
        salvage_value=salvage_value,
        useful_life_years=useful_life_years,
    )


def aggregate_annual_depreciation(
    schedules: Sequence[list[float]],
    n_years: int,
) -> list[float]:
    """
    Sum multiple depreciation schedules into per-year totals.

    Each schedule in ``schedules`` is a list of annual depreciation for
    one asset. The result is the total depreciation for each year across
    all assets, trimmed or padded to ``n_years``.
    """
    result = [0.0] * n_years
    for sched in schedules:
        for i, val in enumerate(sched):
            if i < n_years:
                result[i] += val
    return result
