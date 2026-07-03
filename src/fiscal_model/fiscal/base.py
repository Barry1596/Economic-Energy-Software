"""
Abstract base class for all fiscal regimes.

Every fiscal regime (PSC Cost Recovery, Gross Split, etc.) must implement
this interface so that downstream consumers (cashflow engine, report generators)
can work with any regime polymorphically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from fiscal_model.schemas.outputs import PSCResult


class FiscalRegime(ABC):
    """
    Abstract fiscal regime engine.

    Subclasses implement the ``calculate()`` method, which performs the
    full fiscal waterfall and returns a validated ``PSCResult``.

    The input is supplied at construction time via a Pydantic schema;
    the engine is stateless beyond that — calling ``calculate()`` twice
    produces the same result.
    """

    @abstractmethod
    def calculate(self) -> PSCResult:
        """Run the full fiscal waterfall and return a validated result."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable regime name, e.g. "PSC Cost Recovery"."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
