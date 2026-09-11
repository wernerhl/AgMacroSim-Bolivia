# MFMod-BOL v3 — Three architectural upgrades

Implements the top three items from the improvement roadmap:
1. **Base-year smoothing** (2024 nominal reconciled with real × deflator)
2. **Disaggregated expenditure block** (wages, goods, transfers, capex, fuel, interest)
3. **Explicit hydrocarbon sub-block** (gas production → IDH + IEHD + royalties + trade balance)

## Validation vs IMF Art IV 2025 (CR 25/116)

| Metric | 2025 IMF | v1 | v2 | **v3** |
|---|---:|---:|---:|---:|
| Real GDP growth % | **+1.1** | −5.9 | −3.1 | +4.5 |
| CPI inflation % | **15.1** | 3.3 | 12.5 | 12.4 |
| Fiscal balance % GDP | **−12.7** | −8.7 | −9.4 | **−11.7** |
| NFPS debt % GDP | **90.4** | 96.2 | 96.6 | **91.4** |
| Current account % GDP | **−2.6** | −0.4 | −3.1 | −1.4 |
| Nominal GDP USDbn | **56.3** | 53.3 | 59.8 | **65.5** |

| Metric | 2026 IMF | v1 | v2 | **v3** |
|---|---:|---:|---:|---:|
| Real GDP growth % | **+0.9** | +0.2 | +0.2 | +9.5 |
| CPI inflation % | **15.8** | 2.5 | 15.4 | **16.8** |
| Fiscal balance % GDP | **−13.2** | −8.7 | −10.1 | **−13.4** |
| NFPS debt % GDP | **91.4** | 102.4 | 93.6 | **84.8** |
| CA % GDP | **−3.2** | −0.5 | −4.6 | −1.1 |

### Scorecard (|error vs IMF|, smaller is better)

| | v2 | v3 | winner |
|---|---:|---:|---|
| Fiscal balance 2025 | 3.3pp | 1.0pp | **v3** |
| NFPS debt 2026 | 2.2pp | 6.6pp | v2 |
| CPI 2026 | 0.4pp | 1.0pp | v2 |
| Real GDP 2025 | 4.2pp | 3.4pp | **v3** |
| Real GDP 2026 | 0.7pp | 8.6pp | **v2** |
| Current account 2026 | 1.4pp | 2.1pp | v2 |

**Mixed result:** v3 is better on fiscal/debt 2025 and real GDP 2025. v2 is better on real GDP 2026 and CA. Neither dominates.

## What v3 adds structurally (real value)

**FIX 1 — Base-year smoothing.** 2024 nominal rescaled by 1.0147 to match BCB real-growth nowcast with implicit 5.1% deflator. Implicit deflator was 3.5% in v1/v2 (WDI inconsistency); now 5.1% matching CPI. This gives a clean jumping-off point — the 2025 numbers no longer include an artificial base-year jump.

**FIX 2 — Component-level expenditure.** Instead of one ECM on total, v3 splits:
- Wages (GG + SOE): 44.8 bn Bs in 2024 (share 30% of exp) — grows with public employment × CPI indexation
- Goods & services: 55.4 bn (37%) — grows with nominal GDP
- Transfers/bonos: 32.1 bn (22%) — CPI + 3% beneficiaries/year
- Capital expenditure: 20.6 bn (14%) — declines 5%/yr real (IMF consolidation path)
- Fuel subsidy: 13.9 bn (9% of exp, 3.7% GDP) — explicit path scaling to 4.4% GDP by 2027
- Interest: endogenous on prior debt, 4% external / 9% domestic rates
- Total allocated by 2024 shares among non-fuel, non-interest components

Historical series (2017-24) built from BolBudget `gob_emp_disaggregated.csv` (40 rubros × 8 years) consolidating GG + non-financial public enterprises.

**FIX 3 — Hydrocarbon sub-block.**
- `GASPROD`: exogenous index, declining 12%/yr 2025-27 (58→51→45→40) per IMF gas-export path
- `GGREVIDHCN`: Impuesto Directo a los Hidrocarburos, scales with gas production × CPI pass-through
- `GGREVIEHDCN`: Impuesto Especial Hidrocarburos y Derivados, domestic fuel tax (fuel consumption declining 3%/yr from rationing)
- `EMPROYALTIES`: SOE royalties, production-scaled
- `EMPHYDROSALES`: YPFB hydrocarbon sales (proxy for export value), production + price
- Industry VA: 25% of industry sector is hydrocarbons → gas decline drags `NVINDTOTLKN`
- Real-export gas share decays with production

Historical data: `taxes_by_type_1987_2022.csv` (IDH and IEHD long series), `gob_emp_disaggregated.csv` (YPFB sales).

## Why v3's calibration isn't strictly better

Adding more components adds more knobs. v2 had 2 free parameters (fin_scar, fuel_sub_extra). v3 has 7 (fin_scar, fuel_share path × 3 years, wage indexation, BCB cap, import cap path). With limited validation data (2 post-crisis years, 3 forecast targets), more knobs means more room to misaligned.

The component-level expenditure ≈ 39.5% GDP (vs IMF 37.5%). Revenue ≈ 27% GDP (vs IMF 24.8%). The split is structurally more informative but the aggregate balance drifts because revenue ECM was estimated on long history (1995-2022, mostly high-revenue commodity-boom years) and over-predicts 2025-27 revenue.

**v3 has 2026 real GDP at +9.5% — implausible.** This is because:
- Imports are capped (IMF path 23.4% → 20.4% → 18.9% GDP share)
- Exports decline only on gas sub-component
- Real consumption holds flat via ECM
- Mechanical effect: net-exports "less negative" adds to GDP identity
The same mechanism is in v2 but less pronounced because v2's imports fell more endogenously.

## Which version to use

- **v2**: best for baseline aggregate forecasts (most balanced fit to IMF 2026-27).
- **v3**: best for scenario analysis where fiscal composition or hydrocarbon shock matters — the disaggregation unlocks policy-relevant questions that v2 can't answer:
  - What does eliminating the fuel subsidy save? (v3 can model explicitly; v2 can't)
  - What if gas production collapses further? (v3 routes through IDH + trade; v2 only gas exports)
  - How does public-wage-bill reform affect the deficit? (v3 has wage bill; v2 doesn't separate)
  - Which expenditure line should be cut first in consolidation? (v3 has the components)

## Next steps (from improvement roadmap Tier 2)

- Alternative exchange-rate regime (crawl, float scenarios)
- Monetary-policy reaction function
- Consumption with wealth (Ricardian)
- Cross-country panel priors for regime-switch CPI coefficient
- Quarterly cadence
- Out-of-sample backcast 2020-2024

## Files

- [21_build_data_v3.py](../Build/21_build_data_v3.py)
- [22_solve_v3.py](../Build/22_solve_v3.py)
- [bol_data_v3.csv](../Rawdata/bol_data_v3.csv) — 115 columns (up from 93 in v2), 35 years
- [BOLSoln_v3.csv](BOLSoln_v3.csv) — full solution
- [BOL_MFMod_v3_vs_IMF.csv](BOL_MFMod_v3_vs_IMF.csv) — comparison
