"""
PSC Cost Recovery regime — the standard Indonesian Production Sharing Contract fiscal waterfall.

Fiscal Waterfall (simplified)::

    Gross Revenue = Production × Oil Price
    ├── FTP (First Tranche Petroleum)          = ftp_pct × Gross Revenue
    │   ├── Contractor FTP Share               = ftp_contractor_split × FTP
    │   └── Government FTP Share               = (1 - ftp_contractor_split) × FTP
    │
    ├── Revenue After FTP                      = Gross Revenue − FTP
    │
    ├── Cost Recovery (capped)                 = min(Operating Cost + Depreciation + Unrecovered,
    │                                               CR_ceiling × Revenue After FTP)
    │
    ├── Equity to Split                        = Revenue After FTP − Cost Recovery
    │   ├── Contractor Equity Share            = contractor_split × Equity to Split
    │   └── Government Equity Share            = (1 − contractor_split) × Equity to Split
    │
    ├── Investment Credit                      = investment_credit_pct × Capex (additional recovery)
    │
    ├── Contractor Gross Take                  = FTP_contractor + Cost Recovery + EquityContractor
    │                                             + Investment Credit
    │
    ├── Taxable Income (Contractor)            = Contractor Gross Take − (DMO Fee Cost, etc.)
    │
    ├── Tax Paid                               = tax_rate × Taxable Income
    │
    ├── DMO Revenue                            = DMO delivered × DMO fee/bbl
    │
    └── Net Cashflow (Contractor)              = Taxable Income − Tax + DMO Revenue

References
----------
- ``TH Perbandingan PSC.pdf`` (OneDrive: ``REI File\\MNK PHR\\``)
- Indonesian Government Regulation PP 79/2010, PP 27/2017, PP 53/2017
"""

from __future__ import annotations

from fiscal_model.economics.metrics import discount_factor, irr, npv, payback_period, profitability_index
from fiscal_model.fiscal.base import FiscalRegime
from fiscal_model.schemas.inputs import PSCInput
from fiscal_model.schemas.outputs import FiscalBreakdown, PSCResult


