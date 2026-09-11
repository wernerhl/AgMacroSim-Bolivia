# MFMod-BOL — Macro-Fiscal Model for Bolivia

**Version:** v5 (April 2026)
**Base:** World Bank Macro-Fiscal Model (Burns, Campagne, Jooste, Stephan, Bui 2019; WPS 8965)
**Horizon:** 2025-2027 baseline; scenario framework extends to 2030
**Implementation:** Python, annual cadence, Gauss-Seidel simultaneous solver

This document describes the structure, data, calibration, and predictions of MFMod-BOL, a structural macroeconometric model for Bolivia adapted from the World Bank's MFMod. It also compares MFMod-BOL's projections against the three main external forecasts: IMF 2025 Article IV (April 2025), IMF WEO (October 2025), and World Bank MPO (January 2026).

---

## 1. Context and Motivation

Bolivia is in its deepest macroeconomic crisis since the 1985 hyperinflation. The gas-boom fiscal expansion of 2006-2013 was not wound down when hydrocarbon revenue collapsed; fiscal deficits have averaged 7-10% of GDP since 2014; BCB international reserves fell from USD 15 bn (2014) to USD 1.7-2.0 bn (2023-24); a parallel FX market trades at 12-15 Bs/USD against an official peg of 6.91. A new administration took office on 8 November 2025 with a stabilization program and opened IMF negotiations.

MFMod-BOL was built to produce an internally consistent baseline plus scenarios (peg-break, orderly adjustment, commodity rebound) for this environment, and to provide macro inputs for downstream MFMod-microsim distributional analysis on the EH2023 household survey.

---

## 2. Theoretical framework

The model follows the canonical MFMod architecture described in [WPS 8965](../WPS8965.pdf): a structural econometric system of 50-80 equations organized into seven blocks:

1. **Supply-side equilibrium** — Cobb-Douglas potential GDP, capital stock via perpetual inventory, TFP via HP filter.
2. **GDP demand** — ECM-based consumption, private investment, exports, imports; government consumption/investment mapped from fiscal accounts.
3. **Prices** — Phillips curve on CPI; deflators move with CPI; import and export Keyfitz prices with world-commodity pass-through.
4. **Labor market** — wage ECM (productivity + unemployment gap); employment ECM; structural participation/unemployment via HP filter.
5. **Fiscal** — revenue as effective-rate × tax-base; expenditure components with individual behavioral rules; debt stock endogenous.
6. **Balance of payments** — trade balance from NIA exports/imports; remittances, FDI, capital account scaled to nominal GDP; reserves residual.
7. **Monetary** — Taylor rule (inflation-targeting countries) or UIP condition (pegged countries).

Each behavioral equation uses the error-correction form (Wickens & Breusch 1988):
$$\Delta y_t = \alpha - \theta \cdot [y_{t-1} - f(X_{t-1})] + \sum_i \beta_i \Delta z_{i,t}$$
where the bracketed term drives long-run convergence to a theoretically consistent target, and the short-run deltas capture data-driven cyclical dynamics.

### Bolivia-specific deviations

1. **Pegged FX regime** → UIP imposes policy rate movement; monetary authority surrenders independence.
2. **Monetary-financing inflation channel** → under the peg, BCB financing of the primary deficit creates inflation when reserves are depleted. Modeled as a **regime-switch Phillips curve** where an indicator function `1[reserves < 3 months of imports]` adds ~5pp to inflation. Coefficient estimated on a LATAM panel (7 countries × 35 years) rather than hand-calibrated.
3. **Hydrocarbon sub-block** → gas production exogenous (engineering-driven decline); feeds IDH + IEHD revenue and gas exports; accounts for ~25% of industry VA.
4. **Explicit fuel-subsidy line** → TGN transfers to YPFB, 0.3% GDP (2017) → 3.7% GDP (2024), endogenous to parallel-FX pressure.
5. **NFPS perimeter** → Bolivia's non-financial public sector (GG + SOEs including YPFB, ENDE, ELFEC, COMIBOL) is the IMF-reported debt aggregate. MFMod-BOL matches this perimeter (+~7pp vs general government).

---

## 3. Model equations

### 3.1 Supply side

**Potential GDP** (Cobb-Douglas):
$$\tilde{Y}_t = \tilde{A}_t \cdot {L^*_t}^{\alpha} \cdot K_{t-1}^{1-\alpha}$$
where $\alpha = 0.55$ (labor share, Penn World Tables for BOL), $\tilde{A}_t$ is HP-filtered TFP.

**Capital stock** (perpetual inventory):
$$K_t = (1-\delta) K_{t-1} + I_t, \quad \delta = 0.05$$

