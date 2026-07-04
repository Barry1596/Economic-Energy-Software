"""
Pydantic output schemas — validated containers for fiscal model results.

These are produced by the fiscal engine and consumed by report generators.
All monetary values are in USD unless otherwise noted.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, NonNegativeFloat, computed_field


class FiscalBreakdown(BaseModel, extra="forbid"):
    """Per-year fiscal components for one party (contractor or government)."""

    years: list[int]
    gross_revenue: list[float]
    ftp_share: list[float]
    cost_recovery_received: list[float]
    equity_split_share: list[float]
    investment_credit: list[float]
    dmo_revenue: list[float]
    taxable_income: list[float]
    tax_paid: list[float]
    net_cashflow: list[float]

    @computed_field
    def total_net_cashflow(self) -> float:
        return sum(self.net_cashflow)


class PSCResult(BaseModel, extra="forbid"):
    """
    Complete PSC Cost Recovery result — the output of ``PSCCostRecovery.calculate()``.

    Contains contractor breakdown, government breakdown, and summary economics.
    """

    # Metadata
    project_name: str
    model_years: list[int]

    # Key assumptions snapshot
    ftp_pct: float
    contractor_split_after_cr: float
    cost_recovery_ceiling_pct: float
    tax_rate_pct: float
    discount_rate_pct: float

    # Fiscal breakdowns
    contractor: FiscalBreakdown
    government: FiscalBreakdown

    # Summary economics
    # NOTE: npv_contractor sengaja dibebaskan (float) — proyek tidak layak
    # memiliki NPV negatif, dan itu adalah output analisis yang valid.
    npv_contractor: float = Field(description="NPV at discount_rate_pct (boleh negatif)")
    irr_contractor: float = Field(description="IRR (decimal)")
    payback_period_years: Optional[float] = Field(
        default=None, description="Payback period in years (None if not reached)"
    )
    # profitability_index juga boleh < 1.0 (bahkan 0) untuk proyek yang merugi
    profitability_index: float = Field(ge=0.0)

    # Cost recovery
    total_cost_recovery: NonNegativeFloat
    unrecovered_costs_at_end: NonNegativeFloat

    # Government take
    government_take_total: NonNegativeFloat
    government_take_pct_of_gross: float = Field(
        ge=0.0, le=100.0, description="Government take as % of gross revenue"
    )

    # Production
    cumulative_production_mmboe: NonNegativeFloat = Field(
        description="Cumulative production in million barrels of oil equivalent"
    )

    # Total gross
    total_gross_revenue: NonNegativeFloat

    # Warnings / caveats
    warnings: list[str] = Field(default_factory=list)


class SensitivityResult(BaseModel, extra="forbid"):
    """Result of a sensitivity analysis run."""

    variable_name: str
    base_value: float
    delta_values: list[float]  # e.g. [-0.20, -0.10, 0.0, +0.10, +0.20]
    resulting_npvs: list[float]
    resulting_irrs: list[float]

    @computed_field
    def npv_tornado_delta(self) -> list[float]:
        """NPV deviation from base case for each scenario."""
        base = self.resulting_npvs[self.delta_values.index(0.0)]
        return [v - base for v in self.resulting_npvs]


class ScenarioResult(BaseModel, extra="forbid"):
    """Container for comparing multiple scenarios."""

    scenario_names: list[str]
    results: list[PSCResult]
