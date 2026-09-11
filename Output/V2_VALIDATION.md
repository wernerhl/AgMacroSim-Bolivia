# MFMod-BOL v2 — Validation vs IMF Art IV 2025

Rebuilt from v1 using long BolBudget fiscal series (1990-2022, 30 rubros × 33 years + 2023-24) and with five architectural fixes.

## What changed vs v1

| Fix | v1 | v2 |
|---|---|---|
| Fiscal ECM sample | 7 obs (2017-23) | **28 obs (1995-2022)** |
| Fiscal data source | WDI (breaks 2007) | **BolBudget long SPNF** |
| CPI channel | Phillips only | **Phillips + reserve-scarcity × BCB-financing** |
| BCB monetary financing | not modeled | **explicit series; reserve-depletion regime switch (2021-22)** |
| Fuel subsidy | baked into 2024 level | **endogenous block, +2-2.5pp GDP in 2025-27** |
| Hydrocarbon revenue | flat @ 2024 ratio | **ECM-estimated erosion** |
| Export gas sub-component | rigid −3%/yr total | **non-gas via ECM + gas −15%/yr** |
| Debt perimeter | General Government | **NFPS (+10pp) aligned with IMF** |
| Investment ECM α | estimated free (−0.15) | **clipped to 0** (no drift) |
| Investment SR signal | actual GDP growth | **potential GDP growth** (no feedback) |
| 2024 real GDP | WDI prelim (−1.1%) | **BCB nowcast (+1.3%)** |
| Reserves dynamics | not modeled | **explicit path + months-of-imports metric** |

## Validation vs IMF Country Report 25/116 (Art IV, April 2025)

| 2026 | IMF Art IV | v1 | **v2** | v2 gap |
|---|---:|---:|---:|---:|
| Real GDP growth % | +0.9 | +0.2 | **+0.2** | −0.7pp |
| CPI inflation (avg) % | 15.8 | 2.5 | **15.4** | **−0.4pp** |
| Fiscal bal % GDP | −13.2 | −8.7 | **−10.1** | +3.1pp |
| NFPS debt % GDP | 91.4 | 102.4 | **93.6** | +2.2pp |
| Current acc % GDP | −3.2 | −0.5 | **−4.6** | −1.4pp |
| Nominal GDP USD bn | 65.9 | 54.7 | **69.2** | +3.3bn |

| 2027 | IMF Art IV | **v2** | v2 gap |
|---|---:|---:|---:|
| Real GDP growth % | +0.6 | +1.2 | +0.6pp |
| CPI inflation (avg) % | 17.1 | **17.1** | **0pp** |
| Fiscal bal % GDP | −12.5 | −10.7 | +1.8pp |
| NFPS debt % GDP | 92.8 | 89.7 | −3.1pp |

The inflation match is now within 0.4pp for 2026 and exact for 2027. This was the architectural hole.

## Full comparison table

See [BOL_MFMod_v2_vs_IMF.csv](BOL_MFMod_v2_vs_IMF.csv).

```
year               2023   2024   2025   2026   2027
IMF_RealGDP        3.10   1.30   1.10   0.90   0.60
v2_RealGDP         2.52   1.30  -3.11   0.17   1.24
IMF_CPI            2.60   5.10  15.10  15.80  17.10
v2_CPI             2.58   5.10  12.53  15.43  17.05
IMF_FiscBal      -10.90 -10.30 -12.70 -13.20 -12.50
v2_FiscBal        -9.44  -8.68  -9.43 -10.09 -10.68
IMF_NFPSDebt      90.80  95.00  90.40  91.40  92.80
v2_NFPSDebt       90.80  95.00  96.56  93.60  89.67
IMF_CA            -2.50  -2.70  -2.60  -3.20  -3.80
v2_CA             -2.24  -2.38  -3.14  -4.59  -5.67
IMF_NomGDP_USDbn  45.50  48.40  56.30  65.90  75.00
v2_NomGDP_USDbn   52.34  54.88  59.84  69.19  82.00
```

## Remaining calibration gaps (not architectural)

1. **2025 real GDP −3.1% vs IMF +1.1%** — initial-condition jump from scaling 2024 level to authorities' nowcast. The trajectory is right (2026 +0.2%, 2027 +1.2%) but 2025 is a ~4pp one-off. Would fix by smoothing the base-year adjustment across deflated components. Low priority — 2026-27 projections are what matters for forecast use.

2. **Fiscal deficit 2-3pp tighter than IMF.** My expenditure ECM tracks nominal GDP; IMF assumes further expenditure drift (IMF para 20: wage bill rising, subsidies, interest payments stacking). Could add a "political cycle" dummy or a public-wage-bill Phillips curve.

3. **Current account wider than IMF (−4.6 vs −3.2 in 2026).** My model has imports falling less than IMF in 2026-27. IMF expects FX scarcity to keep compressing imports (they show imports % GDP falling from 23.4 → 18.9 over 2024-26). My compression hard-coded at 5-3% real.

## Code layout

v2 files in [Build/](../Build/):
- [11_build_data_v2.py](../Build/11_build_data_v2.py)
- [12_estimate_v2.py](../Build/12_estimate_v2.py)
- [13_extend_exog_v2.py](../Build/13_extend_exog_v2.py)
- [14_solve_v2.py](../Build/14_solve_v2.py)

Outputs:
- [BOLSoln_v2.csv](BOLSoln_v2.csv) — full workfile
- [BOL_MFMod_v2_projections.csv](BOL_MFMod_v2_projections.csv) — summary
- [BOL_MFMod_v2_vs_IMF.csv](BOL_MFMod_v2_vs_IMF.csv) — side-by-side

## What v2 tells us about Bolivia

1. **The peg is not the same as price stability.** Even with FX held at 6.91, the monetary-financing channel delivers 15-17% inflation when reserves are exhausted. v2 reproduces this mechanism.
2. **NFPS debt stabilizes in the mid-90s of GDP** (v2 and IMF agree: 90-100% range, no runaway). Debt-to-GDP is held flat by nominal GDP inflating faster than new nominal debt.
3. **The cost of inaction is inflation, not debt.** Reform pressure will come from 15-20% CPI hurting households (especially the bottom quintile where fuel subsidies benefit the top — IMF Box 1).