**Structural labor supply:**
$$L^*_t = (1 - U^*_t) \cdot \text{LFPR}^*_t \cdot \text{POP}^{15-64}_t$$
LFPR*, U* from HP filter on historical participation and unemployment.

**Output gap:**
$$Y^{\text{gap}}_t = \frac{Y_t - \tilde{Y}_t}{\tilde{Y}_t} \cdot 100$$

### 3.2 Demand side

**Private consumption ECM:**
$$\Delta c_t = \alpha_c - \theta_c \big[c_{t-1} - \log(\text{YD}/P^c)_{t-1}\big] + \beta_{c,1} \Delta \log(\text{YD}/P^c)_t + \beta_{c,2} \Delta y^{\text{potl}}_t$$
YD = labor-share × nominal GDP factor cost. SR term uses potential GDP growth (not actual) in simulation to break feedback loops.

**Private investment ECM:**
$$\Delta i^p_t = \alpha_i - \theta_i \big[i^p_{t-1} - y^{\text{potl}}_{t-1}\big] + \beta_{i,1} \Delta y^{\text{potl}}_t + \beta_{i,2} \Delta r_t$$
Long-run target is potential GDP (Jorgenson user-cost-of-capital identity). α clipped to zero to prevent estimated drift from contaminating projections.

**Exports ECM:**
$$\Delta x_t = \alpha_x - \theta_x \big[x_{t-1} - \text{xmkt}_{t-1}\big] + \beta_x \Delta \text{xmkt}_t$$
with gas sub-component overridden by exogenous gas-production path (YPFB declining ~12%/yr).

**Imports ECM:**
$$\Delta m_t = \alpha_m - \theta_m \big[m_{t-1} - \text{gde}_{t-1}\big] + \beta_{m,1} \Delta \text{gde}_t + \beta_{m,2} \Delta \log(P^m/P^c)_t$$
Real imports compress when import deflator rises faster than consumer prices (FX-scarcity channel).

**Government consumption** — nominal pinned to nominal GDP (short-run tracker).

**GDP identity:**
$$Y_t = C_t + G_t + I_t + X_t - M_t + \Delta\text{Inv}_t + D^{\text{stat}}_t$$

### 3.3 Price block

**CPI (Phillips curve + reserve-scarcity regime switch):**
$$\pi_t = \alpha_\pi + \rho \pi_{t-1} + \gamma Y^{\text{gap}}_t + \phi \cdot \mathbb{1}[\text{reserves}_t < 3\text{ months}]$$

Panel-estimated coefficients (LATAM 7 countries, 1990-2024):
- $\alpha_\pi = 1.4\%$
- $\rho = 0.71$
- $\gamma = 0.15$
- $\phi = 5.4\text{pp}$ (identified from ARG 1989-91, ARG 2001-02, BOL 2022-24)

**Domestic deflators** — move with CPI:
$$\Delta p_{c,t}, \Delta p_{g,t}, \Delta p_{i,t} = \pi_t$$

**Import deflator:**
$$\Delta p^m_t = 0.02 + 0.4\pi_t + 0.08 \cdot \mathbb{1}[\text{scarcity}]$$
adds parallel-FX pass-through when reserves critical.

**Export deflator:**
$$\Delta p^x_t = 0.01 + 0.3\pi_t$$

### 3.4 Labor market

**Wages** (CPI indexation + productivity):
$$\Delta w_t = \pi_t + 0.5 \Delta(\text{Y}/L^*)_t$$

**Employment ECM:**
$$\Delta l_t = \alpha_l - \theta_l [l_{t-1} - l^*_{t-1}] + \beta_{l,1} \Delta Y^{\text{gap}}_t + \beta_{l,2} \Delta l^*_t$$

### 3.5 Fiscal block

**Revenue** (ECM to nominal GDP long-run share):
$$\Delta R_t = \alpha_R - \theta_R [R_{t-1} - Y^N_{t-1}] + \beta_R \Delta Y^N_t$$

**Hydrocarbon revenue** (separate ECM, scaled by gas production):
$$R^{\text{hc}}_t = f(\text{gas production}_t, P^x_t)$$

**Expenditure** (ECM + explicit fuel-subsidy add-on):
$$G_t = G^{\text{ECM}}_t + (s^{\text{fuel}}_y - s^{\text{fuel}}_{2024}) \cdot Y^N_t$$

**Interest payments:**
$$G^{\text{int}}_t = r^e \cdot D^{\text{ext}}_{t-1} + r^d \cdot D^{\text{dom}}_{t-1}$$
with $r^e = 4\%$, $r^d = 9\%$ (2024 effective rates).

**Overall balance:**
$$\text{BB}_t = R_t - G_t$$

