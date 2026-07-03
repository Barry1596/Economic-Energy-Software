# PSC Cost Recovery — Fiscal Reference

> Indonesian Production Sharing Contract (Kontrak Kerja Sama / KKS)
> cost recovery mechanism — formulas, regulatory basis, and implementation notes.

---

## 1. Overview

The PSC Cost Recovery regime (pre-2017 contracts, and contracts that haven't
transitioned to Gross Split) governs how oil & gas revenue is divided between:

- **Government** (via SKK Migas / BPMA)
- **Contractor** (KKKS — Kontraktor Kontrak Kerja Sama)

Key principle: the contractor bears the upfront investment risk. Costs are
recovered from production revenue before equity sharing begins.

---

## 2. Fiscal Waterfall

```
                    ┌─────────────────────────────┐
                    │     GROSS REVENUE            │
                    │  (Production × ICP Price)    │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │         FTP (20%)            │
                    │  Split: 50/50 Gov/Contractor │
                    └──────┬──────────────────────┘
                           │
                    ┌──────▼──────────────────────┐
                    │   REVENUE AFTER FTP (80%)    │
                    └──────┬──────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     COST RECOVERY        │
              │  min(Opex + Depr + URC,  │
              │      CR Ceiling × RAF)   │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────────────────────┐
                    │    EQUITY TO SPLIT           │
                    │  (RAF − Cost Recovery)       │
                    └──────┬──────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    EQUITY SPLIT          │
              │  Contractor: 15–35%     │
              │  Government: 65–85%     │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────────────────────┐
                    │   CONTRACTOR GROSS TAKE      │
                    │  = FTP_share + CR + Equity   │
                    └──────┬──────────────────────┘
                           │
              ┌────────────▼────────────┐
              │      TAX (22%)           │
              │  DMO adjustment          │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────────────────────┐
                    │  CONTRACTOR NET CASHFLOW     │
                    └─────────────────────────────┘
```

---

## 3. Formulas (As Implemented in ``fiscal_model.fiscal.psc``)

### 3.1 Gross Revenue
```
Gross Revenue(i) = Production(i) × ICP Price(i)
```

### 3.2 FTP (First Tranche Petroleum)
```
FTP(i) = FTP% × Gross Revenue(i)
FTP_Contractor(i) = FTP_Split_Contractor × FTP(i)
FTP_Government(i) = (1 − FTP_Split_Contractor) × FTP(i)
```

- Default FTP% = 20% (common for new contracts)
- Default split = 50/50

### 3.3 Cost Recovery
```
Revenue After FTP(i) = Gross Revenue(i) − FTP(i)
Cost Pool(i) = Opex(i) + Capex Depreciation(i) + Unrecovered(i−1)
CR Ceiling(i) = CR_Ceiling% × Revenue After FTP(i)
Cost Recovery(i) = min(Cost Pool(i), CR Ceiling(i))
Unrecovered(i) = Cost Pool(i) − Cost Recovery(i)
```

- Default CR Ceiling = 80% of Revenue After FTP
- Unrecovered costs carry forward indefinitely (no expiry)

### 3.4 Equity to Split
```
Equity to Split(i) = Revenue After FTP(i) − Cost Recovery(i)
Contractor Equity(i) = Contractor Split% × Equity to Split(i)
Government Equity(i) = (1 − Contractor Split%) × Equity to Split(i)
```

- Contractor split typically 15–35% (depends on field type, vintage)
- Some contracts use **sliding scale** splits based on cumulative production
  or daily production rate (planned for v0.2)

### 3.5 Investment Credit
```
Investment Credit(i) = IC% × Capex ÷ CR Depreciation Life
```
- Provides additional recovery for capital-intensive projects
- Default 5% of capex, amortized over depreciation life

### 3.6 Tax
```
Contractor Gross Take(i) = FTP_Contractor(i) + Cost Recovery(i)
                         + Contractor Equity(i) + Investment Credit(i)

DMO Volume(i) = DMO% × (Contractor Equity(i) / ICP Price(i))
DMO Revenue(i) = DMO Volume(i) × DMO Fee/bbl
DMO Penalty(i) = DMO Volume(i) × ICP Price(i)

Taxable Income(i) = max(0, Contractor Gross Take(i) − DMO Penalty(i))
Tax(i) = Tax% × Taxable Income(i)

Contractor Net Cashflow(i) = Taxable Income(i) − Tax(i) + DMO Revenue(i)
```

- PPh Badan = 22% (since 2022, UU HPP)
- DMO = 25% of contractor equity share
- DMO Fee = typically $0.50/bbl (well below market price = implicit subsidy)

---

## 4. Regulatory References

| Regulation | Content |
|------------|---------|
| UU No. 22/2001 | Oil & Gas Law — basis for PSC contracts |
| PP No. 79/2010 | Operating costs & cost recovery treatment |
| PP No. 27/2017 | Revision of cost recovery provisions |
| PP No. 53/2017 | Tax treatment for upstream O&G |
| Permen ESDM No. 52/2017 | Gross Split (alternative to cost recovery) |
| UU HPP No. 7/2021 | Corporate tax rate increase to 22% |
| PTK-051/SKKIA0000/2024/S0 | Latest SKK Migas cost recovery guidelines |

---

## 5. Comparison: Cost Recovery vs Gross Split

| Aspect | Cost Recovery | Gross Split |
|--------|---------------|-------------|
| Cost reimbursement | Yes (subject to ceiling) | No (embedded in split) |
| Contractor split | 15–35% after CR | 43–57% base split (oil/gas) |
| Government control | Tight (audit every cost) | Lighter (split factors audited) |
| Incentive for cost efficiency | Low (costs recovered) | High (split is fixed) |
| Common for | Pre-2017 contracts | Post-2017 contracts |
| Implementation status | ✅ v0.1 | 🔜 v0.2 |

---

## 6. Typical Model Assumptions (Indonesia)

| Parameter | Typical Range | Default |
|-----------|--------------|---------|
| FTP | 15–25% | 20% |
| FTP Split (Contractor) | 50% | 50% |
| CR Ceiling | 70–90% of RAF | 80% |
| Contractor Equity Split | 15–35% | 35% |
| PPh Badan | 22% | 22% |
| PPh 26 (Branch) | 20% | 20% |
| DMO Percentage | 25% | 25% |
| DMO Fee | $0.25–$0.50/bbl | $0.50/bbl |
| Investment Credit | 0–20% | 5% |
| ICP (benchmark) | $65–$85/bbl | $75/bbl |
| Discount Rate (WACC) | 8–12% | 10% |

---

*Last updated: 3 July 2026 — Fikri Barry Alfian, PT Reka Elang Inovasi.*
