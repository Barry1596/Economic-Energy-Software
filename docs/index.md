# Energi Economic Software — Documentation

> Python library for financial modeling of Indonesian upstream oil & gas, LNG, and energy projects — with BCG/McKinsey-styled Excel & PDF output.

---

## Quick Links

| Section | Description |
|---------|-------------|
| [User Guide](user-guide/getting-started.md) | Step-by-step guide to building your first model |
| [API Reference](api-reference/) | Auto-generated from docstrings (mkdocstrings) |
| [Fiscal Reference](fiscal-reference/psc-cost-recovery.md) | PSC mechanics, formulas, and Indonesian regulatory context |
| [Examples](../examples/) | Working scripts (simple_psc.py, mini_refinery.py) |

---

## Installation

```bash
git clone https://github.com/fikribarry/energi-economic-software.git
cd energi-economic-software
python -m pip install -e ".[dev]"
```

## Key Concepts

### 1. Immutable Pipeline

```
InputSchema → FiscalRegime → CashflowEngine → OutputSchema → ReportGenerator
```

Every stage is a pure function: same input → same output. No global state, no spreadsheet links to trace.

### 2. Pluggable Fiscal Regimes

```python
# Swap PSC Cost Recovery for Gross Split by changing one class
engine = PSCCostRecovery(input)   # v0.1
engine = GrossSplit(input)        # v0.2
```

### 3. Output with Consulting-Grade Styling

All Excel and PDF outputs automatically apply:
- Navy/white palette (BCG/McKinsey standard)
- Inter + Lato fonts
- KPI tiles, action titles, callout boxes
- Gridlines OFF, print-ready layout
- Conditional formatting (green = positive, red = negative)

---

## Industries & Fiscal Terms

| Industry | Status | Fiscal Regime |
|----------|--------|---------------|
| Hulu Migas (Upstream O&G) | ✅ v0.1 | PSC Cost Recovery |
| Hulu Migas (Upstream O&G) | 🔜 v0.2 | Gross Split |
| LNG Facility / Infrastructure | 🔜 v0.3 | Tolling, JDA |
| Biofuel / Renewable Energy | 🔜 v0.4 | Renewable incentive |

---

## Development

```bash
# Run tests
pytest

# Lint
ruff check src tests

# Type check
mypy src/fiscal_model

# Build docs
mkdocs serve
```