**Debt dynamics:**
$$D_t = D_{t-1} - \text{BB}_t + \text{FX revaluation effect}$$
External/domestic share = 25/75 (IMF Art IV path).

### 3.6 Balance of payments

Exports/imports USD derive from NIA nominal divided by FX, scaled to the 2024 BoP-NIA ratio (preserves historical reconciliation).

Remittances grow with weighted income of remitting countries (proxied by LATAM USD GDP). Current account = trade balance + remittances + other flows (scaled to nominal GDP USD).

### 3.7 Monetary

Under peg: policy rate held at 2024 value (8.8% lending rate).
UIP not binding because capital controls reduce arbitrage.
BCB financing is residual: `deficit - external net - private domestic`, capped at 11% of GDP (historical ceiling).

---

## 4. Data sources

All historical data assembled in [bol_data_v5.csv](Rawdata/bol_data_v5.csv) (110 columns × 35 years, 1990-2024).

### 4.1 National accounts

| Variable | Source | Coverage | Notes |
|---|---|---|---|
| Real GDP (constant LCU) | WDI `NY.GDP.MKTP.KN` | 1990-2024 | Growth rates used; level rebuilt from 2015 anchor |
| Nominal GDP (current LCU) | **[gdp_spliced_2000_2024.csv](../analysis/gdp_spliced_2000_2024.csv)** | 2000-2024 | **Splices the 2017 INE methodological break** |
| C, G, I, X, M (real + nominal) | WDI `NE.*.KN/CN` | 1990-2024 | |
| Sectoral VA (Agr/Ind/Srv) | WDI `NV.*.TOTL.KN/CN` | 1990-2024 | |

### 4.2 Prices

| Variable | Source | Coverage |
|---|---|---|
| CPI (2010=100 and 2024=100, YoY) | **[cpi_index_1990_2024.csv](../analysis/cpi_index_1990_2024.csv)** — INE via BolBudget | 1990-2024 |
| GDP deflator | Derived (nominal/real) | 1990-2024 |
| Exchange rate (BOB/USD) | WDI `PA.NUS.FCRF` | 1990-2024 |

### 4.3 Fiscal (the big expansion in v5)

| Variable | Source | Coverage |
|---|---|---|
| SPNF aggregates (27 rubros) | **[spnf_long_1990_2024.csv](../analysis/spnf_long_1990_2024.csv)** — MEFP via UDAPE Dossier c030101 + BEIT | **1990-2024 (35 years)** |
| SPNF in 2024 Bs (real) | [spnf_real_2024Bs.csv](../analysis/spnf_real_2024Bs.csv) | 1990-2024 |
| Tax by type (IVA, IT, IUE, IDH, IEHD, etc.) | **[taxes_by_type_1987_2024.csv](../analysis/taxes_by_type_1987_2024.csv)** — SIN via UDAPE c030401 + BEIT | **1987-2024 (38 years)** |
| Tax by department | [tax_by_dept_1987_2022.csv](../analysis/tax_by_dept_1987_2022.csv) | 1987-2022 |
| GG + SOE disaggregated (40 rubros) | [gob_emp_disaggregated.csv](../analysis/gob_emp_disaggregated.csv) | 2017-2024 |
| Fuel subsidy (TGN → YPFB) | [subsidio_combustibles.csv](../analysis/subsidio_combustibles.csv) — MEFP + MHE + press | 2008-2024 |
| Public investment by sector (38 sectors) | [inversion_publica_by_sector_1990_2024.csv](../analysis/inversion_publica_by_sector_1990_2024.csv) | 1990-2024 |
| Structural balance + output gap | [structural_balance.csv](../analysis/structural_balance.csv) | 2000-2024 |
| Social programs (Renta Dignidad, Bonos) | [social_programs.csv](../analysis/social_programs.csv) | 2019-2024 |
| Intergov transfers | [intergov_transfers_2001_2022.csv](../analysis/intergov_transfers_2001_2022.csv) | 2001-2022 |

### 4.4 Monetary and external

| Variable | Source | Coverage |
|---|---|---|
| BCB reservas internacionales netas | **[bcb_rin_2000_2024.csv](../analysis/bcb_rin_2000_2024.csv)** — BCB | 2000-2024 |
| External public debt | BCB Informes + WDI PPG | 2000-2024 |
| Consolidated NFPS debt %GDP | [macro_gdp_debt_2000_2024.csv](../analysis/macro_gdp_debt_2000_2024.csv) — IMF WEO | 2000-2024 |
| BoP flows (exports, imports, CA, FDI, remittances) | WDI `BX/BM/BN/BF.*.CD` | 1990-2024 |
| Lending rate, M2 | WDI `FR.INR.LEND`, `FM.LBL.BMNY.CN` | 1990-2024 |

### 4.5 Population and labor

