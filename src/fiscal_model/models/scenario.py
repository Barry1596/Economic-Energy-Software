"""
Scenario management — compare multiple fiscal scenarios side by side.
"""

from __future__ import annotations

from typing import Optional

from fiscal_model.schemas.outputs import PSCResult, ScenarioResult


class ScenarioManager:
    """
    Manage multiple PSC scenarios for comparison.

    Usage::

        mgr = ScenarioManager()
        mgr.add("Base Case", base_result)
        mgr.add("Upside", upside_result)
        mgr.add("Downside", downside_result)
        comparison = mgr.compare()
    """

    def __init__(self) -> None:
        self._scenarios: dict[str, PSCResult] = {}

    def add(self, name: str, result: PSCResult) -> None:
        if name in self._scenarios:
            raise ValueError(f"Scenario '{name}' already exists. Use replace() to overwrite.")
        self._scenarios[name] = result

    def replace(self, name: str, result: PSCResult) -> None:
        self._scenarios[name] = result

    def remove(self, name: str) -> None:
        del self._scenarios[name]

    @property
    def names(self) -> list[str]:
        return list(self._scenarios.keys())

    def get(self, name: str) -> PSCResult:
        return self._scenarios[name]

    def compare(self) -> ScenarioResult:
        """
        Return a ScenarioResult containing all scenarios sorted by NPV descending.
        """
        sorted_items = sorted(
            self._scenarios.items(),
            key=lambda kv: kv[1].npv_contractor,
            reverse=True,
        )
        names = [name for name, _ in sorted_items]
        results = [res for _, res in sorted_items]
        return ScenarioResult(scenario_names=names, results=results)

    def summary_table(self) -> list[dict]:
        """
        Build a rows-of-scenarios summary table.
        """
        rows = []
        for name, res in self._scenarios.items():
            rows.append(
                {
                    "scenario": name,
                    "npv": res.npv_contractor,
                    "irr": res.irr_contractor,
                    "payback_years": res.payback_period_years,
                    "pi": res.profitability_index,
                    "gov_take_pct": res.government_take_pct_of_gross,
                }
            )
        return sorted(rows, key=lambda r: r["npv"], reverse=True)
