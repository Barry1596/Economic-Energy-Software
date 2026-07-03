"""
Sensitivity analysis — tornado charts, spider plots, and parameter sweeps.
"""

from __future__ import annotations

from typing import Callable

from fiscal_model.schemas.inputs import PSCInput
from fiscal_model.schemas.outputs import PSCResult, SensitivityResult


def tornado(
    base_input: PSCInput,
    variables: dict[str, tuple[float, list[float]]],
    recalc_fn: Callable[[PSCInput], PSCResult],
) -> list[SensitivityResult]:
    """
    Run a tornado analysis — vary each variable independently ±X%.

    Args:
        base_input: Base case PSC input.
        variables: Dict of {variable_name: (base_value, [delta_fractions])}.
            e.g. ``{"oil_price": (75.0, [-0.30, -0.15, 0.0, 0.15, 0.30])}``
        recalc_fn: Function that takes a PSCInput and returns a PSCResult.
            The caller is responsible for cloning/modifying the input for each scenario.

    Returns:
        List of SensitivityResult, one per variable.
    """
    results = []
    for var_name, (base_val, deltas) in variables.items():
        npvs = []
        irrs = []
        for d in deltas:
            new_val = base_val * (1 + d)
            # Caller must handle cloning in recalc_fn
            # We pass the original input + a hint; the caller is responsible
            res = recalc_fn(base_input, var_name, d)
            npvs.append(res.npv_contractor)
            irrs.append(res.irr_contractor)

        results.append(
            SensitivityResult(
                variable_name=var_name,
                base_value=base_val,
                delta_values=deltas,
                resulting_npvs=npvs,
                resulting_irrs=irrs,
            )
        )
    return results


def npv_swing(results: list[SensitivityResult]) -> list[dict]:
    """
    Calculate NPV swing (max − min) for each variable, sorted descending.

    Returns:
        List of {variable, npv_swing} sorted by swing magnitude.
    """
    swings = []
    for r in results:
        valid_npvs = [v for v in r.resulting_npvs if v == v]  # exclude NaN
        if len(valid_npvs) >= 2:
            swings.append(
                {
                    "variable": r.variable_name,
                    "npv_swing": max(valid_npvs) - min(valid_npvs),
                }
            )
    return sorted(swings, key=lambda x: x["npv_swing"], reverse=True)