| Variable | Source | Coverage |
|---|---|---|
| Total population, 15-64 | WDI `SP.POP.TOTL`, `SP.POP.1564.TO` | 1990-2024 |
| Unemployment rate | WDI `SL.UEM.TOTL.ZS` | 1991-2024 |
| Labor force participation rate | WDI `SL.TLF.CACT.ZS` | 1990-2024 |

### 4.6 Cross-country panel (for CPI estimation)

[latam_comparison_1990_2024.csv](../analysis/latam_comparison_1990_2024.csv) — 7 countries × 35 years × 6 indicators (GDP_USD, inflation_pct, reserves_USD, revenue_pct_GDP, expenditure_pct_GDP, debt_pct_GDP). Countries: ARG, BOL, CHL, COL, ECU, PER, PRY.

**This is what enables the regime-switch CPI coefficient to be estimated rather than guessed.** 210 country-years observations, 66 in the reserves-scarcity regime.

### 4.7 Raw source documents

- MEFP Ejecución SPNF 2017-2024 (all 8 annual Excel files) → [BolBudget root](..)
- BEIT 2024 edition + editions N10-N12 (2019-2022) → [sources/](sources/)
- Informe Fiscal MEFP 2022, 2023
- BCB Informe Deuda Externa Pública jun-2024
- BCB Boletín Sector Externo historical
- UDAPE Dossier Estadístico 2023 — 150+ annual Excel tables
- YPFB Estados Financieros 2023
- CEPR paper on hidrocarburos (1987-2024)
- IMF Country Reports 25/34 (January 2025) and 25/116 (June 2025) → [imf_reports/](../imf_reports/)

---

## 5. Estimation methodology

### 5.1 Sample

Primary estimation sample: **2000-2023** (24 years).

Rationale:
- Pre-1995 data dominated by hyperinflation recovery and IMF stabilization program; structural relationships unstable.
- 2024 excluded as preliminary (INE/BCB revisions typical).
- Spliced GDP available 2000-2024, eliminating the 2017 break that poisoned v1-v4.

Panel CPI estimation uses 1990-2024 (all 7 countries).

### 5.2 ECM estimation

For each behavioral variable, OLS on first-differenced form:
$$\Delta \log y_t = \alpha - \theta [\log y_{t-1} - \log f(X_{t-1})] + \sum_i \beta_i \Delta \log z_{i,t} + \varepsilon_t$$

where $f(X_{t-1})$ is a theory-motivated long-run target (e.g., potential GDP for investment, nominal GDP for revenue). Coefficient $\theta$ constrained to $(0, 1)$. Where $\alpha$ estimates negative (investment, agriculture), clipped to zero to prevent simulation drift — a principled departure from mechanical estimation since WPS 8965 imposes balanced-growth path consistency that requires $\alpha = 0$ in the long run.

### 5.3 Panel CPI estimation

Step 1 (normal regime, reserves ≥ 3 months):
$$\pi_t = \alpha_0 + \rho \pi_{t-1} + \varepsilon_t$$
OLS on pooled 144 country-year observations → $\alpha_0 = 1.4\%$, $\rho = 0.71$.

Step 2 (scarcity regime indicator):
$$\pi_t = \alpha_0 + \rho \pi_{t-1} + \phi \cdot \mathbb{1}[\text{reserves-to-GDP} < 3\%] + \varepsilon_t$$
Scarcity indicator additional loading $\phi = 5.4\text{pp}$ from 66 country-years.

Gap semi-elasticity $\gamma = 0.15$ imposed (standard Phillips curve prior).

### 5.4 Calibrated parameters

Fixed (not estimated) parameters:
- Labor share α = 0.55 (Penn World Tables)
- Depreciation δ = 5%
- External interest rate $r^e = 4\%$ (IMF Art IV effective rate 2024)
- Domestic interest rate $r^d = 9\%$ (BOL lending rate average)
- External debt share = 25% (IMF Art IV)
- BCB financing ceiling = 11% GDP (historical peak 2020)
- Public investment real decline = 5%/yr (IMF consolidation path)
- Gas production index 2025-27: 51 → 45 → 40 (2019=100), per IMF Text Table 3
- Fuel subsidy 2025-27: 3.8% → 4.0% → 4.2% GDP (peg-held drift)

---

## 6. Estimated coefficients (v5)

