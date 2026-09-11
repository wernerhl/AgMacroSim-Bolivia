# MFMod-BOL — Baseline Projections 2026-2027

Implementation of the World Bank Macro-Fiscal Model (Burns et al. 2019, WPS 8965)
for Bolivia. Data drawn from WDI + local BolBudget fiscal database (2017-2024).

## Methodology
- **Supply side**: Cobb-Douglas production (α=0.55), trend TFP via HP filter (λ=100),
  capital stock via perpetual inventory (δ=0.05). Potential GDP rolled forward.
- **Demand side**: ECM equations for C, I_priv, X, M estimated on 1995-2024 annual data.
- **Prices**: Phillips-curve CPI (gap semi-elasticity 0.15, 50/50 backward-/forward-looking).
- **Fiscal**: Revenue/expenditure held at 2024 effective ratios (30.6% and 39.3% of GDP);
  debt evolves endogenously (D_t = D_{t-1} − BB_t). FX held at 6.91 Bs/USD peg.
- **External**: Exports include −3% structural gas-sector decline. World demand proxy grows 5% USD.
- **Solver**: Gauss-Seidel within-year iteration, tolerance 1e-5.

## Baseline projections

|   year |   GDP_real_bnBs15 |   GDP_growth_pct |   GDP_nom_bnBs |   GDP_nom_bnUSD |   CPI_inflation |   Output_gap_pct |   Fiscal_bal_pctGDP |   Debt_pctGDP |   CA_bnUSD |   Employment_mn |   UNR_pct |   ConsPriv_g_pct |   InvPriv_g_pct |   Exports_g_pct |   Imports_g_pct |   Agr_g_pct |   Ind_g_pct |   Srv_g_pct |
|-------:|------------------:|-----------------:|---------------:|----------------:|----------------:|-----------------:|--------------------:|--------------:|-----------:|----------------:|----------:|-----------------:|----------------:|----------------:|----------------:|------------:|------------:|------------:|
|   2018 |            326.46 |             2.87 |         334.54 |           48.41 |            2.27 |             6.26 |               -6.78 |         55    |      -1.72 |            5    |      3.52 |             3.12 |            4.39 |            1.89 |            4.38 |        2.94 |        2.51 |        2.87 |
|   2019 |            331.38 |             1.51 |         338.98 |           49.06 |            1.84 |             4.83 |               -6.02 |         58    |      -1.37 |            5.25 |      3.68 |             1.89 |            4.59 |            1.44 |           -0.74 |        3.17 |        1.28 |        1.81 |
|   2020 |            289.23 |           -12.72 |         292.39 |           42.31 |            0.94 |           -10.78 |              -10.97 |         79    |      -0.02 |            4.98 |      7.9  |           -11.33 |          -40.24 |          -23.91 |          -30.14 |        4.7  |      -20.05 |      -10.26 |
|   2021 |            318.24 |            10.03 |         330.84 |           47.88 |            0.74 |            -2.04 |               -7.84 |         84    |       1.59 |            5.61 |      5.09 |             7.8  |           19.78 |           37.44 |           22.71 |        3.34 |       18.19 |        7.14 |
|   2022 |            330.16 |             3.75 |         352.13 |           50.96 |            1.75 |             0.88 |               -6.13 |         82    |       1.15 |            5.84 |      3.55 |             5.88 |            4.02 |           11.01 |           15.11 |        1.72 |        2    |        5.41 |
|   2023 |            338.47 |             2.52 |         361.67 |           52.34 |            2.58 |             2.6  |               -9.44 |         83    |      -1.17 |            5.98 |      3.02 |             2.6  |            2.98 |           -8.16 |           -4.04 |        6.74 |        0.5  |        3.16 |
|   2024 |            334.67 |            -1.12 |         379.23 |           54.88 |            5.1  |             0.72 |               -8.68 |         85    |      -1.3  |            6.07 |      3.27 |             1.69 |          -10.85 |          -14.47 |          -10.44 |       -3.89 |       -2.75 |        0.89 |
|   2025 |            314.97 |            -5.89 |         368.42 |           53.32 |            3.28 |            -5.06 |               -8.68 |         96.18 |      -0.21 |            6.06 |      4.76 |            -4.49 |          -22.12 |            3.52 |           -9.03 |        3.15 |       -4.75 |       -5.65 |
|   2026 |            315.43 |             0.15 |         378.08 |           54.71 |            2.5  |            -4.29 |               -8.68 |        102.4  |      -0.26 |            6.12 |      5.07 |             0.58 |           -3.53 |            3.81 |            3.57 |        2.51 |        0.76 |       -0.59 |
|   2027 |            318.33 |             0.92 |         390.44 |           56.5  |            2.36 |            -2.71 |               -8.68 |        107.84 |      -0.36 |            6.23 |      4.57 |             1.22 |           -0.94 |            4.05 |            4.15 |        2.03 |        1.48 |        0.42 |

## Key takeaways for 2026-2027

- **Growth**: 0.1% (2026), 0.9% (2027) —
  subdued, below potential. Reflects productivity drag (TFP −1.6% CAGR since 2014),
  gas-sector decline, and investment weakness after 2024 contraction.
- **Inflation**: ~2.5% — the Phillips curve prints near target because of the negative
  output gap (2027: -2.7%) offsetting pass-through.
- **Fiscal**: Balance held at −8.7% of GDP under BAU. Debt rises to
  **108% of GDP** by 2027 — unsustainable without consolidation.
- **External**: Current account widens modestly as imports recover faster than exports.

## Caveats
- FX assumed to hold the peg. A parallel-market devaluation would reshape prices, debt
  valuation (55% external), and competitiveness immediately.
- Exports proxy uses BOL nominal USD GDP × 1.5 as world demand — trading-partner import
  demand matrix not included. Refinement: bring in COMTRADE-weighted XMKT.
- Estimation sample (1995-2024) mixes hyperinflation recovery, commodity boom and bust.
  Some ECMs have low R² (Agriculture 0.15, Exports 0.16). Paper default θ=0.2 used where
  estimation was unreliable (CPI, wages).
- Fiscal ECM estimated on only 7 observations (2017-2023 from local database) — treat as
  BAU rule rather than structural reaction function.
- Model uses aggregated GFS revenue/expenditure; not the DPF-expanded hydrocarbon block.

## Files

- [`Build/01_fetch_data.py`](../Build/01_fetch_data.py) — WDI fetch, 50/51 WB indicators.
- [`Build/02_create_data.py`](../Build/02_create_data.py) — identities, K stock, potential, gap.
- [`Build/03_equations.py`](../Build/03_equations.py) — ECM estimation (14 equations).
- [`Build/04_extend_exog.py`](../Build/04_extend_exog.py) — 2025-27 exogenous inputs.
- [`Build/05_solve_model.py`](../Build/05_solve_model.py) — Gauss-Seidel simulation.
- [`Build/06_interface.py`](../Build/06_interface.py) — this summary.
- [`Rawdata/bol_data.csv`](../Rawdata/bol_data.csv) — historical panel (93 series).
- [`Rawdata/bol_coefficients.json`](../Rawdata/bol_coefficients.json) — estimated ECM coefficients.
- [`Output/BOLSoln.csv`](BOLSoln.csv) — full solution workfile 1990-2027.
- [`Output/BOL_MFMod_projections_2020_2027.csv`](BOL_MFMod_projections_2020_2027.csv) — summary table.