class PSCCostRecovery(FiscalRegime):
    """
    PSC Cost Recovery fiscal engine (Indonesian standard).

    Instantiate with a validated ``PSCInput`` Pydantic model, then call
    ``.calculate()`` to run the full fiscal waterfall.

    Usage::

        psc_input = PSCInput(name="Field X", ...)
        engine = PSCCostRecovery(psc_input)
        result: PSCResult = engine.calculate()

        print(f"NPV: {result.npv_contractor:,.0f}")
        print(f"IRR: {result.irr_contractor:.1%}")
    """

    # ── Construction ─────────────────────────────────────────────────

    def __init__(self, input_data: PSCInput) -> None:
        self._input = input_data
        self._n = input_data.n_years
        self._years = input_data.model_years

    @property
    def name(self) -> str:
        return "PSC Cost Recovery"

    # ── Public API ───────────────────────────────────────────────────

    def calculate(self) -> PSCResult:
        """Run the full PSC fiscal waterfall and return a validated result."""

        inp = self._input
        n = self._n

        # --- 1. Gross revenue per year ---
        gross_rev = self._build_gross_revenue()

        # --- 2. FTP (First Tranche Petroleum) ---
        ftp_total = [inp.ftp_pct * gr for gr in gross_rev]
        ftp_contractor = [inp.ftp_contractor_split * ftp for ftp in ftp_total]
        ftp_government = [(1 - inp.ftp_contractor_split) * ftp for ftp in ftp_total]

        # --- 3. Revenue after FTP ---
        rev_after_ftp = [gr - ftp for gr, ftp in zip(gross_rev, ftp_total)]

        # --- 4. Cost recovery ---
        # Annual operating cost (opex) per year from the input
        opex_per_year = inp.opex.total_per_year if inp.opex else [0.0] * n

        # Depreciation for cost recovery purposes
        cr_dep_per_year = self._build_cr_depreciation(inp.cost_recovery_depreciation_life_years)

        # Total cost pool available each year
        total_cost_pool = [op + dep for op, dep in zip(opex_per_year, cr_dep_per_year)]

        # Cost recovery with carry-forward of unrecovered costs
        cr_ceiling = [inp.cost_recovery_ceiling_pct * raf for raf in rev_after_ftp]
        cr_received, unrecovered_at_end = self._compute_cost_recovery(
            total_cost_pool, cr_ceiling
        )

        # --- 5. Equity to split ---
        equity_to_split = [
            raf - cr for raf, cr in zip(rev_after_ftp, cr_received)
        ]

        # --- 6. Contractor & government equity shares ---
        contractor_equity = [inp.contractor_split_after_cr * eq for eq in equity_to_split]
        gov_equity = [inp.government_split_after_cr * eq for eq in equity_to_split]

        # --- 7. Investment credit ---
        total_capex = inp.capex.total_nominal_usd if inp.capex else 0.0
        invest_credit_per_year = [0.0] * n
        if inp.investment_credit_pct > 0 and total_capex > 0:
            cr_life = int(inp.cost_recovery_depreciation_life_years)
            annual_ic = (inp.investment_credit_pct * total_capex) / cr_life if cr_life > 0 else 0.0
            for i in range(min(cr_life, n)):
                invest_credit_per_year[i] = annual_ic

        # --- 8. Contractor gross take (before tax) ---
        contractor_gross_take = [
            ftp_c + cr + ce + ic
            for ftp_c, cr, ce, ic in zip(
                ftp_contractor, cr_received, contractor_equity, invest_credit_per_year
            )
        ]

        # --- 9. Government gross take ---
        gov_gross_take = [
            ftp_g + ge
            for ftp_g, ge in zip(ftp_government, gov_equity)
        ]

        # --- 10. DMO (Domestic Market Obligation) ---
        # DMO = fraction of contractor equity share sold domestically at `dmo_fee` per barrel.
        dmo_volume = [
            inp.dmo_pct * (ce / inp.price.oil_price_usd_bbl if inp.price.oil_price_usd_bbl > 0 else 0.0)
            for ce in contractor_equity
        ]
        dmo_revenue = [vol * inp.dmo_fee_usd_bbl for vol in dmo_volume]
        dmo_penalty = [
            vol * inp.price.oil_price_usd_bbl
            for vol in dmo_volume
        ]  # DMO portion sold at low fee — rest is "penalty"/loss

        # --- 11. Taxable income ---
        # Taxable income = contractor gross take - DMO penalty
        # (Simplification: DMO reduces taxable income because the low-fee portion is a loss)
        taxable_income = [
            max(0.0, cgt - dp) for cgt, dp in zip(contractor_gross_take, dmo_penalty)
        ]

        # --- 12. Tax paid ---
        tax_paid = [inp.tax_rate_pct * ti for ti in taxable_income]

        # --- 13. Contractor net cashflow ---
        net_cashflow = [
            ti - tax + dr
            for ti, tax, dr in zip(taxable_income, tax_paid, dmo_revenue)
        ]

        # --- Government net cashflow (no tax on gov) ---
        gov_net = gov_gross_take  # Simplified

        # --- 14. Build breakdowns ---
        contractor = FiscalBreakdown(
            years=self._years,
            gross_revenue=gross_rev,
            ftp_share=ftp_contractor,
            cost_recovery_received=cr_received,
            equity_split_share=contractor_equity,
            investment_credit=invest_credit_per_year,
            dmo_revenue=dmo_revenue,
            taxable_income=taxable_income,
            tax_paid=tax_paid,
            net_cashflow=net_cashflow,
        )

        government = FiscalBreakdown(
            years=self._years,
            gross_revenue=gross_rev,
            ftp_share=ftp_government,
            cost_recovery_received=[0.0] * n,
            equity_split_share=gov_equity,
            investment_credit=[0.0] * n,
            dmo_revenue=[0.0] * n,
            taxable_income=gov_net,
            tax_paid=[0.0] * n,
            net_cashflow=gov_net,
        )

        # --- 15. Economic metrics ---
        wacc_rate = inp.discount_rate_pct

        # NPV is calculated after applying discount factor manually (npf.npv handles t=0)
        pv_cf = [cf * discount_factor(wacc_rate, t) for t, cf in enumerate(net_cashflow)]
        total_npv = npv(net_cashflow, wacc_rate)
        project_irr = irr(net_cashflow)
        payback = payback_period(net_cashflow)
        pi = profitability_index(net_cashflow, wacc_rate)

        # Government take
        total_gov_take = sum(gov_net)
        total_gross = sum(gross_rev)
        gov_take_pct = (total_gov_take / total_gross * 100) if total_gross > 0 else 0.0

        # Production
        cumulative_prod_mmboe = (
            sum(inp.production.annual_production_bbl) / 1_000_000
        )

        # Warnings
        warnings = self._collect_warnings(unrecovered_at_end, project_irr, payback)

        return PSCResult(
            project_name=inp.name,
            model_years=self._years,
            ftp_pct=inp.ftp_pct,
            contractor_split_after_cr=inp.contractor_split_after_cr,
            cost_recovery_ceiling_pct=inp.cost_recovery_ceiling_pct,
            tax_rate_pct=inp.tax_rate_pct,
            discount_rate_pct=wacc_rate,
            contractor=contractor,
            government=government,
            npv_contractor=total_npv,
            irr_contractor=project_irr,
            payback_period_years=payback,
            profitability_index=pi,
            total_cost_recovery=sum(cr_received),
            unrecovered_costs_at_end=unrecovered_at_end,
            government_take_total=total_gov_take,
            government_take_pct_of_gross=gov_take_pct,
            cumulative_production_mmboe=cumulative_prod_mmboe,
            total_gross_revenue=total_gross,
            warnings=warnings,
        )

    # ── Internal helpers ─────────────────────────────────────────────

    def _build_gross_revenue(self) -> list[float]:
        """Calculate per-year gross revenue (Production × Price)."""
        inp = self._input
        annual_prod = inp.production.annual_production_bbl
        prices = self._build_price_array()
        return [prod * price for prod, price in zip(annual_prod, prices)]

    def _build_price_array(self) -> list[float]:
        """Expand price assumptions into a per-year array."""
        inp = self._input
        base = inp.price.oil_price_usd_bbl
        esc_pct = inp.price.escalation_pct

        if inp.price.escalation_mode.value == "custom_array" and inp.price.custom_prices:
            return list(inp.price.custom_prices)

        # Flat or annual escalation
        result = []
        for i in range(self._n):
            if inp.price.escalation_mode.value == "flat":
                result.append(base)
            else:
                result.append(base * (1 + esc_pct) ** i)
        return result

    def _build_cr_depreciation(self, cr_life_years: float) -> list[float]:
        """
        Build depreciation schedule for cost recovery.

        For simplicity, capex is spread evenly over the depreciation life.
        """
        inp = self._input
        n = self._n
        cr_life = int(cr_life_years)
        dep_per_year = [0.0] * n

        if inp.capex and cr_life > 0:
            total_depreciable = inp.capex.total_including_contingency_usd
            annual = total_depreciable / cr_life
            for i in range(min(cr_life, n)):
                dep_per_year[i] = annual
        return dep_per_year

    def _build_capex_by_year(self) -> list[float]:
        """Group capex items into per-year totals."""
        inp = self._input
        result = [0.0] * self._n
        if inp.capex:
            for item in inp.capex.items:
                try:
                    idx = self._years.index(item.year_incurred)
                    result[idx] += item.cost_usd
                except ValueError:
                    pass  # Year outside model horizon
        return result

    @staticmethod
    def _compute_cost_recovery(
        cost_pool: list[float],
        ceiling: list[float],
    ) -> tuple[list[float], float]:
        """
        Cost recovery with unlimited carry-forward of unrecovered costs.

        Returns:
            tuple of (cr_received_per_year, unrecovered_costs_at_end)
        """
        n = len(cost_pool)
        cr_received = [0.0] * n
        unrecovered = 0.0

        for i in range(n):
            available = cost_pool[i] + unrecovered
            cr_received[i] = min(available, ceiling[i])
            unrecovered = available - cr_received[i]

        return cr_received, unrecovered

    def _collect_warnings(
        self,
        unrecovered: float,
        project_irr: float,
        payback: float | None,
    ) -> list[str]:
        msgs = []
        if unrecovered > 0:
            msgs.append(
                f"Unrecovered costs at end of model horizon: ${unrecovered:,.0f}. "
                "Consider extending the model horizon or increasing the cost recovery ceiling."
            )
        if project_irr != float("inf") and project_irr < self._input.discount_rate_pct:
            msgs.append(
                f"IRR ({project_irr:.1%}) is below the discount rate "
                f"({self._input.discount_rate_pct:.1%}). Project destroys value on a net basis."
            )
        if payback is None:
            msgs.append("Project does not achieve payback within the model horizon.")
        return msgs
