"""
Pydantic v2 data models for validated financial model inputs.

All fields include constraints (``ge``, ``le``, ``min_length``)
to catch configuration errors before the calculation runs.

Usage::

    from fiscal_model.schemas.inputs import PSCInput, ProductionProfile
    from pydantic import ValidationError

    try:
        psc = PSCInput(name="Study", ...)
    except ValidationError as e:
        print(e)
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
    PositiveFloat,
    NonNegativeFloat,
)


# ──────────────────────────────────────────────────────────────────────
# Utility enums & types
# ──────────────────────────────────────────────────────────────────────


class Currency(str, Enum):
    """Currency for model inputs/outputs."""

    IDR = "IDR"
    USD = "USD"


class DepreciationMethod(str, Enum):
    """Depreciation method for capital expenditure."""

    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    DOUBLE_DECLINING = "double_declining"


class PriceEscalation(str, Enum):
    """Price escalation mode."""

    FLAT = "flat"  # Constant across all years
    ANNUAL_ESCALATION = "annual_escalation"  # Fixed % increase per year
    CUSTOM_ARRAY = "custom_array"  # User provides per-year array


# ──────────────────────────────────────────────────────────────────────
# Production profile
# ──────────────────────────────────────────────────────────────────────


class ProductionProfileVectors(BaseModel, extra="forbid"):
    """Bare production vectors — validated by downstream models."""

    years: list[int] = Field(..., min_length=1, description="Consecutive model years")
    rates_bopd: list[NonNegativeFloat] = Field(
        ..., min_length=1, description="Production rate (barrels of oil per day)"
    )
    days_onstream: Optional[list[NonNegativeFloat]] = Field(
        default=None,
        description="Onstream days per year; defaults to 365 for each year",
    )

    @field_validator("rates_bopd", "days_onstream")
    @classmethod
    def _same_length_as_years(cls, v, info):
        if v is not None and "years" in info.data:
            if len(v) != len(info.data["years"]):
                raise ValueError(
                    f"Length mismatch: got {len(v)}, expected {len(info.data['years'])}"
                )
        return v


class ProductionProfile(BaseModel, extra="forbid"):
    """Full production profile with metadata."""

    vectors: ProductionProfileVectors
    source_description: str = Field(default="", max_length=200)
    uom: str = Field(default="BOPD")

    @computed_field
    def annual_production_bbl(self) -> list[float]:
        """Calculated annual production in barrels."""
        days = self.vectors.days_onstream or [365] * len(self.vectors.years)
        return [rate * day for rate, day in zip(self.vectors.rates_bopd, days)]


# ──────────────────────────────────────────────────────────────────────
# Price assumptions
# ──────────────────────────────────────────────────────────────────────


class PriceAssumption(BaseModel, extra="forbid"):
    """Commodity price assumptions."""

    oil_price_usd_bbl: PositiveFloat = Field(description="Base oil price (ICP) in USD/bbl")
    escalation_mode: PriceEscalation = Field(default=PriceEscalation.FLAT)
    escalation_pct: NonNegativeFloat = Field(
        default=0.0, description="Annual price escalation rate (decimal, e.g. 0.02 = 2%)"
    )
    custom_prices: Optional[list[PositiveFloat]] = Field(
        default=None, description="Per-year prices when escalation_mode='custom_array'"
    )

    @model_validator(mode="after")
    def _validate_custom(self):
        if self.escalation_mode == PriceEscalation.CUSTOM_ARRAY and not self.custom_prices:
            raise ValueError("custom_prices is required when escalation_mode='custom_array'")
        return self


# ──────────────────────────────────────────────────────────────────────
# Capital expenditure (Capex)
# ──────────────────────────────────────────────────────────────────────


class CapexScheduleItem(BaseModel, extra="forbid"):
    """A capital expenditure line item."""

    category: str = Field(..., max_length=80, description="e.g. 'Drilling', 'Facility', 'Pipeline'")
    cost_usd: NonNegativeFloat = Field(description="Total capex cost (nominal USD)")
    year_incurred: int = Field(..., ge=2000, le=2100, description="Year the cost is incurred")
    depreciation_life_years: PositiveFloat = Field(default=10.0)
    depreciation_method: DepreciationMethod = Field(default=DepreciationMethod.STRAIGHT_LINE)
    salvage_value_usd: NonNegativeFloat = Field(default=0.0)


class CapexSchedule(BaseModel, extra="forbid"):
    """Full capital expenditure schedule."""

    items: list[CapexScheduleItem] = Field(..., min_length=1)
    description: str = Field(default="", max_length=200)
    contingency_pct: NonNegativeFloat = Field(
        default=10.0, description="Contingency % applied to total (e.g. 10)"
    )

    @computed_field
    def total_nominal_usd(self) -> float:
        return sum(item.cost_usd for item in self.items)

    @computed_field
    def total_including_contingency_usd(self) -> float:
        return self.total_nominal_usd * (1 + self.contingency_pct / 100)


# ──────────────────────────────────────────────────────────────────────
# Operating expenditure (Opex)
# ──────────────────────────────────────────────────────────────────────


class OpexCategory(str, Enum):
    """Standard operating cost categories."""

    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    LABOR = "labor"
    LOGISTICS = "logistics"
    HSE = "hse"
    OFFICE = "office"
    OTHER = "other"


class OpexSchedule(BaseModel, extra="forbid"):
    """Annual operating expenditure schedule."""

    years: list[int] = Field(..., min_length=1)
    categories: dict[OpexCategory, list[NonNegativeFloat]] = Field(
        ...,
        description="Per-category per-year opex costs (USD). Keys are opex categories.",
    )

    @field_validator("categories")
    @classmethod
    def _validate_vectors(cls, v, info):
        if "years" in info.data:
            n = len(info.data["years"])
            for cat_name, vec in v.items():
                if len(vec) != n:
                    raise ValueError(
                        f"Opex '{cat_name}' has {len(vec)} values, "
                        f"but years has {n}"
                    )
        return v

    @computed_field
    def total_per_year(self) -> list[float]:
        """Total opex per year (sum across categories)."""
        n = len(self.years)
        result = [0.0] * n
        for vec in self.categories.values():
            for i in range(n):
                result[i] += vec[i]
        return result


# ──────────────────────────────────────────────────────────────────────
# PSC Fiscal Terms — the main input object
# ──────────────────────────────────────────────────────────────────────


class PSCInput(BaseModel, extra="forbid"):
    """
    Complete input data for a PSC Cost Recovery financial model.

    All percentages are expressed as decimals (0.0 to 1.0) unless
    otherwise noted.

    Example::

        PSCInput(
            name="Mini Refinery Case",
            production=ProductionProfile(vectors=...),
            price=PriceAssumption(oil_price_usd_bbl=75.0),
            capex=CapexSchedule(items=[...]),
            opex=OpexSchedule(years=[2026], categories={...}),
            ftp_pct=0.20,
            contractor_split_after_cr=0.35,
            tax_rate_pct=0.22,
        )
    """

    # ----- Project metadata -----
    name: str = Field(..., min_length=1, max_length=120, description="Project/study name")
    version: str = Field(default="1.0", max_length=20)
    client: str = Field(default="", max_length=120)

    # ----- Core assumptions -----
    production: ProductionProfile
    price: PriceAssumption
    capex: Optional[CapexSchedule] = Field(default=None)
    opex: Optional[OpexSchedule] = Field(default=None)

    # ----- PSC fiscal parameters -----
    ftp_pct: Annotated[float, Field(ge=0.0, le=0.30, description="FTP share of gross revenue")]
    ftp_contractor_split: Annotated[
        float,
        Field(ge=0.0, le=1.0, default=0.50, description="Contractor share of FTP"),
    ]

    cost_recovery_ceiling_pct: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.80,
            description="Cost recovery ceiling as fraction of gross revenue (post-FTP).",
        ),
    ]
    cost_recovery_depreciation_life_years: PositiveFloat = Field(
        default=5.0, description="Depreciation life for capex in cost recovery calculation"
    )

    # Contractor share AFTER cost recovery (sliding scale by production can be custom)
    contractor_split_after_cr: Annotated[
        float, Field(ge=0.0, le=1.0, description="Contractor equity split after cost recovery")
    ]
    investment_credit_pct: Annotated[
        float,
        Field(
            ge=0.0,
            le=0.20,
            default=0.0,
            description="Investment credit % applied to capex (if applicable).",
        ),
    ]

    # ----- Tax -----
    tax_rate_pct: Annotated[
        float, Field(ge=0.0, le=0.50, default=0.22, description="PPh Badan / corporate income tax")
    ]
    branch_profit_tax_pct: Annotated[
        float, Field(ge=0.0, le=0.40, default=0.20, description="PPh 26 / branch profit tax")
    ]
    dmo_pct: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.25,
            description="Domestic Market Obligation % of contractor share.",
        ),
    ]
    dmo_fee_usd_bbl: NonNegativeFloat = Field(
        default=0.50,
        description="DMO fee received by contractor per barrel delivered (typically ~$0.50/bbl).",
    )

    # ----- Discount rate -----
    discount_rate_pct: Annotated[
        float,
        Field(ge=0.0, le=0.50, default=0.10, description="WACC / discount rate for NPV"),
    ]

    # ----- Notes -----
    notes: str = Field(default="", max_length=2000)

    @computed_field
    @property
    def government_split_after_cr(self) -> float:
        """1 - contractor split (automatically derived)."""
        return 1.0 - self.contractor_split_after_cr

    @computed_field
    @property
    def model_years(self) -> list[int]:
        return self.production.vectors.years

    @computed_field
    @property
    def n_years(self) -> int:
        return len(self.model_years)

    @model_validator(mode="after")
    def _validate_splits(self):
        if self.contractor_split_after_cr <= 0 or self.contractor_split_after_cr >= 1:
            raise ValueError("contractor_split_after_cr must be strictly between 0 and 1")
        return self

    @model_validator(mode="after")
    def _validate_opex_matches_production(self):
        if self.opex is not None:
            py = self.production.vectors.years
            oy = self.opex.years
            if py != oy:
                raise ValueError(
                    f"Production years {py} must match opex years {oy}"
                )
        return self
