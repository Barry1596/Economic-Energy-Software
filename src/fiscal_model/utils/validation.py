"""
Cross-field and business-rule validation helpers.

These complement Pydantic field-level validation with checks that span multiple
fields (e.g. contractor + government split must sum to 1.0).
"""

from __future__ import annotations

from typing import Iterable, Sequence


class ValidationError(Exception):
    """Raised when a business-rule validation fails."""


def assert_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValidationError(f"'{name}' must be non-negative, got {value}")


def assert_in_range(name: str, value: float, low: float, high: float) -> None:
    if not (low <= value <= high):
        raise ValidationError(f"'{name}' must be in [{low}, {high}], got {value}")


def assert_splits_sum_to_one(contractor_split: float, government_split: float) -> None:
    """Contractor + government equity split must equal 1.0 (after CR)."""
    total = contractor_split + government_split
    if abs(total - 1.0) > 1e-6:
        raise ValidationError(
            f"Contractor split ({contractor_split}) + government split "
            f"({government_split}) must sum to 1.0, got {total}"
        )


def assert_same_length(name_a: str, list_a: Sequence, name_b: str, list_b: Sequence) -> None:
    if len(list_a) != len(list_b):
        raise ValidationError(
            f"'{name_a}' (len={len(list_a)}) and '{name_b}' (len={len(list_b)}) "
            "must have the same length"
        )


def assert_monotonic_years(years: Iterable[int]) -> None:
    years_list = list(years)
    for prev, curr in zip(years_list, years_list[1:]):
        if curr != prev + 1:
            raise ValidationError(
                f"Years must be consecutive integers; gap/break at {prev} -> {curr}"
            )


def assert_rates_non_negative(rates: Iterable[float]) -> None:
    for i, r in enumerate(rates):
        if r < 0:
            raise ValidationError(f"Production rate at index {i} is negative: {r}")