| Equation | α | θ | β (short-run) | R² | n |
|---|---:|---:|---|---:|---:|
| Private consumption | 0.020 | 0.054 | inc 0.015, gdp 0.868 | **0.97** | 24 |
| Private investment | 0.000 | 0.042 | gdp 2.972, rate 0.315 | 0.83 | 24 |
| Exports (aggregate) | −0.003 | 0.200 | xmkt 0.356 | 0.13 | 24 |
| Imports | −0.609 | 0.368 | gde 1.845 | **0.91** | 24 |
| Agriculture VA | 0.000 | 0.133 | gde −0.076 | 0.15 | 24 |
| Industry VA | 0.000 | 0.077 | gde 1.083 | **0.91** | 24 |
| Employment | 0.005 | 0.571 | gap 0.447, l★ 0 | 0.83 | 24 |
| Revenue total | −0.150 | 0.124 | gdpn 1.152 | 0.38 | 24 |
| Hydrocarbon revenue | 0.026 | 0.306 | gdpn 2.710 | 0.34 | 19 |
| Expenditure total | −0.086 | 0.110 | gdpn 0.779 | 0.39 | 24 |
| CPI (panel) | 0.014 | — | π_lag 0.710, scarcity 0.054 | — | 210 |

Low R² on exports (0.13) and agriculture (0.15) reflects noise (commodity price shocks, weather) — not a structural problem for the model, but means projections for these variables have wider confidence intervals.

---

## 7. Predictions

### 7.1 MFMod-BOL v5 baseline 2025-2027

| | 2024 actual | 2025 | 2026 | 2027 |
|---|---:|---:|---:|---:|
| Real GDP growth % | +1.3 | **−3.3** | **+1.2** | **+1.3** |
| CPI inflation (avg) % | 5.1 | **10.6** | **14.9** | **18.3** |
| Fiscal balance % GDP | −8.7 | **−8.7** | **−7.8** | **−6.8** |
| NFPS debt % GDP | 93.9 | **96.5** | **90.8** | **82.6** |
| Current account % GDP | −2.4 | **−3.6** | **−5.4** | **−7.1** |
| Unemployment rate % | 3.3 | 3.5 | 3.4 | 3.3 |
| Nominal GDP (USD bn) | 54.9 | **58.7** | **68.3** | **81.8** |
| Nominal GDP (bn Bs) | 379.2 | **405.5** | **471.7** | **565.2** |

**Narrative:**
- **2025**: dollar-shortage crisis peaks. Real GDP contracts as import compression (via FX scarcity) reduces intermediate goods availability; CPI rises to 10.6% (annual average) despite official peg, driven by monetary financing × reserves-depleted regime switch. Fiscal deficit stays at −8.7% GDP as hydrocarbon revenue erosion offsets partial compliance with peg-held expenditure rule.
- **2026**: modest recovery (+1.2%) as prices adjust and output gap closes. CPI persistence pushes inflation to 14.9%. Nominal GDP USD jumps to $68bn despite real weakness — the peg-held inflation inflates USD GDP measured at official rate.
- **2027**: +1.3% real growth with CPI at 18.3% — entering a structural high-inflation equilibrium absent reform.

**Debt dynamics:** the NFPS debt ratio falls from 96.5% (2025) to 82.6% (2027) despite persistent primary deficits. This is not a mistake — it reflects the Latin-American pattern where nominal GDP inflates faster than nominal debt stock when monetary financing sustains the fiscal deficit. The *real cost* is in the inflation tax (15-18% CPI), not the debt ratio.

### 7.2 Validation vs historical data

In-sample fit (2010-2024) key variables:
- Nominal GDP identity: <0.1% RMSE (identity holds by construction)
- CPI: actual 5.10% vs model 5.10% (2024 match, panel CPI anchored to BOL history)
- Fiscal deficit: actual -8.68% vs model -8.68% (GGBALOVRLCN from BolBudget long series)
- NFPS debt: actual 93.9% vs model 93.9% (IMF WEO series)

Out-of-sample backcast (1995-2019 coefficients, 2020-2024 prediction):
| Variable | RMSE |
|---|---:|
| Private consumption | 1.9% |
| Imports | 5.7% |
| Exports | 20.2% (COVID + commodity shocks) |
| Private investment | 24.2% (gas-boom collapse) |

Consumption and imports backcast excellently. Exports and investment are noisy because 1995-2019 didn't include the reserves-crisis regime shift.

---

## 8. Cross-source comparison

Four forecasts available for Bolivia 2025-2027:

1. **MFMod-BOL v5** (this model, April 2026)
2. **IMF Art IV 2025 (CR 25/116)** — staff baseline from [Text Table 3](../imf_reports/wayback_1bolea2025002.pdf), published June 2025, based on discussions concluded April 2025. Pre-Paz-administration baseline.
3. **IMF WEO October 2025** — IMF DataMapper latest vintage. Revised down from Art IV.
4. **World Bank MPO (January 2026)** — post-Paz-election but early in stabilization program.
5. **Authorities (Arce government, April 2025)** — Art IV para 13: +2% growth 2024, +3.5% growth 2025, 7.5% inflation. Stance since overtaken by events.

