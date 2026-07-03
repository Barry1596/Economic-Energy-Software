"""
Number, currency, and date formatting helpers.

All formatting follows the ``kosmetik-dokumen`` spec:
- Number format ``#,##0`` for thousands.
- Currency: ``Rp #,##0`` (IDR), ``$ #,##0`` (USD).
- Percent: ``0.0%``.
- Negative numbers in parentheses with red font, e.g. ``(#,##0)``.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Union

Number = Union[int, float, Decimal]


class Currency(Enum):
    """Supported currency display formats."""

    IDR = "Rp #,##0"
    USD = "$ #,##0"
    EUR = "€ #,##0"
    NONE = "#,##0"

    @property
    def symbol(self) -> str:
        return self.value.split(" ")[0]


# --- Excel number format strings (openpyxl-ready) ---
FMT_INTEGER = "#,##0"
FMT_INTEGER_NEG_RED = "#,##0;[Red](#,##0)"
FMT_DECIMAL1 = "#,##0.0"
FMT_DECIMAL2 = "#,##0.00"
FMT_PERCENT = "0.0%"
FMT_PERCENT_NEG_RED = "0.0%;[Red](0.0%)"
FMT_MULTIPLE = "0.00\"x\""
FMT_USD = "$ #,##0"
FMT_IDR = "Rp #,##0"
FMT_USD_NEG_RED = "$ #,##0;[Red]($ #,##0)"
FMT_IDR_NEG_RED = "Rp #,##0;[Red](Rp #,##0)"


def humanize_currency(value: Number, currency: Currency = Currency.IDR) -> str:
    """
    Format a number into a human-readable currency string with magnitude suffix.

    Examples:
        >>> humanize_currency(1_500_000_000)
        'Rp 1.5 M'
        >>> humanize_currency(2_300_000_000_000, Currency.USD)
        '$ 2.3 T'
    """
    abs_val = abs(float(value))
    sign = "-" if value < 0 else ""
    sym = currency.symbol

    if abs_val >= 1e12:
        return f"{sign}{sym}{abs_val / 1e12:.1f} T"  # Triliun
    if abs_val >= 1e9:
        return f"{sign}{sym}{abs_val / 1e9:.1f} M"  # Miliar
    if abs_val >= 1e6:
        return f"{sign}{sym}{abs_val / 1e6:.1f} Jt"  # Juta
    if abs_val >= 1e3:
        return f"{sign}{sym}{abs_val / 1e3:.1f} Rb"  # Ribu
    return f"{sign}{sym}{abs_val:,.0f}"


def humanize_number(value: Number) -> str:
    """Format a plain number with magnitude suffix (no currency symbol)."""
    abs_val = abs(float(value))
    sign = "-" if value < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}{abs_val / 1e9:.2f} B"
    if abs_val >= 1e6:
        return f"{sign}{abs_val / 1e6:.2f} M"
    if abs_val >= 1e3:
        return f"{sign}{abs_val / 1e3:.1f} K"
    return f"{sign}{abs_val:,.0f}"


def format_bopd(value: Number) -> str:
    """Format barrels-of-oil-per-day with thousands separator."""
    return f"{float(value):,.0f} BOPD"


def format_year_range(years: list[int]) -> str:
    """Compact year range, e.g. ``[2026, 2027, 2028]`` -> ``'2026-2028'``."""
    if not years:
        return ""
    if len(years) == 1:
        return str(years[0])
    return f"{min(years)}-{max(years)}"


def excel_currency_format(currency: Currency = Currency.IDR, neg_red: bool = True) -> str:
    """
    Return the Excel cell number-format string for a given currency.

    With ``neg_red=True`` negatives render in red parentheses.
    """
    base = {
        Currency.IDR: FMT_IDR,
        Currency.USD: FMT_USD,
        Currency.EUR: "€ #,##0",
        Currency.NONE: FMT_INTEGER,
    }[currency]
    if not neg_red:
        return base
    return {
        Currency.IDR: FMT_IDR_NEG_RED,
        Currency.USD: FMT_USD_NEG_RED,
        Currency.EUR: "€ #,##0;[Red](€ #,##0)",
        Currency.NONE: FMT_INTEGER_NEG_RED,
    }[currency]
