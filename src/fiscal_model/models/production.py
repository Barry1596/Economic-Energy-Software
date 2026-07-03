"""
Production profile utilities — decline curve analysis, plateau management,
and production vector generation.
"""

from __future__ import annotations

import math
from typing import Optional

from fiscal_model.schemas.inputs import ProductionProfile, ProductionProfileVectors


def exponential_decline(
    initial_rate: float,
    decline_rate: float,
    n_years: int,
    start_year: int = 2026,
) -> ProductionProfile:
    """
    Generate an exponential decline production profile.

    q(t) = qi × e^(-d × t)

    Args:
        initial_rate: Initial production rate (BOPD).
        decline_rate: Annual exponential decline rate (decimal, e.g. 0.15 = 15%).
        n_years: Number of model years.
        start_year: First year.

    Returns:
        ProductionProfile with declining rates.
    """
    years = list(range(start_year, start_year + n_years))
    rates = [initial_rate * math.exp(-decline_rate * t) for t in range(n_years)]
    return ProductionProfile(
        vectors=ProductionProfileVectors(years=years, rates_bopd=rates),
        source_description=(
            f"Exponential decline: qi={initial_rate:,.0f} BOPD, d={decline_rate:.1%}"
        ),
    )


def harmonic_decline(
    initial_rate: float,
    decline_rate: float,
    b_factor: float = 0.5,
    n_years: int = 10,
    start_year: int = 2026,
) -> ProductionProfile:
    """
    Generate a hyperbolic (harmonic) decline production profile.

    q(t) = qi / (1 + b × d × t)^(1/b)

    Args:
        initial_rate: Initial production rate (BOPD).
        decline_rate: Initial decline rate (decimal).
        b_factor: Arps b-factor (0 = exponential, 1 = harmonic, typically 0 < b < 1).
        n_years: Number of model years.
        start_year: First year.
    """
    years = list(range(start_year, start_year + n_years))
    rates = [
        initial_rate / (1 + b_factor * decline_rate * t) ** (1.0 / b_factor)
        if b_factor > 1e-6
        else initial_rate * math.exp(-decline_rate * t)
        for t in range(n_years)
    ]
    return ProductionProfile(
        vectors=ProductionProfileVectors(years=years, rates_bopd=rates),
        source_description=(
            f"Hyperbolic decline: qi={initial_rate:,.0f} BOPD, "
            f"d={decline_rate:.1%}, b={b_factor:.2f}"
        ),
    )


def plateau_then_decline(
    plateau_rate: float,
    plateau_years: int,
    decline_rate: float,
    total_years: int,
    start_year: int = 2026,
    decline_type: str = "exponential",
    b_factor: float = 0.5,
) -> ProductionProfile:
    """
    Generate a profile with a plateau period followed by decline.

    Args:
        plateau_rate: Production rate during plateau (BOPD).
        plateau_years: Duration of plateau.
        decline_rate: Annual decline rate after plateau.
        total_years: Total model horizon (must be > plateau_years).
        start_year: First year.
        decline_type: 'exponential' or 'hyperbolic'.
        b_factor: b-factor for hyperbolic decline.
    """
    if plateau_years >= total_years:
        raise ValueError("plateau_years must be less than total_years")

    years = list(range(start_year, start_year + total_years))
    rates = [plateau_rate] * plateau_years

    decline_years = total_years - plateau_years
    for t in range(decline_years):
        if decline_type == "exponential":
            rate = plateau_rate * math.exp(-decline_rate * t)
        else:
            rate = (
                plateau_rate
                / (1 + b_factor * decline_rate * t) ** (1.0 / max(b_factor, 1e-6))
            )
        rates.append(rate)

    return ProductionProfile(
        vectors=ProductionProfileVectors(years=years, rates_bopd=rates),
        source_description=(
            f"Plateau {plateau_years}y @ {plateau_rate:,.0f} BOPD → "
            f"{decline_type} decline d={decline_rate:.1%}"
        ),
    )


def custom_vectors(
    years: list[int],
    rates: list[float],
    description: str = "",
    days_onstream: Optional[list[float]] = None,
) -> ProductionProfile:
    """Create a production profile from explicit year/rate vectors."""
    return ProductionProfile(
        vectors=ProductionProfileVectors(
            years=years, rates_bopd=rates, days_onstream=days_onstream
        ),
        source_description=description or "Custom production vectors",
    )


def ultimate_recovery(profile: ProductionProfile) -> float:
    """
    Estimate ultimate recovery (EUR) from a production profile.

    Returns:
        Total barrels produced over the model horizon.
    """
    return sum(profile.annual_production_bbl)