### Side-by-side (selected indicators)

| Metric | Year | MFMod v5 | IMF Art IV | IMF WEO | **WB MPO** | Authorities* |
|---|---:|---:|---:|---:|---:|---:|
| **Real GDP g %** | 2024 | +1.3 | +1.3 | −1.1 | — | +2.0 |
| | 2025 | **−3.3** | +1.1 | −1.2 | **−0.5** | +3.5 |
| | 2026 | **+1.2** | +0.9 | **−3.3** | **−1.1** | — |
| | 2027 | **+1.3** | +0.6 | — | **−1.5** | — |
| **CPI (avg) %** | 2024 | 5.1 | 5.1 | 5.1 | — | — |
| | 2025 | **10.6** | 15.1 | 19.5 | **30** | 7.5 |
| | 2026 | **14.9** | 15.8 | 20.7 | **16.8** | — |
| | 2027 | **18.3** | 17.1 | — | — | — |
| **Fiscal bal % GDP** | 2024 | −8.7 | −10.3 | −8.7 | — | — |
| | 2025 | **−8.7** | −12.7 | −11.6 | **−12.0** | — |
| | 2026 | **−7.8** | −13.2 | −9.3 | — | — |
| **NFPS debt % GDP** | 2024 | 93.9 | 95.0 | 83.2 | — | — |
| | 2025 | **96.5** | 90.4 | 84.8 | — | — |
| | 2026 | **90.8** | 91.4 | 102.7 | — | — |

*Authorities figure from Arce government (pre-November 2025). New Paz administration projections not yet published.

### Interpretation of differences

**MFMod v5 vs IMF Art IV**: Main gap is on 2025 real GDP (v5 −3.3% vs IMF +1.1%). V5's 2024 output gap is +2.3% above potential; mean-reversion pulls real GDP down sharply in 2025. IMF's smooth-landing assumption was written before the acute 2H 2025 FX crisis materialized. CPI paths agree closely (2026: v5 14.9% vs IMF 15.8%, essentially identical; 2027: v5 18.3% vs IMF 17.1%).

**MFMod v5 vs IMF WEO (Oct 2025)**: WEO revised growth sharply lower and inflation sharply higher after seeing 2H 2025 data. v5's CPI path (10.6/14.9/18.3) undershoots WEO (19.5/20.7). v5's growth path (−3.3/+1.2/+1.3) is in between Art IV and WEO.

**MFMod v5 vs WB MPO (Jan 2026)**: MPO is post-election, assumes weaker near-term outlook before stabilization helps. CPI 30% in 2025 exceeds all other estimates — likely reflecting actual 4Q 2025 print which accelerated toward year-end. v5's 10.6% 2025 appears too low ex post.

**All four sources agree** on the core facts:
- BOL is in crisis with CPI accelerating to 15-30%
- Fiscal deficit ~10-13% GDP
- NFPS debt ~90-100% GDP
- Growth stagnant or contracting

They disagree on the **path of adjustment** — this is where the Paz stabilization program, IMF package, and commodity price evolution matter.

---

## 9. Scenario framework

Four canonical scenarios implemented in [32_scenarios_v4.py](Build/32_scenarios_v4.py) using the v4 engine. Note: v4 scenarios should be re-run on the v5 data base (outstanding work).

| Scenario | Description | FX regime | Fiscal | Monetary |
|---|---|---|---|---|
| **baseline** | Peg held, no reform, fuel subsidy drifts | peg | fuel 3.8→4.2% GDP | passive |
| **orderly** | IMF Annex III: 35% step deval + consolidation | float, 35% step + 2% crawl | fuel phased to 0%, wage freeze, capex cut 0.5→1.0pp/yr, tax ratchet | Taylor rule |
| **disorderly** | Reserves run out 2026 → 70% deval, no reform | float, 70% step + 15% crawl | fuel subsidy blows out | passive, BCB fin unlimited |
| **commodity_boom** | 30% commodity-price windfall + slower gas decline | peg | fuel 3.7% GDP (stable) | passive |

Earlier scenarios produced implausible real-GDP responses under the disorderly case (+20% from the import-cap × nominal-GDP identity artifact). **v5 data base will need re-running with proper supply-constraint modeling before scenario results can be considered reliable.**

---

## 10. Debt Sustainability Analysis

Standard WB/IMF stress tests applied to the baseline:

| Stress | Description | Debt 2027 impact |
|---|---|---:|
| Baseline | v5 path | 82.6% |
| FX shock +30% | One-off devaluation | Lower (inflation > revaluation) |
| Growth shock −2pp | Productivity collapse | Modest +3pp |
| Commodity rev decline | Gas faster collapse | +10pp |
| Combined | Smaller FX + growth + commodity | +15pp |

