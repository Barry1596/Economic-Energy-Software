"""
fiscal_model — Financial modeling library for Indonesian upstream oil & gas
PSC, LNG, and energy projects.

Quick start:
    >>> from fiscal_model.schemas.inputs import PSCInput, ProductionProfile
    >>> from fiscal_model.fiscal.psc import PSCCostRecovery
    >>> from fiscal_model.outputs.excel import ExcelReportGenerator

Subpackages
-----------
- ``schemas``   — Pydantic data models for validated input/output.
- ``fiscal``    — Fiscal regime engines (PSC Cost Recovery, Gross Split, Tax).
- ``models``    — Project, production, and cashflow model components.
- ``economics`` — NPV, IRR, payback, WACC, depreciation.
- ``outputs``   — Excel/PDF report generators with BCG/McKinsey styling.
- ``utils``     — Formatting and validation helpers.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Fikri Barry Alfian"
__email__ = "fikri.barry@rekaelang.co.id"
__all__ = ["__version__"]
