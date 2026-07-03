"""
Unit tests for formatting utilities.
"""

from __future__ import annotations

import pytest

from fiscal_model.utils.formatting import (
    Currency,
    humanize_currency,
    humanize_number,
    format_bopd,
    format_year_range,
    excel_currency_format,
    FMT_INTEGER,
    FMT_PERCENT,
    FMT_USD,
    FMT_IDR,
)


class TestHumanizeCurrency:
    def test_trillion(self):
        result = humanize_currency(1_500_000_000_000, Currency.IDR)
        assert "1.5 T" in result
        assert "Rp" in result

    def test_billion(self):
        assert "1.5 M" in humanize_currency(1_500_000_000, Currency.IDR)
        assert "2.3 M" in humanize_currency(2_300_000_000, Currency.USD)

    def test_million(self):
        result = humanize_currency(5_500_000, Currency.IDR)
        assert "5.5 Jt" in result

    def test_thousand(self):
        result = humanize_currency(500_000, Currency.IDR)
        assert "500.0 Rb" in result

    def test_negative(self):
        result = humanize_currency(-1_500_000_000, Currency.IDR)
        assert "1.5 M" in result
        assert result.startswith("-")

    def test_small_number(self):
        result = humanize_currency(500, Currency.USD)
        assert "$500" in result


class TestHumanizeNumber:
    def test_billion(self):
        assert humanize_number(1_500_000_000) == "1.50 B"

    def test_million(self):
        assert humanize_number(5_500_000) == "5.50 M"

    def test_thousand(self):
        assert humanize_number(500_000) == "500.0 K"

    def test_small(self):
        assert humanize_number(500) == "500"


class TestFormatBOPD:
    def test_format(self):
        assert format_bopd(5000) == "5,000 BOPD"
        assert "10,000" in format_bopd(10000)


class TestFormatYearRange:
    def test_range(self):
        assert format_year_range([2026, 2027, 2028, 2029, 2030]) == "2026-2030"

    def test_single(self):
        assert format_year_range([2026]) == "2026"

    def test_empty(self):
        assert format_year_range([]) == ""


class TestExcelCurrencyFormat:
    def test_usd(self):
        fmt = excel_currency_format(Currency.USD)
        assert "USD" in fmt or "$" in fmt

    def test_idr(self):
        fmt = excel_currency_format(Currency.IDR)
        assert "Rp" in fmt

    def test_no_neg_red(self):
        fmt = excel_currency_format(Currency.USD, neg_red=False)
        assert "Red" not in fmt