The counterintuitive result that FX shocks *reduce* debt ratios is documented in IMF Art IV footnote 8 — the inflation-driven nominal-GDP surge dominates the external-debt revaluation. The real cost materializes in the inflation tax, not the debt metric.

---

## 11. Limitations and honest caveats

1. **2025 dynamics too sharp.** v5 has −3.3% real GDP in 2025 driven by mean-reversion from the +2.3% 2024 output gap. Arguably realistic given the actual dollar-shortage shock, but not smooth. Could be improved with a quarterly model.

2. **Fiscal deficit too tight (−7-8% vs IMF −12-13%).** Expenditure ECM pulls toward long-run nominal-GDP share. IMF and WB MPO assume continued political-economy spending drift. Would need explicit reaction function for wages, pensions, interest stacking.

3. **Current account wider than IMF.** Price-channel import compression is weaker than IMF's implicit quota cap. v2 had an explicit cap; v5 uses prices. A hybrid (soft cap) is probably best.

4. **CPI undershoots WB MPO 2025 (10.6% vs 30%).** Panel coefficient assumes constant scarcity-regime response; Bolivia's 2H 2025 acceleration suggests the pass-through is non-linear at very low reserves. Could be fixed with a quadratic term or second threshold.

5. **No explicit parallel-market FX.** Model uses the official peg throughout. Scenarios can impose step devaluations but the emergence of parallel market pressure from fundamentals is not modeled.

6. **Hydrocarbon production path is exogenous.** Gas field depletion driven by engineering factors not modeled endogenously. Production path calibrated to IMF Text Table 3.

7. **No lithium block.** Bolivia's lithium reserves are substantial but production infrastructure is incomplete. Upside scenarios (commodity_boom) crudely scale export prices; a proper lithium module with capex lags is outstanding.

8. **Annual cadence.** Within-year dynamics (reserves run, FX speculation, weekly CPI) not captured. Quarterly model would be a major redesign.

9. **No social indicator block.** Poverty, inequality, food-insecurity effects require the downstream MFMod-microsim on EH2023 microdata. The v4 macro-input Excel ([BOL-MFMod-input.xlsx](Output/BOL-MFMod-input.xlsx)) is ready; Stata run not yet executed.

10. **v4 scenarios use v3 data.** Scenario/DSA/backcast frameworks in [Build/31-35_*.py](Build/) were written before v5 data was available. Regeneration on v5 base is pending work.

---

## 12. File inventory

### Code
- [41_data_v5.py](Build/41_data_v5.py) — data assembly with all BolBudget fixes
- [42_estimate_v5.py](Build/42_estimate_v5.py) — ECM + LATAM panel CPI estimation
- [43_solve_v5.py](Build/43_solve_v5.py) — forward solver, 2025-2027
- [31_core_v4.py](Build/31_core_v4.py) — scenario engine (v4, needs v5 data port)
- [32_scenarios_v4.py](Build/32_scenarios_v4.py) — 4-scenario runner
- [33_dsa_v4.py](Build/33_dsa_v4.py) — DSA stress tests
- [34_backcast_v4.py](Build/34_backcast_v4.py) — out-of-sample validation
- [35_microsim_export_v4.py](Build/35_microsim_export_v4.py) — macro-to-microsim Excel export

### Data
- [Rawdata/bol_data_v5.csv](Rawdata/bol_data_v5.csv) — 110 columns × 35 years
- [Rawdata/bol_coefficients_v5.json](Rawdata/bol_coefficients_v5.json) — ECM + panel CPI coefficients

### Output
- [Output/BOLSoln_v5.csv](Output/BOLSoln_v5.csv) — full workfile
- [Output/BOL_MFMod_v5_vs_IMF.csv](Output/BOL_MFMod_v5_vs_IMF.csv) — v5 vs IMF Art IV
- [Output/V5_VALIDATION.md](Output/V5_VALIDATION.md) — validation narrative

---

## 13. References

### World Bank Macro-Fiscal Model
- Burns, A., Campagne, B., Jooste, C., Stephan, D., & Bui, T. T. (2019). *The World Bank Macro-Fiscal Model: Technical Description.* Policy Research Working Paper 8965. [WPS8965.pdf](../WPS8965.pdf)
- Burns, A., & Jooste, C. (2019). *Estimating and calibrating MFMod: A panel data approach to identifying the parameters of data poor countries in the World Bank's structural macro model.*
- Burns, A., Janse Van Rensburg, T., Dybczak, K., & Bui, T. (2014). Estimating potential output in developing countries. *Journal of Policy Modeling*, 36, 700-716.

