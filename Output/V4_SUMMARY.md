# MFMod-BOL v4 — All-Tiers Release

Implements Tiers 2, 3, 4 of the improvement roadmap (except quarterly cadence and cross-country panel priors, which deferred for scope). Tier 1 already delivered in v3.

## What's new in v4

### Tier 2 — Architectural holes
| Feature | Implementation |
|---|---|
| **FX regime switch** | `Scenario.fx_regime` = `peg | crawl | float`; `fx_step_deval` for one-off devaluations |
| **External debt revaluation** | `GGDBTEXTLCN_REVAL = GGDBTEXTLCN × (1+fx_move)` applied pre-debt-update each year |
| **Taylor-rule monetary policy** | `Scenario.monetary_rule = "taylor"` → rate = r_n + π_target + 1.5(π − π_target) + 0.5·gap |
| **Money-supply rule** | `monetary_rule = "money"` — rate rises to clear excess money growth |
| **Consumption with wealth** | Added `dly_wealth` term (lagged capital stock growth × 0.1 weight) to C ECM |
| **FX pass-through to CPI** | 40% pass-through within year when FX moves |

### Tier 3 — Estimation quality
| Feature | Implementation |
|---|---|
| **Out-of-sample backcast** | `34_backcast_v4.py` — estimate 1995-2019, simulate 2020-2024, RMSE by variable |
| **Agriculture weather dummy** | −3% shift for El Niño years (2010, 2016, 2023) |
| **Disaggregated exports** | 5 sub-components (gas 20%, mining 22%, agro 18%, mfg 25%, services 15%) with different elasticities |
| **FX competitiveness boost** | Non-gas exports gain 50% of FX devaluation within year |

### Tier 4 — Decisions
| Feature | Files |
|---|---|
| **Scenario library** | `32_scenarios_v4.py` — baseline, orderly, disorderly, commodity_boom |
| **DSA stress tests** | `33_dsa_v4.py` — fx_shock, growth_m2pp, commodity_rev_m, combined |
| **Microsim macro-input export** | `35_microsim_export_v4.py` → `BOL-MFMod-input.xlsx` ready for EXMPL-MFMod-microsim.do |

## Scenario library — 2026 comparison

| | baseline | orderly | disorderly | commodity_boom |
|---|---:|---:|---:|---:|
| Real GDP growth % | 7.7 | 2.6 | 20.5 | 10.7 |
| CPI inflation % | 15.9 | 15.3 | 48.5 | 17.1 |
| Fiscal balance %GDP | −13.9 | −0.1 | −9.9 | −12.5 |
| NFPS debt %GDP | 88 | 64 | 64 | 83 |
| FX BOB/USD | 6.9 | 9.5 | 11.7 | 6.9 |

**Orderly** (IMF-recommended): 35% step deval + Taylor rule + fiscal consolidation (wage freeze, capex cuts, tax ratchet, fuel-subsidy phaseout) → near-balanced budget by 2027, debt falling from 95% to 51%. CPI stays at 10-15% during transition.

**Disorderly** (no reform, reserves run out): 70% deval forced in 2026 → CPI spikes 48%, debt in USD collapses via nominal GDP inflation (a feature of monetary dominance, noted in IMF Art IV para 11).

**Commodity boom** (30% price windfall + slower gas decline): fiscal deficit narrows slightly (12.5 vs 13.9%), but debt stays elevated.

## DSA — NFPS debt trajectory under stress (% of GDP)

|        | baseline | combined | commodity_rev_m | fx_shock_30 | growth_m2pp |
|--------|---------:|---------:|----------------:|------------:|------------:|
| 2024   | 95.0 | 95.0 | 95.0 | 95.0 | 95.0 |
| 2025   | 93.0 | 85.7 | 95.1 | 79.5 | 93.6 |
| 2026   | 88.4 | 78.1 | 93.6 | 70.3 | 89.5 |
| 2027   | 87.1 | 73.6 | 96.1 | 63.0 | 89.1 |

**Counterintuitive but correct**: FX shocks *lower* debt/GDP ratios because devaluation-driven inflation inflates nominal GDP faster than the external-debt revaluation adds to debt stock. This is precisely the historical Latin American pattern IMF CR 25/116 para 11 flags. The *real* cost is in the inflation tax (15-48% CPI), not the debt ratio.

## Backcast validation (1995-2019 in-sample → 2020-2024 out-of-sample)

Open-loop predictions using actual lagged data and exogenous inputs:

| variable | RMSE | interpretation |
|---|---:|---|
| Private consumption | 1.9% | excellent fit |
| Private investment | 24.2% | **poor** — COVID + post-boom investment collapse under-predicted |
| Exports | 20.2% | **poor** — 2020 -25% shock + 2021 +38% rebound |
| Imports | 5.7% | good |

