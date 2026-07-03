# Energi Economic Software

> **Financial modeling library for Indonesian upstream oil & gas, LNG, and energy projects** — Python engine with BCG/McKinsey-styled Excel & PDF output.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

---

## Why this exists

Indonesian energy projects — especially **PSC (Production Sharing Contract)** — require complex financial models that combine fiscal regimes (Cost Recovery, Gross Split), sliding-scale splits, DMO obligations, and tax layers. Existing models live in fragile Excel workbooks that are hard to audit, version, or reuse.

This library turns that institutional knowledge into **typed, tested, reproducible Python code**, while still producing the Excel/PDF outputs that finance teams and investment committees expect — styled to top-tier consulting standards (BCG / McKinsey / Bain).

---

## What it does

| Capability | Status |
|------------|--------|
| PSC Cost Recovery engine (FTP, CR, equity split, DMO, tax) | ✅ v0.1 |
| Gross Split regime | 🔜 v0.2 |
| Economic metrics (NPV, IRR, PI, payback, WACC) | ✅ v0.1 |
| Sensitivity & tornado analysis | ✅ v0.1 |
| Multi-scenario management | 🔜 v0.2 |
| Excel output (BCG/McKinsey styling) | ✅ v0.1 |
| PDF investment memo output | 🔜 v0.2 |
| Chart generation (waterfall, tornado, decline curve) | ✅ v0.1 |
| LNG tolling & JDA fiscal regime | 🔜 v0.3 |
| Renewable / biofuel incentive regime | 🔜 v0.4 |

---

## Quick start

```bash
# Install (development)
git clone https://github.com/fikribarry/energi-economic-software.git
cd energi-economic-software
python -m pip install -e ".[dev]"
```

```python
from fiscal_model.schemas.inputs import PSCInput, ProductionProfile, PriceAssumption
from fiscal_model.fiscal.psc import PSCCostRecovery
from fiscal_model.economics.metrics import npv, irr
from fiscal_model.outputs.excel import ExcelReportGenerator

# 1. Define production profile (barrels per day, 10-year horizon)
production = ProductionProfile(
    years=list(range(2026, 2036)),
    rates_bopd=[5000, 8500, 12000, 11500, 10500, 9000, 7500, 6000, 4500, 3000],
)

# 2. Define price assumption
price = PriceAssumption(oil_price_usd_bbl=75.0, escalation_pct=0.02)

# 3. Define PSC fiscal terms
psc_input = PSCInput(
    name="Mini Refinery Case Study",
    production=production,
    price=price,
    ftp_pct=0.20,
    cost_recovery_ceiling_pct=0.80,
    contractor_split_after_cr=0.35,
    tax_rate_pct=0.22,
    dmo_pct=0.25,
    dmo_fee_usd_bbl=0.50,
)

# 4. Run fiscal engine
engine = PSCCostRecovery(psc_input)
result = engine.calculate()

# 5. Economic metrics
project_npv = npv(result.contractor_net_cashflow, discount_rate=0.10)
project_irr = irr(result.contractor_net_cashflow)

# 6. Generate Excel report
ExcelReportGenerator(result).save("mini_refinery_financial_model.xlsx")
```

---

## Architecture

```
InputSchema ──▶ FiscalRegime ──▶ CashflowEngine ──▶ OutputSchema ──▶ ReportGenerator
 (Pydantic)     (PSC/GrossSplit)   (10+ years)       (validated)      (Excel/PDF)
```

- **Immutable pipeline.** Each stage returns a new validated object — no in-place mutation.
- **Pluggable fiscal regimes.** Swap PSC Cost Recovery for Gross Split by changing one class.
- **Styling is centralized.** All visual constants (palette, fonts, layout) live in `outputs/styling.py`, matching the `kosmetik-dokumen` spec.

---

## Project structure

```
src/fiscal_model/
├── schemas/    # Pydantic input/output models (validation)
├── fiscal/     # Fiscal regime engines
│   ├── base.py          # Abstract FiscalRegime interface
│   ├── psc.py           # PSC Cost Recovery (priority)
│   ├── gross_split.py   # Gross Split (v0.2)
│   └── tax.py           # PPh, VAT, branch profit tax
├── models/     # Production, capex/opex, cashflow
├── economics/  # NPV, IRR, payback, depreciation
├── outputs/    # Excel/PDF/charts (BCG/McKinsey styling)
└── utils/      # Formatting & validation helpers
```

---

## Documentation

- 📖 **[User Guide](docs/user-guide/)** — How to build a model from scratch.
- 🔧 **[API Reference](docs/api-reference/)** — Auto-generated from docstrings.
- ⛽ **[Fiscal Reference](docs/fiscal-reference/)** — PSC mechanics, formulas, and Indonesian regulatory context.
- 💡 **[Examples](examples/)** — Working notebooks and scripts.

---

## Fiscal terms covered (PSC Cost Recovery)

The standard Indonesian PSC waterfall implemented:

```
Gross Revenue
   ├── FTP (First Tranche Petroleum)            → 20% of gross
   │      ├── Government share                  → split × FTP
   │      └── Contractor share                  → split × FTP
   ├── Cost Recovery (capped)                   → Opex + Capex depreciation + unrecouped
   └── Equity to Split (after FTP, after CR)
          ├── Contractor share                  → 35% (typical)
          └── Government share                  → 65%

Contractor Taxable Income = FTP_cont + Cost Recovery + Contractor Equity
Contractor Net Cashflow   = Taxable Income − PPh Badan (22%) − DMO penalty
```

See [`docs/fiscal-reference/psc-cost-recovery.md`](docs/fiscal-reference/psc-cost-recovery.md) for full formulas and regulatory references.

---

## Development

```bash
# Run tests with coverage
pytest

# Lint & format
ruff check src tests
ruff format src tests

# Type check
mypy src/fiscal_model

# Build docs
mkdocs serve
```

---

## Contributing

This is an internal tool for PT Reka Elang Inovasi. For changes:

1. Create a feature branch (`git checkout -b feat/my-feature`).
2. Write tests for new fiscal logic — economic calculations must be regression-tested.
3. Ensure `pytest`, `ruff`, and `mypy` all pass.
4. Open a PR with a clear description of the fiscal/economic change.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Fikri Barry Alfian (SKA)** — Engineering Consultant, PT Reka Elang Inovasi.
Domain: EPC, contracts, technical proposals, FEM solver, energy economics.