### Bolivia — official
- **IMF (2025a).** *Bolivia: 2024 Article IV Consultation—Press Release, Staff Report, and Statement by the Executive Director.* IMF Country Report 25/34, January 2025. [Wayback PDF](https://web.archive.org/web/2025/https://www.imf.org/-/media/files/publications/cr/2025/english/1bolea2025001-print-pdf.pdf)
- **IMF (2025b).** *Bolivia: 2025 Article IV Consultation—Press Release, Staff Report, and Statement by the Executive Director.* IMF Country Report 25/116, June 2025. [Wayback PDF](https://web.archive.org/web/2025/https://www.imf.org/-/media/files/publications/cr/2025/english/1bolea2025002-print-pdf.pdf)
- **IMF WEO** (October 2025 and April 2026 vintages) via [DataMapper API](https://www.imf.org/external/datamapper/profile/BOL)
- **World Bank (2026).** *Macro Poverty Outlook — Bolivia.* [MPO](https://thedocs.worldbank.org/en/doc/e408a7e21ba62d843bdd90dc37e61b57-0500032021/related/mpo-bol.pdf) (base URL; January 2026 edition)
- **World Bank (2026).** *Global Economic Prospects — Latin America and Caribbean*. [PDF](https://thedocs.worldbank.org/en/doc/7ce50b5aa95bef66048680bba9926ec8-0050012026/related/GEP-Jan-2026-Analysis-LAC.pdf)
- **INE Bolivia** — Serie Histórica del PIB. [Link](https://www.ine.gob.bo/index.php/estadisticas-economicas/pib-y-cuentas-nacionales/producto-interno-bruto-anual/serie-historica-del-producto-interno-bruto/)
- **MEFP Bolivia** — Ejecución SPNF. [Link](https://www.economiayfinanzas.gob.bo/ejecucion-sector-publico-no-financiero)
- **BCB Bolivia** — Informe de Deuda Externa Pública. [jun-2024 PDF](https://www.bcb.gob.bo/webdocs/informes_deudaexterna/DEPEX%20jun24.pdf)
- **UDAPE** — Dossier Estadístico 2023. [Link](https://www.udape.gob.bo/portales_html/dossierweb2023/)
- **SIN (Servicio de Impuestos Nacionales)** — Estadísticas de recaudación. [Link](https://www.impuestos.gob.bo/)

### Econometric foundations
- Wickens, M. R., & Breusch, T. S. (1988). Dynamic specification, the long-run and the estimation of transformed regression models. *Economic Journal*, 98(390), 189-205.
- Hodrick, R. J., & Prescott, E. C. (1997). Postwar U.S. business cycles: An empirical investigation. *Journal of Money, Credit and Banking*, 29(1), 1-16.
- Jorgenson, D. W. (1996). *Investment — Vol. 2: Tax Policy and the Cost of Capital.* MIT Press.

### Political economy context (for cross-source comparison)
- Americas Quarterly (2025). *In Bolivia, Tough Debt Decisions Await Paz.* [Link](https://www.americasquarterly.org/article/bolivia-tough-debt-decisions-await-paz/)
- Economics Observatory (2025). *From crisis to stability: what next for Bolivia's economy?* [Link](https://www.economicsobservatory.com/from-crisis-to-stability-what-next-for-bolivias-economy)
- DevTech Systems (2025). *Bolivia's New Administration's Macroeconomic Challenges.* [Link](https://devtechsys.com/insights/2025/11/04/bolivias-new-administrations-macroeconomic-challenges/)
- University of Miami News (2025). *Bolivia turns to the center.* [Link](https://news.miami.edu/stories/2025/11/bolivia-turns-to-the-center.html)

---

## 14. Next steps

**Short-term (days)**:
1. Port v5 data base into v4 scenario engine — rerun baseline, orderly, disorderly, commodity_boom.
2. Add supply-constraint term to fix the disorderly-scenario import-cap artifact.
3. Calibrate expenditure path to IMF's 37-38% GDP share (close the fiscal gap).

**Medium-term (weeks)**:
4. Quarterly disaggregation for 2025 dynamics (BCB monthly CPI + INE quarterly GDP).
5. Parallel-FX endogenous mechanism (reserves → parallel premium → CPI).
6. Run Stata MFMod-microsim pipeline on EH2023 with v5 baseline + orderly scenarios; output poverty/inequality by scenario.
7. Add lithium production module with capex lags and export-contract pricing.

**Long-term (months)**:
8. Add the new Paz government stabilization program as a formal scenario (once specifics are published).
9. Extend panel to 20+ LATAM countries (include CHL, URY, CRI, MEX, DOM, ECU) for richer CPI and reserve-scarcity identification.
10. Integrate real-time BCB monthly data for nowcasting.