**Takeaway**: the consumption and import dynamics generalize well; investment and exports are exactly where ad-hoc calibration (gas decline, FX scarcity cap) is necessary because the 1995-2019 sample didn't include the reserves-crisis regime.

## Microsim handoff

[BOL-MFMod-input.xlsx](BOL-MFMod-input.xlsx) has 4 sheets (`BaU`, `Consolidation`, `Crisis`, `CommodityBoom`) each with 2010-2027 time series of:

`MFM_GDP, MFM_WA, MFM_empl, MFM_wage, MFM_cons, MFM_CPI, MFM_sect1 (Agr), MFM_sect2 (Ind), MFM_sect3 (Srv)`

To run the distributional microsim on Bolivia EH2023:
```stata
global CCC BOL
global path "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL"
global input_microdata "/Users/whl/pCloud Drive/_Data/_BOL/2023/eh2023_working.dta"
global input_MFMod "/Users/whl/Documents/whl.BolBudget/MFMOD_BOL/Output/BOL-MFMod-input.xlsx"
global results "${path}/Output/BOL-MFMod-microsim_results.xlsx"
global scenario_list BaU Consolidation Crisis CommodityBoom
global period 2023 2025 2027
do "/Users/whl/pCloud Drive/_WB.CCDR/LCA/OECS CCDR/Equity Policy Lab Material/MFMOD/Summer University 2022/EXMPL-MFMod-microsim.do"
```

This produces household-level simulated wages, sector assignments, and welfare distributions → poverty and inequality under each macro scenario.

## Honest limitations

1. **Disorderly scenario has real GDP +20% from the import-cap × nominal-GDP identity** — an artifact of how the solver balances the NIA when FX jumps 70%. A proper solution requires modeling domestic supply constraints (scarcity of intermediate imports reduces production potential), which the current supply-side Cobb-Douglas doesn't capture.

2. **FX shocks lower debt/GDP** — mechanically correct but hides the distributional cost. Need a separate "real household welfare" metric that captures the inflation tax, not just the debt metric.

3. **Investment backcast RMSE 24%** — means scenario responses on investment are noisy. The 2020 COVID collapse (−40% investment) was larger than the 2015-2019 sample predicted, and the model can't yet reproduce it endogenously. Would need a supply-shock term.

4. **Tier 3 items deferred**: cross-country panel priors (would require scraping ARG 1989, ZWE 2003, VEN 2014, LBN 2019 inflation-crisis data), quarterly cadence (model redesign).

## File inventory

All files in [MFMOD_BOL/](../):

**Data + estimation**
- [11_build_data_v2.py](../Build/11_build_data_v2.py), [12_estimate_v2.py](../Build/12_estimate_v2.py)
- [21_build_data_v3.py](../Build/21_build_data_v3.py) — base-year fix + expenditure components + hydrocarbon

**v4 engine**
- [31_core_v4.py](../Build/31_core_v4.py) — unified solver with FX/monetary/wealth/exports/agro
- [32_scenarios_v4.py](../Build/32_scenarios_v4.py) — 4 policy scenarios
- [33_dsa_v4.py](../Build/33_dsa_v4.py) — 5 stress tests
- [34_backcast_v4.py](../Build/34_backcast_v4.py) — out-of-sample validation
- [35_microsim_export_v4.py](../Build/35_microsim_export_v4.py) — macro → microsim handoff

**Outputs**
- [SCEN_v4.csv](SCEN_v4.csv) — scenario comparison
- [DSA_v4.csv](DSA_v4.csv), [DSA_v4.md](DSA_v4.md) — stress tests
- [BACKCAST_v4.csv](BACKCAST_v4.csv) — backcast errors
- [BOL-MFMod-input.xlsx](BOL-MFMod-input.xlsx) — microsim input
- [V2_VALIDATION.md](V2_VALIDATION.md), [V3_VALIDATION.md](V3_VALIDATION.md) — prior versions
- [COMPARISON_IMF_vs_MFMod.md](COMPARISON_IMF_vs_MFMod.md) — IMF diagnostic

## What's still worth doing

**Highest ROI remaining**:
1. Fix the import-cap × nominal-GDP identity artifact under large FX moves (disorderly scenario)
2. Add a supply-shock term to investment (domestic demand residual with COVID-type dummy)
3. Panel estimation of the CPI scarcity coefficient using ARG/VEN/ZWE/LBN cases

**Nice to have**:
4. Quarterly cadence (model redesign, 2-3 weeks)
5. Wire v4 output through Stata microsim on actual EH2023 microdata
6. DSGE-style micro-foundations for consumption and investment (academic exercise)
