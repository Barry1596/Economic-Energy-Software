"""
Gross Split fiscal regime — placeholder for v0.2.

The Gross Split scheme (introduced by Minister of Energy Regulation
No. 52/2017, updated by No. 8/2017) replaces the cost recovery mechanism
with a simpler base split + variable adjustments.

Unlike PSC Cost Recovery, there is no cost reimbursement — the contractor
receives a fixed share of gross production, with adjustments based on
field characteristics (depth, water depth, location, infrastructure, etc.).

This module will be implemented in v0.2.
"""

from __future__ import annotations

from fiscal_model.fiscal.base import FiscalRegime
from fiscal_model.schemas.outputs import PSCResult


class GrossSplit(FiscalRegime):
    """
    Gross Split fiscal regime (placeholder — full implementation in v0.2).

    The base split is typically 57/43 (government/contractor) for oil,
    adjustable via split factors (variable and progressive components).
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "GrossSplit regime will be implemented in v0.2. "
            "Use PSCCostRecovery for current models."
        )

    @property
    def name(self) -> str:
        return "Gross Split (v0.2 — not yet implemented)"

    def calculate(self) -> PSCResult:
        raise NotImplementedError("Gross Split not yet implemented")
